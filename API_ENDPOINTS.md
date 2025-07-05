# SofaScore API Endpoints Documentation

## Discovered Endpoints

### Live Matches
- **URL**: `https://api.sofascore.com/api/v1/sport/football/events/live`
- **Purpose**: Get all currently live football matches
- **Response**: List of live match events with basic info

### Match Details
- **URL**: `https://api.sofascore.com/api/v1/event/{match_id}`
- **Purpose**: Get detailed information for a specific match
- **Response**: Complete match data including teams, scores, status

### Match Statistics
- **URL**: `https://api.sofascore.com/api/v1/event/{match_id}/statistics`
- **Purpose**: Get match statistics (possession, shots, etc.)
- **Response**: Detailed team and player statistics

### Match Events/Incidents
- **URL**: `https://api.sofascore.com/api/v1/event/{match_id}/incidents`
- **Purpose**: Get match events (goals, cards, substitutions) with timestamps
- **Response**: List of match incidents with exact timing

### Match Lineups
- **URL**: `https://api.sofascore.com/api/v1/event/{match_id}/lineups`
- **Purpose**: Get starting lineups and player information
- **Response**: Home and away team lineups

### Fixtures by Date
- **URL**: `https://api.sofascore.com/api/v1/sport/football/scheduled-events/{YYYY-MM-DD}`
- **Purpose**: Get scheduled matches for a specific date
- **Response**: List of upcoming matches

### Historical Matches by Date
- **URL**: `https://api.sofascore.com/api/v1/sport/football/events/{YYYY-MM-DD}`
- **Purpose**: Get completed matches for a specific date
- **Response**: List of finished matches

### Tournament Fixtures
- **URL**: `https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/season/{season_id}/events/next/0`
- **Purpose**: Get upcoming fixtures for a specific tournament
- **Response**: Tournament-specific fixture list

### Football Categories
- **URL**: `https://api.sofascore.com/api/v1/sport/football/categories`
- **Purpose**: Get list of football tournaments and categories
- **Response**: Hierarchical list of tournaments

## Rate Limiting
- Recommended: 1 second delay between requests
- No API key required for basic endpoints
- Use appropriate User-Agent headers

## Data Structure Notes

### Match Events (Incidents)
- `incidentType`: goal, yellowCard, redCard, substitution, etc.
- `time`: Minute of the event
- `addedTime`: Additional time (stoppage time)
- `teamSide`: 'home' or 'away'
- `player`: Player involved in the event
- `assist1`: First assist player (for goals)

### Goal Analysis Fields
- Goals with `time >= 75` minutes considered "late goals"
- Goals in added time (`addedTime > 0`) are separately tracked
- Goal types: regular, penalty, ownGoal, etc.

### Team Statistics
Common statistics available:
- Ball possession %
- Shots on target / Total shots
- Corner kicks
- Fouls
- Yellow/Red cards
- Passes completed
- Pass accuracy %
