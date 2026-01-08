#!/usr/bin/env python3
"""
Scraper Orchestrator
Runs all scrapers for sports betting model data collection
"""

import os
import sys
from datetime import import datetime
import schedule
import time

# Add scrapers to path
sys.path.append(os.path.dirname(__file__))

from esports.lol_patch_scraper import LoLPatchScraper
from nba.nba_scraper import NBAScraper
from nfl.nfl_scraper import NFLScraper
from nhl.nhl_scraper import NHLScraper

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
    
    try:
        # Run NFL Scraper
        print("\n--- NFL Data Scraper ---")
        nfl_scraper = NFLScraper(database_url)
        nfl_scraper.run()
    
    except Exception as e:
        print(f"NFL scraper error: {e}")
    
    try:
        # Run NHL Scraper
        print("\n--- NHL Data Scraper ---")
        nhl_scraper = NHLScraper(database_url)
        nhl_scraper.run(days_back=7)  # Last 7 days
        from tennis.tennis_scraper import TennisScraper
from soccer.soccer_scraper import SoccerScraper
from esports.cs2_scraper import CS2Scraper
from college_football.cfb_scraper import CFBScraper
    
    except Exception as e:
        print(f"NHL scraper error: {e}")
    
    # Add more scrapers here as they're created
    # Tennis, Soccer, CS2, College Football, etc.

    try:
        # Run Tennis Scraper
        print("\n--- Tennis Data Scraper ---")
        tennis_scraper = TennisScraper(database_url)
        tennis_scraper.run()
    except Exception as e:
        print(f"Tennis scraper error: {e}")
    
    try:
        # Run Soccer Scraper
        print("\n--- Soccer Data Scraper ---")
        soccer_scraper = SoccerScraper(database_url)
        soccer_scraper.run()
    except Exception as e:
        print(f"Soccer scraper error: {e}")
    
    try:
        # Run CS2 Scraper
        print("\n--- Counter-Strike 2 Scraper ---")
        cs2_scraper = CS2Scraper(database_url)
        cs2_scraper.run()
    except Exception as e:
        print(f"CS2 scraper error: {e}")
    
    try:
        # Run College Football Scraper
        print("\n--- College Football Scraper ---")
        cfb_scraper = CFBScraper()
        cfb_scraper.run()
    except Exception as e:
        print(f"CFB scraper error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Scraper run completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Run immediately
    run_all_scrapers()
    
    # Schedule to run daily at 3 AM
    schedule.every().day.at("03:00").do(run_all_scrapers)
    
    print("Scheduler started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute
