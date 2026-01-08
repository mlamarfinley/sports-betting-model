from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
import sys
import joblib
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for model imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

app = Flask(__name__)
CORS(app)

# Load the trained model
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'prediction_model.pkl')
try:
    model = joblib.load(MODEL_PATH)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    model = None

def get_db_connection():
    """Create database connection."""
    try:
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            database=os.getenv('DB_NAME', 'sports_betting'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

@app.route('/')
def home():
    """API homepage with documentation."""
    return jsonify({
        'name': 'Sports Betting Prediction API',
        'version': '1.0.0',
        'description': 'Machine learning-powered predictions for NBA, NFL, NHL, CFB, Tennis, Soccer, LoL, and CS2',
        'endpoints': {
            '/': 'API documentation',
            '/health': 'Health check',
            '/predict': 'Make a prediction (POST)',
            '/sports': 'List available sports',
            '/games/<sport>': 'Get upcoming games for a sport',
            '/teams/<sport>': 'Get teams for a sport',
            '/predictions/recent': 'Get recent predictions',
            '/stats/<sport>': 'Get sports statistics'
        }
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    conn = get_db_connection()
    db_status = 'connected' if conn else 'disconnected'
    if conn:
        conn.close()
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'model_loaded': model is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/sports')
def list_sports():
    """List all available sports."""
    return jsonify({
        'sports': [
            {'name': 'NBA', 'code': 'nba', 'description': 'National Basketball Association'},
            {'name': 'NFL', 'code': 'nfl', 'description': 'National Football League'},
            {'name': 'NHL', 'code': 'nhl', 'description': 'National Hockey League'},
            {'name': 'College Football', 'code': 'cfb', 'description': 'NCAA Football'},
            {'name': 'Tennis', 'code': 'tennis', 'description': 'ATP/WTA Tennis'},
            {'name': 'Soccer', 'code': 'soccer', 'description': 'International Soccer'},
            {'name': 'League of Legends', 'code': 'lol', 'description': 'LoL Esports'},
            {'name': 'Counter-Strike 2', 'code': 'cs2', 'description': 'CS2 Esports'}
        ]
    })

@app.route('/games/<sport>')
def get_games(sport):
    """Get upcoming games for a specific sport."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Map sport codes to tables
        table_map = {
            'nba': 'nba_games',
            'nfl': 'nfl_games',
            'nhl': 'nhl_games',
            'cfb': 'cfb_games',
            'tennis': 'tennis_matches',
            'soccer': 'soccer_matches'
        }
        
        if sport not in table_map:
            return jsonify({'error': f'Sport {sport} not supported'}), 400
        
        table = table_map[sport]
        query = f"""SELECT * FROM {table} 
                    WHERE game_status = 'scheduled' 
                    ORDER BY scraped_at DESC 
                    LIMIT 20"""
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        games = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Convert datetime objects to strings
        for game in games:
            for key, value in game.items():
                if isinstance(value, datetime):
                    game[key] = value.isoformat()
        
        return jsonify({'sport': sport, 'games': games, 'count': len(games)})
    
    except Exception as e:
        logger.error(f"Error fetching games: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/teams/<sport>')
def get_teams(sport):
    """Get teams for a specific sport."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Map sport codes to stats tables
        table_map = {
            'nba': 'nba_team_stats',
            'nfl': 'nfl_team_stats',
            'nhl': 'nhl_team_stats',
            'cfb': 'cfb_team_stats',
            'tennis': 'tennis_rankings',
            'soccer': 'soccer_standings'
        }
        
        if sport not in table_map:
            return jsonify({'error': f'Sport {sport} not supported'}), 400
        
        table = table_map[sport]
        query = f"SELECT * FROM {table} ORDER BY scraped_at DESC LIMIT 50"
        
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        teams = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Convert datetime objects to strings
        for team in teams:
            for key, value in team.items():
                if isinstance(value, datetime):
                    team[key] = value.isoformat()
        
        return jsonify({'sport': sport, 'teams': teams, 'count': len(teams)})
    
    except Exception as e:
        logger.error(f"Error fetching teams: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/predict', methods=['POST'])
def make_prediction():
    """Make a prediction for a game."""
    if not model:
        return jsonify({'error': 'Model not loaded'}), 500
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract required fields
        required_fields = ['sport', 'home_team', 'away_team']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Create feature dataframe (simplified - would need more features in production)
        features = pd.DataFrame([{
            'sport': data['sport'],
            'home_team': data['home_team'],
            'away_team': data['away_team'],
            'home_recent_wins': data.get('home_recent_wins', 0),
            'away_recent_wins': data.get('away_recent_wins', 0)
        }])
        
        # Make prediction
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0].tolist() if hasattr(model, 'predict_proba') else None
        
        result = {
            'prediction': 'home_win' if prediction == 1 else 'away_win',
            'home_team': data['home_team'],
            'away_team': data['away_team'],
            'sport': data['sport'],
            'confidence': max(probability) if probability else None,
            'probability': probability,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predictions/recent')
def recent_predictions():
    """Get recent predictions (if stored in database)."""
    # Placeholder - would need to implement prediction storage
    return jsonify({
        'message': 'Recent predictions endpoint',
        'note': 'Prediction storage not yet implemented',
        'predictions': []
    })

@app.route('/stats/<sport>')
def get_stats(sport):
    """Get aggregated statistics for a sport."""
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        
        # Get record counts for different tables
        stats = {'sport': sport}
        
        table_queries = {
            'nba': 'SELECT COUNT(*) FROM nba_games',
            'nfl': 'SELECT COUNT(*) FROM nfl_games',
            'nhl': 'SELECT COUNT(*) FROM nhl_games'
        }
        
        if sport in table_queries:
            cursor.execute(table_queries[sport])
            stats['total_games'] = cursor.fetchone()[0]
        
        return jsonify(stats)
    
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
