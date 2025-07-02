"""
Transform raw SofaScore JSON data into normalized model objects.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from ..models.curated_models import Competition, Team, Player, Match, Event, MinuteStats
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SofaScoreTransformer:
    """Transform SofaScore raw JSON data into normalized objects."""
    
    @staticmethod
    def extract_competition(tournament_data: Dict[str, Any]) -> Competition:
        """Extract competition from tournament data."""
        return Competition(
            sofascore_id=tournament_data.get('id', 0),
            name=tournament_data.get('name', ''),
            slug=tournament_data.get('slug', ''),
            category=tournament_data.get('category', {}).get('name'),
            country=tournament_data.get('category', {}).get('alpha2'),
            priority=tournament_data.get('priority', 0)
        )
    
    @staticmethod
    def extract_team(team_data: Dict[str, Any]) -> Team:
        """Extract team from team data."""
        return Team(
            sofascore_id=team_data.get('id', 0),
            name=team_data.get('name', ''),
            short_name=team_data.get('shortName'),
            name_code=team_data.get('nameCode'),
            slug=team_data.get('slug', ''),
            country=team_data.get('country', {}).get('alpha2') if team_data.get('country') else None
        )
    
    @staticmethod
    def extract_match(feed_data: Dict[str, Any]) -> Tuple[Match, Competition, Team, Team]:
        """Extract match data and related entities."""
        # Extract competition
        tournament_data = feed_data.get('tournament', {})
        competition = SofaScoreTransformer.extract_competition(tournament_data)
        
        # Extract teams
        home_team_data = feed_data.get('homeTeam', {})
        away_team_data = feed_data.get('awayTeam', {})
        home_team = SofaScoreTransformer.extract_team(home_team_data)
        away_team = SofaScoreTransformer.extract_team(away_team_data)
        
        # Extract match
        status_data = feed_data.get('status', {})
        home_score = feed_data.get('homeScore', {})
        away_score = feed_data.get('awayScore', {})
        
        # Convert timestamp to datetime
        match_date = None
        if feed_data.get('startTimestamp'):
            try:
                match_date = datetime.fromtimestamp(feed_data['startTimestamp'])
            except (ValueError, OSError):
                logger.warning(f"Invalid timestamp: {feed_data['startTimestamp']}")
        
        match = Match(
            match_id=feed_data.get('id', 0),
            season=tournament_data.get('season', {}).get('name'),
            round=feed_data.get('roundInfo', {}).get('name'),
            match_date=match_date,
            home_team_id=home_team.sofascore_id,
            away_team_id=away_team.sofascore_id,
            home_score=home_score.get('current'),
            away_score=away_score.get('current'),
            home_score_ht=home_score.get('period1'),
            away_score_ht=away_score.get('period1'),
            status=status_data.get('description'),
            status_code=status_data.get('code'),
            is_live=status_data.get('code') in [1, 2],
            venue_name=feed_data.get('venue', {}).get('stadium', {}).get('name'),
            venue_city=feed_data.get('venue', {}).get('city', {}).get('name')
        )
        
        return match, competition, home_team, away_team
    
    @staticmethod
    def extract_events(events_data: Dict[str, Any], match_id: int) -> List[Event]:
        """Extract events from incidents data."""
        events = []
        incidents = events_data.get('incidents', [])
        
        for i, incident in enumerate(incidents):
            try:
                event = Event(
                    match_id=match_id,
                    minute=incident.get('time', 0),
                    event_type=incident.get('incidentType', ''),
                    event_detail=incident.get('incidentClass'),
                    player_id=incident.get('player', {}).get('id') if incident.get('player') else None,
                    related_player_id=incident.get('assist1', {}).get('id') if incident.get('assist1') else None,
                    x_coordinate=incident.get('x'),
                    y_coordinate=incident.get('y'),
                    is_home_team=incident.get('isHome'),
                    description=incident.get('text'),
                    event_order=i
                )
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to extract event {i}: {e}")
                continue
        
        return events


class DataValidator:
    """Validate transformed data before saving."""
    
    @staticmethod
    def validate_match(match: Match) -> bool:
        """Validate match data."""
        if not match.match_id or match.match_id <= 0:
            return False
        if not match.home_team_id or not match.away_team_id:
            return False
        return True
    
    @staticmethod
    def validate_team(team: Team) -> bool:
        """Validate team data."""
        if not team.sofascore_id or team.sofascore_id <= 0:
            return False
        if not team.name or len(team.name.strip()) == 0:
            return False
        return True
    
    @staticmethod
    def validate_competition(competition: Competition) -> bool:
        """Validate competition data."""
        if not competition.sofascore_id or competition.sofascore_id <= 0:
            return False
        if not competition.name or len(competition.name.strip()) == 0:
            return False
        return True
    
    @staticmethod
    def validate_event(event: Event) -> bool:
        """Validate event data."""
        if not event.match_id or event.match_id <= 0:
            return False
        if event.minute < 0 or event.minute > 150:
            return False
        if not event.event_type:
            return False
        return True
