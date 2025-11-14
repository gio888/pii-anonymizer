# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PII Anonymizer is a Python tool for detecting, anonymizing, and restoring personally identifiable information (PII) in various document types. The primary use case is processing sensitive documents for use with LLMs while maintaining privacy compliance and the ability to restore original content.

**Key Features:**
- Modern web interface with drag-and-drop file upload
- Support for TXT, MD, CSV, TSV, PDF, DOCX, XLSX
- Semantic aliases (ACME_CORP, JOHN_DOE) instead of random IDs
- spaCy NER for detecting people, companies, products
- Regex patterns for emails, phones, IPs, currency, etc.
- Advanced abbreviation detection (all-caps, alphanumeric, stock tickers)

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Install spaCy language model (required for NER-based detection)
python3 -m spacy download en_core_web_md
```

### Running the Web Application
```bash
# Start the web server (recommended for most users)
python3 run_webapp.py

# Access at http://localhost:5000
# Features: drag-and-drop upload, real-time processing, download anonymized files and mappings
```

### Running the CLI
```bash
# Anonymize a single file
python3 src/pii_anonymizer_cli.py anonymize -i document.txt -o output/document_anon.txt -m output/mapping.json

# Restore an anonymized file
python3 src/pii_anonymizer_cli.py restore -i output/document_anon.txt -o output/document_restored.txt -m output/mapping.json

# Batch process multiple files
python3 src/pii_anonymizer_cli.py anonymize -i input_folder -o output_folder -m output/mapping.json -b

# Use custom PII patterns
python3 src/pii_anonymizer_cli.py anonymize -i document.txt -o output/document_anon.txt -m output/mapping.json -p patterns.json

# Enable verbose logging
python3 src/pii_anonymizer_cli.py anonymize -i document.txt -o output/document_anon.txt -m output/mapping.json -v
```

### Testing
```bash
# Run all tests using unittest
python3 -m unittest discover tests/

# Run a specific test file
python3 -m unittest tests/test_document_processor.py

# Run a specific test class
python3 -m unittest tests.test_document_processor.TestDocumentProcessor

# Run a specific test method
python3 -m unittest tests.test_document_processor.TestDocumentProcessor.test_anonymize_document
```

## Architecture

### Core Components

**PIIManager** (`src/pii_anonymizer/document_processor.py:56-221`)
- Central class for PII detection, anonymization, and restoration
- Maintains bidirectional mapping between original PII and placeholders
- Uses regex patterns to detect PII types (emails, phones, SSNs, etc.)
- Generates unique placeholders in format `<TYPE_uuid>` (e.g., `<EMAIL_a1b2c3d4>`)
- Key methods:
  - `detect_pii_in_text()`: Identifies PII in text using configured patterns
  - `anonymize_text()`: Replaces PII with placeholders
  - `restore_text()`: Replaces placeholders with original PII
  - `save_mapping()` / `load_mapping()`: Persists mapping to JSON

**PiiConfig** (`src/pii_anonymizer/document_processor.py:16-53`)
- Configuration container for PII detection patterns
- Defines regex patterns for various PII types
- Supports custom patterns via dictionary extension
- Includes entity type mapping for normalizing NER results

**DocumentHandler** (`src/pii_anonymizer/document_processor.py:224-285`)
- Abstract base class defining the interface for all document handlers
- Subclasses implement format-specific extraction and processing
- Must implement: `can_handle()`, `extract_text()`, `anonymize()`, `restore()`

**DocumentProcessor** (`src/pii_anonymizer/document_processor.py:288-447`)
- Orchestrates the anonymization/restoration workflow
- Manages handler registration and selection
- Routes documents to appropriate handlers based on file type
- Supports batch processing across directories

### Document Handlers

**TextDocumentHandler** (`src/handlers/text_pdf_handlers.py:13-61`)
- Handles plain text formats: .txt, .text, .md, .csv, .tsv
- Uses UTF-8 encoding with fallback to latin-1
- Directly reads and writes text content

**PDFDocumentHandler** (`src/handlers/text_pdf_handlers.py:64-250`)
- Handles PDF documents
- Uses pdfplumber (preferred) or PyPDF2 (fallback) for text extraction
- Creates both `.txt` and `.pdf` outputs during anonymization
- Uses reportlab to generate PDFs with anonymized/restored text
- Note: Works best with text-based PDFs, not scanned documents

**GoogleDocsHandler / GoogleSheetsHandler** (`src/handlers/google_handlers.py`)
- Handle Google Docs and Google Sheets via Google API
- Require OAuth credentials for authentication
- Support both reading from and writing to Google Drive

### Data Flow

1. **Anonymization Flow:**
   - User provides input document(s) and specifies output location
   - DocumentProcessor selects appropriate handler based on file extension
   - Handler extracts text content
   - PIIManager detects PII using regex patterns
   - PIIManager generates unique placeholders for each PII instance
   - Handler writes anonymized content to output
   - PIIManager saves mapping to JSON file

2. **Restoration Flow:**
   - User provides anonymized document(s) and mapping file
   - DocumentProcessor loads mapping from JSON
   - Handler reads anonymized content
   - PIIManager replaces placeholders with original PII from mapping
   - Handler writes restored content to output

3. **Mapping File Format:**
   ```json
   {
     "pii_to_placeholder": {
       "john@example.com": "<EMAIL_a1b2c3d4>",
       "555-1234": "<PHONE_e5f6g7h8>"
     },
     "placeholder_to_pii": {
       "<EMAIL_a1b2c3d4>": "john@example.com",
       "<PHONE_e5f6g7h8>": "555-1234"
     }
   }
   ```

## Custom PII Patterns

The `patterns.json` file contains additional regex patterns for specialized PII types. To add custom patterns:

1. Create/edit `patterns.json` with new patterns:
   ```json
   {
     "PASSPORT": "\\b[A-Z]{2}[0-9]{7}\\b",
     "CUSTOM_ID": "\\bID-[A-Z]{2}-[0-9]{6}\\b"
   }
   ```

2. Pass to CLI with `-p` flag:
   ```bash
   python3 src/pii_anonymizer_cli.py anonymize -i doc.txt -o out.txt -m map.json -p patterns.json
   ```

## Important Implementation Notes

### Placeholder Generation
- Placeholders use format `<TYPE_UUID>` where UUID is first 8 chars of uuid4().hex
- Same PII value always maps to same placeholder within a session
- Placeholders are designed to be LLM-friendly and clearly distinguishable

### Text Replacement Strategy
- Detections are sorted by position in reverse order before replacement
- This avoids offset issues when replacing multiple instances
- Both anonymization and restoration use this strategy

### Handler Selection
- Handlers are checked in registration order
- First handler that returns `True` from `can_handle()` is selected
- Register more specific handlers before generic ones

### Batch Processing
- All files in input directory are processed sequentially
- Unknown file types are added to 'failed' list
- Mapping file accumulates all PII across all documents
- Results dictionary tracks successful and failed files

### PDF Limitations
- PDF anonymization extracts text and creates new PDF with anonymized content
- Original formatting, images, and complex layouts are not preserved
- Scanned PDFs require external OCR processing before anonymization
- Restoration creates new PDF from text, not overlay on original

### Abbreviation Detection (document_processor.py:171-236)
- Three specialized patterns detect abbreviations that spaCy NER might miss:
  1. **All-caps abbreviations** (`r'\b[A-Z]{2,5}\b'`): Detects BXC, IBM, FTSE, GE, etc.
  2. **Alphanumeric abbreviations** (`r'\b(?:\d+[A-Z]+|[A-Z]+\d+)\b'`): Detects 3M, F5, 401K, etc.
  3. **Stock ticker format** (`r'\b(?:NYSE|NASDAQ|FTSE|S&P|DOW)(?::\s*|\s+)([A-Z]{1,5}|\d+)\b'`): Detects NYSE: ABBV, NASDAQ: NEON, etc.
- **Context-aware filtering** prevents false positives:
  - Blacklist excludes common words: OK, AM, PM, OR, IF, IS, AS, AT, WE, NO
  - Ambiguous words (US, IT, AI) only detected if near organization context (Inc, Corp, capitalized words)
- All abbreviations classified as ORGANIZATION type
- Runs after spaCy NER with deduplication via `detected_spans` set
- **Impact**: Improved real-world detection from 78% to 88% (+10 percentage points)

## Security Considerations

- Mapping files contain original PII in plaintext - store securely
- No PII is transmitted to external services during processing
- Optional encryption for mapping files can be implemented by wrapping save/load methods
- Separation of anonymized content from mapping files is critical for privacy

## Project Structure

```
pii-anonymizer/
├── src/
│   ├── pii_anonymizer/
│   │   ├── __init__.py
│   │   └── document_processor.py    # Core PIIManager and base classes
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── text_pdf_handlers.py     # Text and PDF handlers
│   │   └── google_handlers.py       # Google Docs/Sheets handlers
│   ├── utils/
│   │   └── __init__.py
│   └── pii_anonymizer_cli.py        # Command-line interface
├── tests/
│   ├── test_pii_manager.py
│   ├── test_document_processor.py
│   └── test_text_handler.py
├── examples/
│   ├── anonymize_text_example.py
│   ├── restore_text_example.py
│   └── batch_processing_example.py
├── patterns.json                     # Custom PII detection patterns
├── requirements.txt
└── README.md
```

## Dependencies

Core:
- spacy >= 3.6.0 (NER-based detection, requires language model)
- PyPDF2 >= 3.0.0 (PDF reading)
- pdfplumber >= 0.10.0 (Improved PDF text extraction)
- reportlab >= 4.0.0 (PDF generation)

Optional:
- google-api-python-client >= 2.100.0 (Google Docs/Sheets)
- google-auth-httplib2 >= 0.1.0
- google-auth-oauthlib >= 1.1.0

Utilities:
- tqdm >= 4.66.0 (Progress bars)

## Extending the System

### Adding a New Document Handler

1. Create a new handler class inheriting from `DocumentHandler`
2. Implement all abstract methods: `can_handle()`, `extract_text()`, `anonymize()`, `restore()`
3. Register the handler in `pii_anonymizer_cli.py`'s `setup_processor()` function

Example:
```python
class WordDocumentHandler(DocumentHandler):
    def can_handle(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.doc', '.docx'))

    def extract_text(self, file_path: str) -> str:
        # Implementation for Word document extraction
        pass

    def anonymize(self, input_path: str, output_path: str) -> None:
        text = self.extract_text(input_path)
        anonymized = self.pii_manager.anonymize_text(text)
        # Write to Word format
        pass

    def restore(self, anonymized_path: str, output_path: str) -> None:
        # Implementation for restoration
        pass
```

### Adding New PII Types

1. Add regex pattern to `PiiConfig.patterns` dictionary
2. Or provide via `patterns.json` file
3. Pattern must capture complete PII value in match group 0
4. Use descriptive uppercase name for PII type (e.g., 'PASSPORT', 'DRIVER_LICENSE')
