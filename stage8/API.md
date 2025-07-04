# Stage 8 API Documentation

## Overview

The Stage 8 API provides real-time access to betting predictions and match data from the SofaScore pipeline.

## Base URL

```
http://localhost:8008
```

## Authentication

No authentication required for local development.

## Endpoints

### GET /api/live-matches

Returns current live matches with predictions.

**Response:**
```json
{
  "matches": [
    {
      "match_id": 12345,
      "minute": 65,
      "home_team": "Arsenal",
      "away_team": "Chelsea",
      "home_score": 1,
      "away_score": 0,
      "probabilities": {
        "goal_next_1min": 0.12,
        "goal_next_5min": 0.34,
        "goal_next_15min": 0.58
      },
      "confidence": 0.78,
      "recommendation": {
        "action": "BET",
        "reason": "High confidence betting opportunity"
      },
      "last_updated": "2025-07-04T18:30:00Z"
    }
  ],
  "count": 1
}
```

### GET /api/alerts

Returns active high-confidence alerts.

**Response:**
```json
{
  "alerts": [
    {
      "alert_id": "alert_12345_65",
      "match_id": 12345,
      "message": "HIGH CONFIDENCE BETTING OPPORTUNITY",
      "probability": 0.58,
      "confidence": 0.78,
      "teams": "Arsenal vs Chelsea",
      "timestamp": "2025-07-04T18:30:00Z",
      "priority": "high"
    }
  ],
  "count": 1
}
```

### WebSocket /ws

Real-time updates every 30 seconds.

**Message Format:**
```json
{
  "type": "update",
  "matches": [...],
  "alerts": [...],
  "timestamp": "2025-07-04T18:30:00Z"
}
```
