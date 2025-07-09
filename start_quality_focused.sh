#!/bin/bash
# start_quality_focused.sh - Start the quality-focused scraper

echo "🎯 Starting Quality-Focused SofaScore Scraper"
echo "=============================================="

# Check virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🏆 QUALITY-FIRST FEATURES:"
echo "   • Tier 1 competitions prioritized"
echo "   • Statistical estimation reduces zeros"
echo "   • Enhanced data completeness tracking"
echo "   • Mobile API fallbacks"
echo "   • Smart competition filtering"
echo ""
echo "🎯 Expected Results:"
echo "   • 95%+ success rate on major competitions"
echo "   • 80%+ data completeness"
echo "   • Significant zero reduction"
echo ""
echo "🛑 Press Ctrl+C to stop"
echo ""

# Start the quality-focused scraper
python src/live_scraper_quality_focused.py
