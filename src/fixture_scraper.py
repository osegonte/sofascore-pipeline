"""
Fixture Scraper for SofaScore Data Collection Pipeline
Fetches upcoming match schedules and fixture data
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

class FixtureScraper:
    """Scraper for upcoming fixtures from SofaScore API"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.base_url = SOFASCORE_BASE_URL
        self.delay = RATE_LIMIT_DELAY
        
    def get_fixtures_by_date(self, date_str):
        """
        Fetch fixtures for a specific date
        
        Args:
            date_str (str): Date in format 'YYYY-MM-DD'
            
        Returns:
            list: List of fixture data dictionaries
        """
        self.logger.info(f"Fetching fixtures for date: {date_str}")
        
        url = f"{self.base_url}/sport/football/scheduled-events/{date_str}"
        data = make_api_request(url, delay=self.delay)
        
        if not data:
            self.logger.warning(f"No fixture data received for {date_str}")
            return []
        
        fixtures = []
        events = data.get('events', [])
        
        for event in events:
            fixture_data = self._extract_fixture_info(event)
            if fixture_data:
                fixtures.append(fixture_data)
        
        self.logger.info(f"Found {len(fixtures)} fixtures for {date_str}")
        return fixtures
    
    def get_upcoming_fixtures(self, days_ahead=7):
        """
        Fetch fixtures for the next N days
        
        Args:
            days_ahead (int): Number of days to look ahead
            
        Returns:
            list: List of all upcoming fixtures
        """
        self.logger.info(f"Fetching fixtures for next {days_ahead} days")
        
        all_fixtures = []
        current_date = datetime.now().date()
        
        for i in range(days_ahead):
            date = current_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            daily_fixtures = self.get_fixtures_by_date(date_str)
            all_fixtures.extend(daily_fixtures)
        
        self.logger.info(f"Total upcoming fixtures found: {len(all_fixtures)}")
        return all_fixtures
    
    def get_tournament_fixtures(self, tournament_id, season_id):
        """
        Fetch all fixtures for a specific tournament and season
        
        Args:
            tournament_id (int): SofaScore tournament ID
            season_id (int): SofaScore season ID
            
        Returns:
            list: List of tournament fixtures
        """
        self.logger.info(f"Fetching fixtures for tournament {tournament_id}, season {season_id}")
        
        url = f"{self.base_url}/unique-tournament/{tournament_id}/season/{season_id}/events/next/0"
        data = make_api_request(url, delay=self.delay)
        
        if not data:
            self.logger.warning(f"No tournament fixture data received")
            return []
        
        fixtures = []
        events = data.get('events', [])
        
        for event in events:
            fixture_data = self._extract_fixture_info(event)
            if fixture_data:
                fixture_data['tournament_id'] = tournament_id
                fixture_data['season_id'] = season_id
                fixtures.append(fixture_data)
        
        self.logger.info(f"Found {len(fixtures)} tournament fixtures")
        return fixtures
    
    def _extract_fixture_info(self, event):
        """
        Extract fixture information from event data
        
        Args:
            event (dict): Event data from API
            
        Returns:
            dict: Processed fixture data
        """
        try:
            start_timestamp = event.get('startTimestamp')
            start_time = datetime.fromtimestamp(start_timestamp) if start_timestamp else None
            
            return {
                'fixture_id': event.get('id'),
                'home_team': event.get('homeTeam', {}).get('name'),
                'home_team_id': event.get('homeTeam', {}).get('id'),
                'away_team': event.get('awayTeam', {}).get('name'),
                'away_team_id': event.get('awayTeam', {}).get('id'),
                'kickoff_time': start_time.isoformat() if start_time else None,
                'kickoff_date': start_time.date().isoformat() if start_time else None,
                'kickoff_time_formatted': start_time.strftime('%H:%M') if start_time else None,
                'tournament': event.get('tournament', {}).get('name'),
                'tournament_id': event.get('tournament', {}).get('id'),
                'round_info': event.get('roundInfo', {}).get('name'),
                'status': event.get('status', {}).get('description'),
                'venue': event.get('venue', {}).get('name') if event.get('venue') else None,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error extracting fixture info: {e}")
            return None
    
    def get_popular_tournaments(self):
        """
        Get list of popular football tournaments
        
        Returns:
            list: List of tournament data
        """
        self.logger.info("Fetching popular tournaments")
        
        url = f"{self.base_url}/sport/football/categories"
        data = make_api_request(url, delay=self.delay)
        
        if not data:
            return []
        
        tournaments = []
        categories = data.get('categories', [])
        
        for category in categories:
            for tournament in category.get('tournaments', []):
                tournaments.append({
                    'tournament_id': tournament.get('id'),
                    'tournament_name': tournament.get('name'),
                    'category': category.get('name'),
                    'country': category.get('alpha2')
                })
        
        return tournaments
    
    def scrape_fixtures_comprehensive(self, days_ahead=7, include_tournaments=None):
        """
        Comprehensive fixture scraping
        
        Args:
            days_ahead (int): Days to look ahead for general fixtures
            include_tournaments (list): List of (tournament_id, season_id) tuples
            
        Returns:
            dict: Dictionary with different types of fixtures
        """
        all_fixtures = {
            'upcoming_general': self.get_upcoming_fixtures(days_ahead),
            'tournament_specific': []
        }
        
        if include_tournaments:
            for tournament_id, season_id in include_tournaments:
                tournament_fixtures = self.get_tournament_fixtures(tournament_id, season_id)
                all_fixtures['tournament_specific'].extend(tournament_fixtures)
        
        return all_fixtures
    
    def to_dataframe(self, fixtures_data):
        """
        Convert fixture data to pandas DataFrame
        
        Args:
            fixtures_data (list or dict): Fixture data
            
        Returns:
            pd.DataFrame: DataFrame of fixtures
        """
        if isinstance(fixtures_data, dict):
            # Combine all fixture types
            all_fixtures = []
            for fixture_type, fixtures in fixtures_data.items():
                for fixture in fixtures:
                    fixture['source_type'] = fixture_type
                    all_fixtures.append(fixture)
            return pd.DataFrame(all_fixtures)
        
        return pd.DataFrame(fixtures_data)