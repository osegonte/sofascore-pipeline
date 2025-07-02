"""
Simplified configuration settings without pydantic dependency.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:
    def __init__(self):
        self.url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/sofascore_db')
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = int(os.getenv('DB_PORT', '5432'))
        self.name = os.getenv('DB_NAME', 'sofascore_db')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

class SofaScoreConfig:
    def __init__(self):
        self.base_url = os.getenv('SOFASCORE_BASE_URL', 'https://api.sofascore.com/api/v1')
        self.user_agent = os.getenv('SOFASCORE_USER_AGENT', 'Mozilla/5.0 (compatible; SofaScore-Pipeline/1.0)')
        self.rate_limit_requests = int(os.getenv('SOFASCORE_RATE_LIMIT_REQUESTS', '60'))
        self.rate_limit_period = int(os.getenv('SOFASCORE_RATE_LIMIT_PERIOD', '60'))
        self.timeout = int(os.getenv('SOFASCORE_TIMEOUT', '30'))

class RedisConfig:
    def __init__(self):
        self.url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', '6379'))
        self.db = int(os.getenv('REDIS_DB', '0'))

class LoggingConfig:
    def __init__(self):
        self.level = os.getenv('LOG_LEVEL', 'INFO')
        self.format = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.file_path = os.getenv('LOG_FILE_PATH', 'logs/sofascore_pipeline.log')
        self.max_file_size = int(os.getenv('LOG_MAX_FILE_SIZE', '10485760'))
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))

class PipelineConfig:
    def __init__(self):
        self.scrape_interval_live = int(os.getenv('SCRAPE_INTERVAL_LIVE', '60'))
        self.scrape_interval_finished = int(os.getenv('SCRAPE_INTERVAL_FINISHED', '3600'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.max_concurrent_requests = int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.max_retry_attempts = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))
        self.retry_backoff_factor = int(os.getenv('RETRY_BACKOFF_FACTOR', '2'))

class Settings:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'true').lower() == 'true'
        self.testing = os.getenv('TESTING', 'false').lower() == 'true'
        
        self.database = DatabaseConfig()
        self.sofascore = SofaScoreConfig()
        self.redis = RedisConfig()
        self.logging = LoggingConfig()
        self.pipeline = PipelineConfig()
    
    def validate(self) -> List[str]:
        errors = []
        if not all([self.database.host, self.database.name, self.database.user]):
            errors.append("Database configuration incomplete")
        if not self.sofascore.base_url:
            errors.append("SofaScore base URL not configured")
        return errors

settings = Settings()
