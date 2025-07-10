#!/bin/bash
# scripts/stop_collection.sh - Stop all collection processes gracefully

echo "🛑 Stopping SofaScore Data Collection"
echo "====================================="

stopped_processes=0

# Find and stop quality-focused scraper
quality_pid=$(pgrep -f "live_scraper_quality_focused.py")
if [ -n "$quality_pid" ]; then
    echo "📍 Found Quality-Focused scraper: PID $quality_pid"
    echo "🔄 Sending graceful shutdown signal..."
    kill -INT $quality_pid
    sleep 3
    
    if kill -0 $quality_pid 2>/dev/null; then
        echo "⚠️  Process still running, sending SIGTERM..."
        kill -TERM $quality_pid
        sleep 2
        
        if kill -0 $quality_pid 2>/dev/null; then
            echo "🚫 Force killing process..."
            kill -KILL $quality_pid
        fi
    fi
    echo "✅ Quality-Focused scraper stopped"
    stopped_processes=$((stopped_processes + 1))
fi

# Find and stop original scraper
original_pid=$(pgrep -f "src/live_scraper.py")
if [ -n "$original_pid" ]; then
    echo "📍 Found Original scraper: PID $original_pid"
    echo "🔄 Sending graceful shutdown signal..."
    kill -INT $original_pid
    sleep 3
    
    if kill -0 $original_pid 2>/dev/null; then
        echo "⚠️  Process still running, sending SIGTERM..."
        kill -TERM $original_pid
        sleep 2
        
        if kill -0 $original_pid 2>/dev/null; then
            echo "🚫 Force killing process..."
            kill -KILL $original_pid
        fi
    fi
    echo "✅ Original scraper stopped"
    stopped_processes=$((stopped_processes + 1))
fi

# Find and stop enhanced scraper
enhanced_pid=$(pgrep -f "live_scraper_enhanced.py")
if [ -n "$enhanced_pid" ]; then
    echo "📍 Found Enhanced scraper: PID $enhanced_pid"
    echo "🔄 Sending graceful shutdown signal..."
    kill -INT $enhanced_pid
    sleep 3
    
    if kill -0 $enhanced_pid 2>/dev/null; then
        echo "⚠️  Process still running, sending SIGTERM..."
        kill -TERM $enhanced_pid
        sleep 2
        
        if kill -0 $enhanced_pid 2>/dev/null; then
            echo "🚫 Force killing process..."
            kill -KILL $enhanced_pid
        fi
    fi
    echo "✅ Enhanced scraper stopped"
    stopped_processes=$((stopped_processes + 1))
fi

# Stop any Chrome/ChromeDriver processes from web scraping
chrome_pids=$(pgrep -f "chrome.*sofascore")
if [ -n "$chrome_pids" ]; then
    echo "🌐 Stopping Chrome processes used for web scraping..."
    for pid in $chrome_pids; do
        kill -TERM $pid 2>/dev/null
    done
    sleep 2
    
    # Force kill if still running
    chrome_pids=$(pgrep -f "chrome.*sofascore")
    if [ -n "$chrome_pids" ]; then
        for pid in $chrome_pids; do
            kill -KILL $pid 2>/dev/null
        done
    fi
    echo "✅ Chrome processes stopped"
fi

# Stop any chromedriver processes
chromedriver_pids=$(pgrep chromedriver)
if [ -n "$chromedriver_pids" ]; then
    echo "🔧 Stopping ChromeDriver processes..."
    for pid in $chromedriver_pids; do
        kill -TERM $pid 2>/dev/null
    done
    sleep 1
    
    # Force kill if still running
    chromedriver_pids=$(pgrep chromedriver)
    if [ -n "$chromedriver_pids" ]; then
        for pid in $chromedriver_pids; do
            kill -KILL $pid 2>/dev/null
        done
    fi
    echo "✅ ChromeDriver processes stopped"
fi

if [ $stopped_processes -eq 0 ]; then
    echo "ℹ️  No active scraper processes found"
else
    echo "✅ Stopped $stopped_processes scraper process(es)"
fi

echo ""
echo "📁 Checking for final data exports..."

# Check for recent data in buffer (simulate final export check)
if [ -d "exports" ]; then
    recent_files=$(find exports -name "*.csv" -mmin -10 2>/dev/null)
    if [ -n "$recent_files" ]; then
        echo "📊 Recent exports found:"
        for file in $recent_files; do
            size=$(du -h "$file" 2>/dev/null | cut -f1)
            echo "  📄 $(basename "$file") ($size)"
        done
    else
        echo "ℹ️  No recent exports found"
    fi
else
    echo "ℹ️  No exports directory found"
fi

echo ""
echo "🎯 COLLECTION SUMMARY:"
echo "   All scraper processes stopped"
echo "   Web scraping resources cleaned up"
echo "   Data should be available in exports/ directory"
echo ""
echo "🚀 TO RESTART COLLECTION:"
echo "   ./run.sh → Select your preferred collection method"