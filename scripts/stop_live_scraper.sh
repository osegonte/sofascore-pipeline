#!/bin/bash
# stop_live_scraper.sh - Stop the live scraper gracefully

echo "🛑 Stopping SofaScore Live Scraper"
echo "=================================="

# Find scraper process
scraper_pid=$(pgrep -f "src/live_scraper.py")

if [ -n "$scraper_pid" ]; then
    echo "📍 Found scraper process: PID $scraper_pid"
    echo "🔄 Sending graceful shutdown signal..."
    
    # Send SIGINT for graceful shutdown
    kill -INT $scraper_pid
    
    # Wait for graceful shutdown
    sleep 5
    
    # Check if still running
    if kill -0 $scraper_pid 2>/dev/null; then
        echo "⚠️  Process still running, sending SIGTERM..."
        kill -TERM $scraper_pid
        sleep 3
        
        # Force kill if necessary
        if kill -0 $scraper_pid 2>/dev/null; then
            echo "🚫 Force killing process..."
            kill -KILL $scraper_pid
        fi
    fi
    
    echo "✅ Scraper stopped"
else
    echo "ℹ️  No scraper process found running"
fi

echo "📁 Final data export should be in exports/ directory"
