#!/usr/bin/env python3
"""
download_missing_legislation.py - Script to download missing core legislation.

This script works with the organize_documents.py script to identify and download
missing core legislation from government and legal websites.
"""

import os
import sys
import requests
import logging
import re
import argparse
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegislationDownloader")

# Constants
SCRAPERS_OUTPUT_DIR = "scrapers_output"
CORE_LEGISLATION_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "core_legislation")

# Key legislation that should be present
KEY_LEGISLATION = {
    "commercial": [
        {
            "name": "Companies Act",
            "number": "71",
            "year": "2008",
            "url": "https://www.gov.za/documents/companies-act",
            "description": "South African Companies Act"
        },
        {
            "name": "Consumer Protection Act",
            "number": "68",
            "year": "2008",
            "url": "https://www.gov.za/documents/consumer-protection-act",
            "description": "Consumer Protection Act"
        },
        {
            "name": "Competition Act",
            "number": "89",
            "year": "1998",
            "url": "https://www.gov.za/documents/competition-act",
            "description": "Competition Act"
        },
        {
            "name": "Copyright Act",
            "number": "98",
            "year": "1978",
            "url": "https://www.gov.za/documents/copyright-act",
            "description": "Copyright Act"
        }
    ],
    "financial": [
        {
            "name": "Financial Intelligence Centre Act",
            "number": "38",
            "year": "2001",
            "url": "https://www.gov.za/documents/financial-intelligence-centre-act",
            "description": "Financial Intelligence Centre Act"
        },
        {
            "name": "Financial Sector Regulation Act",
            "number": "9",
            "year": "2017",
            "url": "https://www.gov.za/documents/financial-sector-regulation-act-9-2017-22-aug-2017-0000",
            "description": "Financial Sector Regulation Act"
        },
        {
            "name": "National Credit Act",
            "number": "34",
            "year": "2005",
            "url": "https://www.gov.za/documents/national-credit-act",
            "description": "National Credit Act"
        }
    ],
    "regulatory": [
        {
            "name": "Promotion of Access to Information Act",
            "number": "2",
            "year": "2000",
            "url": "https://www.gov.za/documents/promotion-access-information-act",
            "description": "Promotion of Access to Information Act"
        },
        {
            "name": "Protection of Personal Information Act",
            "number": "4",
            "year": "2013",
            "url": "https://www.gov.za/documents/protection-personal-information-act",
            "description": "Protection of Personal Information Act"
        },
        {
            "name": "Broad-Based Black Economic Empowerment Act",
            "number": "53",
            "year": "2003",
            "url": "https://www.gov.za/documents/broad-based-black-economic-empowerment-act",
            "description": "Broad-Based Black Economic Empowerment Act"
        }
    ]
}

class LegislationDownloader:
    """Class to handle the downloading of missing legislation."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory of the repository."""
        self.base_dir = base_dir
        self.core_legislation_dir = os.path.join(base_dir, CORE_LEGISLATION_DIR)
        
        # Create subdirectories if they don't exist
        for category in KEY_LEGISLATION.keys():
            category_dir = os.path.join(self.core_legislation_dir, category)
            os.makedirs(category_dir, exist_ok=True)
        
        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def is_legislation_present(self, act, category):
        """Check if legislation is already present in the repository."""
        category_dir = os.path.join(self.core_legislation_dir, category)
        act_pattern = f"{act['name']}.*{act['number']}.*{act['year']}|{act['number']}.*{act['year']}.*{act['name']}"
        
        for root, _, files in os.walk(category_dir):
            for file in files:
                if re.search(act_pattern, file, re.IGNORECASE):
                    logger.info(f"Found {act['name']} at {os.path.join(root, file)}")
                    return True
        
        return False
    
    def download_pdf_from_govza(self, act, category):
        """
        Download a PDF from the gov.za website.
        
        The gov.za website typically has a page for each act with links to PDF versions.
        This method finds those links and downloads the PDF.
        """
        url = act['url']
        logger.info(f"Downloading {act['name']} from {url}")
        
        try:
            # Get the main page for the act
            response = self.session.get(url)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for PDF links
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf'):
                    pdf_links.append(urljoin(url, href))
            
            if not pdf_links:
                logger.warning(f"No PDF links found for {act['name']} at {url}")
                return False
            
            # Download the first PDF (typically the main act)
            pdf_url = pdf_links[0]
            
            # Create a temporary file to download to
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                pdf_response = self.session.get(pdf_url, stream=True)
                pdf_response.raise_for_status()
                
                # Write the PDF to the temporary file
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                
                temp_file_path = temp_file.name
            
            # Construct the final path
            filename = f"{act['name']} {act['number']} of {act['year']}.pdf"
            target_path = os.path.join(self.core_legislation_dir, category, filename)
            
            # Move the temporary file to the final location
            shutil.move(temp_file_path, target_path)
            logger.info(f"Downloaded {act['name']} to {target_path}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error downloading {act['name']}: {str(e)}")
            return False
    
    def download_all_missing_legislation(self):
        """Download all missing legislation."""
        success_count = 0
        failure_count = 0
        
        for category, acts in KEY_LEGISLATION.items():
            for act in acts:
                if not self.is_legislation_present(act, category):
                    success = self.download_pdf_from_govza(act, category)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
        
        logger.info(f"Download complete. Successes: {success_count}, Failures: {failure_count}")
        return success_count, failure_count

def main():
    """Main function to run the legislation downloader."""
    parser = argparse.ArgumentParser(description="Download missing core legislation.")
    parser.add_argument("--category", choices=KEY_LEGISLATION.keys(), help="Download only legislation in this category")
    parser.add_argument("--act", help="Download only the specified act (partial name match)")
    parser.add_argument("--force", action="store_true", help="Force download even if already present")
    parser.add_argument("--constitution", action="store_true", help="Download the Constitution of South Africa")
    args = parser.parse_args()
    
    downloader = LegislationDownloader()
    
    if args.constitution:
        # Special case for the Constitution
        logger.info("Downloading the Constitution of South Africa (1996)")
        
        # Create the constitutional category if it doesn't exist
        const_dir = os.path.join(downloader.core_legislation_dir, "constitutional")
        os.makedirs(const_dir, exist_ok=True)
        
        # URLs for the Constitution
        constitution_urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/act108of1996s.pdf",  # Official version
            "https://www.justice.gov.za/legislation/constitution/SAConstitution-web-eng.pdf",  # Justice dept version
            "https://www.concourt.org.za/images/phocadownload/the_constitution/the-constitution-of-the-republic-of-south-africa.pdf"  # Constitutional Court version
        ]
        
        # Try each URL until one works
        success = False
        for url in constitution_urls:
            try:
                # Create a temporary file to download to
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    logger.info(f"Trying to download from {url}")
                    
                    # Set up a session with proper headers
                    session = requests.Session()
                    session.headers.update({
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    })
                    
                    # Download the file
                    response = session.get(url, stream=True)
                    response.raise_for_status()
                    
                    # Write the PDF to a temporary file
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                    
                    temp_file_path = temp_file.name
                
                # Construct the final path
                target_path = os.path.join(const_dir, "Constitution of South Africa 1996.pdf")
                
                # Move the temporary file to the final location
                shutil.move(temp_file_path, target_path)
                logger.info(f"Constitution downloaded to {target_path}")
                
                success = True
                break
            except Exception as e:
                logger.error(f"Error downloading from {url}: {str(e)}")
        
        if success:
            return 0
        else:
            logger.error("Failed to download the Constitution from any source")
            return 1
    
    elif args.act:
        # Download a specific act
        found = False
        for category, acts in KEY_LEGISLATION.items():
            if args.category and category != args.category:
                continue
                
            for act in acts:
                if args.act.lower() in act['name'].lower():
                    if args.force or not downloader.is_legislation_present(act, category):
                        if downloader.download_pdf_from_govza(act, category):
                            logger.info(f"Successfully downloaded {act['name']}")
                        else:
                            logger.error(f"Failed to download {act['name']}")
                    else:
                        logger.info(f"{act['name']} is already present")
                    found = True
        
        if not found:
            logger.error(f"No acts found matching '{args.act}'")
    
    elif args.category:
        # Download all acts in a category
        success_count = 0
        failure_count = 0
        
        for act in KEY_LEGISLATION[args.category]:
            if args.force or not downloader.is_legislation_present(act, args.category):
                success = downloader.download_pdf_from_govza(act, args.category)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
        
        logger.info(f"Category download complete. Successes: {success_count}, Failures: {failure_count}")
    
    else:
        # Download all missing legislation
        downloader.download_all_missing_legislation()

if __name__ == "__main__":
    main() 