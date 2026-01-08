#!/usr/bin/env python3
"""
Soccer Data Scraper
Collects soccer match data, team standings, player stats from major leagues (EPL, La Liga, Serie A, Bundesliga, etc.)
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime, timedelta
import time
import json

class SoccerScraper:
    def __init__(self, database_url):
        self.database_url = database_url
        # API-Football or similar soccer data APIs
        self.api_key = None  # Would be set from environment variable
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        # Major leagues to track
        self.leagues = {
            'EPL': 39,  # English Premier League
            'La Liga': 140,  # Spain
            'Serie A': 135,  # Italy
            'Bundesliga': 78,  # Germany
            'Ligue 1': 61,  # France
            'Champions League': 2,
            'MLS': 253  # USA
        }
    
    def get_database_connection(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def fetch_league_standings(self, league_id, season=2026):
        """Fetch league standings"""
        try:
            # In production, would use actual API with key
            # url = f"{self.base_url}/standings?league={league_id}&season={season}"
            # response = requests.get(url, headers=headers_with_key)
            
            # For now, returning mock structure
            print(f"Fetching standings for league {league_id}...")
            standings = []
            
            return standings
        
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return []
    
    def fetch_recent_matches(self, league_id, days_back=14):
        """Fetch recent match results"""
        try:
            # In production:
            # url = f"{self.base_url}/fixtures?league={league_id}&last={days_back}"
            
            print(f"Fetching recent matches for league {league_id}...")
            matches = []
            
            return matches
        
        except Exception as e:
            print(f"Error fetching matches: {e}")
            return []
    
    def fetch_team_stats(self, team_id, season=2026):
        """Fetch team statistics"""
        try:
            # In production:
            # url = f"{self.base_url}/teams/statistics?team={team_id}&season={season}"
            
            print(f"Fetching stats for team {team_id}...")
            stats = {}
            
            return stats
        
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return {}
    
    def save_league_standings(self, standings_data, league_name):
        """Save league standings to database"""
        if not standings_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for team in standings_data:
                cur.execute("""
                    INSERT INTO soccer_standings
                    (league_name, team_name, position, played, won, drawn, lost,
                     goals_for, goals_against, goal_difference, points, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (league_name, team_name)
                    DO UPDATE SET
                        position = EXCLUDED.position,
                        played = EXCLUDED.played,
                        won = EXCLUDED.won,
                        drawn = EXCLUDED.drawn,
                        lost = EXCLUDED.lost,
                        goals_for = EXCLUDED.goals_for,
                        goals_against = EXCLUDED.goals_against,
                        goal_difference = EXCLUDED.goal_difference,
                        points = EXCLUDED.points,
                        last_updated = EXCLUDED.last_updated
                """, (
                    league_name,
                    team.get('team_name'),
                    team.get('position'),
                    team.get('played'),
                    team.get('won'),
                    team.get('drawn'),
                    team.get('lost'),
                    team.get('goals_for'),
                    team.get('goals_against'),
                    team.get('goal_difference'),
                    team.get('points'),
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(standings_data)} {league_name} standings")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving standings: {e}")
        finally:
            cur.close()
            conn.close()
    
    def save_match_data(self, match_data, league_name):
        """Save match results to database"""
        if not match_data:
            return
        
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            for match in match_data:
                cur.execute("""
                    INSERT INTO soccer_matches
                    (match_id, league_name, match_date, home_team, away_team,
                     home_score, away_score, status, venue, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (match_id)
                    DO UPDATE SET
                        home_score = EXCLUDED.home_score,
                        away_score = EXCLUDED.away_score,
                        status = EXCLUDED.status,
                        last_updated = EXCLUDED.last_updated
                """, (
                    match.get('match_id'),
                    league_name,
                    match.get('date'),
                    match.get('home_team'),
                    match.get('away_team'),
                    match.get('home_score'),
                    match.get('away_score'),
                    match.get('status'),
                    match.get('venue'),
                    datetime.now()
                ))
            
            conn.commit()
            print(f"Saved {len(match_data)} {league_name} matches")
        
        except Exception as e:
            conn.rollback()
            print(f"Error saving matches: {e}")
        finally:
            cur.close()
            conn.close()
    
    def calculate_form(self, team_name, last_n=5):
        """Calculate team form from last N matches"""
        conn = self.get_database_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    CASE 
                        WHEN home_team = %s THEN 
                            CASE 
                                WHEN home_score > away_score THEN 'W'
                                WHEN home_score < away_score THEN 'L'
                                ELSE 'D'
                            END
                        WHEN away_team = %s THEN
                            CASE 
                                WHEN away_score > home_score THEN 'W'
                                WHEN away_score < home_score THEN 'L'
                                ELSE 'D'
                            END
                    END as result
                FROM soccer_matches
                WHERE (home_team = %s OR away_team = %s)
                    AND status = 'FT'
                ORDER BY match_date DESC
                LIMIT %s
            """, (team_name, team_name, team_name, team_name, last_n))
            
            results = [row[0] for row in cur.fetchall()]
            form = ''.join(results)
            
            return form
        
        except Exception as e:
            print(f"Error calculating form: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    
    def run(self):
        """Run soccer data collection"""
        print(f"\nStarting Soccer data scraper...")
        
        # Fetch data for major leagues
        for league_name, league_id in self.leagues.items():
            print(f"\n--- {league_name} ---")
            
            # Fetch and save standings
            standings = self.fetch_league_standings(league_id)
            self.save_league_standings(standings, league_name)
            
            time.sleep(0.5)  # Rate limiting
            
            # Fetch and save recent matches
            matches = self.fetch_recent_matches(league_id)
            self.save_match_data(matches, league_name)
            
            time.sleep(0.5)  # Rate limiting
        
        print("Soccer scraper completed successfully\n")

if __name__ == "__main__":
    import os
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = SoccerScraper(database_url)
    scraper.run()
