"""
Hybrid database manager that tries PostgreSQL first, falls back to memory.
"""

import asyncio
from typing import Dict, List, Any, Optional

from .memory_storage import MemoryStorage
from ..utils.logging import get_logger

logger = get_logger(__name__)


class HybridDatabaseManager:
    """Database manager that falls back to memory storage."""
    
    def __init__(self):
        self.memory_storage = MemoryStorage()
        self.using_memory = True
        
    async def initialize(self):
        """Initialize storage (memory fallback)."""
        try:
            # Try PostgreSQL first (would fail)
            from .database import DatabaseManager as PostgresManager
            self.postgres = PostgresManager()
            await self.postgres.initialize()
            self.using_memory = False
            logger.info("Using PostgreSQL database")
        except Exception as e:
            logger.warning(f"PostgreSQL unavailable ({e}), using memory storage")
            await self.memory_storage.initialize()
            self.using_memory = True
    
    async def close(self):
        """Close storage."""
        if self.using_memory:
            await self.memory_storage.close()
        else:
            await self.postgres.close()
    
    async def save_match_raw(self, match_id: int, endpoint: str, data: Dict[str, Any]) -> bool:
        """Save raw match data."""
        if self.using_memory:
            return await self.memory_storage.save_match_raw(match_id, endpoint, data)
        else:
            return await self.postgres.save_match_raw(match_id, endpoint, data)
    
    async def save_events_raw(self, match_id: int, data: Dict[str, Any]) -> bool:
        """Save raw events data."""
        if self.using_memory:
            return await self.memory_storage.save_events_raw(match_id, data)
        else:
            return await self.postgres.save_events_raw(match_id, data)
    
    async def save_stats_raw(self, match_id: int, minute: Optional[int], data: Dict[str, Any], endpoint: str = 'statistics') -> bool:
        """Save raw stats data."""
        if self.using_memory:
            return await self.memory_storage.save_stats_raw(match_id, minute, data, endpoint)
        else:
            return await self.postgres.save_stats_raw(match_id, minute, data, endpoint)
    
    async def save_scrape_job(self, job) -> bool:
        """Save scrape job."""
        if self.using_memory:
            return await self.memory_storage.save_scrape_job(job)
        else:
            return await self.postgres.save_scrape_job(job)
    
    async def update_scrape_job(self, job) -> bool:
        """Update scrape job."""
        if self.using_memory:
            return await self.memory_storage.update_scrape_job(job)
        else:
            return await self.postgres.update_scrape_job(job)
    
    async def get_scraping_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get scraping statistics."""
        if self.using_memory:
            return await self.memory_storage.get_scraping_stats(hours)
        else:
            return await self.postgres.get_scraping_stats(hours)
    
    async def get_live_matches_data(self) -> List[Dict[str, Any]]:
        """Get live matches data."""
        if self.using_memory:
            return await self.memory_storage.get_live_matches_data()
        else:
            return await self.postgres.get_live_matches_data()
    
    async def cleanup_old_data(self, days: int = 7) -> int:
        """Clean up old data."""
        if self.using_memory:
            return await self.memory_storage.cleanup_old_data(days)
        else:
            return await self.postgres.cleanup_old_data(days)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage."""
        if self.using_memory:
            summary = self.memory_storage.get_summary()
            return {
                'type': 'memory',
                'status': 'active',
                'data_summary': summary
            }
        else:
            return {
                'type': 'postgresql', 
                'status': 'active'
            }
