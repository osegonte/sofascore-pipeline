#!/bin/bash
# scripts/stop_collection.sh - Unified collection stopper

echo "🛑 Stopping SofaScore Data Collection"
echo "====================================="

stopped_processes=0

# Find and stop scraper processes
scraper_processes=$(pgrep -f "live_scraper_quality_focused.py")
if [ -n "$scraper_processes" ]; then
    echo "📍 Found scraper processes: $scraper_processes"
    echo "🔄 Sending graceful shutdown signal..."
    
    for pid in $scraper_processes; do
        kill -INT $pid
        sleep 2
        
        if kill -0 $pid 2>/dev/null; then
            echo "⚠️  Process $pid still running, sending SIGTERM..."
            kill -TERM $pid
            sleep 2
            
            if kill -0 $pid 2>/dev/null; then
                echo "🚫 Force killing process $pid..."
                kill -KILL $pid
            fi
        fi
        stopped_processes=$((stopped_processes + 1))
    done
    
    echo "✅ Stopped $stopped_processes scraper process(es)"
else
    echo "ℹ️  No active scraper processes found"
fi

# Stop web scraping processes
chrome_pids=$(pgrep -f "chrome.*sofascore")
chromedriver_pids=$(pgrep chromedriver)

if [ -n "$chrome_pids" ]; then
    echo "🌐 Stopping Chrome processes..."
    for pid in $chrome_pids; do
        kill -TERM $pid 2>/dev/null
    done
fi

if [ -n "$chromedriver_pids" ]; then
    echo "🔧 Stopping ChromeDriver processes..."
    for pid in $chromedriver_pids; do
        kill -TERM $pid 2>/dev/null
    done
fi

echo ""
echo "✅ Collection stopped successfully"
echo "📁 Data available in exports/ directory"
