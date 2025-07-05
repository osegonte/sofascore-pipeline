#!/usr/bin/env python3
"""
Comprehensive test runner for SofaScore pipeline Stage 4 validation
Runs all test suites and generates combined report
"""

import sys
import os
import unittest
import time
from datetime import datetime
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_suite(test_module, suite_name):
    """Run a specific test suite and capture results"""
    print(f"\n{'='*60}")
    print(f"RUNNING {suite_name.upper()}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Import and run the test module
        suite = unittest.TestLoader().loadTestsFromModule(test_module)
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        end_time = time.time()
        duration = end_time - start_time
        
        return {
            'suite_name': suite_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'duration': duration,
            'status': 'PASSED' if len(result.failures) == 0 and len(result.errors) == 0 else 'FAILED'
        }
        
    except Exception as e:
        return {
            'suite_name': suite_name,
            'tests_run': 0,
            'failures': 1,
            'errors': 0,
            'success_rate': 0,
            'duration': time.time() - start_time,
            'status': 'ERROR',
            'error': str(e)
        }

def main():
    """Run all Stage 4 validation tests"""
    print("SofaScore Pipeline - Stage 4: Comprehensive Validation")
    print("=" * 70)
    print(f"Test execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Import test modules
    test_modules = []
    suite_results = []
    
    try:
        from tests.validation.test_data_accuracy import DataAccuracyValidator
        test_modules.append((DataAccuracyValidator, "Data Accuracy Validation"))
    except ImportError as e:
        print(f"⚠️  Could not import Data Accuracy tests: {e}")
    
    try:
        from tests.validation.test_reliability import ReliabilityTester
        test_modules.append((ReliabilityTester, "Reliability Testing"))
    except ImportError as e:
        print(f"⚠️  Could not import Reliability tests: {e}")
    
    try:
        from tests.performance.test_performance import PerformanceTester
        test_modules.append((PerformanceTester, "Performance Testing"))
    except ImportError as e:
        print(f"⚠️  Could not import Performance tests: {e}")
    
    try:
        from tests.data_quality.test_data_quality import DataQualityMonitor
        test_modules.append((DataQualityMonitor, "Data Quality Monitoring"))
    except ImportError as e:
        print(f"⚠️  Could not import Data Quality tests: {e}")
    
    try:
        from tests.integration.test_end_to_end import EndToEndIntegrationTest
        test_modules.append((EndToEndIntegrationTest, "End-to-End Integration"))
    except ImportError as e:
        print(f"⚠️  Could not import Integration tests: {e}")
    
    # Run all test suites
    overall_start = time.time()
    
    for test_module, suite_name in test_modules:
        try:
            # Create a module instance for testing
            import types
            module_instance = types.ModuleType(test_module.__name__)
            setattr(module_instance, test_module.__name__, test_module)
            
            result = run_test_suite(module_instance, suite_name)
            suite_results.append(result)
            
        except Exception as e:
            print(f"❌ Failed to run {suite_name}: {e}")
            suite_results.append({
                'suite_name': suite_name,
                'status': 'ERROR',
                'error': str(e)
            })
    
    overall_duration = time.time() - overall_start
    
    # Generate summary report
    generate_summary_report(suite_results, overall_duration)
    
    # Return exit code based on results
    failed_suites = [r for r in suite_results if r.get('status') != 'PASSED']
    return 1 if failed_suites else 0

def generate_summary_report(suite_results, total_duration):
    """Generate comprehensive summary report"""
    print(f"\n{'='*70}")
    print("STAGE 4 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    total_tests = sum(r.get('tests_run', 0) for r in suite_results)
    total_failures = sum(r.get('failures', 0) for r in suite_results)
    total_errors = sum(r.get('errors', 0) for r in suite_results)
    
    passed_suites = [r for r in suite_results if r.get('status') == 'PASSED']
    failed_suites = [r for r in suite_results if r.get('status') == 'FAILED']
    error_suites = [r for r in suite_results if r.get('status') == 'ERROR']
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   Total Test Suites: {len(suite_results)}")
    print(f"   Passed Suites: {len(passed_suites)}")
    print(f"   Failed Suites: {len(failed_suites)}")
    print(f"   Error Suites: {len(error_suites)}")
    print(f"   Total Tests Run: {total_tests}")
    print(f"   Total Duration: {total_duration:.1f} seconds")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
        print(f"   Overall Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 SUITE DETAILS:")
    for result in suite_results:
        status_icon = "✅" if result.get('status') == 'PASSED' else "❌"
        suite_name = result.get('suite_name', 'Unknown')
        duration = result.get('duration', 0)
        
        print(f"   {status_icon} {suite_name}: {result.get('status', 'UNKNOWN')} ({duration:.1f}s)")
        
        if result.get('tests_run', 0) > 0:
            success_rate = result.get('success_rate', 0)
            print(f"      Tests: {result.get('tests_run', 0)}, Success Rate: {success_rate:.1f}%")
        
        if 'error' in result:
            print(f"      Error: {result['error']}")
    
    # Save summary to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = f"tests/reports/stage4_validation_summary_{timestamp}.md"
    
    try:
        with open(summary_file, 'w') as f:
            f.write("# Stage 4 Validation Summary Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Test Suites**: {len(suite_results)}\n")
            f.write(f"- **Passed Suites**: {len(passed_suites)}\n")
            f.write(f"- **Failed Suites**: {len(failed_suites)}\n")
            f.write(f"- **Total Tests**: {total_tests}\n")
            f.write(f"- **Total Duration**: {total_duration:.1f} seconds\n")
            
            if total_tests > 0:
                success_rate = ((total_tests - total_failures - total_errors) / total_tests) * 100
                f.write(f"- **Overall Success Rate**: {success_rate:.1f}%\n")
            
            f.write("\n## Test Suite Results\n\n")
            
            for result in suite_results:
                f.write(f"### {result.get('suite_name', 'Unknown')}\n\n")
                f.write(f"- **Status**: {result.get('status', 'UNKNOWN')}\n")
                f.write(f"- **Duration**: {result.get('duration', 0):.1f} seconds\n")
                
                if result.get('tests_run', 0) > 0:
                    f.write(f"- **Tests Run**: {result.get('tests_run', 0)}\n")
                    f.write(f"- **Failures**: {result.get('failures', 0)}\n")
                    f.write(f"- **Errors**: {result.get('errors', 0)}\n")
                    f.write(f"- **Success Rate**: {result.get('success_rate', 0):.1f}%\n")
                
                if 'error' in result:
                    f.write(f"- **Error**: {result['error']}\n")
                
                f.write("\n")
        
        print(f"\n📄 Summary report saved: {summary_file}")
        
    except Exception as e:
        print(f"\n⚠️  Could not save summary report: {e}")
    
    # Final status
    if len(failed_suites) == 0 and len(error_suites) == 0:
        print(f"\n🎉 STAGE 4 VALIDATION COMPLETED SUCCESSFULLY!")
        print(f"✅ All {len(suite_results)} test suites passed")
        print(f"🚀 Pipeline is ready for production deployment")
    else:
        print(f"\n❌ STAGE 4 VALIDATION FAILED")
        print(f"⚠️  {len(failed_suites)} failed suites, {len(error_suites)} error suites")
        print(f"🔧 Please review and fix issues before production deployment")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
