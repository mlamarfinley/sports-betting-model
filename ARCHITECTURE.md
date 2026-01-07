# Sports Betting Model - Architecture Documentation

## Overview
This is a multi-sport betting prediction model with isolated data pipelines for each sport to ensure NO cross-contamination of stats between different sports.

## Core Principles

### 1. **Sport-Specific Isolation**
- Each sport has its OWN dedicated stat table
- NO shared statistics between sports
- Database constraints enforce sport-specific data integrity
- Independent scrapers and model logic per sport

### 2. **No Cross-Contamination**
**WRONG Examples (What We PREVENT):**
- ❌ Snap count appearing in basketball stats
- ❌ Kills (esports) appearing in football stats  
- ❌ Rebounds appearing in hockey stats
- ❌ Aces (tennis) appearing in soccer stats

**RIGHT Approach (What We IMPLEMENT):**
- ✅ Snap count ONLY in `nfl_player_stats` and `cfb_player_stats`
- ✅ Kills ONLY in `lol_player_stats` and `cs2_player_stats`
- ✅ Rebounds ONLY in `nba_player_stats`
- ✅ Aces ONLY in `tennis_match_stats`

## Database Architecture

### Core Tables (Shared)
These tables are shared across all sports but maintain sport identification:

#### `teams`
```sql
- team_id (UUID, PK)
- sport (VARCHAR) -- 'NBA', 'NFL', 'NHL', etc.
- team_name
- city, conference, division
```

#### `players`
```sql
- player_id (UUID, PK)
- sport (VARCHAR) -- Links to specific sport
- full_name
- team_id (FK to teams)
- position
```

#### `games`
```sql
- game_id (UUID, PK)
- sport (VARCHAR)
- home_team_id, away_team_id (FK to teams)
- game_date, game_time
- game_status
```

#### `underdog_props`
```sql
- prop_id (UUID, PK)
- game_id, player_id
- sport (VARCHAR)
- stat_type -- The type of prop (e.g., "points", "rushing_yards")
- line_value
- higher_payout, lower_payout
```

### Sport-Specific Stat Tables
These tables are COMPLETELY ISOLATED per sport:

#### `nba_player_stats` (Basketball ONLY)
```sql
Stats: points, rebounds, assists, steals, blocks, turnovers,
       three_pointers_made, field_goals, minutes_played, plus_minus
       
CONSTRAINT: player_id must be from players WHERE sport = 'NBA'
```

#### `nfl_player_stats` (Football ONLY)
```sql
Stats: passing_yards, passing_touchdowns, interceptions,
       rushing_yards, rushing_touchdowns, rushing_attempts,
       receptions, receiving_yards, targets,
       tackles, sacks, snap_count (FOOTBALL SPECIFIC)
       
CONSTRAINT: player_id must be from players WHERE sport = 'NFL'
```

#### `nhl_player_stats` (Hockey ONLY)
```sql
Stats: goals, assists, points, shots_on_goal, plus_minus,
       penalty_minutes, power_play_goals, time_on_ice,
       saves (goalies), save_percentage
       
CONSTRAINT: player_id must be from players WHERE sport = 'NHL'
```

#### `cfb_player_stats` (College Football ONLY)
```sql
Same structure as NFL but separate table for college players
CONSTRAINT: player_id must be from players WHERE sport = 'CFB'
```

#### `tennis_match_stats` (Tennis ONLY)
```sql
Stats: aces, double_faults, first_serve_percentage,
       break_points_saved, service_games_played
       
CONSTRAINT: player_id must be from players WHERE sport = 'TENNIS'
```

#### `soccer_player_stats` (Soccer ONLY)
```sql
Stats: goals, assists, shots_on_target, passes_completed,
       tackles, fouls_committed, yellow_cards, red_cards,
       saves (goalkeepers), clean_sheets
       
CONSTRAINT: player_id must be from players WHERE sport = 'SOCCER'
```

#### `lol_player_stats` (League of Legends ONLY)
```sql
Stats: kills, deaths, assists, creep_score, gold_earned,
       damage_dealt, wards_placed, champion_played
       
CONSTRAINT: player_id must be from players WHERE sport = 'LOL'
```

#### `cs2_player_stats` (Counter-Strike 2 ONLY)
```sql
Stats: kills, deaths, assists, headshot_percentage, adr,
       kast_percentage, rating, clutches_won, first_kills
       
CONSTRAINT: player_id must be from players WHERE sport = 'CS2'
```

## Data Flow Architecture

### Independent Pipelines Per Sport
```
┌─────────────────────────────────────────────────────────────┐
│                    SPORTS BETTING MODEL                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ NBA Pipeline │   │ NFL Pipeline │   │ NHL Pipeline │
└──────────────┘   └──────────────┘   └──────────────┘
      ↓                   ↓                   ↓
   Scraper             Scraper             Scraper
      ↓                   ↓                   ↓
nba_player_stats   nfl_player_stats   nhl_player_stats
      ↓                   ↓                   ↓
  NBA Model           NFL Model           NHL Model
      ↓                   ↓                   ↓
 NBA Predictions    NFL Predictions    NHL Predictions

┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ CFB Pipeline │   │Tennis Pipeline│  │Soccer Pipeline│
└──────────────┘   └──────────────┘   └──────────────┘
      ↓                   ↓                   ↓
   Scraper             Scraper             Scraper
      ↓                   ↓                   ↓
cfb_player_stats   tennis_match_stats soccer_player_stats
      ↓                   ↓                   ↓
  CFB Model          Tennis Model        Soccer Model
      ↓                   ↓                   ↓
 CFB Predictions   Tennis Predictions Soccer Predictions

┌──────────────┐   ┌──────────────┐
│ LoL Pipeline │   │ CS2 Pipeline │
└──────────────┘   └──────────────┘
      ↓                   ↓
   Scraper             Scraper
      ↓                   ↓
lol_player_stats    cs2_player_stats
      ↓                   ↓
  LoL Model           CS2 Model
      ↓                   ↓
 LoL Predictions    CS2 Predictions
```

### Each Pipeline is INDEPENDENT
1. **Scraper** - Fetches sport-specific data from sources
2. **Parser** - Validates and structures data for that sport ONLY
3. **Database Insert** - Writes to sport-specific stat table
4. **Model** - Uses ONLY relevant features for that sport
5. **Predictions** - Generates predictions for that sport's props

## Infrastructure

### Technology Stack
- **Database**: PostgreSQL on Railway
- **Backend**: Python (scrapers, models)
- **Frontend**: Lovable (web dashboard)
- **Deployment**: Railway (services + database)

### Railway Setup
- PostgreSQL Database (deployed)
- Migration scripts in `database/migrations/`
- Separate services for each sport's scraper (future)
- API service for model predictions (future)

## Model Strategy

### Sport-Specific Feature Engineering
Each sport uses ONLY features relevant to its stats:

**NBA Model Features (Example):**
- Recent points per game avg
- vs. team defensive rating
- vs. position defensive rating
- Home/away splits
- Minutes played trend
- **NO football stats, NO hockey stats**

**NFL Model Features (Example):**
- Recent rushing yards per game
- vs. team rush defense ranking
- Snap count percentage
- Game script (pass-heavy vs run-heavy)
- **NO basketball stats, NO esports stats**

### Underdog Prop Type Mapping
Each sport has specific prop types tracked:

**NBA**: Points, Rebounds, Assists, 3PM, Blocks, Steals, PRA, PR, PA
**NFL**: Passing Yards, Rushing Yards, Receptions, TDs, Tackles, Sacks
**NHL**: Goals, Assists, Points, Shots, Saves
**Tennis**: Aces, Games Won, Sets Won
**Soccer**: Goals, Shots on Target, Tackles
**LoL**: Kills, Deaths, Assists, CS
**CS2**: Kills, Deaths, ADR, Rating

## Development Guidelines

### When Adding New Features
1. ✅ Identify which sport(s) the feature applies to
2. ✅ Add column to the CORRECT sport-specific table ONLY
3. ✅ Update scraper for that sport ONLY
4. ✅ Update model for that sport ONLY
5. ❌ NEVER add football stats to basketball tables
6. ❌ NEVER share stat columns across multiple sport tables

### Testing Isolation
- Test each sport's pipeline independently
- Verify CHECK constraints prevent wrong sport data
- Ensure scrapers don't pull irrelevant stats
- Validate models don't access other sports' tables

## Conclusion
This architecture ensures complete isolation between sports, preventing any possibility of cross-contamination. Each sport operates as an independent system while sharing core infrastructure like teams, players, and games tables.
