#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard for Late Goal Prediction Data Collection
"""

import os
import sys
import time
import glob
from datetime import datetime, timedelta
import pandas as pd
import json
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MonitoringDashboard:
    """Real-time dashboard for monitoring data collection"""
    
    def __init__(self):
        self.exports_dir = 'exports'
        self.refresh_interval = 30  # seconds
        self.running = True
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_latest_files(self):
        """Get latest CSV files"""
        patterns = [
            'late_goal_prediction_data_*.csv',
            'late_goal_continuous_*.csv',
            'late_goal_events_*.csv'
        ]
        
        files = []
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(self.exports_dir, pattern)))
        
        # Sort by modification time
        files.sort(key=os.path.getmtime, reverse=True)
        
        return files
    
    def analyze_data_file(self, filepath):
        """Analyze a single data file"""
        try:
            df = pd.read_csv(filepath)
            
            # Basic stats
            stats = {
                'filename': os.path.basename(filepath),
                'size': os.path.getsize(filepath),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)),
                'records': len(df),
                'columns': len(df.columns),
                'matches': df['match_id'].nunique() if 'match_id' in df.columns else 0
            }
            
            # Late goal analysis
            if 'has_late_goal' in df.columns:
                stats['matches_with_late_goals'] = df['has_late_goal'].sum()
                stats['late_goal_rate'] = (stats['matches_with_late_goals'] / stats['matches']) * 100 if stats['matches'] > 0 else 0
            
            # Current minute distribution
            if 'current_minute' in df.columns:
                stats['avg_minute'] = df['current_minute'].mean()
                stats['min_minute'] = df['current_minute'].min()
                stats['max_minute'] = df['current_minute'].max()
            
            # Competition analysis
            if 'competition' in df.columns:
                stats['top_competitions'] = df['competition'].value_counts().head(3).to_dict()
            
            # Recent data
            if 'collection_timestamp' in df.columns:
                df['collection_timestamp'] = pd.to_datetime(df['collection_timestamp'])
                recent = df[df['collection_timestamp'] > datetime.now() - timedelta(hours=1)]
                stats['recent_records'] = len(recent)
            
            return stats
            
        except Exception as e:
            return {
                'filename': os.path.basename(filepath),
                'error': str(e),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath))
            }
    
    def get_monitoring_stats(self):
        """Get monitoring statistics from JSON files"""
        stats_files = glob.glob(os.path.join(self.exports_dir, 'monitoring_stats_*.json'))
        
        if not stats_files:
            return None
        
        # Get latest stats file
        latest_stats_file = max(stats_files, key=os.path.getmtime)
        
        try:
            with open(latest_stats_file, 'r') as f:
                stats = json.load(f)
            
            stats['file_age'] = datetime.now() - datetime.fromtimestamp(os.path.getmtime(latest_stats_file))
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()
        
        print("⚽ LATE GOAL PREDICTION - MONITORING DASHBOARD")
        print("=" * 60)
        print(f"🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get latest files
        files = self.get_latest_files()
        
        if not files:
            print("📁 No data files found in exports/ directory")
            print("   Start data collection to see monitoring data")
            return
        
        # Analyze latest files
        print("📊 DATA COLLECTION SUMMARY")
        print("-" * 40)
        
        total_records = 0
        total_matches = 0
        total_late_goals = 0
        
        for i, filepath in enumerate(files[:5]):  # Show top 5 files
            stats = self.analyze_data_file(filepath)
            
            if 'error' in stats:
                print(f"❌ {stats['filename']}: {stats['error']}")
                continue
            
            # File info
            age = datetime.now() - stats['modified']
            age_str = f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m ago"
            
            print(f"📄 {stats['filename']}")
            print(f"   Records: {stats['records']:,} | Matches: {stats['matches']} | Age: {age_str}")
            
            if 'matches_with_late_goals' in stats:
                print(f"   Late Goals: {stats['matches_with_late_goals']} matches ({stats['late_goal_rate']:.1f}%)")
                total_late_goals += stats['matches_with_late_goals']
            
            if 'avg_minute' in stats:
                print(f"   Time Range: {stats['min_minute']:.0f}-{stats['max_minute']:.0f} min (avg: {stats['avg_minute']:.0f})")
            
            if 'top_competitions' in stats:
                top_comp = list(stats['top_competitions'].keys())[0] if stats['top_competitions'] else 'None'
                print(f"   Top Competition: {top_comp}")
            
            total_records += stats['records']
            total_matches += stats['matches']
            print()
        
        # Overall statistics
        print("📈 OVERALL STATISTICS")
        print("-" * 40)
        print(f"Total Records: {total_records:,}")
        print(f"Total Matches: {total_matches}")
        print(f"Matches with Late Goals: {total_late_goals}")
        
        if total_matches > 0:
            late_goal_rate = (total_late_goals / total_matches) * 100
            print(f"Late Goal Rate: {late_goal_rate:.1f}%")
        
        # Monitoring process statistics
        monitoring_stats = self.get_monitoring_stats()
        if monitoring_stats and 'error' not in monitoring_stats:
            print(f"\n🔄 MONITORING PROCESS")
            print("-" * 40)
            print(f"Collections: {monitoring_stats.get('collections', 0)}")
            print(f"Matches Processed: {monitoring_stats.get('matches_processed', 0)}")
            print(f"Errors: {monitoring_stats.get('errors', 0)}")
            print(f"Buffer Size: {monitoring_stats.get('buffer_size', 0)}")
            
            if 'start_time' in monitoring_stats:
                start_time = datetime.fromisoformat(monitoring_stats['start_time'])
                running_time = datetime.now() - start_time
                print(f"Running Time: {running_time}")
        
        # Real-time second-half matches
        print(f"\n🎯 CURRENT SECOND-HALF MATCHES")
        print("-" * 40)
        
        try:
            # Try to get current second-half matches
            from src.live_scraper import LiveMatchScraper
            scraper = LiveMatchScraper()
            
            live_matches = scraper.get_live_matches()
            
            if not live_matches:
                print("No live matches currently")
            else:
                second_half_count = 0
                for match in live_matches:
                    period = match.get('period', 1)
                    minutes = match.get('minutes_elapsed', 0)
                    
                    if period >= 2 or minutes >= 45:
                        second_half_count += 1
                        home_team = match.get('home_team', 'Unknown')
                        away_team = match.get('away_team', 'Unknown')
                        home_score = match.get('home_score', 0)
                        away_score = match.get('away_score', 0)
                        
                        print(f"⚽ {home_team} {home_score}-{away_score} {away_team} ({minutes}')")
                
                if second_half_count == 0:
                    print("No second-half matches currently")
                else:
                    print(f"\nTotal second-half matches: {second_half_count}")
        
        except Exception as e:
            print(f"Error getting live matches: {e}")
        
        # Data quality indicators
        print(f"\n🔍 DATA QUALITY INDICATORS")
        print("-" * 40)
        
        # Check for recent data
        if files:
            latest_file = files[0]
            latest_stats = self.analyze_data_file(latest_file)
            
            if 'recent_records' in latest_stats:
                print(f"Recent Records (1h): {latest_stats['recent_records']}")
            
            file_age = datetime.now() - latest_stats['modified']
            
            if file_age < timedelta(minutes=10):
                print("✅ Data freshness: Excellent")
            elif file_age < timedelta(minutes=30):
                print("🟨 Data freshness: Good")
            else:
                print("⚠️  Data freshness: Stale")
        
        # Collection recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        current_hour = datetime.now().hour
        
        if 12 <= current_hour <= 22:
            print("✅ Peak collection time - high match activity expected")
        else:
            print("🌙 Off-peak hours - lower match activity expected")
        
        if total_records < 100:
            print("📈 Need more data - continue collection")
        elif total_records < 1000:
            print("📊 Good data volume - sufficient for initial analysis")
        else:
            print("🎯 Excellent data volume - ready for model development")
        
        if total_late_goals < 10:
            print("⚡ Need more late goal examples - continue monitoring")
        
        print(f"\nPress Ctrl+C to exit | Refreshing every {self.refresh_interval}s")
    
    def run(self):
        """Run the monitoring dashboard"""
        try:
            while self.running:
                self.display_dashboard()
                time.sleep(self.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring dashboard stopped")
            self.running = False

def main():
    """Main dashboard function"""
    dashboard = MonitoringDashboard()
    
    print("Starting Late Goal Prediction Monitoring Dashboard...")
    print("This will refresh every 30 seconds")
    print("Press Ctrl+C to exit")
    
    time.sleep(2)
    dashboard.run()

if __name__ == "__main__":
    main()