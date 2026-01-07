-- Migration: Add period-based stat tracking
-- Adds support for tracking stats by game periods (quarters, halves, periods)
-- This allows analysis of performance patterns throughout games

-- Add period column to NBA stats
ALTER TABLE nba_player_stats ADD COLUMN period INTEGER;
ALTER TABLE nba_player_stats ADD COLUMN period_label VARCHAR(20);

-- Add period column to NFL stats  
ALTER TABLE nfl_player_stats ADD COLUMN period INTEGER;
ALTER TABLE nfl_player_stats ADD COLUMN period_label VARCHAR(20);

-- Add period column to NHL stats
ALTER TABLE nhl_player_stats ADD COLUMN period INTEGER;
ALTER TABLE nhl_player_stats ADD COLUMN period_label VARCHAR(20);

-- Add period column to college football stats
ALTER TABLE cfb_player_stats ADD COLUMN period INTEGER;
ALTER TABLE cfb_player_stats ADD COLUMN period_label VARCHAR(20);

-- Add period column to college basketball stats
ALTER TABLE cbb_player_stats ADD COLUMN period INTEGER;
ALTER TABLE cbb_player_stats ADD COLUMN period_label VARCHAR(20);

-- Add comments explaining the period tracking system
COMMENT ON COLUMN nba_player_stats.period IS 'Quarter number (1-4, 5+ for OT). NULL = full game stats';
COMMENT ON COLUMN nba_player_stats.period_label IS 'Human-readable period (Q1, Q2, Q3, Q4, OT1, etc.)';

COMMENT ON COLUMN nfl_player_stats.period IS 'Quarter number (1-4, 5+ for OT). NULL = full game stats';
COMMENT ON COLUMN nfl_player_stats.period_label IS 'Human-readable period (Q1, Q2, Q3, Q4, OT, etc.)';

COMMENT ON COLUMN nhl_player_stats.period IS 'Period number (1-3, 4+ for OT). NULL = full game stats';
COMMENT ON COLUMN nhl_player_stats.period_label IS 'Human-readable period (P1, P2, P3, OT, SO, etc.)';

COMMENT ON COLUMN cfb_player_stats.period IS 'Quarter number (1-4, 5+ for OT). NULL = full game stats';
COMMENT ON COLUMN cfb_player_stats.period_label IS 'Human-readable period (Q1, Q2, Q3, Q4, OT, etc.)';

COMMENT ON COLUMN cbb_player_stats.period IS 'Half number (1-2, 3+ for OT). NULL = full game stats';
COMMENT ON COLUMN cbb_player_stats.period_label IS 'Human-readable period (H1, H2, OT1, etc.)';

-- Create indexes for efficient period-based queries
CREATE INDEX idx_nba_stats_period ON nba_player_stats(game_id, player_id, period);
CREATE INDEX idx_nfl_stats_period ON nfl_player_stats(game_id, player_id, period);
CREATE INDEX idx_nhl_stats_period ON nhl_player_stats(game_id, player_id, period);
CREATE INDEX idx_cfb_stats_period ON cfb_player_stats(game_id, player_id, period);
CREATE INDEX idx_cbb_stats_period ON cbb_player_stats(game_id, player_id, period);

-- Notes:
-- period = NULL means full game aggregate stats
-- period = 1,2,3,4 for quarters/halves/periods
-- period = 5+ for overtime periods
-- period_label provides human-readable format for display
