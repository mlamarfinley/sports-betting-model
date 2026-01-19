"""Core Analysis Engine - Anti-Recency Bias Methodology v3.0

Implements the full-season baseline analysis workflow for sports betting
prop predictions. CORE PRINCIPLE: Full season baseline (50-60%) is the
PRIMARY ANCHOR. Recent performance only adjusts baseline when there's
a sustainable, identifiable reason (injury, scheme change, etc.).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class PropDirection(Enum):
    OVER = "over"
    UNDER = "under"
    NEUTRAL = "neutral"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


@dataclass
class BaselineData:
    """Season baseline statistics"""
    mean: float
    median: float
    std_dev: float
    floor: float  # 10th percentile
    ceiling: float  # 90th percentile
    sample_size: int


@dataclass
class WeightedProjection:
    """Final weighted projection result"""
    player_id: int
    prop_type: str
    prop_line: float
    season_baseline: float
    final_projection: float
    edge_percentage: float
    confidence_level: str
    recommended_play: Optional[str]
    weights_applied: Dict[str, float] = field(default_factory=dict)
    historical_matchup: Optional[float] = None
    defensive_tier: Optional[float] = None
    recent_form: Optional[float] = None
    trend: Optional[float] = None
    floor: Optional[float] = None
    ceiling: Optional[float] = None


class AntiRecencyEngine:
    """Core analysis engine for prop prediction with recency bias mitigation"""

    def __init__(self, season_baseline_weight=0.55, recent_form_weight=0.13):
        self.season_baseline_weight = season_baseline_weight
        self.recent_form_weight = recent_form_weight
        self.recent_games = 5
        self.trend_games = 3

    def analyze_prop(self,
                     player_id: int,
                     prop_type: str,
                     prop_line: float,
                     game_values: List[float],
                     opponent_tier: int = 3) -> WeightedProjection:
        """Analyze a prop using the full anti-recency methodology"""

        # Phase 1: Calculate season baseline (PRIMARY ANCHOR)
        baseline = self._calculate_baseline(game_values)

        # Phase 4: Analyze recent form with bias detection
        recent_mean = np.mean(game_values[-self.recent_games:])
        recent_std = np.std(game_values)

        # Check if recent performance is an outlier
        z_score = abs((recent_mean - baseline.mean) / baseline.std_dev) if baseline.std_dev > 0 else 0
        is_outlier = z_score > 2.0

        # If recent is outlier but baseline is stable, trust baseline
        if is_outlier:
            adjusted_recent = baseline.mean  # Regress to mean
        else:
            adjusted_recent = recent_mean

        # Phase 5: Trend validation
        trend_mean = np.mean(game_values[-self.trend_games:])
        trend_direction = 1 if trend_mean > baseline.mean else -1

        # Weighted synthesis
        final_projection = (
            baseline.mean * self.season_baseline_weight +
            adjusted_recent * self.recent_form_weight +
            trend_mean * 0.05 +
            baseline.mean * (1 - self.season_baseline_weight - self.recent_form_weight - 0.05)
        )

        # Calculate edge
        edge = ((final_projection - prop_line) / prop_line) * 100 if prop_line > 0 else 0

        # Determine recommendation
        recommended_play = None
        if abs(edge) > 5:
            recommended_play = "OVER" if edge > 0 else "UNDER"

        confidence_level = self._assess_confidence(len(game_values), abs(edge), is_outlier)

        return WeightedProjection(
            player_id=player_id,
            prop_type=prop_type,
            prop_line=prop_line,
            season_baseline=baseline.mean,
            final_projection=final_projection,
            edge_percentage=edge,
            confidence_level=confidence_level,
            recommended_play=recommended_play,
            floor=baseline.floor,
            ceiling=baseline.ceiling,
            weights_applied={
                'baseline': self.season_baseline_weight,
                'recent': self.recent_form_weight,
                'trend': 0.05
            }
        )

    def _calculate_baseline(self, values: List[float]) -> BaselineData:
        """Calculate season baseline - Phase 1"""
        arr = np.array(values)
        return BaselineData(
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            std_dev=float(np.std(arr, ddof=1)),
            floor=float(np.percentile(arr, 10)),
            ceiling=float(np.percentile(arr, 90)),
            sample_size=len(values)
        )

    def _assess_confidence(self, sample_size: int, edge: float, is_outlier: bool) -> str:
        """Assess confidence level"""
        if sample_size < 5:
            return ConfidenceLevel.INSUFFICIENT.value
        if is_outlier or edge < 3:
            return ConfidenceLevel.LOW.value
        if sample_size >= 10 and edge > 8:
            return ConfidenceLevel.HIGH.value
        return ConfidenceLevel.MEDIUM.value
