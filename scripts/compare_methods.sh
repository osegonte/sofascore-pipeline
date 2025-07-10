#!/bin/bash
# scripts/compare_methods.sh - Compare different collection methods

echo "📊 SofaScore Collection Method Comparison"
echo "========================================="

echo ""
echo "🔍 Analyzing recent export files from all methods..."

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python << 'PYEOF'
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

def analyze_scraper_files(pattern, scraper_name):
    files = glob.glob(pattern)
    recent_files = []
    
    # Get files from last 24 hours
    for file in files:
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            if datetime.now() - mod_time < timedelta(days=1):
                recent_files.append(file)
        except:
            continue
    
    if not recent_files:
        print(f"  {scraper_name}: No recent files found")
        return None
    
    all_data = []
    for file in recent_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except:
            continue
    
    if not all_data:
        print(f"  {scraper_name}: No readable data files")
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    total_matches = len(combined_df)
    
    # Calculate completeness metrics
    if 'data_completeness_pct' in combined_df.columns:
        avg_completeness = combined_df['data_completeness_pct'].mean()
        perfect_completion = len(combined_df[combined_df['data_completeness_pct'] >= 98])
        excellent_completion = len(combined_df[combined_df['data_completeness_pct'] >= 95])
    else:
        avg_completeness = (combined_df['non_zero_stats_count'].mean() / 48) * 100
        perfect_completion = len(combined_df[combined_df['non_zero_stats_count'] >= 47])
        excellent_completion = len(combined_df[combined_df['non_zero_stats_count'] >= 45])
    
    with_stats = len(combined_df[combined_df['non_zero_stats_count'] > 0])
    avg_stats = combined_df['non_zero_stats_count'].mean()
    
    success_rate = (with_stats / total_matches * 100) if total_matches > 0 else 0
    perfect_rate = (perfect_completion / total_matches * 100) if total_matches > 0 else 0
    excellent_rate = (excellent_completion / total_matches * 100) if total_matches > 0 else 0
    
    print(f"  {scraper_name}:")
    print(f"    Total matches: {total_matches}")
    print(f"    Success rate: {with_stats}/{total_matches} ({success_rate:.1f}%)")
    print(f"    Perfect completion (98%+): {perfect_completion}/{total_matches} ({perfect_rate:.1f}%)")
    print(f"    Excellent completion (95%+): {excellent_completion}/{total_matches} ({excellent_rate:.1f}%)")
    print(f"    Average completion: {avg_completeness:.1f}%")
    print(f"    Average fields per match: {avg_stats:.1f}/48")
    
    # Zero analysis
    if 'ball_possession_home' in combined_df.columns:
        zero_fields = []
        field_names = [
            'ball_possession_home', 'total_shots_home', 'tackles_home', 
            'interceptions_home', 'clearances_home', 'crosses_home', 'throw_ins_home'
        ]
        
        for field in field_names:
            if field in combined_df.columns:
                zero_count = len(combined_df[combined_df[field] == 0])
                if zero_count > 0:
                    zero_fields.append(f"{field}: {zero_count}")
        
        if zero_fields:
            print(f"    Remaining zeros: {', '.join(zero_fields[:3])}...")
        else:
            print("    ✅ ZERO ELIMINATION COMPLETE!")
    
    print()
    
    return {
        'name': scraper_name,
        'total': total_matches,
        'success_rate': success_rate,
        'perfect_rate': perfect_rate,
        'excellent_rate': excellent_rate,
        'avg_completeness': avg_completeness,
        'avg_stats': avg_stats
    }

print("📈 METHOD COMPARISON:")
print("=" * 30)

# Analyze all collection methods
results = []

# Original basic scraper
original = analyze_scraper_files("exports/live_match_minutes_complete_*.csv", "Original Basic Scraper")
if original: results.append(original)

# Quality-focused scraper
quality = analyze_scraper_files("exports/quality_focused_statistics_*.csv", "Quality-Focused Scraper")
if quality: results.append(quality)

# Complete data scraper
complete = analyze_scraper_files("exports/complete_statistics_*.csv", "Complete Data Scraper")
if complete: results.append(complete)

# Enhanced versions
enhanced = analyze_scraper_files("exports/enhanced_live_statistics_*.csv", "Enhanced Scraper")
if enhanced: results.append(enhanced)

if results:
    print("🏆 RANKINGS:")
    print("=" * 15)
    
    # Rank by completion percentage
    results_by_completion = sorted(results, key=lambda x: x['avg_completeness'], reverse=True)
    print("📊 By Average Completion:")
    for i, result in enumerate(results_by_completion, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i <= 3 else "📊"
        print(f"  {medal} {result['name']}: {result['avg_completeness']:.1f}%")
    
    print()
    # Rank by perfect completion rate
    results_by_perfect = sorted(results, key=lambda x: x['perfect_rate'], reverse=True)
    print("🎯 By Perfect Completion Rate (98%+):")
    for i, result in enumerate(results_by_perfect, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i <= 3 else "📊"
        print(f"  {medal} {result['name']}: {result['perfect_rate']:.1f}%")
    
    print()
    # Rank by success rate
    results_by_success = sorted(results, key=lambda x: x['success_rate'], reverse=True)
    print("✅ By Success Rate:")
    for i, result in enumerate(results_by_success, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i <= 3 else "📊"
        print(f"  {medal} {result['name']}: {result['success_rate']:.1f}%")
    
    print()
    print("💡 RECOMMENDATIONS:")
    
    best_completion = results_by_completion[0] if results_by_completion else None
    best_perfect = results_by_perfect[0] if results_by_perfect else None
    
    if best_completion and best_completion['avg_completeness'] >= 95:
        print(f"   🏆 RECOMMENDED: {best_completion['name']}")
        print(f"       • Best overall completion: {best_completion['avg_completeness']:.1f}%")
        if best_perfect and best_perfect['perfect_rate'] >= 80:
            print(f"       • Excellent perfect completion rate: {best_perfect['perfect_rate']:.1f}%")
        print(f"       • Average {best_completion['avg_stats']:.1f}/48 fields per match")
    else:
        print("   🎯 GOAL: Target 95%+ completion rate")
        if best_completion:
            print(f"       • Current best: {best_completion['name']} at {best_completion['avg_completeness']:.1f}%")
        print("       • Consider using Complete Data Scraper for best results")
    
    print()
    print("🔧 OPTIMIZATION SUGGESTIONS:")
    
    # Check if Complete Data Scraper is performing best
    complete_scraper = next((r for r in results if 'Complete' in r['name']), None)
    if complete_scraper:
        if complete_scraper['avg_completeness'] >= 95:
            print("   ✅ Complete Data Scraper achieving target performance")
        else:
            print(f"   🔧 Complete Data Scraper needs optimization: {complete_scraper['avg_completeness']:.1f}%")
            print("       • Check web scraping setup (Chrome/ChromeDriver)")
            print("       • Verify ML estimation algorithms")
            print("       • Review competition-specific models")
    else:
        print("   📥 Complete Data Scraper not detected - run advanced collection")
    
    # Check for web scraping capabilities
    web_scraping_detected = any('web_scraping' in result.get('name', '') for result in results)
    if not web_scraping_detected:
        print("   🌐 Enable web scraping for best results:")
        print("       • Install Chrome: sudo apt-get install google-chrome-stable")
        print("       • Install ChromeDriver: sudo apt-get install chromium-chromedriver")
        print("       • Run: ./run.sh → Option 2 (Advanced Collection)")

else:
    print("❌ No recent data found for comparison")
    print()
    print("💡 TO GENERATE COMPARISON DATA:")
    print("   1. Run different scrapers: ./run.sh")
    print("   2. Let them collect data for at least 30 minutes")
    print("   3. Run this comparison again")
    print()
    print("🚀 AVAILABLE METHODS:")
    print("   • Basic Collection (legacy)")
    print("   • Quality-Focused Collection (improved)")
    print("   • Complete Data Collection (advanced)")

print()
print("📊 NEXT STEPS:")
print("   • For 100% completion: Use Complete Data Scraper")
print("   • For reliable data: Use Quality-Focused Scraper")
print("   • Monitor with: ./run.sh → Option 4")
print("   • View detailed data: ./run.sh → Option 5")

PYEOF

echo ""
echo "🚀 TO IMPROVE COLLECTION PERFORMANCE:"
echo "   1. Enable web scraping (install Chrome/ChromeDriver)"
echo "   2. Use Complete Data Collection: ./run.sh → Option 2"
echo "   3. Monitor results: ./run.sh → Option 4"
echo "   4. Compare methods: ./run.sh → Option 7"