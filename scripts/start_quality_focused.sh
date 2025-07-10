#!/bin/bash
# scripts/start_quality_focused.sh - Start quality-focused collection

echo "🚀 Starting Quality-Focused Collection"
echo "======================================"

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🎯 Quality-focused features enabled"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the quality-focused scraper
python src/live_scraper_quality_focused.py
