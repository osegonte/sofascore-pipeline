#!/usr/bin/env python3
"""
Direct ETL Pipeline Usage - Bypass CLI issues and use ETL directly.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.etl.pipeline import ETLPipeline, DataQualityChecker
from src.cli.etl_commands import ETLCommandRunner
from src.storage.hybrid_database import HybridDatabaseManager


async def run_etl_processing(limit=None, dry_run=False):
    """Run ETL processing directly."""
    print("🔄 Running ETL Processing")
    print("=" * 30)
    
    runner = ETLCommandRunner()
    await runner.run_etl_processing(limit, dry_run)


async def run_quality_checks():
    """Run data quality checks directly."""
    print("🔍 Running Quality Checks")
    print("=" * 30)
    
    runner = ETLCommandRunner()
    await runner.run_quality_checks()


async def run_complete_pipeline():
    """Run complete ETL pipeline with live data."""
    print("🚀 Complete ETL Pipeline Run")
    print("=" * 40)
    
    try:
        # Step 1: Initialize
        print("\n1️⃣ Initializing pipeline...")
        pipeline = ETLPipeline()
        await pipeline.initialize()
        
        storage_info = pipeline.db_manager.get_storage_info()
        print(f"   Storage: {storage_info['type']}")
        
        # Step 2: Check for existing data
        if 'data_summary' in storage_info:
            summary = storage_info['data_summary']
            existing_data = summary.get('matches_raw', 0) + summary.get('events_raw', 0)
            print(f"   Existing data: {existing_data} records")
            
            # If no data, collect some live data first
            if existing_data == 0:
                print("\n2️⃣ Collecting live data...")
                from src.scrapers.sofascore import SofaScoreAPI
                
                async with SofaScoreAPI() as api:
                    live_matches = await api.get_live_matches()
                    print(f"   Found {len(live_matches)} live matches")
                    
                    if live_matches:
                        # Collect data for first live match
                        test_match = live_matches[0]
                        print(f"   Collecting: {test_match.home_team} vs {test_match.away_team}")
                        
                        # Get all available data
                        feed_data = await api.get_match_feed(test_match.match_id)
                        if feed_data:
                            await pipeline.db_manager.save_match_raw(test_match.match_id, 'feed', feed_data)
                            print("   ✅ Feed data collected")
                        
                        events_data = await api.get_match_events(test_match.match_id)
                        if events_data:
                            await pipeline.db_manager.save_events_raw(test_match.match_id, events_data)
                            print("   ✅ Events data collected")
                        
                        stats_data = await api.get_match_statistics(test_match.match_id)
                        if stats_data:
                            await pipeline.db_manager.save_stats_raw(test_match.match_id, None, stats_data)
                            print("   ✅ Statistics data collected")
        
        # Step 3: Run ETL processing
        print("\n3️⃣ Processing raw data...")
        report = await pipeline.process_raw_data(limit=5)
        
        summary = report['processing_summary']
        entities = report['entities_discovered']
        
        print("   ✅ ETL processing completed")
        print(f"   Duration: {summary['duration_seconds']:.2f}s")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Matches: {summary['processed_matches']}")
        print(f"   Events: {summary['processed_events']}")
        print(f"   Competitions: {entities['competitions']}")
        print(f"   Teams: {entities['teams']}")
        
        # Step 4: Quality assessment
        print("\n4️⃣ Quality assessment...")
        checker = DataQualityChecker(pipeline)
        quality_report = await checker.run_quality_checks()
        
        print(f"   Overall Score: {quality_report['overall_score']:.1f}/100")
        
        for check_name, result in quality_report['quality_checks'].items():
            status = result.get('status', 'unknown')
            emoji = '✅' if status == 'good' else '⚠️'
            print(f"   {emoji} {check_name.replace('_', ' ').title()}")
        
        await pipeline.close()
        
        print("\n🎉 Complete Pipeline Run Successful!")
        return True
        
    except Exception as e:
        print(f"❌ Pipeline run failed: {e}")
        return False


async def demo_data_enrichment():
    """Demonstrate data enrichment capabilities."""
    print("📈 Data Enrichment Demonstration")
    print("=" * 40)
    
    from src.utils.data_validation import DataEnricher
    
    enricher = DataEnricher()
    
    # Sample events to enrich
    sample_events = [
        {'x_coordinate': 95, 'y_coordinate': 50, 'event_type': 'goal', 'minute': 23},
        {'x_coordinate': 75, 'y_coordinate': 30, 'event_type': 'shot', 'minute': 45},
        {'x_coordinate': 92, 'y_coordinate': 48, 'event_type': 'goal', 'minute': 78},
        {'x_coordinate': 85, 'y_coordinate': 60, 'event_type': 'shot', 'minute': 89},
    ]
    
    print("\nEnriching sample events:")
    for i, event in enumerate(sample_events, 1):
        enriched = enricher.enrich_event_data(event)
        
        print(f"\n{i}️⃣ Event {i}:")
        print(f"   Type: {event['event_type']} at minute {event['minute']}")
        print(f"   Position: ({event['x_coordinate']}, {event['y_coordinate']})")
        
        if 'calculated_xg' in enriched:
            print(f"   ⚽ Expected Goals (xG): {enriched['calculated_xg']}")
        
        if 'time_period' in enriched:
            print(f"   ⏰ Time Period: {enriched['time_period']}")


def main():
    """Main function to run different ETL operations."""
    if len(sys.argv) < 2:
        print("🎮 ETL Pipeline Direct Usage")
        print("=" * 40)
        print("\nAvailable commands:")
        print("  python etl_direct_usage.py etl [--limit N] [--dry-run]")
        print("  python etl_direct_usage.py quality")
        print("  python etl_direct_usage.py complete")
        print("  python etl_direct_usage.py enrich")
        print("\nExamples:")
        print("  python etl_direct_usage.py etl --limit 3")
        print("  python etl_direct_usage.py complete")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'etl':
        limit = None
        dry_run = False
        
        if '--limit' in sys.argv:
            try:
                limit_idx = sys.argv.index('--limit') + 1
                limit = int(sys.argv[limit_idx])
            except (IndexError, ValueError):
                print("❌ Invalid limit value")
                return
        
        if '--dry-run' in sys.argv:
            dry_run = True
        
        asyncio.run(run_etl_processing(limit, dry_run))
    
    elif command == 'quality':
        asyncio.run(run_quality_checks())
    
    elif command == 'complete':
        asyncio.run(run_complete_pipeline())
    
    elif command == 'enrich':
        asyncio.run(demo_data_enrichment())
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available: etl, quality, complete, enrich")


if __name__ == "__main__":
    main()