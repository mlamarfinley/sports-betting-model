#!/usr/bin/env python3
"""
NBA Data Scraper
Collects game results, player stats, injury reports, and betting lines
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Optional

class NBAScraper:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.base_url = "https://www.nba.com"
        self.stats_api = "https://stats.nba.com/stats"
        
    def connect_db(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def fetch_games(self, date: datetime = None) -> List[Dict]:
        """Fetch NBA games for a specific date"""
        if not date:
            date = datetime.now()
        
        try:
            # NBA Stats API endpoint
            url = f"{self.stats_api}/scoreboardV2"
            params = {
                'DayOffset': 0,
                'LeagueID': '00',
                'gameDate': date.strftime('%Y-%m-%d')
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.nba.com/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            games = []
            if 'resultSets' in data:
                for game_set in data['resultSets']:
                    if game_set['name'] == 'GameHeader':
                        for game_row in game_set['rowSet']:
                            games.append({
                                'game_id': game_row[2],
                                'game_date': date,
                                'home_team': game_row[6],
                                'away_team': game_row[7],
                                'home_score': game_row[21] if len(game_row) > 21 else None,
                                'away_score': game_row[22] if len(game_row) > 22 else None,
                                'status': game_row[4]
                            })
            
            return games
            
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []
    
    def fetch_player_stats(self, game_id: str) -> List[Dict]:
        """Fetch player stats for a specific game"""
        try:
            url = f"{self.stats_api}/boxscoretraditionalv2"
            params = {'GameID': game_id}
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Referer': 'https://www.nba.com/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            player_stats = []
            if 'resultSets' in data:
                for result_set in data['resultSets']:
                    if result_set['name'] == 'PlayerStats':
                        headers = result_set['headers']
                        for row in result_set['rowSet']:
                            stat_dict = dict(zip(headers, row))
                            player_stats.append({
                                'game_id': game_id,
                                'player_id': stat_dict.get('PLAYER_ID'),
                                'player_name': stat_dict.get('PLAYER_NAME'),
                                'team_id': stat_dict.get('TEAM_ID'),
                                'minutes': stat_dict.get('MIN'),
                                'points': stat_dict.get('PTS'),
                                'rebounds': stat_dict.get('REB'),
                                'assists': stat_dict.get('AST'),
                                'steals': stat_dict.get('STL'),
                                'blocks': stat_dict.get('BLK'),
                                'turnovers': stat_dict.get('TO'),
                                'fg_made': stat_dict.get('FGM'),
                                'fg_attempted': stat_dict.get('FGA'),
                                'three_pt_made': stat_dict.get('FG3M'),
                                'three_pt_attempted': stat_dict.get('FG3A'),
                                'ft_made': stat_dict.get('FTM'),
                                'ft_attempted': stat_dict.get('FTA'),
                                'plus_minus': stat_dict.get('PLUS_MINUS')
                            })
            
            return player_stats
            
        except Exception as e:
            print(f"Error fetching player stats for game {game_id}: {e}")
            return []
    
    def fetch_injury_report(self) -> List[Dict]:
        """Fetch current NBA injury report"""
        try:
            # Note: This would need to be adapted to actual injury report sources
            injuries = []
            
            # Placeholder for injury scraping logic
            # Would need to scrape from ESPN, NBA.com, or RotoWire
            
            return injuries
            
        except Exception as e:
            print(f"Error fetching injury report: {e}")
            return []
    
    def save_game_to_db(self, game: Dict):
        """Save game data to database"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO games 
                (sport, external_game_id, game_date, home_team, away_team, 
                 home_score, away_score, game_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sport, external_game_id) 
                DO UPDATE SET 
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    game_status = EXCLUDED.game_status,
                    last_updated = NOW()
                RETURNING id;
            """, (
                'NBA',
                game['game_id'],
                game['game_date'],
                game['home_team'],
                game['away_team'],
                game['home_score'],
                game['away_score'],
                game['status']
            ))
            
            game_db_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            
            return game_db_id
            
        except Exception as e:
            print(f"Error saving game to database: {e}")
            return None
    
    def save_player_stats_to_db(self, stats: List[Dict], game_db_id: int):
        """Save player stats to database"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            for stat in stats:
                cur.execute("""
                    INSERT INTO player_game_stats
                    (game_id, sport, player_name, team, minutes_played, 
                     points, rebounds, assists, other_stats)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    game_db_id,
                    'NBA',
                    stat['player_name'],
                    stat['team_id'],
                    stat['minutes'],
                    stat['points'],
                    stat['rebounds'],
                    stat['assists'],
                    json.dumps({
                        'steals': stat['steals'],
                        'blocks': stat['blocks'],
                        'turnovers': stat['turnovers'],
                        'fg_made': stat['fg_made'],
                        'fg_attempted': stat['fg_attempted'],
                        'three_pt_made': stat['three_pt_made'],
                        'three_pt_attempted': stat['three_pt_attempted'],
                        'ft_made': stat['ft_made'],
                        'ft_attempted': stat['ft_attempted'],
                        'plus_minus': stat['plus_minus']
                    })
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Error saving player stats: {e}")
    
    def run(self, days_back: int = 7):
        """Main scraping process"""
        print("Starting NBA scraper...")
        
        try:
            # Scrape games from the last N days
            for days_ago in range(days_back):
                target_date = datetime.now() - timedelta(days=days_ago)
                print(f"\nFetching games for {target_date.strftime('%Y-%m-%d')}")
                
                games = self.fetch_games(target_date)
                print(f"Found {len(games)} games")
                
                for game in games:
                    print(f"Processing game: {game['away_team']} @ {game['home_team']}")
                    
                    # Save game to database
                    game_db_id = self.save_game_to_db(game)
                    
                    if game_db_id and game['status'] == 'Final':
                        # Fetch and save player stats for completed games
                        player_stats = self.fetch_player_stats(game['game_id'])
                        if player_stats:
                            self.save_player_stats_to_db(player_stats, game_db_id)
                            print(f"Saved stats for {len(player_stats)} players")
            
            print("\nNBA scraping completed successfully!")
            
        except Exception as e:
            print(f"Scraping failed: {e}")

if __name__ == "__main__":
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = NBAScraper(database_url)
    scraper.run()
