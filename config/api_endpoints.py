"""
Fixed SofaScore API endpoints and configuration
"""

# Primary API endpoints that actually work
SOFASCORE_BASE_URL = "https://api.sofascore.com/api/v1"

# Working endpoint patterns
ENDPOINTS = {
    # Live matches
    'live_matches': '/sport/football/events/live',
    
    # Match details (use these instead of /event/{id})
    'match_details': '/event/{match_id}',
    'match_summary': '/event/{match_id}/summary',
    'match_lineups': '/event/{match_id}/lineups',
    'match_incidents': '/event/{match_id}/incidents',
    
    # Statistics endpoints (often return 404, use alternatives)
    'match_statistics': '/event/{match_id}/statistics',
    'match_head2head': '/event/{match_id}/h2h',
    
    # Alternative data sources
    'team_recent_matches': '/team/{team_id}/events/last/0',
    'tournament_matches': '/unique-tournament/{tournament_id}/season/{season_id}/events/last/0',
    
    # Fixtures
    'fixtures_date': '/sport/football/scheduled-events/{date}',
    'fixtures_live': '/sport/football/events/live',
    
    # Venue information (often in tournament data)
    'tournament_info': '/unique-tournament/{tournament_id}',
    'season_info': '/unique-tournament/{tournament_id}/season/{season_id}'
}

# Headers that work better with SofaScore
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Origin': 'https://www.sofascore.com',
    'Referer': 'https://www.sofascore.com/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site'
}

# Rate limiting
RATE_LIMIT_DELAY = 1.5  # Increased delay
MAX_RETRIES = 3
TIMEOUT = 15  # Increased timeout
