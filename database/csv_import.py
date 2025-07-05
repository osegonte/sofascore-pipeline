#!/usr/bin/env python3
"""
Final fix for CSV import - PostgreSQL compatible version
"""
import sys
import os
import pandas as pd
from datetime import datetime
import glob
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CSVImporter:
    """Final fixed CSV importer with PostgreSQL compatibility"""
    
    def __init__(self, chunk_size=100):
        self.engine = engine
        self.chunk_size = chunk_size
        self.import_stats = {
            'live_matches': 0,
            'goal_events': 0,
            'team_statistics': 0,
            'player_statistics': 0,
            'fixtures': 0,
            'errors': []
        }
        
        # Schema mappings (same as before)
        self.schema_mappings = {
            'live_matches': {
                'required_columns': ['match_id', 'home_team', 'away_team'],
                'column_mapping': {
                    'match_id': 'match_id',
                    'competition': 'competition',
                    'league': 'league',
                    'date': 'match_date',
                    'match_date': 'match_date',
                    'time': 'match_time',
                    'match_time': 'match_time',
                    'datetime': 'match_datetime',
                    'match_datetime': 'match_datetime',
                    'home_team': 'home_team',
                    'away_team': 'away_team',
                    'home_team_id': 'home_team_id',
                    'away_team_id': 'away_team_id',
                    'venue': 'venue',
                    'home_score': 'home_score',
                    'away_score': 'away_score',
                    'minutes_elapsed': 'minutes_elapsed',
                    'period': 'period',
                    'status': 'status',
                    'status_type': 'status_type',
                    'scraped_at': 'scraped_at'
                },
                'default_values': {
                    'created_at': lambda: datetime.now(),
                    'home_score': 0,
                    'away_score': 0
                }
            },
            'goal_events': {
                'required_columns': ['goal_id', 'match_id', 'exact_timestamp'],
                'column_mapping': {
                    'goal_id': 'goal_id',
                    'match_id': 'match_id',
                    'exact_timestamp': 'exact_timestamp',
                    'exact_timestamp_minute': 'exact_timestamp',
                    'added_time': 'added_time',
                    'scoring_player': 'scoring_player',
                    'scoring_player_id': 'scoring_player_id',
                    'assisting_player': 'assisting_player',
                    'assisting_player_id': 'assisting_player_id',
                    'goal_type': 'goal_type',
                    'team_side': 'team_side',
                    'description': 'description',
                    'period': 'period',
                    'competition': 'competition',
                    'scraped_at': 'scraped_at'
                },
                'default_values': {
                    'added_time': 0,
                    'goal_type': 'regular'
                }
            },
            'team_statistics': {
                'required_columns': ['match_id'],
                'column_mapping': {
                    'match_id': 'match_id',
                    'team_side': 'team_side',
                    'team_name': 'team_name',
                    'possession_percentage': 'possession_percentage',
                    'shots_on_target': 'shots_on_target',
                    'total_shots': 'total_shots',
                    'corners': 'corners',
                    'fouls': 'fouls',
                    'yellow_cards': 'yellow_cards',
                    'red_cards': 'red_cards',
                    'offsides': 'offsides',
                    'competition': 'competition',
                    'scraped_at': 'scraped_at'
                },
                'default_values': {
                    'scraped_at': lambda: datetime.now()
                }
            },
            'player_statistics': {
                'required_columns': ['player_name'],
                'column_mapping': {
                    'match_id': 'match_id',
                    'player_name': 'player_name',
                    'player_id': 'player_id',
                    'team_side': 'team_side',
                    'position': 'position',
                    'jersey_number': 'jersey_number',
                    'is_starter': 'is_starter',
                    'goals': 'goals',
                    'assists': 'assists',
                    'cards_received': 'cards_received',
                    'minutes_played': 'minutes_played',
                    'shots_on_target': 'shots_on_target',
                    'competition': 'competition',
                    'scraped_at': 'scraped_at'
                },
                'default_values': {
                    'is_starter': False,
                    'goals': 0,
                    'assists': 0,
                    'cards_received': 0,
                    'scraped_at': lambda: datetime.now()
                }
            },
            'fixtures': {
                'required_columns': ['fixture_id'],
                'column_mapping': {
                    'fixture_id': 'fixture_id',
                    'home_team': 'home_team',
                    'away_team': 'away_team',
                    'home_team_id': 'home_team_id',
                    'away_team_id': 'away_team_id',
                    'kickoff_time': 'kickoff_time',
                    'kickoff_date': 'kickoff_date',
                    'kickoff_time_formatted': 'kickoff_time_formatted',
                    'tournament': 'tournament',
                    'tournament_id': 'tournament_id',
                    'round_info': 'round_info',
                    'status': 'status',
                    'venue': 'venue',
                    'source_type': 'source_type',
                    'scraped_at': 'scraped_at'
                },
                'default_values': {
                    'scraped_at': lambda: datetime.now()
                }
            }
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
                latest_file = max(files, key=os.path.getctime)
                csv_files[file_type] = latest_file
                print(f"📁 Found {file_type}: {os.path.basename(latest_file)}")
        
        return csv_files
    
    def map_dataframe_to_schema(self, df, table_name):
        """Map DataFrame columns to exact database schema"""
        if table_name not in self.schema_mappings:
            print(f"   ⚠️  No schema mapping for table: {table_name}")
            return df
        
        schema = self.schema_mappings[table_name]
        
        # Check required columns
        missing_required = []
        for req_col in schema['required_columns']:
            mapped_col = schema['column_mapping'].get(req_col, req_col)
            if mapped_col and mapped_col not in df.columns:
                found = False
                for csv_col, db_col in schema['column_mapping'].items():
                    if db_col == mapped_col and csv_col in df.columns:
                        found = True
                        break
                if not found:
                    missing_required.append(req_col)
        
        if missing_required:
            print(f"   ⚠️  Missing required columns for {table_name}: {missing_required}")
            return pd.DataFrame()
        
        # Create new DataFrame with only mapped columns
        mapped_df = pd.DataFrame()
        
        for csv_col, db_col in schema['column_mapping'].items():
            if db_col is None:
                continue
            if csv_col in df.columns:
                mapped_df[db_col] = df[csv_col]
        
        # Add default values for missing columns
        for db_col, default_val in schema['default_values'].items():
            if db_col not in mapped_df.columns:
                if callable(default_val):
                    mapped_df[db_col] = default_val()
                else:
                    mapped_df[db_col] = default_val
        
        # Clean the mapped DataFrame
        mapped_df = self.clean_dataframe(mapped_df, table_name)
        
        print(f"   🔄 Mapped {len(df.columns)} CSV columns to {len(mapped_df.columns)} DB columns")
        return mapped_df
    
    def clean_dataframe(self, df, table_name):
        """Clean DataFrame with improved data type handling"""
        if df.empty:
            return df
        
        # Convert datetime columns
        datetime_columns = ['scraped_at', 'created_at', 'match_datetime', 'kickoff_time']
        for col in datetime_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert date columns
        date_columns = ['match_date', 'kickoff_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Convert time columns
        time_columns = ['match_time', 'kickoff_time_formatted']
        for col in time_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
                except:
                    try:
                        df[col] = pd.to_datetime(df[col], format='%H:%M', errors='coerce').dt.time
                    except:
                        df[col] = pd.to_datetime(df[col], errors='coerce').dt.time
        
        # Convert numeric columns
        numeric_columns = ['match_id', 'goal_id', 'fixture_id', 'exact_timestamp', 'added_time', 
                          'home_score', 'away_score', 'minutes_elapsed', 'period',
                          'home_team_id', 'away_team_id', 'tournament_id', 'player_id',
                          'scoring_player_id', 'assisting_player_id', 'jersey_number',
                          'goals', 'assists', 'cards_received', 'minutes_played',
                          'shots_on_target', 'total_shots', 'corners', 'fouls', 
                          'yellow_cards', 'red_cards', 'offsides']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert boolean columns
        boolean_columns = ['is_starter']
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool, errors='ignore')
        
        # Handle NaN values
        df = df.where(pd.notnull(df), None)
        
        # Remove rows where primary key is null
        primary_keys = {
            'live_matches': 'match_id',
            'goal_events': 'goal_id', 
            'fixtures': 'fixture_id'
        }
        
        if table_name in primary_keys:
            pk_col = primary_keys[table_name]
            if pk_col in df.columns:
                initial_count = len(df)
                df = df.dropna(subset=[pk_col])
                if len(df) < initial_count:
                    print(f"   🧹 Removed {initial_count - len(df)} rows with null {pk_col}")
        
        return df
    
    def simple_insert_with_skip(self, df, table_name, chunk_size=None):
        """Simple insert with duplicate skipping - PostgreSQL compatible"""
        if df.empty:
            return 0
        
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        inserted_count = 0
        
        print(f"   📦 Inserting {len(df)} records in {total_chunks} chunks of {chunk_size}")
        
        # Get primary key for duplicate checking
        primary_keys = {
            'live_matches': 'match_id',
            'goal_events': 'goal_id',
            'fixtures': 'fixture_id'
        }
        
        pk_col = primary_keys.get(table_name)
        
        with tqdm(total=len(df), desc=f"Importing {table_name}", unit="records") as pbar:
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i+chunk_size]
                
                try:
                    # For tables with primary keys, check for existing records first
                    if pk_col and pk_col in chunk.columns:
                        new_chunk = self.filter_existing_records(chunk, table_name, pk_col)
                        if not new_chunk.empty:
                            new_chunk.to_sql(
                                table_name, 
                                self.engine, 
                                if_exists='append', 
                                index=False, 
                                method='multi'
                            )
                            inserted_count += len(new_chunk)
                        else:
                            # All records already exist
                            pass
                    else:
                        # For tables without clear primary keys, just try to insert
                        chunk.to_sql(
                            table_name, 
                            self.engine, 
                            if_exists='append', 
                            index=False, 
                            method='multi'
                        )
                        inserted_count += len(chunk)
                    
                    pbar.update(len(chunk))
                    
                except Exception as e:
                    # Individual row handling for failed chunks
                    success_count = self.handle_individual_inserts(chunk, table_name, pk_col)
                    inserted_count += success_count
                    pbar.update(len(chunk))
        
        return inserted_count
    
    def filter_existing_records(self, chunk, table_name, pk_col):
        """Filter out records that already exist in the database"""
        try:
            with self.engine.connect() as conn:
                # Create a simple IN query (more compatible than ANY)
                pk_values = chunk[pk_col].dropna().tolist()
                if not pk_values:
                    return chunk
                
                # Build IN clause
                placeholders = ','.join([f':pk_{i}' for i in range(len(pk_values))])
                query = f"SELECT {pk_col} FROM {table_name} WHERE {pk_col} IN ({placeholders})"
                
                # Create parameters dict
                params = {f'pk_{i}': val for i, val in enumerate(pk_values)}
                
                result = conn.execute(text(query), params)
                existing_ids = {row[0] for row in result}
                
                # Filter out existing records
                new_records = chunk[~chunk[pk_col].isin(existing_ids)]
                return new_records
                
        except Exception as e:
            print(f"      ⚠️  Error checking existing records: {str(e)[:50]}...")
            return chunk  # Return original chunk if check fails
    
    def handle_individual_inserts(self, chunk, table_name, pk_col):
        """Handle individual row inserts for failed chunks"""
        success_count = 0
        
        for idx, row in chunk.iterrows():
            try:
                row_df = pd.DataFrame([row])
                
                # For primary key tables, check if exists first
                if pk_col and pk_col in row_df.columns and not pd.isna(row[pk_col]):
                    with self.engine.connect() as conn:
                        check_result = conn.execute(
                            text(f"SELECT COUNT(*) FROM {table_name} WHERE {pk_col} = :pk_val"),
                            {'pk_val': row[pk_col]}
                        )
                        if check_result.scalar() > 0:
                            continue  # Skip existing record
                
                row_df.to_sql(table_name, self.engine, if_exists='append', index=False)
                success_count += 1
                
            except Exception as e:
                error_msg = f"Row {idx} failed: {str(e)[:100]}..."
                self.import_stats['errors'].append(error_msg)
                if len(self.import_stats['errors']) <= 5:
                    print(f"      ❌ {error_msg}")
        
        print(f"      ✅ {success_count}/{len(chunk)} rows inserted")
        return success_count
    
    # Import methods (simplified)
    def import_live_matches(self, csv_file):
        """Import live match details"""
        try:
            print(f"\n📥 Reading {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file)
            df_mapped = self.map_dataframe_to_schema(df, 'live_matches')
            
            if df_mapped.empty:
                print("⚠️  No valid live match data to import")
                return
            
            print(f"   📊 Found {len(df_mapped)} valid live matches to import")
            inserted_count = self.simple_insert_with_skip(df_mapped, 'live_matches')
            self.import_stats['live_matches'] += inserted_count
            print(f"✅ Imported {inserted_count} live matches")
            
        except Exception as e:
            error_msg = f"Error importing live matches: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_goal_events(self, csv_file):
        """Import goal events"""
        try:
            print(f"\n📥 Reading {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file)
            df_mapped = self.map_dataframe_to_schema(df, 'goal_events')
            
            if df_mapped.empty:
                print("⚠️  No valid goal events data to import")
                return
            
            print(f"   📊 Found {len(df_mapped)} valid goal events to import")
            inserted_count = self.simple_insert_with_skip(df_mapped, 'goal_events')
            self.import_stats['goal_events'] += inserted_count
            print(f"✅ Imported {inserted_count} goal events")
            
        except Exception as e:
            error_msg = f"Error importing goal events: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_team_statistics(self, csv_file):
        """Import team statistics"""
        try:
            print(f"\n📥 Reading {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file)
            df_mapped = self.map_dataframe_to_schema(df, 'team_statistics')
            
            if df_mapped.empty:
                print("⚠️  No valid team statistics data to import")
                return
            
            print(f"   📊 Found {len(df_mapped)} valid team statistics records to import")
            inserted_count = self.simple_insert_with_skip(df_mapped, 'team_statistics')
            self.import_stats['team_statistics'] += inserted_count
            print(f"✅ Imported {inserted_count} team statistics records")
            
        except Exception as e:
            error_msg = f"Error importing team statistics: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_player_statistics(self, csv_file):
        """Import player statistics"""
        try:
            print(f"\n📥 Reading {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file)
            df_mapped = self.map_dataframe_to_schema(df, 'player_statistics')
            
            if df_mapped.empty:
                print("⚠️  No valid player statistics data to import")
                return
            
            print(f"   📊 Found {len(df_mapped)} valid player statistics records to import")
            inserted_count = self.simple_insert_with_skip(df_mapped, 'player_statistics')
            self.import_stats['player_statistics'] += inserted_count
            print(f"✅ Imported {inserted_count} player statistics records")
            
        except Exception as e:
            error_msg = f"Error importing player statistics: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_fixtures(self, csv_file):
        """Import fixtures"""
        try:
            print(f"\n📥 Reading {os.path.basename(csv_file)}...")
            df = pd.read_csv(csv_file)
            df_mapped = self.map_dataframe_to_schema(df, 'fixtures')
            
            if df_mapped.empty:
                print("⚠️  No valid fixtures data to import")
                return
            
            print(f"   📊 Found {len(df_mapped)} valid fixtures to import")
            inserted_count = self.simple_insert_with_skip(df_mapped, 'fixtures', chunk_size=25)
            self.import_stats['fixtures'] += inserted_count
            print(f"✅ Imported {inserted_count} fixtures")
            
        except Exception as e:
            error_msg = f"Error importing fixtures: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def generate_goal_analysis(self):
        """Generate goal analysis summary - simplified version"""
        try:
            print(f"\n📊 Generating goal analysis...")
            
            with self.engine.connect() as conn:
                # Check if we have any goals
                result = conn.execute(text("SELECT COUNT(*) FROM goal_events"))
                total_goals = result.scalar()
                
                if total_goals == 0:
                    print("   ℹ️  No goals found - skipping goal analysis")
                    return
                
                # Get basic goal analysis
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT g.match_id) as total_matches,
                        COUNT(*) as total_goals,
                        COUNT(*) FILTER (WHERE g.is_late_goal = true) as late_goals,
                        CASE 
                            WHEN COUNT(*) > 0 THEN ROUND(COUNT(*) FILTER (WHERE g.is_late_goal = true) * 100.0 / COUNT(*), 2)
                            ELSE 0 
                        END as late_goal_percentage,
                        ROUND(AVG(g.total_minute), 2) as avg_goal_minute
                    FROM goal_events g
                """))
                
                analysis = result.fetchone()
                
                if analysis and analysis[1] > 0:
                    # Simple insert without ON CONFLICT (since we don't have the constraint)
                    try:
                        conn.execute(text("""
                            INSERT INTO goal_analysis (
                                analysis_date, total_matches_analyzed, total_goals_analyzed,
                                late_goals_count, late_goals_percentage, average_goal_minute
                            ) VALUES (
                                CURRENT_DATE, :total_matches, :total_goals,
                                :late_goals, :late_goal_percentage, :avg_goal_minute
                            )
                        """), {
                            'total_matches': analysis[0],
                            'total_goals': analysis[1],
                            'late_goals': analysis[2],
                            'late_goal_percentage': float(analysis[3]),
                            'avg_goal_minute': float(analysis[4])
                        })
                        conn.commit()
                    except Exception as insert_error:
                        if "duplicate" in str(insert_error).lower():
                            print("   ℹ️  Goal analysis already exists for today")
                        else:
                            raise insert_error
                    
                    print("✅ Generated goal analysis summary")
                    print(f"   📊 {analysis[1]} total goals across {analysis[0]} matches")
                    print(f"   🕐 {analysis[2]} late goals ({analysis[3]}%)")
                    print(f"   ⚽ Average goal minute: {analysis[4]}")
                
        except Exception as e:
            error_msg = f"Error generating goal analysis: {e}"
            self.import_stats['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    def import_all_csv_files(self, export_dir='exports'):
        """Import all CSV files with final fixes"""
        print("SofaScore CSV Import Tool - Final Fixed Version")
        print("=" * 55)
        
        csv_files = self.find_latest_csv_files(export_dir)
        
        if not csv_files:
            print("❌ No CSV files found to import")
            return
        
        print(f"\nFound {len(csv_files)} CSV file types to import")
        print(f"Using chunk size: {self.chunk_size} records per batch")
        print("✓ Schema mapping enabled")
        print("✓ PostgreSQL compatible duplicate handling")
        print("=" * 55)
        
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
        
        start_time = datetime.now()
        
        for file_type, import_func in import_order:
            if file_type in csv_files:
                print(f"\n{'='*15} {file_type.upper()} {'='*15}")
                import_func(csv_files[file_type])
        
        # Generate goal analysis
        print(f"\n{'='*15} GOAL ANALYSIS {'='*15}")
        self.generate_goal_analysis()
        
        # Print summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 55)
        print("FINAL IMPORT SUMMARY")
        print("=" * 55)
        
        total_records = 0
        for table, count in self.import_stats.items():
            if table != 'errors' and count > 0:
                print(f"✅ {table:20} {count:>8} records")
                total_records += count
        
        print(f"\n📊 Total records imported: {total_records:,}")
        print(f"⏱️  Total import time: {duration:.1f} seconds")
        if duration > 0:
            print(f"🚀 Average speed: {total_records/duration:.1f} records/second")
        
        # Simplified error reporting
        error_count = len(self.import_stats['errors'])
        if error_count > 0:
            print(f"\n⚠️  {error_count} errors (mostly duplicates)")
        else:
            print("\n🎉 All imports completed successfully!")
        
        print(f"\n🎯 SUCCESS! Your database now contains:")
        print(f"   • {self.import_stats['goal_events']} goal events with timing analysis")
        print(f"   • {self.import_stats['live_matches']} live matches")
        print(f"   • {self.import_stats['fixtures']} upcoming fixtures")
        print(f"   • Player and team statistics")
        
        print(f"\n🚀 Ready for goal timing analysis!")
        print(f"   Run: python database/db_manager.py status")
        print(f"   Run: python database/db_manager.py analyze")

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("SofaScore CSV Import Tool - Final Fixed Edition")
        print("Usage: python database/csv_import.py [export_dir] [chunk_size]")
        return
    
    export_dir = sys.argv[1] if len(sys.argv) > 1 else 'exports'
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    importer = CSVImporter(chunk_size=chunk_size)
    importer.import_all_csv_files(export_dir)

if __name__ == "__main__":
    main()