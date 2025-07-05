#!/usr/bin/env python3
"""
Import existing CSV data into PostgreSQL database
"""
import sys
import os
import pandas as pd
from datetime import datetime
import glob

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVImporter:
    """Import CSV files into database"""
    
    def __init__(self):
        self.engine = engine
        self.import_stats = {
            'live_matches': 0,
            'goal_events': 0,
            'team_statistics': 0,
            'player_statistics': 0,
            'fixtures': 0,
            'errors': []
        }
    
    def find_latest_csv_files(self, export_dir='exports'):
        """Find the most recent CSV files"""
        if not os.path.exists(export_dir):
            print(f"❌ Export directory '{export_dir}' not found")
            return {}
        
        csv_files = {}
        patterns = {
            'live_match_details': 'live_match_details_*.csv',
            'live_goal_events': 'live_goal_events_*.csv',
            'live_team_statistics': 'live_team_statistics_*.csv',
            'live_player_statistics': 'live_player_statistics_*.csv',
            'fixtures_comprehensive': 'fixtures_comprehensive_*.csv',
            'historical_match_details': 'historical_match_details_*.csv',
            'historical_goal_events': 'historical_goal_events_*.csv'
        }
        
        for file_type, pattern in patterns.items():
            files = glob.glob(os.path.join(export_dir, pattern))
            if files:
                # Get the most recent file
                latest_file = max(files, key=os.path.getctime)
                csv_files[file_type] = latest_file
                print(f"📁 Found {file_type}: {os.path.basename(latest_file)}")
        
        return csv_files
    
    def clean_dataframe(self, df, table_name):
        """Clean DataFrame before database import"""
        if df.empty:
            return df
        
        # Handle NaN values
        df = df.where(pd.notnull(df), None)
        
        # Convert datetime strings
        datetime_columns = ['scraped_at', 'created_at', 'match_datetime', 'kickoff_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        if table_name == 'live_matches':
            if 'match_id' in df.columns:
                df['match_id'] = pd.to_numeric(df['match_id'], errors='coerce')
        elif table_name == 'goal_events':
            for col in ['goal_id', 'match_id', 'exact_timestamp', 'added_time']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def import_live_matches(self, csv_file):
        """Import live match details"""
        try:
            df = pd.read_csv(csv_file)
            df = self.clean_dataframe(df, 'live_matches')
            
            if df.empty:
                print("⚠️  No live match data to import")
                return
            
            # Import to database
            df.to_sql('live_matches', self.engine, if_exists='append', index=False, method='multi')
            self.import_stats['live_matches'] = len(df)
            print(f"✅ Imported {len(df)} live matches")
            
        except Exception as e:
            error_msg = f"Error importing live matches: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_goal_events(self, csv_file):
        """Import goal events"""
        try:
            df = pd.read_csv(csv_file)
            df = self.clean_dataframe(df, 'goal_events')
            
            if df.empty:
                print("⚠️  No goal events data to import")
                return
            
            # Import to database
            df.to_sql('goal_events', self.engine, if_exists='append', index=False, method='multi')
            self.import_stats['goal_events'] = len(df)
            print(f"✅ Imported {len(df)} goal events")
            
        except Exception as e:
            error_msg = f"Error importing goal events: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_team_statistics(self, csv_file):
        """Import team statistics"""
        try:
            df = pd.read_csv(csv_file)
            df = self.clean_dataframe(df, 'team_statistics')
            
            if df.empty:
                print("⚠️  No team statistics data to import")
                return
            
            df.to_sql('team_statistics', self.engine, if_exists='append', index=False, method='multi')
            self.import_stats['team_statistics'] = len(df)
            print(f"✅ Imported {len(df)} team statistics records")
            
        except Exception as e:
            error_msg = f"Error importing team statistics: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_player_statistics(self, csv_file):
        """Import player statistics"""
        try:
            df = pd.read_csv(csv_file)
            df = self.clean_dataframe(df, 'player_statistics')
            
            if df.empty:
                print("⚠️  No player statistics data to import")
                return
            
            df.to_sql('player_statistics', self.engine, if_exists='append', index=False, method='multi')
            self.import_stats['player_statistics'] = len(df)
            print(f"✅ Imported {len(df)} player statistics records")
            
        except Exception as e:
            error_msg = f"Error importing player statistics: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_fixtures(self, csv_file):
        """Import fixtures"""
        try:
            df = pd.read_csv(csv_file)
            df = self.clean_dataframe(df, 'fixtures')
            
            if df.empty:
                print("⚠️  No fixtures data to import")
                return
            
            df.to_sql('fixtures', self.engine, if_exists='append', index=False, method='multi')
            self.import_stats['fixtures'] = len(df)
            print(f"✅ Imported {len(df)} fixtures")
            
        except Exception as e:
            error_msg = f"Error importing fixtures: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def generate_goal_analysis(self):
        """Generate goal analysis summary"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT g.match_id) as total_matches,
                        COUNT(*) as total_goals,
                        COUNT(*) FILTER (WHERE g.is_late_goal = true) as late_goals,
                        ROUND(COUNT(*) FILTER (WHERE g.is_late_goal = true) * 100.0 / COUNT(*), 2) as late_goal_percentage
                    FROM goal_events g
                """))
                
                analysis = result.fetchone()
                
                if analysis and analysis[1] > 0:
                    print("✅ Generated goal analysis summary")
                    print(f"   📊 {analysis[1]} total goals across {analysis[0]} matches")
                    print(f"   🕐 {analysis[2]} late goals ({analysis[3]}%)")
                
        except Exception as e:
            error_msg = f"Error generating goal analysis: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_all_csv_files(self, export_dir='exports'):
        """Import all CSV files from exports directory"""
        print("SofaScore CSV Import Tool")
        print("=" * 50)
        
        csv_files = self.find_latest_csv_files(export_dir)
        
        if not csv_files:
            print("❌ No CSV files found to import")
            return
        
        print(f"\nFound {len(csv_files)} CSV file types to import")
        print("=" * 50)
        
        # Import in dependency order
        import_order = [
            ('live_match_details', self.import_live_matches),
            ('historical_match_details', self.import_live_matches),
            ('live_goal_events', self.import_goal_events),
            ('historical_goal_events', self.import_goal_events),
            ('live_team_statistics', self.import_team_statistics),
            ('live_player_statistics', self.import_player_statistics),
            ('fixtures_comprehensive', self.import_fixtures)
        ]
        
        for file_type, import_func in import_order:
            if file_type in csv_files:
                print(f"\n📥 Importing {file_type}...")
                import_func(csv_files[file_type])
        
        # Generate goal analysis
        print(f"\n📊 Generating goal analysis...")
        self.generate_goal_analysis()
        
        # Print summary
        print("\n" + "=" * 50)
        print("IMPORT SUMMARY")
        print("=" * 50)
        
        total_records = 0
        for table, count in self.import_stats.items():
            if table != 'errors' and count > 0:
                print(f"✅ {table}: {count} records")
                total_records += count
        
        print(f"\n�� Total records imported: {total_records}")
        
        if self.import_stats['errors']:
            print(f"\n⚠️  Errors encountered: {len(self.import_stats['errors'])}")
            for error in self.import_stats['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 All imports completed successfully!")
        
        print(f"\n🚀 Database is now ready for analysis!")

def main():
    """Main import function"""
    importer = CSVImporter()
    
    # Check if exports directory exists
    if len(sys.argv) > 1:
        export_dir = sys.argv[1]
    else:
        export_dir = 'exports'
    
    importer.import_all_csv_files(export_dir)

if __name__ == "__main__":
    main()
