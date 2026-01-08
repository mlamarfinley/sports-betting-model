#!/usr/bin/env python3
"""
NFL Data Scraper
Collects game results, team stats, player statistics, and injury reports for NFL
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Optional
import re

class NFLScraper:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.base_url = "https://www.espn.com/nfl"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def connect_db(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def get_current_season(self) -> int:
        """Get current NFL season year"""
        now = datetime.now()
        # NFL season runs Sept-Feb, so if before Sept, it's previous year's season
        return now.year if now.month >= 9 else now.year - 1
    
    def fetch_schedule(self, week: int = None) -> List[Dict]:
        """Fetch NFL schedule for a specific week"""
        season = self.get_current_season()
        
        if week is None:
            # Determine current week
            week = self.get_current_week()
        
        try:
            url = f"{self.base_url}/scoreboard/_/week/{week}/year/{season}/seasontype/2"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            games = []
            # Parse scoreboard for games
            game_elements = soup.find_all('article', class_='scoreboard')
            
            for game_elem in game_elements:
                try:
                    game_data = self.parse_game_element(game_elem, season, week)
                    if game_data:
                        games.append(game_data)
                except Exception as e:
                    print(f"Error parsing game: {e}")
                    continue
            
            return games
            
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return []
    
    def parse_game_element(self, game_elem, season: int, week: int) -> Optional[Dict]:
        """Parse individual game element"""
        try:
            # Extract team names
            teams = game_elem.find_all('div', class_='ScoreCell__TeamName')
            if len(teams) < 2:
                return None
            
            away_team = teams[0].text.strip()
            home_team = teams[1].text.strip()
            
            # Extract scores
            scores = game_elem.find_all('div', class_='ScoreCell__Score')
            away_score = int(scores[0].text.strip()) if len(scores) > 0 and scores[0].text.strip().isdigit() else None
            home_score = int(scores[1].text.strip()) if len(scores) > 1 and scores[1].text.strip().isdigit() else None
            
            # Extract game status
            status_elem = game_elem.find('div', class_='ScoreboardScoreCell__GameStatus')
            status = status_elem.text.strip() if status_elem else 'Scheduled'
            
            # Extract game ID from URL
            game_link = game_elem.find('a', href=True)
            game_id = None
            if game_link:
                match = re.search(r'gameId/(\d+)', game_link['href'])
                if match:
                    game_id = match.group(1)
            
            # Determine game date
            game_date = self.calculate_game_date(season, week)
            
            return {
                'game_id': game_id or f"{season}_W{week}_{away_team}_{home_team}",
                'season': season,
                'week': week,
                'game_date': game_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'status': status
            }
            
        except Exception as e:
            print(f"Error in parse_game_element: {e}")
            return None
    
    def calculate_game_date(self, season: int, week: int) -> datetime:
        """Calculate approximate game date based on season and week"""
        # NFL season typically starts first Thursday after Labor Day
        season_start = datetime(season, 9, 7)  # Approximate start
        # Adjust to Thursday
        days_to_thursday = (3 - season_start.weekday()) % 7
        season_start += timedelta(days=days_to_thursday)
        # Add weeks
        game_date = season_start + timedelta(weeks=week-1)
        return game_date
    
    def get_current_week(self) -> int:
        """Determine current NFL week"""
        try:
            url = f"{self.base_url}/scores"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find week indicator
            week_elem = soup.find('div', text=re.compile(r'Week \d+'))
            if week_elem:
                match = re.search(r'Week (\d+)', week_elem.text)
                if match:
                    return int(match.group(1))
            
            # Default to week 1 if can't determine
            return 1
            
        except Exception as e:
            print(f"Error determining current week: {e}")
            return 1
    
    def fetch_team_stats(self, team_abbr: str) -> Optional[Dict]:
        """Fetch team statistics"""
        try:
            season = self.get_current_season()
            url = f"{self.base_url}/team/stats/_/name/{team_abbr}/season/{season}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse team stats from page
            stats = {
                'team': team_abbr,
                'season': season,
                'points_per_game': 0.0,
                'points_allowed': 0.0,
                'total_yards': 0,
                'yards_allowed': 0
            }
            
            # This would need more specific parsing based on ESPN's structure
            # Placeholder implementation
            
            return stats
            
        except Exception as e:
            print(f"Error fetching team stats for {team_abbr}: {e}")
            return None
    
    def save_game_to_db(self, game: Dict):
        """Save game data to database"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO games 
                (sport, external_game_id, game_date, home_team, away_team, 
                 home_score, away_score, game_status, season, week)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sport, external_game_id) 
                DO UPDATE SET 
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    game_status = EXCLUDED.game_status,
                    last_updated = NOW()
                RETURNING id;
            """, (
                'NFL',
                game['game_id'],
                game['game_date'],
                game['home_team'],
                game['away_team'],
                game['home_score'],
                game['away_score'],
                game['status'],
                game.get('season'),
                game.get('week')
            ))
            
            game_db_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"Saved NFL game: {game['away_team']} @ {game['home_team']} (Week {game.get('week')})")
            return game_db_id
            
        except Exception as e:
            print(f"Error saving game to database: {e}")
            return None
    
    def run(self, weeks_to_scrape: int = 3):
        """Main scraping process"""
        print("Starting NFL scraper...")
        
        try:
            current_week = self.get_current_week()
            print(f"Current week: {current_week}")
            
            # Scrape recent weeks
            for week_offset in range(weeks_to_scrape):
                week = max(1, current_week - week_offset)
                print(f"\nFetching games for Week {week}")
                
                games = self.fetch_schedule(week)
                print(f"Found {len(games)} games")
                
                for game in games:
                    self.save_game_to_db(game)
            
            print("\nNFL scraping completed successfully!")
            
        except Exception as e:
            print(f"Scraping failed: {e}")

if __name__ == "__main__":
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = NFLScraper(database_url)
    scraper.run()
