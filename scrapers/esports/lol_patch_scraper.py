#!/usr/bin/env python3
"""
League of Legends Patch Notes Scraper
Automatically scrapes and parses LoL patch notes from official sources
"""

import requests
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import os
import re
import json
from typing import List, Dict, Optional

class LoLPatchScraper:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.base_url = "https://www.leagueoflegends.com/en-us/news/game-updates/"
        self.patch_notes_url = "https://www.leagueoflegends.com/en-us/news/tags/patch-notes/"
        
    def connect_db(self):
        """Establish database connection"""
        return psycopg2.connect(self.database_url)
    
    def fetch_latest_patches(self) -> List[Dict]:
        """Fetch latest patch notes from League website"""
        try:
            response = requests.get(self.patch_notes_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            patches = []
            # Find patch note articles
            articles = soup.find_all('article', class_=['style__Article', 'default-article'])
            
            for article in articles[:5]:  # Get latest 5 patches
                try:
                    title_elem = article.find('h2') or article.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    link_elem = article.find('a', href=True)
                    patch_url = link_elem['href'] if link_elem else None
                    
                    if not patch_url or not patch_url.startswith('http'):
                        patch_url = f"https://www.leagueoflegends.com{patch_url}"
                    
                    # Extract patch version from title
                    version_match = re.search(r'\b(\d+\.\d+)\b', title)
                    if not version_match:
                        continue
                    
                    patch_version = version_match.group(1)
                    
                    # Extract date if available
                    date_elem = article.find('time') or article.find(class_='date')
                    patch_date = None
                    if date_elem:
                        date_text = date_elem.get('datetime') or date_elem.text
                        try:
                            patch_date = datetime.fromisoformat(date_text.split('T')[0])
                        except:
                            patch_date = datetime.now()
                    else:
                        patch_date = datetime.now()
                    
                    patches.append({
                        'version': patch_version,
                        'title': title,
                        'url': patch_url,
                        'date': patch_date
                    })
                    
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            return patches
            
        except Exception as e:
            print(f"Error fetching patches: {e}")
            return []
    
    def parse_patch_details(self, patch_url: str) -> Dict:
        """Parse detailed patch notes from individual patch page"""
        try:
            response = requests.get(patch_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract full patch notes text
            content_div = soup.find('div', class_=['article-content', 'content'])
            patch_text = content_div.get_text(separator='\n', strip=True) if content_div else ''
            
            # Parse champion changes
            champion_changes = self.extract_champion_changes(soup, patch_text)
            
            return {
                'full_text': patch_text,
                'champion_changes': champion_changes
            }
            
        except Exception as e:
            print(f"Error parsing patch details from {patch_url}: {e}")
            return {'full_text': '', 'champion_changes': []}
    
    def extract_champion_changes(self, soup, patch_text: str) -> List[Dict]:
        """Extract individual champion balance changes"""
        changes = []
        
        # Look for champion sections
        champion_sections = soup.find_all(['h3', 'h4'], text=re.compile(r'^[A-Z]'))
        
        for section in champion_sections:
            try:
                champion_name = section.text.strip()
                
                # Get next sibling elements for change details
                next_elem = section.find_next_sibling()
                change_text = ''
                
                while next_elem and next_elem.name not in ['h3', 'h4']:
                    change_text += next_elem.get_text(separator=' ', strip=True) + ' '
                    next_elem = next_elem.find_next_sibling()
                
                if change_text:
                    # Determine change type
                    change_type = 'adjustment'
                    if re.search(r'\b(buff|increase|improved|enhanced)\b', change_text, re.I):
                        change_type = 'buff'
                    elif re.search(r'\b(nerf|decrease|reduced|lowered)\b', change_text, re.I):
                        change_type = 'nerf'
                    elif re.search(r'\b(rework|reworked|changed)\b', change_text, re.I):
                        change_type = 'adjustment'
                    
                    # Extract ability affected
                    ability = 'stats'
                    if re.search(r'\bpassive\b', change_text, re.I):
                        ability = 'passive'
                    elif re.search(r'\bQ\b', change_text):
                        ability = 'Q'
                    elif re.search(r'\bW\b', change_text):
                        ability = 'W'
                    elif re.search(r'\bE\b', change_text):
                        ability = 'E'
                    elif re.search(r'\bR\b|\bultimate\b', change_text, re.I):
                        ability = 'R'
                    
                    changes.append({
                        'champion': champion_name,
                        'type': change_type,
                        'ability': ability,
                        'summary': change_text[:500]  # Limit length
                    })
                    
            except Exception as e:
                print(f"Error extracting change for {section}: {e}")
                continue
        
        return changes
    
    def save_patch_to_db(self, patch_info: Dict, patch_details: Dict):
        """Save patch and changes to database"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            # Insert patch notes
            cur.execute("""
                INSERT INTO patch_notes 
                (game, patch_version, patch_name, release_date, official_url, 
                 patch_notes_text, scrape_source, is_major_patch)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (game, patch_version) 
                DO UPDATE SET 
                    last_updated = NOW(),
                    patch_notes_text = EXCLUDED.patch_notes_text
                RETURNING id;
            """, (
                'LoL',
                patch_info['version'],
                patch_info['title'],
                patch_info['date'],
                patch_info['url'],
                patch_details['full_text'],
                self.patch_notes_url,
                True  # Assume all are major patches
            ))
            
            patch_id = cur.fetchone()[0]
            
            # Insert champion changes
            for change in patch_details['champion_changes']:
                cur.execute("""
                    INSERT INTO lol_champion_changes
                    (patch_id, champion_name, change_type, ability_affected, 
                     change_summary, estimated_impact)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING;
                """, (
                    patch_id,
                    change['champion'],
                    change['type'],
                    change['ability'],
                    change['summary'],
                    'moderate'  # Default impact
                ))
            
            conn.commit()
            cur.close()
            conn.close()
            
            print(f"Saved patch {patch_info['version']} with {len(patch_details['champion_changes'])} changes")
            return True
            
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def log_scrape(self, status: str, patches_found: int, new_patches: int, error: str = None):
        """Log scraping operation"""
        try:
            conn = self.connect_db()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO patch_scrape_log
                (game, source_url, patches_found, new_patches, scrape_status, error_message)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, ('LoL', self.patch_notes_url, patches_found, new_patches, status, error))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Logging error: {e}")
    
    def run(self):
        """Main scraping process"""
        print("Starting League of Legends patch scraper...")
        
        try:
            # Fetch latest patches
            patches = self.fetch_latest_patches()
            print(f"Found {len(patches)} patches")
            
            new_patches = 0
            
            for patch in patches:
                print(f"Processing patch {patch['version']}...")
                
                # Parse detailed patch notes
                details = self.parse_patch_details(patch['url'])
                
                # Save to database
                if self.save_patch_to_db(patch, details):
                    new_patches += 1
            
            # Log successful scrape
            self.log_scrape('success', len(patches), new_patches)
            print(f"Scraping completed! Processed {new_patches} new patches.")
            
        except Exception as e:
            print(f"Scraping failed: {e}")
            self.log_scrape('failed', 0, 0, str(e))

if __name__ == "__main__":
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        exit(1)
    
    scraper = LoLPatchScraper(database_url)
    scraper.run()
