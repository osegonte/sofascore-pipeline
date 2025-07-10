#!/bin/bash
# scripts/start_collection.sh - Unified collection starter

echo "🚀 Starting SofaScore Data Collection"
echo "====================================="

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🎯 FEATURES:"
echo "   • Complete data collection (48 fields)"
echo "   • Web scraping + API fusion"
echo "   • ML-based estimation"
echo "   • Zero elimination guarantee"
echo "   • Competition-specific modeling"
echo ""
echo "📊 TARGET: 95-100% data completeness"
echo "🔄 Collection every 5 minutes, export every 15 minutes"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the main scraper
python src/live_scraper_quality_focused.py
