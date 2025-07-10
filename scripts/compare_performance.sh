#!/bin/bash
# scripts/compare_performance.sh - Unified performance comparison

echo "📊 SofaScore Collection Performance Analysis"
echo "==========================================="

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python << 'PYEOF'
import pandas as pd
import glob
import os
from datetime import datetime, timedelta

def analyze_recent_exports():
    """Analyze all recent export files"""
    
    # Find all CSV files from last 24 hours
    csv_files = glob.glob("exports/*.csv")
    recent_files = []
    
    for file in csv_files:
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            if datetime.now() - mod_time < timedelta(days=1):
                recent_files.append(file)
        except:
            continue
    
    if not recent_files:
        print("❌ No recent data files found")
        print("   Run collection first: ./run.sh → Option 2")
        return
    
    print(f"📁 Analyzing {len(recent_files)} recent files...")
    
    all_data = []
    for file in recent_files:
        try:
            df = pd.read_csv(file)
            df['source_file'] = os.path.basename(file)
            all_data.append(df)
        except Exception as e:
            print(f"⚠️  Could not read {file}: {e}")
    
    if not all_data:
        print("❌ No readable data files")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Analysis
    total_records = len(combined_df)
    
    # Completion analysis
    if 'data_completeness_pct' in combined_df.columns:
        avg_completion = combined_df['data_completeness_pct'].mean()
        perfect_records = len(combined_df[combined_df['data_completeness_pct'] >= 98])
        excellent_records = len(combined_df[combined_df['data_completeness_pct'] >= 95])
    else:
        avg_completion = (combined_df['non_zero_stats_count'].mean() / 48) * 100
        perfect_records = len(combined_df[combined_df['non_zero_stats_count'] >= 47])
        excellent_records = len(combined_df[combined_df['non_zero_stats_count'] >= 45])
    
    # Source analysis
    if 'stats_source' in combined_df.columns:
        source_counts = combined_df['stats_source'].value_counts()
    else:
        source_counts = pd.Series({'unknown': total_records})
    
    print()
    print("📊 PERFORMANCE SUMMARY")
    print("=" * 25)
    print(f"Total records: {total_records:,}")
    print(f"Average completion: {avg_completion:.1f}%")
    print(f"Perfect completion (98%+): {perfect_records:,} ({perfect_records/total_records*100:.1f}%)")
    print(f"Excellent completion (95%+): {excellent_records:,} ({excellent_records/total_records*100:.1f}%)")
    
    print()
    print("📈 DATA SOURCES")
    print("=" * 15)
    for source, count in source_counts.head(5).items():
        print(f"  {source}: {count:,} records")
    
    print()
    print("🎯 RECOMMENDATIONS")
    print("=" * 18)
    if avg_completion >= 95:
        print("✅ Excellent performance - target achieved!")
    elif avg_completion >= 85:
        print("🟨 Good performance - minor optimization possible")
    else:
        print("🔧 Performance needs improvement")
        print("   • Enable web scraping (install Chrome)")
        print("   • Check internet connectivity")
        print("   • Review logs for errors")
    
    # Zero field analysis
    stat_fields = [col for col in combined_df.columns if any(x in col for x in 
                  ['_home', '_away']) and col not in ['home_team', 'away_team']]
    
    if stat_fields:
        print()
        print("🔍 ZERO ANALYSIS")
        print("=" * 15)
        zero_fields = []
        for field in stat_fields[:10]:  # Check first 10 stat fields
            zero_count = len(combined_df[combined_df[field] == 0])
            if zero_count > 0:
                zero_fields.append(f"{field}: {zero_count}")
        
        if zero_fields:
            print("Fields with zeros:")
            for field_info in zero_fields[:5]:
                print(f"  • {field_info}")
        else:
            print("🎉 Zero elimination successful!")

analyze_recent_exports()
PYEOF
