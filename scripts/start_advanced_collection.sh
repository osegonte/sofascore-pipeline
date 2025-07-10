#!/bin/bash
# scripts/start_advanced_collection.sh - Start advanced collection

echo "🎯 Starting ADVANCED Complete Data Collection"
echo "============================================="

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting quality-focused collection with advanced features..."
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the quality-focused scraper (our main complete scraper)
python src/live_scraper_quality_focused.py
