#!/bin/bash
# create_db_manager.sh - Create database management tool

echo "🛠️  Creating Database Manager Tool..."
echo "===================================="

cat > database/db_manager.py << 'EOF'
#!/usr/bin/env python3
"""
Database management utilities for SofaScore pipeline
"""
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text

class DatabaseManager:
    """Database management and analysis utilities"""
    
    def __init__(self):
        self.engine = engine
    
    def get_database_status(self):
        """Get comprehensive database status"""
        print("SofaScore Database Status")
        print("=" * 50)
        
        try:
            with self.engine.connect() as conn:
                # Table counts
                tables = ['live_matches', 'goal_events', 'team_statistics', 
                         'player_statistics', 'fixtures', 'goal_analysis']
                
                print("📊 TABLE STATISTICS:")
                total_records = 0
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    total_records += count
                    print(f"   {table:20} {count:>8} records")
                
                print(f"   {'TOTAL':20} {total_records:>8} records")
                
                # Goal analysis summary
                if self.get_table_count('goal_events') > 0:
                    print("\n🎯 GOAL ANALYSIS SUMMARY:")
                    result = conn.execute(text("""
                        SELECT 
                            COUNT(*) as total_goals,
                            COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                            ROUND(COUNT(*) FILTER (WHERE is_late_goal = true) * 100.0 / COUNT(*), 1) as late_goal_percentage,
                            COUNT(DISTINCT match_id) as matches_with_goals
                        FROM goal_events
                    """))
                    
                    row = result.fetchone()
                    if row:
                        print(f"   Total goals: {row[0]}")
                        print(f"   Late goals (75+ min): {row[1]} ({row[2]}%)")
                        print(f"   Matches with goals: {row[3]}")
                
                # Recent activity
                print("\n📅 RECENT ACTIVITY:")
                result = conn.execute(text("""
                    SELECT 
                        'Live Matches' as type,
                        COUNT(*) as count,
                        MAX(scraped_at) as latest
                    FROM live_matches
                    WHERE scraped_at > NOW() - INTERVAL '24 hours'
                    
                    UNION ALL
                    
                    SELECT 
                        'Goal Events' as type,
                        COUNT(*) as count,
                        MAX(scraped_at) as latest
                    FROM goal_events
                    WHERE scraped_at > NOW() - INTERVAL '24 hours'
                    
                    UNION ALL
                    
                    SELECT 
                        'Fixtures' as type,
                        COUNT(*) as count,
                        MAX(scraped_at) as latest
                    FROM fixtures
                    WHERE scraped_at > NOW() - INTERVAL '24 hours'
                """))
                
                for row in result:
                    if row[1] > 0:
                        latest_str = row[2].strftime('%Y-%m-%d %H:%M') if row[2] else 'N/A'
                        print(f"   {row[0]:15} {row[1]:>3} records (latest: {latest_str})")
                
        except Exception as e:
            print(f"❌ Error getting database status: {e}")
    
    def get_table_count(self, table_name):
        """Get count of records in a table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except Exception as e:
            print(f"Error getting count for {table_name}: {e}")
            return 0
    
    def analyze_goal_timing(self):
        """Detailed goal timing analysis"""
        print("\n🕐 DETAILED GOAL TIMING ANALYSIS")
        print("=" * 50)
        
        try:
            with self.engine.connect() as conn:
                # Goal distribution by time interval
                result = conn.execute(text("""
                    SELECT 
                        time_interval,
                        COUNT(*) as goals,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
                    FROM goal_events 
                    GROUP BY time_interval
                    ORDER BY 
                        CASE time_interval
                            WHEN '0-15' THEN 1
                            WHEN '16-30' THEN 2
                            WHEN '31-45' THEN 3
                            WHEN '46-60' THEN 4
                            WHEN '61-75' THEN 5
                            WHEN '76-90' THEN 6
                            WHEN '90+' THEN 7
                        END
                """))
                
                print("Goal Distribution by 15-minute intervals:")
                for row in result:
                    bar = "█" * int(row[2] / 2)  # Visual bar chart
                    print(f"   {row[0]:>6} min: {row[1]:>3} goals ({row[2]:>4.1f}%) {bar}")
                
                # Late goals by competition
                result = conn.execute(text("""
                    SELECT 
                        competition,
                        COUNT(*) as total_goals,
                        COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                        ROUND(COUNT(*) FILTER (WHERE is_late_goal = true) * 100.0 / COUNT(*), 1) as late_goal_percentage
                    FROM goal_events 
                    WHERE competition IS NOT NULL
                    GROUP BY competition
                    HAVING COUNT(*) >= 3
                    ORDER BY late_goal_percentage DESC
                    LIMIT 10
                """))
                
                print("\nLate Goal Percentage by Competition (3+ goals):")
                for row in result:
                    print(f"   {row[0]:30} {row[2]:>2}/{row[1]:>2} goals ({row[3]:>4.1f}%)")
        
        except Exception as e:
            print(f"❌ Error in goal timing analysis: {e}")
    
    def backup_database(self, backup_dir='backups'):
        """Export database to CSV backup"""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n💾 BACKING UP DATABASE")
        print("=" * 50)
        
        tables = ['live_matches', 'goal_events', 'team_statistics', 
                 'player_statistics', 'fixtures', 'goal_analysis']
        
        backed_up = 0
        for table in tables:
            try:
                df = pd.read_sql_table(table, self.engine)
                if not df.empty:
                    filename = f"{backup_dir}/{table}_backup_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    print(f"✅ {table}: {len(df)} records -> {filename}")
                    backed_up += 1
                else:
                    print(f"⚠️  {table}: No data to backup")
            except Exception as e:
                print(f"❌ Error backing up {table}: {e}")
        
        print(f"\n📁 Backup completed: {backed_up}/{len(tables)} tables")
    
    def export_goal_analysis(self, output_file=None):
        """Export goal analysis to CSV for external analysis"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"goal_analysis_export_{timestamp}.csv"
        
        print(f"\n📊 EXPORTING GOAL ANALYSIS")
        print("=" * 50)
        
        try:
            # Export comprehensive goal analysis
            query = """
            SELECT 
                g.goal_id,
                g.match_id,
                m.home_team,
                m.away_team,
                m.competition,
                m.match_date,
                g.exact_timestamp,
                g.added_time,
                g.total_minute,
                g.scoring_player,
                g.assisting_player,
                g.goal_type,
                g.team_side,
                g.time_interval,
                g.is_late_goal,
                g.is_very_late_goal,
                g.is_injury_time_goal,
                g.period
            FROM goal_events g
            LEFT JOIN live_matches m ON g.match_id = m.match_id
            ORDER BY g.total_minute
            """
            
            df = pd.read_sql_query(query, self.engine)
            df.to_csv(output_file, index=False)
            
            print(f"✅ Exported {len(df)} goal records to {output_file}")
            
            # Summary statistics
            late_goals = df[df['is_late_goal'] == True]
            print(f"   📈 Late goals: {len(late_goals)}/{len(df)} ({len(late_goals)/len(df)*100:.1f}%)")
            
        except Exception as e:
            print(f"❌ Error exporting goal analysis: {e}")
    
    def run_custom_query(self, query):
        """Run a custom SQL query and display results"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Convert to DataFrame for nice display
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)
                    print(df.to_string(index=False))
                else:
                    print("No results found.")
                    
        except Exception as e:
            print(f"❌ Error running query: {e}")

def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("SofaScore Database Manager")
        print("=" * 30)
        print("Usage: python database/db_manager.py <command>")
        print("\nCommands:")
        print("  status     - Show database status")
        print("  analyze    - Run goal timing analysis")
        print("  backup     - Backup database to CSV")
        print("  export     - Export goal analysis")
        print("  query      - Run custom SQL query")
        return
    
    manager = DatabaseManager()
    command = sys.argv[1].lower()
    
    if command == 'status':
        manager.get_database_status()
    
    elif command == 'analyze':
        manager.get_database_status()
        manager.analyze_goal_timing()
    
    elif command == 'backup':
        backup_dir = sys.argv[2] if len(sys.argv) > 2 else 'backups'
        manager.backup_database(backup_dir)
    
    elif command == 'export':
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        manager.export_goal_analysis(output_file)
    
    elif command == 'query':
        if len(sys.argv) < 3:
            print("Please provide a SQL query")
            return
        query = ' '.join(sys.argv[2:])
        manager.run_custom_query(query)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
EOF

chmod +x database/db_manager.py
echo "✅ Created database/db_manager.py"