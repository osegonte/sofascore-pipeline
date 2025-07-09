#!/bin/bash
# setup_environment.sh - Setup environment for live statistics scraper

echo "🔧 Setting up SofaScore Live Statistics Environment"
echo "=================================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p exports logs tests/reports database

# Test database connection
echo "🔍 Testing database connection..."
python -c "
try:
    from config.database import test_connection
    if test_connection():
        print('✅ Database connection successful')
    else:
        print('⚠️  Database connection failed - scraper will work without DB storage')
except Exception as e:
    print(f'⚠️  Database test error: {e}')
"

# Test API connectivity
echo "🌐 Testing SofaScore API..."
python -c "
try:
    import requests
    response = requests.get('https://api.sofascore.com/api/v1/sport/football/events/live', timeout=10)
    if response.status_code == 200:
        print('✅ SofaScore API accessible')
    else:
        print(f'⚠️  API returned status {response.status_code}')
except Exception as e:
    print(f'❌ API test failed: {e}')
"

echo ""
echo "🎉 Environment setup completed!"
echo ""
echo "🚀 NEXT STEPS:"
echo "   1. Start live scraping: ./start_live_scraper.sh"
echo "   2. Monitor data: ./monitor_scraper.sh"
echo "   3. Stop scraping: ./stop_live_scraper.sh"
echo "   4. View collected data: ./view_data.sh"
echo ""
echo "📊 The scraper will collect ALL Sofascore Statistics tab metrics:"
echo "   • Match Overview, Shots, Attack, Passes, Duels, Defending, Goalkeeping"
echo "   • One CSV row per match-minute with all statistics"
echo "   • Automatic data validation and quality checks"
