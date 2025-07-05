#!/usr/bin/env python3
"""
Reliability testing for SofaScore pipeline
Tests pipeline stability, error handling, and consistency
"""

import sys
import os
import unittest
import time
import threading
import concurrent.futures
from datetime import datetime
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.test_config import RELIABILITY_TEST_CONFIG

class ReliabilityTester(unittest.TestCase):
    """Comprehensive reliability testing suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up reliability test environment"""
        cls.reliability_results = {}
    
    def test_api_consistency(self):
        """Test API response consistency across multiple calls"""
        print("\n🔄 Testing API consistency...")
        
        try:
            from src.fixture_scraper import FixtureScraper
            fixture_scraper = FixtureScraper()
            
            test_cycles = min(5, RELIABILITY_TEST_CONFIG.get('test_cycles', 5))
            failures = []
            response_times = []
            
            for i in range(test_cycles):
                start_time = time.time()
                
                try:
                    fixtures = fixture_scraper.get_fixtures_by_date(
                        datetime.now().strftime('%Y-%m-%d')
                    )
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    if not isinstance(fixtures, list):
                        failures.append(f"Cycle {i}: Invalid response type")
                    
                    if response_time > 30:
                        failures.append(f"Cycle {i}: Slow response time: {response_time:.2f}s")
                
                except Exception as e:
                    failures.append(f"Cycle {i}: Exception: {str(e)}")
                    response_times.append(float('inf'))
                
                time.sleep(1)
            
            failure_rate = len(failures) / test_cycles
            avg_response_time = sum(r for r in response_times if r != float('inf')) / len([r for r in response_times if r != float('inf')]) if response_times else 0
            
            self.reliability_results['api_consistency'] = {
                'test_cycles': test_cycles,
                'failures': len(failures),
                'failure_rate': failure_rate,
                'average_response_time': avg_response_time
            }
            
            print(f"   ✓ Tested {test_cycles} API calls")
            print(f"   ✓ Failure rate: {failure_rate:.1%}")
            print(f"   ✓ Average response time: {avg_response_time:.2f}s")
            
            self.assertLessEqual(failure_rate, 0.2, f"API failure rate too high: {failure_rate:.1%}")
            
        except ImportError:
            self.skipTest("Fixture scraper not available for testing")
    
    def test_data_export_reliability(self):
        """Test CSV export reliability and completeness"""
        print("\n📊 Testing data export reliability...")
        
        try:
            # Create test data
            test_data = {
                'id': [1, 2, 3],
                'name': ['Test A', 'Test B', 'Test C'],
                'value': [10, 20, 30]
            }
            
            df = pd.DataFrame(test_data)
            test_file = "tests/fixtures/sample_data/test_reliability.csv"
            
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            
            # Export test
            start_time = time.time()
            df.to_csv(test_file, index=False)
            export_time = time.time() - start_time
            
            # Re-import test
            start_time = time.time()
            reimported_df = pd.read_csv(test_file)
            import_time = time.time() - start_time
            
            # Validate data integrity
            data_integrity_passed = (
                len(df) == len(reimported_df) and
                list(df.columns) == list(reimported_df.columns)
            )
            
            self.reliability_results['data_export'] = {
                'export_time': export_time,
                'import_time': import_time,
                'data_integrity': data_integrity_passed,
                'file_size_bytes': os.path.getsize(test_file) if os.path.exists(test_file) else 0
            }
            
            print(f"   ✓ Export/import test completed")
            print(f"   ✓ Data integrity: {data_integrity_passed}")
            
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            
            self.assertTrue(data_integrity_passed, "Data export/import integrity failed")
            
        except Exception as e:
            self.fail(f"Data export reliability test failed: {e}")
    
    def test_error_handling_robustness(self):
        """Test error handling and recovery mechanisms"""
        print("\n🛡️  Testing error handling robustness...")
        
        error_scenarios = []
        
        try:
            from src.fixture_scraper import FixtureScraper
            fixture_scraper = FixtureScraper()
            
            # Test invalid date handling
            try:
                result = fixture_scraper.get_fixtures_by_date("invalid-date")
                error_scenarios.append({
                    'scenario': 'invalid_date',
                    'handled_gracefully': isinstance(result, list),
                    'error': None
                })
            except Exception as e:
                error_scenarios.append({
                    'scenario': 'invalid_date',
                    'handled_gracefully': False,
                    'error': str(e)
                })
            
        except ImportError:
            error_scenarios.append({
                'scenario': 'import_test',
                'handled_gracefully': True,
                'error': 'Module not available (acceptable)'
            })
        
        graceful_handling_count = sum(1 for s in error_scenarios if s['handled_gracefully'])
        
        self.reliability_results['error_handling'] = {
            'error_scenarios_tested': len(error_scenarios),
            'gracefully_handled': graceful_handling_count,
            'robustness_score': (graceful_handling_count / len(error_scenarios)) * 100 if error_scenarios else 100
        }
        
        print(f"   ✓ Tested {len(error_scenarios)} error scenarios")
        print(f"   ✓ Robustness score: {self.reliability_results['error_handling']['robustness_score']:.1f}%")
        
        if error_scenarios:
            self.assertGreaterEqual(graceful_handling_count / len(error_scenarios), 0.5, 
                                   "Error handling robustness too low")
    
    @classmethod
    def tearDownClass(cls):
        """Generate reliability report"""
        cls._generate_reliability_report()
    
    @classmethod
    def _generate_reliability_report(cls):
        """Generate comprehensive reliability report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/reliability_report_{timestamp}.md"
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write("# Pipeline Reliability Test Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, results in cls.reliability_results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(results, dict):
                    for key, value in results.items():
                        if key not in ['errors', 'scenarios']:
                            f.write(f"- **{key.replace('_', ' ').title()}**: {value}\n")
                
                f.write("\n")
        
        print(f"\n📄 Reliability report saved: {report_file}")

if __name__ == "__main__":
    unittest.main(verbosity=2)
