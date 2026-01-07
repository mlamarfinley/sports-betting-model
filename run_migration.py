#!/usr/bin/env python3
"""
Database Migration Runner
Runs all SQL migrations in the database/migrations folder
"""

import os
import psycopg2
from pathlib import Path

def run_migrations():
    """Run all SQL migration files"""
    
    # Get database URL from environment variable
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        return False
    
    print("Connecting to database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Get migration files
        migrations_dir = Path(__file__).parent / 'database' / 'migrations'
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        print(f"Found {len(migration_files)} migration file(s)")
        
        for migration_file in migration_files:
            print(f"\nRunning migration: {migration_file.name}")
            
            # Read SQL file
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute SQL
            cursor.execute(sql)
            
            print(f"✓ {migration_file.name} completed successfully")
        
        # Commit all changes
        conn.commit()
        print("\n✅ All migrations completed successfully!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Error running migrations: {str(e)}")
        if conn:
            conn.rollback()
        return False

if __name__ == "__main__":
    success = run_migrations()
    exit(0 if success else 1)
