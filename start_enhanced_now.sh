#!/bin/bash

# Make sure we're using enhanced scraper
cd "$(dirname "$0")"

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting ENHANCED SofaScore Scraper with Mobile API"
echo "====================================================="
echo "🎯 Features:"
echo "   • Mobile API fallbacks (api.sofascore.app)"
echo "   • UEFA qualification match support"
echo "   • Smart endpoint switching"
echo "   • Quality assessment metrics"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the enhanced scraper
python src/live_scraper_enhanced.py
