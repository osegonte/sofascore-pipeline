"""
Comprehensive tests for Stage 2 implementation
"""

import sys
import os

# Import all scraper tests
sys.path.append(os.path.dirname(__file__))
from scrapers.test_live_scraper import run_live_scraper_tests
from scrapers.test_fixture_scraper import run_fixture_scraper_tests
from scrapers.test_historical_scraper import run_historical_scraper_tests

def test_stage2_setup():
    """Test that all Stage 2 components are properly set up"""
    print("Testing Stage 2 Setup...")
    print("-" * 25)
    
    # Check that all required files exist
    required_files = [
        'src/live_scraper.py',
        'src/fixture_scraper.py',
        'src/historical_scraper.py',
        'src/utils.py',
        'config/config.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All Stage 2 files are present")
    
    # Check that directories exist
    required_dirs = ['logs', 'exports', 'tests/scrapers']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Missing directory: {dir_path}")
            return False
    
    print("✅ All required directories are present")
    return True

def run_all_tests():
    """Run all Stage 2 tests"""
    print("SofaScore Pipeline - Stage 2 Testing")
    print("=" * 40)
    
    # Test setup
    setup_ok = test_stage2_setup()
    if not setup_ok:
        print("❌ Setup tests failed!")
        return False
    
    print()
    
    # Test scrapers
    tests_results = [
        run_live_scraper_tests(),
        run_fixture_scraper_tests(),
        run_historical_scraper_tests()
    ]
    
    passed_tests = sum(tests_results)
    total_tests = len(tests_results)
    
    print("\n" + "=" * 40)
    print(f"Overall Results: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All Stage 2 tests passed successfully!")
        print("\nNext steps:")
        print("1. Run: python src/main.py")
        print("2. Check exports/ directory for CSV files")
        print("3. Review logs/ directory for detailed logs")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
