"""
Tests for Fixture Scraper
"""

import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from fixture_scraper import FixtureScraper

def test_fixture_scraper_initialization():
    """Test that fixture scraper initializes correctly"""
    try:
        scraper = FixtureScraper()
        print("✅ FixtureScraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ FixtureScraper initialization failed: {e}")
        return False

def test_get_fixtures_by_date():
    """Test fetching fixtures for a specific date"""
    try:
        scraper = FixtureScraper()
        today = datetime.now().strftime('%Y-%m-%d')
        fixtures = scraper.get_fixtures_by_date(today)
        print(f"✅ Found {len(fixtures)} fixtures for {today}")
        
        if fixtures:
            sample_fixture = fixtures[0]
            required_fields = ['fixture_id', 'home_team', 'away_team', 'kickoff_time']
            for field in required_fields:
                if field not in sample_fixture:
                    print(f"❌ Missing required field: {field}")
                    return False
            print("✅ Fixture data structure is correct")
        
        return True
    except Exception as e:
        print(f"❌ get_fixtures_by_date failed: {e}")
        return False

def run_fixture_scraper_tests():
    """Run all fixture scraper tests"""
    print("Testing Fixture Scraper...")
    print("-" * 30)
    
    tests = [
        test_fixture_scraper_initialization,
        test_get_fixtures_by_date
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nFixture Scraper Tests: {passed}/{len(tests)} passed")
    return passed == len(tests)

if __name__ == "__main__":
    run_fixture_scraper_tests()
