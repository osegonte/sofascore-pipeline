#!/bin/bash
# setup_stage3.sh - Complete Stage 3 Database Setup

echo "🚀 SofaScore Pipeline - Stage 3 Database Setup"
echo "=============================================="

# Create directories
mkdir -p config database

# Create fixed config/database.py
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

echo "✅ Created config/database.py with URL encoding"

# Create src/database_models.py
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

class GoalEvent(Base):
    __tablename__ = 'goal_events'
    
    goal_id = Column(BigInteger, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    exact_timestamp = Column(Integer, nullable=False)
    added_time = Column(Integer, default=0)
    scoring_player = Column(String(255))
    scoring_player_id = Column(BigInteger)
    assisting_player = Column(String(255))
    assisting_player_id = Column(BigInteger)
    goal_type = Column(String(50), default='regular')
    team_side = Column(String(10))
    description = Column(Text)
    period = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class TeamStatistic(Base):
    __tablename__ = 'team_statistics'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    team_side = Column(String(10))
    team_name = Column(String(255))
    possession_percentage = Column(Decimal(5,2))
    shots_on_target = Column(Integer)
    total_shots = Column(Integer)
    corners = Column(Integer)
    fouls = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    offsides = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class PlayerStatistic(Base):
    __tablename__ = 'player_statistics'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    player_name = Column(String(255), nullable=False)
    player_id = Column(BigInteger)
    team_side = Column(String(10))
    position = Column(String(50))
    jersey_number = Column(Integer)
    is_starter = Column(Boolean, default=False)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    cards_received = Column(Integer, default=0)
    minutes_played = Column(Integer)
    shots_on_target = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class Fixture(Base):
    __tablename__ = 'fixtures'
    
    fixture_id = Column(BigInteger, primary_key=True)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    home_team_id = Column(BigInteger)
    away_team_id = Column(BigInteger)
    kickoff_time = Column(DateTime)
    kickoff_date = Column(Date)
    kickoff_time_formatted = Column(Time)
    tournament = Column(String(255))
    tournament_id = Column(BigInteger)
    round_info = Column(String(255))
    status = Column(String(100))
    venue = Column(String(255))
    source_type = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class GoalAnalysis(Base):
    __tablename__ = 'goal_analysis'
    
    id = Column(Integer, primary_key=True)
    analysis_date = Column(Date, default=datetime.utcnow().date)
    total_matches_analyzed = Column(Integer)
    total_goals_analyzed = Column(Integer)
    late_goals_count = Column(Integer)
    late_goals_percentage = Column(Decimal(5,2))
    very_late_goals_count = Column(Integer)
    injury_time_goals_count = Column(Integer)
    average_goals_per_match = Column(Decimal(5,2))
    average_goal_minute = Column(Decimal(5,2))
    goals_0_15 = Column(Integer, default=0)
    goals_16_30 = Column(Integer, default=0)
    goals_31_45 = Column(Integer, default=0)
    goals_46_60 = Column(Integer, default=0)
    goals_61_75 = Column(Integer, default=0)
    goals_76_90 = Column(Integer, default=0)
    goals_90_plus = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
EOF

echo "✅ Created src/database_models.py"

# Create database/test_setup.py
cat > database/test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test database setup and connection
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import test_connection, engine, get_table_info
from sqlalchemy import text

def test_database_schema():
    """Test database schema and tables"""
    print("Testing Database Schema...")
    print("=" * 40)
    
    # Test connection
    if not test_connection():
        return False
    
    # Get table information
    tables = get_table_info()
    expected_tables = ['fixtures', 'goal_analysis', 'goal_events', 'live_matches', 'player_statistics', 'team_statistics']
    
    print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
    
    # Check if all expected tables exist
    missing_tables = [t for t in expected_tables if t not in tables]
    if missing_tables:
        print(f"❌ Missing tables: {missing_tables}")
        return False
    
    # Test each table structure
    for table in expected_tables:
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"✅ Table '{table}': {count} records")
        except Exception as e:
            print(f"❌ Error accessing table '{table}': {e}")
            return False
    
    return True

def test_goal_analysis_features():
    """Test goal analysis specific features"""
    print("\nTesting Goal Analysis Features...")
    print("=" * 40)
    
    try:
        with engine.connect() as conn:
            # Test computed columns by inserting a test goal
            conn.execute(text("""
                INSERT INTO live_matches (match_id, home_team, away_team, competition)
                VALUES (888888, 'Team X', 'Team Y', 'Test League')
                ON CONFLICT (match_id) DO NOTHING
            """))
            
            # Insert a late goal to test computed columns
            conn.execute(text("""
                INSERT INTO goal_events (goal_id, match_id, exact_timestamp, added_time, scoring_player, team_side, competition)
                VALUES (777777, 888888, 78, 2, 'Test Player', 'home', 'Test League')
                ON CONFLICT (goal_id) DO NOTHING
            """))
            conn.commit()
            
            # Test computed columns
            result = conn.execute(text("""
                SELECT total_minute, is_late_goal, time_interval, is_very_late_goal, is_injury_time_goal
                FROM goal_events 
                WHERE goal_id = 777777
            """))
            row = result.fetchone()
            
            if row:
                total_min, is_late, interval, is_very_late, is_injury = row
                print(f"✅ Computed columns working:")
                print(f"   Total minute: {total_min}")
                print(f"   Is late goal: {is_late}")
                print(f"   Time interval: {interval}")
                print(f"   Is very late: {is_very_late}")
                print(f"   Is injury time: {is_injury}")
            
            # Cleanup test data
            conn.execute(text("DELETE FROM goal_events WHERE goal_id = 777777"))
            conn.execute(text("DELETE FROM live_matches WHERE match_id = 888888"))
            conn.commit()
            print("✅ Test data cleaned up")
            
    except Exception as e:
        print(f"❌ Goal analysis features test failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("SofaScore Database Setup Test")
    print("=" * 50)
    
    success = True
    success &= test_database_schema()
    success &= test_goal_analysis_features()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All database tests passed!")
        print("✅ Database setup is complete and working correctly")
        print("\nNext steps:")
        print("1. Run: python database/csv_import.py")
        print("2. Run: python database/db_manager.py status")
        print("3. Set up automated goal analysis")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF

echo "✅ Created database/test_setup.py"

# Make scripts executable
chmod +x database/test_setup.py

echo ""
echo "✅ Stage 3 database configuration files created!"
echo ""
echo "Now test the database connection:"
echo "python database/test_setup.py"