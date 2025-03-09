#!/usr/bin/env python3
"""
Script for processing South African legal documents to prepare them for LLM training.
This script implements various technical processing requirements for legal documents:
1. Citation pattern recognition
2. Legal document structure analysis
3. Cross-reference mapping
4. Legal hierarchy modeling
5. Temporal versioning
6. Multi-language processing
7. Legal reasoning pattern extraction
"""

import os
import sys
import re
import argparse
import json
import logging
import concurrent.futures
from pathlib import Path
from tqdm import tqdm
import spacy
import pandas as pd
from datetime import datetime
import PyPDF2
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import networkx as nx
import pickle

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("LegalDocumentProcessor")

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, "scrapers_output")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed_output")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Create necessary directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "citations"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "structure"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "cross_references"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "hierarchy"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "temporal"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "multilingual"), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, "reasoning"), exist_ok=True)

# Initialize NLP components
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
except Exception as e:
    logger.warning(f"Error downloading NLTK resources: {e}")

# Try to load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception as e:
    logger.warning(f"Could not load spaCy model: {e}. Will try to download.")
    try:
        os.system("python -m spacy download en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    except Exception as e2:
        logger.error(f"Failed to load spaCy model after attempted download: {e2}")
        nlp = None

class LegalDocumentProcessor:
    """Class to process South African legal documents for LLM training."""
    
    def __init__(self, input_dir=INPUT_DIR, output_dir=OUTPUT_DIR, models_dir=MODELS_DIR):
        """Initialize with input and output directories."""
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.models_dir = models_dir
        
        # Define citation patterns for South African law
        self.citation_patterns = [
            # Case citations
            r'\d{4}\s*\(\s*\d+\s*\)\s*\w+\s*\d+\s*\(\w+\)',  # e.g., 2008 (2) SA 232 (SCA)
            r'\[\d{4}\]\s*\w+\s*\d+\s*\(\w+\)',              # e.g., [2008] ZASCA 10
            r'\d{4}\s*\(\d+\)\s*BCLR\s*\d+',                 # e.g., 2001 (1) BCLR 36
            
            # Legislation citations
            r'Act\s+No\.\s*\d+\s+of\s+\d{4}',                # e.g., Act No. 108 of 1996
            r'Act\s+\d+\s+of\s+\d{4}',                        # e.g., Act 108 of 1996
            
            # Section references
            r'section\s+\d+(\(\w+\))?',                      # e.g., section 25(b)
            r's\s*\d+(\(\w+\))?',                            # e.g., s 25(b)
            
            # Constitution references
            r'Constitution',
            r'constitutional',
            
            # Regulations and notices
            r'GN\s+\d+',                                     # Government Notice
            r'GG\s+\d+',                                     # Government Gazette
        ]
        
        # Document structure patterns
        self.structure_patterns = {
            "heading": r'^[A-Z\d\s.,;:\'\"&()[\]{}#*-]+$',
            "section": r'^(\d+\.|\(\d+\)|\([a-z]\)|\d+\s*\.\s*\d+\s*\.)',
            "subsection": r'^\([a-z]\)',
            "paragraph": r'^[a-z]\.',
            "subparagraph": r'^\([ivxlcdm]+\)',
            "definition": r'^"[^"]+"\s+means',
            "table_header": r'\|\s*\w+\s*\|',
            "list_item": r'^\s*•\s+',
            "footnote": r'^\s*\d+\.\s+',
            "preamble": r'^PREAMBLE',
            "endnote": r'^(END ?NOTES|NOTES)'
        }
        
        # Languages for multilingual processing
        self.languages = {
            "en": "English",
            "af": "Afrikaans",
            "zu": "Zulu",
            "xh": "Xhosa",
            "st": "Sotho",
            "tn": "Tswana",
            "nso": "Northern Sotho",
            "ts": "Tsonga",
            "ss": "Swati",
            "ve": "Venda",
            "nr": "Ndebele"
        }
        
        # Legal reasoning patterns
        self.reasoning_patterns = {
            "ratio_decidendi": [
                r'accordingly[,.]',
                r'for these reasons',
                r'it follows that',
                r'I conclude that',
                r'therefore'
            ],
            "obiter_dicta": [
                r'I note that',
                r'it is worth observing',
                r'although not necessary for this decision',
                r'it may be noted'
            ],
            "statutory_interpretation": [
                r'interpreting section',
                r'meaning of the provision',
                r'legislative intent',
                r'purpose of the Act'
            ],
            "constitutional_reasoning": [
                r'constitutional values',
                r'fundamental rights',
                r'limitation of rights',
                r'section 36 analysis'
            ],
            "precedent_application": [
                r'following the decision in',
                r'as held in',
                r'binding precedent',
                r'stare decisis'
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF file using PyMuPDF (fitz)."""
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path} with PyMuPDF: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                return text
            except Exception as e2:
                logger.error(f"Error extracting text with PyPDF2 as well: {e2}")
                return ""
    
    def extract_text_from_file(self, file_path):
        """Extract text from various file formats."""
        ext = file_path.lower().split('.')[-1]
        
        if ext == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif ext in ['txt', 'text']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        elif ext == 'html' or ext == 'htm':
            try:
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    return soup.get_text()
            except Exception as e:
                logger.error(f"Error extracting text from HTML {file_path}: {e}")
                return ""
        elif ext in ['doc', 'docx']:
            try:
                import docx
                doc = docx.Document(file_path)
                return '\n'.join([para.text for para in doc.paragraphs])
            except Exception as e:
                logger.error(f"Error extracting text from Word document {file_path}: {e}")
                return ""
        elif ext == 'rtf':
            try:
                # For RTF, we can use a simpler approach with regex to strip RTF codes
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    rtf_text = f.read()
                    # Remove RTF control codes
                    clean_text = re.sub(r'\\[a-z0-9]+', ' ', rtf_text)
                    clean_text = re.sub(r'\{|\}|\\|;', ' ', clean_text)
                    return clean_text
            except Exception as e:
                logger.error(f"Error extracting text from RTF {file_path}: {e}")
                return ""
        else:
            logger.warning(f"Unsupported file format: {ext} for file {file_path}")
            return ""
    
    def process_citations(self, text, doc_id):
        """Extract and process legal citations from text."""
        citations = []
        
        # Extract citations using predefined patterns
        for pattern in self.citation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citation = {
                    "text": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "pattern_type": pattern,
                    "document_id": doc_id
                }
                citations.append(citation)
        
        return citations
    
    def analyze_document_structure(self, text, doc_id):
        """Analyze the structure of a legal document."""
        structure = {
            "document_id": doc_id,
            "elements": []
        }
        
        # Split text into lines for structure analysis
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Identify the type of structural element
            element_type = "text"  # Default
            for struct_type, pattern in self.structure_patterns.items():
                if re.match(pattern, line):
                    element_type = struct_type
                    break
            
            element = {
                "line_number": i,
                "text": line,
                "type": element_type
            }
            
            structure["elements"].append(element)
        
        return structure
    
    def map_cross_references(self, citations, doc_id):
        """Map cross-references between documents based on citations."""
        cross_refs = {
            "document_id": doc_id,
            "references": []
        }
        
        for citation in citations:
            # For each citation, try to identify the target document
            target_doc = self.identify_target_document(citation["text"])
            if target_doc:
                ref = {
                    "citation": citation["text"],
                    "target_document": target_doc,
                    "location": citation["start"]
                }
                cross_refs["references"].append(ref)
        
        return cross_refs
    
    def identify_target_document(self, citation_text):
        """Try to identify the target document from a citation text."""
        # This is a placeholder for a more sophisticated lookup 
        # that would match citations to actual documents in the collection
        
        # For now, we'll extract some basic identifying information
        # Act citations
        act_match = re.search(r'Act\s+(?:No\.\s*)?(\d+)\s+of\s+(\d{4})', citation_text, re.IGNORECASE)
        if act_match:
            return f"act_{act_match.group(2)}_{act_match.group(1)}"
        
        # Case citations
        case_match = re.search(r'(\d{4})\s*\(\s*\d+\s*\)\s*(\w+)\s*\d+\s*\((\w+)\)', citation_text)
        if case_match:
            return f"case_{case_match.group(1)}_{case_match.group(2)}_{case_match.group(3)}"
        
        return None
    
    def model_legal_hierarchy(self, documents):
        """Model the hierarchy of legal documents."""
        # Create a directed graph to represent legal hierarchy
        hierarchy_graph = nx.DiGraph()
        
        # Add nodes for constitution, acts, regulations, and cases
        hierarchy_graph.add_node("constitution", level=0, type="constitution")
        
        # Process documents to add them to the hierarchy
        for doc_id, doc_info in documents.items():
            doc_type = doc_info.get("type", "unknown")
            
            if doc_type == "act":
                hierarchy_graph.add_node(doc_id, level=1, type="act")
                hierarchy_graph.add_edge("constitution", doc_id)
            
            elif doc_type == "regulation":
                # Connect regulation to its parent act
                parent_act = doc_info.get("parent_act")
                if parent_act and parent_act in hierarchy_graph:
                    hierarchy_graph.add_node(doc_id, level=2, type="regulation")
                    hierarchy_graph.add_edge(parent_act, doc_id)
            
            elif doc_type == "case":
                # Cases interpret legislation or other cases
                hierarchy_graph.add_node(doc_id, level=3, type="case")
                
                # Add edges based on citations
                for ref in doc_info.get("references", []):
                    if ref["target_document"] in hierarchy_graph:
                        hierarchy_graph.add_edge(ref["target_document"], doc_id, relation="interprets")
        
        return hierarchy_graph
    
    def process_temporal_versioning(self, documents):
        """Process temporal versioning of legislation."""
        # Group documents by their base identifier (e.g., all versions of same act)
        document_versions = {}
        
        for doc_id, doc_info in documents.items():
            if doc_info.get("type") != "act":
                continue
                
            # Extract the base identifier (act name without amendments)
            base_id_match = re.match(r'(.*?)(?:\s+Amendment)?$', doc_info.get("title", ""))
            if base_id_match:
                base_id = base_id_match.group(1).strip()
                
                if base_id not in document_versions:
                    document_versions[base_id] = []
                
                # Add this document with its date
                document_versions[base_id].append({
                    "doc_id": doc_id,
                    "date": doc_info.get("date"),
                    "version": doc_info.get("version", "unknown"),
                    "title": doc_info.get("title")
                })
        
        # Sort versions by date
        for base_id in document_versions:
            document_versions[base_id].sort(key=lambda x: x.get("date", ""))
        
        return document_versions
    
    def detect_language(self, text):
        """Detect the language of text."""
        # Simple language detection based on common words
        # For a production system, use a proper language detection library
        language_scores = {}
        
        # Short sample for performance
        sample = text[:1000].lower()
        
        # Common words in South African languages
        language_words = {
            "en": ["the", "and", "of", "to", "a", "in", "that", "is"],
            "af": ["die", "en", "van", "in", "is", "het", "nie", "dat"],
            "zu": ["ukuthi", "umuntu", "futhi", "ngokuthi", "ngoba", "uma"],
            "xh": ["ukuba", "kunye", "ukuze", "umtu", "kodwa", "kuba"],
            "st": ["hore", "le", "ka", "ho", "ke", "ha", "tse", "ya"],
            "tn": ["gore", "le", "ka", "go", "ke", "ga", "tse", "ya"],
            "nso": ["gore", "le", "ka", "go", "ke", "ga", "tše", "ya"],
            "ts": ["ku", "na", "ni", "va", "swi", "laha", "loko", "kambe"],
            "ss": ["kutsi", "uma", "naloku", "ngoba", "kuze", "kantsi"],
            "ve": ["uri", "na", "vha", "nga", "kha", "ha", "ndi", "hu"],
            "nr": ["bona", "ukuthi", "lokhu", "lapho", "uma", "ngakho"]
        }
        
        # Count word occurrences
        for lang, words in language_words.items():
            score = 0
            for word in words:
                score += len(re.findall(r'\b' + re.escape(word) + r'\b', sample))
            language_scores[lang] = score
        
        # Return the language with the highest score
        if not language_scores:
            return "en"  # Default to English
            
        max_lang = max(language_scores.items(), key=lambda x: x[1])
        if max_lang[1] == 0:
            return "en"  # Default to English if no matches
            
        return max_lang[0]
    
    def extract_legal_reasoning(self, text, doc_id):
        """Extract legal reasoning patterns from text."""
        reasoning = {
            "document_id": doc_id,
            "patterns": {}
        }
        
        # For each reasoning type, find matches of its patterns
        for reasoning_type, patterns in self.reasoning_patterns.items():
            reasoning["patterns"][reasoning_type] = []
            
            # Split text into sentences for context
            sentences = sent_tokenize(text)
            
            for pattern in patterns:
                for i, sentence in enumerate(sentences):
                    if re.search(pattern, sentence, re.IGNORECASE):
                        # Get context (previous and next sentence if available)
                        prev_sent = sentences[i-1] if i > 0 else ""
                        next_sent = sentences[i+1] if i < len(sentences)-1 else ""
                        
                        match = {
                            "pattern": pattern,
                            "sentence": sentence,
                            "context": f"{prev_sent} {sentence} {next_sent}".strip()
                        }
                        
                        reasoning["patterns"][reasoning_type].append(match)
        
        return reasoning
    
    def process_file(self, file_path):
        """Process a single legal document file."""
        try:
            # Extract base filename for document ID
            doc_id = os.path.splitext(os.path.basename(file_path))[0]
            
            # Extract text from the file
            text = self.extract_text_from_file(file_path)
            if not text:
                logger.warning(f"No text extracted from {file_path}")
                return None
            
            # Process citations
            citations = self.process_citations(text, doc_id)
            
            # Analyze document structure
            structure = self.analyze_document_structure(text, doc_id)
            
            # Map cross-references
            cross_refs = self.map_cross_references(citations, doc_id)
            
            # Detect language
            language = self.detect_language(text)
            
            # Extract legal reasoning patterns
            reasoning = self.extract_legal_reasoning(text, doc_id)
            
            # Create document info dictionary
            doc_info = {
                "id": doc_id,
                "path": file_path,
                "type": self.infer_document_type(file_path),
                "language": language,
                "citation_count": len(citations),
                "structure": {
                    "elements_count": len(structure["elements"]),
                    "element_types": self.count_element_types(structure["elements"])
                },
                "cross_references": len(cross_refs["references"]),
                "reasoning_patterns": {rt: len(patterns) for rt, patterns in reasoning["patterns"].items()}
            }
            
            # Save detailed processing results to separate files
            self.save_processing_results(doc_id, {
                "citations": citations,
                "structure": structure,
                "cross_references": cross_refs,
                "reasoning": reasoning
            })
            
            return doc_id, doc_info
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def infer_document_type(self, file_path):
        """Infer the document type based on its path and name."""
        path_lower = file_path.lower()
        
        if "constitution" in path_lower:
            return "constitution"
        elif "core_legislation" in path_lower or "act" in path_lower:
            return "act"
        elif "case_law" in path_lower or "judgment" in path_lower:
            return "case"
        elif "regulation" in path_lower:
            return "regulation"
        elif "provincial" in path_lower:
            return "provincial_legislation"
        elif "municipal" in path_lower or "bylaw" in path_lower:
            return "municipal_bylaw"
        else:
            return "unknown"
    
    def count_element_types(self, elements):
        """Count the frequency of each element type in the document structure."""
        counts = {}
        for element in elements:
            element_type = element["type"]
            counts[element_type] = counts.get(element_type, 0) + 1
        return counts
    
    def save_processing_results(self, doc_id, results):
        """Save detailed processing results to separate files."""
        # Citations
        with open(os.path.join(self.output_dir, "citations", f"{doc_id}_citations.json"), 'w', encoding='utf-8') as f:
            json.dump(results["citations"], f, indent=2)
        
        # Structure
        with open(os.path.join(self.output_dir, "structure", f"{doc_id}_structure.json"), 'w', encoding='utf-8') as f:
            json.dump(results["structure"], f, indent=2)
        
        # Cross-references
        with open(os.path.join(self.output_dir, "cross_references", f"{doc_id}_xrefs.json"), 'w', encoding='utf-8') as f:
            json.dump(results["cross_references"], f, indent=2)
        
        # Reasoning
        with open(os.path.join(self.output_dir, "reasoning", f"{doc_id}_reasoning.json"), 'w', encoding='utf-8') as f:
            json.dump(results["reasoning"], f, indent=2)
    
    def process_directory(self, directory, max_files=None):
        """Process all legal documents in a directory and its subdirectories."""
        logger.info(f"Processing documents in {directory}...")
        
        # Find all document files recursively
        file_extensions = ['.pdf', '.txt', '.html', '.htm', '.doc', '.docx', '.rtf']
        document_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in file_extensions):
                    document_files.append(os.path.join(root, file))
        
        # Limit the number of files if specified
        if max_files and len(document_files) > max_files:
            document_files = document_files[:max_files]
        
        logger.info(f"Found {len(document_files)} document files to process")
        
        # Process files concurrently
        documents = {}
        with concurrent.futures.ProcessPoolExecutor() as executor:
            future_to_file = {executor.submit(self.process_file, file): file for file in document_files}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_file), total=len(document_files), desc="Processing documents"):
                file = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        doc_id, doc_info = result
                        documents[doc_id] = doc_info
                except Exception as e:
                    logger.error(f"Error processing file {file}: {e}")
        
        # Additional processing on the complete document collection
        if documents:
            # Model legal hierarchy
            hierarchy_graph = self.model_legal_hierarchy(documents)
            
            # Save the hierarchy graph
            nx.write_gpickle(hierarchy_graph, os.path.join(self.output_dir, "hierarchy", "legal_hierarchy.gpickle"))
            
            # Export a simple representation as JSON
            hierarchy_data = {
                "nodes": [{"id": node, "type": data["type"], "level": data["level"]} 
                        for node, data in hierarchy_graph.nodes(data=True)],
                "edges": [{"source": source, "target": target} 
                        for source, target in hierarchy_graph.edges()]
            }
            with open(os.path.join(self.output_dir, "hierarchy", "legal_hierarchy.json"), 'w', encoding='utf-8') as f:
                json.dump(hierarchy_data, f, indent=2)
            
            # Process temporal versioning
            document_versions = self.process_temporal_versioning(documents)
            
            # Save the temporal versioning information
            with open(os.path.join(self.output_dir, "temporal", "document_versions.json"), 'w', encoding='utf-8') as f:
                json.dump(document_versions, f, indent=2)
            
            # Save all document information
            with open(os.path.join(self.output_dir, "document_info.json"), 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2)
            
            # Generate summary statistics
            stats = {
                "total_documents": len(documents),
                "document_types": {},
                "languages": {},
                "total_citations": sum(doc["citation_count"] for doc in documents.values()),
                "total_cross_references": sum(doc["cross_references"] for doc in documents.values()),
                "reasoning_patterns": {
                    pattern: sum(doc["reasoning_patterns"].get(pattern, 0) for doc in documents.values())
                    for pattern in self.reasoning_patterns
                }
            }
            
            # Count document types and languages
            for doc in documents.values():
                doc_type = doc["type"]
                stats["document_types"][doc_type] = stats["document_types"].get(doc_type, 0) + 1
                
                lang = doc["language"]
                stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
            
            # Save statistics
            with open(os.path.join(self.output_dir, "processing_statistics.json"), 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Successfully processed {len(documents)} documents")
            logger.info(f"Results saved to {self.output_dir}")
            
            return documents
        else:
            logger.warning("No documents were successfully processed")
            return {}

def main():
    """Main function to parse command line arguments and process legal documents."""
    parser = argparse.ArgumentParser(description='Process South African legal documents for LLM training')
    
    parser.add_argument('--input', type=str, default=INPUT_DIR, 
                        help='Input directory containing legal documents')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, 
                        help='Output directory for processed data')
    parser.add_argument('--limit', type=int, help='Limit the number of files to process')
    parser.add_argument('--file', type=str, help='Process a single file')
    parser.add_argument('--citations', action='store_true', help='Process citations only')
    parser.add_argument('--structure', action='store_true', help='Analyze document structure only')
    parser.add_argument('--cross-refs', action='store_true', help='Map cross-references only')
    parser.add_argument('--hierarchy', action='store_true', help='Model legal hierarchy only')
    parser.add_argument('--temporal', action='store_true', help='Process temporal versioning only')
    parser.add_argument('--reasoning', action='store_true', help='Extract legal reasoning patterns only')
    
    args = parser.parse_args()
    
    processor = LegalDocumentProcessor(args.input, args.output)
    
    if args.file:
        # Process a single file
        if os.path.exists(args.file):
            result = processor.process_file(args.file)
            if result:
                doc_id, doc_info = result
                print(f"Processed {args.file}")
                print(json.dumps(doc_info, indent=2))
            else:
                print(f"Failed to process {args.file}")
        else:
            print(f"File not found: {args.file}")
    else:
        # Process a directory
        processor.process_directory(args.input, args.limit)

if __name__ == "__main__":
    main() 