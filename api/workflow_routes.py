"""Flask routes for Anti-Recency Bias Workflow API

Exposes the analysis engine through REST endpoints for prop analysis.
"""

from flask import Blueprint, request, jsonify
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Import the analysis engine
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models.anti_recency_engine import AntiRecencyEngine, PropDirection

# Create blueprint
workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/v1/workflow')

# Initialize engine
analysis_engine = AntiRecencyEngine(
    season_baseline_weight=0.55,
    recent_form_weight=0.13
)


@workflow_bp.route('/health', methods=['GET'])
def workflow_health():
    """Health check for workflow engine"""
    return jsonify({
        'status': 'healthy',
        'engine': 'AntiRecencyEngine v3.0',
        'methodology': 'Full-Season Baseline with Recency Bias Detection'
    })


@workflow_bp.route('/analyze-prop', methods=['POST'])
def analyze_prop():
    """Analyze a single prop using anti-recency methodology
    
    Request body:
    {
        "player_id": int,
        "prop_type": str,
        "prop_line": float,
        "game_values": [float],  # Historical values for player
        "opponent_tier": int  # 1-5 defense ranking
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['player_id', 'prop_type', 'prop_line', 'game_values']
        for field in required:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        player_id = data['player_id']
        prop_type = data['prop_type']
        prop_line = float(data['prop_line'])
        game_values = [float(v) for v in data['game_values']]
        opponent_tier = data.get('opponent_tier', 3)
        
        # Run analysis
        result = analysis_engine.analyze_prop(
            player_id=player_id,
            prop_type=prop_type,
            prop_line=prop_line,
            game_values=game_values,
            opponent_tier=opponent_tier
        )
        
        # Format response
        return jsonify({
            'player_id': result.player_id,
            'prop_type': result.prop_type,
            'prop_line': result.prop_line,
            'season_baseline': round(result.season_baseline, 2),
            'final_projection': round(result.final_projection, 2),
            'edge_percentage': round(result.edge_percentage, 2),
            'edge_direction': result.edge_percentage > 0 and 'OVER' or 'UNDER',
            'confidence_level': result.confidence_level,
            'recommended_play': result.recommended_play,
            'floor': round(result.floor, 2) if result.floor else None,
            'ceiling': round(result.ceiling, 2) if result.ceiling else None,
            'weights_applied': result.weights_applied
        })
        
    except Exception as e:
        logger.error(f"Error analyzing prop: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/batch-analysis', methods=['POST'])
def batch_analysis():
    """Analyze multiple props in a single request
    
    Request body:
    {
        "props": [
            {"player_id": int, "prop_type": str, ...},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        props = data.get('props', [])
        
        if not props:
            return jsonify({'error': 'No props provided'}), 400
        
        results = []
        for prop in props:
            result = analysis_engine.analyze_prop(
                player_id=prop['player_id'],
                prop_type=prop['prop_type'],
                prop_line=float(prop['prop_line']),
                game_values=[float(v) for v in prop['game_values']],
                opponent_tier=prop.get('opponent_tier', 3)
            )
            results.append({
                'player_id': result.player_id,
                'prop_type': result.prop_type,
                'final_projection': round(result.final_projection, 2),
                'edge_percentage': round(result.edge_percentage, 2),
                'confidence_level': result.confidence_level,
                'recommended_play': result.recommended_play
            })
        
        return jsonify({'results': results})
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500


@workflow_bp.route('/methodology', methods=['GET'])
def get_methodology():
    """Return the methodology explanation"""
    return jsonify({
        'name': 'Anti-Recency Bias Methodology v3.0',
        'description': 'Full-season baseline analysis with recency bias detection',
        'phases': [
            'Phase 1: Full Season Baseline (50-60% weight) - PRIMARY ANCHOR',
            'Phase 2: Historical Matchup Analysis (15-20% weight)',
            'Phase 3: Defensive Tier Performance (10-15% weight)',
            'Phase 4: Recent Form Analysis (10-15% MAX weight)',
            'Phase 5: Trend Validation (5% weight CRITICAL)'
        ],
        'core_principle': 'If recent performance differs from season baseline, identify WHY (injury, scheme change). No sustainable reason = treat as variance, default to season baseline.'
    })
