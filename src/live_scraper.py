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
        
        # Get player statistics (if available)
        player_stats_url = f"{self.base_url}/event/{match_id}/player-statistics"
        player_stats_data = make_api_request(player_stats_url, delay=self.delay)
        
        return self._compile_comprehensive_match_data(
            match_data, stats_data, events_data, lineups_data, player_stats_data
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
    
    def _compile_comprehensive_match_data(self, match_data, stats_data, events_data, lineups_data, player_stats_data):
        """Compile all match data with comprehensive field extraction"""
        if not match_data:
            return None
        
        event = match_data.get('event', {})
        
        compiled_data = {
            'match_details': self._extract_comprehensive_match_info(event),
            'goal_events': self._extract_comprehensive_goal_events(events_data),
            'team_statistics': self._extract_comprehensive_team_stats(stats_data),
            'player_statistics': self._extract_comprehensive_player_stats(lineups_data, events_data, player_stats_data),
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
                # Extract comprehensive goal data
                goal_data = {
                    'goal_id': incident.get('id'),
                    'timestamp_minute': incident.get('time'),
                    'added_time': incident.get('addedTime', 0),
                    'total_minute': incident.get('time', 0) + incident.get('addedTime', 0),
                    'exact_timestamp': incident.get('time'),  # Exact minute timestamp
                    
                    # Goal Types
                    'goal_type': incident.get('goalType', 'regular'),  # regular, penalty, ownGoal, etc.
                    'is_penalty': incident.get('goalType') == 'penalty',
                    'is_own_goal': incident.get('goalType') == 'ownGoal',
                    
                    # Players
                    'scoring_player': incident.get('player', {}).get('name') if incident.get('player') else None,
                    'scoring_player_id': incident.get('player', {}).get('id') if incident.get('player') else None,
                    'assisting_player': incident.get('assist1', {}).get('name') if incident.get('assist1') else None,
                    'assisting_player_id': incident.get('assist1', {}).get('id') if incident.get('assist1') else None,
                    
                    # Goal Details
                    'goal_type': incident.get('goalType', 'regular'),
                    'team_side': incident.get('teamSide'),  # 'home' or 'away'
                    'description': incident.get('text'),
                    
                    # Time Analysis
                    'period': 1 if incident.get('time', 0) <= 45 else 2,
                    'is_first_half': incident.get('time', 0) <= 45,
                    'is_second_half': incident.get('time', 0) > 45,
                    'is_late_goal': self._is_late_goal(incident.get('time', 0), incident.get('addedTime', 0)),
                    'time_interval': self._get_time_interval(incident.get('time', 0), incident.get('addedTime', 0)),
                    'is_last_15_minutes': self._is_last_15_minutes(incident.get('time', 0), incident.get('addedTime', 0))
                }
                goals.append(goal_data)
        
        return sorted(goals, key=lambda x: x.get('total_minute', 0))
    
    def _extract_comprehensive_final_stats(self, stats_data):
        """Extract comprehensive final match statistics"""
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
                        
                        # Comprehensive team statistics mapping
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
    
    def _analyze_goal_timing(self, events_data):
        """
        Analyze goal frequency in different time intervals
        
        Args:
            events_data (dict): Events data from API
            
        Returns:
            dict: Goal frequency analysis
        """
        if not events_data or 'incidents' not in events_data:
            return {}
        
        goals = []
        for incident in events_data['incidents']:
            if incident.get('incidentType') == 'goal':
                total_minute = incident.get('time', 0) + incident.get('addedTime', 0)
                goals.append(total_minute)
        
        if not goals:
            return {}
        
        # Analyze goal distribution
        analysis = {
            'total_goals': len(goals),
            'goals_by_interval': self._analyze_goals_by_15min_intervals(goals),
            'goals_by_half': self._analyze_goals_by_half(goals),
            'late_goals_analysis': self._analyze_late_goals(goals),
            'goal_minutes': goals
        }
        
        return analysis
    
    def _analyze_goals_by_15min_intervals(self, goal_minutes):
        """Analyze goals by 15-minute intervals"""
        intervals = {
            '0-15': 0, '16-30': 0, '31-45': 0, '46-60': 0,
            '61-75': 0, '76-90': 0, '90+': 0
        }
        
        for minute in goal_minutes:
            if minute <= 15:
                intervals['0-15'] += 1
            elif minute <= 30:
                intervals['16-30'] += 1
            elif minute <= 45:
                intervals['31-45'] += 1
            elif minute <= 60:
                intervals['46-60'] += 1
            elif minute <= 75:
                intervals['61-75'] += 1
            elif minute <= 90:
                intervals['76-90'] += 1
            else:
                intervals['90+'] += 1
        
        return intervals
    
    def _analyze_goals_by_half(self, goal_minutes):
        """Analyze goals by match halves"""
        halves = {'first_half': 0, 'second_half': 0, 'extra_time': 0}
        
        for minute in goal_minutes:
            if minute <= 45:
                halves['first_half'] += 1
            elif minute <= 90:
                halves['second_half'] += 1
            else:
                halves['extra_time'] += 1
        
        return halves
    
    def _analyze_late_goals(self, goal_minutes):
        """Analyze late goals specifically"""
        late_goals = [m for m in goal_minutes if m >= 75]
        last_15_first_half = [m for m in goal_minutes if 30 <= m <= 45]
        
        return {
            'late_goals_count': len(late_goals),
            'late_goals_percentage': (len(late_goals) / len(goal_minutes)) * 100 if goal_minutes else 0,
            'last_15_first_half': len(last_15_first_half),
            'last_15_second_half': len(late_goals),
            'goals_after_90': len([m for m in goal_minutes if m > 90])
        }
    
    def _extract_all_historical_events(self, events_data):
        """Extract all historical match events"""
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
    
    def _is_last_15_minutes(self, minute, added_time):
        """Check if goal is in last 15 minutes of any half"""
        total_minute = minute + added_time
        return (30 <= total_minute <= 45) or (total_minute >= 75)
    
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
    
    def scrape_historical_comprehensive(self, days_back=7, specific_matches=None):
        """
        Comprehensive historical data scraping with enhanced data extraction
        
        Args:
            days_back (int): Number of days to look back
            specific_matches (list): List of specific match IDs to scrape
            
        Returns:
            dict: Comprehensive historical data
        """
        historical_data = {
            'recent_matches': [],
            'specific_matches': [],
            'comprehensive_goal_analysis': {}
        }
        
        # Try to get recent completed matches
        if days_back > 0:
            recent_matches = self.get_recent_completed_matches(days_back)
            
            # Get detailed data for each completed match
            for match in recent_matches[:20]:  # Limit to prevent API overload
                match_id = match.get('match_id')
                if match_id:
                    details = self.get_match_comprehensive_historical_details(match_id)
                    if details:
                        historical_data['recent_matches'].append(details)
        
        # Scrape specific matches if provided
        if specific_matches:
            for match_id in specific_matches:
                details = self.get_match_comprehensive_historical_details(match_id)
                if details:
                    historical_data['specific_matches'].append(details)
        
        # Perform comprehensive goal timing analysis
        all_matches = historical_data['recent_matches'] + historical_data['specific_matches']
        if all_matches:
            historical_data['comprehensive_goal_analysis'] = self._comprehensive_goal_analysis(all_matches)
        
        return historical_data
    
    def _comprehensive_goal_analysis(self, matches_data):
        """Perform comprehensive goal timing analysis across all matches"""
        all_goals = []
        match_goal_data = []
        
        for match in matches_data:
            match_info = match.get('match_details', {})
            goals = match.get('goal_events', [])
            goal_frequency = match.get('goal_frequency_analysis', {})
            
            # Collect all goals with match context
            for goal in goals:
                goal_analysis = goal.copy()
                goal_analysis['match_id'] = match_info.get('match_id')
                goal_analysis['competition'] = match_info.get('competition')
                all_goals.append(goal_analysis)
            
            # Collect match-level goal data
            if goals:
                match_goal_data.append({
                    'match_id': match_info.get('match_id'),
                    'total_goals': len(goals),
                    'late_goals': len([g for g in goals if g.get('is_late_goal')]),
                    'goal_intervals': goal_frequency.get('goals_by_interval', {}),
                    'competition': match_info.get('competition')
                })
        
        if not all_goals:
            return {}
        
        # Calculate comprehensive statistics
        late_goals = [g for g in all_goals if g.get('is_late_goal')]
        goal_minutes = [g['total_minute'] for g in all_goals]
        
        comprehensive_analysis = {
            'total_matches_analyzed': len(matches_data),
            'total_goals_analyzed': len(all_goals),
            'late_goals_count': len(late_goals),
            'late_goals_percentage': (len(late_goals) / len(all_goals)) * 100 if all_goals else 0,
            'average_goals_per_match': len(all_goals) / len(matches_data) if matches_data else 0,
            'average_goal_minute': sum(goal_minutes) / len(goal_minutes) if goal_minutes else 0,
            
            # Distribution Analysis
            'goals_by_15min_intervals': self._analyze_goals_by_15min_intervals(goal_minutes),
            'goals_by_half': self._analyze_goals_by_half(goal_minutes),
            'late_goals_detailed': self._analyze_late_goals(goal_minutes),
            
            # Match-level analysis
            'matches_with_late_goals': len([m for m in match_goal_data if m['late_goals'] > 0]),
            'percentage_matches_with_late_goals': (len([m for m in match_goal_data if m['late_goals'] > 0]) / len(match_goal_data)) * 100 if match_goal_data else 0
        }
        
        return comprehensive_analysis
    
    def to_comprehensive_dataframes(self, historical_data):
        """
        Convert comprehensive historical data to organized pandas DataFrames
        
        Args:
            historical_data (dict): Historical data from scraping
            
        Returns:
            dict: Dictionary of comprehensive DataFrames
        """
        dataframes = {}
        
        all_matches = []
        all_goals = []
        all_events = []
        all_team_stats = []
        
        # Process all matches
        for match_type in ['recent_matches', 'specific_matches']:
            for match in historical_data.get(match_type, []):
                match_info = match.get('match_details', {})
                all_matches.append(match_info)
                
                # Goals with comprehensive data
                for goal in match.get('goal_events', []):
                    goal_data = goal.copy()
                    goal_data['match_id'] = match_info.get('match_id')
                    goal_data['competition'] = match_info.get('competition')
                    goal_data['home_team'] = match_info.get('home_team')
                    goal_data['away_team'] = match_info.get('away_team')
                    all_goals.append(goal_data)
                
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
        dataframes['team_statistics'] = pd.DataFrame(all_team_stats)
        dataframes['all_events'] = pd.DataFrame(all_events)
        
        # Add comprehensive goal analysis
        if 'comprehensive_goal_analysis' in historical_data:
            analysis_df = pd.DataFrame([historical_data['comprehensive_goal_analysis']])
            dataframes['goal_frequency_analysis'] = analysis_df
        
        return dataframes
