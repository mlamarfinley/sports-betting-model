#!/usr/bin/env python3
"""
Tennis Data Scraper
Collects tennis match data, player rankings, tournament results, and head-to-head stats
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import time
import json

class TennisScraper:
    def __init__(self, database_url):
        self.database_url = database_url
        # ATP and WTA APIs/endpoints
        self.atp_rankings_url = "https://www.atptour.com/en/rankings/singles"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def get_database_connection(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def fetch_atp_rankings(self):
        """Fetch ATP singles rankings"""
        try:
            response = requests.get(self.atp_rankings_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rankings = []
            
            # Parse ranking table
            ranking_rows = soup.find_all('tr', class_='')  # Adjust selectors based on actual HTML
            
            for row in ranking_rows[:100]:  # Top 100 players
                try:
                    rank_cell = row.find('td', class_='rank')
                    player_cell = row.find('td', class_='player')
                    points_cell = row.find('td', class_='points')
                    
                    if rank_cell and player_cell:
                        rankings.append({
                            'rank': rank_cell.text.strip(),
                            'player_name': player_cell.text.strip(),
                            'points': points_cell.text.strip() if points_cell else '0'
                        })
                except Exception as e:
                    continue
            
            return rankings
        
        except Exception as e:
            print(f"Error fetching ATP rankings: {e}")
            return []
    
    def fetch_recent_matches(self):
        """Fetch recent tennis match results"""
        # This would typically use an API like tennisdata.com or sofascore
        # For now, returning mock structure
        matches = []
        
        try:
            # Example: Use FlashScore or similar API
            # For demonstration, creating mock data structure
            print("Fetching recent tennis matches...")
            
            # In production, this would query actual tennis APIs
            # matches = self.query_tennis_api()
            
        except Exception as e:
            print(f"Error fetching matches: {e}")
        
        return matches
    
    def save_rankings(self, rankings_data, tour='ATP'):
        """Save player rankings to database"""
        if not rankings_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for player in rankings_data:
                cur.execute("""
                    INSERT INTO tennis_rankings
                    (player_name, tour, ranking, points, last_updated)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (player_name, tour)
                    DO UPDATE SET
                        ranking = EXCLUDED.ranking,
                        points = EXCLUDED.points,
                        last_updated = EXCLUDED.last_updated
                """, (
                    player['player_name'],
                    tour,
                    int(player['rank']) if player['rank'].isdigit() else 0,
                    int(player['points'].replace(',', '')) if player['points'].replace(',', '').isdigit() else 0,
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(rankings_data)} {tour} rankings")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving rankings: {e}")
        finally:
            cur.close()
            conn.close()
    
    def save_match_data(self, match_data):
        """Save match results to database"""
        if not match_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for match in match_data:
                cur.execute("""
                    INSERT INTO tennis_matches
                    (match_id, tournament_name, match_date, player1_name, player2_name,
                     player1_score, player2_score, winner, surface, round, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id)
                    DO UPDATE SET
                        player1_score = EXCLUDED.player1_score,
                        player2_score = EXCLUDED.player2_score,
                        winner = EXCLUDED.winner,
                        last_updated = EXCLUDED.last_updated
                """, (
                    match.get('match_id'),
                    match.get('tournament'),
                    match.get('date'),
                    match.get('player1'),
                    match.get('player2'),
                    match.get('score1'),
                    match.get('score2'),
                    match.get('winner'),
                    match.get('surface'),
                    match.get('round'),
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(match_data)} tennis matches")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving match data: {e}")
        finally:
            cur.close()
            conn.close()
    
    def calculate_head_to_head(self, player1, player2):
        """Calculate head-to-head record between two players"""
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT winner, COUNT(*) as wins
                FROM tennis_matches
                WHERE (player1_name = %s AND player2_name = %s)
                   OR (player1_name = %s AND player2_name = %s)
                GROUP BY winner
            """, (player1, player2, player2, player1))
            
            results = cur.fetchall()
            h2h = {player1: 0, player2: 0}
            
            for winner, count in results:
                if winner in h2h:
                    h2h[winner] = count
            
            return h2h
        
        except Exception as e:
            print(f"Error calculating H2H: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    
    def run(self):
        """Run tennis data collection"""
        print(f"\nStarting Tennis data scraper...")
        
        # Fetch and save ATP rankings
        print("Fetching ATP rankings...")
        atp_rankings = self.fetch_atp_rankings()
        self.save_rankings(atp_rankings, 'ATP')
        
        time.sleep(1)  # Rate limiting
        
        # Fetch WTA rankings (similar process)
        print("Fetching WTA rankings...")
        # wta_rankings = self.fetch_wta_rankings()
        # self.save_rankings(wta_rankings, 'WTA')
        
        # Fetch recent match results
        print("Fetching recent match results...")
        matches = self.fetch_recent_matches()
        self.save_match_data(matches)
        
        print("Tennis scraper completed successfully\n")

if __name__ == "__main__":
    import os
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = TennisScraper(database_url)
    scraper.run()
