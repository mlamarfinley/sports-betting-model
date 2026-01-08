#!/usr/bin/env python3
"""
Sports Betting Prediction Model
Machine learning model for predicting player prop lines and scores
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import psycopg2
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pickle


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
    
    def fetch_player_data(self, limit: int = 10000) -> pd.DataFrame:
        """Fetch player statistics from database"""
        conn = self.connect_db()
        
        # Build sport-specific query
        if self.sport.upper() == 'NBA':
            query = """
                SELECT player_name, team, opponent, points, rebounds, assists, 
                       steals, blocks, minutes_played, field_goal_pct, three_point_pct,
                       free_throw_pct, game_date
                FROM nba_player_stats
                WHERE game_date >= NOW() - INTERVAL '2 years'
                ORDER BY game_date DESC
                LIMIT %s
            """
        elif self.sport.upper() == 'NFL':
            query = """
                SELECT player_name, team, opponent, passing_yards, rushing_yards, 
                       receiving_yards, touchdowns, receptions, completions, attempts,
                       game_date
                FROM nfl_player_stats
                WHERE game_date >= NOW() - INTERVAL '2 years'
                ORDER BY game_date DESC
                LIMIT %s
            """
        elif self.sport.upper() == 'NHL':
            query = """
                SELECT player_name, team, opponent, goals, assists, shots, 
                       saves, ice_time, plus_minus, game_date
                FROM nhl_player_stats
                WHERE game_date >= NOW() - INTERVAL '2 years'
                ORDER BY game_date DESC
                LIMIT %s
            """
        else:  # College Football
            query = """
                SELECT player_name, team, opponent, passing_yards, rushing_yards,
                       receiving_yards, total_yards, touchdowns, game_date
                FROM college_player_stats
                WHERE game_date >= NOW() - INTERVAL '1 year'
                ORDER BY game_date DESC
                LIMIT %s
            """
        
        df = pd.read_sql_query(query, conn, params=(limit,))
        conn.close()
        return df
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for prediction"""
        df = df.copy()
        df['game_date'] = pd.to_datetime(df['game_date'])
        
        # Sort by player and date
        df = df.sort_values(['player_name', 'game_date'])
        
        # Calculate rolling averages (last 5, 10 games)
        for window in [5, 10]:
            for col in df.select_dtypes(include=[np.number]).columns:
                if col != 'game_date':
                    df[f'{col}_avg_{window}'] = df.groupby('player_name')[col].transform(
                        lambda x: x.rolling(window, min_periods=1).mean()
                    )
                    df[f'{col}_std_{window}'] = df.groupby('player_name')[col].transform(
                        lambda x: x.rolling(window, min_periods=1).std()
                    )
        
        # Trend features (performance trending up/down)
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != 'game_date' and '_avg_' not in col and '_std_' not in col:
                df[f'{col}_trend'] = df.groupby('player_name')[col].transform(
                    lambda x: x.diff()
                )
        
        # Days since last game
        df['days_rest'] = df.groupby('player_name')['game_date'].diff().dt.days
        df['days_rest'] = df['days_rest'].fillna(7)
        
        # Home/away encoding (would need additional data)
        # Team strength metrics (would need additional data)
        
        # Fill NaN values
        df = df.fillna(0)
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame, target_col: str) -> Tuple:
        """Prepare features and target for training"""
        # Drop non-numeric and identifier columns
        exclude_cols = ['player_name', 'team', 'opponent', 'game_date']
        feature_cols = [col for col in df.columns if col not in exclude_cols and col != target_col]
        
        X = df[feature_cols]
        y = df[target_col]
        
        # Store feature columns for later use
        self.feature_columns = feature_cols
        
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def train_model(self, target_metric: str = 'points'):
        """Train the prediction model"""
        print(f"Fetching {self.sport} data...")
        df = self.fetch_player_data()
        
        if df.empty:
            print(f"No data found for {self.sport}")
            return
        
        print(f"Engineering features for {len(df)} records...")
        df = self.engineer_features(df)
        
        # Determine target column based on sport
        if target_metric not in df.columns:
            print(f"Target metric '{target_metric}' not found. Available: {df.columns.tolist()}")
            return
        
        print(f"Preparing training data for {target_metric}...")
        X_train, X_test, y_train, y_test = self.prepare_training_data(df, target_metric)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train ensemble model
        print("Training model...")
        self.model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        
        print(f"Training R² Score: {train_score:.4f}")
        print(f"Testing R² Score: {test_score:.4f}")
        
        return self.model
    
    def predict(self, player_name: str, opponent: str) -> Dict:
        """Predict player performance for upcoming game"""
        if self.model is None:
            return {"error": "Model not trained"}
        
        # Fetch recent player data
        conn = self.connect_db()
        query = f"""
            SELECT * FROM {self.sport.lower()}_player_stats
            WHERE player_name = %s
            ORDER BY game_date DESC
            LIMIT 10
        """
        
        df = pd.read_sql_query(query, conn, params=(player_name,))
        conn.close()
        
        if df.empty:
            return {"error": f"No data found for player {player_name}"}
        
        # Engineer features
        df = self.engineer_features(df)
        
        # Get latest features
        latest_features = df[self.feature_columns].iloc[0:1]
        
        # Scale and predict
        features_scaled = self.scaler.transform(latest_features)
        prediction = self.model.predict(features_scaled)[0]
        
        return {
            "player": player_name,
            "opponent": opponent,
            "predicted_value": float(prediction),
            "confidence": "high" if len(df) >= 10 else "medium"
        }
    
    def save_model(self, filepath: str = 'prediction_model.pkl'):
        """Save trained model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'sport': self.sport
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
    
    @classmethod
    def load_model(cls, filepath: str = 'prediction_model.pkl', database_url: str = None):
        """Load trained model from disk"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        instance = cls(database_url or os.environ.get('DATABASE_URL'), model_data['sport'])
        instance.model = model_data['model']
        instance.scaler = model_data['scaler']
        instance.feature_columns = model_data['feature_columns']
        
        return instance


if __name__ == '__main__':
    # Training script
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("DATABASE_URL environment variable not set")
        exit(1)
    
    # Train models for each sport
    sports_targets = {
        'NBA': 'points',
        'NFL': 'passing_yards',
        'NHL': 'goals'
    }
    
    for sport, target in sports_targets.items():
        print(f"\n{'='*50}")
        print(f"Training {sport} model for {target}")
        print(f"{'='*50}")
        
        try:
            model = SportsPredictionModel(database_url, sport)
            model.train_model(target_metric=target)
            model.save_model(f'{sport.lower()}_prediction_model.pkl')
        except Exception as e:
            print(f"Error training {sport} model: {e}")
    
    print("\nModel training complete!")
