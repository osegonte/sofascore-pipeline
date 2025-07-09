#!/usr/bin/env python3
"""
Fixed Continuous Monitoring Script for Late Goal Prediction
Runs every 5 minutes, collects only second-half matches
"""

import sys
import os
import time
import schedule
import threading
from datetime import datetime, timedelta
import pandas as pd
import json
import signal

# Add project root to path - FIXED PATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import from existing modules - FIXED IMPORTS
from src.live_scraper import LiveMatchScraper
from src.utils import setup_logging

class ContinuousMonitor:
    """Continuous monitoring system for late goal prediction"""
    
    def __init__(self):
        self.logger = setup_logging()
        self.scraper = LiveMatchScraper()
        self.monitoring = False
        self.data_buffer = []
        self.stats = {
            'collections': 0,
            'matches_processed': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Configuration
        self.collection_interval = 5  # minutes
        self.export_interval = 15    # minutes
        self.max_buffer_size = 1000
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Shutdown signal received. Stopping monitoring...")
        self.stop_monitoring()
    
    def is_second_half_match(self, match_data):
        """Enhanced second-half detection"""
        try:
            # Get match status and timing
            status = match_data.get('status', '').lower()
            status_type = match_data.get('status_type', '').lower()
            period = match_data.get('period', 1)
            minutes_elapsed = match_data.get('minutes_elapsed', 0)
            
            # Check if match is live
            if 'finished' in status or 'ended' in status:
                return False
            
            # Check if match is paused (halftime)
            if 'halftime' in status or 'half-time' in status:
                return False
            
            # Check if match is in second half
            if period >= 2:  # Second half, extra time, or penalties
                return True
            
            # Check if match is past 45 minutes (late first half)
            if minutes_elapsed >= 45:
                return True
            
            # Check status type
            if status_type == 'inprogress' and minutes_elapsed >= 45:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking match period: {e}")
            return False
    
    def collect_match_data(self, match_id):
        """Collect comprehensive match data with error handling"""
        try:
            # Get comprehensive match details
            match_details = self.scraper.get_match_comprehensive_details(match_id)
            
            if not match_details:
                return None
            
            # Process the data for prediction
            processed_data = self.process_match_data(match_details)
            return processed_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data for match {match_id}: {e}")
            self.stats['errors'] += 1
            return None
    
    def process_match_data(self, match_details):
        """Process match data for late goal prediction"""
        match_info = match_details.get('match_details', {})
        goal_events = match_details.get('goal_events', [])
        team_stats = match_details.get('team_statistics', {})
        
        # Calculate current state
        current_minute = match_info.get('minutes_elapsed', 0)
        home_score = match_info.get('home_score', 0)
        away_score = match_info.get('away_score', 0)
        
        # Analyze goal timing
        goals_75_plus = len([g for g in goal_events if g.get('total_minute', 0) >= 75])
        goals_80_plus = len([g for g in goal_events if g.get('total_minute', 0) >= 80])
        goals_85_plus = len([g for g in goal_events if g.get('total_minute', 0) >= 85])
        
        # Recent goal activity
        recent_goals = len([g for g in goal_events if g.get('total_minute', 0) >= current_minute - 10])
        
        # Team statistics
        home_stats = team_stats.get('home', {})
        away_stats = team_stats.get('away', {})
        
        # Calculate advanced metrics
        total_shots = home_stats.get('total_shots', 0) + away_stats.get('total_shots', 0)
        total_corners = home_stats.get('corners', 0) + away_stats.get('corners', 0)
        
        # Match intensity indicators
        possession_balance = abs(home_stats.get('possession_percentage', 50) - 50)
        
        return {
            # Basic info
            'match_id': match_info.get('match_id'),
            'competition': match_info.get('competition'),
            'home_team': match_info.get('home_team'),
            'away_team': match_info.get('away_team'),
            'venue': match_info.get('venue'),
            'collection_timestamp': datetime.now().isoformat(),
            
            # Time and score
            'current_minute': current_minute,
            'home_score': home_score,
            'away_score': away_score,
            'total_goals': home_score + away_score,
            'goal_difference': abs(home_score - away_score),
            
            # Goal timing analysis
            'goals_75_plus': goals_75_plus,
            'goals_80_plus': goals_80_plus,
            'goals_85_plus': goals_85_plus,
            'recent_goals_10min': recent_goals,
            'has_late_goal': goals_75_plus > 0,
            
            # Team stats
            'home_possession': home_stats.get('possession_percentage', 50),
            'away_possession': away_stats.get('possession_percentage', 50),
            'home_shots': home_stats.get('total_shots', 0),
            'away_shots': away_stats.get('total_shots', 0),
            'home_shots_on_target': home_stats.get('shots_on_target', 0),
            'away_shots_on_target': away_stats.get('shots_on_target', 0),
            'home_corners': home_stats.get('corners', 0),
            'away_corners': away_stats.get('corners', 0),
            'home_fouls': home_stats.get('fouls', 0),
            'away_fouls': away_stats.get('fouls', 0),
            'home_yellow_cards': home_stats.get('yellow_cards', 0),
            'away_yellow_cards': away_stats.get('yellow_cards', 0),
            'home_red_cards': home_stats.get('red_cards', 0),
            'away_red_cards': away_stats.get('red_cards', 0),
            
            # Derived features
            'possession_balance': possession_balance,
            'total_shots': total_shots,
            'total_corners': total_corners,
            'shot_accuracy_home': (home_stats.get('shots_on_target', 0) / max(home_stats.get('total_shots', 1), 1)) * 100,
            'shot_accuracy_away': (away_stats.get('shots_on_target', 0) / max(away_stats.get('total_shots', 1), 1)) * 100,
            'match_intensity': (total_shots + total_corners) / max(current_minute - 45, 1),
            'is_close_match': abs(home_score - away_score) <= 1,
            'is_high_scoring': (home_score + away_score) >= 3,
            'time_remaining': max(0, 90 - current_minute),
            
            # Prediction features
            'minutes_since_last_goal': self.calculate_minutes_since_last_goal(goal_events, current_minute),
            'pressure_indicator': self.calculate_pressure_indicator(home_stats, away_stats),
            'late_goal_probability_factors': self.calculate_late_goal_factors(
                current_minute, home_score, away_score, possession_balance, total_shots
            )
        }
    
    def calculate_minutes_since_last_goal(self, goal_events, current_minute):
        """Calculate minutes since last goal"""
        if not goal_events:
            return current_minute
        
        goal_times = [g.get('total_minute', 0) for g in goal_events]
        last_goal_time = max(goal_times)
        
        return current_minute - last_goal_time
    
    def calculate_pressure_indicator(self, home_stats, away_stats):
        """Calculate match pressure indicator"""
        home_pressure = (home_stats.get('total_shots', 0) + home_stats.get('corners', 0)) * 0.7
        away_pressure = (away_stats.get('total_shots', 0) + away_stats.get('corners', 0)) * 0.7
        
        return home_pressure + away_pressure
    
    def calculate_late_goal_factors(self, minute, home_score, away_score, possession_balance, total_shots):
        """Calculate factors that increase late goal probability"""
        factors = {
            'late_stage': 1.0 if minute >= 75 else 0.0,
            'close_match': 1.0 if abs(home_score - away_score) <= 1 else 0.0,
            'high_possession_battle': 1.0 if possession_balance >= 15 else 0.0,
            'high_shot_activity': 1.0 if total_shots >= 15 else 0.0,
            'desperation_time': 1.0 if minute >= 85 else 0.0
        }
        
        return factors
    
    def collect_current_data(self):
        """Collect data for current second-half matches"""
        try:
            self.logger.info("Starting data collection cycle...")
            
            # Get live matches
            live_matches = self.scraper.get_live_matches()
            
            if not live_matches:
                self.logger.info("No live matches found")
                return
            
            # Filter for second-half matches
            second_half_matches = [m for m in live_matches if self.is_second_half_match(m)]
            
            if not second_half_matches:
                self.logger.info("No second-half matches found")
                return
            
            self.logger.info(f"Found {len(second_half_matches)} second-half matches")
            
            # Collect data for each match
            for match in second_half_matches:
                match_id = match.get('match_id')
                if match_id:
                    match_data = self.collect_match_data(match_id)
                    if match_data:
                        self.data_buffer.append(match_data)
                        self.stats['matches_processed'] += 1
                        
                        # Log interesting matches
                        if match_data.get('has_late_goal') or match_data.get('current_minute', 0) >= 85:
                            self.logger.info(f"Late goal activity in match {match_id}: "
                                           f"{match_data.get('home_team')} vs {match_data.get('away_team')} "
                                           f"({match_data.get('current_minute')}' - {match_data.get('home_score')}-{match_data.get('away_score')})")
            
            self.stats['collections'] += 1
            
            # Manage buffer size
            if len(self.data_buffer) > self.max_buffer_size:
                self.data_buffer = self.data_buffer[-self.max_buffer_size:]
            
            self.logger.info(f"Collection cycle completed. Buffer size: {len(self.data_buffer)}")
            
        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")
            self.stats['errors'] += 1
    
    def export_data(self):
        """Export collected data to CSV"""
        if not self.data_buffer:
            self.logger.info("No data to export")
            return
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create exports directory
            os.makedirs('exports', exist_ok=True)
            
            # Convert to DataFrame
            df = pd.DataFrame(self.data_buffer)
            
            # Export main data
            filename = f'exports/late_goal_continuous_{timestamp}.csv'
            df.to_csv(filename, index=False)
            
            self.logger.info(f"Exported {len(df)} records to {filename}")
            
            # Export latest stats
            stats_filename = f'exports/monitoring_stats_{timestamp}.json'
            current_stats = self.stats.copy()
            current_stats['buffer_size'] = len(self.data_buffer)
            current_stats['latest_export'] = datetime.now().isoformat()
            
            with open(stats_filename, 'w') as f:
                json.dump(current_stats, f, indent=2, default=str)
            
            # Clear buffer after export
            self.data_buffer = []
            
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            return None
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.logger.info("Starting continuous monitoring...")
        self.monitoring = True
        self.stats['start_time'] = datetime.now()
        
        # Schedule data collection every 5 minutes
        schedule.every(self.collection_interval).minutes.do(self.collect_current_data)
        
        # Schedule data export every 15 minutes
        schedule.every(self.export_interval).minutes.do(self.export_data)
        
        # Initial collection
        self.collect_current_data()
        
        # Run scheduler
        while self.monitoring:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        
        # Final export before shutdown
        self.export_data()
        self.logger.info("Monitoring stopped")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def get_stats(self):
        """Get current monitoring statistics"""
        current_stats = self.stats.copy()
        current_stats['buffer_size'] = len(self.data_buffer)
        current_stats['running_time'] = str(datetime.now() - self.stats['start_time']) if self.stats['start_time'] else None
        
        return current_stats
    
    def print_status(self):
        """Print current monitoring status"""
        stats = self.get_stats()
        
        print(f"\n📊 MONITORING STATUS")
        print(f"=" * 30)
        print(f"Running time: {stats.get('running_time', 'Not started')}")
        print(f"Collections: {stats['collections']}")
        print(f"Matches processed: {stats['matches_processed']}")
        print(f"Current buffer size: {stats['buffer_size']}")
        print(f"Errors: {stats['errors']}")
        print(f"Last check: {datetime.now().strftime('%H:%M:%S')}")

def main():
    """Main monitoring function"""
    monitor = ContinuousMonitor()
    
    print("Late Goal Prediction - Continuous Monitoring")
    print("=" * 50)
    print("Configuration:")
    print(f"  • Collection interval: {monitor.collection_interval} minutes")
    print(f"  • Export interval: {monitor.export_interval} minutes")
    print(f"  • Focus: Second-half matches only")
    print(f"  • Buffer size: {monitor.max_buffer_size} records")
    
    try:
        # Start monitoring in a separate thread
        monitoring_thread = threading.Thread(target=monitor.start_monitoring)
        monitoring_thread.daemon = True
        monitoring_thread.start()
        
        # Status monitoring loop
        while monitor.monitoring:
            monitor.print_status()
            time.sleep(300)  # Print status every 5 minutes
        
    except KeyboardInterrupt:
        print("\n⏹️  Monitoring interrupted by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        monitor.stop_monitoring()
    
    # Final stats
    final_stats = monitor.get_stats()
    print(f"\n📈 FINAL STATISTICS:")
    print(f"  • Total collections: {final_stats['collections']}")
    print(f"  • Matches processed: {final_stats['matches_processed']}")
    print(f"  • Errors: {final_stats['errors']}")
    print(f"  • Running time: {final_stats.get('running_time', 'Unknown')}")

if __name__ == "__main__":
    main()