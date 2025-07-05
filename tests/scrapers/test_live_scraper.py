"""
Tests for Live Match Scraper
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from live_scraper import LiveMatchScraper

def test_live_scraper_initialization():
    """Test that live scraper initializes correctly"""
    try:
        scraper = LiveMatchScraper()
        print("✅ LiveMatchScraper initialized successfully")
        return True
    except Exception as e:
        print(f"❌ LiveMatchScraper initialization failed: {e}")
        return False

def test_get_live_matches():
    """Test fetching live matches"""
    try:
        scraper = LiveMatchScraper()
        matches = scraper.get_live_matches()
        print(f"✅ Found {len(matches)} live matches")
        
        if matches:
            sample_match = matches[0]
            required_fields = ['match_id', 'home_team', 'away_team', 'home_score', 'away_score']
            for field in required_fields:
                if field not in sample_match:
                    print(f"❌ Missing required field: {field}")
                    return False
            print("✅ Match data structure is correct")
        
        return True
    except Exception as e:
        print(f"❌ get_live_matches failed: {e}")
        return False

def run_live_scraper_tests():
    """Run all live scraper tests"""
    print("Testing Live Match Scraper...")
    print("-" * 30)
    
    tests = [
        test_live_scraper_initialization,
        test_get_live_matches
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nLive Scraper Tests: {passed}/{len(tests)} passed")
    return passed == len(tests)

if __name__ == "__main__":
    run_live_scraper_tests()
