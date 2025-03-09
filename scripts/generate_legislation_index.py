#!/usr/bin/env python3
"""
generate_legislation_index.py - Generate a directory listing of all legislation.

This script creates a markdown file with all legislation organized by category.
"""

import os
import re
import argparse
import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegislationIndex")

# Constants
SCRAPERS_OUTPUT_DIR = "scrapers_output"
CORE_LEGISLATION_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "core_legislation")
LEGISLATION_DIR = os.path.join(SCRAPERS_OUTPUT_DIR, "legislation")

class LegislationIndexGenerator:
    """Class to generate a markdown index of legislation."""
    
    def __init__(self, base_dir=".", output_file="LEGISLATION_INDEX.md"):
        """Initialize with the base directory and output file."""
        self.base_dir = base_dir
        self.output_file = os.path.join(base_dir, output_file)
        self.core_legislation_dir = os.path.join(base_dir, CORE_LEGISLATION_DIR)
        self.legislation_dir = os.path.join(base_dir, LEGISLATION_DIR)
        
        # Categories and their human-readable names
        self.categories = {
            "commercial": "Commercial Law",
            "financial": "Financial Law",
            "regulatory": "Regulatory Law",
            "constitutional": "Constitutional Law",
            "criminal": "Criminal Law",
            "administrative": "Administrative Law",
            "labor": "Labor Law",
            "environmental": "Environmental Law",
            "intellectual_property": "Intellectual Property Law",
            "other": "Other Legal Materials"
        }
    
    def extract_act_details(self, filename):
        """Extract act name, number, and year from filename."""
        # Remove file extension
        base_name = os.path.splitext(filename)[0]
        
        # Extract act name, number, and year
        act_match = re.search(r"(.*?)(?:\s+(?:No\.?\s*)?(\d+))?\s+of\s+(\d{4})", base_name, re.IGNORECASE)
        if act_match:
            act_name = act_match.group(1).strip()
            act_number = act_match.group(2) or ""
            act_year = act_match.group(3)
            
            return {
                "name": act_name,
                "number": act_number,
                "year": act_year,
                "filename": filename
            }
        
        return {
            "name": base_name,
            "number": "",
            "year": "",
            "filename": filename
        }
    
    def get_legislation_by_category(self):
        """Get all legislation organized by category."""
        legislation = {}
        
        # Initialize categories
        for category in self.categories.keys():
            legislation[category] = []
        
        # Find core legislation
        for category in os.listdir(self.core_legislation_dir):
            category_path = os.path.join(self.core_legislation_dir, category)
            if os.path.isdir(category_path):
                if category not in legislation:
                    legislation[category] = []
                
                for filename in os.listdir(category_path):
                    if os.path.isfile(os.path.join(category_path, filename)):
                        legislation[category].append(self.extract_act_details(filename))
        
        # Find regular legislation
        if os.path.exists(self.legislation_dir):
            for filename in os.listdir(self.legislation_dir):
                file_path = os.path.join(self.legislation_dir, filename)
                if os.path.isfile(file_path):
                    # Determine category based on filename or content
                    # This is a simple approach - you might want to use more sophisticated categorization
                    category = "other"
                    for cat in self.categories.keys():
                        if cat in filename.lower():
                            category = cat
                            break
                    
                    legislation[category].append(self.extract_act_details(filename))
        
        return legislation
    
    def generate_markdown(self):
        """Generate a markdown file with the legislation index."""
        legislation = self.get_legislation_by_category()
        
        with open(self.output_file, 'w') as f:
            f.write("# South African Legislation Index\n\n")
            f.write(f"*Generated on {datetime.datetime.now().strftime('%Y-%m-%d')}*\n\n")
            f.write("This document provides an index of all South African legislation in the repository, organized by category.\n\n")
            
            f.write("## Table of Contents\n\n")
            for category, display_name in self.categories.items():
                if legislation[category]:
                    f.write(f"- [{display_name}](#{category.lower().replace('_', '-')})\n")
            f.write("\n")
            
            for category, display_name in self.categories.items():
                if legislation[category]:
                    f.write(f"## {display_name}\n\n")
                    
                    # Sort by year, then by name
                    sorted_acts = sorted(legislation[category], key=lambda x: (x["year"] or "0000", x["name"].lower()))
                    
                    f.write("| Act | Number | Year |\n")
                    f.write("|-----|--------|------|\n")
                    
                    for act in sorted_acts:
                        act_number = f"No. {act['number']}" if act['number'] else ""
                        act_year = act['year'] or ""
                        f.write(f"| {act['name']} | {act_number} | {act_year} |\n")
                    
                    f.write("\n")
        
        logger.info(f"Generated legislation index at {self.output_file}")
        return self.output_file

def main():
    """Main function to run the index generator."""
    parser = argparse.ArgumentParser(description="Generate a markdown index of legislation.")
    parser.add_argument("--output", default="LEGISLATION_INDEX.md", help="Output file name")
    args = parser.parse_args()
    
    generator = LegislationIndexGenerator(output_file=args.output)
    output_file = generator.generate_markdown()
    
    print(f"Legislation index generated at {output_file}")

if __name__ == "__main__":
    main() 