#!/usr/bin/env python3
"""
NHL Data Scraper
Collects NHL game data, player stats, team standings, and injury reports
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import time
import json

class NHLScraper:
    def __init__(self, database_url):
        self.database_url = database_url
        self.base_url = "https://statsapi.web.nhl.com/api/v1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def get_database_connection(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def get_current_season(self):
        """Get current NHL season year"""
        now = datetime.now()
        # NHL season runs Oct-June
        if now.month >= 10:
            return f"{now.year}{now.year + 1}"
        else:
            return f"{now.year - 1}{now.year}"
    
    def fetch_team_standings(self):
        """Fetch current NHL team standings"""
        try:
            url = f"{self.base_url}/standings"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return None
    
    def fetch_schedule(self, start_date, end_date):
        """Fetch NHL schedule for date range"""
        try:
            url = f"{self.base_url}/schedule?startDate={start_date}&endDate={end_date}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return None
    
    def fetch_game_details(self, game_id):
        """Fetch detailed game data"""
        try:
            url = f"{self.base_url}/game/{game_id}/feed/live"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching game {game_id}: {e}")
            return None
    
    def fetch_player_stats(self, player_id, season):
        """Fetch player statistics"""
        try:
            url = f"{self.base_url}/people/{player_id}/stats?stats=statsSingleSeason&season={season}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching player {player_id} stats: {e}")
            return None
    
    def save_team_standings(self, standings_data):
        """Save team standings to database"""
        if not standings_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for record in standings_data.get('records', []):
                for team_record in record.get('teamRecords', []):
                    team = team_record.get('team', {})
                    
                    cur.execute("""
                        INSERT INTO nhl_standings 
                        (team_id, team_name, wins, losses, ot_losses, points, 
                         games_played, last_updated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (team_id) 
                        DO UPDATE SET
                            wins = EXCLUDED.wins,
                            losses = EXCLUDED.losses,
                            ot_losses = EXCLUDED.ot_losses,
                            points = EXCLUDED.points,
                            games_played = EXCLUDED.games_played,
                            last_updated = EXCLUDED.last_updated
                    """, (
                        team.get('id'),
                        team.get('name'),
                        team_record.get('leagueRecord', {}).get('wins', 0),
                        team_record.get('leagueRecord', {}).get('losses', 0),
                        team_record.get('leagueRecord', {}).get('ot', 0),
                        team_record.get('points', 0),
                        team_record.get('gamesPlayed', 0),
                        datetime.now()
                    ))
            
            conn.commit()
            print(f"Saved standings for {len(standings_data.get('records', []))} divisions")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving standings: {e}")
        finally:
            cur.close()
            conn.close()
    
    def save_game_data(self, game_data):
        """Save game details to database"""
        if not game_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            game_info = game_data.get('gameData', {})
            live_data = game_data.get('liveData', {})
            
            game_id = game_info.get('game', {}).get('pk')
            game_date = game_info.get('datetime', {}).get('dateTime')
            
            teams = game_info.get('teams', {})
            away_team = teams.get('away', {})
            home_team = teams.get('home', {})
            
            linescore = live_data.get('linescore', {})
            
            cur.execute("""
                INSERT INTO nhl_games 
                (game_id, game_date, home_team_id, home_team_name, 
                 away_team_id, away_team_name, home_score, away_score,
                 game_status, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game_id)
                DO UPDATE SET
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    game_status = EXCLUDED.game_status,
                    last_updated = EXCLUDED.last_updated
            """, (
                game_id,
                game_date,
                home_team.get('id'),
                home_team.get('name'),
                away_team.get('id'),
                away_team.get('name'),
                linescore.get('teams', {}).get('home', {}).get('goals', 0),
                linescore.get('teams', {}).get('away', {}).get('goals', 0),
                game_info.get('status', {}).get('abstractGameState'),
                datetime.now()
            ))
            
            conn.commit()
            print(f"Saved game {game_id}: {away_team.get('name')} @ {home_team.get('name')}")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving game data: {e}")
        finally:
            cur.close()
            conn.close()
    
    def run(self, days_back=7):
        """Run NHL data collection"""
        print(f"\nStarting NHL data scraper...")
        
        # Fetch and save standings
        print("Fetching team standings...")
        standings = self.fetch_team_standings()
        self.save_team_standings(standings)
        
        # Fetch recent games
        print(f"Fetching games from last {days_back} days...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        schedule = self.fetch_schedule(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if schedule:
            game_count = 0
            for date_data in schedule.get('dates', []):
                for game in date_data.get('games', []):
                    game_id = game.get('gamePk')
                    
                    # Add delay to respect rate limits
                    time.sleep(0.5)
                    
                    game_details = self.fetch_game_details(game_id)
                    self.save_game_data(game_details)
                    game_count += 1
            
            print(f"\nProcessed {game_count} NHL games")
        
        print("NHL scraper completed successfully\n")

if __name__ == "__main__":
    import os
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = NHLScraper(database_url)
    scraper.run()
