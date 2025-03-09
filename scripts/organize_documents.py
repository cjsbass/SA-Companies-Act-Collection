#!/usr/bin/env python3
"""
organize_documents.py - Utility script for organizing and validating the document collection.

This script helps ensure the document repository follows best practices by:
1. Checking for required core legislation
2. Validating the organization structure
3. Generating reports on missing or misplaced documents
4. Providing recommendations for better organization
"""

import os
import json
import argparse
import shutil
from pathlib import Path
from collections import defaultdict
import logging
import re

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("DocumentOrganizer")

# Constants
SCRAPERS_OUTPUT_DIR = "scrapers_output"
CORE_LEGISLATION_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "core_legislation")
LEGISLATION_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "legislation")
REGULATORY_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "regulatory_materials")

# Key legislation that should be present
KEY_LEGISLATION = {
    "commercial": [
        {"name": "Companies Act", "number": "71", "year": "2008"},
        {"name": "Consumer Protection Act", "number": "68", "year": "2008"},
        {"name": "Competition Act", "number": "89", "year": "1998"},
        {"name": "Copyright Act", "number": "98", "year": "1978"}
    ],
    "financial": [
        {"name": "Financial Intelligence Centre Act", "number": "38", "year": "2001"},
        {"name": "Financial Sector Regulation Act", "number": "9", "year": "2017"},
        {"name": "National Credit Act", "number": "34", "year": "2005"}
    ],
    "regulatory": [
        {"name": "Promotion of Access to Information Act", "number": "2", "year": "2000"},
        {"name": "Protection of Personal Information Act", "number": "4", "year": "2013"},
        {"name": "Broad-Based Black Economic Empowerment Act", "number": "53", "year": "2003"}
    ]
}

class DocumentOrganizer:
    """Class to handle document organization tasks."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory of the repository."""
        self.base_dir = base_dir
        self.core_legislation_dir = os.path.join(base_dir, CORE_LEGISLATION_DIR)
        self.legislation_dir = os.path.join(base_dir, LEGISLATION_DIR)
        self.regulatory_dir = os.path.join(base_dir, REGULATORY_DIR)
        self.scrapers_output_dir = os.path.join(base_dir, SCRAPERS_OUTPUT_DIR)
        
        # Ensure directories exist
        for directory in [self.core_legislation_dir, self.legislation_dir, self.regulatory_dir]:
            os.makedirs(directory, exist_ok=True)
            
        # Statistics
        self.stats = {
            "total_files": 0,
            "missing_core_legislation": [],
            "unorganized_files": 0,
            "category_counts": defaultdict(int)
        }
    
    def check_for_missing_legislation(self):
        """Check if any key legislation is missing."""
        logger.info("Checking for missing key legislation...")
        
        for category, acts in KEY_LEGISLATION.items():
            category_dir = os.path.join(self.core_legislation_dir, category)
            os.makedirs(category_dir, exist_ok=True)
            
            for act in acts:
                found = False
                act_pattern = f"{act['name']}.*{act['number']}.*{act['year']}|{act['number']}.*{act['year']}.*{act['name']}"
                
                # Search in core_legislation directory
                for root, _, files in os.walk(category_dir):
                    for file in files:
                        if re.search(act_pattern, file, re.IGNORECASE):
                            found = True
                            logger.info(f"Found {act['name']} at {os.path.join(root, file)}")
                            break
                
                if not found:
                    missing_act = f"{act['name']} {act['number']} of {act['year']}"
                    self.stats["missing_core_legislation"].append(missing_act)
                    logger.warning(f"Missing core legislation: {missing_act}")
        
        return self.stats["missing_core_legislation"]
    
    def analyze_directory_structure(self):
        """Analyze the current directory structure and report statistics."""
        logger.info("Analyzing directory structure...")
        
        # Count files by category
        for root, _, files in os.walk(self.scrapers_output_dir):
            for file in files:
                self.stats["total_files"] += 1
                
                # Determine category
                rel_path = os.path.relpath(root, self.scrapers_output_dir)
                category = rel_path.split(os.sep)[0] if os.sep in rel_path else rel_path
                self.stats["category_counts"][category] += 1
                
                # Check for unorganized files
                if root == self.scrapers_output_dir:
                    self.stats["unorganized_files"] += 1
        
        return self.stats
    
    def generate_report(self, output_file=None):
        """Generate a report on the current organization state."""
        logger.info("Generating organization report...")
        
        # Perform all checks
        self.check_for_missing_legislation()
        self.analyze_directory_structure()
        
        # Format the report
        report = {
            "organization_status": {
                "total_files": self.stats["total_files"],
                "files_by_category": dict(self.stats["category_counts"]),
                "unorganized_files": self.stats["unorganized_files"]
            },
            "missing_core_legislation": self.stats["missing_core_legislation"],
            "recommendations": []
        }
        
        # Add recommendations
        if self.stats["missing_core_legislation"]:
            report["recommendations"].append({
                "type": "missing_legislation",
                "message": "Download missing core legislation",
                "details": self.stats["missing_core_legislation"]
            })
        
        if self.stats["unorganized_files"] > 0:
            report["recommendations"].append({
                "type": "organization",
                "message": "Move unorganized files to appropriate directories",
                "count": self.stats["unorganized_files"]
            })
        
        # Print summary
        print("\n=== Document Organization Report ===")
        print(f"Total files: {report['organization_status']['total_files']}")
        print("\nFiles by category:")
        for category, count in report['organization_status']['files_by_category'].items():
            print(f"  - {category}: {count}")
        
        print(f"\nUnorganized files: {report['organization_status']['unorganized_files']}")
        
        if report["missing_core_legislation"]:
            print("\nMissing core legislation:")
            for act in report["missing_core_legislation"]:
                print(f"  - {act}")
        
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec['message']}")
        
        # Save report if requested
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_file}")
        
        return report

    def move_file_to_category(self, file_path, category, subcategory=None):
        """Move a file to the appropriate category directory."""
        dest_dir = os.path.join(self.core_legislation_dir, category)
        if subcategory:
            dest_dir = os.path.join(dest_dir, subcategory)
        
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, os.path.basename(file_path))
        
        shutil.move(file_path, dest_path)
        logger.info(f"Moved {file_path} to {dest_path}")

def main():
    """Main function to run the document organizer."""
    parser = argparse.ArgumentParser(description="Organize and validate the document collection.")
    parser.add_argument("--report", type=str, help="Generate a report and save to specified file")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix organization issues")
    parser.add_argument("--check-missing", action="store_true", help="Check for missing key legislation")
    args = parser.parse_args()
    
    organizer = DocumentOrganizer()
    
    if args.check_missing:
        missing = organizer.check_for_missing_legislation()
        if not missing:
            print("All key legislation is present.")
        else:
            print("Missing key legislation:")
            for act in missing:
                print(f"  - {act}")
    
    if args.report:
        organizer.generate_report(args.report)
    
    if args.fix:
        # Not implemented yet - would move files to correct locations
        print("Auto-fix feature not yet implemented.")
    
    # If no args provided, just generate a report
    if not (args.report or args.fix or args.check_missing):
        organizer.generate_report()

if __name__ == "__main__":
    main() 