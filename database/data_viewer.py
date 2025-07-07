#!/usr/bin/env python3
"""
Unified Match Data Viewer - Live + Historical Combined
Creates a unified view of all match data as specified
"""
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
import warnings
warnings.filterwarnings('ignore')

class UnifiedMatchDataViewer:
    """Creates unified match_data view combining live + historical data"""
    
    def __init__(self):
        self.engine = engine
        
        # Set pandas display options
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', 100)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 40)
    
    def create_unified_match_data(self):
        """Create unified match_data table combining live + historical"""
        print("🔄 Creating Unified Match Data View")
        print("=" * 60)
        
        try:
            # Load all data from database
            matches_df = pd.read_sql_query("SELECT * FROM live_matches ORDER BY match_id", self.engine)
            goals_df = pd.read_sql_query("SELECT * FROM goal_events ORDER BY match_id, total_minute", self.engine)
            team_stats_df = pd.read_sql_query("SELECT * FROM team_statistics", self.engine)
            player_stats_df = pd.read_sql_query("SELECT * FROM player_statistics", self.engine)
            
            print(f"📊 Loaded: {len(matches_df)} matches, {len(goals_df)} goals, {len(team_stats_df)} team stats, {len(player_stats_df)} player stats")
            
            # Create unified match data
            unified_data = []
            
            for _, match in matches_df.iterrows():
                match_id = match['match_id']
                
                # Get match goals
                match_goals = goals_df[goals_df['match_id'] == match_id].copy()
                
                # Get team statistics for this match
                home_stats = team_stats_df[
                    (team_stats_df['match_id'] == match_id) & 
                    (team_stats_df['team_side'] == 'home')
                ].iloc[0] if len(team_stats_df[
                    (team_stats_df['match_id'] == match_id) & 
                    (team_stats_df['team_side'] == 'home')
                ]) > 0 else None
                
                away_stats = team_stats_df[
                    (team_stats_df['match_id'] == match_id) & 
                    (team_stats_df['team_side'] == 'away')
                ].iloc[0] if len(team_stats_df[
                    (team_stats_df['match_id'] == match_id) & 
                    (team_stats_df['team_side'] == 'away')
                ]) > 0 else None
                
                # Get player statistics for this match
                match_players = player_stats_df[player_stats_df['match_id'] == match_id]
                
                # Create minute-by-minute data (0 to max minute + 5)
                max_minute = 90
                if not match_goals.empty and 'total_minute' in match_goals.columns:
                    max_minute = max(90, int(match_goals['total_minute'].max() + 5))
                
                # Track cumulative scores
                home_score = 0
                away_score = 0
                
                for minute in range(0, max_minute + 1):
                    # Check for goals at this minute
                    minute_goals = match_goals[match_goals['total_minute'] == minute]
                    
                    goal_data = {
                        'goal_timestamp': None,
                        'goal_type': None,
                        'scoring_player': None,
                        'assisting_player': None
                    }
                    
                    # Process goals at this minute
                    for _, goal in minute_goals.iterrows():
                        if goal['team_side'] == 'home':
                            home_score += 1
                        elif goal['team_side'] == 'away':
                            away_score += 1
                        
                        # Store goal details (last goal if multiple)
                        goal_data.update({
                            'goal_timestamp': goal.get('scraped_at'),
                            'goal_type': goal.get('goal_type', 'regular'),
                            'scoring_player': goal.get('scoring_player'),
                            'assisting_player': goal.get('assisting_player')
                        })
                    
                    # Create player statistics JSON
                    players_json = []
                    for _, player in match_players.iterrows():
                        player_data = {
                            'player': player.get('player_name'),
                            'role': 'Starter' if player.get('is_starter') else 'Sub',
                            'goals': int(player.get('goals', 0)) if pd.notna(player.get('goals')) else 0,
                            'assists': int(player.get('assists', 0)) if pd.notna(player.get('assists')) else 0,
                            'shots_on_target': int(player.get('shots_on_target', 0)) if pd.notna(player.get('shots_on_target')) else 0,
                            'minutes_played': int(player.get('minutes_played', 0)) if pd.notna(player.get('minutes_played')) else 0,
                            'cards_received': int(player.get('cards_received', 0)) if pd.notna(player.get('cards_received')) else 0,
                            'team_side': player.get('team_side')
                        }
                        players_json.append(player_data)
                    
                    # Determine goal interval bucket
                    goal_interval_bucket = self.get_goal_interval_bucket(minute)
                    
                    # Create unified row
                    row = {
                        # Basic Match Info
                        'match_id': match_id,
                        'competition': match.get('competition'),
                        'match_datetime': match.get('match_datetime'),
                        'home_team': match.get('home_team'),
                        'away_team': match.get('away_team'),
                        'venue': match.get('venue'),
                        
                        # Live & Historical Fields
                        'minute': minute,
                        'added_time': 0,  # Would need to calculate from goals data
                        
                        # Score & Goal Events
                        'current_score_home': home_score,
                        'current_score_away': away_score,
                        'goal_timestamp': goal_data['goal_timestamp'],
                        'goal_type': goal_data['goal_type'],
                        'scoring_player': goal_data['scoring_player'],
                        'assisting_player': goal_data['assisting_player'],
                        
                        # Team Statistics (using available data)
                        'possession_pct': home_stats.get('possession_percentage') if home_stats is not None else None,
                        'shots_on_target': home_stats.get('shots_on_target') if home_stats is not None else None,
                        'total_shots': home_stats.get('total_shots') if home_stats is not None else None,
                        'corners': home_stats.get('corners') if home_stats is not None else None,
                        'fouls': home_stats.get('fouls') if home_stats is not None else None,
                        'yellow_cards': home_stats.get('yellow_cards') if home_stats is not None else None,
                        'red_cards': home_stats.get('red_cards') if home_stats is not None else None,
                        'offsides': home_stats.get('offsides') if home_stats is not None else None,
                        
                        # Player Statistics (JSON)
                        'player_statistics': json.dumps(players_json) if players_json else None,
                        
                        # Historical-Only Fields
                        'final_score_home': match.get('home_score') if match.get('status_type') == 'finished' else None,
                        'final_score_away': match.get('away_score') if match.get('status_type') == 'finished' else None,
                        'goal_interval_bucket': goal_interval_bucket,
                        
                        # Meta fields
                        'match_status': match.get('status'),
                        'scraped_at': match.get('scraped_at')
                    }
                    
                    unified_data.append(row)
            
            # Convert to DataFrame
            unified_df = pd.DataFrame(unified_data)
            print(f"✅ Created unified dataset with {len(unified_df)} minute-level records")
            
            return unified_df
            
        except Exception as e:
            print(f"❌ Error creating unified data: {e}")
            return pd.DataFrame()
    
    def get_goal_interval_bucket(self, minute):
        """Get goal interval bucket for a given minute"""
        if minute <= 15:
            return "0-15"
        elif minute <= 30:
            return "16-30"
        elif minute <= 45:
            return "31-45"
        elif minute <= 60:
            return "46-60"
        elif minute <= 75:
            return "61-75"
        elif minute <= 90:
            return "76-90"
        else:
            return "90+"
    
    def show_unified_sample(self, unified_df, num_records=20):
        """Show sample of unified data"""
        print(f"\n📊 UNIFIED MATCH DATA SAMPLE ({num_records} records)")
        print("=" * 100)
        
        if unified_df.empty:
            print("⚠️  No unified data available")
            return
        
        # Show basic columns first
        basic_cols = ['match_id', 'competition', 'home_team', 'away_team', 'minute', 
                     'current_score_home', 'current_score_away', 'goal_type', 'scoring_player']
        available_basic = [col for col in basic_cols if col in unified_df.columns]
        
        print("\n🏟️  BASIC MATCH INFO:")
        print(unified_df[available_basic].head(num_records).to_string(index=False))
        
        # Show goal events
        goal_events = unified_df[unified_df['goal_type'].notna()]
        if not goal_events.empty:
            print(f"\n⚽ GOAL EVENTS ({len(goal_events)} total):")
            goal_cols = ['match_id', 'minute', 'home_team', 'away_team', 'current_score_home', 
                        'current_score_away', 'scoring_player', 'goal_type']
            available_goal_cols = [col for col in goal_cols if col in goal_events.columns]
            print(goal_events[available_goal_cols].head(10).to_string(index=False))
        
        # Show team statistics sample
        stats_cols = ['match_id', 'minute', 'possession_pct', 'shots_on_target', 'total_shots', 'corners', 'fouls']
        available_stats = [col for col in stats_cols if col in unified_df.columns]
        stats_sample = unified_df[unified_df['possession_pct'].notna()]
        
        if not stats_sample.empty:
            print(f"\n📊 TEAM STATISTICS SAMPLE:")
            print(stats_sample[available_stats].head(10).to_string(index=False))
    
    def show_match_summary(self, unified_df):
        """Show summary statistics of unified data"""
        print(f"\n📈 UNIFIED DATA SUMMARY")
        print("=" * 50)
        
        if unified_df.empty:
            print("⚠️  No data available")
            return
        
        # Basic stats
        total_records = len(unified_df)
        unique_matches = unified_df['match_id'].nunique()
        total_goals = len(unified_df[unified_df['goal_type'].notna()])
        
        print(f"📊 Total Records: {total_records:,}")
        print(f"🏟️  Unique Matches: {unique_matches:,}")
        print(f"⚽ Total Goals: {total_goals:,}")
        
        # Goals by interval
        if 'goal_interval_bucket' in unified_df.columns:
            goal_intervals = unified_df[unified_df['goal_type'].notna()]['goal_interval_bucket'].value_counts().sort_index()
            print(f"\n🕐 Goals by Interval:")
            for interval, count in goal_intervals.items():
                print(f"   {interval:>6}: {count:>3} goals")
        
        # Competitions
        if 'competition' in unified_df.columns:
            competitions = unified_df['competition'].value_counts().head(5)
            print(f"\n🏆 Top Competitions:")
            for comp, matches in competitions.items():
                comp_name = str(comp)[:30] + "..." if len(str(comp)) > 30 else str(comp)
                print(f"   {comp_name:<35} {matches:>4} records")
        
        # Match status
        if 'match_status' in unified_df.columns:
            status_counts = unified_df.drop_duplicates('match_id')['match_status'].value_counts()
            print(f"\n📊 Match Status:")
            for status, count in status_counts.items():
                print(f"   {status:<20} {count:>3} matches")
    
    def export_unified_data(self, unified_df, filename=None):
        """Export unified data to CSV"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unified_match_data_{timestamp}.csv"
        
        try:
            # Create exports directory if it doesn't exist
            os.makedirs('exports', exist_ok=True)
            filepath = os.path.join('exports', filename)
            
            unified_df.to_csv(filepath, index=False)
            print(f"\n💾 Exported unified data to: {filepath}")
            print(f"📊 Records exported: {len(unified_df):,}")
            
            return filepath
        except Exception as e:
            print(f"❌ Error exporting data: {e}")
            return None
    
    def show_specific_match(self, unified_df, match_id):
        """Show detailed view of a specific match"""
        match_data = unified_df[unified_df['match_id'] == match_id]
        
        if match_data.empty:
            print(f"❌ No data found for match ID: {match_id}")
            return
        
        print(f"\n🔍 DETAILED VIEW - Match ID: {match_id}")
        print("=" * 70)
        
        # Match info
        first_row = match_data.iloc[0]
        print(f"🏟️  {first_row['home_team']} vs {first_row['away_team']}")
        print(f"🏆 Competition: {first_row['competition']}")
        print(f"📅 Date: {first_row['match_datetime']}")
        print(f"🏟️  Venue: {first_row['venue']}")
        
        # Goals timeline
        goals = match_data[match_data['goal_type'].notna()]
        if not goals.empty:
            print(f"\n⚽ GOALS TIMELINE ({len(goals)} goals):")
            for _, goal in goals.iterrows():
                score = f"{goal['current_score_home']}-{goal['current_score_away']}"
                print(f"   {goal['minute']:>2}' {goal['scoring_player']:<25} ({goal['goal_type']:<10}) [{score}]")
        
        # Final score
        final_row = match_data.iloc[-1]
        print(f"\n📊 Final Score: {final_row['current_score_home']}-{final_row['current_score_away']}")
        
        # Show minute-by-minute for goals + context
        if not goals.empty:
            print(f"\n🕐 MINUTE-BY-MINUTE AROUND GOALS:")
            for _, goal in goals.iterrows():
                goal_minute = goal['minute']
                context = match_data[
                    (match_data['minute'] >= goal_minute - 2) & 
                    (match_data['minute'] <= goal_minute + 2)
                ]
                
                display_cols = ['minute', 'current_score_home', 'current_score_away', 'scoring_player', 'goal_type']
                available_cols = [col for col in display_cols if col in context.columns]
                print(f"\nAround minute {goal_minute}:")
                print(context[available_cols].to_string(index=False))
    
    def run_viewer(self):
        """Run the unified data viewer"""
        print("🎯 Unified Match Data Viewer")
        print("=" * 50)
        
        # Create unified data
        unified_df = self.create_unified_match_data()
        
        if unified_df.empty:
            print("❌ No data available. Run data collection first:")
            print("   python src/main.py")
            print("   python database/csv_import.py")
            return
        
        while True:
            print("\n" + "=" * 60)
            print("📊 UNIFIED MATCH DATA VIEWER")
            print("=" * 60)
            print("1. 📋 Show Data Sample")
            print("2. 📈 Show Summary Statistics")
            print("3. 🔍 View Specific Match")
            print("4. ⚽ Show All Goals")
            print("5. 💾 Export to CSV")
            print("6. 🔄 Refresh Data")
            print("0. 🚪 Exit")
            
            choice = input("\nSelect option (0-6): ").strip()
            
            if choice == '1':
                num_records = input("Number of records to show (default 20): ").strip()
                num_records = int(num_records) if num_records.isdigit() else 20
                self.show_unified_sample(unified_df, num_records)
                
            elif choice == '2':
                self.show_match_summary(unified_df)
                
            elif choice == '3':
                match_id = input("Enter Match ID: ").strip()
                if match_id.isdigit():
                    self.show_specific_match(unified_df, int(match_id))
                else:
                    print("❌ Please enter a valid numeric Match ID")
                    
            elif choice == '4':
                goals_only = unified_df[unified_df['goal_type'].notna()]
                print(f"\n⚽ ALL GOALS ({len(goals_only)} total):")
                goal_cols = ['match_id', 'minute', 'home_team', 'away_team', 'current_score_home', 
                           'current_score_away', 'scoring_player', 'goal_type', 'goal_interval_bucket']
                available_cols = [col for col in goal_cols if col in goals_only.columns]
                print(goals_only[available_cols].to_string(index=False))
                
            elif choice == '5':
                filename = input("Export filename (press Enter for auto): ").strip()
                filename = filename if filename else None
                exported_file = self.export_unified_data(unified_df, filename)
                if exported_file:
                    print(f"✅ Data exported successfully!")
                    
            elif choice == '6':
                print("🔄 Refreshing data...")
                unified_df = self.create_unified_match_data()
                print("✅ Data refreshed!")
                
            elif choice == '0':
                print("\n👋 Thanks for using Unified Match Data Viewer!")
                break
                
            else:
                print("❌ Invalid option. Please choose 0-6.")
            
            input("\nPress Enter to continue...")

def main():
    """Main function"""
    print("🚀 Starting Unified Match Data Viewer...")
    
    try:
        viewer = UnifiedMatchDataViewer()
        viewer.run_viewer()
    except KeyboardInterrupt:
        print("\n\n⏹️  Viewer interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure to:")
        print("1. Activate virtual environment: source venv/bin/activate")
        print("2. Have data in database: python database/csv_import.py")

if __name__ == "__main__":
    main()