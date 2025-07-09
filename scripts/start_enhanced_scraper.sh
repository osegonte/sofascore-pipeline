#!/bin/bash
# start_enhanced_scraper.sh - Start the enhanced live statistics scraper

echo "🚀 Starting ENHANCED SofaScore Live Statistics Scraper"
echo "====================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup first:"
    echo "   ./scripts/setup_environment.sh"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required directories exist
mkdir -p exports logs

# Check Python dependencies
echo "📋 Checking dependencies..."
python -c "import requests, pandas, schedule" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

echo "✅ Starting ENHANCED live statistics collection..."
echo "🎯 NEW FEATURES:"
echo "   • Mobile API fallbacks"
echo "   • Smart match prioritization" 
echo "   • Better statistics extraction"
echo "   • Quality assessment"
echo "⏱️  Collection runs every 5 minutes"
echo "📁 Data exported to: exports/enhanced_live_statistics_TIMESTAMP.csv"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the enhanced scraper
python src/live_scraper_enhanced.py

echo "👋 Enhanced scraper stopped"
