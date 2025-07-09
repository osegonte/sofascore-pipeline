#!/bin/bash
# compare_all_scrapers.sh - Compare all three scraper versions

echo "📊 SofaScore Scraper Performance Comparison - ALL VERSIONS"
echo "=========================================================="

echo ""
echo "🔍 Analyzing recent export files from all scraper versions..."

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
        return
    
    all_data = []
    for file in recent_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except:
            continue
    
    if not all_data:
        print(f"  {scraper_name}: No readable data files")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    total_matches = len(combined_df)
    with_stats = len(combined_df[combined_df['non_zero_stats_count'] > 0])
    
    # Check for quality metrics
    if 'is_high_quality' in combined_df.columns:
        high_quality = len(combined_df[combined_df['is_high_quality'] == True])
    else:
        high_quality = len(combined_df[combined_df['non_zero_stats_count'] >= 15])
    
    if 'data_completeness_pct' in combined_df.columns:
        avg_completeness = combined_df['data_completeness_pct'].mean()
    else:
        avg_completeness = (combined_df['non_zero_stats_count'].mean() / 48) * 100
    
    avg_stats = combined_df['non_zero_stats_count'].mean()
    
    success_rate = (with_stats / total_matches * 100) if total_matches > 0 else 0
    quality_rate = (high_quality / total_matches * 100) if total_matches > 0 else 0
    
    print(f"  {scraper_name}:")
    print(f"    Total matches: {total_matches}")
    print(f"    Success rate: {with_stats}/{total_matches} ({success_rate:.1f}%)")
    print(f"    High quality: {high_quality}/{total_matches} ({quality_rate:.1f}%)")
    print(f"    Avg completeness: {avg_completeness:.1f}%")
    print(f"    Avg stats per match: {avg_stats:.1f}")
    print()
    
    return {
        'name': scraper_name,
        'total': total_matches,
        'success_rate': success_rate,
        'quality_rate': quality_rate,
        'completeness': avg_completeness,
        'avg_stats': avg_stats
    }

print("📈 PERFORMANCE COMPARISON:")
print("=" * 30)

# Analyze all three versions
results = []

original = analyze_scraper_files("exports/live_match_minutes_complete_*.csv", "Original Scraper")
if original: results.append(original)

enhanced = analyze_scraper_files("exports/enhanced_live_statistics_*.csv", "Enhanced Scraper")
if enhanced: results.append(enhanced)

quality = analyze_scraper_files("exports/quality_focused_statistics_*.csv", "Quality-Focused Scraper")
if quality: results.append(quality)

if results:
    print("🏆 RANKINGS:")
    print("=" * 15)
    
    # Sort by completeness
    results_by_completeness = sorted(results, key=lambda x: x['completeness'], reverse=True)
    print("By Data Completeness:")
    for i, result in enumerate(results_by_completeness, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"  {medal} {result['name']}: {result['completeness']:.1f}%")
    
    print()
    # Sort by success rate
    results_by_success = sorted(results, key=lambda x: x['success_rate'], reverse=True)
    print("By Success Rate:")
    for i, result in enumerate(results_by_success, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        print(f"  {medal} {result['name']}: {result['success_rate']:.1f}%")
    
    print()
    print("💡 RECOMMENDATIONS:")
    best_completeness = results_by_completeness[0]
    best_success = results_by_success[0]
    
    if best_completeness['name'] == best_success['name']:
        print(f"   🏆 Use {best_completeness['name']} for best overall performance")
    else:
        print(f"   🎯 Use {best_completeness['name']} for data completeness")
        print(f"   📊 Use {best_success['name']} for coverage")

else:
    print("No recent data found. Run scrapers to generate comparison data.")

PYEOF

echo ""
echo "🚀 NEXT STEPS:"
echo "   • Quality-Focused Scraper should show highest completeness"
echo "   • Enhanced Scraper should show good overall performance"
echo "   • Original Scraper provides baseline comparison"
echo ""
echo "💡 TIP: Run './run_quality_focused.sh' and select option 4 for best results"
