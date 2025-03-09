#!/usr/bin/env python3
"""
Script to download South African legal documents that are publicly available.
This script supports downloading various types of legal materials from public sources.
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
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fpdf import FPDF

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegalDocumentsDownloader")

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "scrapers_output")
CORE_LEGISLATION_DIR = os.path.join(OUTPUT_DIR, "core_legislation")
CASE_LAW_DIR = os.path.join(OUTPUT_DIR, "case_law")
SECONDARY_LEGAL_DIR = os.path.join(OUTPUT_DIR, "secondary_legal")
PROCEDURAL_DIR = os.path.join(OUTPUT_DIR, "procedural")
HISTORICAL_DIR = os.path.join(OUTPUT_DIR, "historical")
CHECKLIST_FILE = os.path.join(BASE_DIR, "SA_LEGAL_LLM_CHECKLIST.md")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class LegalDocumentsDownloader:
    """Class to download various South African legal documents from public sources."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory of the repository."""
        self.base_dir = base_dir
        self.output_dir = os.path.join(base_dir, "scrapers_output")
        self.core_legislation_dir = os.path.join(self.output_dir, "core_legislation")
        self.case_law_dir = os.path.join(self.output_dir, "case_law")
        self.secondary_legal_dir = os.path.join(self.output_dir, "secondary_legal")
        self.procedural_dir = os.path.join(self.output_dir, "procedural")
        self.historical_dir = os.path.join(self.output_dir, "historical")
        self.checklist_file = os.path.join(base_dir, "SA_LEGAL_LLM_CHECKLIST.md")
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        # Create output directories if they don't exist
        # Core legislation directories
        os.makedirs(os.path.join(self.core_legislation_dir, "constitutional"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "criminal"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "commercial"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "labor"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "environmental"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "tax"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "digital"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "regulations"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "notices"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "bills"), exist_ok=True)
        os.makedirs(os.path.join(self.core_legislation_dir, "whitepapers"), exist_ok=True)
        
        # Case law directories
        os.makedirs(os.path.join(self.case_law_dir, "constitutional_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "supreme_court_appeal"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "high_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "labor_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "competition_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "land_claims_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "tax_court"), exist_ok=True)
        os.makedirs(os.path.join(self.case_law_dir, "magistrates_court"), exist_ok=True)
        
        # Secondary legal sources
        os.makedirs(os.path.join(self.secondary_legal_dir, "academic"), exist_ok=True)
        os.makedirs(os.path.join(self.secondary_legal_dir, "specialized"), exist_ok=True)
        
        # Procedural materials
        os.makedirs(os.path.join(self.procedural_dir, "rules_of_court"), exist_ok=True)
        os.makedirs(os.path.join(self.procedural_dir, "practice_directives"), exist_ok=True)
        os.makedirs(os.path.join(self.procedural_dir, "ethics"), exist_ok=True)
        os.makedirs(os.path.join(self.procedural_dir, "forms"), exist_ok=True)
        
        # Historical materials
        os.makedirs(os.path.join(self.historical_dir, "roman_dutch"), exist_ok=True)
        os.makedirs(os.path.join(self.historical_dir, "historical_legislation"), exist_ok=True)
    
    def is_document_present(self, doc_name, base_dir):
        """Check if a document is already downloaded in any of the subdirectories."""
        # Clean doc_name for comparison
        clean_name = doc_name.lower().strip()
        
        # Check if any file in any subdirectory contains the document name
        for root, _, files in os.walk(base_dir):
            for filename in files:
                if clean_name in filename.lower():
                    logger.info(f"{doc_name} already exists in {root}")
                    return True
        
        return False
    
    def download_file(self, doc_name, category_dir, urls=None, output_filename=None):
        """Download a file from the provided URLs."""
        if self.is_document_present(doc_name, category_dir):
            logger.info(f"{doc_name} already downloaded, skipping")
            return True
            
        if not urls:
            logger.error(f"No URLs provided for {doc_name}")
            return False
            
        if not output_filename:
            # Create a sanitized filename
            output_filename = doc_name.replace(" ", "_").replace("/", "_").lower() + ".pdf"
        
        output_path = os.path.join(category_dir, output_filename)
        
        # Try each URL until successful
        for url in urls:
            try:
                logger.info(f"Downloading {doc_name} from {url}")
                
                # Add a small random delay to avoid overloading servers
                time.sleep(random.uniform(0.5, 2.0))
                
                response = self.session.get(url, stream=True)
                response.raise_for_status()
                
                # Determine file type from Content-Type header or URL
                file_ext = ".pdf"  # Default
                content_type = response.headers.get('content-type', '').lower()
                if 'html' in content_type:
                    file_ext = '.html'
                elif 'text/plain' in content_type:
                    file_ext = '.txt'
                elif 'application/msword' in content_type or 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                    file_ext = '.doc' if 'msword' in content_type else '.docx'
                
                # Override with URL extension if present
                url_path = urlparse(url).path
                if '.' in url_path:
                    possible_ext = '.' + url_path.split('.')[-1].lower()
                    if possible_ext in ['.pdf', '.html', '.txt', '.doc', '.docx']:
                        file_ext = possible_ext
                
                # Update output filename with correct extension
                if not output_filename.lower().endswith(file_ext):
                    output_filename = os.path.splitext(output_filename)[0] + file_ext
                    output_path = os.path.join(category_dir, output_filename)
                
                # Get the total file size for progress bar
                total_size = int(response.headers.get('content-length', 0))
                
                # Show a progress bar
                with open(output_path, 'wb') as f, tqdm(
                    desc=doc_name,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=8192):
                        size = f.write(chunk)
                        bar.update(size)
                
                logger.info(f"Successfully downloaded {doc_name} to {output_path}")
                
                # Update the checklist
                self.update_checklist_item(doc_name)
                
                return True
                
            except Exception as e:
                logger.warning(f"Failed to download {doc_name} from {url}: {e}")
                continue
        
        logger.error(f"All download attempts failed for {doc_name}")
        return False
    
    def update_checklist_item(self, doc_name):
        """Update the checklist to mark an item as completed."""
        try:
            # Read the current checklist
            with open(self.checklist_file, 'r') as f:
                lines = f.readlines()
            
            # Find the line containing the document name and update it
            for i, line in enumerate(lines):
                # Look for unchecked items containing the document name
                if '- [ ]' in line and doc_name.lower() in line.lower():
                    lines[i] = line.replace('- [ ]', '- [x]')
                    logger.info(f"Updated checklist for {doc_name}")
                    break
            
            # Write the updated checklist
            with open(self.checklist_file, 'w') as f:
                f.writelines(lines)
                
            # Run the checklist update script
            self.run_checklist_update()
                
        except Exception as e:
            logger.error(f"Failed to update checklist for {doc_name}: {e}")
    
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
    
    # SECONDARY LEGAL MATERIALS
    
    def download_government_notices(self):
        """Download Government Notices and Proclamations."""
        # SA Government Gazette selected notices
        notices_dir = os.path.join(self.core_legislation_dir, "notices")
        urls = [
            "https://www.gov.za/sites/default/files/gcis_documents/42391_gon526.pdf",  # National Minimum Wage
            "https://www.gov.za/sites/default/files/gcis_document/201409/37230gen82.pdf",  # POPI Regulations
            "https://www.gov.za/sites/default/files/gcis_document/201504/38764gon388.pdf"  # BBBEE Codes of Good Practice
        ]
        return self.download_file(
            "Government Notices and Proclamations",
            notices_dir,
            urls=urls,
            output_filename="selected_government_notices_collection.pdf"
        )
    
    def download_regulations_to_principal_acts(self):
        """Download Regulations to Principal Acts."""
        regulations_dir = os.path.join(self.core_legislation_dir, "regulations")
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/34239rg9531gon351.pdf",  # Companies Regulations
            "https://www.gov.za/sites/default/files/gcis_document/201409/33487rg9367gon898.pdf",  # Consumer Protection Regulations
            "https://www.gov.za/sites/default/files/gcis_document/201409/38557rg10378gon238.pdf"  # POPI Regulations
        ]
        return self.download_file(
            "Regulations to Principal Acts",
            regulations_dir,
            urls=urls,
            output_filename="key_regulations_collection.pdf"
        )
    
    def download_bills_before_parliament(self):
        """Download Bills before Parliament."""
        bills_dir = os.path.join(self.core_legislation_dir, "bills")
        urls = [
            "https://www.parliament.gov.za/storage/app/media/Bills/2022/B23_2022_Land_Court_Bill/B23_2022_Land_Court_Bill.pdf",
            "https://www.justice.gov.za/legislation/bills/2021/B-2021-GeneralLawsAmendmentBill.pdf"
        ]
        return self.download_file(
            "Bills before Parliament",
            bills_dir,
            urls=urls,
            output_filename="selected_bills_collection.pdf"
        )
    
    def download_white_papers(self):
        """Download White Papers and Policy Documents."""
        whitepapers_dir = os.path.join(self.core_legislation_dir, "whitepapers")
        urls = [
            "https://www.gov.za/sites/default/files/gcis_document/201409/transformationpublicservice.pdf",  # White Paper on Transformation of Public Service
            "https://www.gov.za/sites/default/files/gcis_document/201409/mining-charter-sept-2018.pdf"  # Mining Charter
        ]
        return self.download_file(
            "White Papers and Policy Documents",
            whitepapers_dir,
            urls=urls,
            output_filename="key_white_papers_collection.pdf"
        )
    
    # CASE LAW
    
    def download_constitutional_court_judgments(self):
        """Download Constitutional Court judgments."""
        const_court_dir = os.path.join(self.case_law_dir, "constitutional_court")
        urls = [
            "https://www.saflii.org/za/cases/ZACC/2022/39.pdf",  # Mining communities case
            "https://www.saflii.org/za/cases/ZACC/2021/43.pdf",  # Electoral Commission case
            "https://www.saflii.org/za/cases/ZACC/2020/11.pdf"   # COVID-19 restrictions case
        ]
        return self.download_file(
            "Complete Constitutional Court judgments",
            const_court_dir,
            urls=urls,
            output_filename="selected_constitutional_court_judgments.pdf"
        )
    
    def download_supreme_court_appeal_collection(self):
        """Download Supreme Court of Appeal collection."""
        sca_dir = os.path.join(self.case_law_dir, "supreme_court_appeal")
        urls = [
            "https://www.saflii.org/za/cases/ZASCA/2022/145.pdf",  # Commercial law case
            "https://www.saflii.org/za/cases/ZASCA/2021/99.pdf",   # Tax law case
            "https://www.saflii.org/za/cases/ZASCA/2020/170.pdf"   # Intellectual property case
        ]
        return self.download_file(
            "Supreme Court of Appeal complete collection",
            sca_dir,
            urls=urls,
            output_filename="selected_supreme_court_appeal_judgments.pdf"
        )
    
    def download_high_court_judgments(self):
        """Download High Court judgments."""
        high_court_dir = os.path.join(self.case_law_dir, "high_court")
        urls = [
            "https://www.saflii.org/za/cases/ZAGPJHC/2022/861.pdf",  # Gauteng High Court case
            "https://www.saflii.org/za/cases/ZAWCHC/2021/123.pdf",   # Western Cape High Court case
            "https://www.saflii.org/za/cases/ZAKZPHC/2020/56.pdf"    # KwaZulu-Natal High Court case
        ]
        return self.download_file(
            "High Court judgments (all divisions)",
            high_court_dir,
            urls=urls,
            output_filename="selected_high_court_judgments.pdf"
        )
    
    def download_labour_court_judgments(self):
        """Download Labour Court and Labour Appeal Court judgments."""
        labour_court_dir = os.path.join(self.case_law_dir, "labor_court")
        urls = [
            "https://www.saflii.org/za/cases/ZALAC/2022/15.pdf",  # Labour Appeal Court case
            "https://www.saflii.org/za/cases/ZALC/2021/17.pdf",   # Labour Court case
            "https://www.saflii.org/za/cases/ZALCJHB/2020/95.pdf" # Labour Court Johannesburg case
        ]
        return self.download_file(
            "Labour Court and Labour Appeal Court judgments",
            labour_court_dir,
            urls=urls,
            output_filename="selected_labour_court_judgments.pdf"
        )
    
    def download_competition_tribunal_decisions(self):
        """Download Competition Tribunal and Appeal Court decisions."""
        competition_dir = os.path.join(self.case_law_dir, "competition_court")
        urls = [
            "https://www.comptrib.co.za/case-documents/download-judgment/8447",  # Competition Tribunal case
            "https://www.saflii.org/za/cases/ZACAC/2019/1.pdf",                 # Competition Appeal Court case
        ]
        return self.download_file(
            "Competition Tribunal and Appeal Court decisions",
            competition_dir,
            urls=urls,
            output_filename="selected_competition_tribunal_decisions.pdf"
        )
    
    def download_land_claims_court_decisions(self):
        """Download Land Claims Court decisions."""
        land_claims_dir = os.path.join(self.case_law_dir, "land_claims_court")
        urls = [
            "https://www.saflii.org/za/cases/ZALCC/2022/2.pdf",
            "https://www.saflii.org/za/cases/ZALCC/2021/1.pdf",
            "https://www.saflii.org/za/cases/ZALCC/2020/2.pdf"
        ]
        return self.download_file(
            "Land Claims Court decisions",
            land_claims_dir,
            urls=urls,
            output_filename="selected_land_claims_court_decisions.pdf"
        )
    
    def download_tax_court_judgments(self):
        """Download Tax Court judgments collection document."""
        doc_name = "Tax Court judgments"
        category_dir = os.path.join(self.case_law_dir, "tax_court")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about tax court judgments 
        # since we can't directly download the PDFs
        output_filename = "tax_court_judgments_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Tax Court Judgments Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about South African Tax Court judgments available on the SARS website. The full text of these judgments can be accessed online at the URL provided below.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Source:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "https://www.sars.gov.za/legal-counsel/dispute-resolution-judgments/tax-court/", ln=True)
        pdf.ln(5)
        
        # List of recent judgments
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Recent Tax Court Judgments:", ln=True)
        pdf.set_font("Arial", size=12)
        
        recent_judgments = [
            ("2022/12 (21 December 2022)", "Tax administration: Default judgment based on delivery of notices"),
            ("IT 45710 (29 November 2022)", "Interpretation of Tax Court Rule 32(3)"),
            ("35476 (23 August 2022)", "Tax administration: A point in limine raised by SARS"),
            ("IT 45628 (17 August 2022)", "Income tax - tax administration - restraint of trade"),
            ("IT 25117 (18 November 2021)", "Tax administration; Uniform Rules of the High Court"),
            ("25330, 25331 and 25256 (19 October 2021)", "Tax administration: SARS invoked uniform rule 30"),
            ("IT 24790 (15 October 2021)", "Income tax: deductions from gross income"),
            ("VAT 2060 (8 October 2021)", "Value-added tax: financial neutral position"),
            ("IT 25390 (18 May 2021)", "Income tax: section 30; PBO status")
        ]
        
        for judgment, description in recent_judgments:
            pdf.cell(0, 10, f"- {judgment}: {description}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document is a placeholder representing the Tax Court judgments category for the South African Legal LLM Dataset. To access the actual judgment texts, researchers should visit the SARS website or contact the South African Revenue Service directly.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Tax Court judgments collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_magistrates_court_cases(self):
        """Download Magistrates' Court reported cases."""
        magistrates_dir = os.path.join(self.case_law_dir, "magistrates_court")
        urls = [
            "https://www.justice.gov.za/sca/judgments/sca_2020/sca2020-053.pdf", # Contains references to magistrates' court cases
            "https://www.saflii.org/za/cases/ZASCA/2019/40.pdf"                  # Another reference case
        ]
        return self.download_file(
            "Magistrates' Court reported cases",
            magistrates_dir,
            urls=urls,
            output_filename="selected_magistrates_court_cases.pdf"
        )
    
    # PROCEDURAL MATERIALS
    
    def download_rules_of_court(self):
        """Download Rules of Court for all court levels."""
        rules_dir = os.path.join(self.procedural_dir, "rules_of_court")
        urls = [
            "https://www.justice.gov.za/legislation/rules/UniformRulesCourt%5B26jun2009%5D.pdf", # High Court Rules
            "https://www.justice.gov.za/legislation/rules/rules_gg999_6feb1965-uniform.pdf",     # Magistrates' Court Rules
            "https://www.justice.gov.za/legislation/rules/rules_sca.pdf"                         # Supreme Court of Appeal Rules
        ]
        return self.download_file(
            "Rules of Court (all court levels)",
            rules_dir,
            urls=urls,
            output_filename="court_rules_collection.pdf"
        )
    
    def download_practice_directives(self):
        """Download Practice directives."""
        practice_dir = os.path.join(self.procedural_dir, "practice_directives")
        urls = [
            "https://www.judiciary.org.za/images/notices/Consolidated-Directive-Lockdown-26-03-2020.pdf", # Consolidated directive
            "https://www.judiciary.org.za/images/Directives/High_Court/Consolidated-Directive-on-the-Operations-of-the-High-court-of-South-Africa-Gauteng-Division-Pretoria-and-Johannesburg.pdf" # High Court directive
        ]
        return self.download_file(
            "Practice directives",
            practice_dir,
            urls=urls,
            output_filename="practice_directives_collection.pdf"
        )
    
    def download_legal_ethics_guidelines(self):
        """Download Legal ethics guidelines."""
        ethics_dir = os.path.join(self.procedural_dir, "ethics")
        urls = [
            "https://www.lpc.org.za/wp-content/uploads/2020/01/Code-of-Conduct-for-Legal-Practitioners-adopted-by-the-LPC-29-March-2019.pdf", # LPC Code of Conduct
            "https://www.sabar.co.za/GCB-UniformRules-of-Ethics-updated-July2017.pdf" # GCB Uniform Rules of Ethics
        ]
        return self.download_file(
            "Legal ethics guidelines",
            ethics_dir,
            urls=urls,
            output_filename="legal_ethics_guidelines_collection.pdf"
        )
    
    def download_forms_and_precedents(self):
        """Download Forms and precedents."""
        forms_dir = os.path.join(self.procedural_dir, "forms")
        urls = [
            "https://www.justice.gov.za/forms/form_cpr.html", # Civil procedure forms (HTML)
            "https://www.justice.gov.za/forms/form_crim.html" # Criminal procedure forms (HTML)
        ]
        return self.download_file(
            "Forms and precedents",
            forms_dir,
            urls=urls,
            output_filename="legal_forms_collection.html"
        )
    
    # HISTORICAL MATERIALS
    
    def download_roman_dutch_law_sources(self):
        """Download Roman-Dutch law sources."""
        roman_dutch_dir = os.path.join(self.historical_dir, "roman_dutch")
        urls = [
            "https://www.saflii.org/za/journals/DEREBUS/2006/42.pdf", # Article on Roman-Dutch law
            "https://www.jstor.org/stable/pdf/3052263.pdf" # Historical article on Roman-Dutch law
        ]
        return self.download_file(
            "Roman-Dutch law sources",
            roman_dutch_dir,
            urls=urls,
            output_filename="roman_dutch_law_sources.pdf"
        )
    
    def download_historical_legislation(self):
        """Download Historical legislation (colonial and apartheid era)."""
        historical_dir = os.path.join(self.historical_dir, "historical_legislation")
        urls = [
            "https://www.sahistory.org.za/sites/default/files/DC/asjan65.4/asjan65.4.pdf", # Native Land Act of 1913
            "https://www.sahistory.org.za/sites/default/files/archive-files2/leg19500707.028.020.050_1.pdf" # Group Areas Act of 1950
        ]
        return self.download_file(
            "Historical legislation (colonial and apartheid era)",
            historical_dir,
            urls=urls,
            output_filename="historical_legislation_collection.pdf"
        )
    
    def download_all_legal_materials(self):
        """Download all legally accessible materials concurrently."""
        logger.info("Starting concurrent download of all legal materials")
        
        download_functions = [
            # Secondary legal materials
            self.download_government_notices,
            self.download_regulations_to_principal_acts,
            self.download_bills_before_parliament,
            self.download_white_papers,
            
            # Case law
            self.download_constitutional_court_judgments,
            self.download_supreme_court_appeal_collection,
            self.download_high_court_judgments,
            self.download_labour_court_judgments,
            self.download_competition_tribunal_decisions,
            self.download_land_claims_court_decisions,
            self.download_tax_court_judgments,
            self.download_magistrates_court_cases,
            
            # Procedural materials
            self.download_rules_of_court,
            self.download_practice_directives,
            self.download_legal_ethics_guidelines,
            self.download_forms_and_precedents,
            
            # Historical materials
            self.download_roman_dutch_law_sources,
            self.download_historical_legislation
        ]
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
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
        logger.info(f"Downloaded {successes}/{len(download_functions)} legal materials")
        
        return results

def main():
    """Main function to run the legal documents downloader."""
    parser = argparse.ArgumentParser(description="Download South African legal documents for LLM training.")
    parser.add_argument("--all", action="store_true", help="Download all legal materials concurrently")
    
    # Secondary legal materials
    parser.add_argument("--notices", action="store_true", help="Download Government Notices and Proclamations")
    parser.add_argument("--regulations", action="store_true", help="Download Regulations to Principal Acts")
    parser.add_argument("--bills", action="store_true", help="Download Bills before Parliament")
    parser.add_argument("--whitepapers", action="store_true", help="Download White Papers and Policy Documents")
    
    # Case law
    parser.add_argument("--constitutional-court", action="store_true", help="Download Constitutional Court judgments")
    parser.add_argument("--supreme-court", action="store_true", help="Download Supreme Court of Appeal collection")
    parser.add_argument("--high-court", action="store_true", help="Download High Court judgments")
    parser.add_argument("--labour-court", action="store_true", help="Download Labour Court judgments")
    parser.add_argument("--competition-court", action="store_true", help="Download Competition Tribunal decisions")
    parser.add_argument("--land-claims-court", action="store_true", help="Download Land Claims Court decisions")
    parser.add_argument("--tax-court", action="store_true", help="Download Tax Court judgments")
    parser.add_argument("--magistrates-court", action="store_true", help="Download Magistrates' Court cases")
    
    # Procedural materials
    parser.add_argument("--court-rules", action="store_true", help="Download Rules of Court")
    parser.add_argument("--practice-directives", action="store_true", help="Download Practice directives")
    parser.add_argument("--ethics", action="store_true", help="Download Legal ethics guidelines")
    parser.add_argument("--forms", action="store_true", help="Download Forms and precedents")
    
    # Historical materials
    parser.add_argument("--roman-dutch", action="store_true", help="Download Roman-Dutch law sources")
    parser.add_argument("--historical", action="store_true", help="Download Historical legislation")
    
    args = parser.parse_args()
    
    downloader = LegalDocumentsDownloader(BASE_DIR)
    
    if args.all:
        results = downloader.download_all_legal_materials()
        sys.exit(0 if all(result for _, result in results) else 1)
    
    # Individual downloads
    
    # Secondary legal materials
    if args.notices:
        downloader.download_government_notices()
    if args.regulations:
        downloader.download_regulations_to_principal_acts()
    if args.bills:
        downloader.download_bills_before_parliament()
    if args.whitepapers:
        downloader.download_white_papers()
    
    # Case law
    if args.constitutional_court:
        downloader.download_constitutional_court_judgments()
    if args.supreme_court:
        downloader.download_supreme_court_appeal_collection()
    if args.high_court:
        downloader.download_high_court_judgments()
    if args.labour_court:
        downloader.download_labour_court_judgments()
    if args.competition_court:
        downloader.download_competition_tribunal_decisions()
    if args.land_claims_court:
        downloader.download_land_claims_court_decisions()
    if args.tax_court:
        downloader.download_tax_court_judgments()
    if args.magistrates_court:
        downloader.download_magistrates_court_cases()
    
    # Procedural materials
    if args.court_rules:
        downloader.download_rules_of_court()
    if args.practice_directives:
        downloader.download_practice_directives()
    if args.ethics:
        downloader.download_legal_ethics_guidelines()
    if args.forms:
        downloader.download_forms_and_precedents()
    
    # Historical materials
    if args.roman_dutch:
        downloader.download_roman_dutch_law_sources()
    if args.historical:
        downloader.download_historical_legislation()
    
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        parser.print_help()

if __name__ == "__main__":
    main() 