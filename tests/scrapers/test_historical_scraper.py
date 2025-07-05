"""
Tests for Historical Scraper
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from historical_scraper import HistoricalScraper

def test_historical_scraper_initialization():
    """Test that historical scraper initializes correctly"""
    try:
        scraper = HistoricalScraper()
        print("✅ HistoricalScraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ HistoricalScraper initialization failed: {e}")
        return False

def test_get_historical_matches():
    """Test fetching historical matches"""
    try:
        scraper = HistoricalScraper()
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        matches = scraper.get_historical_matches_by_date(yesterday)
        print(f"✅ Found {len(matches)} completed matches for {yesterday}")
        
        if matches:
            sample_match = matches[0]
            required_fields = ['match_id', 'home_team', 'away_team', 'home_score_final', 'away_score_final']
            for field in required_fields:
                if field not in sample_match:
                    print(f"❌ Missing required field: {field}")
                    return False
            print("✅ Historical match data structure is correct")
        
        return True
    except Exception as e:
        print(f"❌ get_historical_matches failed: {e}")
        return False

def run_historical_scraper_tests():
    """Run all historical scraper tests"""
    print("Testing Historical Scraper...")
    print("-" * 30)
    
    tests = [
        test_historical_scraper_initialization,
        test_get_historical_matches
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nHistorical Scraper Tests: {passed}/{len(tests)} passed")
    return passed == len(tests)

if __name__ == "__main__":
    run_historical_scraper_tests()
