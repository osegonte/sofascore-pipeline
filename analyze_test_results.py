#!/usr/bin/env python3
"""
Analyze Stage 4 test results and provide recommendations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine
from sqlalchemy import text

def analyze_current_data_quality():
    """Analyze current data quality based on test results"""
    print("SofaScore Pipeline - Stage 4 Results Analysis")
    print("=" * 50)
    
    try:
        with engine.connect() as conn:
            # Get comprehensive data overview
            result = conn.execute(text("""
                SELECT 
                    'live_matches' as table_name,
                    COUNT(*) as total_records,
                    COUNT(home_team) as complete_home_team,
                    COUNT(away_team) as complete_away_team,
                    COUNT(competition) as complete_competition,
                    MAX(scraped_at) as last_updated
                FROM live_matches
                UNION ALL
                SELECT 
                    'goal_events' as table_name,
                    COUNT(*) as total_records,
                    COUNT(scoring_player) as complete_scoring_player,
                    COUNT(team_side) as complete_team_side,
                    COUNT(exact_timestamp) as complete_timestamp,
                    MAX(scraped_at) as last_updated
                FROM goal_events
                UNION ALL
                SELECT 
                    'fixtures' as table_name,
                    COUNT(*) as total_records,
                    COUNT(tournament) as complete_tournament,
                    COUNT(venue) as complete_venue,
                    COUNT(status) as complete_status,
                    MAX(scraped_at) as last_updated
                FROM fixtures
            """))
            
            print("\n📊 DATA QUALITY ANALYSIS:")
            print("-" * 30)
            
            for row in result:
                table_name = row[0]
                total = row[1]
                print(f"\n{table_name.upper()}:")
                print(f"  Total records: {total}")
                print(f"  Last updated: {row[5]}")
                
                if table_name == 'live_matches':
                    home_pct = (row[2] / total * 100) if total > 0 else 0
                    away_pct = (row[3] / total * 100) if total > 0 else 0
                    comp_pct = (row[4] / total * 100) if total > 0 else 0
                    print(f"  Home team completeness: {home_pct:.1f}%")
                    print(f"  Away team completeness: {away_pct:.1f}%")
                    print(f"  Competition completeness: {comp_pct:.1f}%")
                
                elif table_name == 'goal_events':
                    player_pct = (row[2] / total * 100) if total > 0 else 0
                    team_pct = (row[3] / total * 100) if total > 0 else 0
                    time_pct = (row[4] / total * 100) if total > 0 else 0
                    print(f"  Scoring player completeness: {player_pct:.1f}%")
                    print(f"  Team side completeness: {team_pct:.1f}%")
                    print(f"  Timestamp completeness: {time_pct:.1f}%")
                
                elif table_name == 'fixtures':
                    tourn_pct = (row[2] / total * 100) if total > 0 else 0
                    venue_pct = (row[3] / total * 100) if total > 0 else 0
                    status_pct = (row[4] / total * 100) if total > 0 else 0
                    print(f"  Tournament completeness: {tourn_pct:.1f}%")
                    print(f"  Venue completeness: {venue_pct:.1f}%")
                    print(f"  Status completeness: {status_pct:.1f}%")
            
            # Goal timing analysis
            print(f"\n⚽ GOAL TIMING ANALYSIS:")
            print("-" * 25)
            
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_goals,
                    COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                    COUNT(*) FILTER (WHERE total_minute < 0 OR total_minute > 120) as impossible_goals,
                    ROUND(AVG(total_minute), 1) as avg_minute,
                    COUNT(*) FILTER (WHERE time_interval = '0-15') as goals_0_15,
                    COUNT(*) FILTER (WHERE time_interval = '76-90') as goals_76_90,
                    COUNT(*) FILTER (WHERE time_interval = '90+') as goals_90_plus
                FROM goal_events
                WHERE total_minute IS NOT NULL
            """))
            
            row = result.fetchone()
            if row:
                total_goals = row[0]
                late_goals = row[1]
                impossible_goals = row[2]
                avg_minute = row[3]
                
                print(f"  Total goals with timing: {total_goals}")
                print(f"  Late goals (75+ min): {late_goals} ({(late_goals/total_goals*100):.1f}%)")
                print(f"  Impossible timing goals: {impossible_goals}")
                print(f"  Average goal minute: {avg_minute}")
                print(f"  Early goals (0-15 min): {row[4]}")
                print(f"  Late goals (76-90 min): {row[5]}")
                print(f"  Injury time goals (90+ min): {row[6]}")
        
        # Test results summary based on your output
        print(f"\n🎯 STAGE 4 TEST RESULTS SUMMARY:")
        print("-" * 35)
        print("✅ Overall Grade: B (85.5/100)")
        print("✅ Data Quality Monitoring: PASSED")
        print("✅ End-to-End Integration: PASSED")
        print("⚠️  Data Accuracy Tests: SKIPPED (import issues)")
        print("⚠️  Reliability Tests: SKIPPED (import issues)")
        print("⚠️  Performance Tests: SKIPPED (missing psutil)")
        
        print(f"\n📋 KEY FINDINGS:")
        print("-" * 15)
        print("🟢 Strengths:")
        print("   • Database connectivity: 100% successful")
        print("   • Data freshness: All tables updated within 2 hours")
        print("   • Goal timing logic: Working correctly")
        print("   • API connectivity: Successful (448 fixtures retrieved)")
        print("   • Data consistency: 100% referential integrity")
        
        print("\n🟡 Areas for Improvement:")
        print("   • Goal events player names: Only 43.1% complete")
        print("   • Team statistics: Very low completeness (12.4%)")
        print("   • Venue information: 0% complete for fixtures")
        print("   • Team side assignment: 0% complete for goals")
        
        print(f"\n🔧 RECOMMENDED ACTIONS:")
        print("-" * 20)
        print("1. Fix import issues in test modules")
        print("2. Improve data extraction for player names and team sides")
        print("3. Enhance team statistics collection")
        print("4. Add venue information to fixture scraping")
        print("5. Investigate 2 goals with impossible timing")
        
        print(f"\n🚀 PRODUCTION READINESS: CONDITIONAL")
        print("-" * 35)
        print("• Core functionality: ✅ Ready")
        print("• Data quality: ⚠️  Needs improvement")
        print("• Testing coverage: ⚠️  Needs completion")
        print("• Monitoring: ✅ Ready")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    success = analyze_current_data_quality()
    sys.exit(0 if success else 1)
