"""
Data models for curated/normalized tables.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Competition:
    """Normalized competition data."""
    sofascore_id: int
    name: str
    slug: str
    category: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    priority: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass  
class Team:
    """Normalized team data."""
    sofascore_id: int
    name: str
    short_name: Optional[str] = None
    name_code: Optional[str] = None
    slug: Optional[str] = None
    country: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    founded_year: Optional[int] = None
    venue_name: Optional[str] = None
    venue_capacity: Optional[int] = None
    is_national_team: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Player:
    """Normalized player data."""
    sofascore_id: int
    name: str
    slug: str
    position: Optional[str] = None
    jersey_number: Optional[int] = None
    date_of_birth: Optional[datetime] = None
    height_cm: Optional[int] = None
    weight_kg: Optional[int] = None
    foot: Optional[str] = None
    country: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Match:
    """Normalized match data."""
    match_id: int
    competition_id: Optional[int] = None
    season: Optional[str] = None
    round: Optional[str] = None
    match_date: Optional[datetime] = None
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_score_ht: Optional[int] = None
    away_score_ht: Optional[int] = None
    status: Optional[str] = None
    status_code: Optional[int] = None
    current_minute: Optional[int] = None
    referee_name: Optional[str] = None
    venue_name: Optional[str] = None
    venue_city: Optional[str] = None
    attendance: Optional[int] = None
    weather_condition: Optional[str] = None
    temperature_celsius: Optional[int] = None
    pitch_condition: Optional[str] = None
    importance: Optional[int] = None
    is_live: bool = False
    last_updated: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Event:
    """Normalized event data."""
    match_id: int
    minute: int
    minute_extra: int = 0
    event_type: str = ""
    event_detail: Optional[str] = None
    team_id: Optional[int] = None
    player_id: Optional[int] = None
    related_player_id: Optional[int] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    xg_value: Optional[float] = None
    is_home_team: Optional[bool] = None
    description: Optional[str] = None
    event_order: int = 0
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MinuteStats:
    """Normalized minute-by-minute statistics."""
    match_id: int
    minute: int
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_shots_off_target: int = 0
    away_shots_off_target: int = 0
    home_shots_blocked: int = 0
    away_shots_blocked: int = 0
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_passes: int = 0
    away_passes: int = 0
    home_pass_accuracy: Optional[float] = None
    away_pass_accuracy: Optional[float] = None
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    home_offsides: int = 0
    away_offsides: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    created_at: datetime = field(default_factory=datetime.now)
