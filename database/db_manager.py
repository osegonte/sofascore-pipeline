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
        
        except Exception as e:
            print(f"❌ Error in goal timing analysis: {e}")
    
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
                g.exact_timestamp,
                g.added_time,
                g.total_minute,
                g.scoring_player,
                g.team_side,
                g.time_interval,
                g.is_late_goal,
                g.is_very_late_goal,
                g.is_injury_time_goal
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

def main():
    """Main function with command line interface"""
    if len(sys.argv) < 2:
        print("SofaScore Database Manager")
        print("=" * 30)
        print("Usage: python database/db_manager.py <command>")
        print("\nCommands:")
        print("  status     - Show database status")
        print("  analyze    - Run goal timing analysis")
        print("  export     - Export goal analysis")
        return
    
    manager = DatabaseManager()
    command = sys.argv[1].lower()
    
    if command == 'status':
        manager.get_database_status()
    
    elif command == 'analyze':
        manager.get_database_status()
        manager.analyze_goal_timing()
    
    elif command == 'export':
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        manager.export_goal_analysis(output_file)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
