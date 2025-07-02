-- Migration 001: Create raw data tables for SofaScore pipeline
-- These tables store JSON blobs exactly as delivered by SofaScore

-- Extension for JSON operations and UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Raw matches data table
CREATE TABLE IF NOT EXISTS matches_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    endpoint VARCHAR(50) NOT NULL, -- 'feed', 'events', 'stats', 'momentum'
    raw_json JSONB NOT NULL,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure uniqueness per match, endpoint, and scrape time
    UNIQUE(match_id, endpoint, scrape_timestamp)
);

-- Raw events data table (separate for better performance)
CREATE TABLE IF NOT EXISTS events_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_events_json JSONB NOT NULL,
    event_count INTEGER,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(match_id, scrape_timestamp)
);

-- Raw statistics data table (minute-by-minute)
CREATE TABLE IF NOT EXISTS stats_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    minute SMALLINT, -- NULL for full-match stats
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_stats_json JSONB NOT NULL,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw momentum data table
CREATE TABLE IF NOT EXISTS momentum_raw (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id BIGINT NOT NULL,
    scrape_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    raw_momentum_json JSONB NOT NULL,
    data_points_count INTEGER,
    http_status INTEGER DEFAULT 200,
    scrape_duration_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scrape metadata table to track scraping jobs
CREATE TABLE IF NOT EXISTS scrape_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(100) NOT NULL,
    match_id BIGINT,
    job_type VARCHAR(50) NOT NULL, -- 'live', 'finished', 'bulk'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_raw_match_id ON matches_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_raw_scrape_timestamp ON matches_raw(scrape_timestamp);
CREATE INDEX IF NOT EXISTS idx_matches_raw_endpoint ON matches_raw(endpoint);
CREATE INDEX IF NOT EXISTS idx_matches_raw_match_endpoint ON matches_raw(match_id, endpoint);

CREATE INDEX IF NOT EXISTS idx_events_raw_match_id ON events_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_events_raw_scrape_timestamp ON events_raw(scrape_timestamp);

CREATE INDEX IF NOT EXISTS idx_stats_raw_match_id ON stats_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_stats_raw_minute ON stats_raw(minute);
CREATE INDEX IF NOT EXISTS idx_stats_raw_scrape_timestamp ON stats_raw(scrape_timestamp);
CREATE INDEX IF NOT EXISTS idx_stats_raw_match_minute ON stats_raw(match_id, minute);

CREATE INDEX IF NOT EXISTS idx_momentum_raw_match_id ON momentum_raw(match_id);
CREATE INDEX IF NOT EXISTS idx_momentum_raw_scrape_timestamp ON momentum_raw(scrape_timestamp);

CREATE INDEX IF NOT EXISTS idx_scrape_jobs_match_id ON scrape_jobs(match_id);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_job_type ON scrape_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_scrape_jobs_started_at ON scrape_jobs(started_at);

-- JSONB indexes for common queries
CREATE INDEX IF NOT EXISTS idx_matches_raw_json_competition ON matches_raw USING GIN ((raw_json->'tournament'));
CREATE INDEX IF NOT EXISTS idx_matches_raw_json_status ON matches_raw USING GIN ((raw_json->'status'));
CREATE INDEX IF NOT EXISTS idx_events_raw_json_incidents ON events_raw USING GIN (raw_events_json);
CREATE INDEX IF NOT EXISTS idx_stats_raw_json_stats ON stats_raw USING GIN (raw_stats_json);

-- Add comments for documentation
COMMENT ON TABLE matches_raw IS 'Raw JSON data from SofaScore match feed endpoint';
COMMENT ON TABLE events_raw IS 'Raw JSON data from SofaScore events/incidents endpoint';
COMMENT ON TABLE stats_raw IS 'Raw JSON data from SofaScore statistics endpoint';
COMMENT ON TABLE momentum_raw IS 'Raw JSON data from SofaScore momentum endpoint';
COMMENT ON TABLE scrape_jobs IS 'Metadata for tracking scraping jobs and their status';

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_matches_raw_updated_at BEFORE UPDATE ON matches_raw FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_events_raw_updated_at BEFORE UPDATE ON events_raw FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_stats_raw_updated_at BEFORE UPDATE ON stats_raw FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_momentum_raw_updated_at BEFORE UPDATE ON momentum_raw FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scrape_jobs_updated_at BEFORE UPDATE ON scrape_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();