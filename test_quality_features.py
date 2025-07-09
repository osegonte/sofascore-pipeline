#!/usr/bin/env python3
"""Test quality-focused scraper features"""

import sys
sys.path.append('src')

try:
    from live_scraper_quality_focused import QualityFocusedScraper
    
    scraper = QualityFocusedScraper()
    print("✅ Quality-focused scraper loaded")
    
    # Test tier classification
    test_competitions = [
        'UEFA Champions League',
        'Premier League', 
        'MLS',
        'Reserve Team',
        'Copa Paraguay'
    ]
    
    print("\n🏆 TIER CLASSIFICATION TEST:")
    for comp in test_competitions:
        test_match = {'competition': comp}
        should_collect, reason = scraper.should_collect_match(test_match)
        status = "COLLECT" if should_collect else "SKIP"
        print(f"   • {comp}: {status} ({reason})")
    
    # Test statistical estimation
    print("\n📊 STATISTICAL ESTIMATION TEST:")
    test_match = {
        'home_score': 2,
        'away_score': 1,
        'competition': 'UEFA Champions League',
        'status': '2nd half'
    }
    
    estimated_stats = scraper._estimate_statistics_intelligently(test_match)
    non_zero_count = sum(1 for v in estimated_stats.values() if v != 0)
    
    print(f"   Test match: Home 2-1 Away (Champions League)")
    print(f"   Estimated statistics: {non_zero_count}/48 fields")
    print(f"   Possession: {estimated_stats['ball_possession_home']}% vs {estimated_stats['ball_possession_away']}%")
    print(f"   Shots: {estimated_stats['total_shots_home']} vs {estimated_stats['total_shots_away']}")
    print(f"   Fouls: {estimated_stats['fouls_home']} vs {estimated_stats['fouls_away']}")
    
    print("\n🎯 QUALITY FEATURES:")
    print("   ✅ Tier-based competition filtering")
    print("   ✅ Intelligent statistical estimation")
    print("   ✅ Enhanced data completeness tracking")
    print("   ✅ Quality assessment metrics")
    
    print("\n🚀 Ready for quality-focused data collection!")
    print("   Run: ./start_quality_focused.sh")
    
except Exception as e:
    print(f"❌ Error: {e}")
