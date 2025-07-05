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
