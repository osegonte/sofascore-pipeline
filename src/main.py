#!/usr/bin/env python3
"""
SofaScore Data Collection Pipeline - Enhanced Main Entry Point
Stage 2: Comprehensive Data Collection Implementation
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Add current directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from live_scraper import LiveMatchScraper
from fixture_scraper import FixtureScraper
from historical_scraper import HistoricalScraper
from utils import setup_logging

def main():
    """Enhanced main pipeline execution with comprehensive data collection"""
    logger = setup_logging()
    
    print("SofaScore Data Collection Pipeline - Enhanced Stage 2")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nCollecting comprehensive data including:")
    print("✓ Live Match Details, Score & Time, Goal Events, Team & Player Stats")
    print("✓ Historical Match Data, Final Scores, Goal Times, Goal Frequency")
    print("✓ Upcoming Fixtures with complete scheduling data")
    
    try:
        # Initialize enhanced scrapers
        logger.info("Initializing enhanced scrapers...")
        live_scraper = LiveMatchScraper()
        fixture_scraper = FixtureScraper()
        historical_scraper = HistoricalScraper()
        
        # Create exports directory
        os.makedirs('exports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print("\n" + "="*60)
        print("1. LIVE MATCH DATA COLLECTION")
        print("="*60)
        live_data = live_scraper.scrape_all_live_matches_comprehensive()
        print(f"✓ Found {len(live_data)} live matches with comprehensive data")
        
        if live_data:
            live_dfs = live_scraper.to_comprehensive_dataframes(live_data)
            
            for df_name, df in live_dfs.items():
                if not df.empty:
                    filename = f"exports/live_{df_name}_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    print(f"   📄 Exported: {filename} ({len(df)} records)")
                    
                    # Show sample of key data
                    if df_name == 'goal_events' and len(df) > 0:
                        print(f"      Sample goals: {df['total_minute'].tolist()[:5]} minutes")
                    elif df_name == 'team_statistics' and len(df) > 0:
                        print(f"      Sample possession: {df['possession_percentage'].dropna().tolist()[:3]}%")
        
        print("\n" + "="*60)
        print("2. UPCOMING FIXTURES COLLECTION")
        print("="*60)
        fixtures_data = fixture_scraper.get_upcoming_fixtures(days_ahead=7)
        print(f"✓ Found {len(fixtures_data)} upcoming fixtures")
        
        if fixtures_data:
            fixtures_df = fixture_scraper.to_dataframe(fixtures_data)
            filename = f"exports/fixtures_comprehensive_{timestamp}.csv"
            fixtures_df.to_csv(filename, index=False)
            print(f"   📄 Exported: {filename} ({len(fixtures_df)} fixtures)")
            
            # Show fixture distribution
            if not fixtures_df.empty and 'kickoff_date' in fixtures_df.columns:
                date_counts = fixtures_df['kickoff_date'].value_counts().head(3)
                print(f"      Next few days: {dict(date_counts)}")
        
        print("\n" + "="*60)
        print("3. HISTORICAL MATCH DATA COLLECTION")
        print("="*60)
        historical_data = historical_scraper.scrape_historical_comprehensive(days_back=5)
        recent_matches = len(historical_data.get('recent_matches', []))
        print(f"✓ Found {recent_matches} recent completed matches")
        
        if historical_data.get('recent_matches') or historical_data.get('specific_matches'):
            historical_dfs = historical_scraper.to_comprehensive_dataframes(historical_data)
            
            for df_name, df in historical_dfs.items():
                if not df.empty:
                    filename = f"exports/historical_{df_name}_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    print(f"   📄 Exported: {filename} ({len(df)} records)")
            
            # Show comprehensive goal analysis
            goal_analysis = historical_data.get('comprehensive_goal_analysis', {})
            if goal_analysis:
                print(f"\n   🎯 GOAL TIMING ANALYSIS:")
                print(f"      • Total goals analyzed: {goal_analysis.get('total_goals_analyzed', 0)}")
                print(f"      • Late goals (75+ min): {goal_analysis.get('late_goals_count', 0)} ({goal_analysis.get('late_goals_percentage', 0):.1f}%)")
                print(f"      • Average goal minute: {goal_analysis.get('average_goal_minute', 0):.1f}")
                print(f"      • Matches with late goals: {goal_analysis.get('percentage_matches_with_late_goals', 0):.1f}%")
                
                # Show goal distribution
                intervals = goal_analysis.get('goals_by_15min_intervals', {})
                if intervals:
                    print(f"      • Goal distribution by 15-min intervals:")
                    for interval, count in intervals.items():
                        print(f"        {interval}: {count} goals")
        
        print("\n" + "="*60)
        print("4. DATA SUMMARY")
        print("="*60)
        
        # Count all exported files
        export_files = [f for f in os.listdir('exports') if f.endswith(f'{timestamp}.csv')]
        print(f"✅ Pipeline execution completed successfully!")
        print(f"📊 Generated {len(export_files)} comprehensive data files:")
        
        for file in sorted(export_files):
            file_path = os.path.join('exports', file)
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                print(f"   • {file}: {len(df)} records")
        
        print(f"\n📁 All files saved in: exports/")
        print(f"🕐 Files timestamped: {timestamp}")
        
        print(f"\n🎯 STAGE 2 COMPLETE - All Required Data Collected:")
        print(f"   ✓ Live Match Details, Scores, Goal Events, Team & Player Stats")
        print(f"   ✓ Historical Final Scores, Goal Timestamps, Goal Frequency Analysis")
        print(f"   ✓ Upcoming Fixtures with complete scheduling information")
        print(f"\n🚀 Ready for Stage 3: Database Integration & Storage")
        
    except Exception as e:
        logger.error(f"Enhanced pipeline execution failed: {e}")
        print(f"❌ Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
