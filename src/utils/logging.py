"""
Logging utilities for the SofaScore pipeline.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from config.simple_settings import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.RESET}"
            )
        
        return super().format(record)


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    json_format: bool = False,
    console_output: bool = True
):
    """Setup logging configuration."""
    
    # Get log level from settings or parameter
    log_level = level or settings.logging.level
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_file_path = log_file or settings.logging.file_path
    log_dir = Path(log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        if json_format:
            console_formatter = JSONFormatter()
        else:
            console_formatter = ColoredFormatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file_path:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=settings.logging.max_file_size,
            backupCount=settings.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # Always use JSON format for file logs
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific log levels for third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    # Log the setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging setup completed - Level: {logging.getLevelName(log_level)}")
    logger.info(f"Log file: {log_file_path}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


class PerformanceLogger:
    """Logger for performance metrics."""
    
    def __init__(self, name: str):
        self.logger = get_logger(f"performance.{name}")
        self.start_time = None
    
    def start(self, operation: str):
        """Start timing an operation."""
        self.operation = operation
        self.start_time = datetime.now()
        self.logger.debug(f"Started: {operation}")
    
    def end(self, **kwargs):
        """End timing and log the duration."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            duration_ms = duration.total_seconds() * 1000
            
            self.logger.info(
                f"Completed: {self.operation}",
                extra={
                    'operation': self.operation,
                    'duration_ms': duration_ms,
                    **kwargs
                }
            )
            
            self.start_time = None
        else:
            self.logger.warning(f"End called without start for: {self.operation}")


class ScrapeLogger:
    """Specialized logger for scraping operations."""
    
    def __init__(self, scraper_name: str):
        self.logger = get_logger(f"scraper.{scraper_name}")
        self.scraper_name = scraper_name
    
    def log_request(
        self,
        url: str,
        method: str = 'GET',
        status_code: Optional[int] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log an HTTP request."""
        if error:
            self.logger.error(
                f"Request failed: {method} {url}",
                extra={
                    'url': url,
                    'method': method,
                    'status_code': status_code,
                    'duration_ms': duration_ms,
                    'error': error,
                    'scraper': self.scraper_name
                }
            )
        else:
            self.logger.debug(
                f"Request successful: {method} {url}",
                extra={
                    'url': url,
                    'method': method,
                    'status_code': status_code,
                    'duration_ms': duration_ms,
                    'scraper': self.scraper_name
                }
            )
    
    def log_match_scrape(
        self,
        match_id: int,
        endpoints_successful: int,
        endpoints_failed: int,
        total_duration_ms: int
    ):
        """Log a complete match scraping operation."""
        success_rate = (
            endpoints_successful / (endpoints_successful + endpoints_failed) * 100
            if (endpoints_successful + endpoints_failed) > 0 else 0
        )
        
        self.logger.info(
            f"Match scrape completed: {match_id}",
            extra={
                'match_id': match_id,
                'endpoints_successful': endpoints_successful,
                'endpoints_failed': endpoints_failed,
                'success_rate_percent': round(success_rate, 1),
                'total_duration_ms': total_duration_ms,
                'scraper': self.scraper_name
            }
        )
    
    def log_discovery(self, matches_found: int, competitions: list):
        """Log match discovery results."""
        self.logger.info(
            f"Match discovery completed: {matches_found} matches found",
            extra={
                'matches_found': matches_found,
                'competitions': competitions,
                'scraper': self.scraper_name
            }
        )


class DatabaseLogger:
    """Specialized logger for database operations."""
    
    def __init__(self):
        self.logger = get_logger("database")
    
    def log_query(
        self,
        operation: str,
        table: str,
        records_affected: int = 0,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Log a database operation."""
        if error:
            self.logger.error(
                f"Database operation failed: {operation} on {table}",
                extra={
                    'operation': operation,
                    'table': table,
                    'records_affected': records_affected,
                    'duration_ms': duration_ms,
                    'error': error
                }
            )
        else:
            self.logger.debug(
                f"Database operation successful: {operation} on {table}",
                extra={
                    'operation': operation,
                    'table': table,
                    'records_affected': records_affected,
                    'duration_ms': duration_ms
                }
            )
    
    def log_connection_event(self, event: str, details: Optional[str] = None):
        """Log database connection events."""
        self.logger.info(
            f"Database connection: {event}",
            extra={
                'event': event,
                'details': details
            }
        )


class AlertLogger:
    """Logger for alerts and critical events."""
    
    def __init__(self):
        self.logger = get_logger("alerts")
        self.logger.setLevel(logging.WARNING)  # Only log warnings and above
    
    def rate_limit_exceeded(self, scraper_name: str, wait_time: int):
        """Log rate limiting events."""
        self.logger.warning(
            f"Rate limit exceeded for {scraper_name}",
            extra={
                'scraper': scraper_name,
                'wait_time_seconds': wait_time,
                'alert_type': 'rate_limit'
            }
        )
    
    def scraping_failure(
        self,
        scraper_name: str,
        consecutive_failures: int,
        last_success: Optional[datetime] = None
    ):
        """Log scraping failures that might need attention."""
        self.logger.error(
            f"Scraping failures detected for {scraper_name}",
            extra={
                'scraper': scraper_name,
                'consecutive_failures': consecutive_failures,
                'last_success': last_success.isoformat() if last_success else None,
                'alert_type': 'scraping_failure'
            }
        )
    
    def database_error(self, operation: str, error: str):
        """Log database errors."""
        self.logger.error(
            f"Database error during {operation}",
            extra={
                'operation': operation,
                'error': error,
                'alert_type': 'database_error'
            }
        )
    
    def data_quality_issue(self, issue_type: str, details: dict):
        """Log data quality issues."""
        self.logger.warning(
            f"Data quality issue: {issue_type}",
            extra={
                'issue_type': issue_type,
                'details': details,
                'alert_type': 'data_quality'
            }
        )


# Global logger instances
performance_logger = PerformanceLogger("main")
database_logger = DatabaseLogger()
alert_logger = AlertLogger()