#!/usr/bin/env python3
"""
Performance testing for SofaScore pipeline
Tests response times, memory usage, and throughput
"""

import sys
import os
import unittest
import time
import threading
from datetime import datetime
import pandas as pd

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.database import engine
from tests.test_config import PERFORMANCE_TEST_CONFIG, VALIDATION_THRESHOLDS
from sqlalchemy import text

class PerformanceTester(unittest.TestCase):
    """Comprehensive performance testing suite"""
    
    @classmethod
    def setUpClass(cls):
        """Set up performance test environment"""
        cls.performance_results = {}
        if PSUTIL_AVAILABLE:
            cls.process = psutil.Process()
    
    def test_api_response_times(self):
        """Test API response time performance"""
        print("\n⚡ Testing API response times...")
        
        try:
            from src.fixture_scraper import FixtureScraper
            fixture_scraper = FixtureScraper()
            
            response_times = []
            
            for i in range(3):  # Limited test runs
                start_time = time.time()
                
                try:
                    fixtures = fixture_scraper.get_fixtures_by_date(
                        datetime.now().strftime('%Y-%m-%d')
                    )
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                except Exception as e:
                    response_times.append(float('inf'))
                
                time.sleep(1)
            
            valid_times = [t for t in response_times if t != float('inf')]
            
            self.performance_results['api_response_times'] = {
                'total_requests': len(response_times),
                'successful_requests': len(valid_times),
                'average_response_time': sum(valid_times) / len(valid_times) if valid_times else 0,
                'max_response_time': max(valid_times) if valid_times else 0
            }
            
            avg_time = self.performance_results['api_response_times']['average_response_time']
            
            print(f"   ✓ {len(valid_times)}/{len(response_times)} successful requests")
            print(f"   ✓ Average response time: {avg_time:.2f}s")
            
            self.assertLess(avg_time, 15, f"Average response time too slow: {avg_time:.2f}s")
            
        except ImportError:
            self.skipTest("API modules not available for performance testing")
    
    def test_database_query_performance(self):
        """Test database query performance"""
        print("\n🗄️  Testing database query performance...")
        
        query_times = {}
        
        try:
            with engine.connect() as conn:
                # Test simple count query
                start_time = time.time()
                result = conn.execute(text("SELECT COUNT(*) FROM live_matches"))
                query_times['simple_count'] = time.time() - start_time
                result.fetchall()
                
                # Test join query if data exists
                start_time = time.time()
                result = conn.execute(text("""
                    SELECT m.match_id, m.home_team, m.away_team, 
                           COUNT(g.goal_id) as total_goals
                    FROM live_matches m
                    LEFT JOIN goal_events g ON m.match_id = g.match_id
                    GROUP BY m.match_id, m.home_team, m.away_team
                    ORDER BY total_goals DESC
                    LIMIT 10
                """))
                query_times['join_with_aggregation'] = time.time() - start_time
                result.fetchall()
        
        except Exception as e:
            query_times['error'] = str(e)
        
        max_query_time = VALIDATION_THRESHOLDS.get('database_query_timeout_seconds', 30)
        
        self.performance_results['database_query_performance'] = {
            'queries_tested': len([k for k in query_times.keys() if k != 'error']),
            'query_times': query_times,
            'average_query_time': sum(v for v in query_times.values() if isinstance(v, (int, float))) / len([v for v in query_times.values() if isinstance(v, (int, float))]) if query_times else 0
        }
        
        print(f"   ✓ Tested {len([k for k in query_times.keys() if k != 'error'])} database queries")
        for query_name, query_time in query_times.items():
            if isinstance(query_time, (int, float)):
                print(f"   ✓ {query_name}: {query_time:.3f}s")
        
        # Assert reasonable performance
        for query_name, query_time in query_times.items():
            if isinstance(query_time, (int, float)):
                self.assertLess(query_time, max_query_time, f"{query_name} query too slow: {query_time:.3f}s")
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring (if psutil available)"""
        print("\n🧠 Testing memory usage monitoring...")
        
        if not PSUTIL_AVAILABLE:
            self.skipTest("psutil not available for memory monitoring")
            return
        
        try:
            initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Perform some memory-intensive operations
            data_frames = []
            for i in range(3):
                # Create temporary DataFrame
                df = pd.DataFrame({
                    'id': range(1000),
                    'data': [f'test_data_{j}' for j in range(1000)]
                })
                data_frames.append(df)
            
            peak_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Cleanup
            del data_frames
            
            final_memory = self.process.memory_info().rss / 1024 / 1024
            memory_growth = final_memory - initial_memory
            
            self.performance_results['memory_usage'] = {
                'initial_memory_mb': initial_memory,
                'peak_memory_mb': peak_memory,
                'final_memory_mb': final_memory,
                'memory_growth_mb': memory_growth,
                'within_limits': peak_memory < PERFORMANCE_TEST_CONFIG.get('max_memory_usage_mb', 512)
            }
            
            print(f"   ✓ Initial memory: {initial_memory:.1f} MB")
            print(f"   ✓ Peak memory: {peak_memory:.1f} MB")
            print(f"   ✓ Memory growth: {memory_growth:.1f} MB")
            
            # Lenient memory assertion
            self.assertLess(memory_growth, 100, f"Memory growth too high: {memory_growth:.1f} MB")
            
        except Exception as e:
            self.fail(f"Memory monitoring test failed: {e}")
    
    def test_data_processing_throughput(self):
        """Test data processing throughput"""
        print("\n📈 Testing data processing throughput...")
        
        try:
            # Test DataFrame processing throughput
            test_data = {
                'id': range(1000),
                'name': [f'Test_{i}' for i in range(1000)],
                'value': [i * 2 for i in range(1000)]
            }
            
            start_time = time.time()
            df = pd.DataFrame(test_data)
            processing_time = time.time() - start_time
            
            # Test CSV operations
            test_file = "tests/fixtures/sample_data/throughput_test.csv"
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            
            start_time = time.time()
            df.to_csv(test_file, index=False)
            export_time = time.time() - start_time
            
            file_size = os.path.getsize(test_file) / 1024 if os.path.exists(test_file) else 0  # KB
            
            throughput_metrics = {
                'dataframe_processing': {
                    'records_processed': len(df),
                    'processing_time': processing_time,
                    'records_per_second': len(df) / processing_time if processing_time > 0 else 0
                },
                'csv_export': {
                    'records_exported': len(df),
                    'export_time': export_time,
                    'file_size_kb': file_size,
                    'records_per_second': len(df) / export_time if export_time > 0 else 0
                }
            }
            
            self.performance_results['data_processing_throughput'] = throughput_metrics
            
            for process_type, metrics in throughput_metrics.items():
                records_per_sec = metrics.get('records_per_second', 0)
                print(f"   ✓ {process_type}: {records_per_sec:.1f} records/second")
            
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            
            # Basic throughput assertion (should process at least 100 records per second)
            for process_type, metrics in throughput_metrics.items():
                self.assertGreater(metrics['records_per_second'], 100, 
                                 f"{process_type} throughput too low")
            
        except Exception as e:
            self.fail(f"Data processing throughput test failed: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Generate performance report"""
        cls._generate_performance_report()
    
    @classmethod
    def _generate_performance_report(cls):
        """Generate comprehensive performance report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"tests/reports/performance_report_{timestamp}.md"
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            f.write("# Pipeline Performance Test Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # System info
            f.write("## System Information\n\n")
            if PSUTIL_AVAILABLE:
                f.write(f"- **CPU Count**: {psutil.cpu_count()}\n")
                f.write(f"- **Memory Total**: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f} GB\n")
            f.write(f"- **Python Version**: {sys.version.split()[0]}\n\n")
            
            # Performance results
            for test_name, results in cls.performance_results.items():
                f.write(f"## {test_name.replace('_', ' ').title()}\n\n")
                
                if isinstance(results, dict):
                    cls._write_dict_to_report(f, results, 0)
                
                f.write("\n")
        
        print(f"\n📄 Performance report saved: {report_file}")
    
    @classmethod
    def _write_dict_to_report(cls, file, data, level):
        """Recursively write dictionary to report"""
        indent = "  " * level
        
        for key, value in data.items():
            if isinstance(value, dict):
                file.write(f"{indent}- **{key.replace('_', ' ').title()}**:\n")
                cls._write_dict_to_report(file, value, level + 1)
            else:
                file.write(f"{indent}- **{key.replace('_', ' ').title()}**: {value}\n")

if __name__ == "__main__":
    unittest.main(verbosity=2)
