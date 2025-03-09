#!/usr/bin/env python3
"""
Script to download missing legislation from the checklist.
This script supports downloading specific acts or downloading multiple acts concurrently.
"""

import os
import sys
import subprocess
import argparse
import requests
import logging
import concurrent.futures
from pathlib import Path
from tqdm import tqdm
import time
import random

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegislationDownloader")

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "scrapers_output", "core_legislation")
CHECKLIST_FILE = os.path.join(BASE_DIR, "SA_LEGAL_LLM_CHECKLIST.md")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class LegislationDownloader:
    """Class to download missing legislation from various sources."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory of the repository."""
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, "scrapers_output", "core_legislation")
        self.checklist_file = os.path.join(base_dir, "SA_LEGAL_LLM_CHECKLIST.md")
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Create output directories if they don't exist
        os.makedirs(os.path.join(self.output_dir, "constitutional"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "criminal"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "commercial"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "labor"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "environmental"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "tax"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "digital"), exist_ok=True)
    
    def is_legislation_present(self, act, category):
        """Check if the legislation is already downloaded."""
        category_dir = os.path.join(self.output_dir, category)
        
        # Check if any file in the directory contains the act name
        if os.path.exists(category_dir):
            for filename in os.listdir(category_dir):
                if act.lower() in filename.lower():
                    logger.info(f"{act} already exists in {category_dir}")
                    return True
        
        return False
    
    def download_pdf_from_govza(self, act, category, urls=None, output_filename=None):
        """Download a PDF from gov.za or specified URLs."""
        if self.is_legislation_present(act, category):
            logger.info(f"{act} already downloaded, skipping")
            return True
            
        if not urls:
            logger.error(f"No URLs provided for {act}")
            return False
            
        if not output_filename:
            # Create a sanitized filename
            output_filename = act.replace(" ", "_").replace("/", "_").lower() + ".pdf"
        
        output_path = os.path.join(self.output_dir, category, output_filename)
        
        # Try each URL until successful
        for url in urls:
            try:
                logger.info(f"Downloading {act} from {url}")
                
                # Add a small random delay to avoid overloading servers
                time.sleep(random.uniform(0.5, 2.0))
                
                response = self.session.get(url, stream=True)
                response.raise_for_status()
                
                # Get the total file size for progress bar
                total_size = int(response.headers.get('content-length', 0))
                
                # Show a progress bar
                with open(output_path, 'wb') as f, tqdm(
                    desc=act,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        bar.update(size)
                
                logger.info(f"Successfully downloaded {act} to {output_path}")
                
                # Update the checklist
                self.update_checklist_item(act)
                
                return True
                
            except Exception as e:
                logger.warning(f"Failed to download {act} from {url}: {e}")
                continue
        
        logger.error(f"All download attempts failed for {act}")
        return False
    
    def update_checklist_item(self, act):
        """Update the checklist to mark an item as completed."""
        try:
            # Read the current checklist
            with open(self.checklist_file, 'r') as f:
                lines = f.readlines()
            
            # Find the line containing the act and update it
            for i, line in enumerate(lines):
                # Look for unchecked items containing the act name
                if '- [ ]' in line and act.lower() in line.lower():
                    lines[i] = line.replace('- [ ]', '- [x]')
                    logger.info(f"Updated checklist for {act}")
                    break
            
            # Write the updated checklist
            with open(self.checklist_file, 'w') as f:
                f.writelines(lines)
                
            # Run the checklist update script
            self.run_checklist_update()
                
        except Exception as e:
            logger.error(f"Failed to update checklist for {act}: {e}")
    
    def run_checklist_update(self):
        """Run the update_llm_checklist.py script to recalculate progress."""
        try:
            subprocess.run([sys.executable, os.path.join(self.base_dir, "scripts", "update_llm_checklist.py")], 
                           check=True, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE)
            logger.info("Updated checklist statistics")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update checklist statistics: {e}")
    
    def download_copyright_act(self):
        """Download the Copyright Act 98 of 1978."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201504/act-98-1978.pdf",
            "https://www.wipo.int/edocs/lexdocs/laws/en/za/za002en.pdf",
            "https://cipc.co.za/images/Copyright_Act.pdf"
        ]
        return self.download_pdf_from_govza(
            "Copyright Act 98 of 1978",
            "commercial",
            urls=urls
        )
    
    def download_prevention_of_organised_crime_act(self):
        """Download the Prevention of Organised Crime Act 121 of 1998."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a121-98.pdf",
            "https://www.justice.gov.za/legislation/acts/1998-121.pdf"
        ]
        return self.download_pdf_from_govza(
            "Prevention of Organised Crime Act 121 of 1998",
            "criminal",
            urls=urls
        )
    
    def download_basic_conditions_of_employment_act(self):
        """Download the Basic Conditions of Employment Act 75 of 1997."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a75-97.pdf",
            "https://www.labour.gov.za/DocumentCenter/Acts/Basic%20Conditions%20of%20Employment%20Act.pdf"
        ]
        return self.download_pdf_from_govza(
            "Basic Conditions of Employment Act 75 of 1997",
            "labor",
            urls=urls
        )
    
    def download_national_environmental_management_act(self):
        """Download the National Environmental Management Act 107 of 1998."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a107-98.pdf",
            "https://www.environment.gov.za/sites/default/files/legislations/nema_amendment_act107.pdf"
        ]
        return self.download_pdf_from_govza(
            "National Environmental Management Act 107 of 1998",
            "environmental",
            urls=urls
        )
    
    def download_mineral_resources_act(self):
        """Download the Mineral and Petroleum Resources Development Act 28 of 2002."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a28-020.pdf",
            "https://www.dmr.gov.za/Portals/0/pdf/acts/mprda.pdf"
        ]
        return self.download_pdf_from_govza(
            "Mineral and Petroleum Resources Development Act 28 of 2002",
            "environmental",
            urls=urls
        )
    
    def download_income_tax_act(self):
        """Download the Income Tax Act 58 of 1962."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201505/act-58-1962s.pdf",
            "https://www.sars.gov.za/wp-content/uploads/Legal/Acts/LAPD-LPrim-Act-2012-01-Income-Tax-Act-1962.pdf"
        ]
        return self.download_pdf_from_govza(
            "Income Tax Act 58 of 1962",
            "tax",
            urls=urls
        )
    
    def download_tax_administration_act(self):
        """Download the Tax Administration Act 28 of 2011."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a282011.pdf",
            "https://www.sars.gov.za/wp-content/uploads/Legal/Acts/LAPD-LPrim-Act-2012-02-Tax-Administration-Act-2011.pdf",
            "https://www.saflii.org/za/legis/consol_act/taa2011215/taa2011a28o2011.pdf"
        ]
        return self.download_pdf_from_govza(
            "Tax Administration Act 28 of 2011",
            "tax",
            urls=urls
        )
    
    def download_customs_and_excise_act(self):
        """Download the Customs and Excise Act 91 of 1964."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201505/act-91-1964s.pdf",
            "https://www.sars.gov.za/wp-content/uploads/Legal/Acts/LAPD-LPrim-Act-2012-04-Customs-and-Excise-Act-1964.pdf"
        ]
        return self.download_pdf_from_govza(
            "Customs and Excise Act 91 of 1964",
            "tax",
            urls=urls
        )
    
    def download_electronic_communications_act(self):
        """Download the Electronic Communications and Transactions Act 25 of 2002."""
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/a25-02.pdf",
            "https://www.justice.gov.za/legislation/acts/2002-025.pdf"
        ]
        return self.download_pdf_from_govza(
            "Electronic Communications and Transactions Act 25 of 2002",
            "digital",
            urls=urls
        )
    
    def download_all_missing_legislation(self):
        """Download all missing legislation concurrently."""
        logger.info("Starting concurrent download of all missing legislation")
        
        download_functions = [
            self.download_copyright_act,
            self.download_prevention_of_organised_crime_act,
            self.download_basic_conditions_of_employment_act,
            self.download_national_environmental_management_act,
            self.download_mineral_resources_act,
            self.download_income_tax_act,
            self.download_tax_administration_act,
            self.download_customs_and_excise_act,
            self.download_electronic_communications_act
        ]
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all downloads and keep track of futures
            future_to_func = {executor.submit(func): func.__name__ for func in download_functions}
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_func):
                func_name = future_to_func[future]
                try:
                    result = future.result()
                    logger.info(f"Completed {func_name}: {'Success' if result else 'Failed'}")
                    results.append((func_name, result))
                except Exception as e:
                    logger.error(f"Error in {func_name}: {e}")
                    results.append((func_name, False))
        
        # Summarize results
        successes = sum(1 for _, result in results if result)
        logger.info(f"Downloaded {successes}/{len(download_functions)} missing documents")
        
        return results

def main():
    """Main function to run the legislation downloader."""
    parser = argparse.ArgumentParser(description="Download missing legislation from various sources.")
    parser.add_argument("--all", action="store_true", help="Download all missing legislation concurrently")
    parser.add_argument("--copyright", action="store_true", help="Download the Copyright Act")
    parser.add_argument("--organised-crime", action="store_true", help="Download the Prevention of Organised Crime Act")
    parser.add_argument("--employment", action="store_true", help="Download the Basic Conditions of Employment Act")
    parser.add_argument("--environmental", action="store_true", help="Download the National Environmental Management Act")
    parser.add_argument("--mineral", action="store_true", help="Download the Mineral Resources Development Act")
    parser.add_argument("--income-tax", action="store_true", help="Download the Income Tax Act")
    parser.add_argument("--tax-admin", action="store_true", help="Download the Tax Administration Act")
    parser.add_argument("--customs", action="store_true", help="Download the Customs and Excise Act")
    parser.add_argument("--electronic", action="store_true", help="Download the Electronic Communications Act")
    
    args = parser.parse_args()
    
    downloader = LegislationDownloader(BASE_DIR)
    
    if args.all:
        results = downloader.download_all_missing_legislation()
        sys.exit(0 if all(result for _, result in results) else 1)
    
    # Individual downloads
    if args.copyright:
        downloader.download_copyright_act()
    if args.organised_crime:
        downloader.download_prevention_of_organised_crime_act()
    if args.employment:
        downloader.download_basic_conditions_of_employment_act()
    if args.environmental:
        downloader.download_national_environmental_management_act()
    if args.mineral:
        downloader.download_mineral_resources_act()
    if args.income_tax:
        downloader.download_income_tax_act()
    if args.tax_admin:
        downloader.download_tax_administration_act()
    if args.customs:
        downloader.download_customs_and_excise_act()
    if args.electronic:
        downloader.download_electronic_communications_act()
    
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        parser.print_help()

if __name__ == "__main__":
    main() 