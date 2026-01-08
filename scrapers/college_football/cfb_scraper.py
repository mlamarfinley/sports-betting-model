import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import logging
import os
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CFBScraper:
    """Scraper for College Football data including team stats, rankings, and game results."""
    
    def __init__(self):
        self.db_connection = None
        self.base_url = "https://www.espn.com/college-football"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def connect_to_db(self):
        """Establish database connection using environment variables."""
        try:
            self.db_connection = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'sports_betting'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            logger.info("Successfully connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def scrape_team_rankings(self) -> List[Dict[str, Any]]:
        """Scrape current College Football team rankings."""
        try:
            url = f"{self.base_url}/rankings"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            rankings = []
            
            # Find ranking tables
            ranking_items = soup.find_all('div', class_='team-rank-item')
            
            for item in ranking_items:
                try:
                    rank_elem = item.find('span', class_='rank')
                    team_elem = item.find('span', class_='team-name')
                    record_elem = item.find('span', class_='record')
                    
                    if rank_elem and team_elem:
                        ranking = {
                            'rank': int(rank_elem.text.strip()),
                            'team_name': team_elem.text.strip(),
                            'record': record_elem.text.strip() if record_elem else None,
                            'scraped_at': datetime.now()
                        }
                        rankings.append(ranking)
                except Exception as e:
                    logger.warning(f"Error parsing ranking item: {e}")
                    continue
            
            logger.info(f"Scraped {len(rankings)} CFB team rankings")
            return rankings
            
        except Exception as e:
            logger.error(f"Error scraping CFB rankings: {e}")
            return []
    
    def scrape_team_stats(self) -> List[Dict[str, Any]]:
        """Scrape team statistics for all CFB teams."""
        try:
            url = f"{self.base_url}/stats/team"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            teams_stats = []
            
            # Find stats tables
            stats_rows = soup.find_all('tr', class_='Table__TR')
            
            for row in stats_rows[1:]:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 8:
                        team_stats = {
                            'team_name': cells[0].text.strip(),
                            'games_played': int(cells[1].text.strip()) if cells[1].text.strip().isdigit() else 0,
                            'points_per_game': float(cells[2].text.strip()) if cells[2].text.strip() else 0.0,
                            'yards_per_game': float(cells[3].text.strip()) if cells[3].text.strip() else 0.0,
                            'passing_yards': float(cells[4].text.strip()) if cells[4].text.strip() else 0.0,
                            'rushing_yards': float(cells[5].text.strip()) if cells[5].text.strip() else 0.0,
                            'turnovers': int(cells[6].text.strip()) if cells[6].text.strip().isdigit() else 0,
                            'penalties': int(cells[7].text.strip()) if cells[7].text.strip().isdigit() else 0,
                            'scraped_at': datetime.now()
                        }
                        teams_stats.append(team_stats)
                except Exception as e:
                    logger.warning(f"Error parsing team stats row: {e}")
                    continue
            
            logger.info(f"Scraped stats for {len(teams_stats)} CFB teams")
            return teams_stats
            
        except Exception as e:
            logger.error(f"Error scraping CFB team stats: {e}")
            return []
    
    def scrape_schedule_and_scores(self) -> List[Dict[str, Any]]:
        """Scrape recent games and upcoming schedule."""
        try:
            url = f"{self.base_url}/scoreboard"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            games = []
            
            # Find game cards
            game_cards = soup.find_all('div', class_='ScoreCell')
            
            for card in game_cards:
                try:
                    teams = card.find_all('div', class_='ScoreCell__TeamName')
                    scores = card.find_all('div', class_='ScoreCell__Score')
                    date_elem = card.find('div', class_='ScoreCell__Date')
                    
                    if len(teams) >= 2:
                        game = {
                            'home_team': teams[0].text.strip(),
                            'away_team': teams[1].text.strip(),
                            'home_score': int(scores[0].text.strip()) if len(scores) > 0 and scores[0].text.strip().isdigit() else None,
                            'away_score': int(scores[1].text.strip()) if len(scores) > 1 and scores[1].text.strip().isdigit() else None,
                            'game_date': date_elem.text.strip() if date_elem else None,
                            'game_status': 'completed' if len(scores) > 0 else 'scheduled',
                            'scraped_at': datetime.now()
                        }
                        games.append(game)
                except Exception as e:
                    logger.warning(f"Error parsing game card: {e}")
                    continue
            
            logger.info(f"Scraped {len(games)} CFB games")
            return games
            
        except Exception as e:
            logger.error(f"Error scraping CFB games: {e}")
            return []
    
    def save_rankings_to_db(self, rankings: List[Dict[str, Any]]):
        """Save team rankings to database."""
        if not self.db_connection:
            logger.error("No database connection available")
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
                INSERT INTO cfb_rankings (rank, team_name, record, scraped_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (team_name, scraped_at::date) 
                DO UPDATE SET rank = EXCLUDED.rank, record = EXCLUDED.record;
            """
            
            for ranking in rankings:
                cursor.execute(insert_query, (
                    ranking['rank'],
                    ranking['team_name'],
                    ranking.get('record'),
                    ranking['scraped_at']
                ))
            
            self.db_connection.commit()
            logger.info(f"Successfully saved {len(rankings)} rankings to database")
            
        except Exception as e:
            logger.error(f"Error saving rankings to database: {e}")
            self.db_connection.rollback()
    
    def save_team_stats_to_db(self, stats: List[Dict[str, Any]]):
        """Save team statistics to database."""
        if not self.db_connection:
            logger.error("No database connection available")
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
                INSERT INTO cfb_team_stats 
                (team_name, games_played, points_per_game, yards_per_game, 
                 passing_yards, rushing_yards, turnovers, penalties, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (team_name, scraped_at::date) 
                DO UPDATE SET 
                    games_played = EXCLUDED.games_played,
                    points_per_game = EXCLUDED.points_per_game,
                    yards_per_game = EXCLUDED.yards_per_game,
                    passing_yards = EXCLUDED.passing_yards,
                    rushing_yards = EXCLUDED.rushing_yards,
                    turnovers = EXCLUDED.turnovers,
                    penalties = EXCLUDED.penalties;
            """
            
            for stat in stats:
                cursor.execute(insert_query, (
                    stat['team_name'],
                    stat['games_played'],
                    stat['points_per_game'],
                    stat['yards_per_game'],
                    stat['passing_yards'],
                    stat['rushing_yards'],
                    stat['turnovers'],
                    stat['penalties'],
                    stat['scraped_at']
                ))
            
            self.db_connection.commit()
            logger.info(f"Successfully saved {len(stats)} team stats to database")
            
        except Exception as e:
            logger.error(f"Error saving team stats to database: {e}")
            self.db_connection.rollback()
    
    def save_games_to_db(self, games: List[Dict[str, Any]]):
        """Save game data to database."""
        if not self.db_connection:
            logger.error("No database connection available")
            return
        
        try:
            cursor = self.db_connection.cursor()
            
            insert_query = """
                INSERT INTO cfb_games 
                (home_team, away_team, home_score, away_score, game_date, game_status, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (home_team, away_team, game_date) 
                DO UPDATE SET 
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score,
                    game_status = EXCLUDED.game_status,
                    scraped_at = EXCLUDED.scraped_at;
            """
            
            for game in games:
                cursor.execute(insert_query, (
                    game['home_team'],
                    game['away_team'],
                    game.get('home_score'),
                    game.get('away_score'),
                    game.get('game_date'),
                    game['game_status'],
                    game['scraped_at']
                ))
            
            self.db_connection.commit()
            logger.info(f"Successfully saved {len(games)} games to database")
            
        except Exception as e:
            logger.error(f"Error saving games to database: {e}")
            self.db_connection.rollback()
    
    def run(self):
        """Execute the complete scraping workflow."""
        try:
            logger.info("Starting CFB scraper...")
            self.connect_to_db()
            
            # Scrape rankings
            rankings = self.scrape_team_rankings()
            if rankings:
                self.save_rankings_to_db(rankings)
            
            # Scrape team stats
            stats = self.scrape_team_stats()
            if stats:
                self.save_team_stats_to_db(stats)
            
            # Scrape games
            games = self.scrape_schedule_and_scores()
            if games:
                self.save_games_to_db(games)
            
            logger.info("CFB scraper completed successfully")
            
        except Exception as e:
            logger.error(f"Error in CFB scraper: {e}")
        finally:
            if self.db_connection:
                self.db_connection.close()
                logger.info("Database connection closed")

if __name__ == "__main__":
    scraper = CFBScraper()
    scraper.run()
