"""
Main application runner for the SofaScore data pipeline.
"""

import asyncio
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import click

try:
    from src.scrapers.sofascore import LiveMatchTracker, SofaScoreAPI
    from src.storage.hybrid_database import HybridDatabaseManager as DatabaseManager
    from src.utils.logging import setup_logging, get_logger
    from config.simple_settings import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root and have installed dependencies")
    sys.exit(1)

# Setup logging
setup_logging()
logger = get_logger(__name__)


class PipelineManager:
    """Main pipeline manager that coordinates all components."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.live_tracker = LiveMatchTracker()
        self.running = False
        self._shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize all components."""
        logger.info("Initializing SofaScore pipeline...")
        
        try:
            # Initialize database
            await self.db_manager.initialize()
            logger.info("Database initialized")
            
            # Test SofaScore API connectivity
            async with SofaScoreAPI() as api:
                test_matches = await api.get_live_matches()
                logger.info(f"API connectivity test: found {len(test_matches)} live matches")
            
            logger.info("Pipeline initialization completed")
            
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    
    async def start_live_tracking(self):
        """Start the live match tracking process."""
        logger.info("Starting live match tracking...")
        self.running = True
        
        try:
            # Start the live tracker in the background
            tracker_task = asyncio.create_task(
                self.live_tracker.run_continuous_tracking()
            )
            
            # Start monitoring tasks
            monitor_task = asyncio.create_task(self._monitoring_loop())
            cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            # Cancel all tasks
            logger.info("Shutting down live tracking...")
            tracker_task.cancel()
            monitor_task.cancel()
            cleanup_task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(tracker_task, monitor_task, cleanup_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error in live tracking: {e}")
            raise
        finally:
            self.running = False
    
    async def _monitoring_loop(self):
        """Monitor pipeline health and performance."""
        while self.running:
            try:
                # Get scraping statistics
                stats = await self.db_manager.get_scraping_stats(hours=1)
                
                if stats:
                    logger.info("Pipeline Stats (last hour):")
                    for job_stat in stats.get('job_statistics', []):
                        logger.info(f"  Jobs {job_stat['status']}: {job_stat['count']}")
                    
                    for vol_stat in stats.get('volume_statistics', []):
                        logger.info(f"  {vol_stat['table_name']}: {vol_stat['record_count']} records")
                
                # Wait 10 minutes before next monitoring cycle
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def _cleanup_loop(self):
        """Periodic cleanup of old data."""
        while self.running:
            try:
                # Run cleanup once per day
                await asyncio.sleep(86400)  # 24 hours
                
                logger.info("Starting periodic cleanup...")
                deleted_count = await self.db_manager.cleanup_old_data(days=7)
                logger.info(f"Cleanup completed: {deleted_count} records deleted")
                
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of the pipeline."""
        logger.info("Starting pipeline shutdown...")
        self.running = False
        self._shutdown_event.set()
        
        # Close database connections
        await self.db_manager.close()
        logger.info("Pipeline shutdown completed")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


class CLIRunner:
    """Command-line interface for the pipeline."""
    
    def __init__(self):
        self.pipeline = PipelineManager()
    
    async def run_live_mode(self):
        """Run in live tracking mode."""
        logger.info("Starting SofaScore pipeline in live mode")
        
        try:
            await self.pipeline.initialize()
            self.pipeline.setup_signal_handlers()
            await self.pipeline.start_live_tracking()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            sys.exit(1)
        finally:
            await self.pipeline.shutdown()
    
    async def run_discovery_mode(self):
        """Run API discovery to find available endpoints."""
        logger.info("Running SofaScore API discovery...")
        
        try:
            async with SofaScoreAPI() as api:
                # Get current live matches
                live_matches = await api.get_live_matches()
                logger.info(f"Found {len(live_matches)} live matches")
                
                if live_matches:
                    # Test different endpoints on first match
                    test_match = live_matches[0]
                    logger.info(f"Testing endpoints on match: {test_match.home_team} vs {test_match.away_team}")
                    
                    endpoints = {
                        'feed': api.get_match_feed,
                        'events': api.get_match_events,
                        'statistics': api.get_match_statistics,
                        'lineups': api.get_match_lineups,
                        'momentum': api.get_momentum_data,
                    }
                    
                    for endpoint_name, endpoint_func in endpoints.items():
                        try:
                            data = await endpoint_func(test_match.match_id)
                            if data:
                                logger.info(f"✓ {endpoint_name}: Working ({len(str(data))} chars)")
                            else:
                                logger.warning(f"✗ {endpoint_name}: No data")
                        except Exception as e:
                            logger.error(f"✗ {endpoint_name}: Error - {e}")
                
                # Get today's matches
                todays_matches = await api.get_todays_matches()
                logger.info(f"Found {len(todays_matches)} matches today")
                
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            sys.exit(1)
    
    async def run_test_mode(self, match_id: Optional[int] = None):
        """Run test scraping on a specific match."""
        logger.info("Running test scraping...")
        
        try:
            await self.pipeline.initialize()
            
            if match_id:
                # Test specific match
                success = await self.pipeline.live_tracker.scrape_match_data(match_id)
                logger.info(f"Test scraping match {match_id}: {'Success' if success else 'Failed'}")
            else:
                # Find a live match to test
                async with SofaScoreAPI() as api:
                    live_matches = await api.get_live_matches()
                    
                    if live_matches:
                        test_match = live_matches[0]
                        logger.info(f"Testing on live match: {test_match.home_team} vs {test_match.away_team}")
                        success = await self.pipeline.live_tracker.scrape_match_data(test_match.match_id)
                        logger.info(f"Test scraping: {'Success' if success else 'Failed'}")
                    else:
                        logger.warning("No live matches found for testing")
                        
        except Exception as e:
            logger.error(f"Test error: {e}")
            sys.exit(1)
        finally:
            await self.pipeline.shutdown()
    
    async def show_stats(self, hours: int = 24):
        """Show pipeline statistics."""
        logger.info(f"Getting pipeline statistics for last {hours} hours...")
        
        try:
            await self.pipeline.initialize()
            
            stats = await self.pipeline.db_manager.get_scraping_stats(hours)
            
            if stats:
                print(f"\n📊 Pipeline Statistics (Last {hours} hours)")
                print("=" * 50)
                
                # Job statistics
                print("\n🔄 Job Statistics:")
                for job_stat in stats.get('job_statistics', []):
                    print(f"  {job_stat['status'].title()}: {job_stat['count']} jobs")
                    if job_stat.get('avg_duration'):
                        print(f"    Avg Duration: {job_stat['avg_duration']:.1f}s")
                    if job_stat.get('total_successful'):
                        print(f"    Successful Requests: {job_stat['total_successful']}")
                    if job_stat.get('total_failed'):
                        print(f"    Failed Requests: {job_stat['total_failed']}")
                
                # Volume statistics
                print("\n📈 Data Volume:")
                for vol_stat in stats.get('volume_statistics', []):
                    table_name = vol_stat['table_name'].replace('_', ' ').title()
                    print(f"  {table_name}: {vol_stat['record_count']} records")
                    print(f"    Unique Matches: {vol_stat['unique_matches']}")
                
                # Live matches
                live_data = await self.pipeline.db_manager.get_live_matches_data()
                print(f"\n⚽ Active Matches: {len(live_data)}")
                
            else:
                print("No statistics available")
                
        except Exception as e:
            logger.error(f"Stats error: {e}")
            sys.exit(1)
        finally:
            await self.pipeline.shutdown()


# CLI Commands
@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--config', help='Configuration file path')
def cli(debug, config):
    """SofaScore Data Pipeline CLI."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    if config:
        logger.info(f"Using config file: {config}")


@cli.command()
def live():
    """Start live match tracking."""
    runner = CLIRunner()
    asyncio.run(runner.run_live_mode())


@cli.command()
def discover():
    """Discover available SofaScore API endpoints."""
    runner = CLIRunner()
    asyncio.run(runner.run_discovery_mode())


@cli.command()
@click.option('--match-id', type=int, help='Specific match ID to test')
def test(match_id):
    """Test scraping functionality."""
    runner = CLIRunner()
    asyncio.run(runner.run_test_mode(match_id))


@cli.command()
@click.option('--hours', default=24, help='Number of hours to show stats for')
def stats(hours):
    """Show pipeline statistics."""
    runner = CLIRunner()
    asyncio.run(runner.show_stats(hours))


@cli.command()
@click.option('--days', default=7, help='Delete data older than N days')
@click.confirmation_option(prompt='Are you sure you want to delete old data?')
def cleanup(days):
    """Clean up old data."""
    async def run_cleanup():
        pipeline = PipelineManager()
        try:
            await pipeline.initialize()
            deleted = await pipeline.db_manager.cleanup_old_data(days)
            logger.info(f"Deleted {deleted} old records")
        finally:
            await pipeline.shutdown()
    
    asyncio.run(run_cleanup())


def main():
    """Main entry point."""
    try:
        # Validate configuration
        validation_errors = settings.validate()
        if validation_errors:
            logger.error(f"Configuration errors: {', '.join(validation_errors)}")
            sys.exit(1)
        
        # Run CLI
        cli()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()