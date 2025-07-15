"""
Fixed utility functions with better API handling and fallback strategies
"""

import logging
import time
import requests
from datetime import datetime
import os
import json

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

def get_request_headers():
    """Get proper headers for SofaScore API"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.sofascore.com',
        'Referer': 'https://www.sofascore.com/',
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }

def make_api_request(url, timeout=15, delay=1.5, max_retries=3):
    """
    Enhanced API request with better error handling and fallback strategies
    """
    logger = logging.getLogger(__name__)
    
    for attempt in range(max_retries):
        try:
            # Rate limiting
            time.sleep(delay)
            
            headers = get_request_headers()
            
            logger.info(f"Attempt {attempt + 1}: Fetching {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            
            # Log response details for debugging
            logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 404:
                logger.warning(f"404 - Endpoint not found: {url}")
                return None
                
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched data from: {url}")
            logger.debug(f"Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            if attempt == max_retries - 1:
                logger.error(f"All attempts timed out for {url}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed on attempt {attempt + 1} for {url}: {e}")
            if attempt == max_retries - 1:
                return None
                
        except ValueError as e:
            logger.error(f"JSON parsing failed for {url}: {e}")
            # Try to log response content for debugging
            try:
                logger.debug(f"Response content: {response.text[:500]}...")
            except:
                pass
            return None
    
    return None

def try_alternative_endpoints(match_id, endpoint_type):
    """
    Try alternative endpoints when primary ones fail
    """
    logger = logging.getLogger(__name__)
    base_url = "https://api.sofascore.com/api/v1"
    
    alternatives = {
        'statistics': [
            f"{base_url}/event/{match_id}/statistics",
            f"{base_url}/event/{match_id}/summary",
            f"{base_url}/event/{match_id}"
        ],
        'lineups': [
            f"{base_url}/event/{match_id}/lineups",
            f"{base_url}/event/{match_id}/summary",
            f"{base_url}/event/{match_id}"
        ],
        'venue': [
            f"{base_url}/event/{match_id}",
            f"{base_url}/event/{match_id}/summary"
        ]
    }
    
    if endpoint_type not in alternatives:
        return None
    
    for url in alternatives[endpoint_type]:
        logger.info(f"Trying alternative endpoint: {url}")
        data = make_api_request(url)
        if data:
            return data
    
    return None

def extract_venue_from_response(data):
    """
    Extract venue information from various response formats
    """
    if not data:
        return None
    
    # Try different locations for venue data
    venue_paths = [
        ['event', 'venue', 'name'],
        ['venue', 'name'],
        ['event', 'venue', 'stadium', 'name'],
        ['stadium', 'name'],
        ['event', 'tournament', 'venue'],
        ['match', 'venue']
    ]
    
    for path in venue_paths:
        try:
            current = data
            for key in path:
                current = current[key]
            if current and isinstance(current, str):
                return current
        except (KeyError, TypeError):
            continue
    
    return None

def extract_possession_from_stats(stats_data):
    """
    Extract possession data from statistics response
    """
    if not stats_data or 'statistics' not in stats_data:
        return None, None
    
    for period in stats_data['statistics']:
        if period.get('period') in ['ALL', '1ST', '2ND']:
            for group in period.get('groups', []):
                for stat in group.get('statisticsItems', []):
                    stat_name = stat.get('name', '').lower()
                    if 'possession' in stat_name or 'ball possession' in stat_name:
                        return stat.get('home'), stat.get('away')
    
    return None, None

def format_timestamp(timestamp):
    """Format timestamp for consistent logging"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(timestamp)

def safe_get_nested(data, keys, default=None):
    """Safely get nested dictionary values"""
    try:
        for key in keys:
            data = data[key]
        return data
    except (KeyError, TypeError):
        return default


# Enhanced functions for corrected goal extraction
def extract_corrected_match_details(match_data, incidents_data, stats_data, team_id, team_name=""):
    """
    Extract match details with corrected goal data consistency
    Integrates with existing utils functions
    """
    from .goal_data_extractor import GoalDataExtractor
    
    logger = setup_logging()
    extractor = GoalDataExtractor(logger)
    
    # Get corrected goal data
    corrected_details = extractor.extract_corrected_match_details(
        match_data, incidents_data, team_id, team_name
    )
    
    # Merge with statistics data if available
    if stats_data and 'statistics' in stats_data:
        team_stats = extract_team_statistics_from_stats(stats_data, team_id, match_data)
        corrected_details.update(team_stats)
    
    return corrected_details

def extract_team_statistics_from_stats(stats_data, team_id, match_data):
    """
    Extract team statistics with proper team identification
    """
    home_team_id = safe_get_nested(match_data, ['event', 'homeTeam', 'id']) or safe_get_nested(match_data, ['homeTeam', 'id'])
    team_is_home = (home_team_id == team_id)
    team_side = 'home' if team_is_home else 'away'
    
    team_stats = {}
    
    try:
        for period in stats_data.get('statistics', []):
            if period.get('period') == 'ALL':
                for group in period.get('groups', []):
                    for stat in group.get('statisticsItems', []):
                        stat_name = stat.get('name', '').lower()
                        team_value = stat.get(team_side)
                        
                        if team_value is not None:
                            # Map statistics with proper cleaning
                            if 'ball possession' in stat_name:
                                team_stats['possession_pct'] = _clean_percentage_value(team_value)
                            elif 'shots on target' in stat_name:
                                team_stats['shots_on_target'] = int(team_value)
                            elif 'total shots' in stat_name:
                                team_stats['total_shots'] = int(team_value)
                            elif 'corner kicks' in stat_name:
                                team_stats['corners'] = int(team_value)
                            elif 'fouls' in stat_name:
                                team_stats['fouls'] = int(team_value)
                            elif 'yellow cards' in stat_name:
                                team_stats['yellow_cards'] = int(team_value)
                            elif 'red cards' in stat_name:
                                team_stats['red_cards'] = int(team_value)
                            elif 'passes' in stat_name and 'accurate' not in stat_name:
                                team_stats['passes'] = int(team_value)
                            elif 'accurate passes' in stat_name:
                                if '%' in str(team_value):
                                    team_stats['pass_accuracy_pct'] = _clean_percentage_value(team_value)
                                else:
                                    team_stats['accurate_passes'] = int(team_value)
    
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Error extracting team statistics: {e}")
    
    return team_stats

def _clean_percentage_value(value):
    """Clean percentage values from API responses"""
    if isinstance(value, str) and value.endswith('%'):
        return float(value.rstrip('%'))
    return float(value)

def log_consistency_metrics(match_details, logger=None):
    """
    Log consistency metrics for debugging
    """
    if not logger:
        logger = setup_logging()
    
    goals_scored = match_details.get('goals_scored', 0)
    goals_conceded = match_details.get('goals_conceded', 0)
    
    logger.info("🎯 CONSISTENCY METRICS:")
    logger.info(f"   Goals scored: {goals_scored}")
    logger.info(f"   Goal times array: {len(match_details.get('goal_times', []))}")
    logger.info(f"   Goal scorers array: {len(match_details.get('goal_scorers', []))}")
    logger.info(f"   Assists array: {len(match_details.get('assists', []))}")
    logger.info(f"   Goals conceded: {goals_conceded}")
    logger.info(f"   Goal conceded times array: {len(match_details.get('goal_conceded_times', []))}")
    
    # Check consistency
    consistency_checks = [
        len(match_details.get('goal_times', [])) == goals_scored,
        len(match_details.get('goal_scorers', [])) == goals_scored,
        len(match_details.get('assists', [])) <= goals_scored,
        len(match_details.get('goal_conceded_times', [])) == goals_conceded
    ]
    
    if all(consistency_checks):
        logger.info("✅ PERFECT CONSISTENCY ACHIEVED!")
    else:
        logger.warning("❌ Consistency issues detected")
    
    return all(consistency_checks)
