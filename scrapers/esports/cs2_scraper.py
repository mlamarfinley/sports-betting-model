#!/usr/bin/env python3
"""
Counter-Strike 2 Data Scraper
Collects CS2 match data, team rankings, player stats, tournament results from HLTV and other sources
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import time
import json

class CS2Scraper:
    def __init__(self, database_url):
        self.database_url = database_url
        self.hltv_url = "https://www.hltv.org"
        self.liquipedia_url = "https://liquipedia.net/counterstrike"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def get_database_connection(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def fetch_team_rankings(self):
        """Fetch CS2 team rankings from HLTV"""
        try:
            url = f"{self.hltv_url}/ranking/teams"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            rankings = []
            
            # Parse ranking table
            ranking_rows = soup.find_all('div', class_='ranked-team')
            
            for row in ranking_rows[:30]:  # Top 30 teams
                try:
                    rank_elem = row.find('span', class_='position')
                    team_elem = row.find('span', class_='name')
                    points_elem = row.find('span', class_='points')
                    
                    if rank_elem and team_elem:
                        rankings.append({
                            'rank': rank_elem.text.strip(),
                            'team_name': team_elem.text.strip(),
                            'points': points_elem.text.strip() if points_elem else '0'
                        })
                except Exception as e:
                    continue
            
            return rankings
        
        except Exception as e:
            print(f"Error fetching team rankings: {e}")
            return []
    
    def fetch_recent_matches(self, days_back=7):
        """Fetch recent CS2 match results"""
        try:
            url = f"{self.hltv_url}/results"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            matches = []
            
            # Parse match results
            match_elements = soup.find_all('div', class_='result-con')
            
            for match_elem in match_elements[:50]:  # Last 50 matches
                try:
                    team1_elem = match_elem.find('div', class_='team1')
                    team2_elem = match_elem.find('div', class_='team2')
                    score_elem = match_elem.find('span', class_='score')
                    event_elem = match_elem.find('span', class_='event-name')
                    
                    if team1_elem and team2_elem and score_elem:
                        matches.append({
                            'team1': team1_elem.text.strip(),
                            'team2': team2_elem.text.strip(),
                            'score': score_elem.text.strip(),
                            'event': event_elem.text.strip() if event_elem else 'Unknown',
                            'date': datetime.now()  # Would parse actual date from page
                        })
                except Exception as e:
                    continue
            
            return matches
        
        except Exception as e:
            print(f"Error fetching matches: {e}")
            return []
    
    def fetch_player_stats(self, days=30):
        """Fetch player statistics"""
        try:
            url = f"{self.hltv_url}/stats/players"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            player_stats = []
            
            # Parse player stats table
            player_rows = soup.find_all('tr')
            
            for row in player_rows[:50]:  # Top 50 players
                try:
                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        player_stats.append({
                            'player_name': cols[0].text.strip(),
                            'team': cols[1].text.strip(),
                            'maps_played': cols[2].text.strip(),
                            'rating': cols[3].text.strip(),
                            'kd_diff': cols[4].text.strip()
                        })
                except Exception as e:
                    continue
            
            return player_stats
        
        except Exception as e:
            print(f"Error fetching player stats: {e}")
            return []
    
    def save_team_rankings(self, rankings_data):
        """Save team rankings to database"""
        if not rankings_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for team in rankings_data:
                cur.execute("""
                    INSERT INTO cs2_rankings
                    (team_name, ranking, points, last_updated)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (team_name)
                    DO UPDATE SET
                        ranking = EXCLUDED.ranking,
                        points = EXCLUDED.points,
                        last_updated = EXCLUDED.last_updated
                """, (
                    team['team_name'],
                    int(team['rank']) if team['rank'].isdigit() else 0,
                    int(team['points'].replace(',', '')) if team['points'].replace(',', '').isdigit() else 0,
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(rankings_data)} CS2 team rankings")
        
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
                # Parse score (format: "16 - 14")
                scores = match['score'].split('-')
                team1_score = int(scores[0].strip()) if len(scores) > 0 else 0
                team2_score = int(scores[1].strip()) if len(scores) > 1 else 0
                
                cur.execute("""
                    INSERT INTO cs2_matches
                    (team1_name, team2_name, team1_score, team2_score,
                     event_name, match_date, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    match['team1'],
                    match['team2'],
                    team1_score,
                    team2_score,
                    match['event'],
                    match['date'],
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(match_data)} CS2 matches")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving match data: {e}")
        finally:
            cur.close()
            conn.close()
    
    def save_player_stats(self, player_data):
        """Save player statistics to database"""
        if not player_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for player in player_data:
                cur.execute("""
                    INSERT INTO cs2_players
                    (player_name, team_name, maps_played, rating, kd_diff, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (player_name)
                    DO UPDATE SET
                        team_name = EXCLUDED.team_name,
                        maps_played = EXCLUDED.maps_played,
                        rating = EXCLUDED.rating,
                        kd_diff = EXCLUDED.kd_diff,
                        last_updated = EXCLUDED.last_updated
                """, (
                    player['player_name'],
                    player['team'],
                    int(player['maps_played']) if player['maps_played'].isdigit() else 0,
                    float(player['rating']) if player['rating'].replace('.', '').isdigit() else 0.0,
                    int(player['kd_diff']) if player['kd_diff'].lstrip('-').isdigit() else 0,
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(player_data)} CS2 player stats")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving player stats: {e}")
        finally:
            cur.close()
            conn.close()
    
    def run(self):
        """Run CS2 data collection"""
        print(f"\nStarting CS2 data scraper...")
        
        # Fetch and save team rankings
        print("Fetching team rankings...")
        rankings = self.fetch_team_rankings()
        self.save_team_rankings(rankings)
        
        time.sleep(1)  # Rate limiting
        
        # Fetch and save recent matches
        print("Fetching recent match results...")
        matches = self.fetch_recent_matches()
        self.save_match_data(matches)
        
        time.sleep(1)  # Rate limiting
        
        # Fetch and save player stats
        print("Fetching player statistics...")
        player_stats = self.fetch_player_stats()
        self.save_player_stats(player_stats)
        
        print("CS2 scraper completed successfully\n")

if __name__ == "__main__":
    import os
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = CS2Scraper(database_url)
    scraper.run()
