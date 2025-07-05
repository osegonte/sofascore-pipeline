#!/bin/bash

# Quick validation script for SofaScore pipeline
echo "SofaScore Pipeline - Quick Validation"
echo "===================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $(basename $VIRTUAL_ENV)"
else
    echo "❌ Virtual environment not active"
    echo "   Run: source venv/bin/activate"
    exit 1
fi

# Run essential tests only
echo -e "\n🔍 Running essential validation tests..."

echo -e "\n1. Database Connection Test:"
python -c "
from config.database import test_connection
if test_connection():
    print('   ✅ Database connection successful')
else:
    print('   ❌ Database connection failed')
    exit(1)
"

echo -e "\n2. Data Quality Check:"
python -c "
from config.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT COUNT(*) FROM live_matches'))
        matches = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM goal_events'))
        goals = result.scalar()
        result = conn.execute(text('SELECT COUNT(*) FROM fixtures'))
        fixtures = result.scalar()
    print(f'   ✅ Data counts: {matches} matches, {goals} goals, {fixtures} fixtures')
except Exception as e:
    print(f'   ❌ Data quality check failed: {e}')
    exit(1)
"

echo -e "\n3. API Connectivity Test:"
python -c "
from src.fixture_scraper import FixtureScraper
from datetime import datetime
try:
    scraper = FixtureScraper()
    fixtures = scraper.get_fixtures_by_date(datetime.now().strftime('%Y-%m-%d'))
    print(f'   ✅ API connectivity successful (found {len(fixtures)} fixtures)')
except Exception as e:
    print(f'   ⚠️  API connectivity issue: {e}')
"

echo -e "\n4. Goal Analysis Validation:"
python -c "
from config.database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('''
            SELECT 
                COUNT(*) as total_goals,
                COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                ROUND(AVG(total_minute), 1) as avg_minute
            FROM goal_events
            WHERE total_minute IS NOT NULL
        '''))
        row = result.fetchone()
        if row and row[0] > 0:
            total, late, avg_min = row[0], row[1], row[2]
            late_pct = (late / total * 100) if total > 0 else 0
            print(f'   ✅ Goal analysis: {total} goals, {late} late ({late_pct:.1f}%), avg {avg_min} min')
        else:
            print('   ℹ️  No goals found for analysis')
except Exception as e:
    print(f'   ❌ Goal analysis failed: {e}')
"

echo -e "\n✅ Quick validation completed!"
echo "   For comprehensive validation, run: python tests/run_all_tests.py"
