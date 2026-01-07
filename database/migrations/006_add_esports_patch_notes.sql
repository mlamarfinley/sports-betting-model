-- Migration: Add esports patch notes tracking
-- Implements automatic patch note monitoring for LoL, CS2, and CoD
-- Tracks champion/agent/weapon changes, meta shifts, and balance updates

-- =================================================================
-- PATCH NOTES MASTER TABLE
-- =================================================================
CREATE TABLE patch_notes (
    id SERIAL PRIMARY KEY,
    game VARCHAR(50) NOT NULL, -- 'LoL', 'CS2', 'CoD'
    patch_version VARCHAR(50) NOT NULL,
    patch_name VARCHAR(200),
    release_date DATE NOT NULL,
    official_url TEXT,
    
    -- Scraping metadata
    scraped_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    scrape_source VARCHAR(200), -- URL of source
    
    -- Patch categorization
    is_major_patch BOOLEAN DEFAULT FALSE,
    is_hotfix BOOLEAN DEFAULT FALSE,
    patch_notes_text TEXT, -- Full raw text
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(game, patch_version)
);

CREATE INDEX idx_patch_notes_game ON patch_notes(game);
CREATE INDEX idx_patch_notes_date ON patch_notes(release_date);
CREATE INDEX idx_patch_notes_game_date ON patch_notes(game, release_date DESC);

-- =================================================================
-- LEAGUE OF LEGENDS CHAMPION CHANGES
-- =================================================================
CREATE TABLE lol_champion_changes (
    id SERIAL PRIMARY KEY,
    patch_id INTEGER NOT NULL REFERENCES patch_notes(id) ON DELETE CASCADE,
    champion_name VARCHAR(100) NOT NULL,
    
    -- Change categorization
    change_type VARCHAR(50), -- 'buff', 'nerf', 'adjustment', 'rework', 'new'
    ability_affected VARCHAR(50), -- 'passive', 'Q', 'W', 'E', 'R', 'stats'
    
    -- Change details
    change_summary TEXT,
    previous_value VARCHAR(200),
    new_value VARCHAR(200),
    
    -- Impact assessment (can be updated by model)
    estimated_impact VARCHAR(20), -- 'major', 'moderate', 'minor'
    affects_pro_meta BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_lol_changes_patch ON lol_champion_changes(patch_id);
CREATE INDEX idx_lol_changes_champion ON lol_champion_changes(champion_name);
CREATE INDEX idx_lol_changes_type ON lol_champion_changes(change_type);

-- =================================================================
-- COUNTER-STRIKE 2 CHANGES
-- =================================================================
CREATE TABLE cs2_patch_changes (
    id SERIAL PRIMARY KEY,
    patch_id INTEGER NOT NULL REFERENCES patch_notes(id) ON DELETE CASCADE,
    
    -- Change category
    change_category VARCHAR(50), -- 'weapon', 'agent', 'map', 'economy', 'mechanic'
    item_name VARCHAR(100), -- weapon/agent/map name
    
    -- Change details
    change_type VARCHAR(50), -- 'buff', 'nerf', 'fix', 'new', 'removed'
    change_summary TEXT,
    stat_affected VARCHAR(100), -- 'damage', 'fire_rate', 'recoil', 'price', etc.
    previous_value VARCHAR(200),
    new_value VARCHAR(200),
    
    -- Impact
    estimated_impact VARCHAR(20), -- 'major', 'moderate', 'minor'
    affects_economy BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cs2_changes_patch ON cs2_patch_changes(patch_id);
CREATE INDEX idx_cs2_changes_category ON cs2_patch_changes(change_category);
CREATE INDEX idx_cs2_changes_item ON cs2_patch_changes(item_name);

-- =================================================================
-- CALL OF DUTY CHANGES
-- =================================================================
CREATE TABLE cod_patch_changes (
    id SERIAL PRIMARY KEY,
    patch_id INTEGER NOT NULL REFERENCES patch_notes(id) ON DELETE CASCADE,
    
    -- Change category
    change_category VARCHAR(50), -- 'weapon', 'perk', 'scorestreak', 'map', 'mode'
    item_name VARCHAR(100),
    
    -- Change details
    change_type VARCHAR(50), -- 'buff', 'nerf', 'fix', 'new', 'removed'
    change_summary TEXT,
    stat_affected VARCHAR(100),
    previous_value VARCHAR(200),
    new_value VARCHAR(200),
    
    -- Impact
    estimated_impact VARCHAR(20), -- 'major', 'moderate', 'minor'
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cod_changes_patch ON cod_patch_changes(patch_id);
CREATE INDEX idx_cod_changes_category ON cod_patch_changes(change_category);
CREATE INDEX idx_cod_changes_item ON cod_patch_changes(item_name);

-- =================================================================
-- META ANALYSIS TABLE
-- =================================================================
CREATE TABLE esports_meta_analysis (
    id SERIAL PRIMARY KEY,
    game VARCHAR(50) NOT NULL,
    patch_id INTEGER REFERENCES patch_notes(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    
    -- Top picks/bans (JSON or array)
    top_champions_agents TEXT, -- JSON array of top picks
    ban_priorities TEXT, -- JSON array of commonly banned
    
    -- Meta shifts
    meta_description TEXT,
    playstyle_trends TEXT, -- 'aggressive', 'defensive', 'early game focused', etc.
    
    -- Model insights
    model_notes TEXT,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_meta_game ON esports_meta_analysis(game);
CREATE INDEX idx_meta_date ON esports_meta_analysis(analysis_date DESC);

-- =================================================================
-- PATCH SCRAPE LOG
-- =================================================================
CREATE TABLE patch_scrape_log (
    id SERIAL PRIMARY KEY,
    game VARCHAR(50) NOT NULL,
    scrape_timestamp TIMESTAMP DEFAULT NOW(),
    source_url TEXT,
    patches_found INTEGER DEFAULT 0,
    new_patches INTEGER DEFAULT 0,
    scrape_status VARCHAR(50), -- 'success', 'partial', 'failed'
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_scrape_log_game ON patch_scrape_log(game);
CREATE INDEX idx_scrape_log_time ON patch_scrape_log(scrape_timestamp DESC);

-- Add comments
COMMENT ON TABLE patch_notes IS 'Master table for all esports patch notes across LoL, CS2, and CoD';
COMMENT ON TABLE lol_champion_changes IS 'Detailed tracking of League of Legends champion balance changes';
COMMENT ON TABLE cs2_patch_changes IS 'Counter-Strike 2 weapon, agent, and map changes';
COMMENT ON TABLE cod_patch_changes IS 'Call of Duty weapon and gameplay changes';
COMMENT ON TABLE esports_meta_analysis IS 'High-level meta analysis and trends for each game';
COMMENT ON TABLE patch_scrape_log IS 'Logging table for automated patch scraping operations';
