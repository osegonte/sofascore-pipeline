"""
Database manager for storing and retrieving scraped data.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging

import asyncpg
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..models.raw_models import (
    ScrapeJob, MatchRaw, EventsRaw, StatsRaw, MomentumRaw, ProcessingLog,
    RawDataValidator, RawDataSanitizer
)
from ..utils.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database operations for raw data storage."""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or settings.database.connection_string
        self.engine = None
        self.async_engine = None
        self.session_maker = None
        self._pool = None
        
    async def initialize(self):
        """Initialize database connections."""
        try:
            # Create async engine for high-performance operations
            self.async_engine = create_async_engine(
                self.connection_string.replace('postgresql://', 'postgresql+asyncpg://'),
                echo=settings.debug,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            # Create session maker
            self.session_maker = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("Database connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
        logger.info("Database connections closed")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # Scrape Job Operations
    async def save_scrape_job(self, job: ScrapeJob) -> bool:
        """Save a scrape job to the database."""
        try:
            # Validate data
            errors = RawDataValidator.validate_scrape_job(job)
            if errors:
                logger.error(f"Invalid scrape job data: {errors}")
                return False
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    INSERT INTO scrape_jobs (
                        id, job_id, match_id, job_type, status, started_at,
                        completed_at, total_requests, successful_requests,
                        failed_requests, error_details, created_at, updated_at
                    ) VALUES (
                        :id, :job_id, :match_id, :job_type, :status, :started_at,
                        :completed_at, :total_requests, :successful_requests,
                        :failed_requests, :error_details, :created_at, :updated_at
                    )
                    ON CONFLICT (job_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        completed_at = EXCLUDED.completed_at,
                        total_requests = EXCLUDED.total_requests,
                        successful_requests = EXCLUDED.successful_requests,
                        failed_requests = EXCLUDED.failed_requests,
                        error_details = EXCLUDED.error_details,
                        updated_at = EXCLUDED.updated_at
                """)
                
                job_data = job.to_dict()
                await conn.execute(query, job_data)
            
            logger.debug(f"Saved scrape job: {job.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scrape job {job.job_id}: {e}")
            return False
    
    async def update_scrape_job(self, job: ScrapeJob) -> bool:
        """Update an existing scrape job."""
        try:
            job.updated_at = datetime.now()
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    UPDATE scrape_jobs SET
                        status = :status,
                        completed_at = :completed_at,
                        total_requests = :total_requests,
                        successful_requests = :successful_requests,
                        failed_requests = :failed_requests,
                        error_details = :error_details,
                        updated_at = :updated_at
                    WHERE job_id = :job_id
                """)
                
                result = await conn.execute(query, {
                    'status': job.status,
                    'completed_at': job.completed_at,
                    'total_requests': job.total_requests,
                    'successful_requests': job.successful_requests,
                    'failed_requests': job.failed_requests,
                    'error_details': json.dumps(job.error_details) if job.error_details else None,
                    'updated_at': job.updated_at,
                    'job_id': job.job_id
                })
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating scrape job {job.job_id}: {e}")
            return False
    
    async def get_scrape_job(self, job_id: str) -> Optional[ScrapeJob]:
        """Get a scrape job by ID."""
        try:
            async with self.async_engine.begin() as conn:
                query = text("SELECT * FROM scrape_jobs WHERE job_id = :job_id")
                result = await conn.execute(query, {'job_id': job_id})
                row = result.fetchone()
                
                if row:
                    return ScrapeJob(**dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Error getting scrape job {job_id}: {e}")
            return None
    
    # Raw Match Data Operations
    async def save_match_raw(self, match_id: int, endpoint: str, data: Dict[str, Any]) -> bool:
        """Save raw match data."""
        try:
            # Sanitize data
            sanitized_data = RawDataSanitizer.sanitize_json_data(data)
            sanitized_data = RawDataSanitizer.remove_sensitive_data(sanitized_data)
            
            match_raw = MatchRaw(
                match_id=match_id,
                endpoint=endpoint,
                raw_json=sanitized_data
            )
            
            # Validate
            errors = RawDataValidator.validate_match_raw(match_raw)
            if errors:
                logger.error(f"Invalid match raw data: {errors}")
                return False
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    INSERT INTO matches_raw (
                        id, match_id, scrape_timestamp, endpoint, raw_json,
                        http_status, scrape_duration_ms, error_message,
                        created_at, updated_at
                    ) VALUES (
                        :id, :match_id, :scrape_timestamp, :endpoint, :raw_json,
                        :http_status, :scrape_duration_ms, :error_message,
                        :created_at, :updated_at
                    )
                """)
                
                await conn.execute(query, match_raw.to_dict())
            
            logger.debug(f"Saved match raw data: {match_id}/{endpoint}")
            return True
            
        except IntegrityError:
            # Duplicate entry, which is fine for raw data
            logger.debug(f"Duplicate match raw data: {match_id}/{endpoint}")
            return True
        except Exception as e:
            logger.error(f"Error saving match raw data {match_id}/{endpoint}: {e}")
            return False
    
    async def save_events_raw(self, match_id: int, data: Dict[str, Any]) -> bool:
        """Save raw events data."""
        try:
            # Sanitize data
            sanitized_data = RawDataSanitizer.sanitize_json_data(data)
            sanitized_data = RawDataSanitizer.remove_sensitive_data(sanitized_data)
            
            events_raw = EventsRaw(
                match_id=match_id,
                raw_events_json=sanitized_data
            )
            
            # Validate
            errors = RawDataValidator.validate_events_raw(events_raw)
            if errors:
                logger.error(f"Invalid events raw data: {errors}")
                return False
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    INSERT INTO events_raw (
                        id, match_id, scrape_timestamp, raw_events_json,
                        event_count, http_status, scrape_duration_ms,
                        error_message, created_at, updated_at
                    ) VALUES (
                        :id, :match_id, :scrape_timestamp, :raw_events_json,
                        :event_count, :http_status, :scrape_duration_ms,
                        :error_message, :created_at, :updated_at
                    )
                """)
                
                await conn.execute(query, events_raw.to_dict())
            
            logger.debug(f"Saved events raw data: {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving events raw data {match_id}: {e}")
            return False
    
    async def save_stats_raw(
        self, 
        match_id: int, 
        minute: Optional[int], 
        data: Dict[str, Any],
        endpoint: str = 'statistics'
    ) -> bool:
        """Save raw statistics data."""
        try:
            # Sanitize data
            sanitized_data = RawDataSanitizer.sanitize_json_data(data)
            sanitized_data = RawDataSanitizer.remove_sensitive_data(sanitized_data)
            
            stats_raw = StatsRaw(
                match_id=match_id,
                minute=minute,
                raw_stats_json=sanitized_data
            )
            
            # Validate
            errors = RawDataValidator.validate_stats_raw(stats_raw)
            if errors:
                logger.error(f"Invalid stats raw data: {errors}")
                return False
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    INSERT INTO stats_raw (
                        id, match_id, minute, scrape_timestamp, raw_stats_json,
                        http_status, scrape_duration_ms, error_message,
                        created_at, updated_at
                    ) VALUES (
                        :id, :match_id, :minute, :scrape_timestamp, :raw_stats_json,
                        :http_status, :scrape_duration_ms, :error_message,
                        :created_at, :updated_at
                    )
                """)
                
                await conn.execute(query, stats_raw.to_dict())
            
            logger.debug(f"Saved stats raw data: {match_id}/{minute}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving stats raw data {match_id}/{minute}: {e}")
            return False
    
    async def save_momentum_raw(self, match_id: int, data: Dict[str, Any]) -> bool:
        """Save raw momentum data."""
        try:
            # Sanitize data
            sanitized_data = RawDataSanitizer.sanitize_json_data(data)
            sanitized_data = RawDataSanitizer.remove_sensitive_data(sanitized_data)
            
            momentum_raw = MomentumRaw(
                match_id=match_id,
                raw_momentum_json=sanitized_data
            )
            
            async with self.async_engine.begin() as conn:
                query = text("""
                    INSERT INTO momentum_raw (
                        id, match_id, scrape_timestamp, raw_momentum_json,
                        data_points_count, http_status, scrape_duration_ms,
                        error_message, created_at, updated_at
                    ) VALUES (
                        :id, :match_id, :scrape_timestamp, :raw_momentum_json,
                        :data_points_count, :http_status, :scrape_duration_ms,
                        :error_message, :created_at, :updated_at
                    )
                """)
                
                await conn.execute(query, momentum_raw.to_dict())
            
            logger.debug(f"Saved momentum raw data: {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving momentum raw data {match_id}: {e}")
            return False
    
    # Data Retrieval Operations
    async def get_recent_raw_data(
        self, 
        table_name: str, 
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent raw data from specified table."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            async with self.async_engine.begin() as conn:
                query = text(f"""
                    SELECT * FROM {table_name}
                    WHERE created_at >= :since
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)
                
                result = await conn.execute(query, {'since': since})
                return [dict(row) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting recent raw data from {table_name}: {e}")
            return []
    
    async def get_live_matches_data(self) -> List[Dict[str, Any]]:
        """Get data for currently live matches."""
        try:
            async with self.async_engine.begin() as conn:
                query = text("""
                    SELECT DISTINCT match_id, MAX(scrape_timestamp) as last_update
                    FROM matches_raw
                    WHERE scrape_timestamp >= NOW() - INTERVAL '2 hours'
                    GROUP BY match_id
                    ORDER BY last_update DESC
                """)
                
                result = await conn.execute(query)
                return [dict(row) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting live matches data: {e}")
            return []
    
    async def get_match_raw_data(
        self, 
        match_id: int, 
        endpoint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all raw data for a specific match."""
        try:
            async with self.async_engine.begin() as conn:
                if endpoint:
                    query = text("""
                        SELECT * FROM matches_raw
                        WHERE match_id = :match_id AND endpoint = :endpoint
                        ORDER BY scrape_timestamp DESC
                    """)
                    params = {'match_id': match_id, 'endpoint': endpoint}
                else:
                    query = text("""
                        SELECT * FROM matches_raw
                        WHERE match_id = :match_id
                        ORDER BY scrape_timestamp DESC
                    """)
                    params = {'match_id': match_id}
                
                result = await conn.execute(query, params)
                return [dict(row) for row in result.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting match raw data {match_id}: {e}")
            return []
    
    # Statistics and Monitoring
    async def get_scraping_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get scraping statistics for the last N hours."""
        try:
            since = datetime.now() - timedelta(hours=hours)
            
            async with self.async_engine.begin() as conn:
                # Get job statistics
                job_stats_query = text("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration,
                        SUM(successful_requests) as total_successful,
                        SUM(failed_requests) as total_failed
                    FROM scrape_jobs
                    WHERE started_at >= :since
                    GROUP BY status
                """)
                
                job_result = await conn.execute(job_stats_query, {'since': since})
                job_stats = [dict(row) for row in job_result.fetchall()]
                
                # Get data volume statistics
                volume_query = text("""
                    SELECT 
                        'matches_raw' as table_name,
                        COUNT(*) as record_count,
                        COUNT(DISTINCT match_id) as unique_matches
                    FROM matches_raw
                    WHERE created_at >= :since
                    UNION ALL
                    SELECT 
                        'events_raw' as table_name,
                        COUNT(*) as record_count,
                        COUNT(DISTINCT match_id) as unique_matches
                    FROM events_raw
                    WHERE created_at >= :since
                    UNION ALL
                    SELECT 
                        'stats_raw' as table_name,
                        COUNT(*) as record_count,
                        COUNT(DISTINCT match_id) as unique_matches
                    FROM stats_raw
                    WHERE created_at >= :since
                """)
                
                volume_result = await conn.execute(volume_query, {'since': since})
                volume_stats = [dict(row) for row in volume_result.fetchall()]
                
                return {
                    'period_hours': hours,
                    'job_statistics': job_stats,
                    'volume_statistics': volume_stats,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting scraping stats: {e}")
            return {}
    
    async def cleanup_old_data(self, days: int = 7) -> int:
        """Clean up old raw data to save space."""
        try:
            cutoff = datetime.now() - timedelta(days=days)
            total_deleted = 0
            
            tables = ['matches_raw', 'events_raw', 'stats_raw', 'momentum_raw']
            
            async with self.async_engine.begin() as conn:
                for table in tables:
                    query = text(f"""
                        DELETE FROM {table}
                        WHERE created_at < :cutoff
                    """)
                    
                    result = await conn.execute(query, {'cutoff': cutoff})
                    deleted = result.rowcount
                    total_deleted += deleted
                    
                    logger.info(f"Deleted {deleted} old records from {table}")
            
            logger.info(f"Cleanup completed: {total_deleted} total records deleted")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0


# Global database manager instance
db_manager = DatabaseManager()