#!/bin/bash
# view_data.sh - View and analyze collected data

echo "📊 SofaScore Data Viewer"
echo "========================"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Function to list available data files
list_data_files() {
    echo "📁 AVAILABLE DATA FILES"
    echo "-----------------------"
    
    if [ -d "exports" ]; then
        files=$(find exports -name "*.csv" -mtime -7 | sort -r)
        
        if [ -n "$files" ]; then
            i=1
            for file in $files; do
                size=$(du -h "$file" 2>/dev/null | cut -f1)
                modified=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
                echo "  [$i] $(basename "$file") ($size, $modified)"
                i=$((i + 1))
            done
        else
            echo "  No data files found"
            return 1
        fi
    else
        echo "  Exports directory not found"
        return 1
    fi
}

# Function to analyze a specific file
analyze_file() {
    local file_path="$1"
    
    echo ""
    echo "🔍 ANALYZING: $(basename "$file_path")"
    echo "=================================="
    
    python -c "
import pandas as pd
import numpy as np

try:
    df = pd.read_csv('$file_path')
    print(f'📊 BASIC STATISTICS')
    print(f'   Rows: {len(df):,}')
    print(f'   Columns: {len(df.columns)}')
    
    if 'match_id' in df.columns:
        print(f'   Unique matches: {df[\"match_id\"].nunique()}')
    
    if 'match_minute' in df.columns:
        print(f'   Minute range: {df[\"match_minute\"].min()}-{df[\"match_minute\"].max()}')
    
    if 'competition' in df.columns:
        print(f'   Competitions: {df[\"competition\"].nunique()}')
        top_comps = df['competition'].value_counts().head(3)
        print('   Top competitions:')
        for comp, count in top_comps.items():
            print(f'     • {comp}: {count} records')
    
    print()
    print('📈 STATISTICS COMPLETENESS')
    
    # Check completeness of key statistics
    key_stats = [
        'ball_possession_home', 'ball_possession_away',
        'total_shots_home', 'total_shots_away', 
        'shots_on_target_home', 'shots_on_target_away',
        'passes_home', 'passes_away',
        'fouls_home', 'fouls_away',
        'corner_kicks_home', 'corner_kicks_away'
    ]
    
    for stat in key_stats:
        if stat in df.columns:
            completeness = (df[stat].notna().sum() / len(df)) * 100
            status = '✅' if completeness > 90 else '🟨' if completeness > 70 else '❌'
            print(f'   {status} {stat}: {completeness:.1f}%')
    
    print()
    print('🎯 KEY INSIGHTS')
    
    # Possession analysis
    if 'ball_possession_home' in df.columns:
        avg_home_poss = df['ball_possession_home'].mean()
        print(f'   Average home possession: {avg_home_poss:.1f}%')
    
    # Shot analysis
    if 'total_shots_home' in df.columns and 'total_shots_away' in df.columns:
        avg_total_shots = (df['total_shots_home'] + df['total_shots_away']).mean()
        print(f'   Average total shots per match-minute: {avg_total_shots:.1f}')
    
    # High activity matches
    if 'total_shots_home' in df.columns and 'total_shots_away' in df.columns:
        high_shot_records = df[(df['total_shots_home'] + df['total_shots_away']) > 20]
        print(f'   High shot activity records (>20 shots): {len(high_shot_records)}')
    
    # Recent data
    if 'collection_timestamp' in df.columns:
        df['collection_timestamp'] = pd.to_datetime(df['collection_timestamp'])
        recent_hours = (df['collection_timestamp'].max() - df['collection_timestamp'].min()).total_seconds() / 3600
        print(f'   Data spans: {recent_hours:.1f} hours')

except Exception as e:
    print(f'❌ Error analyzing file: {e}')
"
}

# Main menu
while true; do
    echo ""
    list_data_files
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "Select a file to analyze (number), or 'q' to quit:"
        read -p "> " choice
        
        if [ "$choice" = "q" ]; then
            break
        fi
        
        # Get the selected file
        files_array=($(find exports -name "*.csv" -mtime -7 | sort -r))
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#files_array[@]}" ]; then
            selected_file="${files_array[$((choice-1))]}"
            analyze_file "$selected_file"
            
            echo ""
            read -p "Press Enter to continue..."
        else
            echo "❌ Invalid selection"
        fi
    else
        echo "Run the live scraper first to generate data files"
        break
    fi
done
