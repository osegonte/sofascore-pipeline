"""
Test utilities for SofaScore pipeline tests
"""
import logging
import time
import requests
from datetime import datetime

def setup_logging():
    """Set up logging for tests"""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def make_api_request(url, timeout=30, delay=1.0):
    """Make API request for testing"""
    logger = logging.getLogger(__name__)
    
    try:
        time.sleep(delay)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Successfully fetched data from: {url}")
        return response.json()
    except Exception as e:
        logger.error(f"API request failed for {url}: {e}")
        return None
