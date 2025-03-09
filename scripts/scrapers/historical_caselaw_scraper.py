import requests
import os
import json
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from datetime import datetime
import re

class HistoricalCaseLawScraper:
    def __init__(self):
        self.output_dir = "scrapers_output/historical_caselaw"
        self.max_workers = 5
        self.delay = 2  # seconds between requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Define court sources and their URLs
        self.court_sources = {
            "sca": {
                "base_url": "http://www.saflii.org/za/cases/ZASCA",
                "years": range(1990, 2023),  # Pre-2023 cases
                "pattern": r"ZASCA/\d{4}/\d+"
            },
            "constitutional": {
                "base_url": "http://www.saflii.org/za/cases/ZACC",
                "years": range(1995, 2023),  # Pre-2023 cases
                "pattern": r"ZACC/\d{4}/\d+"
            },
            "high_courts": {
                "base_url": "http://www.saflii.org/za/cases",
                "years": range(1990, 2023),
                "pattern": r"Z[A-Z]+HC/\d{4}/\d+",
                "courts": {
                    "ZAGPJHC": "Johannesburg High Court",
                    "ZAWCHC": "Western Cape High Court",
                    "ZAKZDHC": "KwaZulu-Natal High Court",
                    "ZAECGHC": "Eastern Cape High Court"
                }
            },
            "competition": {
                "base_url": "http://www.saflii.org/za/cases/ZACT",
                "years": range(1999, 2023),
                "pattern": r"ZACT/\d{4}/\d+"
            }
        }
        
        self.setup_logging()
        self.create_directories()

    def setup_logging(self):
        """Set up logging configuration"""
        log_filename = f'logs/historical_caselaw_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
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
        
        logging.info("Historical Case Law Scraper started")

    def create_directories(self):
        """Create necessary directories for downloads"""
        # Create main court directories
        for court in self.court_sources.keys():
            if court == "high_courts":
                # Create subdirectories for each high court
                for hc_code in self.court_sources[court]["courts"].keys():
                    Path(f"{self.output_dir}/{hc_code}").mkdir(parents=True, exist_ok=True)
            else:
                Path(f"{self.output_dir}/{court}").mkdir(parents=True, exist_ok=True)

    def download_case(self, url, output_path):
        """Download a case from URL and save to output path"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the HTML and extract the main content
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find('div', class_='judgment-body')
            
            if main_content:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(main_content))
                logging.info(f"Successfully downloaded {url} to {output_path}")
                return True
            else:
                logging.error(f"No main content found for {url}")
                return False
                
        except Exception as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return False

    def scrape_year(self, court, year):
        """Scrape all cases for a specific court and year"""
        try:
            if court == "high_courts":
                for hc_code, hc_name in self.court_sources[court]["courts"].items():
                    url = f"{self.court_sources[court]['base_url']}{hc_code}/{year}/"
                    self.scrape_court_year(hc_code, url, year, self.court_sources[court]['pattern'])
            else:
                url = f"{self.court_sources[court]['base_url']}{year}/"
                self.scrape_court_year(court, url, year, self.court_sources[court]['pattern'])
            
        except Exception as e:
            logging.error(f"Error scraping {court} for year {year}: {str(e)}")

    def scrape_court_year(self, court_code, url, year, pattern):
        """Scrape all cases for a specific court, year combination"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all case links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if re.search(pattern, href):
                    case_number = href.split('/')[-1]
                    output_path = f"{self.output_dir}/{court_code}/{year}_{case_number}.html"
                    
                    if os.path.exists(output_path):
                        logging.info(f"Case already exists: {output_path}")
                        continue
                    
                    if not href.startswith('http'):
                        href = f"http://www.saflii.org{href}"
                    
                    self.download_case(href, output_path)
                    sleep(self.delay)
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")

    def run(self):
        """Run the scraper for all historical case law"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for court, details in self.court_sources.items():
                for year in details['years']:
                    executor.submit(self.scrape_year, court, year)
                    sleep(self.delay)

if __name__ == "__main__":
    scraper = HistoricalCaseLawScraper()
    scraper.run() 