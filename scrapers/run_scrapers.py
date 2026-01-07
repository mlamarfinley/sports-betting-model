#!/usr/bin/env python3
"""
Scraper Orchestrator
Runs all scrapers for sports betting model data collection
"""

import os
import sys
from datetime import datetime
import schedule
import time

# Add scrapers to path
sys.path.append(os.path.dirname(__file__))

from esports.lol_patch_scraper import LoLPatchScraper
from nba.nba_scraper import NBAScraper

def run_all_scrapers():
    """Run all configured scrapers"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return
    
    print(f"\n{'='*60}")
    print(f"Starting scraper run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    try:
        # Run LoL Patch Scraper
        print("\n--- League of Legends Patch Scraper ---")
        lol_scraper = LoLPatchScraper(database_url)
        lol_scraper.run()
        
    except Exception as e:
        print(f"LoL scraper error: {e}")
    
    try:
        # Run NBA Scraper
        print("\n--- NBA Data Scraper ---")
        nba_scraper = NBAScraper(database_url)
        nba_scraper.run(days_back=3)  # Last 3 days
        
    except Exception as e:
        print(f"NBA scraper error: {e}")
    
    # Add more scrapers here as they're created
    # NFL, NHL, Tennis, Soccer, CS2, etc.
    
    print(f"\n{'='*60}")
    print(f"Scraper run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

def schedule_scrapers():
    """Schedule scrapers to run periodically"""
    # Run immediately on start
    run_all_scrapers()
    
    # Schedule regular runs
    schedule.every(6).hours.do(run_all_scrapers)
    
    print("\nScheduler started. Scrapers will run every 6 hours.")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run sports betting data scrapers')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--schedule', action='store_true', help='Run on schedule')
    
    args = parser.parse_args()
    
    if args.schedule:
        schedule_scrapers()
    else:
        run_all_scrapers()
