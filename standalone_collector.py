#!/usr/bin/env python3
"""
Standalone Late Goal Data Collector
Self-contained collector that doesn't depend on other modules
"""

import requests
import time
import json
import pandas as pd
from datetime import datetime
import os
import logging

class StandaloneCollector:
    """Self-contained data collector"""
    
    def __init__(self):
        self.base_url = "https://api.sofascore.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.sofascore.com',
            'Referer': 'https://www.sofascore.com/',
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def make_request(self, url, max_retries=3):
        """Make API request with retry logic"""
        for attempt in range(max_retries):
            try:
                time.sleep(1.5)  # Rate limiting
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
        return None
    
    def get_live_matches(self):
        """Get live football matches"""
        url = f"{self.base_url}/sport/football/events/live"
        return self.make_request(url)
    
    def get_match_details(self, match_id):
        """Get detailed match information"""
        url = f"{self.base_url}/event/{match_id}"
        return self.make_request(url)
    
    def get_match_statistics(self, match_id):
        """Get match statistics"""
        url = f"{self.base_url}/event/{match_id}/statistics"
        return self.make_request(url)
    
    def get_match_incidents(self, match_id):
        """Get match incidents (goals, cards, etc.)"""
        url = f"{self.base_url}/event/{match_id}/incidents"
        return self.make_request(url)
    
    def is_second_half_match(self, match_data):
        """Check if match is in second half"""
        try:
            status = match_data.get('status', {})
            status_type = status.get('type', '')
            
            # Skip finished matches
            if status_type == 'finished':
                return False
            
            # Check time info
            time_info = match_data.get('time', {})
            if time_info:
                period = time_info.get('period', 1)
                if period >= 2:  # Second half or later
                    return True
            
            # Check status description
            status_desc = status.get('description', '').lower()
            if any(keyword in status_desc for keyword in ['2nd half', 'second half', '2h']):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking match period: {e}")
            return False
    
    def extract_match_data(self, match_event):
        """Extract basic match data from event"""
        try:
            # Basic info
            match_id = match_event.get('id')
            home_team = match_event.get('homeTeam', {}).get('name', 'Unknown')
            away_team = match_event.get('awayTeam', {}).get('name', 'Unknown')
            
            # Score
            home_score = match_event.get('homeScore', {}).get('current', 0)
            away_score = match_event.get('awayScore', {}).get('current', 0)
            
            # Competition
            tournament = match_event.get('tournament', {})
            competition = tournament.get('name', 'Unknown')
            
            # Time info
            time_info = match_event.get('time', {})
            period = time_info.get('period', 1)
            
            # Status
            status = match_event.get('status', {})
            status_desc = status.get('description', 'Unknown')
            
            return {
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'competition': competition,
                'period': period,
                'status': status_desc,
                'collection_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting match data: {e}")
            return None
    
    def collect_detailed_data(self, match_id):
        """Collect detailed data for a specific match"""
        try:
            self.logger.info(f"Collecting detailed data for match {match_id}")
            
            # Get match details
            match_data = self.get_match_details(match_id)
            if not match_data:
                return None
            
            event = match_data.get('event', {})
            
            # Get statistics
            stats_data = self.get_match_statistics(match_id)
            
            # Get incidents (goals)
            incidents_data = self.get_match_incidents(match_id)
            
            # Extract basic info
            basic_data = self.extract_match_data(event)
            if not basic_data:
                return None
            
            # Add venue if available
            venue = event.get('venue', {})
            basic_data['venue'] = venue.get('name', 'Unknown') if venue else 'Unknown'
            
            # Process statistics
            if stats_data and 'statistics' in stats_data:
                self.add_statistics_to_data(basic_data, stats_data['statistics'])
            
            # Process goals
            if incidents_data and 'incidents' in incidents_data:
                self.add_goal_data(basic_data, incidents_data['incidents'])
            
            return basic_data
            
        except Exception as e:
            self.logger.error(f"Error collecting detailed data for match {match_id}: {e}")
            return None
    
    def add_statistics_to_data(self, data, statistics):
        """Add team statistics to match data"""
        try:
            for period in statistics:
                if period.get('period') == 'ALL':
                    for group in period.get('groups', []):
                        for stat in group.get('statisticsItems', []):
                            stat_name = stat.get('name', '').lower()
                            
                            if 'possession' in stat_name:
                                data['home_possession'] = stat.get('home', 0)
                                data['away_possession'] = stat.get('away', 0)
                            elif 'shots on target' in stat_name:
                                data['home_shots_on_target'] = stat.get('home', 0)
                                data['away_shots_on_target'] = stat.get('away', 0)
                            elif 'total shots' in stat_name or stat_name == 'shots':
                                data['home_shots'] = stat.get('home', 0)
                                data['away_shots'] = stat.get('away', 0)
                            elif 'corner' in stat_name:
                                data['home_corners'] = stat.get('home', 0)
                                data['away_corners'] = stat.get('away', 0)
                            elif 'fouls' in stat_name:
                                data['home_fouls'] = stat.get('home', 0)
                                data['away_fouls'] = stat.get('away', 0)
                            elif 'yellow cards' in stat_name:
                                data['home_yellow_cards'] = stat.get('home', 0)
                                data['away_yellow_cards'] = stat.get('away', 0)
                            elif 'red cards' in stat_name:
                                data['home_red_cards'] = stat.get('home', 0)
                                data['away_red_cards'] = stat.get('away', 0)
            
            # Add defaults for missing stats
            defaults = {
                'home_possession': 50, 'away_possession': 50,
                'home_shots': 0, 'away_shots': 0,
                'home_shots_on_target': 0, 'away_shots_on_target': 0,
                'home_corners': 0, 'away_corners': 0,
                'home_fouls': 0, 'away_fouls': 0,
                'home_yellow_cards': 0, 'away_yellow_cards': 0,
                'home_red_cards': 0, 'away_red_cards': 0
            }
            
            for key, default_value in defaults.items():
                if key not in data:
                    data[key] = default_value
                    
        except Exception as e:
            self.logger.error(f"Error adding statistics: {e}")
    
    def add_goal_data(self, data, incidents):
        """Add goal-related data"""
        try:
            goals = [inc for inc in incidents if inc.get('incidentType') == 'goal']
            
            data['total_goals'] = len(goals)
            data['goals_75_plus'] = len([g for g in goals if g.get('time', 0) >= 75])
            data['goals_80_plus'] = len([g for g in goals if g.get('time', 0) >= 80])
            data['goals_85_plus'] = len([g for g in goals if g.get('time', 0) >= 85])
            data['has_late_goal'] = data['goals_75_plus'] > 0
            
            # Calculate minutes since last goal
            if goals:
                goal_times = [g.get('time', 0) for g in goals]
                last_goal_time = max(goal_times)
                current_time = 90  # Approximate current time
                data['minutes_since_last_goal'] = current_time - last_goal_time
            else:
                data['minutes_since_last_goal'] = 90
                
        except Exception as e:
            self.logger.error(f"Error adding goal data: {e}")
    
    def collect_second_half_matches(self):
        """Collect all current second-half matches"""
        print("🔍 Collecting second-half matches...")
        
        # Get live matches
        live_data = self.get_live_matches()
        if not live_data:
            print("   ❌ No live match data received")
            return []
        
        events = live_data.get('events', [])
        print(f"   Found {len(events)} live matches")
        
        # Filter for second-half matches
        second_half_matches = []
        for event in events:
            if self.is_second_half_match(event):
                second_half_matches.append(event)
        
        print(f"   {len(second_half_matches)} are in second half")
        
        if not second_half_matches:
            print("   ℹ️  No second-half matches currently")
            return []
        
        # Display matches
        print("\n⚽ SECOND-HALF MATCHES:")
        for event in second_half_matches:
            home_team = event.get('homeTeam', {}).get('name', 'Unknown')
            away_team = event.get('awayTeam', {}).get('name', 'Unknown')
            home_score = event.get('homeScore', {}).get('current', 0)
            away_score = event.get('awayScore', {}).get('current', 0)
            
            print(f"   • {home_team} {home_score}-{away_score} {away_team}")
        
        # Collect detailed data
        print(f"\n📊 Collecting detailed data...")
        detailed_data = []
        
        for i, event in enumerate(second_half_matches[:5]):  # Limit to 5 matches
            match_id = event.get('id')
            if match_id:
                print(f"   Processing match {i+1}/{min(len(second_half_matches), 5)}: {match_id}")
                
                detailed_match = self.collect_detailed_data(match_id)
                if detailed_match:
                    detailed_data.append(detailed_match)
                    print(f"     ✅ Success")
                else:
                    print(f"     ❌ Failed")
        
        return detailed_data
    
    def export_data(self, data):
        """Export data to CSV"""
        if not data:
            print("No data to export")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'exports/standalone_late_goal_{timestamp}.csv'
        
        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)
        
        # Convert to DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
        print(f"\n💾 Data exported to: {filename}")
        print(f"   Records: {len(data)}")
        print(f"   Columns: {len(df.columns)}")
        
        # Show summary
        if len(data) > 0:
            late_goals = sum(1 for record in data if record.get('has_late_goal'))
            print(f"   Late goals: {late_goals}/{len(data)} matches")
        
        return filename

def main():
    """Main function"""
    collector = StandaloneCollector()
    
    print("🎯 Standalone Late Goal Data Collector")
    print("=" * 45)
    print("This collector works independently of other modules")
    print()
    
    # Collect data
    data = collector.collect_second_half_matches()
    
    if not data:
        print("\n⚠️  No data collected")
        print("   This is normal if no matches are in second half")
        print("   Try running during peak football hours")
        return
    
    # Export data
    filename = collector.export_data(data)
    
    if filename:
        print(f"\n✅ Collection completed successfully!")
        print(f"   Check the CSV file for your data")
        print(f"   File: {filename}")
        
        # Show sample data
        print(f"\n📋 Sample Data:")
        for i, record in enumerate(data[:2]):
            print(f"   Match {i+1}: {record.get('home_team')} vs {record.get('away_team')}")
            print(f"     Score: {record.get('home_score')}-{record.get('away_score')}")
            print(f"     Late goals: {record.get('goals_75_plus', 0)}")
            print(f"     Possession: {record.get('home_possession', 0):.1f}% - {record.get('away_possession', 0):.1f}%")

if __name__ == "__main__":
    main()