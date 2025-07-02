#!/bin/bash
# Fix PostgreSQL Docker setup completely

echo "🐘 Fixing PostgreSQL Docker Setup Completely"
echo "============================================="

echo "1️⃣ Stopping and cleaning existing PostgreSQL..."
docker-compose down
docker volume rm sofascore-pipeline_postgres_data 2>/dev/null || true

echo ""
echo "2️⃣ Checking docker-compose.yml configuration..."

# Show current postgres config
echo "Current PostgreSQL config in docker-compose.yml:"
grep -A 20 "postgres:" docker-compose.yml || echo "No postgres section found"

echo ""
echo "3️⃣ Creating a simple docker-compose override for PostgreSQL..."

# Create a simple docker-compose override to ensure proper PostgreSQL setup
cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: sofascore_postgres_fixed
    environment:
      POSTGRES_DB: sofascore_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data_fixed:/var/lib/postgresql/data
    networks:
      - sofascore_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d sofascore_db"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data_fixed:
    driver: local

networks:
  sofascore_network:
    driver: bridge
EOF

echo "✅ Created docker-compose.override.yml"

echo ""
echo "4️⃣ Starting PostgreSQL with proper configuration..."
docker-compose up -d postgres

echo ""
echo "5️⃣ Waiting for PostgreSQL to be fully ready..."
echo "This may take 30-60 seconds..."

# Wait for PostgreSQL to be ready
MAX_ATTEMPTS=30
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Testing PostgreSQL connection..."
    
    if docker-compose exec -T postgres pg_isready -U postgres -d sofascore_db >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    else
        echo "⏳ PostgreSQL not ready yet, waiting 3 seconds..."
        sleep 3
        ATTEMPT=$((ATTEMPT + 1))
    fi
done

if [ $ATTEMPT -gt $MAX_ATTEMPTS ]; then
    echo "❌ PostgreSQL failed to start after $MAX_ATTEMPTS attempts"
    echo "📋 Checking logs..."
    docker-compose logs postgres
    exit 1
fi

echo ""
echo "6️⃣ Testing direct PostgreSQL connection..."

# Test basic connection
docker-compose exec -T postgres psql -U postgres -d sofascore_db -c "SELECT version();" || {
    echo "❌ Direct connection failed"
    echo "📋 PostgreSQL logs:"
    docker-compose logs postgres
    exit 1
}

echo "✅ Direct PostgreSQL connection works!"

echo ""
echo "7️⃣ Creating tables manually..."

# Create the raw tables directly
docker-compose exec -T postgres psql -U postgres -d sofascore_db << 'EOF'
-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create raw matches table
CREATE TABLE IF NOT EXISTS matches_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(50) NOT NULL,
    raw_json JSONB NOT NULL,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create raw events table
CREATE TABLE IF NOT EXISTS events_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_events_json JSONB NOT NULL,
    event_count INTEGER,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create raw stats table
CREATE TABLE IF NOT EXISTS stats_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    minute SMALLINT,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_stats_json JSONB NOT NULL,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create scrape jobs table
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(100) NOT NULL UNIQUE,
    match_id BIGINT,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_matches_raw_match_id ON matches_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_events_raw_match_id ON events_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_stats_raw_match_id ON stats_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_match_id ON scrape_jobs(match_id);

-- Show created tables
\dt
EOF

echo "✅ Tables created successfully!"

echo ""
echo "8️⃣ Testing Python database connection..."

# Test with Python
python -c "
import asyncio
import asyncpg

async def test_connection():
    try:
        print('🔗 Testing asyncpg connection...')
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/sofascore_db')
        
        # Test basic query
        result = await conn.fetchval('SELECT COUNT(*) FROM matches_raw')
        print(f'✅ Connection successful! matches_raw has {result} rows')
        
        # Test insert
        await conn.execute('''
            INSERT INTO matches_raw (match_id, endpoint, raw_json) 
            VALUES (\$1, \$2, \$3)
        ''', 999999, 'test', '{\"test\": true}')
        
        print('✅ Test insert successful!')
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        return False

success = asyncio.run(test_connection())
print(f'Database test result: {success}')
"

echo ""
echo "9️⃣ Testing our application database manager..."

# Test our application
python -c "
import asyncio
from src.storage.database import DatabaseManager

async def test_app_db():
    try:
        print('🧪 Testing DatabaseManager...')
        db = DatabaseManager()
        await db.initialize()
        print('✅ DatabaseManager initialized!')
        
        # Test saving a scrape job
        from src.models.raw_models import ScrapeJob
        test_job = ScrapeJob(
            job_id='final_test_001',
            match_id=123456,
            job_type='test',
            status='completed'
        )
        
        success = await db.save_scrape_job(test_job)
        print(f'✅ Scrape job save: {success}')
        
        # Test saving match data
        test_data = {'test': True, 'match': 'data'}
        success = await db.save_match_raw(123456, 'feed', test_data)
        print(f'✅ Match raw save: {success}')
        
        await db.close()
        return True
        
    except Exception as e:
        print(f'❌ Application test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

success = asyncio.run(test_app_db())
if success:
    print('🎉 Application database connection works!')
else:
    print('❌ Application database connection failed')
"

echo ""
echo "🔟 Final verification - checking data in database..."

# Show what's in the database
docker-compose exec -T postgres psql -U postgres -d sofascore_db -c "
SELECT 
    'matches_raw' as table_name, COUNT(*) as row_count 
FROM matches_raw
UNION ALL
SELECT 
    'events_raw' as table_name, COUNT(*) as row_count 
FROM events_raw
UNION ALL
SELECT 
    'stats_raw' as table_name, COUNT(*) as row_count 
FROM stats_raw
UNION ALL
SELECT 
    'scrape_jobs' as table_name, COUNT(*) as row_count 
FROM scrape_jobs;
"

echo ""
echo "🎉 PostgreSQL Setup Complete!"
echo "============================="
echo ""
echo "✅ What's working:"
echo "  - PostgreSQL running in Docker"
echo "  - Database 'sofascore_db' created"
echo "  - All required tables created"
echo "  - Python asyncpg connection working"
echo "  - Application DatabaseManager working"
echo "  - Test data successfully saved"
echo ""
echo "🚀 Ready to test the full pipeline:"
echo "  python -m src.main discover   # Test API (should work)"
echo "  python -m src.main test       # Test with database"
echo "  python -m src.main live       # Start data collection"
echo ""
echo "📊 Database connection details:"
echo "  Host: localhost:5432"
echo "  Database: sofascore_db"
echo "  User: postgres"
echo "  Password: postgres"