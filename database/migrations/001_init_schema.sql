-- ============================================
-- SPORTS BETTING MODEL DATABASE SCHEMA
-- Initial Migration - v001
-- Railway PostgreSQL Setup
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. CORE TABLES
-- ============================================

CREATE TABLE teams (
    team_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport VARCHAR(50) NOT NULL,
    team_name VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    conference VARCHAR(50),
    division VARCHAR(50),
    abbreviation VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sport, team_name)
);

CREATE TABLE players (
    player_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport VARCHAR(50) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    team_id UUID REFERENCES teams(team_id),
    position VARCHAR(50),
    jersey_number INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    date_of_birth DATE,
    height_inches INTEGER,
    weight_pounds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE games (
    game_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sport VARCHAR(50) NOT NULL,
    home_team_id UUID REFERENCES teams(team_id),
    away_team_id UUID REFERENCES teams(team_id),
    game_date DATE NOT NULL,
    game_time TIME,
    venue VARCHAR(200),
    game_status VARCHAR(50) DEFAULT 'scheduled',
    home_score INTEGER,
    away_score INTEGER,
    season VARCHAR(20),
    week INTEGER,
    playoff_game BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. PROPOSITION DATA
-- ============================================

CREATE TABLE underdog_props (
    prop_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID REFERENCES games(game_id),
    player_id UUID REFERENCES players(player_id),
    sport VARCHAR(50) NOT NULL,
    stat_type VARCHAR(100) NOT NULL,
    line_value DECIMAL(10, 2) NOT NULL,
    higher_payout DECIMAL(10, 2),
    lower_payout DECIMAL(10, 2),
    prop_status VARCHAR(50) DEFAULT 'open',
    result_value DECIMAL(10, 2),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_underdog_props_player ON underdog_props(player_id, game_id);
CREATE INDEX idx_underdog_props_sport_stat ON underdog_props(sport, stat_type);

-- Migration completed
SELECT 'Migration 001 completed successfully' AS status;
