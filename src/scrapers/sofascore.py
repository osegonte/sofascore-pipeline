"""
SofaScore API scraper for live match data collection.
Handles all live matches across all competitions.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
from asyncio_throttle import Throttler
import redis

from ..utils.logging import get_logger
from ..storage.hybrid_database import HybridDatabaseManager as DatabaseManager
from ..models.raw_models import ScrapeJob, MatchRaw, EventsRaw, StatsRaw
from config.simple_settings import settings

logger = get_logger(__name__)


@dataclass
class MatchInfo:
    """Basic match information for tracking."""
    match_id: int
    status: str
    current_minute: int
    home_team: str
    away_team: str
    competition: str
    is_live: bool
    importance: int


class SofaScoreAPI:
    """SofaScore API client with rate limiting and error handling."""
    
    def __init__(self):
        self.base_url = settings.sofascore.base_url
        self.session: Optional[ClientSession] = None
        self.throttler = Throttler(
            rate_limit=settings.sofascore.rate_limit_requests,
            period=settings.sofascore.rate_limit_period
        )
        
        # Redis for caching and deduplication
        try:
            self.redis_client = redis.from_url(settings.redis.url)
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.redis_client = None
        
        # Request headers
        self.headers = {
            'User-Agent': settings.sofascore.user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sofascore.com/',
            'Origin': 'https://www.sofascore.com'
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        timeout = ClientTimeout(total=settings.sofascore.timeout)
        self.session = ClientSession(
            timeout=timeout,
            headers=self.headers,
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, url: str, cache_key: Optional[str] = None) -> Optional[Dict]:
        """Make rate-limited HTTP request with caching."""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # Check cache first
        if cache_key and self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
        
        # Rate limiting
        async with self.throttler:
            start_time = time.time()
            
            try:
                async with self.session.get(url) as response:
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Cache successful response
                        if cache_key and self.redis_client:
                            try:
                                self.redis_client.setex(
                                    cache_key, 
                                    300,  # 5 minutes cache
                                    json.dumps(data)
                                )
                            except Exception as e:
                                logger.warning(f"Cache write error: {e}")
                        
                        return data
                    
                    elif response.status == 429:
                        logger.warning(f"Rate limited on {url}")
                        await asyncio.sleep(30)  # Wait 30 seconds
                        return None
                    
                    else:
                        logger.error(f"HTTP {response.status} for {url}")
                        return None
            
            except ClientError as e:
                logger.error(f"Request error for {url}: {e}")
                return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout for {url}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                return None
    
    async def get_live_matches(self) -> List[MatchInfo]:
        """Get all currently live matches."""
        url = f"{self.base_url}/sport/football/events/live"
        cache_key = "sofascore:live_matches"
        
        data = await self._make_request(url, cache_key)
        if not data or 'events' not in data:
            return []
        
        matches = []
        for event in data['events']:
            try:
                match_info = MatchInfo(
                    match_id=event['id'],
                    status=event['status']['description'],
                    current_minute=event.get('time', {}).get('currentPeriodStartTimestamp', 0),
                    home_team=event['homeTeam']['name'],
                    away_team=event['awayTeam']['name'],
                    competition=event['tournament']['name'],
                    is_live=event['status']['code'] in [1, 2],  # Live statuses
                    importance=event.get('customId', 1)
                )
                matches.append(match_info)
            except KeyError as e:
                logger.warning(f"Incomplete match data: {e}")
                continue
        
        logger.info(f"Found {len(matches)} live matches")
        return matches
    
    async def get_todays_matches(self) -> List[MatchInfo]:
        """Get all matches for today (including finished and upcoming)."""
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{self.base_url}/sport/football/scheduled-events/{today}"
        cache_key = f"sofascore:matches:{today}"
        
        data = await self._make_request(url, cache_key)
        if not data or 'events' not in data:
            return []
        
        matches = []
        for event in data['events']:
            try:
                match_info = MatchInfo(
                    match_id=event['id'],
                    status=event['status']['description'],
                    current_minute=event.get('time', {}).get('currentPeriodStartTimestamp', 0),
                    home_team=event['homeTeam']['name'],
                    away_team=event['awayTeam']['name'],
                    competition=event['tournament']['name'],
                    is_live=event['status']['code'] in [1, 2],
                    importance=event.get('customId', 1)
                )
                matches.append(match_info)
            except KeyError as e:
                logger.warning(f"Incomplete match data: {e}")
                continue
        
        logger.info(f"Found {len(matches)} matches for {today}")
        return matches
    
    async def get_match_feed(self, match_id: int) -> Optional[Dict]:
        """Get match metadata and basic info."""
        url = f"{self.base_url}/event/{match_id}"
        return await self._make_request(url)
    
    async def get_match_events(self, match_id: int) -> Optional[Dict]:
        """Get match events (goals, cards, subs)."""
        url = f"{self.base_url}/event/{match_id}/incidents"
        return await self._make_request(url)
    
    async def get_match_statistics(self, match_id: int) -> Optional[Dict]:
        """Get match statistics."""
        url = f"{self.base_url}/event/{match_id}/statistics"
        return await self._make_request(url)
    
    async def get_match_lineups(self, match_id: int) -> Optional[Dict]:
        """Get match lineups."""
        url = f"{self.base_url}/event/{match_id}/lineups"
        return await self._make_request(url)
    
    async def get_momentum_data(self, match_id: int) -> Optional[Dict]:
        """Get momentum/attack data if available."""
        url = f"{self.base_url}/event/{match_id}/graph"
        return await self._make_request(url)


class LiveMatchTracker:
    """Tracks and scrapes all live matches continuously."""
    
    def __init__(self):
        self.api = SofaScoreAPI()
        self.db_manager = DatabaseManager()
        self.tracked_matches: Set[int] = set()
        self.last_discovery = datetime.min
        self.discovery_interval = timedelta(minutes=2)  # Discover new matches every 2 minutes
        self.scrape_interval = timedelta(seconds=60)  # Scrape live matches every minute
        
    async def discover_matches(self) -> List[MatchInfo]:
        """Discover all available live matches."""
        now = datetime.now()
        
        if now - self.last_discovery < self.discovery_interval:
            return []
        
        logger.info("Discovering live matches...")
        
        async with self.api:
            # Get both live and today's matches to catch recently started ones
            live_matches = await self.api.get_live_matches()
            todays_matches = await self.api.get_todays_matches()
            
            # Combine and deduplicate
            all_matches = {match.match_id: match for match in live_matches + todays_matches}
            
            # Filter for live or recently finished matches
            relevant_matches = []
            for match in all_matches.values():
                if (match.is_live or 
                    match.status in ['finished', 'ended'] or
                    'live' in match.status.lower()):
                    relevant_matches.append(match)
            
            self.last_discovery = now
            logger.info(f"Discovered {len(relevant_matches)} relevant matches")
            return relevant_matches
    
    async def scrape_match_data(self, match_id: int) -> bool:
        """Scrape all data for a single match."""
        logger.debug(f"Scraping match {match_id}")
        
        start_time = time.time()
        success = True
        
        async with self.api:
            # Create scrape job record
            job = ScrapeJob(
                job_id=f"live_scrape_{match_id}_{int(time.time())}",
                match_id=match_id,
                job_type='live',
                status='running'
            )
            
            try:
                # Save job to database
                await self.db_manager.save_scrape_job(job)
                
                # Scrape all endpoints concurrently
                tasks = [
                    self._scrape_endpoint(match_id, 'feed', self.api.get_match_feed),
                    self._scrape_endpoint(match_id, 'events', self.api.get_match_events),
                    self._scrape_endpoint(match_id, 'statistics', self.api.get_match_statistics),
                    self._scrape_endpoint(match_id, 'lineups', self.api.get_match_lineups),
                    self._scrape_endpoint(match_id, 'momentum', self.api.get_momentum_data),
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Count successful requests
                successful = sum(1 for r in results if r is True)
                failed = len(results) - successful
                
                # Update job status
                job.status = 'completed' if failed == 0 else 'partial'
                job.successful_requests = successful
                job.failed_requests = failed
                job.completed_at = datetime.now()
                
                await self.db_manager.update_scrape_job(job)
                
                logger.debug(f"Match {match_id}: {successful} successful, {failed} failed requests")
                
            except Exception as e:
                logger.error(f"Error scraping match {match_id}: {e}")
                job.status = 'failed'
                job.error_details = {'error': str(e)}
                job.completed_at = datetime.now()
                await self.db_manager.update_scrape_job(job)
                success = False
        
        duration = time.time() - start_time
        logger.debug(f"Match {match_id} scraped in {duration:.2f}s")
        return success
    
    async def _scrape_endpoint(self, match_id: int, endpoint: str, scrape_func) -> bool:
        """Scrape a specific endpoint and save to database."""
        try:
            data = await scrape_func(match_id)
            
            if data:
                if endpoint == 'feed':
                    await self.db_manager.save_match_raw(match_id, endpoint, data)
                elif endpoint == 'events':
                    await self.db_manager.save_events_raw(match_id, data)
                elif endpoint in ['statistics', 'lineups', 'momentum']:
                    await self.db_manager.save_stats_raw(match_id, None, data, endpoint)
                
                return True
            else:
                logger.warning(f"No data for match {match_id} endpoint {endpoint}")
                return False
                
        except Exception as e:
            logger.error(f"Error scraping {endpoint} for match {match_id}: {e}")
            return False
    
    async def run_continuous_tracking(self):
        """Main loop for continuous live match tracking."""
        logger.info("Starting continuous live match tracking...")
        
        while True:
            try:
                # Discover new matches
                discovered_matches = await self.discover_matches()
                
                # Add new matches to tracking
                for match in discovered_matches:
                    if match.match_id not in self.tracked_matches:
                        self.tracked_matches.add(match.match_id)
                        logger.info(f"Now tracking: {match.home_team} vs {match.away_team} ({match.competition})")
                
                # Scrape all tracked matches
                if self.tracked_matches:
                    logger.info(f"Scraping {len(self.tracked_matches)} tracked matches...")
                    
                    # Limit concurrent requests to avoid overwhelming the API
                    semaphore = asyncio.Semaphore(settings.pipeline.max_concurrent_requests)
                    
                    async def scrape_with_semaphore(match_id):
                        async with semaphore:
                            return await self.scrape_match_data(match_id)
                    
                    # Execute scraping tasks
                    tasks = [scrape_with_semaphore(match_id) for match_id in self.tracked_matches]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    successful = sum(1 for r in results if r is True)
                    logger.info(f"Scraping completed: {successful}/{len(results)} matches successful")
                
                # Clean up finished matches periodically
                await self._cleanup_finished_matches()
                
                # Wait before next iteration
                await asyncio.sleep(self.scrape_interval.total_seconds())
                
            except KeyboardInterrupt:
                logger.info("Shutting down live match tracker...")
                break
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _cleanup_finished_matches(self):
        """Remove finished matches from tracking after some time."""
        # Remove matches that finished more than 2 hours ago
        # This logic would need match status checking - simplified for now
        
        if len(self.tracked_matches) > 50:  # Simple cleanup when too many matches
            # Keep only the most recent matches
            sorted_matches = sorted(self.tracked_matches)
            self.tracked_matches = set(sorted_matches[-30:])  # Keep last 30
            logger.info(f"Cleaned up tracking list, now tracking {len(self.tracked_matches)} matches")


async def main():
    """Main function for testing the scraper."""
    tracker = LiveMatchTracker()
    await tracker.run_continuous_tracking()


if __name__ == "__main__":
    asyncio.run(main())