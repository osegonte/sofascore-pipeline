"""
Utility functions and helpers for web scraping operations.
"""

import re
import json
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, parse_qs
import logging

import redis
from ..utils.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class EndpointDiscovery:
    """Discover and map SofaScore API endpoints."""
    
    # Known endpoint patterns
    ENDPOINT_PATTERNS = {
        'live_matches': '/sport/football/events/live',
        'daily_matches': '/sport/football/scheduled-events/{date}',
        'match_feed': '/event/{match_id}',
        'match_events': '/event/{match_id}/incidents',
        'match_statistics': '/event/{match_id}/statistics',
        'match_lineups': '/event/{match_id}/lineups',
        'match_momentum': '/event/{match_id}/graph',
        'match_h2h': '/event/{match_id}/h2h',
        'match_odds': '/event/{match_id}/odds',
        'team_info': '/team/{team_id}',
        'player_info': '/player/{player_id}',
        'tournament_info': '/tournament/{tournament_id}',
        'tournament_standings': '/tournament/{tournament_id}/season/{season_id}/standings',
        'search': '/search/{query}',
    }
    
    @classmethod
    def get_endpoint_url(cls, base_url: str, endpoint_type: str, **kwargs) -> str:
        """Get full URL for an endpoint type."""
        if endpoint_type not in cls.ENDPOINT_PATTERNS:
            raise ValueError(f"Unknown endpoint type: {endpoint_type}")
        
        pattern = cls.ENDPOINT_PATTERNS[endpoint_type]
        
        try:
            # Replace placeholders with actual values
            endpoint = pattern.format(**kwargs)
            return urljoin(base_url, endpoint)
        except KeyError as e:
            raise ValueError(f"Missing parameter {e} for endpoint {endpoint_type}")
    
    @classmethod
    def discover_match_endpoints(cls, match_id: int) -> Dict[str, str]:
        """Get all available endpoints for a match."""
        base_url = settings.sofascore.base_url
        
        endpoints = {}
        match_endpoints = [
            'match_feed', 'match_events', 'match_statistics', 
            'match_lineups', 'match_momentum', 'match_h2h', 'match_odds'
        ]
        
        for endpoint_type in match_endpoints:
            try:
                url = cls.get_endpoint_url(base_url, endpoint_type, match_id=match_id)
                endpoints[endpoint_type] = url
            except ValueError:
                continue
        
        return endpoints
    
    @classmethod
    def validate_response_structure(cls, data: Dict, endpoint_type: str) -> bool:
        """Validate if response data has expected structure."""
        validation_rules = {
            'live_matches': lambda d: 'events' in d and isinstance(d['events'], list),
            'match_feed': lambda d: 'event' in d or 'id' in d,
            'match_events': lambda d: 'incidents' in d and isinstance(d['incidents'], list),
            'match_statistics': lambda d: 'statistics' in d and isinstance(d['statistics'], list),
            'match_lineups': lambda d: ('home' in d and 'away' in d) or 'lineups' in d,
            'match_momentum': lambda d: 'graphPoints' in d or 'graph' in d,
        }
        
        validator = validation_rules.get(endpoint_type)
        if validator:
            try:
                return validator(data)
            except (KeyError, TypeError):
                return False
        
        # If no specific validation rule, just check if it's a dict
        return isinstance(data, dict) and len(data) > 0


class DataCache:
    """Redis-based caching for scraped data."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(settings.redis.url)
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis not available for caching: {e}")
                self.redis_client = None
    
    def _get_cache_key(self, prefix: str, identifier: str, suffix: str = "") -> str:
        """Generate cache key."""
        key = f"sofascore:{prefix}:{identifier}"
        if suffix:
            key += f":{suffix}"
        return key
    
    def _get_ttl_for_data_type(self, data_type: str) -> int:
        """Get TTL based on data type."""
        ttls = {
            'live_matches': 30,        # 30 seconds for live match discovery
            'match_feed': 60,          # 1 minute for basic match info
            'match_events': 30,        # 30 seconds for live events
            'match_statistics': 60,    # 1 minute for statistics
            'match_lineups': 3600,     # 1 hour for lineups (rarely change)
            'daily_matches': 300,      # 5 minutes for daily schedule
            'team_info': 86400,        # 24 hours for team info
            'player_info': 86400,      # 24 hours for player info
        }
        return ttls.get(data_type, 300)  # Default 5 minutes
    
    async def get(self, data_type: str, identifier: str, suffix: str = "") -> Optional[Dict]:
        """Get cached data."""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_cache_key(data_type, identifier, suffix)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def set(self, data_type: str, identifier: str, data: Dict, suffix: str = ""):
        """Set cached data."""
        if not self.redis_client:
            return
        
        try:
            key = self._get_cache_key(data_type, identifier, suffix)
            ttl = self._get_ttl_for_data_type(data_type)
            
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    async def invalidate(self, data_type: str, identifier: str = "*"):
        """Invalidate cached data."""
        if not self.redis_client:
            return
        
        try:
            pattern = self._get_cache_key(data_type, identifier)
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} cache entries for {data_type}:{identifier}")
        except Exception as e:
            logger.warning(f"Cache invalidation error: {e}")


class DataDeduplicator:
    """Detect and handle duplicate data."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(settings.redis.url)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
    
    def _calculate_hash(self, data: Dict) -> str:
        """Calculate hash of data for deduplication."""
        # Remove timestamp fields that change frequently
        cleaned_data = self._clean_data_for_hash(data)
        data_str = json.dumps(cleaned_data, sort_keys=True, default=str)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _clean_data_for_hash(self, data: Dict) -> Dict:
        """Remove fields that change frequently but don't indicate new data."""
        fields_to_remove = [
            'timestamp', 'lastUpdated', 'scrapeTime', 'requestTime',
            'serverTime', 'responseTime', 'cacheTime'
        ]
        
        cleaned = data.copy()
        for field in fields_to_remove:
            cleaned.pop(field, None)
        
        return cleaned
    
    async def is_duplicate(self, data_type: str, identifier: str, data: Dict) -> bool:
        """Check if data is duplicate of previously seen data."""
        if not self.redis_client:
            return False
        
        try:
            current_hash = self._calculate_hash(data)
            key = f"sofascore:hash:{data_type}:{identifier}"
            
            stored_hash = self.redis_client.get(key)
            
            if stored_hash and stored_hash.decode() == current_hash:
                return True
            
            # Store new hash with TTL
            self.redis_client.setex(key, 3600, current_hash)  # 1 hour TTL
            return False
            
        except Exception as e:
            logger.warning(f"Deduplication check error: {e}")
            return False


class ResponseValidator:
    """Validate API responses for data quality."""
    
    @staticmethod
    def validate_match_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate match data structure and content."""
        errors = []
        
        # Basic structure validation
        if not isinstance(data, dict):
            errors.append("Response is not a dictionary")
            return False, errors
        
        # Check for essential fields
        required_fields = ['id', 'homeTeam', 'awayTeam', 'status']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate team data
        for team_key in ['homeTeam', 'awayTeam']:
            if team_key in data:
                team = data[team_key]
                if not isinstance(team, dict) or 'name' not in team:
                    errors.append(f"Invalid {team_key} data")
        
        # Validate status
        if 'status' in data:
            status = data['status']
            if not isinstance(status, dict) or 'description' not in status:
                errors.append("Invalid status data")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_events_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate events data structure."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Response is not a dictionary")
            return False, errors
        
        # Check for incidents array
        if 'incidents' not in data:
            errors.append("Missing incidents array")
            return False, errors
        
        incidents = data['incidents']
        if not isinstance(incidents, list):
            errors.append("Incidents is not an array")
            return False, errors
        
        # Validate individual incidents
        for i, incident in enumerate(incidents[:5]):  # Check first 5
            if not isinstance(incident, dict):
                errors.append(f"Incident {i} is not a dictionary")
                continue
            
            required_fields = ['incidentType', 'time']
            for field in required_fields:
                if field not in incident:
                    errors.append(f"Incident {i} missing field: {field}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_statistics_data(data: Dict) -> Tuple[bool, List[str]]:
        """Validate statistics data structure."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Response is not a dictionary")
            return False, errors
        
        # Check for statistics array or periods
        if 'statistics' not in data and 'periods' not in data:
            errors.append("Missing statistics or periods data")
            return False, errors
        
        return len(errors) == 0, errors


class MatchStatusTracker:
    """Track match status changes for efficient scraping."""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(settings.redis.url)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
    
    async def get_match_status(self, match_id: int) -> Optional[str]:
        """Get last known status of a match."""
        if not self.redis_client:
            return None
        
        try:
            key = f"sofascore:status:{match_id}"
            status = self.redis_client.get(key)
            return status.decode() if status else None
        except Exception:
            return None
    
    async def update_match_status(self, match_id: int, status: str, minute: int = 0):
        """Update match status."""
        if not self.redis_client:
            return
        
        try:
            key = f"sofascore:status:{match_id}"
            status_data = {
                'status': status,
                'minute': minute,
                'updated_at': datetime.now().isoformat()
            }
            
            # Keep status for 24 hours
            self.redis_client.setex(key, 86400, json.dumps(status_data))
        except Exception as e:
            logger.warning(f"Error updating match status: {e}")
    
    async def has_status_changed(self, match_id: int, current_status: str, current_minute: int = 0) -> bool:
        """Check if match status has changed since last update."""
        try:
            key = f"sofascore:status:{match_id}"
            stored_data = self.redis_client.get(key)
            
            if not stored_data:
                return True  # No previous status, treat as changed
            
            stored = json.loads(stored_data)
            
            # Status changed
            if stored['status'] != current_status:
                return True
            
            # Minute progressed (for live matches)
            if current_status in ['inprogress', 'live'] and current_minute > stored.get('minute', 0):
                return True
            
            return False
            
        except Exception:
            return True  # Assume changed if we can't check


class RequestThrottler:
    """Advanced request throttling with adaptive rate limiting."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
        self.backoff_until: Optional[datetime] = None
        self.consecutive_errors = 0
    
    async def acquire(self):
        """Acquire permission to make a request."""
        now = time.time()
        
        # Check if we're in backoff period
        if self.backoff_until and datetime.now() < self.backoff_until:
            wait_seconds = (self.backoff_until - datetime.now()).total_seconds()
            logger.debug(f"Throttler in backoff, waiting {wait_seconds:.1f}s")
            await asyncio.sleep(wait_seconds)
            self.backoff_until = None
        
        # Clean old requests (older than 1 minute)
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check if we need to wait
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0])
            if wait_time > 0:
                logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Record this request
        self.request_times.append(now)
    
    def on_success(self):
        """Call when request succeeds."""
        self.consecutive_errors = 0
        self.backoff_until = None
    
    def on_error(self, status_code: Optional[int] = None):
        """Call when request fails."""
        self.consecutive_errors += 1
        
        # Implement exponential backoff for repeated errors
        if self.consecutive_errors >= 3:
            backoff_seconds = min(300, 2 ** self.consecutive_errors)  # Max 5 minutes
            self.backoff_until = datetime.now() + timedelta(seconds=backoff_seconds)
            logger.warning(f"Too many errors, backing off for {backoff_seconds}s")
        
        # Special handling for rate limit errors
        if status_code == 429:
            self.backoff_until = datetime.now() + timedelta(seconds=60)
            logger.warning("Rate limited by server, backing off for 60s")


# Global instances
data_cache = DataCache()
data_deduplicator = DataDeduplicator()
match_status_tracker = MatchStatusTracker()