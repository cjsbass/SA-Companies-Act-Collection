import requests
import os
import json
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from time import sleep
from datetime import datetime

class CoreLegislationDownloader:
    def __init__(self, output_dir="scrapers_output/core_legislation", max_workers=2, delay=2):
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Set up logging
        self.setup_logging()
        
        # Create output directories
        self.create_directories()
        
        # Define core legislation to download - gov.za only
        self.core_legislation = {
            "constitutional": {
                "Constitution of South Africa": {
                    "number": "108",
                    "year": "1996",
                    "url": "https://www.gov.za/sites/default/files/gcis_document/201409/act108of1996s.pdf"
                }
            },
            "commercial": {
                "Companies Act": {
                    "number": "71",
                    "year": "2008",
                    "url": "https://www.gov.za/documents/companies-act"
                },
                "Consumer Protection Act": {
                    "number": "68",
                    "year": "2008",
                    "url": "https://www.gov.za/documents/consumer-protection-act"
                },
                "Competition Act": {
                    "number": "89",
                    "year": "1998",
                    "url": "https://www.gov.za/documents/competition-act"
                },
                "National Credit Act": {
                    "number": "34",
                    "year": "2005",
                    "url": "https://www.gov.za/documents/national-credit-act"
                }
            },
            "financial": {
                "Financial Intelligence Centre Act": {
                    "number": "38",
                    "year": "2001",
                    "url": "https://www.gov.za/documents/financial-intelligence-centre-act"
                },
                "Financial Advisory and Intermediary Services Act": {
                    "number": "37",
                    "year": "2002",
                    "url": "https://www.gov.za/documents/financial-advisory-and-intermediary-services-act"
                },
                "Banks Act": {
                    "number": "94",
                    "year": "1990",
                    "url": "https://static.pmg.org.za/files/B94-1990.pdf"
                }
            },
            "regulatory": {
                "Protection of Personal Information Act": {
                    "number": "4",
                    "year": "2013",
                    "url": "https://www.gov.za/documents/protection-personal-information-act"
                },
                "Promotion of Administrative Justice Act": {
                    "number": "3",
                    "year": "2000",
                    "url": "https://www.gov.za/documents/promotion-administrative-justice-act"
                },
                "Broad-Based Black Economic Empowerment Act": {
                    "number": "53",
                    "year": "2003",
                    "url": "https://www.gov.za/documents/broad-based-black-economic-empowerment-act"
                }
            }
        }

    def setup_logging(self):
        """Set up logging configuration"""
        log_filename = f'logs/core_legislation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        os.makedirs('logs', exist_ok=True)
        
        # Remove any existing handlers
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
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
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.info("Core Legislation Downloader started - gov.za only")

    def create_directories(self):
        """Create necessary directories for downloads"""
        for category in ["commercial", "financial", "regulatory"]:
            Path(f"{self.output_dir}/{category}").mkdir(parents=True, exist_ok=True)

    def download_file(self, url, output_path):
        """Download a file from URL and save to output path"""
        try:
            logging.info(f"Attempting to download {url}")
            response = self.session.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logging.warning(f"Warning: Content-Type is not PDF: {content_type}")
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was downloaded
            if os.path.getsize(output_path) > 0:
                logging.info(f"Successfully downloaded {url} to {output_path}")
                return True
            else:
                logging.error(f"Downloaded file is empty: {output_path}")
                os.remove(output_path)
                return False
                
        except requests.exceptions.Timeout:
            logging.error(f"Timeout downloading {url}")
            return False
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading {url}: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error downloading {url}: {str(e)}")
            return False

    def extract_download_url(self, page_url):
        """Extract actual download URL from legislation page"""
        try:
            logging.info(f"Extracting download URL from {page_url}")
            response = self.session.get(page_url, timeout=60)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF download link
            pdf_links = soup.find_all('a', href=lambda x: x and x.endswith('.pdf'))
            
            if not pdf_links:
                logging.error(f"No PDF links found on {page_url}")
                return None
                
            # Log all found PDF links
            for link in pdf_links:
                logging.info(f"Found PDF link: {link['href']}")
            
            # Use the first PDF link found
            return pdf_links[0]['href']
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout accessing {page_url}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error accessing {page_url}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error processing {page_url}: {str(e)}")
            return None

    def download_legislation(self, category, name, details):
        """Download legislation from source"""
        try:
            output_filename = f"{name.replace(' ', '_')}_{details['number']}_{details['year']}.pdf"
            output_path = f"{self.output_dir}/{category}/{output_filename}"
            
            if os.path.exists(output_path):
                logging.info(f"File already exists: {output_path}")
                return
            
            # If URL ends with .pdf, download directly
            if details['url'].lower().endswith('.pdf'):
                self.download_file(details['url'], output_path)
            else:
                # Otherwise try to extract PDF URL from page
                download_url = self.extract_download_url(details['url'])
                if download_url:
                    if not download_url.startswith('http'):
                        download_url = f"https://www.gov.za{download_url}"
                    self.download_file(download_url, output_path)
            sleep(self.delay)
            
        except Exception as e:
            logging.error(f"Error processing {name}: {str(e)}")

    def run(self):
        """Run the downloader for all legislation"""
        try:
            logging.info("Starting download process...")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for category, acts in self.core_legislation.items():
                    logging.info(f"Processing category: {category}")
                    for name, details in acts.items():
                        executor.submit(self.download_legislation, category, name, details)
                        sleep(self.delay)
            logging.info("Download process completed")
            
        except Exception as e:
            logging.error(f"Error in run process: {str(e)}")

if __name__ == "__main__":
    downloader = CoreLegislationDownloader()
    downloader.run() 