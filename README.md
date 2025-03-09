# South African Companies Act Document Collection

This repository contains a collection of legal documents related to South African company law, including case law and legislation. 

## Project Structure

- `scrapers_output/`: Contains all downloaded legal documents (35GB+)
- `core_legislation/`: Key legislation documents organized by category
- `scripts/`: Utility scripts for working with the document collection
- `.venv/`: Python virtual environment

## Working with Large Document Collection

The document collection in `scrapers_output` is very large (35GB+) and contains over 113,000 files. To work efficiently with this collection while keeping Cursor running fast, we've implemented several optimizations:

### 1. Cursor Optimizations

- `.cursorignore`: Prevents Cursor from indexing the large `scrapers_output` directory
- `.cursor-settings/settings.json`: Optimized settings for better performance

### 2. Document Analysis Tool

We've created a document analysis script that allows you to check your legal documents without requiring Cursor to index the entire directory:

```bash
# Generate a report on document formats
python3 scripts/check_documents.py --report

# Search for documents matching criteria
python3 scripts/check_documents.py --search "companies act"

# Save report to JSON file
python3 scripts/check_documents.py --report --output report.json
```

### 3. Document Organization

To ensure the repository follows best practices for organization, we've created the `organize_documents.py` script:

```bash
# Check for missing core legislation
python3 scripts/organize_documents.py --check-missing

# Generate a full organization report
python3 scripts/organize_documents.py

# Save the report to a file
python3 scripts/organize_documents.py --report organization_report.json
```

#### Organization Best Practices
For maintaining this legal document repository, we follow these best practices:

1. **Hierarchical Structure**:
   - Core legislation is organized by category (commercial, financial, regulatory)
   - Court judgments are organized by court code
   - Regulatory materials are organized by regulatory body

2. **Naming Conventions**:
   - Legislation: `[Act Name] [Number] of [Year].pdf`
   - Court judgments: `[Court Code]_[Case Number]_[Year]_[Short Description].pdf`
   - Regulatory materials: `[Regulator]_[Type]_[Date]_[Description].pdf`

3. **Core Legislation**:
   - Essential acts are maintained in the `core_legislation` directory
   - Each act is categorized by legal domain
   - Full text versions are provided in PDF format
   - Key legislation is regularly checked for updates

4. **Documentation**:
   - Each directory contains a README with summary information
   - Document patterns and organization schemas are documented
   - Search and navigation tools are maintained and updated

### 4. Web-Based Document Explorer

A web-based explorer for browsing and searching the document collection:

```bash
# Install requirements
pip install -r scripts/explorer_requirements.txt

# Run the explorer on port 8888
python3 scripts/document_explorer.py --port 8888
```

You can then access the explorer at http://localhost:8888/ to browse all documents, filter by court or category, and search for specific documents.

### Terminal Commands for Checking Documents

You can also use these terminal commands to check your documents directly:

```bash
# Count PDFs in the directory
find scrapers_output/ -name "*.pdf" | wc -l

# Search for specific files
find scrapers_output/ -name "*companies*act*" -type f

# Search inside text files
grep -r "companies act" scrapers_output/
```

### Repository Maintenance

To help maintain the organization of this repository, we've created several utility scripts:

```bash
# Clean up and standardize legislation filenames
python3 scripts/cleanup_legislation_files.py

# Generate a legislation index in markdown format
python3 scripts/generate_legislation_index.py

# Download missing core legislation
python3 scripts/download_missing_legislation.py

# Check organization status
python3 scripts/organize_documents.py
```

#### Naming Conventions

All legislation follows these naming conventions:
- Act: `[Act Name] No. [Number] of [Year].pdf`
- Amendment: `[Act Name] Amendment Act [Number] [Year].pdf`
- Consolidated: `[Act Name] [Number] [Year] Consolidated.pdf`

#### Adding New Legislation

When adding new legislation:

1. Place it in the appropriate category directory under `scrapers_output/core_legislation/`
2. Run the cleanup script to ensure consistent naming
3. Regenerate the legislation index

#### Keeping Up with Changes

South African legislation is regularly amended. To keep the repository up to date:

1. Check for updates on the government websites listed in the sources section
2. Download updated versions of legislation
3. Run the cleanup and organization scripts

## Collection Statistics

The document collection contains approximately 113,952 documents (34.92 GB) across various South African courts, with the following breakdown:

| File Type | Count |
|-----------|-------|
| HTML      | 44,559|
| PDF       | 34,492|
| RTF       | 30,762|
| DOC       | 3,795 |
| **Total** | **113,608** |

## Preparing Data for Legal BERT Training

The SAFLII document collection provides an excellent foundation for training a Legal BERT model specialized in South African law. The collection includes:

### 1. Comprehensive Coverage

- **Case Law**: Judgments from all major courts including the Constitutional Court, Supreme Court of Appeal, High Courts, and specialized courts
- **Time Span**: Documents spanning from the 1940s to 2024, providing historical context and evolution of legal principles
- **Subject Matter**: Wide variety of legal topics including commercial, constitutional, labor, and administrative law

### 2. Document Format and Processing

The documents are available in various formats (HTML, PDF, RTF, DOC) and require processing before they can be used for BERT training:

1. **Text Extraction**: First, plain text needs to be extracted from different file formats
   - HTML files can be processed using BeautifulSoup or similar libraries
   - PDF files require extraction tools like PyPDF2 or pdfminer
   - RTF and DOC files need specialized libraries for text extraction

2. **Text Cleaning**:
   - Remove headers, footers, and page numbers
   - Standardize formatting (spacing, line breaks)
   - Handle legal citations and references consistently
   - Clean up special characters and formatting artifacts

3. **Sentence Segmentation**:
   - Split documents into sentences
   - Preserve paragraph structure where relevant
   - Handle lists and indented sections properly

4. **BERT-Ready Format**:
   - Convert to BERT's expected input format
   - Create training, validation, and test splits
   - Prepare for masked language model (MLM) pre-training

### 3. Current Processing Status

1. **Directory Structure**: A `.gitignore` entry for `bert_data/` suggests this directory is intended for the processed BERT-ready data
2. **Processing Scripts**: Some processing utilities appear to be available in the repository:
   - Text extraction utilities in various scripts
   - Document structure analysis in the explorer interface
   - Some functionality for handling specific document types

### 4. Next Steps for BERT Training

To prepare this data for Legal BERT training, the following steps are recommended:

1. **Create a Processing Pipeline**:
   ```bash
   # Install required dependencies
   pip install transformers datasets pandas tqdm nltk beautifulsoup4 pdfminer.six python-docx
   
   # Create directory for BERT data
   mkdir -p bert_data/{raw,processed,final}
   ```

2. **Data Processing Workflow**:
   - Extract text from all document formats
   - Clean and normalize the text
   - Segment into appropriate units for BERT
   - Create training datasets

3. **BERT Pre-training Configuration**:
   - Use HuggingFace Transformers library
   - Configure for South African legal domain
   - Train on masked language modeling objective

4. **Fine-tuning Options**:
   - Case outcome prediction
   - Legal citation recommendation
   - Document classification by area of law
   - Legal entity recognition

### 5. South African Legal Domain Considerations

When training a Legal BERT model for South African law, several unique characteristics should be considered:

1. **Legal System Context**:
   - South Africa has a mixed legal system combining Roman-Dutch civil law, English common law, and indigenous customary law
   - Post-apartheid constitutional jurisprudence forms a significant part of modern case law
   - International law is incorporated through Section 39 of the Constitution

2. **Linguistic Considerations**:
   - Legal documents contain specialized terms from multiple legal traditions
   - Some documents may include terms from South Africa's 11 official languages
   - Unique legal terminology for South African statutory bodies and procedures

3. **Citation Patterns**:
   - South African legal citations have specific formats (e.g., "2023 (2) SA 123 (CC)")
   - References to specific acts and regulations follow unique patterns
   - Understanding these patterns can improve the model's performance on legal tasks

4. **Document Structure**:
   - Judgments follow specific structural patterns (introduction, facts, legal issues, analysis, conclusion)
   - Legislative documents have standardized formats with numbered sections and subsections
   - These structures can be leveraged for better text segmentation and understanding

## Example BERT Training Configuration

Below is a starting configuration for pre-training a South African Legal BERT model:

```python
from transformers import BertConfig, BertForMaskedLM, DataCollatorForLanguageModeling
from transformers import Trainer, TrainingArguments

# South African Legal BERT configuration
config = BertConfig(
    vocab_size=32000,  # Adjusted for legal vocabulary
    hidden_size=768,
    num_hidden_layers=12,
    num_attention_heads=12,
    intermediate_size=3072,
)

# Create model
model = BertForMaskedLM(config)

# Training arguments
training_args = TrainingArguments(
    output_dir="./sa-legal-bert",
    overwrite_output_dir=True,
    num_train_epochs=5,
    per_device_train_batch_size=8,
    save_steps=10000,
    save_total_limit=2,
    prediction_loss_only=True,
    fp16=True,  # Mixed precision training
)

# Data collator for masked language modeling
data_collator = DataCollatorForLanguageModeling(
    tokenizer=tokenizer,
    mlm=True,
    mlm_probability=0.15
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    data_collator=data_collator,
    train_dataset=dataset,
)

# Start training
trainer.train()
```

## Core Legislation

Key legislation documents are available in the `core_legislation` directory, organized by category:

### Commercial Law

- Competition Act 89 of 1998
- Consumer Protection Act 68 of 2008
- National Credit Act 34 of 2005

### Financial Law

- Banks Act 94 of 1990 (with amendments)
- Financial Advisory and Intermediary Services Act 37 of 2002
- Financial Intelligence Centre Act 38 of 2001
- Financial Sector Regulation Act 9 of 2017
- Financial Sector Laws Amendment Act 23 of 2021
- Financial Matters Amendment Act 18 of 2019

### Regulatory Law

- Broad-Based Black Economic Empowerment Act 53 of 2003
- Promotion of Administrative Justice Act 3 of 2000
- Protection of Personal Information Act 4 of 2013

## Using the Document Explorer for BERT Data Preparation

The web-based document explorer can be a valuable tool for preparing data for BERT training:

1. **Document Selection**:
   - Use the filtering capabilities to select specific document sets by court, year, or category
   - Create balanced training datasets across different legal domains
   - Identify high-quality documents for initial model training

2. **Data Inspection**:
   - Examine document structures and formats to inform processing strategies
   - Identify inconsistencies or quality issues that need addressing
   - View documents directly in the browser to understand their content

3. **Metadata Extraction**:
   - Extract court information, dates, and document types for metadata enrichment
   - Create structured datasets with appropriate metadata for training
   - Use document metadata for specialized training tasks

4. **Corpus Analysis**:
   - Analyze document distributions across courts and years
   - Identify potential biases in the training data
   - Ensure comprehensive coverage of legal domains

To leverage the document explorer for BERT preparation:

```bash
# Start the document explorer
source .venv-explorer/bin/activate
python3 scripts/document_explorer.py --port 8890

# In another terminal, run the document analysis script
python3 scripts/check_documents.py --save

# This creates a comprehensive JSON report you can use for data selection
```

## Building a Comprehensive South African Legal LLM

We are tracking our progress in building a comprehensive dataset for a South African legal language model. The detailed checklist is maintained in a separate file for easy reference:

### [📋 SA Legal LLM Dataset Checklist](./SA_LEGAL_LLM_CHECKLIST.md)

This checklist tracks all materials needed to build a state-of-the-art legal LLM for South African law, including:
- Legislative framework (constitution, acts, regulations)
- Case law from all courts
- Secondary legal sources (textbooks, journals)
- Procedural materials
- Historical and contextual materials
- Technical processing requirements

**Quick reference:** When discussing this project, you can refer to "the checklist" or "SA Legal LLM Checklist" to reference this tracking document.

**Current progress:** We've collected 9/81 essential resources (11%), primarily focused on core commercial, financial and regulatory legislation.

**Opening the checklist:**
```bash
# Open the checklist directly in your preferred editor
./scripts/open_checklist.sh

# Update the checklist automatically based on detected files
python3 scripts/update_llm_checklist.py

# Access the checklist through a web browser (on port 8742)
python3 scripts/serve_checklist.py
```

**Accessing via URL:**
- Local web interface: http://localhost:8742/checklist
- To access remotely: Push to GitHub and use https://github.com/yourusername/repo-name/blob/main/SA_LEGAL_LLM_CHECKLIST.md

## Sources for Legal Documents

- South African Legal Information Institute (SAFLII)
- Government Gazette (https://www.gov.za/documents/government-gazette)
- Departmental websites:
  - Competition Commission (https://www.compcom.co.za/)
  - National Credit Regulator (http://www.ncr.org.za/)
  - Financial Sector Conduct Authority (https://www.fsca.co.za/)
  - Information Regulator (https://www.justice.gov.za/inforeg/)
