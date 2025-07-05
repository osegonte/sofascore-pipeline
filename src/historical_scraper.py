"""
Historical Data Scraper for SofaScore Data Collection Pipeline
Fetches past match results and historical events for analysis
"""

import logging
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add config to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import SOFASCORE_BASE_URL, RATE_LIMIT_DELAY

# Local imports
from utils import make_api_request, setup_logging

class HistoricalScraper:
    """Scraper for historical match data from SofaScore API"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = SOFASCORE_BASE_URL
        self.delay = RATE_LIMIT_DELAY
        
    def get_historical_matches_by_date(self, date_str):
        """
        Fetch completed matches for a specific date
        
        Args:
            date_str (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            list: List of completed match data
        """
        self.logger.info(f"Fetching historical matches for date: {date_str}")
        
        url = f"{self.base_url}/sport/football/events/{date_str}"
        data = make_api_request(url, delay=self.delay)
        
        if not data:
            self.logger.warning(f"No historical data received for {date_str}")
            return []
        
        matches = []
        events = data.get('events', [])
        
        for event in events:
            # Only process finished matches
            if event.get('status', {}).get('type') == 'finished':
                match_data = self._extract_historical_match_info(event)
                if match_data:
                    matches.append(match_data)
        
        self.logger.info(f"Found {len(matches)} completed matches for {date_str}")
        return matches
    
    def get_historical_range(self, start_date, end_date):
        """
        Fetch historical matches for a date range
        
        Args:
            start_date (str): Start date 'YYYY-MM-DD'
            end_date (str): End date 'YYYY-MM-DD'
            
        Returns:
            list: List of all historical matches in range
        """
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
        
        self.logger.info(f"Total historical matches found: {len(all_matches)}")
        return all_matches
    
    def get_match_historical_details(self, match_id):
        """
        Fetch detailed historical data for a specific match
        
        Args:
            match_id (int): SofaScore match ID
            
        Returns:
            dict: Detailed historical match data with goal timestamps
        """
        self.logger.info(f"Fetching historical details for match {match_id}")
        
        # Get basic match info
        match_url = f"{self.base_url}/event/{match_id}"
        match_data = make_api_request(match_url, delay=self.delay)
        
        if not match_data:
            return None
        
        # Get match events for goal timestamps
        events_url = f"{self.base_url}/event/{match_id}/incidents"
        events_data = make_api_request(events_url, delay=self.delay)
        
        # Get match statistics
        stats_url = f"{self.base_url}/event/{match_id}/statistics"
        stats_data = make_api_request(stats_url, delay=self.delay)
        
        return self._compile_historical_details(match_data, events_data, stats_data)
    
    def _extract_historical_match_info(self, event):
        """Extract basic historical match information"""
        try:
            start_timestamp = event.get('startTimestamp')
            start_time = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            
            return {
                'match_id': event.get('id'),
                'home_team': event.get('homeTeam', {}).get('name'),
                'home_team_id': event.get('homeTeam', {}).get('id'),
                'away_team': event.get('awayTeam', {}).get('name'),
                'away_team_id': event.get('awayTeam', {}).get('id'),
                'home_score_final': event.get('homeScore', {}).get('current', 0),
                'away_score_final': event.get('awayScore', {}).get('current', 0),
                'home_score_ht': event.get('homeScore', {}).get('period1', 0),
                'away_score_ht': event.get('awayScore', {}).get('period1', 0),
                'match_date': start_time.date().isoformat() if start_time else None,
                'kickoff_time': start_time.isoformat() if start_time else None,
                'tournament': event.get('tournament', {}).get('name'),
                'tournament_id': event.get('tournament', {}).get('id'),
                'round_info': event.get('roundInfo', {}).get('name'),
                'status': event.get('status', {}).get('description'),
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting historical match info: {e}")
            return None
    
    def _compile_historical_details(self, match_data, events_data, stats_data):
        """Compile detailed historical match data"""
        if not match_data:
            return None
        
        event = match_data.get('event', {})
        
        compiled_data = {
            'match_info': self._extract_historical_match_info(event),
            'goal_events': self._extract_goal_timestamps(events_data),
            'all_events': self._extract_all_events(events_data),
            'final_stats': self._extract_final_stats(stats_data)
        }
        
        return compiled_data
    
    def _extract_goal_timestamps(self, events_data):
        """
        Extract goal events with precise timestamps for late-goal analysis
        
        Args:
            events_data (dict): Events data from API
            
        Returns:
            list: List of goal events with timestamps
        """
        if not events_data or 'incidents' not in events_data:
            return []
        
        goals = []
        
        for incident in events_data['incidents']:
            if incident.get('incidentType') == 'goal':
                goal_data = {
                    'goal_id': incident.get('id'),
                    'minute': incident.get('time'),
                    'added_time': incident.get('addedTime', 0),
                    'total_minute': incident.get('time', 0) + incident.get('addedTime', 0),
                    'team_side': incident.get('teamSide'),  # 'home' or 'away'
                    'player_name': incident.get('player', {}).get('name') if incident.get('player') else None,
                    'player_id': incident.get('player', {}).get('id') if incident.get('player') else None,
                    'goal_type': incident.get('goalType'),  # e.g., 'regular', 'penalty', 'ownGoal'
                    'assist_player': incident.get('assist1', {}).get('name') if incident.get('assist1') else None,
                    'is_late_goal': self._is_late_goal(incident.get('time', 0), incident.get('addedTime', 0)),
                    'period': incident.get('time', 0) // 45 + 1  # Approximate period
                }
                goals.append(goal_data)
        
        return sorted(goals, key=lambda x: x.get('total_minute', 0))
    
    def _is_late_goal(self, minute, added_time):
        """
        Determine if a goal is considered a 'late goal'
        
        Args:
            minute (int): Goal minute
            added_time (int): Added time minutes
            
        Returns:
            bool: True if considered a late goal
        """
        total_minute = minute + added_time
        
        # Define late goals as:
        # - Last 15 minutes of first half (30+ minutes)
        # - Last 15 minutes of second half (75+ minutes)
        # - Any goal in extra time (90+ minutes)
        
        return (
            (30 <= total_minute <= 45) or  # Late first half
            (total_minute >= 75)           # Late second half or extra time
        )
    
    def _extract_all_events(self, events_data):
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
                'description': incident.get('text')
            }
            events.append(event)
        
        return sorted(events, key=lambda x: x.get('total_minute', 0))
    
    def _extract_final_stats(self, stats_data):
        """Extract final match statistics"""
        if not stats_data or 'statistics' not in stats_data:
            return {}
        
        final_stats = {}
        
        for period in stats_data['statistics']:
            if period.get('period') == 'ALL':
                groups = period.get('groups', [])
                
                for group in groups:
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower().replace(' ', '_')
                        final_stats[f'home_{stat_name}'] = stat.get('home')
                        final_stats[f'away_{stat_name}'] = stat.get('away')
        
        return final_stats
    
    def analyze_goal_timing_patterns(self, matches_data):
        """
        Analyze goal timing patterns from historical data
        
        Args:
            matches_data (list): List of historical matches with goal data
            
        Returns:
            dict: Goal timing analysis results
        """
        all_goals = []
        
        for match in matches_data:
            match_id = match.get('match_info', {}).get('match_id')
            goals = match.get('goal_events', [])
            
            for goal in goals:
                goal_analysis = goal.copy()
                goal_analysis['match_id'] = match_id
                all_goals.append(goal_analysis)
        
        if not all_goals:
            return {}
        
        # Calculate goal timing statistics
        goal_minutes = [goal['total_minute'] for goal in all_goals]
        late_goals = [goal for goal in all_goals if goal.get('is_late_goal')]
        
        analysis = {
            'total_goals': len(all_goals),
            'late_goals_count': len(late_goals),
            'late_goals_percentage': (len(late_goals) / len(all_goals)) * 100 if all_goals else 0,
            'average_goal_minute': sum(goal_minutes) / len(goal_minutes) if goal_minutes else 0,
            'goals_by_period': self._analyze_goals_by_period(all_goals),
            'goals_by_15min_intervals': self._analyze_goals_by_intervals(all_goals)
        }
        
        return analysis
    
    def _analyze_goals_by_period(self, goals):
        """Analyze goal distribution by match periods"""
        periods = {'first_half': 0, 'second_half': 0, 'extra_time': 0}
        
        for goal in goals:
            minute = goal.get('total_minute', 0)
            if minute <= 45:
                periods['first_half'] += 1
            elif minute <= 90:
                periods['second_half'] += 1
            else:
                periods['extra_time'] += 1
        
        return periods
    
    def _analyze_goals_by_intervals(self, goals):
        """Analyze goals by 15-minute intervals"""
        intervals = {
            '0-15': 0, '16-30': 0, '31-45': 0, '46-60': 0,
            '61-75': 0, '76-90': 0, '90+': 0
        }
        
        for goal in goals:
            minute = goal.get('total_minute', 0)
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
    
    def scrape_historical_comprehensive(self, days_back=30, specific_matches=None):
        """
        Comprehensive historical data scraping
        
        Args:
            days_back (int): Number of days to look back
            specific_matches (list): List of specific match IDs to scrape
            
        Returns:
            dict: Comprehensive historical data
        """
        historical_data = {
            'recent_matches': [],
            'specific_matches': [],
            'goal_analysis': {}
        }
        
        # Scrape recent matches
        if days_back > 0:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days_back)
            
            recent_matches = self.get_historical_range(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Get detailed data for each match
            for match in recent_matches[:50]:  # Limit to prevent API overload
                match_id = match.get('match_id')
                if match_id:
                    details = self.get_match_historical_details(match_id)
                    if details:
                        historical_data['recent_matches'].append(details)
        
        # Scrape specific matches
        if specific_matches:
            for match_id in specific_matches:
                details = self.get_match_historical_details(match_id)
                if details:
                    historical_data['specific_matches'].append(details)
        
        # Perform goal timing analysis
        all_matches = historical_data['recent_matches'] + historical_data['specific_matches']
        if all_matches:
            historical_data['goal_analysis'] = self.analyze_goal_timing_patterns(all_matches)
        
        return historical_data
    
    def to_dataframe(self, historical_data):
        """
        Convert historical data to pandas DataFrames
        
        Args:
            historical_data (dict): Historical data from scraping
            
        Returns:
            dict: Dictionary of DataFrames
        """
        dataframes = {}
        
        all_matches = []
        all_goals = []
        all_events = []
        
        # Process all matches
        for match_type in ['recent_matches', 'specific_matches']:
            for match in historical_data.get(match_type, []):
                match_info = match.get('match_info', {})
                all_matches.append(match_info)
                
                # Add goals with match context
                for goal in match.get('goal_events', []):
                    goal_data = goal.copy()
                    goal_data['match_id'] = match_info.get('match_id')
                    all_goals.append(goal_data)
                
                # Add all events with match context
                for event in match.get('all_events', []):
                    event_data = event.copy()
                    event_data['match_id'] = match_info.get('match_id')
                    all_events.append(event_data)
        
        dataframes['matches'] = pd.DataFrame(all_matches)
        dataframes['goals'] = pd.DataFrame(all_goals)
        dataframes['events'] = pd.DataFrame(all_events)
        
        # Add goal analysis as a separate summary
        if 'goal_analysis' in historical_data:
            analysis_df = pd.DataFrame([historical_data['goal_analysis']])
            dataframes['goal_analysis'] = analysis_df
        
        return dataframes
