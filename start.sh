#!/bin/bash

# Run database migrations
echo "Running database migrations..."
python run_migration.py

# Start automated scheduler in background
echo "Starting automated scheduler..."
python automation/scheduler.py &
SCHEDULER_PID=$!

# Wait a moment for scheduler to initialize
sleep 2

# Start Flask API (this will keep the container running)
echo "Starting Flask API..."
exec python api/app.py

