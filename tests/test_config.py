"""
Test configuration for SofaScore pipeline validation
"""
import os
from datetime import datetime, timedelta

# Test Database Configuration
TEST_DB_NAME = "sofascore_test"
TEST_EXPORT_DIR = "tests/fixtures/sample_data"
TEST_REPORTS_DIR = "tests/reports"

# Data Validation Thresholds
VALIDATION_THRESHOLDS = {
    'goal_timestamp_accuracy_seconds': 60,  # Goals within 1 minute tolerance
    'possession_percentage_tolerance': 5.0,  # 5% tolerance for possession
    'shots_count_tolerance': 2,  # +/- 2 shots tolerance
    'fixture_time_accuracy_minutes': 15,  # 15 minute tolerance for kickoff times
    'minimum_data_completeness': 0.85,  # 85% data completeness required
    'late_goal_percentage_range': (5.0, 25.0),  # Expected late goal percentage range
    'max_api_response_time_seconds': 10.0,  # Maximum acceptable API response time
    'database_query_timeout_seconds': 30.0  # Maximum database query time
}

# Reference Data Sources
REFERENCE_SOURCES = {
    'sofascore_ui': 'https://www.sofascore.com',
    'backup_api': None,  # Could add ESPN, BBC Sport, etc.
}

# Test Match IDs (known completed matches for validation)
REFERENCE_MATCH_IDS = [
    # Add specific match IDs here after identifying reliable test cases
]

# Performance Test Parameters
PERFORMANCE_TEST_CONFIG = {
    'concurrent_matches': 5,
    'test_duration_minutes': 10,
    'max_memory_usage_mb': 512,
    'max_cpu_percentage': 80
}

# Reliability Test Configuration
RELIABILITY_TEST_CONFIG = {
    'test_cycles': 50,
    'acceptable_failure_rate': 0.05,  # 5% failure rate acceptable
    'retry_attempts': 3,
    'backoff_seconds': [1, 2, 5]
}
