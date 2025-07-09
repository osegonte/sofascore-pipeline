#!/bin/bash
# compare_scrapers.sh - Compare original vs enhanced scraper performance

echo "📊 SofaScore Scraper Performance Comparison"
echo "==========================================="

echo ""
echo "🔍 Analyzing recent export files..."

original_files=$(find exports -name "enhanced_live_statistics_*.csv" -mtime -1 2>/dev/null | wc -l)
enhanced_files=$(find exports -name "enhanced_live_statistics_*.csv" -mtime -1 2>/dev/null | wc -l)

echo "Recent files found:"
echo "  Original scraper: $original_files files"
echo "  Enhanced scraper: $enhanced_files files"

echo ""
echo "📈 Performance Analysis:"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python << 'PYEOF'
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

def analyze_files(pattern, scraper_type):
    files = glob.glob(pattern)
    recent_files = []
    
    # Get files from last 24 hours
    for file in files:
        mod_time = datetime.fromtimestamp(os.path.getmtime(file))
        if datetime.now() - mod_time < timedelta(days=1):
            recent_files.append(file)
    
    if not recent_files:
        print(f"  {scraper_type}: No recent files found")
        return
    
    all_data = []
    for file in recent_files:
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except:
            continue
    
    if not all_data:
        print(f"  {scraper_type}: No readable data files")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    total_matches = len(combined_df)
    with_stats = len(combined_df[combined_df['non_zero_stats_count'] > 0])
    high_quality = len(combined_df[combined_df.get('is_high_quality', False) == True])
    avg_stats = combined_df['non_zero_stats_count'].mean()
    
    success_rate = (with_stats / total_matches * 100) if total_matches > 0 else 0
    quality_rate = (high_quality / total_matches * 100) if total_matches > 0 else 0
    
    print(f"  {scraper_type}:")
    print(f"    Total matches: {total_matches}")
    print(f"    Success rate: {with_stats}/{total_matches} ({success_rate:.1f}%)")
    print(f"    High quality: {high_quality}/{total_matches} ({quality_rate:.1f}%)")
    print(f"    Avg stats per match: {avg_stats:.1f}")
    print()

# Analyze original scraper files
analyze_files("exports/live_match_minutes_complete_*.csv", "Original Scraper")

# Analyze enhanced scraper files  
analyze_files("exports/enhanced_live_statistics_*.csv", "Enhanced Scraper")

print("💡 RECOMMENDATIONS:")
print("  • If Enhanced Scraper shows higher success rate, switch to it")
print("  • Enhanced scraper should handle qualification matches better")
print("  • Look for 'mobile_endpoint' and 'team_events_fallback' in stats_source")
PYEOF

echo ""
echo "🚀 To test the enhanced scraper:"
echo "  ./run_enhanced.sh and select option 3"
echo ""
echo "📊 To monitor in real-time:"
echo "  Open new terminal and run: ./scripts/monitor_scraper.sh"
