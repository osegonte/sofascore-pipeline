#!/usr/bin/env python3
"""
Fixed test runner for Stage 4 validation
Handles missing dependencies gracefully and provides detailed analysis
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check and report on test dependencies"""
    print("🔍 Checking test dependencies...")
    
    dependencies = {
        'psutil': False,
        'pandas': False,
        'sqlalchemy': False,
        'requests': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"   ✅ {dep}: Available")
        except ImportError:
            print(f"   ❌ {dep}: Missing")
    
    return dependencies

def run_available_tests():
    """Run tests that can execute with current dependencies"""
    print(f"\n{'='*60}")
    print("RUNNING AVAILABLE TESTS")
    print(f"{'='*60}")
    
    test_results = []
    
    # Test 1: Database connectivity
    print("\n🗄️  Testing database connectivity...")
    try:
        from config.database import test_connection
        if test_connection():
            print("   ✅ Database connection successful")
            test_results.append(('Database Connectivity', True))
        else:
            print("   ❌ Database connection failed")
            test_results.append(('Database Connectivity', False))
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        test_results.append(('Database Connectivity', False))
    
    # Test 2: Data quality check
    print("\n📊 Testing basic data quality...")
    try:
        from config.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            # Check table counts
            tables = ['live_matches', 'goal_events', 'fixtures', 'team_statistics']
            table_counts = {}
            
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_counts[table] = count
                print(f"   ✅ {table}: {count} records")
            
            # Check goal timing consistency
            result = conn.execute(text("""
                SELECT COUNT(*) FROM goal_events 
                WHERE total_minute != exact_timestamp + COALESCE(added_time, 0)
            """))
            timing_errors = result.scalar()
            
            if timing_errors == 0:
                print("   ✅ Goal timing calculations: Consistent")
            else:
                print(f"   ⚠️  Goal timing calculations: {timing_errors} inconsistencies found")
            
            test_results.append(('Data Quality Basic', timing_errors == 0))
            
    except Exception as e:
        print(f"   ❌ Data quality test failed: {e}")
        test_results.append(('Data Quality Basic', False))
    
    # Test 3: API connectivity (if possible)
    print("\n🌐 Testing API connectivity...")
    try:
        from src.fixture_scraper import FixtureScraper
        from datetime import datetime
        
        scraper = FixtureScraper()
        start_time = time.time()
        fixtures = scraper.get_fixtures_by_date(datetime.now().strftime('%Y-%m-%d'))
        response_time = time.time() - start_time
        
        print(f"   ✅ API response: {len(fixtures)} fixtures in {response_time:.2f}s")
        test_results.append(('API Connectivity', True))
        
    except Exception as e:
        print(f"   ⚠️  API connectivity issue: {e}")
        test_results.append(('API Connectivity', False))
    
    # Test 4: Goal analysis validation
    print("\n⚽ Testing goal analysis...")
    try:
        from config.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total_goals,
                    COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                    ROUND(AVG(total_minute), 1) as avg_minute,
                    COUNT(*) FILTER (WHERE total_minute < 0 OR total_minute > 120) as impossible_goals
                FROM goal_events
                WHERE total_minute IS NOT NULL
            """))
            
            row = result.fetchone()
            if row and row[0] > 0:
                total, late, avg_min, impossible = row[0], row[1], row[2], row[3]
                late_pct = (late / total * 100) if total > 0 else 0
                
                print(f"   ✅ Total goals analyzed: {total}")
                print(f"   ✅ Late goals: {late} ({late_pct:.1f}%)")
                print(f"   ✅ Average goal minute: {avg_min}")
                
                if impossible > 0:
                    print(f"   ⚠️  Impossible timing goals: {impossible}")
                    test_results.append(('Goal Analysis', False))
                else:
                    print("   ✅ All goal timings within valid range")
                    test_results.append(('Goal Analysis', True))
            else:
                print("   ℹ️  No goals found for analysis")
                test_results.append(('Goal Analysis', True))  # No data is not a failure
                
    except Exception as e:
        print(f"   ❌ Goal analysis failed: {e}")
        test_results.append(('Goal Analysis', False))
    
    return test_results

def generate_summary_report(test_results, dependencies):
    """Generate comprehensive summary report"""
    print(f"\n{'='*60}")
    print("STAGE 4 VALIDATION SUMMARY")
    print(f"{'='*60}")
    
    # Test results summary
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 TEST RESULTS:")
    print(f"   Tests Run: {total_tests}")
    print(f"   Tests Passed: {passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, result in test_results:
        status_icon = "✅" if result else "❌"
        print(f"   {status_icon} {test_name}")
    
    # Dependency status
    available_deps = sum(1 for available in dependencies.values() if available)
    total_deps = len(dependencies)
    
    print(f"\n📦 DEPENDENCIES:")
    print(f"   Available: {available_deps}/{total_deps}")
    for dep, available in dependencies.items():
        status_icon = "✅" if available else "❌"
        print(f"   {status_icon} {dep}")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    
    if success_rate >= 90 and available_deps == total_deps:
        grade = "A"
        status = "PRODUCTION READY"
        color = "🟢"
    elif success_rate >= 80:
        grade = "B"
        status = "MOSTLY READY"
        color = "🟡"
    elif success_rate >= 70:
        grade = "C"
        status = "NEEDS WORK"
        color = "🟠"
    else:
        grade = "D"
        status = "NOT READY"
        color = "🔴"
    
    print(f"   Grade: {grade}")
    print(f"   Status: {color} {status}")
    
    # Recommendations
    print(f"\n🔧 RECOMMENDATIONS:")
    
    if available_deps < total_deps:
        print("   1. Install missing dependencies:")
        for dep, available in dependencies.items():
            if not available:
                print(f"      pip install {dep}")
    
    failed_tests = [name for name, result in test_results if not result]
    if failed_tests:
        print("   2. Fix failing tests:")
        for test in failed_tests:
            print(f"      - {test}")
    
    print("   3. Run comprehensive tests after fixes:")
    print("      python tests/run_all_tests.py")
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"tests/reports/fixed_validation_summary_{timestamp}.md"
    
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write("# Stage 4 Fixed Validation Summary\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Overall Assessment\n\n")
        f.write(f"- **Grade**: {grade}\n")
        f.write(f"- **Status**: {status}\n")
        f.write(f"- **Success Rate**: {success_rate:.1f}%\n\n")
        f.write(f"## Test Results\n\n")
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            f.write(f"- **{test_name}**: {status}\n")
        f.write(f"\n## Dependencies\n\n")
        for dep, available in dependencies.items():
            status = "Available" if available else "Missing"
            f.write(f"- **{dep}**: {status}\n")
    
    print(f"\n📄 Report saved: {report_file}")
    
    return success_rate >= 70  # Return True if acceptable

def main():
    """Main test execution"""
    print("SofaScore Pipeline - Stage 4: Fixed Validation")
    print("=" * 55)
    print(f"Execution started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check dependencies
    dependencies = check_dependencies()
    
    # Run available tests
    test_results = run_available_tests()
    
    # Generate summary
    success = generate_summary_report(test_results, dependencies)
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
