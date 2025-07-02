"""
Configuration settings for SofaScore data pipeline.
"""
import os
from typing import List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/sofascore_db')
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'sofascore_db')
    user: str = os.getenv('DB_USER', 'username')
    password: str = os.getenv('DB_PASSWORD', 'password')
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

@dataclass
class S3Config:
    """AWS S3 configuration settings."""
    access_key_id: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    secret_access_key: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    region: str = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name: str = os.getenv('S3_BUCKET_NAME', 'sofascore-raw-data')
    bucket_prefix: str = os.getenv('S3_BUCKET_PREFIX', 'data/')

@dataclass
class SofaScoreConfig:
    """SofaScore API configuration settings."""
    base_url: str = os.getenv('SOFASCORE_BASE_URL', 'https://api.sofascore.com/api/v1')
    user_agent: str = os.getenv('SOFASCORE_USER_AGENT', 'Mozilla/5.0 (compatible; SofaScore-Pipeline/1.0)')
    rate_limit_requests: int = int(os.getenv('SOFASCORE_RATE_LIMIT_REQUESTS', '60'))
    rate_limit_period: int = int(os.getenv('SOFASCORE_RATE_LIMIT_PERIOD', '60'))
    timeout: int = int(os.getenv('SOFASCORE_TIMEOUT', '30'))
    
    # Endpoints
    @property
    def feed_endpoint(self) -> str:
        return f"{self.base_url}/event/{{match_id}}/feed"
    
    @property
    def events_endpoint(self) -> str:
        return f"{self.base_url}/event/{{match_id}}/incidents"
    
    @property
    def stats_endpoint(self) -> str:
        return f"{self.base_url}/event/{{match_id}}/statistics"
    
    @property
    def momentum_endpoint(self) -> str:
        return f"{self.base_url}/event/{{match_id}}/momentum"

@dataclass
class RedisConfig:
    """Redis configuration settings."""
    url: str = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    db: int = int(os.getenv('REDIS_DB', '0'))

@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_path: str = os.getenv('LOG_FILE_PATH', 'logs/sofascore_pipeline.log')
    max_file_size: int = int(os.getenv('LOG_MAX_FILE_SIZE', '10485760'))  # 10MB
    backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))

@dataclass
class PipelineConfig:
    """Pipeline configuration settings."""
    scrape_interval_live: int = int(os.getenv('SCRAPE_INTERVAL_LIVE', '60'))
    scrape_interval_finished: int = int(os.getenv('SCRAPE_INTERVAL_FINISHED', '3600'))
    batch_size: int = int(os.getenv('BATCH_SIZE', '100'))
    max_concurrent_requests: int = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
    max_retry_attempts: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
    retry_backoff_factor: int = int(os.getenv('RETRY_BACKOFF_FACTOR', '2'))

@dataclass
class AlertingConfig:
    """Alerting and monitoring configuration."""
    slack_webhook_url: Optional[str] = os.getenv('SLACK_WEBHOOK_URL')
    email_smtp_host: str = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    email_smtp_port: int = int(os.getenv('EMAIL_SMTP_PORT', '587'))
    email_username: Optional[str] = os.getenv('EMAIL_USERNAME')
    email_password: Optional[str] = os.getenv('EMAIL_PASSWORD')
    alert_recipients: List[str] = os.getenv('ALERT_RECIPIENTS', '').split(',')

class Settings:
    """Main settings class that combines all configuration."""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.testing = os.getenv('TESTING', 'false').lower() == 'true'
        
        # Storage configuration
        self.storage_backend = os.getenv('STORAGE_BACKEND', 'postgresql')
        self.raw_data_storage = os.getenv('RAW_DATA_STORAGE', 's3')
        
        # Match filtering
        self.competitions = os.getenv('COMPETITIONS', '').split(',')
        self.min_match_importance = int(os.getenv('MIN_MATCH_IMPORTANCE', '3'))
        self.include_friendlies = os.getenv('INCLUDE_FRIENDLIES', 'false').lower() == 'true'
        
        # Initialize configuration objects
        self.database = DatabaseConfig()
        self.s3 = S3Config()
        self.sofascore = SofaScoreConfig()
        self.redis = RedisConfig()
        self.logging = LoggingConfig()
        self.pipeline = PipelineConfig()
        self.alerting = AlertingConfig()
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check required database settings
        if not all([self.database.host, self.database.name, self.database.user]):
            errors.append("Database configuration incomplete")
        
        # Check S3 settings if using S3 storage
        if self.raw_data_storage in ['s3', 'both']:
            if not all([self.s3.access_key_id, self.s3.secret_access_key, self.s3.bucket_name]):
                errors.append("S3 configuration incomplete")
        
        # Check SofaScore settings
        if not self.sofascore.base_url:
            errors.append("SofaScore base URL not configured")
        
        return errors
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == 'production'
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == 'development'

# Global settings instance
settings = Settings()

# Validate settings on import
validation_errors = settings.validate()
if validation_errors and not settings.testing:
    raise ValueError(f"Configuration errors: {', '.join(validation_errors)}")