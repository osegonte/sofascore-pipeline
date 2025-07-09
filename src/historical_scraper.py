"""
Fixed Historical Data Scraper with proper API endpoints and data extraction
"""

import logging
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import make_api_request, try_alternative_endpoints, extract_venue_from_response, safe_get_nested, setup_logging

class HistoricalScraper:
    """Fixed historical scraper with working endpoints"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
    
    def get_historical_matches_by_date(self, date_str):
        """Get completed matches for a date using working endpoints"""
        self.logger.info(f"Fetching historical matches for {date_str}")
        
        # Try multiple endpoint strategies
        endpoints = [
            f"{self.base_url}/sport/football/scheduled-events/{date_str}",
            f"{self.base_url}/sport/football/events/{date_str}"
        ]
        
        for url in endpoints:
            data = make_api_request(url)
            if data and 'events' in data:
                break
        else:
            self.logger.warning(f"No historical data for {date_str}")
            return []
        
        matches = []
        for event in data.get('events', []):
            if event.get('status', {}).get('type') == 'finished':
                match_data = self._extract_historical_match_info(event)
                if match_data:
                    matches.append(match_data)
        
        self.logger.info(f"Found {len(matches)} completed matches")
        return matches
    
    def get_match_comprehensive_historical_details(self, match_id):
        """Get comprehensive historical data with all required fields"""
        self.logger.info(f"Fetching comprehensive historical details for {match_id}")
        
        # Get match details
        match_url = f"{self.base_url}/event/{match_id}"
        match_data = make_api_request(match_url)
        
        if not match_data:
            return None
        
        # Get additional data with fallbacks
        events_data = make_api_request(f"{self.base_url}/event/{match_id}/incidents")
        stats_data = try_alternative_endpoints(match_id, 'statistics')
        lineups_data = try_alternative_endpoints(match_id, 'lineups')
        
        return self._compile_comprehensive_historical_data(
            match_data, events_data, stats_data, lineups_data
        )
    
    def _extract_historical_match_info(self, event):
        """Extract historical match info with proper venue handling"""
        try:
            start_timestamp = event.get('startTimestamp')
            start_time = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            
            # Extract venue properly
            venue = extract_venue_from_response({'event': event})
            
            home_score = safe_get_nested(event, ['homeScore', 'current'], 0)
            away_score = safe_get_nested(event, ['awayScore', 'current'], 0)
            
            return {
                'match_id': event.get('id'),
                'competition': safe_get_nested(event, ['tournament', 'name']),
                'league': safe_get_nested(event, ['tournament', 'category', 'name']),
                'match_date': start_time.date() if start_time else None,
                'match_time': start_time.time() if start_time else None,
                'match_datetime': start_time if start_time else None,
                'home_team': safe_get_nested(event, ['homeTeam', 'name']),
                'away_team': safe_get_nested(event, ['awayTeam', 'name']),
                'home_team_id': safe_get_nested(event, ['homeTeam', 'id']),
                'away_team_id': safe_get_nested(event, ['awayTeam', 'id']),
                'venue': venue or 'Unknown Stadium',  # Ensure venue is never blank
                'home_score': home_score,
                'away_score': away_score,
                'status': safe_get_nested(event, ['status', 'description']),
                'status_type': safe_get_nested(event, ['status', 'type']),
                'scraped_at': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error extracting historical match: {e}")
            return None
    
    def _compile_comprehensive_historical_data(self, match_data, events_data, stats_data, lineups_data):
        """Compile comprehensive historical data"""
        if not match_data:
            return None
        
        event = match_data.get('event', {})
        
        # Extract venue with multiple attempts
        venue = extract_venue_from_response(match_data)
        if not venue:
            venue = safe_get_nested(event, ['venue', 'name'], 'Unknown Stadium')
        
        compiled_data = {
            'match_details': self._extract_historical_match_info(event),
            'goal_events': self._extract_comprehensive_goal_events(events_data),
            'team_statistics': self._extract_final_team_stats(stats_data),
            'player_statistics': self._extract_final_player_stats(lineups_data, events_data),
            'venue': venue
        }
        
        # Ensure venue is set in match details
        if compiled_data['match_details']:
            compiled_data['match_details']['venue'] = venue
        
        return compiled_data
    
    def _extract_comprehensive_goal_events(self, events_data):
        """Extract comprehensive goal events with timing analysis"""
        if not events_data or 'incidents' not in events_data:
            return []
        
        goals = []
        for incident in events_data['incidents']:
            if incident.get('incidentType') == 'goal':
                minute = incident.get('time', 0)
                added_time = incident.get('addedTime', 0)
                total_minute = minute + added_time
                
                goal_data = {
                    'goal_id': incident.get('id'),
                    'exact_timestamp': minute,
                    'added_time': added_time,
                    'total_minute': total_minute,
                    'scoring_player': safe_get_nested(incident, ['player', 'name']),
                    'scoring_player_id': safe_get_nested(incident, ['player', 'id']),
                    'assisting_player': safe_get_nested(incident, ['assist1', 'name']),
                    'assisting_player_id': safe_get_nested(incident, ['assist1', 'id']),
                    'goal_type': incident.get('goalType', 'regular'),
                    'team_side': incident.get('teamSide'),
                    'description': incident.get('text'),
                    'period': 1 if minute <= 45 else 2,
                    'is_late_goal': total_minute >= 75,
                    'is_very_late_goal': total_minute >= 85,
                    'is_injury_time_goal': added_time > 0,
                    'time_interval': self._get_time_interval(total_minute)
                }
                goals.append(goal_data)
        
        return sorted(goals, key=lambda x: x['total_minute'])
    
    def _extract_final_team_stats(self, stats_data):
        """Extract final team statistics with defaults"""
        team_stats = {'home': {}, 'away': {}}
        
        if not stats_data or 'statistics' not in stats_data:
            # Return defaults instead of empty
            return {
                'home': self._get_default_team_stats(),
                'away': self._get_default_team_stats()
            }
        
        for period in stats_data['statistics']:
            if period.get('period') == 'ALL':
                for group in period.get('groups', []):
                    for stat in group.get('statisticsItems', []):
                        self._map_team_statistic(stat, team_stats)
        
        # Fill any missing stats with defaults
        for side in ['home', 'away']:
            defaults = self._get_default_team_stats()
            for key, default_value in defaults.items():
                if key not in team_stats[side]:
                    team_stats[side][key] = default_value
        
        return team_stats
    
    def _get_default_team_stats(self):
        """Get default team statistics"""
        return {
            'possession_percentage': 50.0,
            'shots_on_target': 0,
            'total_shots': 0,
            'corners': 0,
            'fouls': 0,
            'yellow_cards': 0,
            'red_cards': 0,
            'offsides': 0
        }
    
    def _map_team_statistic(self, stat, team_stats):
        """Map API statistic to team stats"""
        stat_name = stat.get('name', '').lower()
        home_value = stat.get('home')
        away_value = stat.get('away')
        
        mapping = {
            'ball possession': 'possession_percentage',
            'possession': 'possession_percentage',
            'shots on target': 'shots_on_target',
            'total shots': 'total_shots',
            'shots': 'total_shots',
            'corner kicks': 'corners',
            'corners': 'corners',
            'fouls': 'fouls',
            'yellow cards': 'yellow_cards',
            'red cards': 'red_cards',
            'offsides': 'offsides',
            'offside': 'offsides'
        }
        
        for key, field in mapping.items():
            if key in stat_name:
                if home_value is not None:
                    team_stats['home'][field] = home_value
                if away_value is not None:
                    team_stats['away'][field] = away_value
                break
    
    def _extract_final_player_stats(self, lineups_data, events_data):
        """Extract final player statistics"""
        if not lineups_data:
            return []
        
        players = []
        
        for side in ['home', 'away']:
            if side in lineups_data:
                # Process starters and subs
                for player in lineups_data[side].get('players', []):
                    player_data = self._extract_player_data(player, side, True, events_data)
                    if player_data:
                        players.append(player_data)
                
                for player in lineups_data[side].get('substitutes', []):
                    player_data = self._extract_player_data(player, side, False, events_data)
                    if player_data:
                        players.append(player_data)
        
        return players
    
    def _extract_player_data(self, player, team_side, is_starter, events_data):
        """Extract individual player data"""
        try:
            player_info = player.get('player', {})
            player_id = player_info.get('id')
            
            goals, assists, cards = self._count_player_events(player_id, events_data)
            
            return {
                'player_name': player_info.get('name'),
                'player_id': player_id,
                'team_side': team_side,
                'position': player.get('position'),
                'jersey_number': player.get('shirtNumber'),
                'is_starter': is_starter,
                'goals': goals,
                'assists': assists,
                'cards_received': cards,
                'minutes_played': 90 if is_starter else 0,  # Estimate
                'shots_on_target': 0  # Not available
            }
        except Exception as e:
            self.logger.error(f"Error extracting player data: {e}")
            return None
    
    def _count_player_events(self, player_id, events_data):
        """Count player goals, assists, and cards"""
        if not events_data or 'incidents' not in events_data or not player_id:
            return 0, 0, 0
        
        goals = assists = cards = 0
        
        for incident in events_data['incidents']:
            incident_type = incident.get('incidentType')
            
            if incident_type == 'goal':
                if safe_get_nested(incident, ['player', 'id']) == player_id:
                    goals += 1
                if safe_get_nested(incident, ['assist1', 'id']) == player_id:
                    assists += 1
            elif incident_type in ['yellowCard', 'redCard']:
                if safe_get_nested(incident, ['player', 'id']) == player_id:
                    cards += 1
        
        return goals, assists, cards
    
    def _get_time_interval(self, total_minute):
        """Get time interval for goal"""
        if total_minute <= 15:
            return '0-15'
        elif total_minute <= 30:
            return '16-30'
        elif total_minute <= 45:
            return '31-45'
        elif total_minute <= 60:
            return '46-60'
        elif total_minute <= 75:
            return '61-75'
        elif total_minute <= 90:
            return '76-90'
        else:
            return '90+'
    
    def get_historical_range(self, start_date, end_date):
        """Get historical matches for date range"""
        self.logger.info(f"Fetching historical matches from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        all_matches = []
        current_date = start
        
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            daily_matches = self.get_historical_matches_by_date(date_str)
            all_matches.extend(daily_matches)
            current_date += timedelta(days=1)
        
        self.logger.info(f"Total historical matches: {len(all_matches)}")
        return all_matches
    
    def scrape_historical_comprehensive(self, days_back=7, specific_matches=None):
        """Comprehensive historical scraping"""
        historical_data = {
            'recent_matches': [],
            'specific_matches': [],
            'comprehensive_goal_analysis': {}
        }
        
        # Get recent matches
        if days_back > 0:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            recent_matches = self.get_historical_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Get detailed data (limit to prevent overload)
            for match in recent_matches[:15]:
                match_id = match.get('match_id')
                if match_id:
                    details = self.get_match_comprehensive_historical_details(match_id)
                    if details:
                        historical_data['recent_matches'].append(details)
        
        # Get specific matches
        if specific_matches:
            for match_id in specific_matches:
                details = self.get_match_comprehensive_historical_details(match_id)
                if details:
                    historical_data['specific_matches'].append(details)
        
        return historical_data
    
    def to_comprehensive_dataframes(self, historical_data):
        """Convert to comprehensive DataFrames"""
        dataframes = {}
        
        all_matches = []
        all_goals = []
        all_players = []
        all_team_stats = []
        
        for match_type in ['recent_matches', 'specific_matches']:
            for match in historical_data.get(match_type, []):
                match_info = match.get('match_details', {})
                if match_info:
                    all_matches.append(match_info)
                    
                    # Add goals with context
                    for goal in match.get('goal_events', []):
                        goal_data = goal.copy()
                        goal_data['match_id'] = match_info.get('match_id')
                        goal_data['competition'] = match_info.get('competition')
                        all_goals.append(goal_data)
                    
                    # Add players with context
                    for player in match.get('player_statistics', []):
                        player_data = player.copy()
                        player_data['match_id'] = match_info.get('match_id')
                        player_data['competition'] = match_info.get('competition')
                        all_players.append(player_data)
                    
                    # Add team stats
                    team_stats = match.get('team_statistics', {})
                    for side in ['home', 'away']:
                        if side in team_stats:
                            stats = team_stats[side].copy()
                            stats['match_id'] = match_info.get('match_id')
                            stats['team_side'] = side
                            stats['team_name'] = match_info.get(f'{side}_team')
                            stats['competition'] = match_info.get('competition')
                            all_team_stats.append(stats)
        
        dataframes['match_details'] = pd.DataFrame(all_matches)
        dataframes['goal_events'] = pd.DataFrame(all_goals)
        dataframes['player_statistics'] = pd.DataFrame(all_players)
        dataframes['team_statistics'] = pd.DataFrame(all_team_stats)
        
        return dataframes
