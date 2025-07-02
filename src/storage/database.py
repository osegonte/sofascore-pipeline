"""
Simplified database manager using asyncpg for Python 3.13 compatibility.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

import asyncpg
from asyncpg import Pool

from ..models.raw_models import (
    ScrapeJob, MatchRaw, EventsRaw, StatsRaw, MomentumRaw,
    RawDataValidator, RawDataSanitizer
)
from ..utils.logging import get_logger
from config.simple_settings import settings

logger = get_logger(__name__)


class DatabaseManager:
    """Manages database operations using asyncpg."""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or settings.database.connection_string
        self.pool: Optional[Pool] = None
        
    async def initialize(self):
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            logger.info("Database connection pool established")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
        logger.info("Database connections closed")
    
    async def save_match_raw(self, match_id: int, endpoint: str, data: Dict[str, Any]) -> bool:
        """Save raw match data."""
        try:
            match_raw = MatchRaw(
                match_id=match_id,
                endpoint=endpoint,
                raw_json=data
            )
            
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO matches_raw (
                        id, match_id, scrape_timestamp, endpoint, raw_json,
                        http_status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await conn.execute(
                    query,
                    match_raw.id, match_raw.match_id, match_raw.scrape_timestamp,
                    match_raw.endpoint, json.dumps(match_raw.raw_json),
                    match_raw.http_status, match_raw.created_at, match_raw.updated_at
                )
            
            logger.debug(f"Saved match raw data: {match_id}/{endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving match raw data {match_id}/{endpoint}: {e}")
            return False
    
    async def save_events_raw(self, match_id: int, data: Dict[str, Any]) -> bool:
        """Save raw events data."""
        try:
            events_raw = EventsRaw(
                match_id=match_id,
                raw_events_json=data
            )
            
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO events_raw (
                        id, match_id, scrape_timestamp, raw_events_json,
                        event_count, http_status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await conn.execute(
                    query,
                    events_raw.id, events_raw.match_id, events_raw.scrape_timestamp,
                    json.dumps(events_raw.raw_events_json), events_raw.event_count,
                    events_raw.http_status, events_raw.created_at, events_raw.updated_at
                )
            
            logger.debug(f"Saved events raw data: {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving events raw data {match_id}: {e}")
            return False
    
    async def save_stats_raw(self, match_id: int, minute: Optional[int], data: Dict[str, Any], endpoint: str = 'statistics') -> bool:
        """Save raw statistics data."""
        try:
            stats_raw = StatsRaw(
                match_id=match_id,
                minute=minute,
                raw_stats_json=data
            )
            
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO stats_raw (
                        id, match_id, minute, scrape_timestamp, raw_stats_json,
                        http_status, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """
                
                await conn.execute(
                    query,
                    stats_raw.id, stats_raw.match_id, stats_raw.minute,
                    stats_raw.scrape_timestamp, json.dumps(stats_raw.raw_stats_json),
                    stats_raw.http_status, stats_raw.created_at, stats_raw.updated_at
                )
            
            logger.debug(f"Saved stats raw data: {match_id}/{minute}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving stats raw data {match_id}/{minute}: {e}")
            return False
    
    async def save_scrape_job(self, job: ScrapeJob) -> bool:
        """Save a scrape job to the database."""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    INSERT INTO scrape_jobs (
                        id, job_id, match_id, job_type, status, started_at,
                        total_requests, successful_requests, failed_requests,
                        created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (job_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        total_requests = EXCLUDED.total_requests,
                        successful_requests = EXCLUDED.successful_requests,
                        failed_requests = EXCLUDED.failed_requests,
                        updated_at = EXCLUDED.updated_at
                """
                
                await conn.execute(
                    query,
                    job.id, job.job_id, job.match_id, job.job_type, job.status,
                    job.started_at, job.total_requests, job.successful_requests,
                    job.failed_requests, job.created_at, job.updated_at
                )
            
            logger.debug(f"Saved scrape job: {job.job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving scrape job {job.job_id}: {e}")
            return False
    
    async def update_scrape_job(self, job: ScrapeJob) -> bool:
        """Update an existing scrape job."""
        try:
            job.updated_at = datetime.now()
            
            async with self.pool.acquire() as conn:
                query = """
                    UPDATE scrape_jobs SET
                        status = $1,
                        completed_at = $2,
                        total_requests = $3,
                        successful_requests = $4,
                        failed_requests = $5,
                        updated_at = $6
                    WHERE job_id = $7
                """
                
                await conn.execute(
                    query,
                    job.status, job.completed_at, job.total_requests,
                    job.successful_requests, job.failed_requests,
                    job.updated_at, job.job_id
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating scrape job {job.job_id}: {e}")
            return False
    
    async def get_scraping_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get basic scraping statistics."""
        try:
            return {
                'period_hours': hours,
                'job_statistics': [],
                'volume_statistics': [],
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting scraping stats: {e}")
            return {}
    
    async def get_live_matches_data(self) -> List[Dict[str, Any]]:
        """Get data for currently live matches."""
        try:
            async with self.pool.acquire() as conn:
                query = """
                    SELECT DISTINCT match_id, MAX(scrape_timestamp) as last_update
                    FROM matches_raw
                    WHERE scrape_timestamp >= NOW() - INTERVAL '2 hours'
                    GROUP BY match_id
                    ORDER BY last_update DESC
                """
                
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting live matches data: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 7) -> int:
        """Clean up old raw data."""
        logger.info(f"Would cleanup data older than {days} days")
        return 0


# Global database manager instance
db_manager = DatabaseManager()
