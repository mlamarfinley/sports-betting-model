#!/usr/bin/env python3
"""
Automated Sports Betting Model Scheduler
Runs scrapers every 10 minutes and generates predictions
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime, timedelta
import requests

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.orchestrator import ScraperOrchestrator
from models.prediction_model import SportsPredictionModel
from models.continuous_learning import ContinuousLearningSystem

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
RUN_INTERVAL_MINUTES = int(os.environ.get('SCRAPER_INTERVAL', '10'))


class PredictionScheduler:
    def __init__(self):
        self.database_url = DATABASE_URL
        self.orchestrator = ScraperOrchestrator()
        self.model = SportsPredictionModel()
        self.learning_system = ContinuousLearningSystem(self.database_url)
        
    def run_scrapers(self):
        """Run all sports scrapers to get fresh data"""
        try:
            logger.info("🔄 Starting scraper run...")
            
            # Run orchestrator to scrape all sports
            self.orchestrator.run_all_scrapers()
            
            logger.info("✅ Scrapers completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error running scrapers: {e}")
            return False
    
    def generate_predictions_for_today(self):
        """Generate predictions for all games today"""
        try:
            logger.info("🎯 Generating predictions for today's games...")
            
            # Get today's games from scraped data
            today = datetime.now().strftime('%Y-%m-%d')
            
            # This would query your database for today's games
            # For now, we'll demonstrate with sample data
            
            prediction_count = 0
            
            # NBA predictions
            nba_predictions = self._generate_nba_predictions(today)
            prediction_count += len(nba_predictions)
            
            # NFL predictions
            nfl_predictions = self._generate_nfl_predictions(today)
            prediction_count += len(nfl_predictions)
            
            # NHL predictions
            nhl_predictions = self._generate_nhl_predictions(today)
            prediction_count += len(nhl_predictions)
            
            logger.info(f"✅ Generated {prediction_count} predictions for today")
            return prediction_count
            
        except Exception as e:
            logger.error(f"❌ Error generating predictions: {e}")
            return 0
    
    def _generate_nba_predictions(self, date):
        """Generate NBA predictions for given date"""
        predictions = []
        
        try:
            # Query database for NBA games today
            # For each player in each game:
            #   - Get their recent stats
            #   - Generate prediction for each stat type
            #   - Log prediction to database
            
            # Example prediction types for NBA
            stat_types = ['points', 'rebounds', 'assists', 'threes', 'steals', 'blocks']
            
            # This is placeholder - would query actual game data
            logger.info(f"  → NBA: Checking games for {date}")
            
        except Exception as e:
            logger.error(f"Error in NBA predictions: {e}")
        
        return predictions
    
    def _generate_nfl_predictions(self, date):
        """Generate NFL predictions for given date"""
        predictions = []
        
        try:
            stat_types = ['passing_yards', 'rushing_yards', 'receptions', 'touchdowns']
            logger.info(f"  → NFL: Checking games for {date}")
            
        except Exception as e:
            logger.error(f"Error in NFL predictions: {e}")
        
        return predictions
    
    def _generate_nhl_predictions(self, date):
        """Generate NHL predictions for given date"""
        predictions = []
        
        try:
            stat_types = ['goals', 'assists', 'points', 'shots']
            logger.info(f"  → NHL: Checking games for {date}")
            
        except Exception as e:
            logger.error(f"Error in NHL predictions: {e}")
        
        return predictions
    
    def scheduled_job(self):
        """Main scheduled job that runs every interval"""
        logger.info("\n" + "="*60)
        logger.info(f"🚀 SCHEDULED JOB STARTED - {datetime.now()}")
        logger.info("="*60)
        
        # Step 1: Run scrapers
        scraper_success = self.run_scrapers()
        
        if scraper_success:
            # Step 2: Generate predictions
            time.sleep(2)  # Brief pause between steps
            prediction_count = self.generate_predictions_for_today()
            
            logger.info(f"\n📊 Job Summary:")
            logger.info(f"  - Scrapers: {'✅ Success' if scraper_success else '❌ Failed'}")
            logger.info(f"  - Predictions: {prediction_count} generated")
        else:
            logger.warning("⚠️  Skipping predictions due to scraper failure")
        
        logger.info("="*60 + "\n")


def main():
    """Main entry point"""
    if not DATABASE_URL:
        logger.error("❌ DATABASE_URL environment variable not set!")
        sys.exit(1)
    
    logger.info("\n" + "#"*60)
    logger.info("# SPORTS BETTING MODEL - AUTOMATED SCHEDULER")
    logger.info(f"# Run Interval: Every {RUN_INTERVAL_MINUTES} minutes")
    logger.info(f"# Started: {datetime.now()}")
    logger.info("#"*60 + "\n")
    
    scheduler = PredictionScheduler()
    
    # Run immediately on startup
    logger.info("🎬 Running initial job...")
    scheduler.scheduled_job()
    
    # Schedule recurring jobs
    schedule.every(RUN_INTERVAL_MINUTES).minutes.do(scheduler.scheduled_job)
    
    logger.info(f"⏰ Scheduler active. Next run in {RUN_INTERVAL_MINUTES} minutes.")
    
    # Keep running
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("\n🛑 Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            time.sleep(60)  # Wait a minute before retrying


if __name__ == '__main__':
    main()
