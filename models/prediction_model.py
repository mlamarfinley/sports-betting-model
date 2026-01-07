#!/usr/bin/env python3
"""
Sports Betting Prediction Model
Machine learning model for predicting sports outcomes and prop bets
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import psycopg2
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class SportsPredictionModel:
    def __init__(self, database_url: str, sport: str):
        self.database_url = database_url
        self.sport = sport
        self.scaler = StandardScaler()
        self.model = None
        self.feature_columns = []
        
    def connect_db(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def load_training_data(self, days_back: int = 365) -> pd.DataFrame:
        """Load historical game data for training"""
        try:
            conn = self.connect_db()
            
            # Query historical games and stats
            query = """
                SELECT 
                    g.id,
                    g.game_date,
                    g.home_team,
                    g.away_team,
                    g.home_score,
                    g.away_score,
                    g.home_team_rest_days,
                    g.away_team_rest_days,
                    ts_home.win_percentage as home_win_pct,
                    ts_home.avg_points as home_avg_points,
                    ts_away.win_percentage as away_win_pct,
                    ts_away.avg_points as away_avg_points
                FROM games g
                LEFT JOIN team_stats ts_home ON g.home_team = ts_home.team_name AND ts_home.sport = g.sport
                LEFT JOIN team_stats ts_away ON g.away_team = ts_away.team_name AND ts_away.sport = g.sport
                WHERE g.sport = %s 
                AND g.game_status = 'Final'
                AND g.game_date >= NOW() - INTERVAL '%s days'
                ORDER BY g.game_date DESC;
            """
            
            df = pd.read_sql_query(query, conn, params=(self.sport, days_back))
            conn.close()
            
            # Calculate target variable (home team win)
            df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
            
            # Calculate point differential
            df['point_diff'] = df['home_score'] - df['away_score']
            
            return df
            
        except Exception as e:
            print(f"Error loading training data: {e}")
            return pd.DataFrame()
    
    def feature_engineering(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create additional features for better predictions"""
        # Rest advantage
        df['rest_advantage'] = df['home_team_rest_days'] - df['away_team_rest_days']
        
        # Win percentage differential
        df['win_pct_diff'] = df['home_win_pct'] - df['away_win_pct']
        
        # Points per game differential
        df['ppg_diff'] = df['home_avg_points'] - df['away_avg_points']
        
        # Home advantage (historical win rate at home)
        df['home_advantage'] = 0.55  # Default home advantage
        
        # Time features
        df['day_of_week'] = pd.to_datetime(df['game_date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['game_date']).dt.month
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare feature matrix and target variable"""
        self.feature_columns = [
            'home_win_pct', 'away_win_pct', 'win_pct_diff',
            'home_avg_points', 'away_avg_points', 'ppg_diff',
            'home_team_rest_days', 'away_team_rest_days', 'rest_advantage',
            'home_advantage', 'day_of_week', 'month'
        ]
        
        # Drop rows with missing values
        df_clean = df.dropna(subset=self.feature_columns + ['home_win'])
        
        X = df_clean[self.feature_columns].values
        y = df_clean['home_win'].values
        
        return X, y
    
    def build_neural_network(self, input_dim: int) -> keras.Model:
        """Build a neural network model for predictions"""
        model = keras.Sequential([
            layers.Input(shape=(input_dim,)),
            layers.Dense(128, activation='relu'),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy', 'AUC']
        )
        
        return model
    
    def train_model(self, use_nn: bool = True, test_size: float = 0.2):
        """Train the prediction model"""
        print(f"Loading training data for {self.sport}...")
        df = self.load_training_data()
        
        if df.empty:
            print("No training data available")
            return
        
        print(f"Loaded {len(df)} games")
        
        # Feature engineering
        df = self.feature_engineering(df)
        
        # Prepare features
        X, y = self.prepare_features(df)
        print(f"Training on {len(X)} samples with {X.shape[1]} features")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        if use_nn:
            # Train neural network
            print("Training neural network...")
            self.model = self.build_neural_network(X_train_scaled.shape[1])
            
            history = self.model.fit(
                X_train_scaled, y_train,
                validation_data=(X_test_scaled, y_test),
                epochs=50,
                batch_size=32,
                verbose=1
            )
            
            # Evaluate
            test_loss, test_acc, test_auc = self.model.evaluate(X_test_scaled, y_test)
            print(f"\nTest Accuracy: {test_acc:.4f}")
            print(f"Test AUC: {test_auc:.4f}")
            
        else:
            # Train Random Forest
            print("Training Random Forest...")
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            train_acc = self.model.score(X_train_scaled, y_train)
            test_acc = self.model.score(X_test_scaled, y_test)
            print(f"\nTrain Accuracy: {train_acc:.4f}")
            print(f"Test Accuracy: {test_acc:.4f}")
    
    def predict_game(self, home_team: str, away_team: str, game_date: datetime) -> Dict:
        """Predict outcome of a specific game"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # Get team stats
            cur.execute("""
                SELECT win_percentage, avg_points
                FROM team_stats
                WHERE team_name = %s AND sport = %s
            """, (home_team, self.sport))
            home_stats = cur.fetchone()
            
            cur.execute("""
                SELECT win_percentage, avg_points
                FROM team_stats
                WHERE team_name = %s AND sport = %s
            """, (away_team, self.sport))
            away_stats = cur.fetchone()
            
            conn.close()
            
            if not home_stats or not away_stats:
                return {'error': 'Team stats not found'}
            
            # Create feature vector
            features = {
                'home_win_pct': home_stats[0] or 0.5,
                'away_win_pct': away_stats[0] or 0.5,
                'win_pct_diff': (home_stats[0] or 0.5) - (away_stats[0] or 0.5),
                'home_avg_points': home_stats[1] or 100,
                'away_avg_points': away_stats[1] or 100,
                'ppg_diff': (home_stats[1] or 100) - (away_stats[1] or 100),
                'home_team_rest_days': 2,  # Default
                'away_team_rest_days': 2,  # Default
                'rest_advantage': 0,
                'home_advantage': 0.55,
                'day_of_week': game_date.weekday(),
                'month': game_date.month
            }
            
            # Create feature array
            X = np.array([[features[col] for col in self.feature_columns]])
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            if isinstance(self.model, keras.Model):
                prob = self.model.predict(X_scaled)[0][0]
            else:
                prob = self.model.predict_proba(X_scaled)[0][1]
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'home_win_probability': float(prob),
                'away_win_probability': float(1 - prob),
                'predicted_winner': home_team if prob > 0.5 else away_team,
                'confidence': float(abs(prob - 0.5) * 2)
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {'error': str(e)}
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        if isinstance(self.model, keras.Model):
            self.model.save(filepath)
        else:
            import joblib
            joblib.dump(self.model, filepath)
        
        # Save scaler
        import joblib
        joblib.dump(self.scaler, filepath.replace('.h5', '_scaler.pkl'))
    
    def load_model(self, filepath: str, use_nn: bool = True):
        """Load trained model from disk"""
        if use_nn:
            self.model = keras.models.load_model(filepath)
        else:
            import joblib
            self.model = joblib.load(filepath)
        
        # Load scaler
        import joblib
        self.scaler = joblib.load(filepath.replace('.h5', '_scaler.pkl'))

if __name__ == "__main__":
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        exit(1)
    
    # Train NBA model
    print("Training NBA prediction model...")
    nba_model = SportsPredictionModel(database_url, 'NBA')
    nba_model.train_model(use_nn=True)
    nba_model.save_model('models/nba_model.h5')
    
    print("\nModel training complete!")
