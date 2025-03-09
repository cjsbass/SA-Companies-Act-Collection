#!/usr/bin/env python3
"""
Workspace cleaner script to help prevent Cursor crashes with large repos.
This script removes temporary files, cleans caches, and optimizes the workspace.
"""

import os
import sys
import glob
import shutil
import argparse
from pathlib import Path

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Clean workspace to prevent Cursor crashes")
    parser.add_argument("--temp", action="store_true", help="Remove temporary files (logs, nohup.out, etc)")
    parser.add_argument("--cache", action="store_true", help="Clean Python and Cursor caches")
    parser.add_argument("--all", action="store_true", help="Perform all cleaning operations")
    return parser.parse_args()

def remove_temp_files():
    """Remove temporary files like logs, nohup.out, etc."""
    temp_patterns = [
        "**/*.log",
        "**/nohup.out",
        "**/*.tmp",
        "**/*.bak",
        "**/__pycache__/**",
        "**/.pytest_cache/**",
        "**/.ipynb_checkpoints/**"
    ]
    
    removed = 0
    total_size = 0
    
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        removed += 1
                        total_size += size
                        print(f"Removed: {file_path} ({size/1024:.1f} KB)")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        removed += 1
                        print(f"Removed directory: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")
    
    print(f"\nRemoved {removed} temporary files/directories totaling {total_size/1024/1024:.2f} MB")

def clean_cursor_cache():
    """Clean Cursor-specific cache directories."""
    home = Path.home()
    cursor_cache_dirs = [
        home / "Library" / "Application Support" / "Cursor" / "Cache",
        home / "Library" / "Application Support" / "Cursor" / "Code Cache",
        home / "Library" / "Application Support" / "Cursor" / "GPUCache",
        home / ".cursor" / "extensions",
        Path(".cursor")
    ]
    
    for cache_dir in cursor_cache_dirs:
        if cache_dir.exists() and cache_dir.is_dir():
            try:
                for item in cache_dir.glob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                print(f"Cleaned cache directory: {cache_dir}")
            except Exception as e:
                print(f"Error cleaning {cache_dir}: {e}")

def main():
    """Main function."""
    args = parse_args()
    
    if not (args.temp or args.cache or args.all):
        print("No cleaning option selected. Use --temp, --cache, or --all")
        parser.print_help()
        return
    
    print("Starting workspace cleanup...")
    
    if args.temp or args.all:
        print("\n== Removing Temporary Files ==")
        remove_temp_files()
    
    if args.cache or args.all:
        print("\n== Cleaning Cursor Cache ==")
        clean_cursor_cache()
    
    print("\nWorkspace cleanup complete. Restart Cursor for best results.")

if __name__ == "__main__":
    main() 