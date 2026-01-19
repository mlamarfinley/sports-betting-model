"""Configuration for Anti-Recency Bias Analysis Framework v3.0"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

class Sport(Enum):
    NBA = "nba"
    NFL = "nfl"
    NHL = "nhl"
    CFB = "cfb"
    TENNIS = "tennis"
    SOCCER = "soccer"
    LOL = "lol"
    CS2 = "cs2"

@dataclass
class WeightingConfig:
    """CORE PRINCIPLE: Full season baseline is PRIMARY ANCHOR (50-60%)"""
    season_baseline_weight: float = 0.55
    historical_matchup_weight: float = 0.15
    defensive_tier_weight: float = 0.12
    recent_form_weight: float = 0.13
    trend_validation_weight: float = 0.05
    recent_form_games: int = 5
    trend_validation_games: int = 3
    std_dev_threshold: float = 2.0
    variance_percentage_threshold: float = 0.25
