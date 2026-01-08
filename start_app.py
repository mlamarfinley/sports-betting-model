#!/usr/bin/env python3
"""
Startup script for Railway deployment.
Runs database migrations and then starts the Flask API server.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    print("Running database migrations...")
    
    # Import and run migrations without calling exit()
    from run_migration import run_migrations
    success = run_migrations()
    
    if not success:
        print("Warning: Migrations encountered errors, but continuing to start Flask...")
    
    print("Starting Flask API...")
    
    # Import and run Flask app
    from api.app import app    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
