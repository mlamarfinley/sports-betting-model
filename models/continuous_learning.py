#!/usr/bin/env python3
"""
Continuous Learning System
Automatically tracks predictions, verifies results, calculates accuracy, and triggers model retraining
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import logging
from prediction_model import SportsPredictionModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContinuousLearningSystem:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.accuracy_threshold = 70.0  # Retrain if accuracy drops below 70%
        self.min_predictions = 50  # Need at least 50 predictions before evaluating

    def connect_db(self):
        """Create database connection"""
        return psycopg2.connect(self.database_url)

    def log_prediction(self, sport: str, player_name: str, team: str, opponent: str,
                       game_date: datetime, prediction_type: str, predicted_value: float,
                       confidence_score: float = None, model_version: str = "1.0",
                       feature_importance: Dict = None) -> str:
        """
        Log a prediction to the database
        Returns: prediction_id
        """
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            query = """
                INSERT INTO predictions (
                    sport, player_name, team, opponent, game_date,
                    prediction_type, predicted_value, confidence_score,
                    model_version, feature_importance
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING prediction_id
            """

            cur.execute(query, (
                sport, player_name, team, opponent, game_date,
                prediction_type, predicted_value, confidence_score,
                model_version, json.dumps(feature_importance) if feature_importance else None
            ))

            prediction_id = cur.fetchone()[0]
            conn.commit()

            logger.info(f"Logged prediction {prediction_id}: {player_name} - {prediction_type} = {predicted_value}")

            # Log to continuous learning log
            self._log_learning_event(
                conn, sport, 'prediction_made',
                {'prediction_id': str(prediction_id), 'player': player_name, 'type': prediction_type}
            )

            return str(prediction_id)

        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def verify_result(self, prediction_id: str, actual_value: float, data_source: str = "scraper") -> Dict:
        """
        Verify a prediction against actual result
        Returns: accuracy metrics
        """
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Insert result (triggers auto-calculate accuracy via database trigger)
            query = """
                INSERT INTO prediction_results (
                    prediction_id, actual_value, data_source
                )
                VALUES (%s, %s, %s)
                RETURNING result_id, prediction_error, error_percentage, is_accurate
            """

            cur.execute(query, (prediction_id, actual_value, data_source))
            result = cur.fetchone()
            conn.commit()

            logger.info(f"Verified prediction {prediction_id}: Actual={actual_value}, Accurate={result['is_accurate']}")

            # Get sport info
            cur.execute("SELECT sport FROM predictions WHERE prediction_id = %s", (prediction_id,))
            sport = cur.fetchone()['sport']

            # Log learning event
            self._log_learning_event(
                conn, sport, 'result_verified',
                {'prediction_id': prediction_id, 'accurate': result['is_accurate']}
            )

            # Check if retraining needed
            self._check_retraining_needed(conn, sport)

            return dict(result)

        except Exception as e:
            logger.error(f"Error verifying result: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def get_accuracy_metrics(self, sport: str, time_period: str = 'daily', days_back: int = 7) -> Dict:
        """
        Get accuracy metrics for a sport
        """
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            query = """
                SELECT
                    sport,
                    prediction_type,
                    time_period,
                    total_predictions,
                    correct_predictions,
                    accuracy_rate,
                    avg_error,
                    updated_at
                FROM model_performance_metrics
                WHERE sport = %s
                AND time_period = %s
                AND period_start >= NOW() - INTERVAL '%s days'
                ORDER BY updated_at DESC
                LIMIT 10
            """

            cur.execute(query, (sport, time_period, days_back))
            results = cur.fetchall()

            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting accuracy metrics: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def get_learning_summary(self, sport: str, days_back: int = 7) -> Dict:
        """
        Get summary of continuous learning activity
        """
        conn = self.connect_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


                summary = {}
        try:
            # Retraining events
            cur.execute(
                "SELECT COUNT(*) as retrains FROM model_retraining_triggers WHERE sport = %s AND triggered_at >= NOW() - INTERVAL '%s days'",
                (sport, days_back)
            )
            summary['retraining_events'] = cur.fetchone()['retrains']

            # Learning events
            cur.execute(
                "SELECT COUNT(*) as events FROM continuous_learning_log WHERE sport = %s AND created_at >= NOW() - INTERVAL '%s days'",
                (sport, days_back)
            )
            summary['learning_events'] = cur.fetchone()['events']

            return summary

        except Exception as e:
            logger.error(f"Error getting learning summary: {e}")
            return {}
        finally:
            cur.close()
            conn.close()

    def _log_learning_event(self, conn, sport: str, event_type: str, details: Dict):
        """Internal: Log a learning event"""
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO continuous_learning_log (sport, event_type, details) VALUES (%s, %s, %s)",
                (sport, event_type, json.dumps(details))
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging learning event: {e}")
            conn.rollback()
        finally:
            cur.close()

    def _check_retraining_needed(self, conn, sport: str):
        """Internal: Check if model retraining is needed based on accuracy"""
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        try:
            # Get recent accuracy
            cur.execute(
                """
                SELECT accuracy_rate, total_predictions
                FROM model_performance_metrics
                WHERE sport = %s AND time_period = 'daily'
                ORDER BY period_start DESC
                LIMIT 1
                """,
                (sport,)
            )

            result = cur.fetchone()

            if result and result['total_predictions'] >= self.min_predictions:
                accuracy = float(result['accuracy_rate'])

                if accuracy < self.accuracy_threshold:
                    # Trigger retraining
                    logger.warning(f"Accuracy {accuracy}% below threshold {self.accuracy_threshold}% for {sport}. Triggering retrain.")

                    cur.execute(
                        """
                        INSERT INTO model_retraining_triggers (sport, reason, accuracy_before_trigger)
                        VALUES (%s, %s, %s)
                        RETURNING trigger_id
                        """,
                        (sport, f"Accuracy dropped to {accuracy}%", accuracy)
                    )

                    trigger_id = cur.fetchone()[0]
                    conn.commit()

                    # Log event
                    self._log_learning_event(
                        conn, sport, 'retrain_triggered',
                        {'trigger_id': trigger_id, 'accuracy': accuracy}
                    )

        except Exception as e:
            logger.error(f"Error checking retraining: {e}")
        finally:
            cur.close()


if __name__ == '__main__':
    # Example usage
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        print("DATABASE_URL environment variable not set")
        exit(1)

    system = ContinuousLearningSystem(database_url)

    # Get learning summary for NBA
    print("\nContinuous Learning Summary (NBA):")
    summary = system.get_learning_summary('NBA', days_back=7)
