#!/usr/bin/env python3
"""
update_llm_checklist.py - Script to update the SA Legal LLM Checklist.

This script:
1. Analyzes the repository to identify available materials
2. Updates the checklist (SA_LEGAL_LLM_CHECKLIST.md) to reflect current progress
3. Calculates completion statistics

Usage: python3 scripts/update_llm_checklist.py
"""

import os
import re
import json
import argparse
from pathlib import Path
import logging
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ChecklistUpdater")

# Constants
CHECKLIST_FILE = "SA_LEGAL_LLM_CHECKLIST.md"
CORE_LEGISLATION_DIR = "scrapers_output/core_legislation"

# Mapping of legislation to checklist items
LEGISLATION_MAPPING = {
    "Companies Act": {
        "pattern": r"Companies\s+Act.*?71.*?2008",
        "checklist_item": "Companies Act 71 of 2008"
    },
    "Consumer Protection Act": {
        "pattern": r"Consumer\s+Protection\s+Act.*?68.*?2008",
        "checklist_item": "Consumer Protection Act 68 of 2008"
    },
    "Competition Act": {
        "pattern": r"Competition\s+Act.*?89.*?1998",
        "checklist_item": "Competition Act 89 of 1998"
    },
    "Copyright Act": {
        "pattern": r"Copyright\s+Act.*?98.*?1978",
        "checklist_item": "Copyright Act 98 of 1978"
    },
    "Financial Intelligence Centre Act": {
        "pattern": r"Financial\s+Intelligence\s+Centre\s+Act.*?38.*?2001",
        "checklist_item": "Financial Intelligence Centre Act 38 of 2001"
    },
    "Financial Sector Regulation Act": {
        "pattern": r"Financial\s+Sector\s+Regulation\s+Act.*?9.*?2017",
        "checklist_item": "Financial Sector Regulation Act 9 of 2017"
    },
    "National Credit Act": {
        "pattern": r"National\s+Credit\s+Act.*?34.*?2005",
        "checklist_item": "National Credit Act 34 of 2005"
    },
    "PAIA": {
        "pattern": r"(Promotion\s+of\s+Access\s+to\s+Information\s+Act|PAIA).*?2.*?2000",
        "checklist_item": "Promotion of Access to Information Act 2 of 2000"
    },
    "POPI": {
        "pattern": r"(Protection\s+of\s+Personal\s+Information\s+Act|POPI|POPIA).*?4.*?2013",
        "checklist_item": "Protection of Personal Information Act 4 of 2013"
    },
    "BBBEE": {
        "pattern": r"(Broad[\s-]+Based\s+Black\s+Economic\s+Empowerment\s+Act|BBBEE).*?53.*?2003",
        "checklist_item": "Broad-Based Black Economic Empowerment Act 53 of 2003"
    },
    "Constitution": {
        "pattern": r"Constitution\s+of\s+South\s+Africa.*?1996",
        "checklist_item": "Constitution of South Africa (1996) with all amendments"
    },
    "Criminal Procedure Act": {
        "pattern": r"Criminal\s+Procedure\s+Act.*?51.*?1977",
        "checklist_item": "Criminal Procedure Act 51 of 1977"
    },
    "Labour Relations Act": {
        "pattern": r"Labour\s+Relations\s+Act.*?66.*?1995",
        "checklist_item": "Labour Relations Act 66 of 1995"
    }
}

class ChecklistUpdater:
    """Class to update the SA Legal LLM checklist based on repository contents."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory of the repository."""
        self.base_dir = base_dir
        self.checklist_file = os.path.join(base_dir, CHECKLIST_FILE)
        self.core_legislation_dir = os.path.join(base_dir, CORE_LEGISLATION_DIR)
        
        # Detected files
        self.detected_materials = set()
        
        # Checklist structure
        self.categories = {
            "Legislative Framework": {
                "Constitution and Foundational Documents": [],
                "Principal Acts by Domain": [],
                "Secondary Legal Materials": []
            },
            "Case Law": {
                "Higher Courts": [],
                "Lower Courts and Historical Cases": []
            },
            "Secondary Legal Sources": {
                "Academic and Reference Materials": [],
                "Specialized Legal Domains": []
            },
            "Procedural Materials": [],
            "Historical and Contextual Materials": [],
            "Technical Processing Requirements": []
        }
        
        # Total counts by category
        self.category_counts = {}
        
        # Parse existing checklist
        self.parse_existing_checklist()
    
    def parse_existing_checklist(self):
        """Parse the existing checklist file to get items and their status."""
        if not os.path.exists(self.checklist_file):
            logger.warning(f"Checklist file not found: {self.checklist_file}")
            self.initialize_default_checklist()
            return
        
        # Reset categories with empty structure
        self.categories = {
            "Legislative Framework": {
                "Constitution and Foundational Documents": [],
                "Principal Acts by Domain": [],
                "Secondary Legal Materials": []
            },
            "Case Law": {
                "Higher Courts": [],
                "Lower Courts and Historical Cases": []
            },
            "Secondary Legal Sources": {
                "Academic and Reference Materials": [],
                "Specialized Legal Domains": []
            },
            "Procedural Materials": [],
            "Historical and Contextual Materials": [],
            "Technical Processing Requirements": []
        }
        
        current_category = None
        current_subcategory = None
        
        with open(self.checklist_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and non-item lines
                if not line or line.startswith('#') or line.startswith('**'):
                    continue
                
                # Check if it's a category header
                category_match = re.match(r'^## (\d+\.\s*)?(.+)$', line)
                if category_match:
                    current_category = category_match.group(2)
                    current_subcategory = None
                    continue
                
                # Check if it's a subcategory header
                subcategory_match = re.match(r'^### (.+)$', line)
                if subcategory_match:
                    current_subcategory = subcategory_match.group(1)
                    continue
                
                # Check if it's a checklist item
                item_match = re.match(r'^- \[([ xX])\] (.+)$', line)
                if item_match and current_category:
                    is_checked = item_match.group(1).lower() == 'x'
                    item_text = item_match.group(2)
                    
                    # Add to the appropriate category
                    if current_subcategory:
                        if current_subcategory in self.categories[current_category]:
                            self.categories[current_category][current_subcategory].append({
                                "text": item_text,
                                "checked": is_checked
                            })
                    else:
                        if isinstance(self.categories[current_category], list):
                            self.categories[current_category].append({
                                "text": item_text,
                                "checked": is_checked
                            })
    
    def initialize_default_checklist(self):
        """Initialize the checklist with default items if not found."""
        logger.info("Initializing default checklist items")
        
        # Constitution and Foundational Documents
        self.categories["Legislative Framework"]["Constitution and Foundational Documents"] = [
            {"text": "Constitution of South Africa (1996) with all amendments", "checked": False},
            {"text": "Bill of Rights jurisprudence compilation", "checked": False},
            {"text": "Interpretation of Statutes guidelines", "checked": False}
        ]
        
        # Principal Acts by Domain
        self.categories["Legislative Framework"]["Principal Acts by Domain"] = [
            {"text": "Companies Act 71 of 2008", "checked": False},
            {"text": "Consumer Protection Act 68 of 2008", "checked": False},
            {"text": "Competition Act 89 of 1998", "checked": False},
            {"text": "Copyright Act 98 of 1978 (still missing)", "checked": False},
            {"text": "Financial Intelligence Centre Act 38 of 2001", "checked": False},
            {"text": "Financial Sector Regulation Act 9 of 2017", "checked": False},
            {"text": "National Credit Act 34 of 2005", "checked": False},
            {"text": "Promotion of Access to Information Act 2 of 2000", "checked": False},
            {"text": "Protection of Personal Information Act 4 of 2013", "checked": False},
            {"text": "Broad-Based Black Economic Empowerment Act 53 of 2003", "checked": False},
            {"text": "Criminal Procedure Act 51 of 1977", "checked": False},
            {"text": "Prevention of Organised Crime Act 121 of 1998", "checked": False},
            {"text": "Labour Relations Act 66 of 1995", "checked": False},
            {"text": "Basic Conditions of Employment Act 75 of 1997", "checked": False},
            {"text": "National Environmental Management Act 107 of 1998", "checked": False},
            {"text": "Mineral and Petroleum Resources Development Act 28 of 2002", "checked": False},
            {"text": "Income Tax Act 58 of 1962", "checked": False},
            {"text": "Tax Administration Act 28 of 2011", "checked": False},
            {"text": "Customs and Excise Act 91 of 1964", "checked": False},
            {"text": "Electronic Communications and Transactions Act 25 of 2002", "checked": False}
        ]
        
        # Secondary Legal Materials
        self.categories["Legislative Framework"]["Secondary Legal Materials"] = [
            {"text": "Government Notices and Proclamations", "checked": False},
            {"text": "Regulations to Principal Acts", "checked": False},
            {"text": "Bills before Parliament", "checked": False},
            {"text": "White Papers and Policy Documents", "checked": False},
            {"text": "Provincial legislation", "checked": False},
            {"text": "Municipal by-laws (major cities)", "checked": False}
        ]
        
        # Higher Courts
        self.categories["Case Law"]["Higher Courts"] = [
            {"text": "Complete Constitutional Court judgments", "checked": False},
            {"text": "Supreme Court of Appeal complete collection", "checked": False},
            {"text": "High Court judgments (all divisions)", "checked": False},
            {"text": "Labour Court and Labour Appeal Court judgments", "checked": False},
            {"text": "Competition Tribunal and Appeal Court decisions", "checked": False},
            {"text": "Land Claims Court decisions", "checked": False},
            {"text": "Tax Court judgments", "checked": False}
        ]
        
        # Lower Courts and Historical Cases
        self.categories["Case Law"]["Lower Courts and Historical Cases"] = [
            {"text": "Magistrates' Court reported cases", "checked": False},
            {"text": "Pre-1994 landmark cases", "checked": False},
            {"text": "Specialized court decisions", "checked": False},
            {"text": "Foreign judgments cited in SA courts", "checked": False}
        ]
        
        # Academic and Reference Materials
        self.categories["Secondary Legal Sources"]["Academic and Reference Materials"] = [
            {"text": "Standard legal textbooks by authoritative authors", "checked": False},
            {"text": "Law Journal articles from major SA law reviews", "checked": False},
            {"text": "Legal encyclopedias (e.g., LAWSA)", "checked": False},
            {"text": "Legal dictionaries and glossaries", "checked": False},
            {"text": "Practice manuals and handbooks", "checked": False},
            {"text": "Law Reform Commission reports and papers", "checked": False}
        ]
        
        # Specialized Legal Domains
        self.categories["Secondary Legal Sources"]["Specialized Legal Domains"] = [
            {"text": "Customary law materials and research", "checked": False},
            {"text": "Environmental law compilations", "checked": False},
            {"text": "Tax law commentaries and guides", "checked": False},
            {"text": "Maritime law texts", "checked": False},
            {"text": "International law ratified by South Africa", "checked": False},
            {"text": "Banking and finance law materials", "checked": False},
            {"text": "Intellectual property law compilations", "checked": False},
            {"text": "Competition law guidelines and notices", "checked": False}
        ]
        
        # Procedural Materials
        self.categories["Procedural Materials"] = [
            {"text": "Rules of Court (all court levels)", "checked": False},
            {"text": "Practice directives", "checked": False},
            {"text": "Legal ethics guidelines", "checked": False},
            {"text": "Forms and precedents", "checked": False},
            {"text": "Law Society and Bar Council guidelines", "checked": False}
        ]
        
        # Historical and Contextual Materials
        self.categories["Historical and Contextual Materials"] = [
            {"text": "Roman-Dutch law sources", "checked": False},
            {"text": "Historical legislation (colonial and apartheid era)", "checked": False},
            {"text": "Legal development commentaries", "checked": False},
            {"text": "Comparative law studies relevant to SA", "checked": False},
            {"text": "Legal anthropology studies on SA customary law", "checked": False}
        ]
        
        # Technical Processing Requirements
        self.categories["Technical Processing Requirements"] = [
            {"text": "Citation pattern recognition development", "checked": False},
            {"text": "Cross-reference mapping between sources", "checked": False},
            {"text": "Legal hierarchy modeling", "checked": False},
            {"text": "Temporal versioning of legislation", "checked": False},
            {"text": "Multi-language processing capability (11 official languages)", "checked": False},
            {"text": "Legal document structure analysis", "checked": False},
            {"text": "Legal reasoning pattern extraction", "checked": False}
        ]
    
    def scan_repository(self):
        """Scan the repository to detect available materials."""
        logger.info("Scanning repository for legal materials...")
        
        # Scan for legislation
        self.scan_legislation()
        
        logger.info(f"Detected {len(self.detected_materials)} materials in the repository")
    
    def scan_legislation(self):
        """Scan for legislation files and match them to checklist items."""
        if not os.path.exists(self.core_legislation_dir):
            logger.warning(f"Core legislation directory not found: {self.core_legislation_dir}")
            return
        
        for category in os.listdir(self.core_legislation_dir):
            category_path = os.path.join(self.core_legislation_dir, category)
            if not os.path.isdir(category_path):
                continue
                
            for filename in os.listdir(category_path):
                file_path = os.path.join(category_path, filename)
                if not os.path.isfile(file_path) or filename.startswith('.'):
                    continue
                
                # Check against known legislation patterns
                for leg_key, leg_info in LEGISLATION_MAPPING.items():
                    pattern = leg_info["pattern"]
                    if re.search(pattern, filename, re.IGNORECASE):
                        self.detected_materials.add(leg_info["checklist_item"])
                        logger.info(f"Detected legislation: {leg_info['checklist_item']}")
                        break
    
    def update_checklist(self):
        """Update the checklist based on detected materials."""
        # Update checked status based on detected materials
        for category, subcategories in self.categories.items():
            if isinstance(subcategories, dict):
                for subcategory, items in subcategories.items():
                    for item in items:
                        if item["text"] in self.detected_materials:
                            item["checked"] = True
            else:  # If the category doesn't have subcategories
                for item in subcategories:
                    if item["text"] in self.detected_materials:
                        item["checked"] = True
        
        # Calculate category statistics
        self.calculate_statistics()
        
        # Write the updated checklist
        self.write_checklist()
    
    def calculate_statistics(self):
        """Calculate completion statistics for the checklist."""
        total_items = 0
        total_checked = 0
        
        self.category_counts = {}
        
        for category, subcategories in self.categories.items():
            category_items = 0
            category_checked = 0
            
            if isinstance(subcategories, dict):
                for subcategory, items in subcategories.items():
                    category_items += len(items)
                    category_checked += sum(1 for item in items if item["checked"])
            else:
                category_items = len(subcategories)
                category_checked = sum(1 for item in subcategories if item["checked"])
            
            total_items += category_items
            total_checked += category_checked
            
            self.category_counts[category] = {
                "total": category_items,
                "checked": category_checked,
                "percentage": round((category_checked / category_items * 100) if category_items > 0 else 0)
            }
        
        self.total_stats = {
            "total": total_items,
            "checked": total_checked,
            "percentage": round((total_checked / total_items * 100) if total_items > 0 else 0)
        }
    
    def write_checklist(self):
        """Write the updated checklist to the file."""
        with open(self.checklist_file, 'w') as f:
            f.write("# South African Legal LLM Dataset Checklist\n\n")
            f.write("This checklist tracks the materials needed to build a comprehensive South African legal language model.\n\n")
            
            # Write categories
            for category, subcategories in self.categories.items():
                if category.startswith(tuple("0123456789")):
                    f.write(f"## {category}\n\n")
                else:
                    f.write(f"## {category}\n\n")
                
                if isinstance(subcategories, dict):
                    for subcategory, items in subcategories.items():
                        f.write(f"### {subcategory}\n")
                        for item in items:
                            check_mark = "x" if item["checked"] else " "
                            f.write(f"- [{check_mark}] {item['text']}\n")
                        f.write("\n")
                else:
                    for item in subcategories:
                        check_mark = "x" if item["checked"] else " "
                        f.write(f"- [{check_mark}] {item['text']}\n")
                    f.write("\n")
            
            # Write progress summary
            f.write("## Progress Summary\n\n")
            f.write(f"**Overall Completion**: {self.total_stats['checked']}/{self.total_stats['total']} items ({self.total_stats['percentage']}%)\n\n")
            
            f.write("**By Category**:\n")
            for category, stats in self.category_counts.items():
                f.write(f"- {category}: {stats['checked']}/{stats['total']} ({stats['percentage']}%)\n")
            
            logger.info(f"Updated checklist written to {self.checklist_file}")
    
    def update(self):
        """Perform the full update process."""
        logger.info("Starting checklist update...")
        
        self.scan_repository()
        self.update_checklist()
        
        logger.info("Checklist update complete!")
        
        return {
            "total_stats": self.total_stats,
            "category_counts": self.category_counts
        }

def main():
    """Main function to run the checklist updater."""
    parser = argparse.ArgumentParser(description="Update the SA Legal LLM Checklist based on repository contents.")
    parser.add_argument("--output", help="Output file for the checklist (default: SA_LEGAL_LLM_CHECKLIST.md)")
    args = parser.parse_args()
    
    updater = ChecklistUpdater()
    stats = updater.update()
    
    print("\nSA Legal LLM Checklist Update Complete!")
    print(f"Overall Progress: {stats['total_stats']['checked']}/{stats['total_stats']['total']} items ({stats['total_stats']['percentage']}%)")
    
    print("\nProgress by Category:")
    for category, count in stats['category_counts'].items():
        print(f"- {category}: {count['checked']}/{count['total']} ({count['percentage']}%)")

if __name__ == "__main__":
    main() 