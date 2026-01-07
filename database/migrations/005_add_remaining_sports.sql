-- Migration: Add remaining sports tables
-- Adds College Basketball, Tennis, Soccer, League of Legends, and Counter-Strike 2


-- Drop tables if they exist (for idempotency)
DROP TABLE IF EXISTS cbb_player_stats CASCADE;
DROP TABLE IF EXISTS tennis_match_stats CASCADE;
DROP TABLE IF EXISTS soccer_player_stats CASCADE;
DROP TABLE IF EXISTS lol_player_stats CASCADE;
DROP TABLE IF EXISTS cs2_player_stats CASCADE;
-- =================================================================
-- COLLEGE BASKETBALL (CBB)
-- =================================================================
CREATE TABLE cbb_player_stats (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    
    -- Period tracking (H1, H2, OT)
    period INTEGER,  -- 1=first half, 2=second half, 3+=overtime
    period_label VARCHAR(20),  -- 'H1', 'H2', 'OT1', etc.
    
    -- Basic stats
    minutes_played DECIMAL(5, 2),
    points INTEGER DEFAULT 0,
    field_goals_made INTEGER DEFAULT 0,
    field_goals_attempted INTEGER DEFAULT 0,
    three_pointers_made INTEGER DEFAULT 0,
    three_pointers_attempted INTEGER DEFAULT 0,
    free_throws_made INTEGER DEFAULT 0,
    free_throws_attempted INTEGER DEFAULT 0,
    offensive_rebounds INTEGER DEFAULT 0,
    defensive_rebounds INTEGER DEFAULT 0,
    total_rebounds INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    steals INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    personal_fouls INTEGER DEFAULT 0,
    
    -- Advanced stats
    plus_minus INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cbb_player_stats_game ON cbb_player_stats(game_id);
CREATE INDEX idx_cbb_player_stats_player ON cbb_player_stats(player_id);
CREATE INDEX idx_cbb_player_stats_team ON cbb_player_stats(team_id);
CREATE INDEX idx_cbb_stats_period ON cbb_player_stats(game_id, player_id, period);

-- =================================================================
-- TENNIS
-- =================================================================
CREATE TABLE tennis_match_stats (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    
    -- Set-by-set tracking
    set_number INTEGER,  -- 1-5 for best of 5, 1-3 for best of 3
    set_score VARCHAR(10),  -- '6-4', '7-6', etc.
    
    -- Match outcome
    won BOOLEAN,
    sets_won INTEGER DEFAULT 0,
    sets_lost INTEGER DEFAULT 0,
    
    -- Service stats
    aces INTEGER DEFAULT 0,
    double_faults INTEGER DEFAULT 0,
    first_serve_percentage DECIMAL(5, 2),
    first_serve_points_won INTEGER DEFAULT 0,
    first_serve_points_total INTEGER DEFAULT 0,
    second_serve_points_won INTEGER DEFAULT 0,
    second_serve_points_total INTEGER DEFAULT 0,
    break_points_saved INTEGER DEFAULT 0,
    break_points_faced INTEGER DEFAULT 0,
    service_games_played INTEGER DEFAULT 0,
    
    -- Return stats
    first_serve_return_won INTEGER DEFAULT 0,
    first_serve_return_total INTEGER DEFAULT 0,
    second_serve_return_won INTEGER DEFAULT 0,
    second_serve_return_total INTEGER DEFAULT 0,
    break_points_converted INTEGER DEFAULT 0,
    break_points_opportunities INTEGER DEFAULT 0,
    return_games_played INTEGER DEFAULT 0,
    
    -- Rally stats
    winners INTEGER DEFAULT 0,
    unforced_errors INTEGER DEFAULT 0,
    total_points_won INTEGER DEFAULT 0,
    total_points_played INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tennis_match_game ON tennis_match_stats(game_id);
CREATE INDEX idx_tennis_match_player ON tennis_match_stats(player_id);
CREATE INDEX idx_tennis_match_set ON tennis_match_stats(game_id, player_id, set_number);

-- =================================================================
-- SOCCER
-- =================================================================
CREATE TABLE soccer_player_stats (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    
    -- Period tracking (H1, H2, ET1, ET2 for extra time)
    period INTEGER,  -- 1=first half, 2=second half, 3=ET first half, 4=ET second half
    period_label VARCHAR(20),  -- 'H1', 'H2', 'ET1', 'ET2'
    
    -- Playing time
    minutes_played INTEGER DEFAULT 0,
    
    -- Scoring
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    
    -- Passing
    passes_completed INTEGER DEFAULT 0,
    passes_attempted INTEGER DEFAULT 0,
    pass_accuracy DECIMAL(5, 2),
    key_passes INTEGER DEFAULT 0,
    crosses INTEGER DEFAULT 0,
    
    -- Defending
    tackles INTEGER DEFAULT 0,
    tackles_won INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    clearances INTEGER DEFAULT 0,
    blocks INTEGER DEFAULT 0,
    
    -- Discipline
    fouls_committed INTEGER DEFAULT 0,
    fouls_won INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    
    -- Other
    offsides INTEGER DEFAULT 0,
    dribbles_attempted INTEGER DEFAULT 0,
    dribbles_successful INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_soccer_player_stats_game ON soccer_player_stats(game_id);
CREATE INDEX idx_soccer_player_stats_player ON soccer_player_stats(player_id);
CREATE INDEX idx_soccer_player_stats_team ON soccer_player_stats(team_id);
CREATE INDEX idx_soccer_stats_period ON soccer_player_stats(game_id, player_id, period);

-- =================================================================
-- LEAGUE OF LEGENDS
-- =================================================================
CREATE TABLE lol_player_stats (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    
    -- Champion and role
    champion VARCHAR(100),
    role VARCHAR(50),  -- Top, Jungle, Mid, ADC, Support
    
    -- Game outcome
    won BOOLEAN,
    game_duration_seconds INTEGER,
    
    -- KDA
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    
    -- Farm
    creep_score INTEGER DEFAULT 0,  -- CS
    cs_per_minute DECIMAL(5, 2),
    gold_earned INTEGER DEFAULT 0,
    
    -- Damage
    total_damage_dealt INTEGER DEFAULT 0,
    total_damage_to_champions INTEGER DEFAULT 0,
    total_damage_taken INTEGER DEFAULT 0,
    
    -- Vision
    wards_placed INTEGER DEFAULT 0,
    wards_destroyed INTEGER DEFAULT 0,
    vision_score INTEGER DEFAULT 0,
    
    -- Objectives
    turrets_destroyed INTEGER DEFAULT 0,
    inhibitors_destroyed INTEGER DEFAULT 0,
    dragons_taken INTEGER DEFAULT 0,
    barons_taken INTEGER DEFAULT 0,
    
    -- Combat
    largest_killing_spree INTEGER DEFAULT 0,
    largest_multi_kill INTEGER DEFAULT 0,
    first_blood BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lol_player_stats_game ON lol_player_stats(game_id);
CREATE INDEX idx_lol_player_stats_player ON lol_player_stats(player_id);
CREATE INDEX idx_lol_player_stats_team ON lol_player_stats(team_id);
CREATE INDEX idx_lol_player_stats_champion ON lol_player_stats(champion);
CREATE INDEX idx_lol_player_stats_role ON lol_player_stats(role);

-- =================================================================
-- COUNTER-STRIKE 2
-- =================================================================
CREATE TABLE cs2_player_stats (
    id SERIAL PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team_id UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    player_id UUID NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    
    -- Map and side
    map_name VARCHAR(100),
    side VARCHAR(10),  -- 'T' or 'CT'
    
    -- Game outcome
    won BOOLEAN,
    rounds_played INTEGER DEFAULT 0,
    
    -- Kills/Deaths
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    headshot_kills INTEGER DEFAULT 0,
    headshot_percentage DECIMAL(5, 2),
    
    -- Round impact
    first_kills INTEGER DEFAULT 0,
    first_deaths INTEGER DEFAULT 0,
    trade_kills INTEGER DEFAULT 0,
    clutch_wins INTEGER DEFAULT 0,
    
    -- Damage
    total_damage INTEGER DEFAULT 0,
    average_damage_per_round DECIMAL(7, 2),
    
    -- Utility
    utility_damage INTEGER DEFAULT 0,
    enemies_flashed INTEGER DEFAULT 0,
    teammates_flashed INTEGER DEFAULT 0,
    
    -- Economy
    money_spent INTEGER DEFAULT 0,
    equipment_value INTEGER DEFAULT 0,
    
    -- Advanced stats
    rating DECIMAL(5, 3),  -- HLTV-style rating
    kd_ratio DECIMAL(5, 2),
    adr DECIMAL(7, 2),  -- Average Damage per Round
    kast_percentage DECIMAL(5, 2),  -- Kill, Assist, Survive, Trade
    impact_rating DECIMAL(5, 3),
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cs2_player_stats_game ON cs2_player_stats(game_id);
CREATE INDEX idx_cs2_player_stats_player ON cs2_player_stats(player_id);
CREATE INDEX idx_cs2_player_stats_team ON cs2_player_stats(team_id);
CREATE INDEX idx_cs2_player_stats_map ON cs2_player_stats(map_name);

-- Add comments
COMMENT ON TABLE cbb_player_stats IS 'College basketball player statistics with half-by-half tracking';
COMMENT ON TABLE tennis_match_stats IS 'Tennis match statistics with set-by-set tracking';
COMMENT ON TABLE soccer_player_stats IS 'Soccer player statistics with half-by-half tracking';
COMMENT ON TABLE lol_player_stats IS 'League of Legends player statistics';
COMMENT ON TABLE cs2_player_stats IS 'Counter-Strike 2 player statistics with advanced metrics';
