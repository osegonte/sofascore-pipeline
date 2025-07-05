"""
Configuration settings for SofaScore data collection pipeline
"""

# API Configuration
SOFASCORE_BASE_URL = "https://api.sofascore.com/api/v1"
REQUEST_TIMEOUT = 30
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# Database Configuration
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "sofascore_data"
DB_USER = "postgres"
DB_PASSWORD = ""

# Export Configuration
EXPORT_DIR = "exports"
CSV_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "pipeline.log"
