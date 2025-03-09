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

### 2. Fixing Cursor Crashes

If you experience Cursor crashes while working with this large repository, you can use our automated fix script:

```bash
# Make the script executable if needed
chmod +x scripts/fix_cursor_crashes.sh

# Run the fix script
./scripts/fix_cursor_crashes.sh
```

This script will:
- Clean temporary files and logs that might cause memory issues
- Stop background processes that could be consuming resources
- Clear Cursor application caches
- Ensure your `.cursorignore` and settings files are properly configured
- Set performance mode for better handling of large repositories

You can also manually clean temporary files:

```bash
# Clean only temporary files
python3 scripts/clean_workspace.py --temp

# Clean only Cursor cache
python3 scripts/clean_workspace.py --cache

# Clean everything
python3 scripts/clean_workspace.py --all
```

### 3. Document Analysis Tool

We've created a document analysis script that allows you to check your legal documents without requiring Cursor to index the entire directory:

```bash
# Generate a report on document formats
python3 scripts/check_documents.py --report

# Search for documents matching criteria
python3 scripts/check_documents.py --search "companies act"

# Save report to JSON file
python3 scripts/check_documents.py --report --output report.json
```

### 4. Document Organization

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

### 5. Web-Based Document Explorer

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

# South African Legal LLM Dataset

A comprehensive collection of South African legal documents for training or fine-tuning Legal Large Language Models (LLMs).

## Project Status: 85% Complete

The South African Legal LLM Dataset project is currently **85% complete** (61 out of 72 items). We have made significant progress in collecting and processing South African legal documents across various categories.

### Completion by Category:

- **Legislative Framework**: 93% complete (27/29 items)
  - Constitution of South Africa ✅
  - Companies Act and Regulations ✅
  - All Principal Acts ✅
  - Amended legislation ✅
  - Most subordinate legislation ✅

- **Case Law**: 73% complete (8/11 items)
  - Constitutional Court judgments ✅
  - Supreme Court of Appeal judgments ✅
  - High Court judgments ✅
  - Companies Tribunal decisions ✅
  - CIPC practice notes ✅

- **Secondary Legal Sources**: 60% complete (9/15 items)
  - Banking and finance law materials ✅
  - International law ratified by South Africa ✅
  - Law Journal articles ✅
  - Environmental law compilations ✅
  - Legal dictionaries and glossaries ✅
  - Tax law commentaries and guides ✅
  - Intellectual property law compilations ✅

- **Procedural Materials**: 100% complete (5/5 items)
  - Rules of Court ✅
  - Practice directives ✅
  - Legal ethics guidelines ✅
  - Forms and precedents ✅
  - Law Society guidelines ✅

- **Historical and Contextual Materials**: 100% complete (5/5 items)
  - Roman-Dutch law sources ✅
  - Historical legislation ✅
  - Legal development commentaries ✅
  - Comparative law studies ✅
  - Legal anthropology studies ✅

- **Technical Processing Requirements**: 100% complete (7/7 items)
  - Citation pattern recognition ✅
  - Legal document structure analysis ✅
  - Cross-reference mapping ✅
  - Legal hierarchy modeling ✅
  - Temporal versioning ✅
  - Multi-language processing ✅
  - Legal reasoning pattern extraction ✅

## Dataset Organization

The legal documents are organized in the following structure:

```
├── core_legislation/
│   ├── constitution/
│   ├── acts/
│   ├── regulations/
│   └── notices/
├── case_law/
│   ├── constitutional_court/
│   ├── supreme_court_appeal/
│   ├── high_courts/
│   └── specialized_courts/
├── procedural_materials/
│   ├── rules_of_court/
│   └── practice_directives/
├── secondary_sources/
│   ├── international_treaties/
│   └── banking_finance/
├── historical_materials/
│   └── parliamentary_debates/
└── processed_output/
    ├── citations/
    ├── structure/
    ├── cross_references/
    ├── hierarchy/
    ├── temporal/
    ├── multilingual/
    └── reasoning/
```

## Freely Available Resources

We have identified several freely available resources for South African legal documents:

1. **SAFLII (Southern African Legal Information Institute)**: [https://www.saflii.org/](https://www.saflii.org/)
   - Comprehensive database of case law, legislation and legal materials
   - Includes judgments from all major courts

2. **Gazettes.Africa**: [https://gazettes.africa/](https://gazettes.africa/)
   - Collection of government gazettes from South Africa and other African countries
   - Searchable database of official publications

3. **OpenGazettes**: [https://opengazettes.org.za/](https://opengazettes.org.za/)
   - Open repository of South African government gazettes

4. **South African Government Website**: [https://www.gov.za/documents/](https://www.gov.za/documents/)
   - Official repository of government publications
   - Includes Acts, Bills, and Policy documents

5. **Constitutional Court Website**: [https://www.concourt.org.za/](https://www.concourt.org.za/)
   - Judgments from the Constitutional Court
   - Constitutional Court Bulletin

6. **Parliamentary Monitoring Group**: [https://pmg.org.za/](https://pmg.org.za/)
   - Parliamentary committee reports
   - Bill tracking and legislative processes

7. **South African Reserve Bank**: [https://www.resbank.co.za/](https://www.resbank.co.za/)
   - Banking legislation and regulations
   - Financial sector laws and frameworks

## Technical Processing Tools

The project now includes a comprehensive set of technical processing tools for legal documents, implemented in the `scripts/process_legal_documents.py` script. These tools prepare the collected legal documents for effective use in training or fine-tuning Legal LLMs:

1. **Citation Pattern Recognition**: Automatically identifies and extracts South African legal citations (cases, legislation, sections) following standard citation formats.

2. **Document Structure Analysis**: Parses legal documents to identify headings, sections, subsections, definitions, and other structural elements common in legal texts.

3. **Cross-Reference Mapping**: Creates connections between legal documents based on their citations, building a network of legal references.

4. **Legal Hierarchy Modeling**: Models the hierarchical relationship between legal documents (constitution → acts → regulations → cases) using a directed graph structure.

5. **Temporal Versioning**: Tracks and organizes different versions of legislation over time, allowing analysis of legal evolution.

6. **Multi-language Processing**: Supports all 11 official South African languages with language detection capabilities.

7. **Legal Reasoning Pattern Extraction**: Identifies patterns of legal reasoning in judgments, including ratio decidendi, obiter dicta, statutory interpretation, constitutional reasoning, and precedent application.

## Using the Dataset

### Docker Setup for Document Processing

To avoid dependency issues, we've created a Docker environment for document processing. This ensures consistent processing across different environments.

#### Using Docker Compose

The easiest way to use the processing tools is with Docker Compose:

```bash
# Build the Docker images
docker-compose build

# Process documents
docker-compose run legal-processor --input /app/scrapers_output --output /app/processed_output

# Start the checklist server
docker-compose up checklist-server
```

#### Using the Helper Script

We've also created a helper script to make processing even easier:

```bash
# Make the script executable (if needed)
chmod +x scripts/run_processing.sh

# Process all documents
./scripts/run_processing.sh

# Process only citations from a specific file
./scripts/run_processing.sh --file ./scrapers_output/core_legislation/acts/Companies_Act_71_of_2008.pdf --citations

# Limit processing to 100 files
./scripts/run_processing.sh --limit 100

# See all available options
./scripts/run_processing.sh --help
```

### Checklist Tool

We provide a checklist tool to track progress and ensure comprehensive coverage. Run the checklist server:

```bash
python3 scripts/update_llm_checklist.py --serve
```

Then open http://localhost:8742/checklist in your browser to view progress.

### Downloading Legal Materials

To download missing legal materials, use the downloader script:

```bash
python3 scripts/download_missing_legislation.py --help
```

Available options include downloading specific types of legislation (acts, regulations, case law, etc.) and bypassing SSL verification for problematic websites.

## Preparing Data for Training a Legal BERT Model

For training a specialized Legal BERT model for South African law, the following steps are recommended:

1. **Preprocessing**: Clean and normalize all legal texts using the processing tools
2. **Tokenization**: Build a domain-specific tokenizer with legal terminology
3. **Model Architecture**: Start with a pretrained BERT model and adapt to legal domain
4. **Training Strategy**: Use masked language modeling on the legal corpus
5. **Evaluation**: Validate on legal tasks like citation prediction and case outcome prediction

## South African Legal Domain Considerations

The South African legal system has unique features that should be considered:

1. **Mixed Legal System**: Combination of Roman-Dutch civil law and English common law
2. **Constitutional Supremacy**: Constitution is the highest law
3. **Multilingual Context**: 11 official languages with legal texts primarily in English and Afrikaans
4. **Post-Apartheid Jurisprudence**: Emphasis on human rights and transformative justice
5. **Indigenous Law Recognition**: Traditional African customary law as part of the legal system

## Legal Usage Considerations

The materials in this dataset are primarily public domain government documents intended for research, education, and legal practice. For commercial applications, consult a legal expert regarding copyright and terms of use.

## Contributors

- [Add Your Name Here]

## License

This collection is provided for research and educational purposes. Individual documents may have different usage terms depending on their source.
