"""
CLI commands for ETL operations.
"""

import asyncio
from typing import Optional

from ..etl.pipeline import ETLPipeline, DataQualityChecker
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ETLCommandRunner:
    """Runner for ETL CLI commands."""
    
    def __init__(self):
        self.pipeline = ETLPipeline()
    
    async def run_etl_processing(self, limit: Optional[int] = None, dry_run: bool = False):
        """Run ETL processing."""
        try:
            await self.pipeline.initialize()
            
            if dry_run:
                logger.info("Running ETL in dry-run mode (no data will be modified)")
            
            report = await self.pipeline.process_raw_data(limit)
            self._print_processing_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"ETL processing failed: {e}")
            raise
        finally:
            await self.pipeline.close()
    
    async def run_quality_checks(self):
        """Run data quality checks."""
        try:
            await self.pipeline.initialize()
            
            checker = DataQualityChecker(self.pipeline)
            quality_report = await checker.run_quality_checks()
            
            self._print_quality_report(quality_report)
            return quality_report
            
        except Exception as e:
            logger.error(f"Quality checks failed: {e}")
            raise
        finally:
            await self.pipeline.close()
    
    def _print_processing_report(self, report: dict):
        """Print ETL processing report."""
        summary = report['processing_summary']
        entities = report['entities_discovered']
        
        print(f"\n📊 ETL Processing Report")
        print("=" * 50)
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Errors: {summary['errors']}")
        print()
        print("📈 Processing Results:")
        print(f"  Matches: {summary['processed_matches']}")
        print(f"  Events: {summary['processed_events']}")
        print(f"  Statistics: {summary['processed_stats']}")
        print()
        print("🏗️ Entities Discovered:")
        print(f"  Competitions: {entities['competitions']}")
        print(f"  Teams: {entities['teams']}")
        print(f"  Players: {entities['players']}")
    
    def _print_quality_report(self, report: dict):
        """Print data quality report."""
        checks = report['quality_checks']
        overall_score = report['overall_score']
        
        print(f"\n🔍 Data Quality Report")
        print("=" * 50)
        print(f"Overall Quality Score: {overall_score:.1f}/100")
        print()
        
        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            message = check_result.get('message', 'No details available')
            status_emoji = '✅' if status == 'good' else '⚠️' if status == 'warning' else '❌'
            print(f"{status_emoji} {check_name.replace('_', ' ').title()}: {message}")
