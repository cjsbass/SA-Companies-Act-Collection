#!/usr/bin/env python3
"""
Script to consolidate the Banks Act 94 of 1990 with all its amendments up to 2022.
This script will:
1. Extract text from all PDFs
2. Process amendments in chronological order
3. Create a consolidated version
"""

import os
import re
import PyPDF2
from pathlib import Path

def clean_text(text):
    """Clean extracted text by removing headers, footers, and page numbers."""
    # Remove page numbers and headers
    text = re.sub(r'GOVERNMENT GAZETTE.*?\d+\s*', '', text)
    text = re.sub(r'No\.\s*\d+\s*\d+', '', text)
    # Remove multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return clean_text(text)
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None

def write_header():
    """Create the header for the consolidated act."""
    return """BANKS ACT 94 OF 1990
[CONSOLIDATED VERSION INCLUDING AMENDMENTS UP TO 2022]

Last updated: March 8, 2024
Original Act: Banks Act 94 of 1990 (formerly Deposit-taking Institutions Act)

Amendments incorporated:
1. Banks Amendment Act 3 of 2015
2. Financial Sector Regulation Act 9 of 2017
3. Financial Matters Amendment Act 18 of 2019
4. Financial Sector Laws Amendment Act 23 of 2021
5. Financial Sector and Deposit Insurance Levies Act 11 of 2022

Note: This consolidated version has been prepared for convenience. While every effort 
has been made to ensure accuracy, the official Government Gazette versions of the 
Act and its amendments remain the authoritative sources.

--------------------

"""

def process_amendments(base_text, amendments):
    """Process amendments in chronological order."""
    consolidated = base_text
    
    # Process each amendment
    for amendment_path in amendments:
        print(f"\nProcessing amendment: {amendment_path}")
        amendment_text = extract_text_from_pdf(amendment_path)
        if amendment_text:
            # Extract amendment sections
            sections = re.finditer(
                r'(?:Section|section) (\d+)[^.]*?(?:is hereby amended|shall be amended)[^.]*?(?:by|as follows)(?:[^.]*?:)?(.*?)(?=(?:Section|section) \d+|$)',
                amendment_text,
                re.DOTALL | re.IGNORECASE
            )
            
            for section in sections:
                section_num = section.group(1)
                amendment_details = section.group(2).strip()
                print(f"\nFound amendment to Section {section_num}")
                
                # Find the section in the consolidated text
                section_pattern = rf"(?:Section|section) {section_num}\.[^\n]*\n"
                section_match = re.search(section_pattern, consolidated)
                
                if section_match:
                    section_start = section_match.start()
                    next_section = re.search(rf"(?:Section|section) {int(section_num) + 1}\.", consolidated[section_start:])
                    section_end = next_section.start() + section_start if next_section else len(consolidated)
                    section_text = consolidated[section_start:section_end]
                    
                    # Process different types of amendments
                    amendments_list = re.split(r'[;.](?:\s*and\s*|\s*)?', amendment_details)
                    
                    for amendment in amendments_list:
                        amendment = amendment.strip()
                        if not amendment:
                            continue
                            
                        print(f"Processing amendment: {amendment}")
                        
                        # Handle substitutions
                        if re.search(r'substitution|replacing|substitute', amendment, re.IGNORECASE):
                            old_text = re.search(r'(?:substitution for|replacing|of)[^"]*"([^"]*)"', amendment)
                            new_text = re.search(r'(?:with|by|of)[^"]*"([^"]*)"(?:\s*$|\s*[,;])', amendment)
                            
                            if old_text and new_text:
                                old_text = old_text.group(1).strip()
                                new_text = new_text.group(1).strip()
                                print(f"Substituting: '{old_text}' with '{new_text}'")
                                section_text = section_text.replace(old_text, new_text)
                        
                        # Handle insertions
                        elif re.search(r'insertion|inserting|insert', amendment, re.IGNORECASE):
                            insert_text = re.search(r'(?:insertion of|inserting|insert)[^"]*"([^"]*)"', amendment)
                            if insert_text:
                                insert_text = insert_text.group(1).strip()
                                print(f"Inserting: '{insert_text}'")
                                
                                # Check for position specifiers
                                if 'after' in amendment.lower():
                                    after_text = re.search(r'after[^"]*"([^"]*)"', amendment)
                                    if after_text:
                                        after_text = after_text.group(1).strip()
                                        section_text = section_text.replace(after_text, after_text + insert_text)
                                elif 'before' in amendment.lower():
                                    before_text = re.search(r'before[^"]*"([^"]*)"', amendment)
                                    if before_text:
                                        before_text = before_text.group(1).strip()
                                        section_text = section_text.replace(before_text, insert_text + before_text)
                                else:
                                    section_text += f"\n{insert_text}"
                        
                        # Handle deletions
                        elif re.search(r'deletion|deleting|delete|omission', amendment, re.IGNORECASE):
                            delete_text = re.search(r'(?:deletion of|deleting|delete|omission of)[^"]*"([^"]*)"', amendment)
                            if delete_text:
                                delete_text = delete_text.group(1).strip()
                                print(f"Deleting: '{delete_text}'")
                                section_text = section_text.replace(delete_text, "")
                    
                    # Update the consolidated text with the amended section
                    consolidated = consolidated[:section_start] + section_text + consolidated[section_end:]
                    print(f"Applied amendments to Section {section_num}")
    
    return consolidated

def format_consolidated_text(text):
    """Format the consolidated text for better readability."""
    # Add proper spacing between sections
    text = re.sub(r'(?:Section|section) (\d+)', r'\n\nSection \1', text)
    
    # Format definitions and subsections
    text = re.sub(r'\((\w+)\)', r'\n    (\1)', text)
    text = re.sub(r'\((\d+)\)', r'\n    (\1)', text)
    
    # Clean up multiple newlines and spaces
    text = re.sub(r'\n{3,}', r'\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Add proper indentation for subsections
    text = re.sub(r'\n    \(', r'\n        (', text)
    
    return text.strip()

def main():
    base_dir = Path('scrapers_output/core_legislation/financial')
    
    # Original Act
    original_act = base_dir / 'Banks_Act_94_1990_English.pdf'
    
    # Amendments in chronological order
    amendments = [
        base_dir / 'Banks_Amendment_Act_3_2015.pdf',
        base_dir / 'Financial_Sector_Regulation_Act_9_2017.pdf',
        base_dir / 'Financial_Matters_Amendment_Act_18_2019.pdf',
        base_dir / 'Financial_Sector_Laws_Amendment_Act_23_2021.pdf',
        base_dir / 'Financial_Sector_and_Deposit_Insurance_Levies_Act_11_2022.pdf'
    ]
    
    # Extract text from original act
    print("Processing original Banks Act...")
    base_text = extract_text_from_pdf(original_act)
    if not base_text:
        print("Failed to process original act")
        return
    
    # Create consolidated version
    consolidated = write_header()
    consolidated += format_consolidated_text(base_text)
    consolidated = process_amendments(consolidated, amendments)
    
    # Save consolidated version
    output_path = base_dir / 'Banks_Act_94_1990_Consolidated.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(consolidated)
    
    print(f"Consolidated version saved to {output_path}")

if __name__ == '__main__':
    main() 