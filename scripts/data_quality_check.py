#!/usr/bin/env python3
"""
Database setup script for SofaScore pipeline.
Creates database, runs migrations, and sets up initial data.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """Handle database setup and migrations."""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or settings.database.connection_string
        self.migration_dir = Path(__file__).parent.parent / "sql" / "migrations"
        
    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist."""
        try:
            # Parse database URL to get components
            db_config = settings.database
            
            # Connect to postgres database to create our target database
            temp_url = f"postgresql://{db_config.user}:{db_config.password}@{db_config.host}:{db_config.port}/postgres"
            
            logger.info("Checking if database exists...")
            
            # Use psycopg2 directly for database creation
            conn = psycopg2.connect(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
                (db_config.name,)
            )
            
            if cursor.fetchone():
                logger.info(f"Database '{db_config.name}' already exists")
            else:
                logger.info(f"Creating database '{db_config.name}'...")
                cursor.execute(f'CREATE DATABASE "{db_config.name}"')
                logger.info(f"Database '{db_config.name}' created successfully")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def get_migration_files(self) -> List[Path]:
        """Get list of migration files in order."""
        if not self.migration_dir.exists():
            logger.warning(f"Migration directory {self.migration_dir} does not exist")
            return []
        
        migration_files = sorted([
            f for f in self.migration_dir.glob("*.sql")
            if f.is_file()
        ])
        
        logger.info(f"Found {len(migration_files)} migration files")
        return migration_files
    
    def run_migration_file(self, engine: sa.Engine, migration_file: Path):
        """Run a single migration file."""
        logger.info(f"Running migration: {migration_file.name}")
        
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with engine.connect() as conn:
                for statement in statements:
                    if statement:
                        conn.execute(text(statement))
                conn.commit()
            
            logger.info(f"Migration {migration_file.name} completed successfully")
            
        except Exception as e:
            logger.error(f"Error running migration {migration_file.name}: {e}")
            raise
    
    def create_migration_log_table(self, engine: sa.Engine):
        """Create table to track migration history."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_log (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            checksum VARCHAR(64),
            success BOOLEAN DEFAULT true
        );
        """
        
        try:
            with engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
            logger.info("Migration log table created/verified")
        except Exception as e:
            logger.error(f"Error creating migration log table: {e}")
            raise
    
    def is_migration_applied(self, engine: sa.Engine, migration_name: str) -> bool:
        """Check if a migration has already been applied."""
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 1 FROM migration_log WHERE migration_name = :name AND success = true"),
                    {"name": migration_name}
                )
                return result.fetchone() is not None
        except Exception:
            # If table doesn't exist yet, migration hasn't been applied
            return False
    
    def log_migration(self, engine: sa.Engine, migration_name: str, success: bool = True):
        """Log migration execution."""
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO migration_log (migration_name, success)
                        VALUES (:name, :success)
                        ON CONFLICT (migration_name) 
                        DO UPDATE SET applied_at = CURRENT_TIMESTAMP, success = :success
                    """),
                    {"name": migration_name, "success": success}
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Could not log migration {migration_name}: {e}")
    
    def run_migrations(self):
        """Run all pending migrations."""
        try:
            # Create database engine
            engine = create_engine(self.database_url)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
            # Create migration log table
            self.create_migration_log_table(engine)
            
            # Get migration files
            migration_files = self.get_migration_files()
            
            if not migration_files:
                logger.warning("No migration files found")
                return
            
            # Run migrations
            for migration_file in migration_files:
                migration_name = migration_file.name
                
                if self.is_migration_applied(engine, migration_name):
                    logger.info(f"Migration {migration_name} already applied, skipping")
                    continue
                
                try:
                    self.run_migration_file(engine, migration_file)
                    self.log_migration(engine, migration_name, success=True)
                except Exception as e:
                    self.log_migration(engine, migration_name, success=False)
                    logger.error(f"Migration {migration_name} failed: {e}")
                    if not args.continue_on_error:
                        raise
            
            logger.info("All migrations completed successfully")
            
        except Exception as e:
            logger.error(f"Error running migrations: {e}")
            raise
    
    def create_sample_data(self):
        """Create sample data for development/testing."""
        logger.info("Creating sample data...")
        
        sample_data_sql = """
        -- Insert sample competitions
        INSERT INTO competitions (sofascore_id, name, slug, category, country, priority)
        VALUES 
            (17, 'Premier League', 'premier-league', 'domestic', 'England', 10),
            (7, 'Champions League', 'champions-league', 'international', NULL, 15),
            (23, 'Serie A', 'serie-a', 'domestic', 'Italy', 8),
            (8, 'La Liga', 'la-liga', 'domestic', 'Spain', 9),
            (35, 'Bundesliga', 'bundesliga', 'domestic', 'Germany', 8)
        ON CONFLICT (sofascore_id) DO NOTHING;
        
        -- Insert sample teams
        INSERT INTO teams (sofascore_id, name, short_name, name_code, slug, country)
        VALUES 
            (17, 'Manchester United', 'Man United', 'MUN', 'manchester-united', 'England'),
            (18, 'Manchester City', 'Man City', 'MCI', 'manchester-city', 'England'),
            (19, 'Arsenal', 'Arsenal', 'ARS', 'arsenal', 'England'),
            (20, 'Chelsea', 'Chelsea', 'CHE', 'chelsea', 'England')
        ON CONFLICT (sofascore_id) DO NOTHING;
        """
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                conn.execute(text(sample_data_sql))
                conn.commit()
            
            logger.info("Sample data created successfully")
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            raise
    
    def verify_setup(self):
        """Verify database setup is correct."""
        logger.info("Verifying database setup...")
        
        verification_queries = [
            ("Raw tables", "SELECT COUNT(*) FROM matches_raw"),
            ("Curated tables", "SELECT COUNT(*) FROM matches"),
            ("Competitions", "SELECT COUNT(*) FROM competitions"),
            ("Teams", "SELECT COUNT(*) FROM teams"),
        ]
        
        try:
            engine = create_engine(self.database_url)
            
            with engine.connect() as conn:
                for description, query in verification_queries:
                    result = conn.execute(text(query))
                    count = result.scalar()
                    logger.info(f"{description}: {count} records")
            
            logger.info("Database verification completed successfully")
            
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            raise


def main():
    """Main setup function."""
    global args
    
    parser = argparse.ArgumentParser(description="Setup SofaScore pipeline database")
    parser.add_argument("--create-db", action="store_true", help="Create database if it doesn't exist")
    parser.add_argument("--run-migrations", action="store_true", help="Run database migrations")
    parser.add_argument("--sample-data", action="store_true", help="Create sample data")
    parser.add_argument("--verify", action="store_true", help="Verify database setup")
    parser.add_argument("--all", action="store_true", help="Run all setup steps")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue if migration fails")
    parser.add_argument("--database-url", help="Database URL (overrides config)")
    
    args = parser.parse_args()
    
    if not any([args.create_db, args.run_migrations, args.sample_data, args.verify, args.all]):
        parser.print_help()
        sys.exit(1)
    
    # Initialize database setup
    db_setup = DatabaseSetup(args.database_url)
    
    try:
        if args.all or args.create_db:
            db_setup.create_database_if_not_exists()
        
        if args.all or args.run_migrations:
            db_setup.run_migrations()
        
        if args.all or args.sample_data:
            db_setup.create_sample_data()
        
        if args.all or args.verify:
            db_setup.verify_setup()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()