-- ============================================
-- SPORT-SPECIFIC STAT TABLES
-- Migration v002 - Isolated stat tracking per sport
-- Ensures NO cross-contamination between sports
-- ============================================

-- ============================================
-- NBA BASKETBALL STATS (ONLY)
-- ============================================
CREATE TABLE nba_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- NBA-specific stats ONLY
    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,
    turnovers INTEGER,
    three_pointers_made INTEGER,
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    free_throws_made INTEGER,
    free_throws_attempted INTEGER,
    minutes_played DECIMAL(5,2),
    plus_minus INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_nba_stats_player_game ON nba_player_stats(player_id, game_id);

-- ============================================
-- NFL FOOTBALL STATS (ONLY)
-- ============================================
CREATE TABLE nfl_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- NFL-specific stats ONLY
    -- Passing
    passing_yards INTEGER,
    passing_touchdowns INTEGER,
    interceptions INTEGER,
    completions INTEGER,
    pass_attempts INTEGER,
    
    -- Rushing
    rushing_yards INTEGER,
    rushing_touchdowns INTEGER,
    rushing_attempts INTEGER,
    
    -- Receiving
    receptions INTEGER,
    receiving_yards INTEGER,
    receiving_touchdowns INTEGER,
    targets INTEGER,
    
    -- Defense
    tackles INTEGER,
    sacks DECIMAL(4,1),
    forced_fumbles INTEGER,
    
    -- Special Teams
    field_goals_made INTEGER,
    field_goals_attempted INTEGER,
    
    -- Football-specific
    snap_count INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_nfl_stats_player_game ON nfl_player_stats(player_id, game_id);

-- ============================================
-- NHL HOCKEY STATS (ONLY)
-- ============================================
CREATE TABLE nhl_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- NHL-specific stats ONLY
    goals INTEGER,
    assists INTEGER,
    points INTEGER,
    shots_on_goal INTEGER,
    plus_minus INTEGER,
    penalty_minutes INTEGER,
    power_play_goals INTEGER,
    short_handed_goals INTEGER,
    game_winning_goals INTEGER,
    time_on_ice DECIMAL(5,2),
    
    -- Goalie stats
    saves INTEGER,
    goals_against INTEGER,
    save_percentage DECIMAL(5,3),
    shutouts INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_nhl_stats_player_game ON nhl_player_stats(player_id, game_id);

-- ============================================
-- COLLEGE FOOTBALL STATS (ONLY)
-- ============================================
CREATE TABLE cfb_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- Same as NFL structure but separate table
    passing_yards INTEGER,
    passing_touchdowns INTEGER,
    interceptions INTEGER,
    rushing_yards INTEGER,
    rushing_touchdowns INTEGER,
    rushing_attempts INTEGER,
    receptions INTEGER,
    receiving_yards INTEGER,
    receiving_touchdowns INTEGER,
    targets INTEGER,
    tackles INTEGER,
    sacks DECIMAL(4,1),
    snap_count INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_cfb_stats_player_game ON cfb_player_stats(player_id, game_id);

-- ============================================
-- TENNIS STATS (ONLY)
-- ============================================
CREATE TABLE tennis_match_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- Tennis-specific stats ONLY
    aces INTEGER,
    double_faults INTEGER,
    first_serve_percentage DECIMAL(5,2),
    first_serve_points_won INTEGER,
    second_serve_points_won INTEGER,
    break_points_faced INTEGER,
    break_points_saved INTEGER,
    service_games_played INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_tennis_stats_player_game ON tennis_match_stats(player_id, game_id);

-- ============================================
-- SOCCER STATS (ONLY)
-- ============================================
CREATE TABLE soccer_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- Soccer-specific stats ONLY
    goals INTEGER,
    assists INTEGER,
    shots_on_target INTEGER,
    shots_total INTEGER,
    passes_completed INTEGER,
    pass_attempts INTEGER,
    tackles INTEGER,
    interceptions INTEGER,
    fouls_committed INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    minutes_played INTEGER,
    
    -- Goalkeeper stats
    saves INTEGER,
    goals_conceded INTEGER,
    clean_sheets INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_soccer_stats_player_game ON soccer_player_stats(player_id, game_id);

-- ============================================
-- LEAGUE OF LEGENDS (ESPORTS) STATS (ONLY)
-- ============================================
CREATE TABLE lol_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- LoL-specific stats ONLY
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    creep_score INTEGER,
    gold_earned INTEGER,
    damage_dealt INTEGER,
    damage_taken INTEGER,
    wards_placed INTEGER,
    wards_destroyed INTEGER,
    champion_played VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_lol_stats_player_game ON lol_player_stats(player_id, game_id);

-- ============================================
-- COUNTER-STRIKE 2 (ESPORTS) STATS (ONLY)
-- ============================================
CREATE TABLE cs2_player_stats (
    stat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    player_id UUID REFERENCES players(player_id),
    game_id UUID REFERENCES games(game_id),
    
    -- CS2-specific stats ONLY
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    headshot_percentage DECIMAL(5,2),
    adr DECIMAL(6,2), -- Average Damage per Round
    kast_percentage DECIMAL(5,2), -- Kill, Assist, Survive, Trade %
    rating DECIMAL(4,2),
    clutches_won INTEGER,
    first_kills INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

CREATE INDEX idx_cs2_stats_player_game ON cs2_player_stats(player_id, game_id);

-- Migration completed
SELECT 'Migration 002 completed - Sport-specific stats tables created with proper isolation' AS status;
