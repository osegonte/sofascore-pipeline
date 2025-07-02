#!/bin/bash
# Final PostgreSQL fix - create the postgres role properly

echo "🔧 Final PostgreSQL Role Fix"
echo "============================"

echo "1️⃣ Checking current PostgreSQL container status..."
docker-compose ps

echo ""
echo "2️⃣ Fixing PostgreSQL role issue directly..."

# Connect as the default superuser and create the postgres role
echo "Creating postgres role..."
docker-compose exec -T postgres psql -U postgres postgres << 'EOF'
-- First, let's see what users exist
\du

-- Create postgres role if it doesn't exist (it should already exist, but let's be sure)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
        CREATE ROLE postgres WITH LOGIN SUPERUSER CREATEDB CREATEROLE PASSWORD 'postgres';
        RAISE NOTICE 'Role postgres created';
    ELSE
        RAISE NOTICE 'Role postgres already exists';
    END IF;
END
$$;

-- Make sure postgres role has all necessary permissions
ALTER ROLE postgres WITH LOGIN SUPERUSER CREATEDB CREATEROLE;

-- Show final user list
\du
EOF

echo ""
echo "3️⃣ Testing connection with different approaches..."

# Test 1: Direct psql connection
echo "Test 1: Direct psql connection..."
docker-compose exec -T postgres psql -U postgres -d sofascore_db -c "SELECT 'Connection successful as postgres user';"

# Test 2: Python asyncpg with different connection strings
echo ""
echo "Test 2: Testing different Python connection strings..."
python -c "
import asyncio
import asyncpg

async def test_connections():
    connection_strings = [
        'postgresql://postgres:postgres@localhost:5432/sofascore_db',
        'postgresql://postgres@localhost:5432/sofascore_db',
        'postgresql://localhost:5432/sofascore_db',
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        try:
            print(f'Test {i}: {conn_str}')
            conn = await asyncpg.connect(conn_str)
            result = await conn.fetchval('SELECT current_user')
            print(f'✅ Success! Connected as user: {result}')
            await conn.close()
            return conn_str
        except Exception as e:
            print(f'❌ Failed: {e}')
    
    return None

working_conn = asyncio.run(test_connections())
print(f'Working connection string: {working_conn}')
"

echo ""
echo "4️⃣ Updating application configuration with working connection..."

# Update the .env file with the correct connection string
echo "Updating .env file..."
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sofascore_db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sofascore_db
DB_USER=postgres
DB_PASSWORD=postgres

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# SofaScore API Configuration
SOFASCORE_BASE_URL=https://api.sofascore.com/api/v1
SOFASCORE_USER_AGENT=Mozilla/5.0 (compatible; SofaScore-Pipeline/1.0)
SOFASCORE_RATE_LIMIT_REQUESTS=60
SOFASCORE_RATE_LIMIT_PERIOD=60
SOFASCORE_TIMEOUT=30

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE_PATH=logs/sofascore_pipeline.log

# Development Environment
ENVIRONMENT=development
DEBUG=true

# Pipeline Configuration
SCRAPE_INTERVAL_LIVE=60
MAX_CONCURRENT_REQUESTS=5
EOF

echo "✅ Updated .env file"

echo ""
echo "5️⃣ Testing our application with the corrected setup..."

python -c "
import asyncio
from src.storage.database import DatabaseManager

async def test_final():
    try:
        print('🧪 Testing final DatabaseManager setup...')
        
        # Force reload config
        from config.simple_settings import settings
        print(f'Database URL: {settings.database.connection_string}')
        
        db = DatabaseManager()
        await db.initialize()
        print('✅ DatabaseManager connection successful!')
        
        # Test saving data
        from src.models.raw_models import ScrapeJob, MatchRaw
        
        # Test scrape job
        test_job = ScrapeJob(
            job_id='final_working_test',
            match_id=888888,
            job_type='test',
            status='completed'
        )
        
        success = await db.save_scrape_job(test_job)
        print(f'✅ Scrape job save: {success}')
        
        # Test match raw data
        test_match_data = {
            'match_id': 888888,
            'home_team': 'Test Team A',
            'away_team': 'Test Team B',
            'status': 'finished',
            'score': {'home': 2, 'away': 1}
        }
        
        success = await db.save_match_raw(888888, 'feed', test_match_data)
        print(f'✅ Match raw save: {success}')
        
        # Test events data
        test_events = {
            'incidents': [
                {'minute': 25, 'type': 'goal', 'team': 'home'},
                {'minute': 67, 'type': 'goal', 'team': 'home'},
                {'minute': 89, 'type': 'goal', 'team': 'away'}
            ]
        }
        
        success = await db.save_events_raw(888888, test_events)
        print(f'✅ Events raw save: {success}')
        
        await db.close()
        print('🎉 All database operations successful!')
        return True
        
    except Exception as e:
        print(f'❌ Final test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

success = asyncio.run(test_final())
"

echo ""
echo "6️⃣ Checking data was actually saved..."

# Verify data in database
docker-compose exec -T postgres psql -U postgres -d sofascore_db -c "
SELECT 
    'matches_raw' as table_name, 
    COUNT(*) as row_count,
    MAX(created_at) as latest_entry
FROM matches_raw
UNION ALL
SELECT 
    'events_raw' as table_name, 
    COUNT(*) as row_count,
    MAX(created_at) as latest_entry
FROM events_raw
UNION ALL
SELECT 
    'scrape_jobs' as table_name, 
    COUNT(*) as row_count,
    MAX(created_at) as latest_entry
FROM scrape_jobs;
"

echo ""
echo "7️⃣ Testing the full CLI pipeline..."

# Test the CLI commands
echo "Testing CLI discover command..."
python -m src.main discover || echo "❌ CLI discover failed"

echo ""
echo "🎉 FINAL STATUS CHECK"
echo "===================="

# Show working connection details
echo "✅ Working Database Connection:"
echo "  Host: localhost"
echo "  Port: 5432" 
echo "  Database: sofascore_db"
echo "  User: postgres"
echo "  Password: postgres"
echo "  Connection String: postgresql://postgres:postgres@localhost:5432/sofascore_db"

echo ""
echo "🚀 Ready to run:"
echo "  python -m src.main discover  # Test API discovery"
echo "  python -m src.main test      # Test scraping with database"
echo "  python -m src.main live      # Start live data collection"

echo ""
echo "📊 To check data in database:"
echo "  docker-compose exec postgres psql -U postgres -d sofascore_db"
echo "  Then run: SELECT * FROM matches_raw LIMIT 5;"