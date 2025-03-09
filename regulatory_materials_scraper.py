import requests
import os
import json
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from datetime import datetime

class RegulatoryMaterialsScraper:
    def __init__(self):
        self.output_dir = "scrapers_output/regulatory_materials"
        self.max_workers = 5
        self.delay = 2  # seconds between requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Define regulatory sources and their URLs
        self.regulatory_sources = {
            "cipc": {
                "base_url": "http://www.cipc.co.za",
                "sections": {
                    "practice_notes": "/Publications/Practice%20Notes",
                    "guidelines": "/Publications/Guidelines",
                    "notices": "/Publications/Notices"
                }
            },
            "jse": {
                "base_url": "https://www.jse.co.za",
                "sections": {
                    "listing_requirements": "/content/JSEContentBuilder/JSE%20Listings%20Requirements",
                    "bulletins": "/content/JSEContentBuilder/JSE%20Bulletins"
                }
            },
            "fsca": {
                "base_url": "https://www.fsca.co.za",
                "sections": {
                    "regulatory_frameworks": "/Regulatory%20Frameworks",
                    "legislation": "/Legislation",
                    "regulations": "/Regulations"
                }
            },
            "takeover_panel": {
                "base_url": "https://trpanel.co.za",
                "sections": {
                    "rules": "/rules",
                    "guidelines": "/guidelines",
                    "practice_notes": "/practice-notes"
                }
            }
        }
        
        self.setup_logging()
        self.create_directories()

    def setup_logging(self):
        """Set up logging configuration"""
        log_filename = f'logs/regulatory_materials_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        os.makedirs('logs', exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Get logger and add handlers
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.info("Regulatory Materials Scraper started")

    def create_directories(self):
        """Create necessary directories for downloads"""
        for regulator in self.regulatory_sources.keys():
            for section in self.regulatory_sources[regulator]['sections'].keys():
                Path(f"{self.output_dir}/{regulator}/{section}").mkdir(parents=True, exist_ok=True)

    def download_file(self, url, output_path):
        """Download a file from URL and save to output path"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logging.info(f"Successfully downloaded {url} to {output_path}")
            return True
        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return False

    def scrape_section(self, regulator, section_name, section_url):
        """Scrape a specific section of a regulatory website"""
        try:
            full_url = f"{self.regulatory_sources[regulator]['base_url']}{section_url}"
            response = self.session.get(full_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF and document links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
                    filename = os.path.basename(href)
                    output_path = f"{self.output_dir}/{regulator}/{section_name}/{filename}"
                    
                    if os.path.exists(output_path):
                        logging.info(f"File already exists: {output_path}")
                        continue
                    
                    if not href.startswith('http'):
                        href = f"{self.regulatory_sources[regulator]['base_url']}{href}"
                    
                    self.download_file(href, output_path)
                    sleep(self.delay)
            
        except Exception as e:
            logging.error(f"Error scraping {full_url}: {str(e)}")

    def run(self):
        """Run the scraper for all regulatory materials"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for regulator, details in self.regulatory_sources.items():
                for section_name, section_url in details['sections'].items():
                    executor.submit(self.scrape_section, regulator, section_name, section_url)
                    sleep(self.delay)

if __name__ == "__main__":
    scraper = RegulatoryMaterialsScraper()
    scraper.run() 