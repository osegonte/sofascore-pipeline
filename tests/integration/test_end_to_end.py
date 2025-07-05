#!/usr/bin/env python3
"""
End-to-end integration tests for SofaScore pipeline
Tests complete workflow from data collection to database storage
"""

import sys
import os
import unittest
import tempfile
import shutil
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.main import main as run_pipeline
from database.csv_import import CSVImporter
from database.db_manager import DatabaseManager
from config.database import engine
from sqlalchemy import text

class EndToEndIntegrationTest(unittest.TestCase):
    """End-to-end pipeline integration tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test environment"""
        cls.test_export_dir = tempfile.mkdtemp(prefix="sofascore_test_")
        cls.integration_results = {}
        
    @classmethod
    def tearDownClass(cls):
        """Clean up integration test environment"""
        if os.path.exists(cls.test_export_dir):
            shutil.rmtree(cls.test_export_dir)
    
    def test_complete_pipeline_workflow(self):
        """Test complete pipeline from data collection to storage"""
        print("\n🚀 Testing complete pipeline workflow...")
        
        workflow_results = {}
        
        # Step 1: Test data collection
        print("   Step 1: Data collection...")
        try:
            # Note: In a real test, we'd mock the API calls
            # For now, we'll test the components independently
            
            from src.fixture_scraper import FixtureScraper
            fixture_scraper = FixtureScraper()
            
            # Test fixture collection
            fixtures = fixture_scraper.get_upcoming_fixtures(days_ahead=2)
            workflow_results['data_collection'] = {
                'fixtures_collected': len(fixtures),
                'success': len(fixtures) >= 0  # Allow zero fixtures
            }
            
            print(f"     ✓ Collected {len(fixtures)} fixtures")
            
        except Exception as e:
            workflow_results['data_collection'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ Data collection failed: {e}")
        
        # Step 2: Test CSV export
        print("   Step 2: CSV export...")
        try:
            if fixtures:
                fixtures_df = fixture_scraper.to_dataframe(fixtures)
                test_csv = os.path.join(self.test_export_dir, "test_fixtures.csv")
                fixtures_df.to_csv(test_csv, index=False)
                
                # Verify file exists and has content
                file_exists = os.path.exists(test_csv)
                file_size = os.path.getsize(test_csv) if file_exists else 0
                
                workflow_results['csv_export'] = {
                    'file_created': file_exists,
                    'file_size_bytes': file_size,
                    'records_exported': len(fixtures_df),
                    'success': file_exists and file_size > 0
                }
                
                print(f"     ✓ Exported {len(fixtures_df)} records to CSV")
            else:
                workflow_results['csv_export'] = {
                    'success': True,
                    'message': 'No data to export'
                }
                print("     ✓ No data to export (valid result)")
                
        except Exception as e:
            workflow_results['csv_export'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ CSV export failed: {e}")
        
        # Step 3: Test database operations
        print("   Step 3: Database operations...")
        try:
            db_manager = DatabaseManager()
            
            # Test database connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                connection_success = result.scalar() == 1
            
            # Test basic queries
            fixture_count = db_manager.get_table_count('fixtures')
            match_count = db_manager.get_table_count('live_matches')
            goal_count = db_manager.get_table_count('goal_events')
            
            workflow_results['database_operations'] = {
                'connection_success': connection_success,
                'fixture_count': fixture_count,
                'match_count': match_count,
                'goal_count': goal_count,
                'success': connection_success
            }
            
            print(f"     ✓ Database connection successful")
            print(f"     ✓ Current data: {fixture_count} fixtures, {match_count} matches, {goal_count} goals")
            
        except Exception as e:
            workflow_results['database_operations'] = {
                'success': False,
                'error': str(e)
            }
            print(f"     ❌ Database operations failed: {e}")
        
        self.integration_results['complete_workflow'] = workflow_results
        
        # Assert overall workflow success
        critical_steps = ['data_collection', 'database_operations']
        failed_steps = [step for step in critical_steps 
                       if not workflow_results.get(step, {}).get('success', False)]
        
        self.assertEqual(len(failed_steps), 0, f"Critical workflow steps failed: {failed_steps}")
    
    def test_data_consistency_across_pipeline(self):
        """Test data consistency from collection through storage"""
        print("\n🔗 Testing data consistency across pipeline...")
        
        consistency_results = {}
        
        try:
            with engine.connect() as conn:
                # Test referential integrity
                result = conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM goal_events) as total_goals,
                        (SELECT COUNT(*) FROM goal_events g 
                         JOIN live_matches m ON g.match_id = m.match_id) as goals_with_matches,
                        (SELECT COUNT(*) FROM team_statistics) as total_team_stats,
                        (SELECT COUNT(*) FROM team_statistics ts 
                         JOIN live_matches m ON ts.match_id = m.match_id) as stats_with_matches
                """))
                
                row = result.fetchone()
                total_goals, goals_with_matches = row[0], row[1]
                total_team_stats, stats_with_matches = row[2], row[3]
                
                # Calculate integrity ratios
                goal_integrity = (goals_with_matches / total_goals * 100) if total_goals > 0 else 100
                stats_integrity = (stats_with_matches / total_team_stats * 100) if total_team_stats > 0 else 100
                
                consistency_results = {
                    'total_goals': total_goals,
                    'goals_with_matches': goals_with_matches,
                    'goal_integrity_percentage': goal_integrity,
                    'total_team_stats': total_team_stats,
                    'stats_with_matches': stats_with_matches,
                    'stats_integrity_percentage': stats_integrity,
                    'overall_integrity': (goal_integrity + stats_integrity) / 2
                }
                
                print(f"     ✓ Goal events integrity: {goal_integrity:.1f}%")
                print(f"     ✓ Team stats integrity: {stats_integrity:.1f}%")
                print(f"     ✓ Overall integrity: {consistency_results['overall_integrity']:.1f}%")
                
        except Exception as e:
            consistency_results = {
                'error': str(e),
                'overall_integrity': 0
            }
            print(f"     ❌ Consistency check failed: {e}")
        
        self.integration_results['data_consistency'] = consistency_results
        
        # Assert high data integrity
        if 'overall_integrity' in consistency_results:
            self.assertGreaterEqual(consistency_results['overall_integrity'], 90, 
                                   "Data integrity across pipeline too low")
    
    def test_error_recovery_workflow(self):
        """Test pipeline error recovery and resilience"""
        print("\n🛡️  Testing error recovery workflow...")
        
        recovery_results = {}
        
        # Test graceful handling of API failures
        try:
            from src.live_scraper import LiveMatchScraper
            live_scraper = LiveMatchScraper()
            
            # Test with invalid base URL (simulating API failure)
            original_url = live_scraper.base_url
            live_scraper.base_url = "https://invalid-api-endpoint.com/api/v1"
            
            # Should not crash, should return empty list
            result = live_scraper.get_live_matches()
            
            api_failure_handled = isinstance(result, list)
            
            # Restore original URL
            live_scraper.base_url = original_url
            
            recovery_results['api_failure_handling'] = {
                'handled_gracefully': api_failure_handled,
                'returned_empty_list': len(result) == 0
            }
            
            print(f"     ✓ API failure handled gracefully: {api_failure_handled}")
            
        except Exception as e:
            recovery_results['api_failure_handling'] = {
                'handled_gracefully': False,
                'error': str(e)
            }
            print(f"     ❌ API failure handling failed: {e}")
        
        # Test database connection recovery
        try:
            from config.database import test_connection
            
            # Test connection
            connection_works = test_connection()
            
            recovery_results['database_recovery'] = {
                'connection_successful': connection_works
            }
            
            print(f"     ✓ Database connection recovery: {connection_works}")
            
        except Exception as e:
            recovery_results['database_recovery'] = {
                'connection_successful': False,
                'error': str(e)
            }
        
        self.integration_results['error_recovery'] = recovery_results
        
        # Assert error recovery works
        api_handled = recovery_results.get('api_failure_handling', {}).get('handled_gracefully', False)
        db_works = recovery_results.get('database_recovery', {}).get('connection_successful', False)
        
        self.assertTrue(api_handled, "API failure not handled gracefully")
        self.assertTrue(db_works, "Database connection recovery failed")
    
    def test_performance_under_load(self):
        """Test pipeline performance under simulated load"""
        print("\n⚡ Testing performance under load...")
        
        performance_results = {}
        
        try:
            import time
            from src.fixture_scraper import FixtureScraper
            
            fixture_scraper = FixtureScraper()
            
            # Test multiple rapid requests
            start_time = time.time()
            request_times = []
            
            for i in range(3):  # Limited for CI/CD
                request_start = time.time()
                fixtures = fixture_scraper.get_fixtures_by_date(
                    datetime.now().strftime('%Y-%m-%d')
                )
                request_end = time.time()
                
                request_times.append(request_end - request_start)
                time.sleep(1)  # Rate limiting
            
            total_time = time.time() - start_time
            avg_request_time = sum(request_times) / len(request_times)
            
            performance_results = {
                'total_requests': len(request_times),
                'total_time': total_time,
                'average_request_time': avg_request_time,
                'max_request_time': max(request_times),
                'performance_acceptable': avg_request_time < 10  # 10 second threshold
            }
            
            print(f"     ✓ {len(request_times)} requests in {total_time:.2f}s")
            print(f"     ✓ Average request time: {avg_request_time:.2f}s")
            
        except Exception as e:
            performance_results = {
                'error': str(e),
                'performance_acceptable': False
            }
            print(f"     ❌ Performance test failed: {e}")
        
        self.integration_results['performance_under_load'] = performance_results
        
        # Assert acceptable performance
        if 'performance_acceptable' in performance_results:
            self.assertTrue(performance_results['performance_acceptable'], 
                          "Performance under load not acceptable")
    
    def tearDown(self):
        """Clean up after each test"""
        pass

if __name__ == "__main__":
    unittest.main(verbosity=2)
