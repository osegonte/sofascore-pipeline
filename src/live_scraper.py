"""
Fixed Live Match Scraper with corrected API endpoints and data extraction
"""

import logging
import sys
import os
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import make_api_request, try_alternative_endpoints, extract_venue_from_response, extract_possession_from_stats, safe_get_nested, setup_logging

class LiveMatchScraper:
    """Fixed scraper with working API endpoints and proper data extraction"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = "https://api.sofascore.com/api/v1"
        
    def get_live_matches(self):
        """Fetch live matches with proper error handling"""
        self.logger.info("Fetching live matches...")
        
        url = f"{self.base_url}/sport/football/events/live"
        data = make_api_request(url)
        
        if not data:
            self.logger.warning("No live match data received")
            return []
        
        live_matches = []
        events = data.get('events', [])
        
        for event in events:
            match_data = self._extract_fixed_match_info(event)
            if match_data:
                live_matches.append(match_data)
        
        self.logger.info(f"Found {len(live_matches)} live matches")
        return live_matches
    
    def get_match_comprehensive_details(self, match_id):
        """Get complete match details using working endpoints"""
        self.logger.info(f"Fetching comprehensive details for match {match_id}")
        
        # Primary match data
        match_url = f"{self.base_url}/event/{match_id}"
        match_data = make_api_request(match_url)
        
        if not match_data:
            return None
        
        # Try to get additional data with fallbacks
        stats_data = try_alternative_endpoints(match_id, 'statistics')
        events_data = make_api_request(f"{self.base_url}/event/{match_id}/incidents")
        lineups_data = try_alternative_endpoints(match_id, 'lineups')
        
        return self._compile_fixed_match_data(match_data, stats_data, events_data, lineups_data)
    
    def _extract_fixed_match_info(self, event):
        """Extract match info with fixed field mapping"""
        try:
            start_timestamp = event.get('startTimestamp')
            start_time = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            
            # Extract venue from event data
            venue = extract_venue_from_response({'event': event})
            
            # Get status info
            status_info = event.get('status', {})
            
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
                'venue': venue,  # Now properly extracted
                'home_score': safe_get_nested(event, ['homeScore', 'current'], 0),
                'away_score': safe_get_nested(event, ['awayScore', 'current'], 0),
                'minutes_elapsed': safe_get_nested(event, ['time', 'currentPeriodStartTimestamp']),
                'period': safe_get_nested(event, ['time', 'period']),
                'status': status_info.get('description'),
                'status_type': status_info.get('type'),
                'scraped_at': datetime.now()
            }
        except Exception as e:
            self.logger.error(f"Error extracting match info: {e}")
            return None
    
    def _compile_fixed_match_data(self, match_data, stats_data, events_data, lineups_data):
        """Compile match data with proper field extraction"""
        if not match_data:
            return None
        
        event = match_data.get('event', {})
        
        # Extract venue with multiple fallback attempts
        venue = extract_venue_from_response(match_data)
        if not venue and stats_data:
            venue = extract_venue_from_response(stats_data)
        
        compiled_data = {
            'match_details': self._extract_fixed_match_info(event),
            'goal_events': self._extract_fixed_goal_events(events_data),
            'team_statistics': self._extract_fixed_team_stats(stats_data, event),
            'player_statistics': self._extract_fixed_player_stats(lineups_data, events_data),
            'venue': venue  # Ensure venue is captured
        }
        
        # Update match details with venue if found
        if compiled_data['match_details'] and venue:
            compiled_data['match_details']['venue'] = venue
        
        return compiled_data
    
    def _extract_fixed_goal_events(self, events_data):
        """Extract goal events with proper data handling"""
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
                    'time_interval': self._get_time_interval(total_minute)
                }
                goals.append(goal_data)
        
        return sorted(goals, key=lambda x: x.get('total_minute', 0))
    
    def _extract_fixed_team_stats(self, stats_data, event_data):
        """Extract team statistics with fallback strategies"""
        team_stats = {'home': {}, 'away': {}}
        
        # Try to get stats from statistics endpoint
        if stats_data and 'statistics' in stats_data:
            home_poss, away_poss = extract_possession_from_stats(stats_data)
            if home_poss is not None:
                team_stats['home']['possession_percentage'] = home_poss
                team_stats['away']['possession_percentage'] = away_poss
            
            # Extract other statistics
            for period in stats_data['statistics']:
                if period.get('period') == 'ALL':
                    for group in period.get('groups', []):
                        for stat in group.get('statisticsItems', []):
                            self._map_statistic(stat, team_stats)
        
        # Fallback: try to get basic stats from event data
        if not team_stats['home'] and event_data:
            # Some basic stats might be in the main event
            team_stats['home']['shots_on_target'] = safe_get_nested(event_data, ['homeScore', 'normaltime'])
            team_stats['away']['shots_on_target'] = safe_get_nested(event_data, ['awayScore', 'normaltime'])
        
        return team_stats
    
    def _map_statistic(self, stat, team_stats):
        """Map API statistics to database fields"""
        stat_name = stat.get('name', '').lower()
        home_value = stat.get('home')
        away_value = stat.get('away')
        
        mapping = {
            'ball possession': 'possession_percentage',
            'possession': 'possession_percentage',
            'shots on target': 'shots_on_target',
            'shots': 'total_shots',
            'total shots': 'total_shots',
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
    
    def _extract_fixed_player_stats(self, lineups_data, events_data):
        """Extract player statistics with proper handling"""
        if not lineups_data:
            return []
        
        players = []
        
        for side in ['home', 'away']:
            if side in lineups_data:
                # Starters
                for player in lineups_data[side].get('players', []):
                    player_data = self._extract_player_data(player, side, True, events_data)
                    if player_data:
                        players.append(player_data)
                
                # Substitutes
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
            
            # Count player events
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
                'minutes_played': None,  # Would need live tracking
                'shots_on_target': None  # Not available in lineups
            }
        except Exception as e:
            self.logger.error(f"Error extracting player data: {e}")
            return None
    
    def _count_player_events(self, player_id, events_data):
        """Count goals, assists, and cards for a player"""
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
    
    def scrape_all_live_matches_comprehensive(self):
        """Scrape all live matches with comprehensive data"""
        live_matches = self.get_live_matches()
        comprehensive_data = []
        
        for match in live_matches:
            match_id = match.get('match_id')
            if match_id:
                details = self.get_match_comprehensive_details(match_id)
                if details:
                    comprehensive_data.append(details)
        
        return comprehensive_data
    
    def to_comprehensive_dataframes(self, live_data):
        """Convert to DataFrames with proper null handling"""
        dataframes = {}
        
        all_matches = []
        all_goals = []
        all_players = []
        all_team_stats = []
        
        for match in live_data:
            match_info = match.get('match_details', {})
            if match_info:
                all_matches.append(match_info)
                
                # Add match context to goals
                for goal in match.get('goal_events', []):
                    goal_data = goal.copy()
                    goal_data['match_id'] = match_info.get('match_id')
                    goal_data['competition'] = match_info.get('competition')
                    all_goals.append(goal_data)
                
                # Add match context to players
                for player in match.get('player_statistics', []):
                    player_data = player.copy()
                    player_data['match_id'] = match_info.get('match_id')
                    player_data['competition'] = match_info.get('competition')
                    all_players.append(player_data)
                
                # Process team statistics
                team_stats = match.get('team_statistics', {})
                for side in ['home', 'away']:
                    if side in team_stats and team_stats[side]:
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
