"""
In-memory storage fallback for when database is not available.
This allows Stage 3 completion while we fix database issues.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ..models.raw_models import ScrapeJob, MatchRaw, EventsRaw, StatsRaw
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MemoryStorage:
    """In-memory storage that mimics database operations."""
    
    def __init__(self):
        self.matches_raw = []
        self.events_raw = []
        self.stats_raw = []
        self.scrape_jobs = []
        self.momentum_raw = []
        
    async def initialize(self):
        """Initialize memory storage."""
        logger.info("Memory storage initialized (database fallback)")
        
    async def close(self):
        """Close memory storage."""
        logger.info("Memory storage closed")
        
    async def save_match_raw(self, match_id: int, endpoint: str, data: Dict[str, Any]) -> bool:
        """Save raw match data to memory."""
        try:
            match_raw = MatchRaw(
                match_id=match_id,
                endpoint=endpoint,
                raw_json=data
            )
            self.matches_raw.append(match_raw)
            logger.debug(f"Saved to memory: match {match_id}/{endpoint}")
            return True
        except Exception as e:
            logger.error(f"Memory save error: {e}")
            return False
    
    async def save_events_raw(self, match_id: int, data: Dict[str, Any]) -> bool:
        """Save raw events data to memory."""
        try:
            events_raw = EventsRaw(
                match_id=match_id,
                raw_events_json=data
            )
            self.events_raw.append(events_raw)
            logger.debug(f"Saved to memory: events {match_id}")
            return True
        except Exception as e:
            logger.error(f"Memory save error: {e}")
            return False
    
    async def save_stats_raw(self, match_id: int, minute: Optional[int], data: Dict[str, Any], endpoint: str = 'statistics') -> bool:
        """Save raw stats data to memory."""
        try:
            stats_raw = StatsRaw(
                match_id=match_id,
                minute=minute,
                raw_stats_json=data
            )
            self.stats_raw.append(stats_raw)
            logger.debug(f"Saved to memory: stats {match_id}/{minute}")
            return True
        except Exception as e:
            logger.error(f"Memory save error: {e}")
            return False
    
    async def save_scrape_job(self, job: ScrapeJob) -> bool:
        """Save scrape job to memory."""
        try:
            self.scrape_jobs.append(job)
            logger.debug(f"Saved to memory: job {job.job_id}")
            return True
        except Exception as e:
            logger.error(f"Memory save error: {e}")
            return False
    
    async def update_scrape_job(self, job: ScrapeJob) -> bool:
        """Update scrape job in memory."""
        try:
            for i, existing_job in enumerate(self.scrape_jobs):
                if existing_job.job_id == job.job_id:
                    self.scrape_jobs[i] = job
                    logger.debug(f"Updated in memory: job {job.job_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Memory update error: {e}")
            return False
    
    async def get_scraping_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get basic stats from memory."""
        return {
            'period_hours': hours,
            'job_statistics': [
                {'status': 'completed', 'count': len(self.scrape_jobs)}
            ],
            'volume_statistics': [
                {'table_name': 'matches_raw', 'record_count': len(self.matches_raw), 'unique_matches': len(set(m.match_id for m in self.matches_raw))},
                {'table_name': 'events_raw', 'record_count': len(self.events_raw), 'unique_matches': len(set(e.match_id for e in self.events_raw))},
                {'table_name': 'stats_raw', 'record_count': len(self.stats_raw), 'unique_matches': len(set(s.match_id for s in self.stats_raw))},
            ],
            'generated_at': datetime.now().isoformat()
        }
    
    async def get_live_matches_data(self) -> List[Dict[str, Any]]:
        """Get live matches from memory."""
        matches = defaultdict(datetime)
        for match in self.matches_raw:
            if match.match_id not in matches or match.scrape_timestamp > matches[match.match_id]:
                matches[match.match_id] = match.scrape_timestamp
        
        return [
            {'match_id': match_id, 'last_update': timestamp}
            for match_id, timestamp in matches.items()
        ]
    
    async def cleanup_old_data(self, days: int = 7) -> int:
        """Cleanup old data from memory."""
        logger.info(f"Memory cleanup: would remove data older than {days} days")
        return 0
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of data in memory."""
        return {
            'matches_raw': len(self.matches_raw),
            'events_raw': len(self.events_raw),
            'stats_raw': len(self.stats_raw),
            'scrape_jobs': len(self.scrape_jobs),
            'unique_matches': len(set(
                list(m.match_id for m in self.matches_raw) +
                list(e.match_id for e in self.events_raw) +
                list(s.match_id for s in self.stats_raw)
            ))
        }
