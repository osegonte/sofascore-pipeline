"""
SQLAlchemy models for SofaScore database
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Decimal, ForeignKey, Text, Date, Time, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class LiveMatch(Base):
    __tablename__ = 'live_matches'
    
    match_id = Column(BigInteger, primary_key=True)
    competition = Column(String(255))
    league = Column(String(255))
    match_date = Column(Date)
    match_time = Column(Time)
    match_datetime = Column(DateTime)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    home_team_id = Column(BigInteger)
    away_team_id = Column(BigInteger)
    venue = Column(String(255))
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    minutes_elapsed = Column(Integer)
    period = Column(Integer)
    status = Column(String(100))
    status_type = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class GoalEvent(Base):
    __tablename__ = 'goal_events'
    
    goal_id = Column(BigInteger, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    exact_timestamp = Column(Integer, nullable=False)
    added_time = Column(Integer, default=0)
    scoring_player = Column(String(255))
    scoring_player_id = Column(BigInteger)
    assisting_player = Column(String(255))
    assisting_player_id = Column(BigInteger)
    goal_type = Column(String(50), default='regular')
    team_side = Column(String(10))
    description = Column(Text)
    period = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class TeamStatistic(Base):
    __tablename__ = 'team_statistics'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    team_side = Column(String(10))
    team_name = Column(String(255))
    possession_percentage = Column(Decimal(5,2))
    shots_on_target = Column(Integer)
    total_shots = Column(Integer)
    corners = Column(Integer)
    fouls = Column(Integer)
    yellow_cards = Column(Integer)
    red_cards = Column(Integer)
    offsides = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class PlayerStatistic(Base):
    __tablename__ = 'player_statistics'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(BigInteger, ForeignKey('live_matches.match_id'))
    player_name = Column(String(255), nullable=False)
    player_id = Column(BigInteger)
    team_side = Column(String(10))
    position = Column(String(50))
    jersey_number = Column(Integer)
    is_starter = Column(Boolean, default=False)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    cards_received = Column(Integer, default=0)
    minutes_played = Column(Integer)
    shots_on_target = Column(Integer)
    competition = Column(String(255))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class Fixture(Base):
    __tablename__ = 'fixtures'
    
    fixture_id = Column(BigInteger, primary_key=True)
    home_team = Column(String(255), nullable=False)
    away_team = Column(String(255), nullable=False)
    home_team_id = Column(BigInteger)
    away_team_id = Column(BigInteger)
    kickoff_time = Column(DateTime)
    kickoff_date = Column(Date)
    kickoff_time_formatted = Column(Time)
    tournament = Column(String(255))
    tournament_id = Column(BigInteger)
    round_info = Column(String(255))
    status = Column(String(100))
    venue = Column(String(255))
    source_type = Column(String(50))
    scraped_at = Column(DateTime, default=datetime.utcnow)

class GoalAnalysis(Base):
    __tablename__ = 'goal_analysis'
    
    id = Column(Integer, primary_key=True)
    analysis_date = Column(Date, default=datetime.utcnow().date)
    total_matches_analyzed = Column(Integer)
    total_goals_analyzed = Column(Integer)
    late_goals_count = Column(Integer)
    late_goals_percentage = Column(Decimal(5,2))
    very_late_goals_count = Column(Integer)
    injury_time_goals_count = Column(Integer)
    average_goals_per_match = Column(Decimal(5,2))
    average_goal_minute = Column(Decimal(5,2))
    goals_0_15 = Column(Integer, default=0)
    goals_16_30 = Column(Integer, default=0)
    goals_31_45 = Column(Integer, default=0)
    goals_46_60 = Column(Integer, default=0)
    goals_61_75 = Column(Integer, default=0)
    goals_76_90 = Column(Integer, default=0)
    goals_90_plus = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
