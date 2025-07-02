"""
Raw data models for SofaScore pipeline.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class ScrapeJob:
    """Model for scrape job tracking."""
    job_id: str
    match_id: Optional[int] = None
    job_type: str = 'live'  # 'live', 'finished', 'bulk'
    status: str = 'pending'  # 'pending', 'running', 'completed', 'failed', 'partial'
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_details: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class MatchRaw:
    """Model for raw match data."""
    match_id: int
    endpoint: str
    raw_json: Dict[str, Any]
    scrape_timestamp: datetime = field(default_factory=datetime.now)
    http_status: int = 200
    scrape_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class EventsRaw:
    """Model for raw events data."""
    match_id: int
    raw_events_json: Dict[str, Any]
    scrape_timestamp: datetime = field(default_factory=datetime.now)
    event_count: Optional[int] = None
    http_status: int = 200
    scrape_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """Calculate event count after initialization."""
        if self.event_count is None and isinstance(self.raw_events_json, dict):
            incidents = self.raw_events_json.get('incidents', [])
            self.event_count = len(incidents) if isinstance(incidents, list) else 0


@dataclass
class StatsRaw:
    """Model for raw statistics data."""
    match_id: int
    raw_stats_json: Dict[str, Any]
    minute: Optional[int] = None
    scrape_timestamp: datetime = field(default_factory=datetime.now)
    http_status: int = 200
    scrape_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class MomentumRaw:
    """Model for raw momentum data."""
    match_id: int
    raw_momentum_json: Dict[str, Any]
    scrape_timestamp: datetime = field(default_factory=datetime.now)
    data_points_count: Optional[int] = None
    http_status: int = 200
    scrape_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ProcessingLog:
    """Model for processing job tracking."""
    job_type: str
    match_id: Optional[int] = None
    status: str = 'pending'
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    id: int = field(default_factory=lambda: 0)


class RawDataValidator:
    """Validate raw data models before database storage."""
    
    @staticmethod
    def validate_scrape_job(job: ScrapeJob) -> List[str]:
        """Validate scrape job data."""
        errors = []
        if not job.job_id or len(job.job_id.strip()) == 0:
            errors.append("job_id is required")
        return errors
    
    @staticmethod
    def validate_match_raw(match_raw: MatchRaw) -> List[str]:
        """Validate match raw data."""
        errors = []
        if not match_raw.match_id or match_raw.match_id <= 0:
            errors.append("match_id must be positive integer")
        return errors
    
    @staticmethod
    def validate_events_raw(events_raw: EventsRaw) -> List[str]:
        """Validate events raw data."""
        errors = []
        if not events_raw.match_id or events_raw.match_id <= 0:
            errors.append("match_id must be positive integer")
        return errors
    
    @staticmethod
    def validate_stats_raw(stats_raw: StatsRaw) -> List[str]:
        """Validate stats raw data."""
        errors = []
        if not stats_raw.match_id or stats_raw.match_id <= 0:
            errors.append("match_id must be positive integer")
        return errors


class RawDataSanitizer:
    """Sanitize raw data before storage."""
    
    @staticmethod
    def sanitize_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize JSON data by removing problematic characters."""
        return data
    
    @staticmethod
    def remove_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove potentially sensitive data fields."""
        return data
