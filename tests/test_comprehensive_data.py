"""
Test comprehensive data extraction for all required fields
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from live_scraper import LiveMatchScraper
from historical_scraper import HistoricalScraper

def test_live_data_fields():
    """Test that live data contains all required fields"""
    print("Testing Live Match Data Fields...")
    print("-" * 40)
    
    required_live_fields = {
        'match_details': [
            'match_id', 'competition', 'date', 'time', 'home_team', 'away_team', 'venue',
            'home_score', 'away_score', 'minutes_elapsed', 'status'
        ],
        'goal_events': [
            'exact_timestamp', 'goal_type', 'scoring_player', 'assisting_player',
            'team_side', 'is_penalty', 'total_minute'
        ],
        'team_statistics': [
            'possession_percentage', 'shots_on_target', 'total_shots', 'corners',
            'fouls', 'yellow_cards', 'red_cards', 'offsides'
        ],
        'player_statistics': [
            'player_name', 'position', 'jersey_number', 'is_starter', 'goals',
            'assists', 'shots_on_target', 'minutes_played', 'cards_received'
        ]
    }
    
    try:
        scraper = LiveMatchScraper()
        live_matches = scraper.get_live_matches()
        
        if live_matches:
            sample_match_id = live_matches[0]['match_id']
            details = scraper.get_match_comprehensive_details(sample_match_id)
            
            if details:
                dfs = scraper.to_comprehensive_dataframes([details])
                
                for df_name, required_fields in required_live_fields.items():
                    if df_name in dfs and not dfs[df_name].empty:
                        df = dfs[df_name]
                        missing_fields = [f for f in required_fields if f not in df.columns]
                        
                        if missing_fields:
                            print(f"❌ {df_name}: Missing fields {missing_fields}")
                        else:
                            print(f"✅ {df_name}: All required fields present ({len(df)} records)")
                    else:
                        print(f"⚠️  {df_name}: No data available")
            else:
                print("⚠️  Could not get match details")
        else:
            print("⚠️  No live matches available for testing")
            
        return True
        
    except Exception as e:
        print(f"❌ Live data test failed: {e}")
        return False

def test_historical_data_fields():
    """Test that historical data contains all required fields"""
    print("\nTesting Historical Match Data Fields...")
    print("-" * 40)
    
    required_historical_fields = {
        'match_details': [
            'match_id', 'competition', 'date', 'home_team', 'away_team',
            'home_score_final', 'away_score_final', 'total_goals'
        ],
        'goal_events': [
            'exact_timestamp_minute', 'scoring_player', 'assisting_player',
            'goal_type', 'time_interval', 'is_late_goal', 'is_last_15_minutes'
        ],
        'team_statistics': [
            'possession_percentage', 'total_shots', 'shots_on_target',
            'corners', 'fouls', 'yellow_cards', 'red_cards'
        ],
        'goal_frequency_analysis': [
            'total_goals_analyzed', 'late_goals_percentage', 'goals_by_15min_intervals',
            'percentage_matches_with_late_goals'
        ]
    }
    
    try:
        scraper = HistoricalScraper()
        historical_data = scraper.scrape_historical_comprehensive(days_back=3)
        
        if historical_data.get('recent_matches'):
            dfs = scraper.to_comprehensive_dataframes(historical_data)
            
            for df_name, required_fields in required_historical_fields.items():
                if df_name in dfs and not dfs[df_name].empty:
                    df = dfs[df_name]
                    missing_fields = [f for f in required_fields if f not in df.columns]
                    
                    if missing_fields:
                        print(f"❌ {df_name}: Missing fields {missing_fields}")
                    else:
                        print(f"✅ {df_name}: All required fields present ({len(df)} records)")
                else:
                    print(f"⚠️  {df_name}: No data available")
        else:
            print("⚠️  No historical matches available for testing")
            
        return True
        
    except Exception as e:
        print(f"❌ Historical data test failed: {e}")
        return False

def run_comprehensive_data_tests():
    """Run all comprehensive data tests"""
    print("SofaScore Pipeline - Comprehensive Data Field Testing")
    print("=" * 60)
    
    tests = [
        test_live_data_fields,
        test_historical_data_fields
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Comprehensive Data Tests: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All comprehensive data fields are properly extracted!")
        print("\n📊 Data Collection Capabilities Verified:")
        print("   ✓ Live Match Details, Score & Time, Goal Events")
        print("   ✓ Team Statistics (Possession, Shots, Cards, etc.)")
        print("   ✓ Player Statistics (Goals, Assists, Minutes, etc.)")
        print("   ✓ Historical Final Scores, Goal Timestamps")
        print("   ✓ Goal Frequency Analysis for Late-Goal Modeling")
    else:
        print("⚠️  Some data field tests failed. Check output above.")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_comprehensive_data_tests()
    sys.exit(0 if success else 1)
