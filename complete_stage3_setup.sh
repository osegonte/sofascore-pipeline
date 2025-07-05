#!/bin/bash
# complete_stage3_setup.sh - Complete Stage 3 Database Setup

echo "🚀 SofaScore Pipeline - Complete Stage 3 Setup"
echo "==============================================="
echo "This script will:"
echo "1. Create database configuration files"
echo "2. Create CSV import tool"
echo "3. Create database manager"
echo "4. Test database connection"
echo "5. Import your existing CSV data"
echo ""

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo "❌ Please run this from your sofascore-pipeline directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Please activate your virtual environment first:"
    echo "   source venv/bin/activate"
    exit 1
fi

echo "📁 Creating directories..."
mkdir -p config database backups

echo ""
echo "🔧 Creating database configuration..."

# Create config/database.py with URL encoding fix
cat > config/database.py << 'EOF'
"""
Database configuration for SofaScore pipeline
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'sofascore_data')
DB_USER = os.getenv('DB_USER', 'sofascore_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Boss@1759')

# URL encode the password to handle special characters
encoded_password = quote_plus(DB_PASSWORD)

# Create database URL with encoded password
DATABASE_URL = f"postgresql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_table_info():
    """Get information about existing tables"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            return tables
    except Exception as e:
        print(f"Error getting table info: {e}")
        return []
EOF

echo "✅ Created config/database.py"

# Create database models
cat > src/database_models.py << 'EOF'
"""
SQLAlchemy models for SofaScore database
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Decimal, ForeignKey, Text, Date, Time, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class LiveMatch(Base):
    __tablename__ = 'live_matches'
    
    match_id = Column(BigInteger, primary_key=True)
    competition = Column(String(255))
    league = Column(String(255))
    match_date = Column(Date)
    match_time = Column(Time)
    match_datetime = Column(DateTime)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    home_team_id = Column(BigInteger)
    away_team_id = Column(BigInteger)
    venue = Column(String(255))
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    minutes_elapsed = Column(Integer)
    period = Column(Integer)
    status = Column(String(100))
    status_type = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

# Additional models would go here...
EOF

echo "✅ Created src/database_models.py"

# Test database connection
echo ""
echo "🔌 Testing database connection..."
python3 -c "
import sys
sys.path.append('.')
from config.database import test_connection
test_connection()
"

if [ $? -eq 0 ]; then
    echo "✅ Database connection successful!"
else
    echo "❌ Database connection failed. Please check your PostgreSQL setup."
    exit 1
fi

# Create CSV import tool
echo ""
echo "📥 Creating CSV import tool..."
bash create_csv_import.sh

# Create database manager
echo ""
echo "🛠️  Creating database manager..."
bash create_db_manager.sh

# Make scripts executable
chmod +x database/*.py

echo ""
echo "🎯 Testing database setup..."
python database/test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Database setup completed successfully!"
    echo ""
    echo "🚀 Next Steps:"
    echo "=============="
    echo "1. Import your existing CSV data:"
    echo "   python database/csv_import.py"
    echo ""
    echo "2. Check database status:"
    echo "   python database/db_manager.py status"
    echo ""
    echo "3. Run goal analysis:"
    echo "   python database/db_manager.py analyze"
    echo ""
    echo "4. Export goal analysis:"
    echo "   python database/db_manager.py export"
    echo ""
    echo "📁 Your Stage 3 database integration is ready!"
else
    echo "❌ Database setup failed. Please check the errors above."
    exit 1
fi