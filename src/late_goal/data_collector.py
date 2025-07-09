#!/usr/bin/env python3
"""
Simple Late Goal Data Collector
Basic data collection for testing and development
"""

import sys
import os
from datetime import datetime
import pandas as pd

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.live_scraper import LiveMatchScraper
from src.utils import setup_logging

class SimpleDataCollector:
    """Simple data collector for late goal prediction"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.scraper = LiveMatchScraper()
        
    def is_second_half_match(self, match_data):
        """Check if match is in second half"""
        try:
            period = match_data.get('period', 1)
            minutes_elapsed = match_data.get('minutes_elapsed', 0)
            status = match_data.get('status', '').lower()
            
            # Check if match is in second half
            if period >= 2:
                return True
            
            # Check if match is past 45 minutes
            if minutes_elapsed >= 45:
                return True
            
            # Check if it's live and likely in second half
            if 'live' in status and minutes_elapsed >= 45:
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking match period: {e}")
            return False
    
    def collect_current_second_half_matches(self):
        """Collect current second-half matches"""
        print("🔍 Collecting second-half matches...")
        
        try:
            # Get live matches
            live_matches = self.scraper.get_live_matches()
            
            if not live_matches:
                print("   No live matches found")
                return []
            
            print(f"   Found {len(live_matches)} live matches")
            
            # Filter for second-half matches
            second_half_matches = []
            for match in live_matches:
                if self.is_second_half_match(match):
                    second_half_matches.append(match)
            
            print(f"   {len(second_half_matches)} are in second half")
            
            # Display second-half matches
            if second_half_matches:
                print("\n⚽ SECOND-HALF MATCHES:")
                for match in second_half_matches:
                    home_team = match.get('home_team', 'Unknown')
                    away_team = match.get('away_team', 'Unknown')
                    home_score = match.get('home_score', 0)
                    away_score = match.get('away_score', 0)
                    minute = match.get('minutes_elapsed', 0)
                    
                    print(f"   • {home_team} {home_score}-{away_score} {away_team} ({minute}')")
            
            return second_half_matches
            
        except Exception as e:
            print(f"   ❌ Error collecting matches: {e}")
            return []
    
    def collect_detailed_data(self, matches):
        """Collect detailed data for matches"""
        if not matches:
            print("No matches to collect detailed data for")
            return []
        
        print(f"\n📊 Collecting detailed data for {len(matches)} matches...")
        
        detailed_data = []
        
        for i, match in enumerate(matches[:3]):  # Limit to first 3 for testing
            match_id = match.get('match_id')
            if not match_id:
                continue
            
            print(f"   Processing match {i+1}/{min(len(matches), 3)}: {match_id}")
            
            try:
                # Get comprehensive match details
                match_details = self.scraper.get_match_comprehensive_details(match_id)
                
                if match_details:
                    # Extract basic info
                    match_info = match_details.get('match_details', {})
                    goal_events = match_details.get('goal_events', [])
                    team_stats = match_details.get('team_statistics', {})
                    
                    # Create simplified record
                    record = {
                        'match_id': match_id,
                        'collection_timestamp': datetime.now().isoformat(),
                        'home_team': match_info.get('home_team'),
                        'away_team': match_info.get('away_team'),
                        'competition': match_info.get('competition'),
                        'current_minute': match_info.get('minutes_elapsed', 0),
                        'home_score': match_info.get('home_score', 0),
                        'away_score': match_info.get('away_score', 0),
                        'total_goals': match_info.get('home_score', 0) + match_info.get('away_score', 0),
                        'venue': match_info.get('venue'),
                        'status': match_info.get('status'),
                        
                        # Goal analysis
                        'total_goal_events': len(goal_events),
                        'late_goals_75_plus': len([g for g in goal_events if g.get('total_minute', 0) >= 75]),
                        'has_late_goal': len([g for g in goal_events if g.get('total_minute', 0) >= 75]) > 0,
                        
                        # Team stats
                        'home_possession': team_stats.get('home', {}).get('possession_percentage', 0),
                        'away_possession': team_stats.get('away', {}).get('possession_percentage', 0),
                        'home_shots': team_stats.get('home', {}).get('total_shots', 0),
                        'away_shots': team_stats.get('away', {}).get('total_shots', 0),
                        'home_shots_on_target': team_stats.get('home', {}).get('shots_on_target', 0),
                        'away_shots_on_target': team_stats.get('away', {}).get('shots_on_target', 0),
                    }
                    
                    detailed_data.append(record)
                    print(f"     ✅ Data collected successfully")
                    
                else:
                    print(f"     ❌ No detailed data available")
                    
            except Exception as e:
                print(f"     ❌ Error collecting detailed data: {e}")
        
        return detailed_data
    
    def export_data(self, data):
        """Export data to CSV"""
        if not data:
            print("No data to export")
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'exports/late_goal_test_{timestamp}.csv'
        
        # Ensure exports directory exists
        os.makedirs('exports', exist_ok=True)
        
        # Convert to DataFrame and export
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        
        print(f"\n💾 Data exported to: {filename}")
        print(f"   Records: {len(data)}")
        print(f"   Columns: {len(df.columns)}")
        
        # Show sample data
        print(f"\n📋 Sample Data:")
        for i, record in enumerate(data[:2]):
            print(f"   Match {i+1}: {record.get('home_team')} vs {record.get('away_team')}")
            print(f"     Score: {record.get('home_score')}-{record.get('away_score')} ({record.get('current_minute')}')")
            print(f"     Late goals: {record.get('late_goals_75_plus')}")
            print(f"     Possession: {record.get('home_possession'):.1f}% - {record.get('away_possession'):.1f}%")
        
        return filename

def main():
    """Main function for simple data collection"""
    collector = SimpleDataCollector()
    
    print("🎯 Simple Late Goal Data Collector")
    print("=" * 40)
    
    # Step 1: Collect second-half matches
    second_half_matches = collector.collect_current_second_half_matches()
    
    if not second_half_matches:
        print("\n⚠️  No second-half matches found currently")
        print("   This is normal if no matches are in progress")
        print("   Try running during peak football hours (12:00-22:00 UTC)")
        return
    
    # Step 2: Collect detailed data
    detailed_data = collector.collect_detailed_data(second_half_matches)
    
    if not detailed_data:
        print("\n⚠️  No detailed data collected")
        return
    
    # Step 3: Export data
    filename = collector.export_data(detailed_data)
    
    if filename:
        print(f"\n✅ Collection completed successfully!")
        print(f"   File: {filename}")
        print(f"   Records: {len(detailed_data)}")
    
    print(f"\n🚀 Next Steps:")
    print("   1. Review the exported CSV file")
    print("   2. Run continuous monitoring for ongoing collection")
    print("   3. Verify data quality against SofaScore website")

if __name__ == "__main__":
    main()