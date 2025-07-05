"""
Utility functions for the SofaScore data collection pipeline
"""

import logging
import time
import requests
from datetime import datetime
import os

def setup_logging():
    """Set up logging configuration"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def make_api_request(url, timeout=30, delay=1.0):
    """
    Make a rate-limited API request to SofaScore
    
    Args:
        url (str): The API endpoint URL
        timeout (int): Request timeout in seconds
        delay (float): Delay between requests in seconds
    
    Returns:
        dict: JSON response data or None if failed
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Rate limiting
        time.sleep(delay)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched data from: {url}")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {url}: {e}")
        return None
    except ValueError as e:
        logger.error(f"JSON parsing failed for {url}: {e}")
        return None

def format_timestamp(timestamp):
    """
    Format timestamp for consistent logging
    
    Args:
        timestamp (int): Unix timestamp
    
    Returns:
        str: Formatted timestamp string
    """
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
