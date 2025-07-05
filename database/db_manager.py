#!/usr/bin/env python3
"""
Database management utilities for SofaScore pipeline
Enhanced with better error handling and division by zero protection
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
        """Get comprehensive database status with error handling"""
        print("SofaScore Database Status")
        print("=" * 50)
        
        try:
            with self.engine.connect() as conn:
                # Table counts with error handling
                tables = ['live_matches', 'goal_events', 'team_statistics', 
                         'player_statistics', 'fixtures', 'goal_analysis']
                
                print("📊 TABLE STATISTICS:")
                total_records = 0
                table_stats = {}
                
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        count = result.scalar()
                        total_records += count
                        table_stats[table] = count
                        print(f"   {table:20} {count:>8} records")
                    except Exception as e:
                        print(f"   {table:20} {'ERROR':>8} - {str(e)[:50]}...")
                        table_stats[table] = 0
                
                print(f"   {'TOTAL':20} {total_records:>8} records")
                
                # Goal analysis summary with division by zero protection
                if table_stats.get('goal_events', 0) > 0:
                    print("\n🎯 GOAL ANALYSIS SUMMARY:")
                    try:
                        result = conn.execute(text("""
                            SELECT 
                                COUNT(*) as total_goals,
                                COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                                CASE 
                                    WHEN COUNT(*) > 0 THEN ROUND(COUNT(*) FILTER (WHERE is_late_goal = true) * 100.0 / COUNT(*), 1)
                                    ELSE 0 
                                END as late_goal_percentage,
                                COUNT(DISTINCT match_id) as matches_with_goals,
                                CASE 
                                    WHEN COUNT(DISTINCT match_id) > 0 THEN ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT match_id), 1)
                                    ELSE 0 
                                END as avg_goals_per_match
                            FROM goal_events
                        """))
                        
                        row = result.fetchone()
                        if row:
                            print(f"   Total goals: {row[0]}")
                            print(f"   Late goals (75+ min): {row[1]} ({row[2]}%)")
                            print(f"   Matches with goals: {row[3]}")
                            print(f"   Average goals per match: {row[4]}")
                    except Exception as e:
                        print(f"   ❌ Error in goal analysis: {e}")
                else:
                    print("\n🎯 GOAL ANALYSIS: No goals found yet")
                
                # Recent activity with error handling
                print("\n📅 RECENT ACTIVITY:")
                self._show_recent_activity(conn, table_stats)
                
                # Data quality checks
                print("\n🔍 DATA QUALITY:")
                self._show_data_quality(conn, table_stats)
                
        except Exception as e:
            print(f"❌ Error getting database status: {e}")
    
    def _show_recent_activity(self, conn, table_stats):
        """Show recent activity with error handling"""
        activity_queries = {
            'Live Matches': "SELECT COUNT(*), MAX(scraped_at) FROM live_matches WHERE scraped_at > NOW() - INTERVAL '24 hours'",
            'Goal Events': "SELECT COUNT(*), MAX(scraped_at) FROM goal_events WHERE scraped_at > NOW() - INTERVAL '24 hours'",
            'Fixtures': "SELECT COUNT(*), MAX(scraped_at) FROM fixtures WHERE scraped_at > NOW() - INTERVAL '24 hours'"
        }
        
        for activity_type, query in activity_queries.items():
            try:
                result = conn.execute(text(query))
                row = result.fetchone()
                if row and row[0] > 0:
                    latest_str = row[1].strftime('%Y-%m-%d %H:%M') if row[1] else 'N/A'
                    print(f"   {activity_type:15} {row[0]:>3} records (latest: {latest_str})")
            except Exception as e:
                print(f"   {activity_type:15} ERROR - {str(e)[:30]}...")
    
    def _show_data_quality(self, conn, table_stats):
        """Show data quality metrics"""
        try:
            # Check for matches with goals
            if table_stats.get('live_matches', 0) > 0 and table_stats.get('goal_events', 0) > 0:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT m.match_id) as total_matches,
                        COUNT(DISTINCT g.match_id) as matches_with_goals,
                        CASE 
                            WHEN COUNT(DISTINCT m.match_id) > 0 
                            THEN ROUND(COUNT(DISTINCT g.match_id) * 100.0 / COUNT(DISTINCT m.match_id), 1)
                            ELSE 0 
                        END as percentage_with_goals
                    FROM live_matches m
                    LEFT JOIN goal_events g ON m.match_id = g.match_id
                """))
                row = result.fetchone()
                if row:
                    print(f"   Matches with goals: {row[1]}/{row[0]} ({row[2]}%)")
            
            # Check for upcoming fixtures
            if table_stats.get('fixtures', 0) > 0:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM fixtures 
                    WHERE kickoff_date >= CURRENT_DATE 
                    AND kickoff_date <= CURRENT_DATE + INTERVAL '7 days'
                """))
                upcoming = result.scalar()
                print(f"   Upcoming fixtures (7 days): {upcoming}")
            
            # Check for data completeness
            if table_stats.get('goal_events', 0) > 0:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_goals,
                        COUNT(scoring_player) as goals_with_player,
                        COUNT(team_side) as goals_with_team_side
                    FROM goal_events
                """))
                row = result.fetchone()
                if row and row[0] > 0:
                    player_pct = (row[1] / row[0]) * 100 if row[0] > 0 else 0
                    team_pct = (row[2] / row[0]) * 100 if row[0] > 0 else 0
                    print(f"   Goal data completeness: {player_pct:.1f}% have player, {team_pct:.1f}% have team")
        
        except Exception as e:
            print(f"   ❌ Error in data quality check: {e}")
    
    def get_table_count(self, table_name):
        """Get count of records in a table with error handling"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except Exception as e:
            print(f"Error getting count for {table_name}: {e}")
            return 0
    
    def analyze_goal_timing(self):
        """Detailed goal timing analysis with division by zero protection"""
        print("\n🕐 DETAILED GOAL TIMING ANALYSIS")
        print("=" * 50)
        
        # First check if we have any goals
        goal_count = self.get_table_count('goal_events')
        if goal_count == 0:
            print("   ℹ️  No goals found for analysis")
            return
        
        try:
            with self.engine.connect() as conn:
                # Goal distribution by time interval with error handling
                print("Goal Distribution by 15-minute intervals:")
                result = conn.execute(text("""
                    SELECT 
                        time_interval,
                        COUNT(*) as goals,
                        CASE 
                            WHEN SUM(COUNT(*)) OVER () > 0 
                            THEN ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)
                            ELSE 0 
                        END as percentage
                    FROM goal_events 
                    WHERE time_interval IS NOT NULL
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
                
                total_analyzed = 0
                for row in result:
                    bar = "█" * max(1, int(row[2] / 2))  # Visual bar chart (min 1 char)
                    print(f"   {row[0]:>6} min: {row[1]:>3} goals ({row[2]:>4.1f}%) {bar}")
                    total_analyzed += row[1]
                
                if total_analyzed == 0:
                    print("   ⚠️  No goals with valid time intervals found")
                    return
                
                # Late goals by competition with protection
                print(f"\nLate Goal Analysis (from {total_analyzed} total goals):")
                result = conn.execute(text("""
                    SELECT 
                        COALESCE(competition, 'Unknown') as competition,
                        COUNT(*) as total_goals,
                        COUNT(*) FILTER (WHERE is_late_goal = true) as late_goals,
                        CASE 
                            WHEN COUNT(*) > 0 
                            THEN ROUND(COUNT(*) FILTER (WHERE is_late_goal = true) * 100.0 / COUNT(*), 1)
                            ELSE 0 
                        END as late_goal_percentage
                    FROM goal_events 
                    GROUP BY competition
                    HAVING COUNT(*) >= 3
                    ORDER BY late_goal_percentage DESC, total_goals DESC
                    LIMIT 10
                """))
                
                competitions_found = False
                for row in result:
                    if not competitions_found:
                        print("Late Goal Percentage by Competition (3+ goals):")
                        competitions_found = True
                    comp_name = row[0][:25] + "..." if len(row[0]) > 25 else row[0]
                    print(f"   {comp_name:30} {row[2]:>2}/{row[1]:>2} goals ({row[3]:>4.1f}%)")
                
                if not competitions_found:
                    print("   ℹ️  No competitions with 3+ goals found")
                
                # Advanced timing statistics
                print(f"\nAdvanced Timing Statistics:")
                result = conn.execute(text("""
                    SELECT 
                        ROUND(AVG(total_minute), 1) as avg_minute,
                        ROUND(STDDEV(total_minute), 1) as stddev_minute,
                        MIN(total_minute) as earliest_goal,
                        MAX(total_minute) as latest_goal,
                        COUNT(*) FILTER (WHERE is_very_late_goal = true) as very_late_goals,
                        COUNT(*) FILTER (WHERE is_injury_time_goal = true) as injury_time_goals
                    FROM goal_events
                    WHERE total_minute IS NOT NULL
                """))
                
                row = result.fetchone()
                if row:
                    print(f"   Average goal minute: {row[0] or 'N/A'}")
                    print(f"   Standard deviation: {row[1] or 'N/A'}")
                    print(f"   Earliest goal: {row[2] or 'N/A'} min")
                    print(f"   Latest goal: {row[3] or 'N/A'} min")
                    print(f"   Very late goals (85+ min): {row[4] or 0}")
                    print(f"   Injury time goals: {row[5] or 0}")
        
        except Exception as e:
            print(f"❌ Error in goal timing analysis: {e}")
    
    def backup_database(self, backup_dir='backups'):
        """Export database to CSV backup with progress tracking"""
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"\n💾 BACKING UP DATABASE")
        print("=" * 50)
        
        tables = ['live_matches', 'goal_events', 'team_statistics', 
                 'player_statistics', 'fixtures', 'goal_analysis']
        
        backed_up = 0
        total_records = 0
        
        for table in tables:
            try:
                print(f"   📦 Backing up {table}...")
                df = pd.read_sql_table(table, self.engine)
                if not df.empty:
                    filename = f"{backup_dir}/{table}_backup_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    print(f"   ✅ {table}: {len(df)} records -> {filename}")
                    backed_up += 1
                    total_records += len(df)
                else:
                    print(f"   ⚠️  {table}: No data to backup")
            except Exception as e:
                print(f"   ❌ Error backing up {table}: {e}")
        
        print(f"\n📁 Backup completed: {backed_up}/{len(tables)} tables")
        print(f"📊 Total records backed up: {total_records:,}")
    
    def export_goal_analysis(self, output_file=None):
        """Export goal analysis to CSV for external analysis"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"goal_analysis_export_{timestamp}.csv"
        
        print(f"\n📊 EXPORTING GOAL ANALYSIS")
        print("=" * 50)
        
        # Check if we have goals first
        goal_count = self.get_table_count('goal_events')
        if goal_count == 0:
            print("   ℹ️  No goals found to export")
            return
        
        try:
            # Export comprehensive goal analysis with error handling
            query = """
            SELECT 
                g.goal_id,
                g.match_id,
                COALESCE(m.home_team, 'Unknown') as home_team,
                COALESCE(m.away_team, 'Unknown') as away_team,
                COALESCE(m.competition, g.competition, 'Unknown') as competition,
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
            
            # Summary statistics with protection
            if not df.empty:
                late_goals = df[df['is_late_goal'] == True] if 'is_late_goal' in df.columns else pd.DataFrame()
                late_pct = (len(late_goals) / len(df) * 100) if len(df) > 0 else 0
                print(f"   📈 Late goals: {len(late_goals)}/{len(df)} ({late_pct:.1f}%)")
                
                if 'total_minute' in df.columns:
                    avg_minute = df['total_minute'].mean()
                    print(f"   ⏱️  Average goal minute: {avg_minute:.1f}")
            
        except Exception as e:
            print(f"❌ Error exporting goal analysis: {e}")
    
    def run_custom_query(self, query):
        """Run a custom SQL query and display results with error handling"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                
                # Convert to DataFrame for nice display
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    df = pd.DataFrame(rows, columns=columns)
                    print(df.to_string(index=False, max_rows=50))
                    if len(df) > 50:
                        print(f"\n... ({len(df)} total rows, showing first 50)")
                else:
                    print("No results found.")
                    
        except Exception as e:
            print(f"❌ Error running query: {e}")
            print(f"   Query: {query[:100]}...")
    
    def optimize_database(self):
        """Run database optimization tasks"""
        print("\n🔧 DATABASE OPTIMIZATION")
        print("=" * 50)
        
        try:
            with self.engine.connect() as conn:
                # Update table statistics
                print("   📊 Updating table statistics...")
                conn.execute(text("ANALYZE"))
                
                # Check for missing indexes
                print("   🔍 Checking index usage...")
                result = conn.execute(text("""
                    SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_tup_read DESC
                    LIMIT 10
                """))
                
                print("   Top 10 most used indexes:")
                for row in result:
                    print(f"     {row[0]}.{row[1]}.{row[2]}: {row[3]} reads, {row[4]} fetches")
                
                print("   ✅ Optimization completed")
                
        except Exception as e:
            print(f"❌ Error during optimization: {e}")

def main():
    """Main function with enhanced command line interface"""
    if len(sys.argv) < 2:
        print("SofaScore Database Manager - Enhanced Edition")
        print("=" * 45)
        print("Usage: python database/db_manager.py <command> [options]")
        print("\nCommands:")
        print("  status     - Show comprehensive database status")
        print("  analyze    - Run detailed goal timing analysis")
        print("  backup     - Backup database to CSV files")
        print("  export     - Export goal analysis to CSV")
        print("  query      - Run custom SQL query")
        print("  optimize   - Run database optimization")
        print("\nOptions:")
        print("  backup [dir]     - Specify backup directory")
        print("  export [file]    - Specify output file")
        print("  query \"SELECT...\" - SQL query in quotes")
        return
    
    manager = DatabaseManager()
    command = sys.argv[1].lower()
    
    try:
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
                print("Please provide a SQL query in quotes")
                return
            query = ' '.join(sys.argv[2:])
            manager.run_custom_query(query)
        
        elif command == 'optimize':
            manager.optimize_database()
        
        else:
            print(f"Unknown command: {command}")
            print("Use --help for available commands")
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Command failed: {e}")

if __name__ == "__main__":
    main()