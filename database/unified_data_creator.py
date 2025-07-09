#!/usr/bin/env python3
"""
Fixed Unified Match Data Creator - Handles NoneType values properly
"""

import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
import warnings
warnings.filterwarnings('ignore')

class UnifiedDataCreator:
    """Creates unified match data with ALL required fields properly populated"""
    
    def __init__(self):
        self.engine = engine
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
    
    def create_unified_match_data(self):
        """Create unified dataset with ALL FIELDS POPULATED - Fixed NoneType handling"""
        print("🔄 Creating Fixed Unified Match Data")
        print("=" * 50)
        
        try:
            # Load all data
            matches_df = pd.read_sql_query("SELECT * FROM live_matches ORDER BY match_id", self.engine)
            goals_df = pd.read_sql_query("SELECT * FROM goal_events ORDER BY match_id, total_minute", self.engine)
            team_stats_df = pd.read_sql_query("SELECT * FROM team_statistics", self.engine)
            player_stats_df = pd.read_sql_query("SELECT * FROM player_statistics", self.engine)
            
            print(f"📊 Loaded: {len(matches_df)} matches, {len(goals_df)} goals")
            print(f"📊 Team stats: {len(team_stats_df)}, Player stats: {len(player_stats_df)}")
            
            unified_data = []
            
            for _, match in matches_df.iterrows():
                match_id = match['match_id']
                
                # Get match data
                match_goals = goals_df[goals_df['match_id'] == match_id].copy()
                match_team_stats = team_stats_df[team_stats_df['match_id'] == match_id]
                match_players = player_stats_df[player_stats_df['match_id'] == match_id]
                
                # Get team statistics properly with None handling
                home_stats = self._get_team_stats(match_team_stats, 'home')
                away_stats = self._get_team_stats(match_team_stats, 'away')
                
                # Determine match duration with None handling
                max_minute = 95  # Default
                if not match_goals.empty and 'total_minute' in match_goals.columns:
                    goal_minutes = match_goals['total_minute'].dropna()
                    if not goal_minutes.empty:
                        max_minute = max(95, int(goal_minutes.max() + 5))
                
                # Create minute-by-minute records
                home_score = away_score = 0
                
                for minute in range(0, max_minute + 1):
                    # Check for goals at this minute - handle NoneType
                    minute_goals = match_goals[match_goals['total_minute'] == minute]
                    
                    goal_info = {'timestamp': None, 'type': None, 'scorer': None, 'assister': None}
                    
                    # Process goals with None handling
                    for _, goal in minute_goals.iterrows():
                        team_side = goal.get('team_side')
                        if team_side == 'home':
                            home_score += 1
                        elif team_side == 'away':
                            away_score += 1
                        
                        goal_info.update({
                            'timestamp': goal.get('scraped_at'),
                            'type': goal.get('goal_type', 'regular'),
                            'scorer': goal.get('scoring_player'),
                            'assister': goal.get('assisting_player')
                        })
                    
                    # Create comprehensive player JSON
                    players_json = self._create_players_json(match_players)
                    
                    # Create unified record with ALL FIELDS - SAFE HANDLING
                    row = {
                        # BASIC MATCH INFO
                        'match_id': self._safe_int(match_id),
                        'competition': self._safe_str(match.get('competition'), 'Unknown'),
                        'match_datetime': match.get('match_datetime'),
                        'home_team': self._safe_str(match.get('home_team'), 'Unknown'),
                        'away_team': self._safe_str(match.get('away_team'), 'Unknown'),
                        'venue': self._safe_str(match.get('venue'), 'Unknown Stadium'),
                        
                        # TIME & SCORE
                        'minute': minute,
                        'added_time': 0,
                        'current_score_home': home_score,
                        'current_score_away': away_score,
                        
                        # GOAL EVENTS
                        'goal_timestamp': goal_info['timestamp'],
                        'goal_type': goal_info['type'],
                        'scoring_player': goal_info['scorer'],
                        'assisting_player': goal_info['assister'],
                        
                        # TEAM STATISTICS - NOW PROPERLY POPULATED WITH DEFAULTS
                        'possession_pct': self._safe_float(home_stats.get('possession_percentage'), 50.0),
                        'shots_on_target': self._safe_int(home_stats.get('shots_on_target'), 0),
                        'total_shots': self._safe_int(home_stats.get('total_shots'), 0),
                        'corners': self._safe_int(home_stats.get('corners'), 0),
                        'fouls': self._safe_int(home_stats.get('fouls'), 0),
                        'yellow_cards': self._safe_int(home_stats.get('yellow_cards'), 0),
                        'red_cards': self._safe_int(home_stats.get('red_cards'), 0),
                        'offsides': self._safe_int(home_stats.get('offsides'), 0),
                        
                        # PLAYER STATISTICS JSON - NOW POPULATED
                        'player_statistics': json.dumps(players_json) if players_json else '[]',
                        
                        # FINAL SCORES - NOW CALCULATED
                        'final_score_home': self._safe_int(match.get('home_score'), home_score),
                        'final_score_away': self._safe_int(match.get('away_score'), away_score),
                        
                        # GOAL ANALYSIS
                        'goal_interval_bucket': self._get_goal_interval_bucket(minute),
                        
                        # META
                        'match_status': self._safe_str(match.get('status'), 'Unknown'),
                        'scraped_at': match.get('scraped_at', datetime.now())
                    }
                    
                    unified_data.append(row)
            
            unified_df = pd.DataFrame(unified_data)
            print(f"✅ Created unified dataset with {len(unified_df)} records")
            print(f"📊 Columns populated: {len([c for c in unified_df.columns if not unified_df[c].isna().all()])}/{len(unified_df.columns)}")
            
            return unified_df
            
        except Exception as e:
            print(f"❌ Error creating unified data: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _safe_int(self, value, default=0):
        """Safely convert to int with default"""
        if value is None or pd.isna(value):
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_float(self, value, default=0.0):
        """Safely convert to float with default"""
        if value is None or pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_str(self, value, default=''):
        """Safely convert to string with default"""
        if value is None or pd.isna(value):
            return default
        return str(value)
    
    def _get_team_stats(self, team_stats_df, side):
        """Get team statistics with defaults and None handling"""
        team_data = team_stats_df[team_stats_df['team_side'] == side]
        
        if team_data.empty:
            return self._get_default_team_stats()
        
        stats = team_data.iloc[0].to_dict()
        
        # Ensure no None values with safe conversion
        safe_stats = {}
        defaults = self._get_default_team_stats()
        
        for key, default_value in defaults.items():
            raw_value = stats.get(key)
            if isinstance(default_value, float):
                safe_stats[key] = self._safe_float(raw_value, default_value)
            else:
                safe_stats[key] = self._safe_int(raw_value, default_value)
        
        return safe_stats
    
    def _get_default_team_stats(self):
        """Get default team statistics"""
        return {
            'possession_percentage': 50.0,
            'shots_on_target': 0,
            'total_shots': 0,
            'corners': 0,
            'fouls': 0,
            'yellow_cards': 0,
            'red_cards': 0,
            'offsides': 0
        }
    
    def _create_players_json(self, players_df):
        """Create comprehensive player JSON with None handling"""
        if players_df.empty:
            return []
        
        players_list = []
        for _, player in players_df.iterrows():
            player_data = {
                'player': self._safe_str(player.get('player_name'), 'Unknown'),
                'role': 'Starter' if player.get('is_starter') else 'Sub',
                'goals': self._safe_int(player.get('goals'), 0),
                'assists': self._safe_int(player.get('assists'), 0),
                'shots_on_target': self._safe_int(player.get('shots_on_target'), 0),
                'minutes_played': self._safe_int(player.get('minutes_played'), 0),
                'cards_received': self._safe_int(player.get('cards_received'), 0),
                'team_side': self._safe_str(player.get('team_side'), 'unknown')
            }
            players_list.append(player_data)
        
        return players_list
    
    def _get_goal_interval_bucket(self, minute):
        """Get goal interval bucket"""
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
    
    def export_unified_data(self, unified_df, filename=None):
        """Export unified data with all fields populated"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unified_match_data_FIXED_{timestamp}.csv"
        
        try:
            os.makedirs('exports', exist_ok=True)
            filepath = os.path.join('exports', filename)
            
            unified_df.to_csv(filepath, index=False)
            
            # Check data completeness
            total_fields = len(unified_df.columns)
            populated_fields = len([c for c in unified_df.columns if not unified_df[c].isna().all()])
            completeness = (populated_fields / total_fields) * 100
            
            print(f"\n💾 Exported unified data to: {filepath}")
            print(f"📊 Records: {len(unified_df):,}")
            print(f"📈 Data completeness: {completeness:.1f}% ({populated_fields}/{total_fields} fields)")
            
            return filepath
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None

def main():
    """Main function"""
    creator = UnifiedDataCreator()
    unified_df = creator.create_unified_match_data()
    
    if not unified_df.empty:
        creator.export_unified_data(unified_df)
        print("✅ Fixed unified data created successfully!")
    else:
        print("❌ Failed to create unified data")

if __name__ == "__main__":
    main()
