#!/usr/bin/env python3
"""
Document Checker Script
-----------------------
This script checks the scrapers_output directory and generates reports on document counts,
missing files, and other statistics without requiring Cursor to index the directory.
"""

import os
import sys
import json
from pathlib import Path
from collections import Counter
import argparse

def count_files_by_extension(directory, max_depth=None):
    """Count files by extension in the directory up to max_depth."""
    counter = Counter()
    start_depth = len(Path(directory).parts)
    
    for root, dirs, files in os.walk(directory):
        # Check depth
        current_depth = len(Path(root).parts) - start_depth
        if max_depth is not None and current_depth > max_depth:
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:  # Skip files with no extension
                counter[ext] += 1
    
    return counter

def count_files_in_subdirectories(directory, max_depth=1):
    """Count files in each immediate subdirectory."""
    results = {}
    base_path = Path(directory)
    
    for item in base_path.iterdir():
        if item.is_dir():
            count = sum(1 for _ in item.glob('**/*') if _.is_file())
            results[item.name] = count
    
    # Sort by count, descending
    return {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}

def find_empty_directories(directory):
    """Find directories that have no files."""
    empty_dirs = []
    
    for root, dirs, files in os.walk(directory):
        # This directory is empty if it has no files and no subdirectories
        if not files and not dirs:
            empty_dirs.append(root)
    
    return empty_dirs

def generate_report(output_dir="scrapers_output"):
    """Generate a comprehensive report on the documents."""
    if not os.path.exists(output_dir):
        print(f"Error: Directory {output_dir} does not exist.")
        return
    
    print(f"\n--- Document Analysis Report for {output_dir} ---\n")
    
    # Count by extension
    extensions = count_files_by_extension(output_dir)
    print("File counts by extension:")
    for ext, count in extensions.most_common():
        print(f"  {ext}: {count}")
    
    # Count by subdirectory
    print("\nFile counts by top-level subdirectory:")
    subdirs = count_files_in_subdirectories(output_dir)
    for subdir, count in subdirs.items():
        print(f"  {subdir}: {count}")
    
    # Look for empty directories
    empty = find_empty_directories(output_dir)
    if empty:
        print("\nEmpty directories:")
        for d in empty:
            print(f"  {d}")
    
    # Calculate total size
    total_size = sum(os.path.getsize(os.path.join(root, file)) 
                     for root, _, files in os.walk(output_dir) 
                     for file in files)
    
    print(f"\nTotal size: {total_size / (1024 * 1024 * 1024):.2f} GB")
    print(f"Total files: {sum(extensions.values())}")
    
    return {
        "extensions": dict(extensions),
        "subdirectories": subdirs,
        "empty_directories": empty,
        "total_size_bytes": total_size,
        "total_files": sum(extensions.values())
    }

def search_for_document(output_dir, search_term):
    """Search for documents matching the search term."""
    count = 0
    found_files = []
    
    print(f"\nSearching for '{search_term}' in {output_dir}...")
    
    for root, _, files in os.walk(output_dir):
        for file in files:
            if search_term.lower() in file.lower():
                full_path = os.path.join(root, file)
                found_files.append(full_path)
                count += 1
                # Limit results to avoid overwhelming output
                if count >= 20:
                    break
        if count >= 20:
            break
    
    print(f"Found {count} matches. First 20 results:")
    for file in found_files:
        print(f"  {file}")
    
    return found_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check and report on document archives")
    parser.add_argument("--dir", default="scrapers_output", help="Directory to check")
    parser.add_argument("--search", help="Search for files matching this term")
    parser.add_argument("--save", action="store_true", help="Save report to JSON file")
    
    args = parser.parse_args()
    
    if args.search:
        search_for_document(args.dir, args.search)
    else:
        report = generate_report(args.dir)
        
        if args.save and report:
            with open("document_report.json", "w") as f:
                json.dump(report, f, indent=2)
            print(f"\nReport saved to document_report.json")

# Example usage:
# python check_documents.py                  # Generate basic report
# python check_documents.py --save           # Generate report and save to JSON
# python check_documents.py --search "companies act"  # Search for specific documents 