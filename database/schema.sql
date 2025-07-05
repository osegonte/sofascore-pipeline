-- SofaScore Database Schema
-- Drop tables if they exist (for fresh start)
DROP TABLE IF EXISTS goal_events CASCADE;
DROP TABLE IF EXISTS team_statistics CASCADE;
DROP TABLE IF EXISTS player_statistics CASCADE;
DROP TABLE IF EXISTS match_events CASCADE;
DROP TABLE IF EXISTS fixtures CASCADE;
DROP TABLE IF EXISTS live_matches CASCADE;
DROP TABLE IF EXISTS goal_analysis CASCADE;

-- 1. Live Matches Table
CREATE TABLE live_matches (
    match_id BIGINT PRIMARY KEY,
    competition VARCHAR(255),
    league VARCHAR(255),
    match_date DATE,
    match_time TIME,
    match_datetime TIMESTAMP,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    home_team_id BIGINT,
    away_team_id BIGINT,
    venue VARCHAR(255),
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    minutes_elapsed INTEGER,
    period INTEGER,
    status VARCHAR(100),
    status_type VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Goal Events Table (Enhanced for late-goal analysis)
CREATE TABLE goal_events (
    goal_id BIGINT PRIMARY KEY,
    match_id BIGINT REFERENCES live_matches(match_id),
    exact_timestamp INTEGER NOT NULL,
    added_time INTEGER DEFAULT 0,
    total_minute INTEGER GENERATED ALWAYS AS (exact_timestamp + added_time) STORED,
    scoring_player VARCHAR(255),
    scoring_player_id BIGINT,
    assisting_player VARCHAR(255),
    assisting_player_id BIGINT,
    goal_type VARCHAR(50) DEFAULT 'regular',
    team_side VARCHAR(10) CHECK (team_side IN ('home', 'away')),
    description TEXT,
    
    -- Time Analysis Fields
    period INTEGER CHECK (period IN (1, 2)),
    is_first_half BOOLEAN GENERATED ALWAYS AS (exact_timestamp <= 45) STORED,
    is_second_half BOOLEAN GENERATED ALWAYS AS (exact_timestamp > 45) STORED,
    is_late_goal BOOLEAN GENERATED ALWAYS AS (exact_timestamp + added_time >= 75) STORED,
    is_very_late_goal BOOLEAN GENERATED ALWAYS AS (exact_timestamp + added_time >= 85) STORED,
    is_injury_time_goal BOOLEAN GENERATED ALWAYS AS (added_time > 0) STORED,
    
    -- Time Interval for Analysis
    time_interval VARCHAR(10) GENERATED ALWAYS AS (
        CASE 
            WHEN exact_timestamp + added_time <= 15 THEN '0-15'
            WHEN exact_timestamp + added_time <= 30 THEN '16-30'
            WHEN exact_timestamp + added_time <= 45 THEN '31-45'
            WHEN exact_timestamp + added_time <= 60 THEN '46-60'
            WHEN exact_timestamp + added_time <= 75 THEN '61-75'
            WHEN exact_timestamp + added_time <= 90 THEN '76-90'
            ELSE '90+'
        END
    ) STORED,
    
    competition VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Team Statistics Table
CREATE TABLE team_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES live_matches(match_id),
    team_side VARCHAR(10) CHECK (team_side IN ('home', 'away')),
    team_name VARCHAR(255),
    possession_percentage DECIMAL(5,2),
    shots_on_target INTEGER,
    total_shots INTEGER,
    corners INTEGER,
    fouls INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    offsides INTEGER,
    competition VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(match_id, team_side)
);

-- 4. Player Statistics Table
CREATE TABLE player_statistics (
    id SERIAL PRIMARY KEY,
    match_id BIGINT REFERENCES live_matches(match_id),
    player_name VARCHAR(255) NOT NULL,
    player_id BIGINT,
    team_side VARCHAR(10) CHECK (team_side IN ('home', 'away')),
    position VARCHAR(50),
    jersey_number INTEGER,
    is_starter BOOLEAN DEFAULT FALSE,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    cards_received INTEGER DEFAULT 0,
    minutes_played INTEGER,
    shots_on_target INTEGER,
    competition VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Fixtures Table
CREATE TABLE fixtures (
    fixture_id BIGINT PRIMARY KEY,
    home_team VARCHAR(255) NOT NULL,
    away_team VARCHAR(255) NOT NULL,
    home_team_id BIGINT,
    away_team_id BIGINT,
    kickoff_time TIMESTAMP,
    kickoff_date DATE,
    kickoff_time_formatted TIME,
    tournament VARCHAR(255),
    tournament_id BIGINT,
    round_info VARCHAR(255),
    status VARCHAR(100),
    venue VARCHAR(255),
    source_type VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Goal Analysis Summary Table
CREATE TABLE goal_analysis (
    id SERIAL PRIMARY KEY,
    analysis_date DATE DEFAULT CURRENT_DATE,
    total_matches_analyzed INTEGER,
    total_goals_analyzed INTEGER,
    late_goals_count INTEGER,
    late_goals_percentage DECIMAL(5,2),
    very_late_goals_count INTEGER,
    injury_time_goals_count INTEGER,
    average_goals_per_match DECIMAL(5,2),
    average_goal_minute DECIMAL(5,2),
    
    -- Goal distribution by intervals
    goals_0_15 INTEGER DEFAULT 0,
    goals_16_30 INTEGER DEFAULT 0,
    goals_31_45 INTEGER DEFAULT 0,
    goals_46_60 INTEGER DEFAULT 0,
    goals_61_75 INTEGER DEFAULT 0,
    goals_76_90 INTEGER DEFAULT 0,
    goals_90_plus INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX idx_goal_events_match_id ON goal_events(match_id);
CREATE INDEX idx_goal_events_total_minute ON goal_events(total_minute);
CREATE INDEX idx_goal_events_is_late_goal ON goal_events(is_late_goal);
CREATE INDEX idx_goal_events_time_interval ON goal_events(time_interval);
CREATE INDEX idx_team_stats_match_id ON team_statistics(match_id);
CREATE INDEX idx_player_stats_match_id ON player_statistics(match_id);
CREATE INDEX idx_fixtures_kickoff_date ON fixtures(kickoff_date);
CREATE INDEX idx_live_matches_date ON live_matches(match_date);

-- Create Views for Common Queries
CREATE VIEW late_goals_analysis AS
SELECT 
    g.match_id,
    m.home_team,
    m.away_team,
    m.competition,
    g.total_minute,
    g.time_interval,
    g.scoring_player,
    g.team_side,
    m.match_date
FROM goal_events g
JOIN live_matches m ON g.match_id = m.match_id
WHERE g.is_late_goal = TRUE
ORDER BY g.total_minute DESC;

CREATE VIEW goal_frequency_by_interval AS
SELECT 
    time_interval,
    COUNT(*) as goal_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM goal_events 
GROUP BY time_interval
ORDER BY 
    CASE time_interval
        WHEN '0-15' THEN 1
        WHEN '16-30' THEN 2
        WHEN '31-45' THEN 3
        WHEN '46-60' THEN 4
        WHEN '61-75' THEN 5
        WHEN '76-90' THEN 6
        WHEN '90+' THEN 7
    END;