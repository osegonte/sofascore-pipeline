#!/bin/bash
# monitor_scraper.sh - Monitor live scraper status and data quality

echo "📊 SofaScore Live Scraper Monitoring Dashboard"
echo "=============================================="

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Function to show current live matches
show_live_matches() {
    echo "⚽ CURRENT LIVE MATCHES"
    echo "----------------------"
    python -c "
import requests
try:
    response = requests.get('https://api.sofascore.com/api/v1/sport/football/events/live', timeout=10)
    if response.status_code == 200:
        data = response.json()
        events = data.get('events', [])
        if events:
            for event in events[:10]:  # Show first 10
                home = event.get('homeTeam', {}).get('name', 'Unknown')
                away = event.get('awayTeam', {}).get('name', 'Unknown')
                home_score = event.get('homeScore', {}).get('current', 0)
                away_score = event.get('awayScore', {}).get('current', 0)
                competition = event.get('tournament', {}).get('name', 'Unknown')
                print(f'  • {home} {home_score}-{away_score} {away} ({competition})')
        else:
            print('  No live matches currently')
    else:
        print(f'  API Error: Status {response.status_code}')
except Exception as e:
    print(f'  Error: {e}')
"
}

# Function to show recent exports
show_recent_data() {
    echo ""
    echo "📁 RECENT DATA EXPORTS"
    echo "----------------------"
    
    if [ -d "exports" ]; then
        # Find recent CSV files
        recent_files=$(find exports -name "live_match_minutes_complete_*.csv" -mtime -1 2>/dev/null | sort -r | head -5)
        
        if [ -n "$recent_files" ]; then
            for file in $recent_files; do
                size=$(du -h "$file" 2>/dev/null | cut -f1)
                modified=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1,2 | cut -d'.' -f1)
                
                # Count rows and get basic stats
                if command -v python &> /dev/null; then
                    stats=$(python -c "
import pandas as pd
try:
    df = pd.read_csv('$file')
    print(f'{len(df)} rows, {df[\"match_id\"].nunique() if \"match_id\" in df.columns else 0} matches')
except:
    print('Error reading file')
")
                    echo "  📄 $(basename "$file") ($size, $stats, $modified)"
                else
                    echo "  📄 $(basename "$file") ($size, $modified)"
                fi
            done
        else
            echo "  No recent data files found"
        fi
    else
        echo "  Exports directory not found"
    fi
}

# Function to check scraper process
check_scraper_process() {
    echo ""
    echo "🔄 SCRAPER PROCESS STATUS"
    echo "-------------------------"
    
    scraper_pid=$(pgrep -f "src/live_scraper.py")
    
    if [ -n "$scraper_pid" ]; then
        echo "  ✅ Scraper is running (PID: $scraper_pid)"
        
        # Show CPU and memory usage
        if command -v ps &> /dev/null; then
            ps_info=$(ps -p $scraper_pid -o %cpu,%mem,etime 2>/dev/null | tail -1)
            echo "  📊 Resource usage: $ps_info"
        fi
    else
        echo "  ❌ Scraper is not running"
        echo "  💡 Start with: ./start_live_scraper.sh"
    fi
}

# Function to show log status
show_logs() {
    echo ""
    echo "📋 LOG STATUS"
    echo "-------------"
    
    if [ -d "logs" ]; then
        recent_log=$(find logs -name "pipeline_*.log" -mtime -1 2>/dev/null | sort -r | head -1)
        
        if [ -n "$recent_log" ]; then
            echo "  📄 Recent log: $(basename "$recent_log")"
            
            # Show last few entries
            echo "  📝 Recent entries:"
            tail -3 "$recent_log" 2>/dev/null | while read line; do
                echo "    $line"
            done
            
            # Count errors and warnings
            errors=$(grep -c "ERROR" "$recent_log" 2>/dev/null || echo "0")
            warnings=$(grep -c "WARNING" "$recent_log" 2>/dev/null || echo "0")
            
            echo "  🚨 Errors: $errors, Warnings: $warnings"
        else
            echo "  No recent log files found"
        fi
    else
        echo "  Logs directory not found"
    fi
}

# Main monitoring display
show_status() {
    clear
    echo "📊 SofaScore Live Scraper Monitoring Dashboard"
    echo "=============================================="
    echo "⏰ $(date '+%Y-%m-%d %H:%M:%S')"
    
    show_live_matches
    check_scraper_process
    show_recent_data
    show_logs
    
    echo ""
    echo "🔄 Auto-refresh in 30 seconds... (Press Ctrl+C to exit)"
    echo "💡 TIP: Check exports/ directory for CSV files with complete statistics"
}

# Main monitoring loop
if [ "$1" = "--once" ]; then
    show_status
else
    while true; do
        show_status
        sleep 30
    done
fi
