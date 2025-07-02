"""
Base scraper classes and utilities for the SofaScore pipeline.
"""

import abc
import asyncio
import time
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


@dataclass
class ScrapeResult:
    """Result of a scraping operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: int = 0
    endpoint: str = ""
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_period: int = 60
    period_seconds: int = 60
    burst_limit: int = 10
    backoff_factor: float = 2.0
    max_backoff: int = 300


class CircuitBreaker:
    """Circuit breaker pattern for handling API failures."""
    
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func):
        """Decorator to apply circuit breaker."""
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if self._should_attempt_reset():
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.reset_timeout
    
    def _on_success(self):
        """Handle successful request."""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'


class BaseScraper(abc.ABC):
    """Base scraper class with common functionality."""
    
    def __init__(self, name: str, base_url: str, rate_limit_config: Optional[RateLimitConfig] = None):
        self.name = name
        self.base_url = base_url
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self.session: Optional[ClientSession] = None
        self.circuit_breaker = CircuitBreaker()
        
        # Request tracking
        self.request_times: List[float] = []
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # Common headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; DataPipeline/1.0)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self):
        """Initialize HTTP session."""
        if self.session is None:
            timeout = ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            self.session = ClientSession(
                timeout=timeout,
                headers=self.headers,
                connector=connector
            )
            logger.debug(f"{self.name} session started")
    
    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.debug(f"{self.name} session closed")
    
    def _should_rate_limit(self) -> bool:
        """Check if we should rate limit based on recent requests."""
        now = time.time()
        
        # Clean old requests outside the time window
        cutoff = now - self.rate_limit_config.period_seconds
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        # Check if we're at the limit
        return len(self.request_times) >= self.rate_limit_config.requests_per_period
    
    async def _wait_for_rate_limit(self):
        """Wait if rate limit is exceeded."""
        if self._should_rate_limit():
            oldest_request = min(self.request_times) if self.request_times else time.time()
            wait_time = oldest_request + self.rate_limit_config.period_seconds - time.time()
            
            if wait_time > 0:
                logger.debug(f"{self.name} rate limit hit, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((ClientError, asyncio.TimeoutError))
    )
    async def make_request(
        self, 
        url: str, 
        method: str = 'GET',
        **kwargs
    ) -> ScrapeResult:
        """Make HTTP request with rate limiting and error handling."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        await self._wait_for_rate_limit()
        
        start_time = time.time()
        self.request_times.append(start_time)
        self.total_requests += 1
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                duration_ms = int((time.time() - start_time) * 1000)
                
                if response.status == 200:
                    data = await response.json()
                    self.successful_requests += 1
                    
                    return ScrapeResult(
                        success=True,
                        data=data,
                        status_code=response.status,
                        duration_ms=duration_ms,
                        endpoint=url
                    )
                
                elif response.status == 429:
                    # Rate limited
                    self.failed_requests += 1
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"{self.name} rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)
                    
                    return ScrapeResult(
                        success=False,
                        error=f"Rate limited (429)",
                        status_code=response.status,
                        duration_ms=duration_ms,
                        endpoint=url
                    )
                
                else:
                    self.failed_requests += 1
                    error_text = await response.text()
                    
                    return ScrapeResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text[:200]}",
                        status_code=response.status,
                        duration_ms=duration_ms,
                        endpoint=url
                    )
        
        except ClientError as e:
            self.failed_requests += 1
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ScrapeResult(
                success=False,
                error=f"Client error: {str(e)}",
                duration_ms=duration_ms,
                endpoint=url
            )
        
        except asyncio.TimeoutError:
            self.failed_requests += 1
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ScrapeResult(
                success=False,
                error="Request timeout",
                duration_ms=duration_ms,
                endpoint=url
            )
        
        except Exception as e:
            self.failed_requests += 1
            duration_ms = int((time.time() - start_time) * 1000)
            
            return ScrapeResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                duration_ms=duration_ms,
                endpoint=url
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        success_rate = (
            (self.successful_requests / self.total_requests * 100)
            if self.total_requests > 0 else 0
        )
        
        avg_duration = (
            sum(self.request_times[-100:]) / len(self.request_times[-100:])
            if self.request_times else 0
        )
        
        return {
            'name': self.name,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate_percent': round(success_rate, 2),
            'avg_duration_ms': round(avg_duration * 1000, 2),
            'current_rate_limit_usage': len(self.request_times),
            'rate_limit_max': self.rate_limit_config.requests_per_period,
            'circuit_breaker_state': self.circuit_breaker.state
        }
    
    @abc.abstractmethod
    async def scrape(self, *args, **kwargs) -> ScrapeResult:
        """Abstract method for scraping implementation."""
        pass


class BatchScraper(BaseScraper):
    """Scraper for batch operations with semaphore control."""
    
    def __init__(self, name: str, base_url: str, max_concurrent: int = 5, **kwargs):
        super().__init__(name, base_url, **kwargs)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.batch_results: List[ScrapeResult] = []
    
    async def scrape_batch(
        self, 
        items: List[Any], 
        scrape_func,
        progress_callback=None
    ) -> List[ScrapeResult]:
        """Scrape multiple items with concurrency control."""
        self.batch_results = []
        
        async def scrape_with_semaphore(item):
            async with self.semaphore:
                result = await scrape_func(item)
                self.batch_results.append(result)
                
                if progress_callback:
                    await progress_callback(len(self.batch_results), len(items))
                
                return result
        
        logger.info(f"{self.name} starting batch scrape of {len(items)} items")
        start_time = time.time()
        
        tasks = [scrape_with_semaphore(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        successful = sum(1 for r in results if isinstance(r, ScrapeResult) and r.success)
        
        logger.info(
            f"{self.name} batch completed: {successful}/{len(items)} successful "
            f"in {duration:.2f}s"
        )
        
        return [r for r in results if isinstance(r, ScrapeResult)]
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """Get statistics for the last batch operation."""
        if not self.batch_results:
            return {}
        
        successful = sum(1 for r in self.batch_results if r.success)
        total = len(self.batch_results)
        avg_duration = sum(r.duration_ms for r in self.batch_results) / total
        
        return {
            'batch_size': total,
            'batch_successful': successful,
            'batch_failed': total - successful,
            'batch_success_rate': round(successful / total * 100, 2),
            'batch_avg_duration_ms': round(avg_duration, 2)
        }


class ScraperRegistry:
    """Registry for managing multiple scrapers."""
    
    def __init__(self):
        self._scrapers: Dict[str, BaseScraper] = {}
    
    def register(self, scraper: BaseScraper):
        """Register a scraper."""
        self._scrapers[scraper.name] = scraper
        logger.info(f"Registered scraper: {scraper.name}")
    
    def get(self, name: str) -> Optional[BaseScraper]:
        """Get a scraper by name."""
        return self._scrapers.get(name)
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered scrapers."""
        return {name: scraper.get_stats() for name, scraper in self._scrapers.items()}
    
    async def close_all(self):
        """Close all registered scrapers."""
        for scraper in self._scrapers.values():
            await scraper.close_session()
        logger.info("All scrapers closed")


# Global scraper registry
scraper_registry = ScraperRegistry()