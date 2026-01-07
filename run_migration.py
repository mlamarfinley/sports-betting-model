#!/usr/bin/env python3
"""
Database Migration Runner
Runs SQL migrations in the database/migrations folder
Tracks completed migrations to avoid re-running them
"""

import os
import psycopg2
from pathlib import Path

def run_migrations():
    """Run all SQL migration files that haven't been executed yet"""
    
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
        
        # Create schema_migrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

                # Populate schema_migrations with already-executed migrations
        # Check if tables from migration 001 exist
        cursor.execute("SELECT to_regclass('public.teams')")
        if cursor.fetchone()[0] is not None:
            # Migration 001 was already executed
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING",
                ('001_init_schema.sql',)
            )
        
        # Check if tables from migration 002 exist
        cursor.execute("SELECT to_regclass('public.nba_player_stats')")
        if cursor.fetchone()[0] is not None:
            # Migration 002 was already executed
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING",
                ('002_sport_specific_stats.sql',)
            )
        
        conn.commit()
        
        # Get list of already executed migrations
        cursor.execute("SELECT version FROM schema_migrations")
        executed_migrations = set(row[0] for row in cursor.fetchall())
        
        # Get migration files
        migrations_dir = Path(__file__).parent / 'database' / 'migrations'
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        print(f"\nFound {len(migration_files)} migration file(s)")
        
        migrations_to_run = [
            f for f in migration_files 
            if f.name not in executed_migrations
        ]
        
        if not migrations_to_run:
            print("✓ All migrations already executed. Database is up to date!")
            cursor.close()
            conn.close()
            return True
        
        print(f"Running {len(migrations_to_run)} new migration(s)\n")
        
        for migration_file in migrations_to_run:
            print(f"Running migration: {migration_file.name}")
            
            # Read SQL file
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            # Execute SQL
            cursor.execute(sql)
            
            # Record this migration as completed
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (migration_file.name,)
            )
            
            # Commit this migration
            conn.commit()
            
            print(f"✓ {migration_file.name} completed successfully")
        
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
