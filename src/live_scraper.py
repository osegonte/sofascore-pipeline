"""
Enhanced Live Match Scraper for SofaScore Data Collection Pipeline
Captures comprehensive live match data including all required fields
"""

import logging
import sys
import os
from datetime import datetime
import pandas as pd

# Add config to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import SOFASCORE_BASE_URL, RATE_LIMIT_DELAY

# Local imports
from utils import make_api_request, setup_logging

class LiveMatchScraper:
    """Enhanced scraper for comprehensive live match data from SofaScore API"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = SOFASCORE_BASE_URL
        self.delay = RATE_LIMIT_DELAY
        
    def get_live_matches(self):
        """
        Fetch all currently live football matches
        
        Returns:
            list: List of live match data dictionaries
        """
        self.logger.info("Fetching live matches...")
        
        url = f"{self.base_url}/sport/football/events/live"
        data = make_api_request(url, delay=self.delay)
        
        if not data:
            self.logger.warning("No live match data received")
            return []
        
        live_matches = []
        events = data.get('events', [])
        
        for event in events:
            match_data = self._extract_comprehensive_match_info(event)
            if match_data:
                live_matches.append(match_data)
        
        self.logger.info(f"Found {len(live_matches)} live matches")
        return live_matches
    
    def get_match_comprehensive_details(self, match_id):
        """
        Fetch ALL required match information including detailed stats and events
        
        Args:
            match_id (int): SofaScore match ID
            
        Returns:
            dict: Complete match data with all required fields
        """
        self.logger.info(f"Fetching comprehensive details for match {match_id}")
        
        # Get basic match info
        match_url = f"{self.base_url}/event/{match_id}"
        match_data = make_api_request(match_url, delay=self.delay)
        
        if not match_data:
            return None
        
        # Get match statistics
        stats_url = f"{self.base_url}/event/{match_id}/statistics"
        stats_data = make_api_request(stats_url, delay=self.delay)
        
        # Get match events (goals, cards, etc.)
        events_url = f"{self.base_url}/event/{match_id}/incidents"
        events_data = make_api_request(events_url, delay=self.delay)
        
        # Get lineups for player stats
        lineups_url = f"{self.base_url}/event/{match_id}/lineups"
        lineups_data = make_api_request(lineups_url, delay=self.delay)
        
        return self._compile_comprehensive_match_data(
            match_data, stats_data, events_data, lineups_data
        )
    
    def _extract_comprehensive_match_info(self, event):
        """Extract comprehensive match information from event data"""
        try:
            start_timestamp = event.get('startTimestamp')
            start_time = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            
            # Extract current time info
            time_info = event.get('time', {})
            current_minute = time_info.get('currentPeriodStartTimestamp')
            
            return {
                # Match Details
                'match_id': event.get('id'),
                'competition': event.get('tournament', {}).get('name'),
                'league': event.get('tournament', {}).get('category', {}).get('name'),
                'date': start_time.date().isoformat() if start_time else None,
                'time': start_time.time().isoformat() if start_time else None,
                'datetime': start_time.isoformat() if start_time else None,
                'home_team': event.get('homeTeam', {}).get('name'),
                'away_team': event.get('awayTeam', {}).get('name'),
                'home_team_id': event.get('homeTeam', {}).get('id'),
                'away_team_id': event.get('awayTeam', {}).get('id'),
                'venue': event.get('venue', {}).get('name') if event.get('venue') else None,
                
                # Score & Time
                'home_score': event.get('homeScore', {}).get('current', 0),
                'away_score': event.get('awayScore', {}).get('current', 0),
                'minutes_elapsed': current_minute,
                'period': time_info.get('period'),
                'status': event.get('status', {}).get('description'),
                'status_type': event.get('status', {}).get('type'),
                
                # Meta
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting comprehensive match info: {e}")
            return None
    
    def _compile_comprehensive_match_data(self, match_data, stats_data, events_data, lineups_data):
        """Compile all match data with comprehensive field extraction"""
        if not match_data:
            return None
        
        event = match_data.get('event', {})
        
        compiled_data = {
            'match_details': self._extract_comprehensive_match_info(event),
            'goal_events': self._extract_comprehensive_goal_events(events_data),
            'team_statistics': self._extract_comprehensive_team_stats(stats_data),
            'player_statistics': self._extract_comprehensive_player_stats(lineups_data, events_data),
            'all_events': self._extract_all_match_events(events_data)
        }
        
        return compiled_data
    
    def _extract_comprehensive_goal_events(self, events_data):
        """Extract comprehensive goal events with all required fields"""
        if not events_data or 'incidents' not in events_data:
            return []
        
        goals = []
        
        for incident in events_data['incidents']:
            if incident.get('incidentType') == 'goal':
                goal_data = {
                    'goal_id': incident.get('id'),
                    'exact_timestamp': incident.get('time'),
                    'added_time': incident.get('addedTime', 0),
                    'total_minute': incident.get('time', 0) + incident.get('addedTime', 0),
                    
                    # Goal Types
                    'goal_type': incident.get('goalType', 'regular'),
                    'is_penalty': incident.get('goalType') == 'penalty',
                    'is_own_goal': incident.get('goalType') == 'ownGoal',
                    
                    # Players
                    'scoring_player': incident.get('player', {}).get('name') if incident.get('player') else None,
                    'scoring_player_id': incident.get('player', {}).get('id') if incident.get('player') else None,
                    'assisting_player': incident.get('assist1', {}).get('name') if incident.get('assist1') else None,
                    'assisting_player_id': incident.get('assist1', {}).get('id') if incident.get('assist1') else None,
                    
                    # Goal Details
                    'team_side': incident.get('teamSide'),  # 'home' or 'away'
                    'description': incident.get('text'),
                    
                    # Time Analysis
                    'period': 1 if incident.get('time', 0) <= 45 else 2,
                    'is_first_half': incident.get('time', 0) <= 45,
                    'is_second_half': incident.get('time', 0) > 45,
                    'is_late_goal': self._is_late_goal(incident.get('time', 0), incident.get('addedTime', 0)),
                    'time_interval': self._get_time_interval(incident.get('time', 0), incident.get('addedTime', 0))
                }
                goals.append(goal_data)
        
        return sorted(goals, key=lambda x: x.get('total_minute', 0))
    
    def _extract_comprehensive_team_stats(self, stats_data):
        """Extract comprehensive team statistics"""
        if not stats_data or 'statistics' not in stats_data:
            return {'home': {}, 'away': {}}
        
        team_stats = {'home': {}, 'away': {}}
        
        for period in stats_data['statistics']:
            if period.get('period') == 'ALL':
                groups = period.get('groups', [])
                
                for group in groups:
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower()
                        home_value = stat.get('home')
                        away_value = stat.get('away')
                        
                        # Map statistics to required fields
                        if 'ball possession' in stat_name or 'possession' in stat_name:
                            team_stats['home']['possession_percentage'] = home_value
                            team_stats['away']['possession_percentage'] = away_value
                        elif 'shots on target' in stat_name:
                            team_stats['home']['shots_on_target'] = home_value
                            team_stats['away']['shots_on_target'] = away_value
                        elif 'total shots' in stat_name or stat_name == 'shots':
                            team_stats['home']['total_shots'] = home_value
                            team_stats['away']['total_shots'] = away_value
                        elif 'corner kicks' in stat_name or 'corners' in stat_name:
                            team_stats['home']['corners'] = home_value
                            team_stats['away']['corners'] = away_value
                        elif 'fouls' in stat_name:
                            team_stats['home']['fouls'] = home_value
                            team_stats['away']['fouls'] = away_value
                        elif 'yellow cards' in stat_name:
                            team_stats['home']['yellow_cards'] = home_value
                            team_stats['away']['yellow_cards'] = away_value
                        elif 'red cards' in stat_name:
                            team_stats['home']['red_cards'] = home_value
                            team_stats['away']['red_cards'] = away_value
                        elif 'offsides' in stat_name or 'offside' in stat_name:
                            team_stats['home']['offsides'] = home_value
                            team_stats['away']['offsides'] = away_value
        
        return team_stats
    
    def _extract_comprehensive_player_stats(self, lineups_data, events_data):
        """Extract comprehensive player statistics"""
        if not lineups_data:
            return []
        
        players = []
        
        # Extract lineups
        for side in ['home', 'away']:
            if side not in lineups_data:
                continue
                
            # Starting XI
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
            player_id = player.get('player', {}).get('id')
            player_name = player.get('player', {}).get('name')
            
            # Count goals and assists from events
            goals = 0
            assists = 0
            cards = 0
            
            if events_data and 'incidents' in events_data:
                for incident in events_data['incidents']:
                    # Goals
                    if (incident.get('incidentType') == 'goal' and 
                        incident.get('player', {}).get('id') == player_id):
                        goals += 1
                    
                    # Assists
                    if (incident.get('incidentType') == 'goal' and 
                        incident.get('assist1', {}).get('id') == player_id):
                        assists += 1
                    
                    # Cards
                    if (incident.get('incidentType') in ['yellowCard', 'redCard'] and 
                        incident.get('player', {}).get('id') == player_id):
                        cards += 1
            
            return {
                'player_name': player_name,
                'player_id': player_id,
                'team_side': team_side,
                'position': player.get('position'),
                'jersey_number': player.get('shirtNumber'),
                'is_starter': is_starter,
                'goals': goals,
                'assists': assists,
                'cards_received': cards,
                'minutes_played': None,  # Would need live tracking
                'shots_on_target': None  # Would need detailed player stats endpoint
            }
        except Exception as e:
            self.logger.error(f"Error extracting player data: {e}")
            return None
    
    def _extract_all_match_events(self, events_data):
        """Extract all match events for comprehensive analysis"""
        if not events_data or 'incidents' not in events_data:
            return []
        
        events = []
        
        for incident in events_data['incidents']:
            event = {
                'event_id': incident.get('id'),
                'type': incident.get('incidentType'),
                'minute': incident.get('time'),
                'added_time': incident.get('addedTime', 0),
                'total_minute': incident.get('time', 0) + incident.get('addedTime', 0),
                'team_side': incident.get('teamSide'),
                'player_name': incident.get('player', {}).get('name') if incident.get('player') else None,
                'description': incident.get('text'),
                'period': 1 if incident.get('time', 0) <= 45 else 2
            }
            events.append(event)
        
        return sorted(events, key=lambda x: x.get('total_minute', 0))
    
    def _is_late_goal(self, minute, added_time):
        """Determine if a goal is considered a 'late goal'"""
        total_minute = minute + added_time
        return total_minute >= 75
    
    def _get_time_interval(self, minute, added_time):
        """Get time interval for goal"""
        total_minute = minute + added_time
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
        """
        Scrape comprehensive data for all live matches
        
        Returns:
            list: List of comprehensive match data
        """
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
        """
        Convert live data to organized pandas DataFrames
        
        Args:
            live_data (list): List of comprehensive match data
            
        Returns:
            dict: Dictionary of DataFrames for different data types
        """
        dataframes = {}
        
        all_matches = []
        all_goals = []
        all_players = []
        all_team_stats = []
        all_events = []
        
        for match in live_data:
            match_info = match.get('match_details', {})
            all_matches.append(match_info)
            
            # Goals with match context
            for goal in match.get('goal_events', []):
                goal_data = goal.copy()
                goal_data['match_id'] = match_info.get('match_id')
                goal_data['competition'] = match_info.get('competition')
                all_goals.append(goal_data)
            
            # Players with match context
            for player in match.get('player_statistics', []):
                player_data = player.copy()
                player_data['match_id'] = match_info.get('match_id')
                player_data['competition'] = match_info.get('competition')
                all_players.append(player_data)
            
            # Team statistics
            team_stats = match.get('team_statistics', {})
            for side in ['home', 'away']:
                if side in team_stats:
                    stats = team_stats[side].copy()
                    stats['match_id'] = match_info.get('match_id')
                    stats['team_side'] = side
                    stats['team_name'] = match_info.get(f'{side}_team')
                    stats['competition'] = match_info.get('competition')
                    all_team_stats.append(stats)
            
            # All events
            for event in match.get('all_events', []):
                event_data = event.copy()
                event_data['match_id'] = match_info.get('match_id')
                event_data['competition'] = match_info.get('competition')
                all_events.append(event_data)
        
        dataframes['match_details'] = pd.DataFrame(all_matches)
        dataframes['goal_events'] = pd.DataFrame(all_goals)
        dataframes['player_statistics'] = pd.DataFrame(all_players)
        dataframes['team_statistics'] = pd.DataFrame(all_team_stats)
        dataframes['all_events'] = pd.DataFrame(all_events)
        
        return dataframes