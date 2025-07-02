-- Migration 002: Create curated/normalized tables for SofaScore pipeline
-- These tables contain structured, normalized data extracted from raw JSON

-- Competitions/Tournaments table
CREATE TABLE IF NOT EXISTS competitions (
    id SERIAL PRIMARY KEY,
    sofascore_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    category VARCHAR(100), -- 'domestic', 'international', 'club', 'national'
    country VARCHAR(100),
    logo_url TEXT,
    priority INTEGER DEFAULT 0, -- Higher number = higher priority
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    sofascore_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50),
    name_code VARCHAR(10), -- TLA like 'MUN', 'ARS'
    slug VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    logo_url TEXT,
    primary_color VARCHAR(7), -- Hex color
    secondary_color VARCHAR(7), -- Hex color
    founded_year INTEGER,
    venue_name VARCHAR(255),
    venue_capacity INTEGER,
    is_national_team BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Players table
CREATE TABLE IF NOT EXISTS players (
    id SERIAL PRIMARY KEY,
    sofascore_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    position VARCHAR(50), -- 'GK', 'DEF', 'MID', 'ATT'
    jersey_number INTEGER,
    date_of_birth DATE,
    height_cm INTEGER,
    weight_kg INTEGER,
    foot VARCHAR(10), -- 'left', 'right', 'both'
    country VARCHAR(100),
    photo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Matches table (normalized from raw data)
CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    match_id BIGINT UNIQUE NOT NULL, -- SofaScore match ID
    competition_id INTEGER REFERENCES competitions(id),
    season VARCHAR(20),
    round VARCHAR(50),
    match_date TIMESTAMP WITH TIME ZONE NOT NULL,
    home_team_id INTEGER REFERENCES teams(id),
    away_team_id INTEGER REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    home_score_ht INTEGER, -- Half-time score
    away_score_ht INTEGER,
    status VARCHAR(50) NOT NULL, -- 'notstarted', 'inprogress', 'finished', 'cancelled', 'postponed'
    status_code INTEGER,
    current_minute INTEGER,
    referee_name VARCHAR(255),
    venue_name VARCHAR(255),
    venue_city VARCHAR(100),
    attendance INTEGER,
    weather_condition VARCHAR(50),
    temperature_celsius INTEGER,
    pitch_condition VARCHAR(50),
    importance INTEGER, -- 1-5 scale
    is_live BOOLEAN DEFAULT false,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Team lineups for each match
CREATE TABLE IF NOT EXISTS lineups (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    is_starter BOOLEAN NOT NULL DEFAULT true,
    position VARCHAR(50),
    jersey_number INTEGER,
    formation_position INTEGER, -- 1-11 for starters
    minute_in INTEGER DEFAULT 0, -- 0 for starters
    minute_out INTEGER, -- NULL if played full match
    captain BOOLEAN DEFAULT false,
    rating NUMERIC(3,1), -- Player rating out of 10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(match_id, team_id, player_id)
);

-- Match events (goals, cards, substitutions, etc.)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    minute INTEGER NOT NULL,
    minute_extra INTEGER DEFAULT 0, -- Added time
    event_type VARCHAR(50) NOT NULL, -- 'goal', 'card', 'substitution', 'var', etc.
    event_detail VARCHAR(100), -- 'penalty', 'own-goal', 'yellow-card', etc.
    team_id INTEGER REFERENCES teams(id),
    player_id INTEGER REFERENCES players(id),
    related_player_id INTEGER REFERENCES players(id), -- For substitutions, assists
    x_coordinate NUMERIC(5,2), -- 0-100 scale
    y_coordinate NUMERIC(5,2), -- 0-100 scale
    xg_value NUMERIC(4,3), -- Expected goals value
    is_home_team BOOLEAN,
    description TEXT,
    event_order INTEGER, -- Order within the minute
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Minute-by-minute statistics
CREATE TABLE IF NOT EXISTS minute_stats (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    minute INTEGER NOT NULL,
    
    -- Possession stats
    home_possession NUMERIC(5,2),
    away_possession NUMERIC(5,2),
    
    -- Shot stats
    home_shots INTEGER DEFAULT 0,
    away_shots INTEGER DEFAULT 0,
    home_shots_on_target INTEGER DEFAULT 0,
    away_shots_on_target INTEGER DEFAULT 0,
    home_shots_off_target INTEGER DEFAULT 0,
    away_shots_off_target INTEGER DEFAULT 0,
    home_shots_blocked INTEGER DEFAULT 0,
    away_shots_blocked INTEGER DEFAULT 0,
    
    -- Expected goals
    home_xg NUMERIC(4,3) DEFAULT 0,
    away_xg NUMERIC(4,3) DEFAULT 0,
    
    -- Passing stats
    home_passes INTEGER DEFAULT 0,
    away_passes INTEGER DEFAULT 0,
    home_pass_accuracy NUMERIC(5,2),
    away_pass_accuracy NUMERIC(5,2),
    
    -- Other stats
    home_corners INTEGER DEFAULT 0,
    away_corners INTEGER DEFAULT 0,
    home_fouls INTEGER DEFAULT 0,
    away_fouls INTEGER DEFAULT 0,
    home_offsides INTEGER DEFAULT 0,
    away_offsides INTEGER DEFAULT 0,
    home_yellow_cards INTEGER DEFAULT 0,
    away_yellow_cards INTEGER DEFAULT 0,
    home_red_cards INTEGER DEFAULT 0,
    away_red_cards INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (match_id, minute)
);

-- Player statistics per match
CREATE TABLE IF NOT EXISTS player_match_stats (
    id SERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES matches(match_id),
    player_id INTEGER REFERENCES players(id),
    team_id INTEGER REFERENCES teams(id),
    
    -- Basic stats
    minutes_played INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    
    -- Shooting
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    xg NUMERIC(4,3) DEFAULT 0,
    
    -- Passing
    passes INTEGER DEFAULT 0,
    pass_accuracy NUMERIC(5,2),
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    
    -- Defending
    tackles INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    
    -- Other
    touches INTEGER DEFAULT 0,
    dribbles_attempted INTEGER DEFAULT 0,
    dribbles_successful INTEGER DEFAULT 0,
    fouls_committed INTEGER DEFAULT 0,
    fouls_drawn INTEGER DEFAULT 0,
    offsides INTEGER DEFAULT 0,
    
    -- Performance rating
    rating NUMERIC(3,1),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(match_id, player_id)
);

-- Data processing log to track normalization jobs
CREATE TABLE IF NOT EXISTS processing_log (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL, -- 'normalize_matches', 'normalize_events', etc.
    match_id BIGINT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    raw_data_source VARCHAR(50), -- 'matches_raw', 'events_raw', etc.
    processing_duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_competitions_sofascore_id ON competitions(sofascore_id);
CREATE INDEX IF NOT EXISTS idx_competitions_name ON competitions(name);
CREATE INDEX IF NOT EXISTS idx_competitions_priority ON competitions(priority DESC);

CREATE INDEX IF NOT EXISTS idx_teams_sofascore_id ON teams(sofascore_id);
CREATE INDEX IF NOT EXISTS idx_teams_name ON teams(name);
CREATE INDEX IF NOT EXISTS idx_teams_country ON teams(country);

CREATE INDEX IF NOT EXISTS idx_players_sofascore_id ON players(sofascore_id);
CREATE INDEX IF NOT EXISTS idx_players_name ON players(name);
CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);

CREATE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition_id);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_matches_live ON matches(is_live) WHERE is_live = true;
CREATE INDEX IF NOT EXISTS idx_matches_date_status ON matches(match_date, status);

CREATE INDEX IF NOT EXISTS idx_lineups_match_team ON lineups(match_id, team_id);
CREATE INDEX IF NOT EXISTS idx_lineups_player ON lineups(player_id);
CREATE INDEX IF NOT EXISTS idx_lineups_starter ON lineups(is_starter);

CREATE INDEX IF NOT EXISTS idx_events_match_id ON events(match_id);
CREATE INDEX IF NOT EXISTS idx_events_minute ON events(minute);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_player ON events(player_id);
CREATE INDEX IF NOT EXISTS idx_events_team ON events(team_id);
CREATE INDEX IF NOT EXISTS idx_events_match_minute ON events(match_id, minute);
CREATE INDEX IF NOT EXISTS idx_events_xg ON events(xg_value) WHERE xg_value IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_minute_stats_match_id ON minute_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_minute_stats_minute ON minute_stats(minute);

CREATE INDEX IF NOT EXISTS idx_player_match_stats_match ON player_match_stats(match_id);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_player ON player_match_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_player_match_stats_team ON player_match_stats(team_id);

CREATE INDEX IF NOT EXISTS idx_processing_log_job_type ON processing_log(job_type);
CREATE INDEX IF NOT EXISTS idx_processing_log_status ON processing_log(status);
CREATE INDEX IF NOT EXISTS idx_processing_log_match_id ON processing_log(match_id);
CREATE INDEX IF NOT EXISTS idx_processing_log_started_at ON processing_log(started_at);

-- Add foreign key constraints with proper naming
ALTER TABLE matches ADD CONSTRAINT fk_matches_competition FOREIGN KEY (competition_id) REFERENCES competitions(id);
ALTER TABLE matches ADD CONSTRAINT fk_matches_home_team FOREIGN KEY (home_team_id) REFERENCES teams(id);
ALTER TABLE matches ADD CONSTRAINT fk_matches_away_team FOREIGN KEY (away_team_id) REFERENCES teams(id);

-- Add check constraints for data quality
ALTER TABLE matches ADD CONSTRAINT chk_matches_score_positive CHECK (home_score >= 0 AND away_score >= 0);
ALTER TABLE matches ADD CONSTRAINT chk_matches_ht_score_positive CHECK (home_score_ht >= 0 AND away_score_ht >= 0);
ALTER TABLE matches ADD CONSTRAINT chk_matches_current_minute CHECK (current_minute >= 0 AND current_minute <= 150);
ALTER TABLE matches ADD CONSTRAINT chk_matches_importance CHECK (importance >= 1 AND importance <= 5);

ALTER TABLE events ADD CONSTRAINT chk_events_minute CHECK (minute >= 0 AND minute <= 150);
ALTER TABLE events ADD CONSTRAINT chk_events_coordinates CHECK (
    (x_coordinate IS NULL OR (x_coordinate >= 0 AND x_coordinate <= 100)) AND
    (y_coordinate IS NULL OR (y_coordinate >= 0 AND y_coordinate <= 100))
);
ALTER TABLE events ADD CONSTRAINT chk_events_xg CHECK (xg_value >= 0 AND xg_value <= 1);

ALTER TABLE minute_stats ADD CONSTRAINT chk_minute_stats_minute CHECK (minute >= 0 AND minute <= 150);
ALTER TABLE minute_stats ADD CONSTRAINT chk_minute_stats_possession CHECK (
    (home_possession IS NULL OR (home_possession >= 0 AND home_possession <= 100)) AND
    (away_possession IS NULL OR (away_possession >= 0 AND away_possession <= 100))
);

ALTER TABLE lineups ADD CONSTRAINT chk_lineups_minutes CHECK (
    minute_in >= 0 AND (minute_out IS NULL OR minute_out > minute_in)
);

ALTER TABLE player_match_stats ADD CONSTRAINT chk_player_stats_rating CHECK (
    rating IS NULL OR (rating >= 0 AND rating <= 10)
);

-- Add comments for documentation
COMMENT ON TABLE competitions IS 'Normalized competition/tournament data';
COMMENT ON TABLE teams IS 'Normalized team data with metadata';
COMMENT ON TABLE players IS 'Normalized player data with basic information';
COMMENT ON TABLE matches IS 'Normalized match data extracted from raw JSON';
COMMENT ON TABLE lineups IS 'Starting lineups and substitutions for each match';
COMMENT ON TABLE events IS 'Match events (goals, cards, subs) with coordinates and xG';
COMMENT ON TABLE minute_stats IS 'Minute-by-minute match statistics';
COMMENT ON TABLE player_match_stats IS 'Individual player statistics per match';
COMMENT ON TABLE processing_log IS 'Log of data processing jobs and their status';

-- Apply updated_at triggers to curated tables
CREATE TRIGGER update_competitions_updated_at BEFORE UPDATE ON competitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_players_updated_at BEFORE UPDATE ON players FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_matches_updated_at BEFORE UPDATE ON matches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_processing_log_updated_at BEFORE UPDATE ON processing_log FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE OR REPLACE VIEW live_matches AS
SELECT 
    m.*,
    hc.name as home_team_name,
    ac.name as away_team_name,
    comp.name as competition_name
FROM matches m
JOIN teams hc ON m.home_team_id = hc.id
JOIN teams ac ON m.away_team_id = ac.id
JOIN competitions comp ON m.competition_id = comp.id
WHERE m.is_live = true;

CREATE OR REPLACE VIEW recent_matches AS
SELECT 
    m.*,
    hc.name as home_team_name,
    ac.name as away_team_name,
    comp.name as competition_name
FROM matches m
JOIN teams hc ON m.home_team_id = hc.id
JOIN teams ac ON m.away_team_id = ac.id
JOIN competitions comp ON m.competition_id = comp.id
WHERE m.match_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY m.match_date DESC;