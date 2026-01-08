#!/bin/bash

# Run database migrations
echo "Running database migrations..."
python run_migration.py

# Start Flask API
echo "Starting Flask API..."
exec python api/app.py
