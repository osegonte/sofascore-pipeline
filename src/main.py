#!/usr/bin/env python3
"""
Enhanced SofaScore Data Collection Pipeline - Fixed Main Entry Point
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from live_scraper import LiveMatchScraper
from fixture_scraper import FixtureScraper  
from historical_scraper import HistoricalScraper
from utils import setup_logging

def main():
    """Enhanced main pipeline with comprehensive data collection and validation"""
    logger = setup_logging()
    
    print("SofaScore Data Collection Pipeline - FIXED VERSION")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 FIXING ALL BLANK COLUMN ISSUES:")
    print("✓ Fixed API endpoints and data extraction")
    print("✓ Enhanced venue, possession, and player statistics collection")
    print("✓ Improved error handling and fallback strategies")
    print("✓ Complete unified data generation")
    
    try:
        # Initialize enhanced scrapers
        logger.info("Initializing fixed scrapers...")
        live_scraper = LiveMatchScraper()
        fixture_scraper = FixtureScraper()
        historical_scraper = HistoricalScraper()
        
        os.makedirs('exports', exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print("\n" + "="*60)
        print("1. LIVE MATCH DATA COLLECTION (FIXED)")
        print("="*60)
        
        live_data = live_scraper.scrape_all_live_matches_comprehensive()
        print(f"✓ Found {len(live_data)} live matches")
        
        if live_data:
            live_dfs = live_scraper.to_comprehensive_dataframes(live_data)
            
            for df_name, df in live_dfs.items():
                if not df.empty:
                    filename = f"exports/FIXED_live_{df_name}_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    
                    # Check for blank columns
                    blank_cols = [col for col in df.columns if df[col].isna().all()]
                    populated_cols = len(df.columns) - len(blank_cols)
                    
                    print(f"   📄 {filename}")
                    print(f"      Records: {len(df)}, Fields: {populated_cols}/{len(df.columns)} populated")
                    
                    if blank_cols:
                        print(f"      ⚠️  Blank columns: {blank_cols[:3]}...")
                    else:
                        print(f"      ✅ All columns populated!")
        
        print("\n" + "="*60)
        print("2. UPCOMING FIXTURES COLLECTION (ENHANCED)")
        print("="*60)
        
        fixtures_data = fixture_scraper.get_upcoming_fixtures(days_ahead=7)
        print(f"✓ Found {len(fixtures_data)} upcoming fixtures")
        
        if fixtures_data:
            fixtures_df = fixture_scraper.to_dataframe(fixtures_data)
            filename = f"exports/FIXED_fixtures_{timestamp}.csv"
            fixtures_df.to_csv(filename, index=False)
            
            blank_cols = [col for col in fixtures_df.columns if fixtures_df[col].isna().all()]
            print(f"   📄 {filename} ({len(fixtures_df)} fixtures)")
            print(f"   📊 Data completeness: {len(fixtures_df.columns) - len(blank_cols)}/{len(fixtures_df.columns)} fields")
        
        print("\n" + "="*60)
        print("3. HISTORICAL MATCH DATA COLLECTION (FIXED)")
        print("="*60)
        
        historical_data = historical_scraper.scrape_historical_comprehensive(days_back=5)
        recent_matches = len(historical_data.get('recent_matches', []))
        print(f"✓ Found {recent_matches} recent completed matches")
        
        if historical_data.get('recent_matches'):
            historical_dfs = historical_scraper.to_comprehensive_dataframes(historical_data)
            
            for df_name, df in historical_dfs.items():
                if not df.empty:
                    filename = f"exports/FIXED_historical_{df_name}_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    
                    blank_cols = [col for col in df.columns if df[col].isna().all()]
                    populated_pct = ((len(df.columns) - len(blank_cols)) / len(df.columns)) * 100
                    
                    print(f"   📄 {filename}")
                    print(f"      Records: {len(df)}, Completeness: {populated_pct:.1f}%")
        
        print("\n" + "="*60)
        print("4. DATA VALIDATION AND SUMMARY")
        print("="*60)
        
        # Count exported files and check quality
        export_files = [f for f in os.listdir('exports') if f.startswith('FIXED_') and f.endswith(f'{timestamp}.csv')]
        total_records = 0
        total_fields = 0
        populated_fields = 0
        
        print(f"📊 Generated {len(export_files)} FIXED data files:")
        
        for file in sorted(export_files):
            try:
                df = pd.read_csv(os.path.join('exports', file))
                blank_cols = [col for col in df.columns if df[col].isna().all()]
                file_populated = len(df.columns) - len(blank_cols)
                completeness = (file_populated / len(df.columns)) * 100
                
                total_records += len(df)
                total_fields += len(df.columns)
                populated_fields += file_populated
                
                print(f"   • {file}")
                print(f"     Records: {len(df):,}, Completeness: {completeness:.1f}%")
                
                if completeness < 70:
                    print(f"     ⚠️  LOW COMPLETENESS - needs attention")
                elif completeness >= 90:
                    print(f"     ✅ EXCELLENT COMPLETENESS")
                    
            except Exception as e:
                print(f"   ❌ Error reading {file}: {e}")
        
        overall_completeness = (populated_fields / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"\n📈 OVERALL PIPELINE RESULTS:")
        print(f"   • Total records collected: {total_records:,}")
        print(f"   • Overall data completeness: {overall_completeness:.1f}%")
        print(f"   • Files exported: {len(export_files)}")
        print(f"   • Timestamp: {timestamp}")
        
        if overall_completeness >= 85:
            print(f"\n🎉 PIPELINE SUCCESS - Data quality excellent!")
            print(f"✅ All major blank column issues have been resolved")
        elif overall_completeness >= 70:
            print(f"\n🟨 PIPELINE GOOD - Minor improvements possible")
            print(f"✅ Most blank column issues resolved")
        else:
            print(f"\n⚠️  PIPELINE NEEDS WORK - Some data quality issues remain")
            print(f"🔧 Continue troubleshooting API endpoints and data extraction")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Run: python database/csv_import.py")
        print(f"2. Run: python database/unified_data_creator.py")
        print(f"3. Run: python database/validate_data_quality.py")
        print(f"4. Check unified dataset for complete field population")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        print(f"❌ Pipeline failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
