#!/bin/bash
# start_live_scraper.sh - Start the comprehensive live statistics scraper

echo "🚀 Starting SofaScore Live Statistics Scraper"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup first:"
    echo "   ./setup_environment.sh"
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

# Check database connection
echo "🔍 Testing database connection..."
python -c "from config.database import test_connection; exit(0 if test_connection() else 1)"
if [ $? -ne 0 ]; then
    echo "⚠️  Database connection failed. Scraper will still work but won't store to DB."
fi

echo "✅ Starting comprehensive live statistics collection..."
echo "📊 Collecting ALL Sofascore Statistics tab metrics"
echo "⏱️  Collection runs every 5 minutes"
echo "📁 Data exported to: exports/live_match_minutes_complete_TIMESTAMP.csv"
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the scraper
python src/live_scraper.py

echo "👋 Live scraper stopped"
