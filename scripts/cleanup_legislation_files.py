#!/usr/bin/env python3
"""
cleanup_legislation_files.py - Script to clean up and standardize legislation filenames.

This script removes duplicate files and standardizes naming conventions for legislation files.
"""

import os
import re
import logging
import argparse
import shutil
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegislationCleanup")

# Constants
CORE_LEGISLATION_DIR = "scrapers_output/core_legislation"

class LegislationCleaner:
    """Class to handle cleaning up and standardizing legislation files."""
    
    def __init__(self, base_dir="."):
        """Initialize with the base directory."""
        self.base_dir = base_dir
        self.core_legislation_dir = os.path.join(base_dir, CORE_LEGISLATION_DIR)
        
        # Stats
        self.stats = {
            "duplicates_removed": 0,
            "renamed_files": 0,
            "errors": 0
        }
    
    def standardize_filename(self, filename):
        """Convert a filename to the standard format."""
        # Remove extension
        base_name = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        
        # Replace underscores with spaces
        base_name = base_name.replace('_', ' ')
        
        # Make sure "Act" is capitalized
        base_name = re.sub(r'\bact\b', 'Act', base_name, flags=re.IGNORECASE)
        
        # Format "No X" consistently
        base_name = re.sub(r'(No\.?\s*)?(\d+)(\s+of\s+\d{4})', r'No. \2\3', base_name)
        
        # Return with original extension
        return base_name + ext
    
    def find_duplicate_patterns(self):
        """Find patterns of duplicate files (same content, different naming)."""
        duplicates = []
        
        for category in os.listdir(self.core_legislation_dir):
            category_path = os.path.join(self.core_legislation_dir, category)
            if not os.path.isdir(category_path):
                continue
            
            # Group files by act name/number/year
            act_files = {}
            
            for filename in os.listdir(category_path):
                file_path = os.path.join(category_path, filename)
                if not os.path.isfile(file_path) or filename.startswith('.'):
                    continue
                
                # Extract act name, number, and year
                act_match = re.search(r"(.*?)(?:(?:No\.?\s*)?(\d+))?\s+of\s+(\d{4})", 
                                     filename.replace('_', ' '), 
                                     re.IGNORECASE)
                
                if act_match:
                    act_name = act_match.group(1).strip()
                    act_number = act_match.group(2) or ""
                    act_year = act_match.group(3)
                    
                    key = f"{act_name.lower()}-{act_number}-{act_year}"
                    
                    if key not in act_files:
                        act_files[key] = []
                    
                    act_files[key].append(file_path)
                else:
                    # Handle non-standard filenames with underscores
                    parts = filename.replace('.pdf', '').replace('.txt', '').split('_')
                    if len(parts) >= 3 and parts[-1].isdigit() and parts[-2].isdigit():
                        act_name = ' '.join(parts[:-2])
                        act_number = parts[-2]
                        act_year = parts[-1]
                        
                        key = f"{act_name.lower()}-{act_number}-{act_year}"
                        
                        if key not in act_files:
                            act_files[key] = []
                        
                        act_files[key].append(file_path)
            
            # Find duplicates
            for key, files in act_files.items():
                if len(files) > 1:
                    duplicates.append({
                        "key": key,
                        "files": files
                    })
        
        return duplicates
    
    def cleanup_duplicates(self, dry_run=False):
        """Remove duplicate files, keeping the better named version."""
        duplicates = self.find_duplicate_patterns()
        
        for duplicate in duplicates:
            files = duplicate["files"]
            
            # Sort files by name quality - prefer space-separated and more complete names
            def file_quality(file_path):
                filename = os.path.basename(file_path)
                
                # Prefer PDF to text
                if filename.endswith('.txt'):
                    return -10
                
                # Prefer space-separated names
                if '_' in filename:
                    quality = -5
                else:
                    quality = 0
                
                # Prefer "Act XX of YYYY" format
                if re.search(r"Act.*?No\.?\s*\d+\s+of\s+\d{4}", filename):
                    quality += 10
                
                return quality
            
            sorted_files = sorted(files, key=file_quality, reverse=True)
            
            # Keep the best file, remove others
            keep_file = sorted_files[0]
            for file_path in sorted_files[1:]:
                logger.info(f"Duplicate found: {os.path.basename(file_path)} is duplicate of {os.path.basename(keep_file)}")
                
                if not dry_run:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed: {file_path}")
                        self.stats["duplicates_removed"] += 1
                    except Exception as e:
                        logger.error(f"Error removing {file_path}: {str(e)}")
                        self.stats["errors"] += 1
                else:
                    logger.info(f"Would remove: {file_path}")
    
    def standardize_filenames(self, dry_run=False):
        """Standardize filenames to a consistent format."""
        for category in os.listdir(self.core_legislation_dir):
            category_path = os.path.join(self.core_legislation_dir, category)
            if not os.path.isdir(category_path):
                continue
            
            for filename in os.listdir(category_path):
                file_path = os.path.join(category_path, filename)
                if not os.path.isfile(file_path) or filename.startswith('.'):
                    continue
                
                # Standardize name
                standard_name = self.standardize_filename(filename)
                
                if standard_name != filename:
                    new_path = os.path.join(category_path, standard_name)
                    
                    logger.info(f"Rename: {filename} -> {standard_name}")
                    
                    if not dry_run:
                        try:
                            if os.path.exists(new_path):
                                # If target exists, keep the larger file
                                src_size = os.path.getsize(file_path)
                                dst_size = os.path.getsize(new_path)
                                
                                if src_size > dst_size:
                                    logger.info(f"Replacing existing file with larger version: {new_path}")
                                    os.remove(new_path)
                                    shutil.move(file_path, new_path)
                                    self.stats["renamed_files"] += 1
                                else:
                                    logger.info(f"Removing smaller duplicate: {file_path}")
                                    os.remove(file_path)
                                    self.stats["duplicates_removed"] += 1
                            else:
                                shutil.move(file_path, new_path)
                                self.stats["renamed_files"] += 1
                        except Exception as e:
                            logger.error(f"Error renaming {file_path}: {str(e)}")
                            self.stats["errors"] += 1
                    else:
                        logger.info(f"Would rename: {file_path} -> {new_path}")
    
    def cleanup(self, dry_run=False):
        """Perform the full cleanup process."""
        logger.info("Starting legislation file cleanup...")
        
        # First remove duplicates
        self.cleanup_duplicates(dry_run)
        
        # Then standardize names
        self.standardize_filenames(dry_run)
        
        logger.info("Cleanup complete!")
        logger.info(f"Stats: Duplicates removed: {self.stats['duplicates_removed']}, Files renamed: {self.stats['renamed_files']}, Errors: {self.stats['errors']}")
        
        return self.stats

def main():
    """Main function to run the legislation cleaner."""
    parser = argparse.ArgumentParser(description="Clean up and standardize legislation filenames.")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()
    
    cleaner = LegislationCleaner()
    stats = cleaner.cleanup(args.dry_run)
    
    if args.dry_run:
        print("\nThis was a dry run. No changes were made.")
    else:
        print("\nCleanup complete!")
    
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"Files renamed: {stats['renamed_files']}")
    print(f"Errors: {stats['errors']}")

if __name__ == "__main__":
    main() 