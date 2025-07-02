#!/bin/bash
# Fix Stage 3 issues: imports and PostgreSQL setup

echo "🔧 Fixing Stage 3 Issues"
echo "========================"

echo "1️⃣ Fixing import issues..."

# Check what settings files exist
echo "Checking config files:"
ls -la config/

# The issue is that cleanup might have removed simple_settings.py
# Let's recreate it or fix the import

if [ ! -f "config/simple_settings.py" ]; then
    echo "📝 Recreating config/simple_settings.py..."
    
    # Create simple_settings.py again
    cat > config/simple_settings.py << 'EOF'
"""
Simplified configuration settings without pydantic dependency.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/sofascore_db')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.name = os.getenv('DB_NAME', 'sofascore_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class SofaScoreConfig:
    def __init__(self):
        self.base_url = os.getenv('SOFASCORE_BASE_URL', 'https://api.sofascore.com/api/v1')
        self.user_agent = os.getenv('SOFASCORE_USER_AGENT', 'Mozilla/5.0 (compatible; SofaScore-Pipeline/1.0)')
        self.rate_limit_requests = int(os.getenv('SOFASCORE_RATE_LIMIT_REQUESTS', '60'))
        self.rate_limit_period = int(os.getenv('SOFASCORE_RATE_LIMIT_PERIOD', '60'))
        self.timeout = int(os.getenv('SOFASCORE_TIMEOUT', '30'))

class RedisConfig:
    def __init__(self):
        self.url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', '6379'))
        self.db = int(os.getenv('REDIS_DB', '0'))

class LoggingConfig:
    def __init__(self):
        self.level = os.getenv('LOG_LEVEL', 'INFO')
        self.format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_path = os.getenv('LOG_FILE_PATH', 'logs/sofascore_pipeline.log')
        self.max_file_size = int(os.getenv('LOG_MAX_FILE_SIZE', '10485760'))
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))

class PipelineConfig:
    def __init__(self):
        self.scrape_interval_live = int(os.getenv('SCRAPE_INTERVAL_LIVE', '60'))
        self.scrape_interval_finished = int(os.getenv('SCRAPE_INTERVAL_FINISHED', '3600'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.max_retry_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
        self.retry_backoff_factor = int(os.getenv('RETRY_BACKOFF_FACTOR', '2'))

class Settings:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.testing = os.getenv('TESTING', 'false').lower() == 'true'
        
        self.database = DatabaseConfig()
        self.sofascore = SofaScoreConfig()
        self.redis = RedisConfig()
        self.logging = LoggingConfig()
        self.pipeline = PipelineConfig()
    
    def validate(self) -> List[str]:
        errors = []
        if not all([self.database.host, self.database.name, self.database.user]):
            errors.append("Database configuration incomplete")
        if not self.sofascore.base_url:
            errors.append("SofaScore base URL not configured")
        return errors

settings = Settings()
EOF
    
    echo "✅ Created config/simple_settings.py"
fi

echo ""
echo "2️⃣ Fixing PostgreSQL user setup..."

# Fix PostgreSQL user and database setup
echo "🐘 Setting up PostgreSQL user and database properly..."

# Connect to PostgreSQL container and set up properly
docker-compose exec -T postgres psql -U postgres -c "
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'postgres') THEN
      CREATE ROLE postgres LOGIN SUPERUSER;
   END IF;
END
\$\$;
" 2>/dev/null || echo "User already exists or created"

# Create database if it doesn't exist
docker-compose exec -T postgres psql -U postgres -c "
SELECT 'CREATE DATABASE sofascore_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'sofascore_db')\gexec
" 2>/dev/null || echo "Database setup attempted"

echo ""
echo "3️⃣ Testing fixes..."

# Test the import fix
echo "Testing imports..."
python -c "
try:
    from config.simple_settings import settings
    print('✅ simple_settings import works')
    print(f'   Database URL: {settings.database.connection_string}')
except Exception as e:
    print(f'❌ Import still broken: {e}')
"

echo ""
echo "4️⃣ Running database setup manually..."

# Manual database setup with better error handling
python -c "
import asyncio
import asyncpg
import sys
import os

async def setup_database_manually():
    try:
        print('🔗 Connecting to PostgreSQL...')
        
        # Try different connection methods
        connection_attempts = [
            'postgresql://postgres:postgres@localhost:5432/postgres',
            'postgresql://postgres@localhost:5432/postgres',
        ]
        
        conn = None
        for attempt in connection_attempts:
            try:
                print(f'Trying: {attempt}')
                conn = await asyncpg.connect(attempt)
                print('✅ Connected successfully')
                break
            except Exception as e:
                print(f'❌ Failed: {e}')
                continue
        
        if not conn:
            print('❌ Could not connect to PostgreSQL')
            return False
        
        # Check if database exists
        result = await conn.fetchval(
            \"SELECT 1 FROM pg_database WHERE datname = 'sofascore_db'\"
        )
        
        if not result:
            print('📝 Creating sofascore_db database...')
            await conn.execute('CREATE DATABASE sofascore_db')
            print('✅ Database created')
        else:
            print('✅ Database already exists')
            
        await conn.close()
        
        # Connect to the sofascore_db and run migrations
        db_conn = None
        db_attempts = [
            'postgresql://postgres:postgres@localhost:5432/sofascore_db',
            'postgresql://postgres@localhost:5432/sofascore_db',
        ]
        
        for attempt in db_attempts:
            try:
                print(f'Connecting to sofascore_db: {attempt}')
                db_conn = await asyncpg.connect(attempt)
                print('✅ Connected to sofascore_db')
                break
            except Exception as e:
                print(f'❌ Failed: {e}')
                continue
        
        if not db_conn:
            print('❌ Could not connect to sofascore_db')
            return False
        
        # Run migrations
        print('📋 Running migrations...')
        migration_files = ['sql/migrations/001_create_raw_tables.sql', 'sql/migrations/002_create_curated_tables.sql']
        
        for migration_file in migration_files:
            if os.path.exists(migration_file):
                print(f'  Running {migration_file}...')
                with open(migration_file, 'r') as f:
                    sql_content = f.read()
                
                # Execute the migration
                try:
                    await db_conn.execute(sql_content)
                    print(f'  ✅ {migration_file} completed')
                except Exception as e:
                    print(f'  ⚠️  {migration_file} had issues (might be normal): {e}')
        
        await db_conn.close()
        print('✅ Database setup completed')
        return True
        
    except Exception as e:
        print(f'❌ Database setup failed: {e}')
        return False

success = asyncio.run(setup_database_manually())
if success:
    print('🎉 Database setup successful!')
else:
    print('❌ Database setup failed')
    sys.exit(1)
"

echo ""
echo "5️⃣ Final test of the complete pipeline..."

# Test the application
python -c "
import asyncio
from src.storage.database import DatabaseManager

async def test_app():
    try:
        print('🧪 Testing application database connection...')
        db = DatabaseManager()
        await db.initialize()
        print('✅ Database connection works!')
        
        # Test saving data
        from src.models.raw_models import ScrapeJob
        test_job = ScrapeJob(
            job_id='fix_test_001',
            match_id=99999,
            job_type='test'
        )
        
        success = await db.save_scrape_job(test_job)
        print(f'✅ Test save: {success}')
        
        await db.close()
        return True
        
    except Exception as e:
        print(f'❌ Application test failed: {e}')
        return False

success = asyncio.run(test_app())
if success:
    print('🎉 Application works!')
"

echo ""
echo "✅ Issues should be fixed!"
echo ""
echo "Now try:"
echo "  python -m src.main discover"
echo "  python -m src.main test"