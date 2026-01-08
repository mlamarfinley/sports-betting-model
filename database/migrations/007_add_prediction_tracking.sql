-- Migration: Add Prediction Tracking and Model Performance System
-- Purpose: Track all predictions, verify results, calculate accuracy, enable continuous learning

-- Table: predictions
-- Stores every prediction made by the model
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    team VARCHAR(255),
    opponent VARCHAR(255),
    game_date TIMESTAMP,
    prediction_type VARCHAR(100) NOT NULL, -- e.g., 'points', 'rebounds', 'passing_yards', 'goals'
    predicted_value DECIMAL(10, 2) NOT NULL,
    confidence_score DECIMAL(5, 4), -- 0.0000 to 1.0000
    model_version VARCHAR(50),
    feature_importance JSONB, -- Store which features influenced this prediction
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_predictions_sport (sport),
    INDEX idx_predictions_player (player_name),
    INDEX idx_predictions_game_date (game_date),
    INDEX idx_predictions_type (prediction_type)
);

-- Table: prediction_results
-- Stores actual results to verify predictions
CREATE TABLE IF NOT EXISTS prediction_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID NOT NULL REFERENCES predictions(prediction_id) ON DELETE CASCADE,
    actual_value DECIMAL(10, 2) NOT NULL,
    prediction_error DECIMAL(10, 2), -- |predicted - actual|
    error_percentage DECIMAL(5, 2), -- percentage error
    is_accurate BOOLEAN, -- TRUE if within acceptable threshold
    verified_at TIMESTAMP DEFAULT NOW(),
    data_source VARCHAR(100), -- where the actual result came from
    INDEX idx_results_prediction (prediction_id),
    INDEX idx_results_verified (verified_at),
    INDEX idx_results_accuracy (is_accurate)
);

-- Table: model_performance_metrics
-- Aggregated performance metrics by sport, player, prediction type
CREATE TABLE IF NOT EXISTS model_performance_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    prediction_type VARCHAR(100) NOT NULL,
    time_period VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'all_time'
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5, 2), -- percentage
    avg_error DECIMAL(10, 2),
    median_error DECIMAL(10, 2),
    rmse DECIMAL(10, 2), -- root mean squared error
    mae DECIMAL(10, 2), -- mean absolute error
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_metrics_sport (sport),
    INDEX idx_metrics_type (prediction_type),
    INDEX idx_metrics_period (time_period, period_start)
);

-- Table: model_training_history
-- Track when models were trained and with what data
CREATE TABLE IF NOT EXISTS model_training_history (
    training_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    training_started_at TIMESTAMP NOT NULL,
    training_completed_at TIMESTAMP,
    training_duration_seconds INTEGER,
    training_data_size INTEGER, -- number of records used
    training_data_date_range_start TIMESTAMP,
    training_data_date_range_end TIMESTAMP,
    model_parameters JSONB, -- hyperparameters used
    train_score DECIMAL(5, 4), -- R² or accuracy on training set
    test_score DECIMAL(5, 4), -- R² or accuracy on test set
    feature_count INTEGER,
    feature_names JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_training_sport (sport),
    INDEX idx_training_version (model_version),
    INDEX idx_training_date (training_completed_at)
);

-- Table: model_retraining_triggers
-- Track what triggered model retraining (poor performance, new data, etc.)
CREATE TABLE IF NOT EXISTS model_retraining_triggers (
    trigger_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    trigger_type VARCHAR(100) NOT NULL, -- 'accuracy_drop', 'scheduled', 'manual', 'new_data'
    trigger_reason TEXT,
    accuracy_before_retrain DECIMAL(5, 2),
    accuracy_after_retrain DECIMAL(5, 2),
    improvement_percentage DECIMAL(5, 2),
    triggered_at TIMESTAMP DEFAULT NOW(),
    training_id UUID REFERENCES model_training_history(training_id),
    INDEX idx_triggers_sport (sport),
    INDEX idx_triggers_type (trigger_type),
    INDEX idx_triggers_date (triggered_at)
);

-- Table: feature_importance_tracking
-- Track which features are most important over time
CREATE TABLE IF NOT EXISTS feature_importance_tracking (
    importance_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    feature_name VARCHAR(255) NOT NULL,
    importance_score DECIMAL(10, 6),
    rank INTEGER, -- 1 = most important
    calculated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_importance_sport (sport),
    INDEX idx_importance_version (model_version),
    INDEX idx_importance_rank (rank)
);

-- Table: continuous_learning_log
-- Log all continuous learning events
CREATE TABLE IF NOT EXISTS continuous_learning_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- 'prediction_made', 'result_verified', 'model_retrained', 'performance_calculated'
    event_details JSONB,
    accuracy_impact DECIMAL(5, 2), -- how this event affected accuracy
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_learning_sport (sport),
    INDEX idx_learning_type (event_type),
    INDEX idx_learning_date (created_at)
);

-- Function: Calculate prediction accuracy
CREATE OR REPLACE FUNCTION calculate_prediction_accuracy()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate error metrics
    NEW.prediction_error := ABS(NEW.actual_value - (
        SELECT predicted_value FROM predictions WHERE prediction_id = NEW.prediction_id
    ));
    
    -- Calculate error percentage
    NEW.error_percentage := CASE 
        WHEN NEW.actual_value = 0 THEN 100
        ELSE (NEW.prediction_error / NEW.actual_value) * 100
    END;
    
    -- Mark as accurate if within 10% threshold
    NEW.is_accurate := (NEW.error_percentage <= 10);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-calculate accuracy when result is added
CREATE TRIGGER trigger_calculate_accuracy
BEFORE INSERT ON prediction_results
FOR EACH ROW
EXECUTE FUNCTION calculate_prediction_accuracy();

-- Function: Update performance metrics
CREATE OR REPLACE FUNCTION update_performance_metrics()
RETURNS TRIGGER AS $$
DECLARE
    v_sport VARCHAR(50);
    v_prediction_type VARCHAR(100);
BEGIN
    -- Get sport and prediction type
    SELECT sport, prediction_type INTO v_sport, v_prediction_type
    FROM predictions WHERE prediction_id = NEW.prediction_id;
    
    -- Insert or update daily metrics
    INSERT INTO model_performance_metrics (
        sport, prediction_type, time_period, period_start, period_end,
        total_predictions, correct_predictions, accuracy_rate
    )
    SELECT 
        v_sport,
        v_prediction_type,
        'daily',
        DATE_TRUNC('day', NOW()),
        DATE_TRUNC('day', NOW()) + INTERVAL '1 day',
        COUNT(*),
        SUM(CASE WHEN r.is_accurate THEN 1 ELSE 0 END),
        (SUM(CASE WHEN r.is_accurate THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)) * 100
    FROM predictions p
    JOIN prediction_results r ON p.prediction_id = r.prediction_id
    WHERE p.sport = v_sport 
        AND p.prediction_type = v_prediction_type
        AND DATE_TRUNC('day', r.verified_at) = DATE_TRUNC('day', NOW())
    ON CONFLICT (sport, prediction_type, time_period, period_start) 
    DO UPDATE SET
        total_predictions = EXCLUDED.total_predictions,
        correct_predictions = EXCLUDED.correct_predictions,
        accuracy_rate = EXCLUDED.accuracy_rate,
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Update metrics when result is verified
CREATE TRIGGER trigger_update_metrics
AFTER INSERT ON prediction_results
FOR EACH ROW
EXECUTE FUNCTION update_performance_metrics();

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_results_verified_at ON prediction_results(verified_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_updated_at ON model_performance_metrics(updated_at DESC);

-- Insert initial metrics tracking
INSERT INTO continuous_learning_log (sport, event_type, event_details)
VALUES 
    ('system', 'schema_initialized', '{"message": "Prediction tracking system initialized", "version": "1.0"}'::JSONB);
