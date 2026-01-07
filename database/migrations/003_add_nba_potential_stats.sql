-- =====================================================
-- ADD POTENTIAL ASSISTS AND REBOUNDS TO NBA STATS
-- Migration v003 - Adds advanced tracking metrics
-- =====================================================

-- Potential assists: number of times a player passed to a teammate
-- who attempted a shot (regardless of make/miss)
-- Potential rebounds: rebounding opportunities based on positioning

ALTER TABLE nba_player_stats
    ADD COLUMN potential_assists INTEGER,
    ADD COLUMN potential_rebounds INTEGER;
