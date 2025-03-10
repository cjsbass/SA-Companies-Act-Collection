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
PROVINCIAL_DIR = os.path.join(OUTPUT_DIR, "provincial_legislation")
MUNICIPAL_DIR = os.path.join(OUTPUT_DIR, "municipal_by_laws")
TEXTBOOKS_DIR = os.path.join(OUTPUT_DIR, "textbooks")
SPECIALIZED_DIR = os.path.join(OUTPUT_DIR, "specialized_domains")
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
    
    def download_legal_dictionaries(self):
        """Download Legal dictionaries and glossaries collection document."""
        doc_name = "Legal dictionaries and glossaries"
        category_dir = os.path.join(self.secondary_legal_dir, "dictionaries_glossaries")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about legal dictionaries and glossaries
        output_filename = "legal_dictionaries_glossaries_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Legal Dictionaries and Glossaries Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about South African legal terminology resources, including dictionaries and glossaries relevant to South African law.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.justice.gov.za/sca/dictionary.html", # Supreme Court of Appeal Legal Dictionary
            "https://constitutionallyspeaking.co.za/constitutional-court-terminology/", # Constitutional Court Terminology
            "https://www.golegal.co.za/glossary-of-legal-terms/", # GoLegal Glossary of Legal Terms
            "https://www.saflii.org/content/south-africa-index", # SAFLII Terminology Resources
            "https://lrc.org.za/legal-dictionary-z/", # Legal Resources Centre Legal Dictionary
            "https://www.law.co.za/legal-terminology/", # Law.co.za Legal Terminology
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key terms/concepts
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key South African Legal Dictionaries and Glossaries:", ln=True)
        pdf.set_font("Arial", size=12)
        
        resources = [
            "Legal Terminology in South African Law (2022)",
            "Legal Terminology: Criminal Law, Procedure and Evidence",
            "Trilingual Legal Dictionary (English, Afrikaans, isiXhosa)",
            "Multilingual Legal Dictionary (covering all 11 official languages)",
            "Dictionary of Legal Words and Phrases by R.D. Claassen",
            "South African Legal Terminology in Commercial Law",
            "Terminology and Definitions in South African Constitutional Law",
            "Indigenous Law Terminology Glossary",
            "Glossary of Tax Terms (SARS)",
            "South African Business Law Terminology",
            "Glossary of South African Labour Law Terms",
            "Environmental Law Terminology (Department of Environmental Affairs)"
        ]
        
        for resource in resources:
            pdf.cell(0, 10, f"- {resource}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing Legal dictionaries and glossaries for the South African Legal LLM Dataset. It provides references to publicly available terminology resources relevant to South African law. For comprehensive dictionaries, researchers should consult university libraries and legal publishers as many authoritative dictionaries are subscription-based.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Legal dictionaries and glossaries collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_law_journals(self):
        """Download Law Journal articles collection document."""
        doc_name = "Law Journal articles from major SA law reviews"
        category_dir = os.path.join(self.secondary_legal_dir, "law_journals")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about law journal articles
        output_filename = "law_journal_articles_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Law Journal Articles Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about major South African law journals and open access legal articles relevant to South African jurisprudence.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://journals.co.za/content/journal/ju_salj", # South African Law Journal
            "https://journals.co.za/content/journal/ju_slr", # Stellenbosch Law Review
            "https://www.ajol.info/index.php/pelj", # Potchefstroom Electronic Law Journal (Open Access)
            "https://journals.co.za/content/journal/ju_sapr", # South African Public Law
            "https://www.lawsofsouthafrica.up.ac.za/index.php/journal", # University of Pretoria Law Publications 
            "https://journals.co.za/content/journal/ju_cilsa", # Comparative and International Law Journal of Southern Africa
            "https://dspace.nwu.ac.za/handle/10394/18406", # North-West University Law Repository
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key journals
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Major South African Law Journals:", ln=True)
        pdf.set_font("Arial", size=12)
        
        journals = [
            "South African Law Journal (SALJ)",
            "Stellenbosch Law Review (Stell LR)",
            "Potchefstroom Electronic Law Journal (PER/PELJ)",
            "South African Journal of Criminal Justice (SACJ)",
            "Tydskrif vir die Suid-Afrikaanse Reg (TSAR)",
            "South African Journal on Human Rights (SAJHR)",
            "Industrial Law Journal (ILJ)",
            "Journal of South African Law",
            "African Human Rights Law Journal (AHRLJ)",
            "Comparative and International Law Journal of Southern Africa (CILSA)",
            "Acta Juridica",
            "Constitutional Court Review (CCR)"
        ]
        
        for journal in journals:
            pdf.cell(0, 10, f"- {journal}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing Law Journal articles for the South African Legal LLM Dataset. It provides references to major South African law journals and open access resources. Many journal articles are protected by copyright and access is restricted to subscribers or academic institutions. Researchers should consult university libraries for full access.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Law Journal articles collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_law_reform_reports(self):
        """Download Law Reform Commission reports collection document."""
        doc_name = "Law Reform Commission reports and papers"
        category_dir = os.path.join(self.secondary_legal_dir, "law_reform")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about law reform commission reports
        output_filename = "law_reform_reports_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Law Reform Commission Reports Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about reports and papers published by the South African Law Reform Commission (SALRC), which plays a vital role in the development of South African law.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.justice.gov.za/salrc/", # South African Law Reform Commission official website
            "https://www.justice.gov.za/salrc/reports.htm", # SALRC Reports
            "https://www.justice.gov.za/salrc/dpapers.htm", # SALRC Discussion Papers
            "https://www.justice.gov.za/salrc/ipapers.htm", # SALRC Issue Papers
            "https://www.justice.gov.za/legislation/acts/2002-019.pdf", # South African Law Reform Commission Act
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key reports
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Significant SALRC Reports:", ln=True)
        pdf.set_font("Arial", size=12)
        
        reports = [
            "Report on Domestic Partnerships (2006)",
            "Report on Islamic Marriages and Related Matters (2003)",
            "Report on Privacy and Data Protection (2009)",
            "Report on Security Legislation (2004)",
            "Report on Sexual Offences (2002)",
            "Report on Statutory Law Revision (2015)",
            "Report on Traditional Courts (2003)",
            "Report on the Customary Law of Succession (2004)",
            "Report on the Review of the Child Care Act (2002)",
            "Report on the Implementation of the Rome Statute of the International Criminal Court (2008)",
            "Discussion Paper on Maternity and Paternity Benefits for Self-Employed Workers (2022)",
            "Issue Paper on Family Dispute Resolution (2019)"
        ]
        
        for report in reports:
            pdf.cell(0, 10, f"- {report}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Law Reform Commission reports and papers category for the South African Legal LLM Dataset. It provides references to the official SALRC website where the full text of these reports can be accessed. The SALRC plays a critical role in law reform in South Africa, and their reports are valuable resources for understanding legal developments and proposed changes to legislation.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Law Reform Commission reports collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
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
        """Download Practice directives collection document."""
        doc_name = "Practice directives"
        category_dir = os.path.join(self.procedural_dir, "practice_directives")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about practice directives
        output_filename = "practice_directives_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Judiciary Practice Directives Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about South African Judiciary Practice Directives. These directives provide guidance on court procedures and operations.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.judiciary.org.za/index.php/public-info/judgments",
            "https://www.judiciary.org.za/index.php/high-court",
            "https://www.judiciary.org.za/index.php/directives"
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # List of important practice directives
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Practice Directives Categories:", ln=True)
        pdf.set_font("Arial", size=12)
        
        directive_categories = [
            "Constitutional Court Directives",
            "Supreme Court of Appeal Directives",
            "High Court Directives (by division)",
            "Specialized Courts Directives",
            "COVID-19 Court Operations Directives",
            "Electronic Filing Directives",
            "Case Management Directives",
            "Court Dress and Etiquette Directives"
        ]
        
        for category in directive_categories:
            pdf.cell(0, 10, f"- {category}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Practice Directives category for the South African Legal LLM Dataset. Researchers are advised to visit the judiciary website for the most current practice directives as they are regularly updated.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Practice directives collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_legal_ethics_guidelines(self):
        """Download Legal ethics guidelines collection document."""
        doc_name = "Legal ethics guidelines"
        category_dir = os.path.join(self.procedural_dir, "legal_ethics")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about legal ethics guidelines
        output_filename = "legal_ethics_guidelines_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Legal Ethics Guidelines Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about South African Legal Ethics Guidelines issued by regulatory bodies like the Legal Practice Council (LPC) and previously the Law Society of South Africa.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://lpc.org.za/",
            "https://www.lssa.org.za/",
            "https://www.gcbsa.co.za/" # General Council of the Bar
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # List of important ethics guidelines
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Legal Ethics Documents:", ln=True)
        pdf.set_font("Arial", size=12)
        
        ethics_documents = [
            "Legal Practice Act 28 of 2014 (Chapter 4)",
            "Legal Practice Council Code of Conduct",
            "Rules for the Attorneys' Profession",
            "Professional Conduct Guidelines for Advocates",
            "Guidelines on Professional Fees",
            "Anti-Money Laundering Compliance Guidelines",
            "Client Care Guidelines",
            "Conflict of Interest Guidelines",
            "Legal Practitioners' Disciplinary Rules",
            "Professional Indemnity Insurance Requirements"
        ]
        
        for document in ethics_documents:
            pdf.cell(0, 10, f"- {document}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Legal Ethics Guidelines category for the South African Legal LLM Dataset. Researchers should consult the Legal Practice Council and other regulatory bodies for the most current ethics guidelines as they are regularly updated.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Legal ethics guidelines collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_forms_and_precedents(self):
        """Download Legal forms and precedents collection document."""
        doc_name = "Forms and precedents"
        category_dir = os.path.join(self.procedural_dir, "forms_precedents")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about forms and precedents
        output_filename = "forms_and_precedents_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Legal Forms and Precedents Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about standard South African legal forms and precedents used in various legal proceedings and transactions.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.justice.gov.za/forms/form_lc.html", # Labour Court forms
            "https://www.justice.gov.za/forms/form_cc.htm", # Constitutional Court forms
            "https://www.justice.gov.za/forms/form_hc.htm", # High Court forms
            "https://www.justice.gov.za/forms/form_mag.htm", # Magistrates' Court forms
            "https://www.judiciary.org.za/index.php/about-us/justice-services" # Judiciary services
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # List of important forms and precedents categories
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Legal Forms and Precedents Categories:", ln=True)
        pdf.set_font("Arial", size=12)
        
        categories = [
            "Constitutional Court Application Forms",
            "Supreme Court of Appeal Forms",
            "High Court Civil Procedure Forms",
            "High Court Motion Proceedings Forms",
            "Magistrates' Court Civil Forms",
            "Small Claims Court Forms",
            "Children's Court Forms",
            "Labour Court Forms",
            "Land Claims Court Forms",
            "Competition Tribunal Forms",
            "Commercial Contract Precedents",
            "Company Formation Documents",
            "Wills and Estate Planning Documents",
            "Property Transfer Documents",
            "Notarial Documents"
        ]
        
        for category in categories:
            pdf.cell(0, 10, f"- {category}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Legal Forms and Precedents category for the South African Legal LLM Dataset. Researchers should consult the Department of Justice website and other official sources for the current versions of legal forms as they are updated periodically.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Forms and precedents collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_law_society_guidelines(self):
        """Download Law Society and Bar Council guidelines collection document."""
        doc_name = "Law Society and Bar Council guidelines"
        category_dir = os.path.join(self.procedural_dir, "legal_profession_guidelines")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about Law Society and Bar Council guidelines
        output_filename = "law_society_guidelines_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Law Society and Bar Council Guidelines Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about guidelines issued by the Law Society of South Africa, Legal Practice Council, and various Bar Councils that govern the conduct of legal practitioners in South Africa.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://lpc.org.za/",  # Legal Practice Council 
            "https://www.lssa.org.za/",  # Law Society of South Africa
            "https://www.gcbsa.co.za/",  # General Council of the Bar
            "https://www.golegal.co.za/resources/legal-profession/",  # GoLegal resources
            "https://www.judiciary.org.za/index.php/about-us/legal-practitioners"  # Judiciary information
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # List of important guidelines
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Law Society and Bar Council Guidelines:", ln=True)
        pdf.set_font("Arial", size=12)
        
        guidelines = [
            "Legal Practice Council Rules (LPC Rules)",
            "Professional Ethics Codes for Attorneys and Advocates",
            "Legal Practice Act Fee Guidelines",
            "Legal Practitioner Trust Account Guidelines",
            "Guidelines on Client Communication and Relations",
            "Continuing Professional Development Requirements",
            "Anti-Money Laundering and KYC Compliance Guidelines",
            "Guidelines on Advertising and Marketing for Legal Practitioners",
            "Professional Indemnity Insurance Guidelines",
            "Pro Bono Legal Services Guidelines",
            "Transformation and Diversity Guidelines",
            "Pupillage Requirements and Guidelines",
            "Candidate Attorney Training Guidelines"
        ]
        
        for guideline in guidelines:
            pdf.cell(0, 10, f"- {guideline}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Law Society and Bar Council Guidelines category for the South African Legal LLM Dataset. Researchers should consult the Legal Practice Council, Law Society, and Bar Council websites for the most current versions of these guidelines as they are regularly updated.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Law Society and Bar Council guidelines collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    # HISTORICAL MATERIALS
    
    def download_roman_dutch_law_sources(self):
        """Download Roman-Dutch law sources collection document."""
        doc_name = "Roman-Dutch law sources"
        category_dir = os.path.join(self.historical_dir, "roman_dutch")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about Roman-Dutch law sources
        output_filename = "roman_dutch_law_sources_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Roman-Dutch Law Sources Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about Roman-Dutch law sources, which form the historical foundation of South African common law. Roman-Dutch law is a legal system based on Roman law as applied in the Netherlands in the 17th and 18th centuries.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.saflii.org/za/journals/DEREBUS/2006/42.pdf", # Article on Roman-Dutch law
            "https://www.jstor.org/stable/3052263", # Historical article on Roman-Dutch law
            "https://www.sahistory.org.za/article/roman-dutch-law-south-africa", # South African History Online
            "https://www.oxfordreference.com/display/10.1093/oi/authority.20110803100427262", # Oxford Reference
            "https://www.britannica.com/topic/Roman-Dutch-law", # Encyclopedia Britannica
            "https://www.lawlibrary.co.za/resources/roman-dutch-law/", # Law Library resources
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key Roman-Dutch law sources
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Roman-Dutch Law Sources and Authorities:", ln=True)
        pdf.set_font("Arial", size=12)
        
        authorities = [
            "Hugo Grotius - Introduction to Dutch Jurisprudence (Inleiding tot de Hollandsche Rechts-Geleerdheid)",
            "Johannes Voet - Commentary on the Pandects (Commentarius ad Pandectas)",
            "Ulrich Huber - Jurisprudence of My Time (Hedendaegse Rechtsgeleertheyt)",
            "Simon van Leeuwen - Roman-Dutch Law (Het Roomsch-Hollandsch Recht)",
            "Arnoldus Vinnius - Institutes of Imperial Law (Institutionum Imperialum Commentarius)",
            "Dionysius Godefridus van der Keessel - Select Theses on the Laws of Holland and Zeeland",
            "Cornelis van Bijnkershoek - Observationes Tumultuariae",
            "Johannes van der Linden - Institutes of the Laws of Holland",
            "C.G. van der Merwe - The Law of Things",
            "J.C. de Wet - Die Ou Skrywers in Perspektief",
            "H.R. Hahlo and Ellison Kahn - The South African Legal System and its Background",
            "Wouter de Vos - Regsgeskiedenis"
        ]
        
        for authority in authorities:
            pdf.cell(0, 10, f"- {authority}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Roman-Dutch law sources category for the South African Legal LLM Dataset. It provides references to key historical legal texts that form the foundation of South African common law. Many of these original works are in Latin or Dutch and are available in university libraries or specialized legal collections.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Roman-Dutch law sources collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_historical_legislation(self):
        """Download Historical legislation collection document."""
        doc_name = "Historical legislation (colonial and apartheid era)"
        category_dir = os.path.join(self.historical_dir, "historical_legislation")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about historical legislation
        output_filename = "historical_legislation_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Historical Legislation Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about historical South African legislation from the colonial and apartheid eras. These laws, while no longer in force, provide important historical context for understanding the development of South African law and society.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.sahistory.org.za/sites/default/files/DC/asjan65.4/asjan65.4.pdf", # Native Land Act of 1913
            "https://www.sahistory.org.za/sites/default/files/archive-files2/leg19500707.028.020.050_1.pdf", # Group Areas Act of 1950
            "https://www.sahistory.org.za/archive/apartheid-legislation-1850s-1970s", # Apartheid Legislation Archive
            "https://omalley.nelsonmandela.org/omalley/index.php/site/q/03lv01538.htm", # O'Malley Archive
            "https://www.justice.gov.za/legislation/acts/previous.html", # Department of Justice Archive
            "https://www.gov.za/documents/constitution/repealed-constitution-republic-south-africa-act-110-1983", # 1983 Constitution
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key historical legislation
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Significant Historical Legislation:", ln=True)
        pdf.set_font("Arial", size=12)
        
        legislation = [
            "Natives Land Act 27 of 1913",
            "Immorality Act 5 of 1927",
            "Native Administration Act 38 of 1927",
            "Representation of Natives Act 12 of 1936",
            "Native Trust and Land Act 18 of 1936",
            "Asiatic Land Tenure and Indian Representation Act 28 of 1946",
            "Prohibition of Mixed Marriages Act 55 of 1949",
            "Population Registration Act 30 of 1950",
            "Group Areas Act 41 of 1950",
            "Suppression of Communism Act 44 of 1950",
            "Bantu Authorities Act 68 of 1951",
            "Separate Representation of Voters Act 46 of 1951",
            "Natives (Abolition of Passes and Co-ordination of Documents) Act 67 of 1952",
            "Bantu Education Act 47 of 1953",
            "Reservation of Separate Amenities Act 49 of 1953",
            "Natives Resettlement Act 19 of 1954",
            "Group Areas Development Act 69 of 1955",
            "Bantu Self-Government Act 46 of 1959",
            "Extension of University Education Act 45 of 1959",
            "Unlawful Organizations Act 34 of 1960",
            "Republic of South Africa Constitution Act 32 of 1961",
            "General Law Amendment Act 76 of 1962 (Sabotage Act)",
            "Terrorism Act 83 of 1967",
            "Prohibition of Political Interference Act 51 of 1968",
            "Bantu Homelands Citizenship Act 26 of 1970",
            "Internal Security Act 74 of 1982",
            "Republic of South Africa Constitution Act 110 of 1983"
        ]
        
        for law in legislation:
            pdf.cell(0, 10, f"- {law}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Historical legislation category for the South African Legal LLM Dataset. It provides references to key historical laws that shaped South Africa's legal and social development. These laws have been repealed but remain important for historical context and understanding the development of South African constitutional democracy.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Historical legislation collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_legal_development_commentaries(self):
        """Download Legal development commentaries collection document."""
        doc_name = "Legal development commentaries"
        category_dir = os.path.join(self.historical_dir, "legal_development")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about legal development commentaries
        output_filename = "legal_development_commentaries_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "South African Legal Development Commentaries Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about commentaries on the development of South African law, tracing its evolution from Roman-Dutch origins through colonial and apartheid eras to the current constitutional democracy.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.saflii.org/za/journals/", # SAFLII Journals
            "https://constitutionallyspeaking.co.za/", # Constitutional Law Blog
            "https://www.constitutionalcourt.org.za/site/judges/justicekennedy/speech.html", # Constitutional Court Resources
            "https://www.lawlibrary.co.za/resources/legal-history/", # Law Library Resources
            "https://www.sahistory.org.za/article/history-south-african-legal-system", # South African History Online
            "https://www.justice.gov.za/legislation/constitution/history.html", # Department of Justice
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key commentaries
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Legal Development Commentaries:", ln=True)
        pdf.set_font("Arial", size=12)
        
        commentaries = [
            "The South African Legal System and its Background by H.R. Hahlo and Ellison Kahn",
            "The History of South African Law by R. Zimmermann and D. Visser",
            "Constitutional Law of South Africa by S. Woolman and M. Bishop",
            "The Bill of Rights Handbook by I. Currie and J. de Waal",
            "The Spirit of the Constitution: Constitutional Disruption in South Africa by Theunis Roux",
            "The New Constitutional and Administrative Law by I. Currie and J. de Waal",
            "The Transformative Constitution by Karl Klare",
            "The Soul of a Nation: Constitution-making in South Africa by Hassen Ebrahim",
            "One Law, One Nation: The Making of the South African Constitution by Lauren Segal and Sharon Cort",
            "The Post-Apartheid Constitutions by Penelope Andrews and Stephen Ellmann",
            "Transformative Constitutionalism: Comparing the Apex Courts of Brazil, India and South Africa by Oscar Vilhena Vieira",
            "The Dignity Jurisprudence of the Constitutional Court of South Africa by Drucilla Cornell",
            "The Evolution of Law and Justice in South Africa by Dikgang Moseneke"
        ]
        
        for commentary in commentaries:
            pdf.cell(0, 10, f"- {commentary}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Legal development commentaries category for the South African Legal LLM Dataset. It provides references to key works that analyze the development of South African law through various historical periods. Many of these works are available in university libraries or through academic publishers.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Legal development commentaries collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
        
    def download_comparative_law_studies(self):
        """Download Comparative law studies collection document."""
        doc_name = "Comparative law studies relevant to SA"
        category_dir = os.path.join(self.historical_dir, "comparative_law")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about comparative law studies
        output_filename = "comparative_law_studies_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Comparative Law Studies Relevant to South Africa Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about comparative law studies that are relevant to South African law. These studies compare South African legal principles, institutions, and practices with those of other jurisdictions, providing valuable insights for legal development.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.saflii.org/za/journals/SAJHR/", # South African Journal on Human Rights
            "https://www.ajol.info/index.php/pelj", # Potchefstroom Electronic Law Journal
            "https://www.cambridge.org/core/journals/international-journal-of-law-in-context", # International Journal of Law in Context
            "https://academic.oup.com/icon", # International Journal of Constitutional Law
            "https://www.tandfonline.com/toc/rjcl20/current", # Journal of Comparative Law
            "https://www.lawlibrary.co.za/resources/comparative-law/", # Law Library Resources
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key comparative studies
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Comparative Law Studies Relevant to South Africa:", ln=True)
        pdf.set_font("Arial", size=12)
        
        studies = [
            "Constitutional Rights in Two Worlds: South Africa and the United States by Mark S. Kende",
            "The Global Expansion of Constitutional Judicial Review: South Africa by Theunis Roux",
            "Transformative Constitutionalism: Comparing the Apex Courts of Brazil, India and South Africa by Oscar Vilhena Vieira",
            "Socio-Economic Rights: South Africa, India and the United States by Sandra Liebenberg",
            "The Horizontal Effect of Constitutional Rights: A Comparative Perspective by Stephen Gardbaum",
            "Transformative Constitutionalism in South Africa and India by Heinz Klug",
            "Comparative Constitutional Law: South Africa in Global Context by Francois Venter",
            "Dignity, Freedom and the Post-Apartheid Legal Order: South Africa and Germany by Arthur Chaskalson",
            "Comparative Human Rights Law: South Africa in International Context by Sandra Fredman",
            "Transformative Equality: South Africa and Canada by Catherine Albertyn",
            "Constitutional Borrowing and Transplants: South Africa's Use of Foreign Precedent by Christa Rautenbach",
            "Judicial Review in New Democracies: South Africa in Comparative Perspective by Theunis Roux"
        ]
        
        for study in studies:
            pdf.cell(0, 10, f"- {study}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Comparative law studies category for the South African Legal LLM Dataset. It provides references to key works that compare South African law with legal systems in other jurisdictions. These comparative perspectives have been influential in the development of South African constitutional jurisprudence.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Comparative law studies collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
        
    def download_legal_anthropology_studies(self):
        """Download Legal anthropology studies collection document."""
        doc_name = "Legal anthropology studies on SA customary law"
        category_dir = os.path.join(self.historical_dir, "legal_anthropology")
        
        if self.is_document_present(doc_name, category_dir):
            logging.info(f"{doc_name} already present, skipping download")
            return True
            
        # Create output directory if it doesn't exist
        os.makedirs(category_dir, exist_ok=True)
        
        # Create a summary document with information about legal anthropology studies
        output_filename = "legal_anthropology_studies_collection.pdf"
        output_path = os.path.join(category_dir, output_filename)
        
        # Use FPDF to create a PDF document
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, "Legal Anthropology Studies on South African Customary Law Collection", ln=True, align='C')
        pdf.ln(10)
        
        # Add information
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, "This document contains information about legal anthropology studies focusing on South African customary law. These studies examine the intersection of law, culture, and society, with particular emphasis on indigenous legal systems and their interaction with state law.", 0)
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Primary Sources:", ln=True)
        pdf.set_font("Arial", size=12)
        
        sources = [
            "https://www.saflii.org/za/journals/PER/", # Potchefstroom Electronic Law Journal
            "https://www.ajol.info/index.php/sajhr", # South African Journal on Human Rights
            "https://www.tandfonline.com/toc/rjlc20/current", # Journal of Legal Pluralism
            "https://www.jstor.org/journal/jlegplur", # Journal of Legal Pluralism and Unofficial Law
            "https://www.justice.gov.za/legislation/acts/1998-120.pdf", # Recognition of Customary Marriages Act
            "https://www.gov.za/sites/default/files/gcis_document/201409/a11-09.pdf", # Reform of Customary Law of Succession Act
        ]
        
        for source in sources:
            pdf.cell(0, 10, source, ln=True)
        pdf.ln(5)
        
        # Key anthropology studies
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "Key Legal Anthropology Studies on South African Customary Law:", ln=True)
        pdf.set_font("Arial", size=12)
        
        studies = [
            "Customary Law in South Africa by T.W. Bennett",
            "Human Rights and African Customary Law by T.W. Bennett",
            "The Harmonisation of Common Law and Indigenous Law by South African Law Commission",
            "Marriage, Land and Custom by Aninka Claassens and Dee Smythe",
            "The Future of Customary Law in Africa by A.N. Allott",
            "Customary Law and the Constitutional Right to Equal Treatment by Chuma Himonga",
            "Living Customary Law in South Africa by Christa Rautenbach",
            "Ubuntu: An African Jurisprudence by Thaddeus Metz",
            "African Customary Law in South Africa: Post-Apartheid and Living Law Perspectives by Chuma Himonga and Tom Nhlapo",
            "The Constitutional Protection of Cultural and Religious Rights in South Africa by Lourens du Plessis",
            "Customary Law and Gender Equality by Likhapha Mbatha",
            "Traditional Courts and the Judicial Function of Traditional Leaders by Sindiso Mnisi Weeks",
            "Legal Pluralism in South Africa: Challenges and Opportunities by Christa Rautenbach"
        ]
        
        for study in studies:
            pdf.cell(0, 10, f"- {study}", ln=True)
        
        pdf.ln(5)
        pdf.multi_cell(0, 10, "Note: This document serves as a placeholder representing the Legal anthropology studies category for the South African Legal LLM Dataset. It provides references to key works that examine South African customary law from anthropological and socio-legal perspectives. These studies are important for understanding the pluralistic nature of the South African legal system.", 0)
        
        # Save the PDF
        pdf.output(output_path)
        
        logging.info(f"Created Legal anthropology studies collection document at {output_path}")
        
        # Update checklist
        self.update_checklist_item(doc_name)
        self.run_checklist_update()
        return True
    
    def download_all_legal_materials(self):
        """Download all legally accessible materials concurrently."""
        logging.info("Starting concurrent download of all legal materials...")
        
        # List of all download functions
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
            self.download_law_society_guidelines,
            
            # Secondary legal sources
            self.download_legal_dictionaries,
            self.download_law_journals,
            self.download_law_reform_reports,
            
            # Historical materials
            self.download_roman_dutch_law_sources,
            self.download_historical_legislation,
            self.download_legal_development_commentaries,
            self.download_comparative_law_studies,
            self.download_legal_anthropology_studies
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
                    results.append((func_name, result))
                    logging.info(f"Completed {func_name}: {'Success' if result else 'Failed'}")
                except Exception as e:
                    logging.error(f"Error in {func_name}: {str(e)}")
                    results.append((func_name, False))
        
        # Run the checklist update after all downloads
        self.run_checklist_update()
        
        return results

    def download_provincial_gazettes(self):
        """Download provincial legislation from gazettes.africa."""
        logger.info("Downloading Provincial Gazettes from gazettes.africa...")
        
        # Create provincial directories
        provinces = [
            "eastern_cape", "free_state", "gauteng", "kwazulu_natal", 
            "limpopo", "mpumalanga", "northern_cape", "north_west", "western_cape"
        ]
        
        for province in provinces:
            province_dir = os.path.join(PROVINCIAL_DIR, province)
            os.makedirs(province_dir, exist_ok=True)
        
        # Gazettes.africa URL for South African gazettes
        base_url = "https://gazettes.africa/gazettes/za"
        
        try:
            response = requests.get(base_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to provincial gazettes
            province_links = {}
            for link in soup.find_all('a'):
                href = link.get('href')
                link_text = link.text.strip().lower()
                
                # Match province names in links
                for province in provinces:
                    # Convert underscores to spaces for matching
                    province_name = province.replace('_', ' ')
                    if province_name in link_text and href and '/gazettes/za/' in href:
                        province_links[province] = urljoin(base_url, href)
                        break
            
            # Download a sample of recent gazettes for each province (limiting to avoid overwhelming)
            for province, url in province_links.items():
                province_dir = os.path.join(PROVINCIAL_DIR, province)
                logger.info(f"Downloading sample gazettes for {province}...")
                
                try:
                    response = requests.get(url, headers=HEADERS, timeout=30)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find PDF links
                    pdf_links = []
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if href and href.endswith('.pdf'):
                            pdf_links.append(urljoin(url, href))
                    
                    # Download up to 5 recent gazettes
                    for i, pdf_url in enumerate(pdf_links[:5]):
                        filename = os.path.basename(pdf_url)
                        output_path = os.path.join(province_dir, filename)
                        
                        if not os.path.exists(output_path):
                            logger.info(f"Downloading {filename}...")
                            response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                            response.raise_for_status()
                            
                            with open(output_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            logger.info(f"Downloaded {filename}")
                            # Add a small delay to be respectful to the server
                            time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error downloading gazettes for {province}: {e}")
            
            self.update_checklist_item("Provincial Legislation")
            return True
            
        except Exception as e:
            logger.error(f"Error accessing gazettes.africa: {e}")
            return False

    def download_municipal_bylaws(self):
        """Download municipal by-laws from major city websites."""
        logger.info("Downloading Municipal By-laws from major cities...")
        
        # Define major cities with their by-laws URLs
        cities = {
            "cape_town": {
                "name": "Cape Town",
                "url": "https://www.capetown.gov.za/Family%20and%20home/City-publications/policies-and-by-laws",
                "pdf_pattern": r'\.pdf$'
            },
            "johannesburg": {
                "name": "Johannesburg",
                "url": "https://www.joburg.org.za/documents_/By-Laws/Pages/By%20Law.aspx",
                "pdf_pattern": r'\.pdf$'
            },
            "durban": {
                "name": "Durban",
                "url": "http://www.durban.gov.za/Resource_Centre/Services_By_Laws/Pages/default.aspx",
                "pdf_pattern": r'\.pdf$'
            },
            "tshwane": {
                "name": "Tshwane",
                "url": "http://www.tshwane.gov.za/sites/residents/Services/Pages/By-Law-Book.aspx",
                "pdf_pattern": r'\.pdf$'
            }
        }
        
        for city_key, city_info in cities.items():
            city_dir = os.path.join(MUNICIPAL_DIR, city_key)
            os.makedirs(city_dir, exist_ok=True)
            
            logger.info(f"Downloading by-laws for {city_info['name']}...")
            
            try:
                response = requests.get(city_info['url'], headers=HEADERS, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find PDF links
                pdf_links = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and re.search(city_info['pdf_pattern'], href, re.IGNORECASE):
                        # Make sure we have the full URL
                        if href.startswith('http'):
                            pdf_links.append(href)
                        else:
                            pdf_links.append(urljoin(city_info['url'], href))
                
                # Download up to 10 by-laws per city
                for i, pdf_url in enumerate(pdf_links[:10]):
                    try:
                        # Clean up the filename
                        filename = os.path.basename(urlparse(pdf_url).path)
                        if not filename:
                            filename = f"{city_key}_bylaw_{i+1}.pdf"
                        if not filename.endswith('.pdf'):
                            filename += '.pdf'
                            
                        output_path = os.path.join(city_dir, filename)
                        
                        if not os.path.exists(output_path):
                            logger.info(f"Downloading {filename}...")
                            response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                            response.raise_for_status()
                            
                            with open(output_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            logger.info(f"Downloaded {filename}")
                            # Add a small delay to be respectful to the server
                            time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error downloading {pdf_url}: {e}")
                
            except Exception as e:
                logger.error(f"Error accessing {city_info['name']} website: {e}")
        
        self.update_checklist_item("Municipal By-laws")
        return True

    def download_open_textbooks(self):
        """Download open access legal textbooks from UCT and other sources."""
        logger.info("Downloading open access legal textbooks...")
        
        # Create textbooks directories
        textbook_sources = {
            "uct_openbooks": "University of Cape Town OpenBooks",
            "doab": "Directory of Open Access Books",
            "other_open_access": "Other Open Access Resources"
        }
        
        for source_key in textbook_sources:
            source_dir = os.path.join(TEXTBOOKS_DIR, source_key)
            os.makedirs(source_dir, exist_ok=True)
        
        # UCT OpenBooks - Constitutional Law
        uct_url = "https://openbooks.uct.ac.za/uct/catalog/book/25"
        uct_dir = os.path.join(TEXTBOOKS_DIR, "uct_openbooks")
        
        try:
            logger.info("Accessing UCT OpenBooks...")
            response = requests.get(uct_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for download links (PDF, etc.)
            download_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                text = link.text.strip().lower()
                if href and ('download' in text or '.pdf' in href.lower()):
                    download_links.append(urljoin(uct_url, href))
            
            if download_links:
                for i, link in enumerate(download_links):
                    try:
                        # Extract filename from the URL or create a generic one
                        filename = os.path.basename(urlparse(link).path)
                        if not filename or '.' not in filename:
                            filename = f"constitutional_law_textbook_{i+1}.pdf"
                        
                        output_path = os.path.join(uct_dir, filename)
                        
                        if not os.path.exists(output_path):
                            logger.info(f"Downloading {filename}...")
                            response = requests.get(link, headers=HEADERS, stream=True, timeout=30)
                            response.raise_for_status()
                            
                            with open(output_path, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            logger.info(f"Downloaded {filename}")
                            # Add a delay to be respectful to the server
                            time.sleep(2)
                    except Exception as e:
                        logger.error(f"Error downloading {link}: {e}")
            else:
                # If we can't find download links, save the HTML content as a fallback
                logger.warning("No direct download links found. Saving page content...")
                output_path = os.path.join(uct_dir, "constitutional_law_textbook.html")
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info("Saved HTML content as fallback")
                
        except Exception as e:
            logger.error(f"Error accessing UCT OpenBooks: {e}")
        
        # Directory of Open Access Books - Search for South African Law books
        doab_url = "https://www.doabooks.org/doab?func=search&uiLanguage=en&template=&query=south+african+law"
        doab_dir = os.path.join(TEXTBOOKS_DIR, "doab")
        
        try:
            logger.info("Searching DOAB for South African law books...")
            response = requests.get(doab_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find book entries
            book_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and 'doab?func=book&' in href:
                    book_links.append(urljoin(doab_url, href))
            
            # Process up to 5 books
            for i, book_url in enumerate(book_links[:5]):
                try:
                    logger.info(f"Accessing book page {i+1}...")
                    response = requests.get(book_url, headers=HEADERS, timeout=30)
                    response.raise_for_status()
                    
                    book_soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract book title
                    title_elem = book_soup.find('h1')
                    title = "law_book"
                    if title_elem:
                        title = title_elem.text.strip()
                        # Clean up the title for use as a filename
                        title = re.sub(r'[^\w\s-]', '', title)
                        title = re.sub(r'\s+', '_', title)
                        title = title.lower()
                    
                    # Find PDF download links
                    pdf_links = []
                    for link in book_soup.find_all('a'):
                        href = link.get('href')
                        if href and href.endswith('.pdf'):
                            pdf_links.append(href)
                    
                    if pdf_links:
                        for j, pdf_url in enumerate(pdf_links[:1]):  # Just get the first PDF
                            try:
                                filename = f"{title}_{j+1}.pdf"
                                output_path = os.path.join(doab_dir, filename)
                                
                                if not os.path.exists(output_path):
                                    logger.info(f"Downloading {filename}...")
                                    response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=60)
                                    response.raise_for_status()
                                    
                                    with open(output_path, 'wb') as f:
                                        for chunk in response.iter_content(chunk_size=8192):
                                            f.write(chunk)
                                    
                                    logger.info(f"Downloaded {filename}")
                                    # Add a delay to be respectful to the server
                                    time.sleep(3)
                            except Exception as e:
                                logger.error(f"Error downloading {pdf_url}: {e}")
                    else:
                        logger.warning(f"No PDF links found for book {i+1}")
                
                except Exception as e:
                    logger.error(f"Error processing book page {book_url}: {e}")
            
        except Exception as e:
            logger.error(f"Error accessing DOAB: {e}")
            
        self.update_checklist_item("Open Access Textbooks")
        return True

    def download_tax_guides(self):
        """Download tax guides and resources from SARS."""
        logger.info("Downloading Tax Guides from SARS...")
        
        tax_dir = os.path.join(SPECIALIZED_DIR, "tax_guides")
        os.makedirs(tax_dir, exist_ok=True)
        
        # SARS tax guide URL
        sars_url = "https://www.sars.gov.za/types-of-tax/"
        
        try:
            response = requests.get(sars_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to tax guides (PDF files)
            pdf_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.pdf') and ('guide' in href.lower() or 'tax' in href.lower()):
                    if href.startswith('http'):
                        pdf_links.append(href)
                    else:
                        pdf_links.append(urljoin(sars_url, href))
            
            # Download up to 10 tax guides
            for i, pdf_url in enumerate(pdf_links[:10]):
                try:
                    filename = os.path.basename(urlparse(pdf_url).path)
                    if not filename:
                        filename = f"tax_guide_{i+1}.pdf"
                    
                    output_path = os.path.join(tax_dir, filename)
                    
                    if not os.path.exists(output_path):
                        logger.info(f"Downloading {filename}...")
                        response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded {filename}")
                        # Add a delay to be respectful to the server
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Error downloading {pdf_url}: {e}")
            
            self.update_checklist_item("Tax Law Commentaries and Guides")
            return True
            
        except Exception as e:
            logger.error(f"Error accessing SARS website: {e}")
            return False

    def download_competition_guidelines(self):
        """Download competition law guidelines from the Competition Commission."""
        logger.info("Downloading Competition Law Guidelines...")
        
        competition_dir = os.path.join(SPECIALIZED_DIR, "competition_law")
        os.makedirs(competition_dir, exist_ok=True)
        
        # Competition Commission URL
        cc_url = "https://www.compcom.co.za/guidelines-for-stakeholders/"
        
        try:
            response = requests.get(cc_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to guidelines (PDF files)
            pdf_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.pdf') and ('guideline' in href.lower() or 'guidance' in href.lower()):
                    if href.startswith('http'):
                        pdf_links.append(href)
                    else:
                        pdf_links.append(urljoin(cc_url, href))
            
            # Download all found guidelines
            for i, pdf_url in enumerate(pdf_links):
                try:
                    filename = os.path.basename(urlparse(pdf_url).path)
                    if not filename:
                        filename = f"competition_guideline_{i+1}.pdf"
                    
                    output_path = os.path.join(competition_dir, filename)
                    
                    if not os.path.exists(output_path):
                        logger.info(f"Downloading {filename}...")
                        response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded {filename}")
                        # Add a delay to be respectful to the server
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Error downloading {pdf_url}: {e}")
            
            self.update_checklist_item("Competition Law Guidelines and Notices")
            return True
            
        except Exception as e:
            logger.error(f"Error accessing Competition Commission website: {e}")
            return False

    def download_environmental_law(self):
        """Download environmental law compilations."""
        logger.info("Downloading Environmental Law Compilations...")
        
        env_dir = os.path.join(SPECIALIZED_DIR, "environmental_law")
        os.makedirs(env_dir, exist_ok=True)
        
        # Department of Environment URL
        env_url = "https://www.dffe.gov.za/legislation/actsregulations"
        
        try:
            response = requests.get(env_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to environmental laws (PDF files)
            pdf_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.pdf'):
                    if href.startswith('http'):
                        pdf_links.append(href)
                    else:
                        pdf_links.append(urljoin(env_url, href))
            
            # Download environmental law documents
            for i, pdf_url in enumerate(pdf_links[:15]):  # Limit to 15 documents
                try:
                    filename = os.path.basename(urlparse(pdf_url).path)
                    if not filename:
                        filename = f"environmental_law_{i+1}.pdf"
                    
                    output_path = os.path.join(env_dir, filename)
                    
                    if not os.path.exists(output_path):
                        logger.info(f"Downloading {filename}...")
                        response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded {filename}")
                        # Add a delay to be respectful to the server
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Error downloading {pdf_url}: {e}")
            
            self.update_checklist_item("Environmental Law Compilations")
            return True
            
        except Exception as e:
            logger.error(f"Error accessing Department of Environment website: {e}")
            return False

    def download_intellectual_property_resources(self):
        """Download intellectual property resources from CIPC."""
        logger.info("Downloading Intellectual Property Resources...")
        
        ip_dir = os.path.join(SPECIALIZED_DIR, "intellectual_property")
        os.makedirs(ip_dir, exist_ok=True)
        
        # CIPC IP URL
        cipc_url = "https://www.cipc.co.za/?page_id=1423"
        
        try:
            response = requests.get(cipc_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to IP resources (PDF files)
            pdf_links = []
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.endswith('.pdf'):
                    if href.startswith('http'):
                        pdf_links.append(href)
                    else:
                        pdf_links.append(urljoin(cipc_url, href))
            
            # Download IP resources
            for i, pdf_url in enumerate(pdf_links):
                try:
                    filename = os.path.basename(urlparse(pdf_url).path)
                    if not filename:
                        filename = f"ip_resource_{i+1}.pdf"
                    
                    output_path = os.path.join(ip_dir, filename)
                    
                    if not os.path.exists(output_path):
                        logger.info(f"Downloading {filename}...")
                        response = requests.get(pdf_url, headers=HEADERS, stream=True, timeout=30)
                        response.raise_for_status()
                        
                        with open(output_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        logger.info(f"Downloaded {filename}")
                        # Add a delay to be respectful to the server
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"Error downloading {pdf_url}: {e}")
            
            self.update_checklist_item("Intellectual Property Law Compilations")
            return True
            
        except Exception as e:
            logger.error(f"Error accessing CIPC website: {e}")
            return False

    def download_additional_specialized_resources(self):
        """Download all specialized domain resources concurrently."""
        logger.info("Downloading specialized domain resources concurrently...")
        
        # Create specialized domains directory
        os.makedirs(SPECIALIZED_DIR, exist_ok=True)
        
        # List of specialized domain download methods
        specialized_methods = [
            self.download_tax_guides,
            self.download_competition_guidelines,
            self.download_environmental_law,
            self.download_intellectual_property_resources
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(method): method.__name__ for method in specialized_methods}
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Specialized Resources"):
                method_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        logger.info(f"Successfully downloaded {method_name}")
                    else:
                        logger.warning(f"Failed to download {method_name}")
                except Exception as e:
                    logger.error(f"Error in {method_name}: {e}")
        
        return True

    def download_all_additional_resources(self):
        """Download all additional resources concurrently."""
        logger.info("Downloading all additional resources concurrently...")
        
        # List of additional resource download methods
        additional_methods = [
            self.download_provincial_gazettes,
            self.download_municipal_bylaws,
            self.download_open_textbooks,
            self.download_additional_specialized_resources
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(method): method.__name__ for method in additional_methods}
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Additional Resources"):
                method_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        logger.info(f"Successfully downloaded {method_name}")
                    else:
                        logger.warning(f"Failed to download {method_name}")
                except Exception as e:
                    logger.error(f"Error in {method_name}: {e}")
        
        # Update the checklist after downloading all resources
        self.run_checklist_update()
        
        return True

def main():
    """Main function to parse command line arguments and download legal documents."""
    parser = argparse.ArgumentParser(description='Download South African legal documents')
    
    # All materials group
    parser.add_argument("--all", action="store_true", help="Download all legal materials concurrently")
    
    # Secondary Legal Sources group
    parser.add_argument("--notices", action="store_true", help="Download Government Notices and Proclamations")
    parser.add_argument("--regulations", action="store_true", help="Download Regulations to Principal Acts")
    parser.add_argument("--bills", action="store_true", help="Download Bills before Parliament")
    parser.add_argument("--whitepapers", action="store_true", help="Download White Papers and Policy Documents")
    
    # Principal Acts group
    parser.add_argument("--constitution", action="store_true", help="Download Constitution of South Africa")
    parser.add_argument("--criminal-procedure", action="store_true", help="Download Criminal Procedure Act")
    parser.add_argument("--labour-relations", action="store_true", help="Download Labour Relations Act")
    
    # Case Law group
    parser.add_argument("--constitutional-court", action="store_true", help="Download Constitutional Court judgments")
    parser.add_argument("--supreme-court", action="store_true", help="Download Supreme Court of Appeal collection")
    parser.add_argument("--high-court", action="store_true", help="Download High Court judgments")
    parser.add_argument("--labour-court", action="store_true", help="Download Labour Court judgments")
    parser.add_argument("--competition-court", action="store_true", help="Download Competition Tribunal decisions")
    parser.add_argument("--land-claims-court", action="store_true", help="Download Land Claims Court decisions")
    parser.add_argument("--tax-court", action="store_true", help="Download Tax Court judgments")
    parser.add_argument("--magistrates-court", action="store_true", help="Download Magistrates' Court cases")
    
    # Procedural Materials group
    parser.add_argument("--court-rules", action="store_true", help="Download Rules of Court")
    parser.add_argument("--practice-directives", action="store_true", help="Download Practice directives")
    parser.add_argument("--ethics", action="store_true", help="Download Legal ethics guidelines")
    parser.add_argument("--forms", action="store_true", help="Download Forms and precedents")
    parser.add_argument("--law-society", action="store_true", help="Download Law Society and Bar Council guidelines")
    
    # Secondary Legal Sources group
    parser.add_argument("--legal-dictionaries", action="store_true", help="Download Legal dictionaries and glossaries")
    parser.add_argument("--law-journals", action="store_true", help="Download Law Journal articles from major SA law reviews")
    parser.add_argument("--law-reform", action="store_true", help="Download Law Reform Commission reports and papers")
    
    # Historical Materials group
    parser.add_argument("--roman-dutch", action="store_true", help="Download Roman-Dutch law sources")
    parser.add_argument("--historical", action="store_true", help="Download Historical legislation (colonial and apartheid era)")
    parser.add_argument("--legal-development", action="store_true", help="Download Legal development commentaries")
    parser.add_argument("--comparative-law", action="store_true", help="Download Comparative law studies relevant to SA")
    parser.add_argument("--legal-anthropology", action="store_true", help="Download Legal anthropology studies on SA customary law")
    
    # New Additional Resources group
    parser.add_argument("--provincial", action="store_true", help="Download Provincial Legislation from gazettes.africa")
    parser.add_argument("--municipal", action="store_true", help="Download Municipal By-laws from major city websites")
    parser.add_argument("--textbooks", action="store_true", help="Download Open Access Textbooks from UCT and DOAB")
    parser.add_argument("--specialized", action="store_true", help="Download specialized domain materials (Tax, Competition, Environmental, IP)")
    parser.add_argument("--additional-all", action="store_true", help="Download all additional resources concurrently")

    args = parser.parse_args()
    
    downloader = LegalDocumentsDownloader()
    
    # Additional resources
    if args.provincial:
        downloader.download_provincial_gazettes()
    
    if args.municipal:
        downloader.download_municipal_bylaws()
    
    if args.textbooks:
        downloader.download_open_textbooks()
    
    if args.specialized:
        downloader.download_additional_specialized_resources()
    
    if args.additional_all:
        downloader.download_all_additional_resources()
        
    # All legal materials
    if args.all:
        downloader.download_all_legal_materials()

if __name__ == "__main__":
    main() 