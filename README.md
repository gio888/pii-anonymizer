# PII Anonymizer

A comprehensive Python tool for detecting, anonymizing, and restoring personally identifiable information (PII) in various document types. Features a modern web interface with drag-and-drop file upload.

## Features

- 🎨 **Modern Web Interface**: Drag-and-drop file upload with real-time processing
- 🔍 **Advanced PII Detection**:
  - Regex patterns for emails, phones, SSNs, credit cards, IPs, URLs, etc.
  - spaCy NER for detecting people, companies, products, and locations
  - Currency and number detection
  - Abbreviation detection (all-caps: IBM, BXC; alphanumeric: 3M, F5; stock tickers: NYSE: ABBV)
- 🎭 **Semantic Aliases**: Generate human-readable placeholders like ACME_CORP, JOHN_DOE instead of random IDs
- 📄 **Multiple Document Formats**:
  - Plain text files (.txt, .md, .csv, .tsv)
  - PDF documents (exported as markdown)
  - Microsoft Word (.docx)
  - Microsoft Excel (.xlsx)
  - Google Docs
  - Google Sheets
- 🔄 **Reversible Mapping**: Restore anonymized documents back to original form
- 📦 **Batch Processing**: Handle multiple documents at once
- 💻 **Dual Interface**: Web UI for ease of use, CLI for automation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pii-anonymizer.git
   cd pii-anonymizer
   ```

2. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Download spaCy language model (required for NER):
   ```bash
   python3 -m spacy download en_core_web_md
   ```

## Usage

### Web Interface (Recommended)

The easiest way to use PII Anonymizer is through the web interface:

1. Start the web server:
   ```bash
   python3 run_webapp.py
   ```

2. Open your browser and go to: **http://localhost:5000**

3. Drag and drop your document or click to browse

4. Download the anonymized document and mapping files

**Features:**
- Drag-and-drop file upload
- Real-time processing with progress bar
- Download anonymized documents in clean formats
- Download mapping files in both JSON and CSV formats
- Processing statistics displayed in the UI

### Command-Line Interface

For automation and scripting, use the CLI:

**Anonymize a document:**
```bash
python3 src/pii_anonymizer_cli.py anonymize -i document.txt -o document_anon.txt -m mapping.json
```

**Restore an anonymized document:**
```bash
python3 src/pii_anonymizer_cli.py restore -i document_anon.txt -o document_restored.txt -m mapping.json
```

**Batch processing:**
```bash
python3 src/pii_anonymizer_cli.py anonymize -i input_folder -o output_folder -m mapping.json -b
```

**Custom PII patterns:**
```bash
python3 src/pii_anonymizer_cli.py anonymize -i document.txt -o output.txt -m mapping.json -p patterns.json
```

**Google Docs/Sheets (requires credentials):**
```bash
python3 src/pii_anonymizer_cli.py anonymize -i "https://docs.google.com/document/d/1234..." -o gdoc_anon.txt -m mapping.json -g credentials.json
```

## Setting Up Google API Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Docs API and Google Sheets API
4. Go to "Credentials" and create OAuth 2.0 Client IDs
5. Download the JSON credentials file
6. Provide the path to this file when using the `-g` option

## What Gets Detected

The PII Anonymizer detects the following types of sensitive information:

**Via Regex Patterns:**
- Email addresses
- Phone numbers (US and international formats)
- Social Security Numbers (SSN)
- Credit card numbers
- IP addresses
- URLs
- Physical addresses
- Dates
- Currency amounts (e.g., $1,250.00, €99.99)
- Large numbers (4+ digits)

**Via spaCy NER (Named Entity Recognition):**
- Person names
- Company/organization names
- Product names
- Geographic locations

## Output Formats

Different input formats produce different outputs:

| Input Format | Anonymized Output | Notes |
|-------------|-------------------|-------|
| .txt, .md, .csv, .tsv | Same format | Preserves original format |
| .pdf | .md (Markdown) | Extracts text from PDF and outputs as clean markdown |
| .docx | .txt (Plain text) | Extracts text from Word document |
| .xlsx | .txt (Plain text) | Extracts all sheets with tab-separated values |

**Mapping Files:**
- Always outputs both `mapping.json` and `mapping.csv`
- JSON for programmatic use
- CSV for easy human review in spreadsheet applications

## Semantic Aliases

Unlike traditional anonymization that uses random IDs, this tool generates meaningful placeholders:

```
Original → Anonymized
----------------------------------
john.smith@company.com → <EMAIL_a1b2c3d4>
Microsoft Corporation → ACME_CORP
Jane Doe → JANE_DOE
CloudSync Pro → PROPLATFORM
192.168.1.1 → <IP_ADDRESS_8e90b6d6>
$1,250.00 → <CURRENCY_af64ebd2>
```

This makes anonymized documents easier to read and understand while maintaining privacy.

## Configuration

Add custom PII patterns via `patterns.json`:

```json
{
  "PASSPORT": "\\b[A-Z]{2}[0-9]{7}\\b",
  "EMPLOYEE_ID": "\\bEMP-[0-9]{5}\\b",
  "CUSTOM_ID": "\\bID-[A-Z]{2}-[0-9]{6}\\b"
}
```

## Project Structure

```
pii-anonymizer/
├── src/
│   ├── pii_anonymizer/
│   │   └── document_processor.py    # Core PIIManager and base classes
│   ├── handlers/
│   │   ├── text_pdf_handlers.py     # Text and PDF handlers
│   │   ├── office_handlers.py       # DOCX and XLSX handlers
│   │   └── google_handlers.py       # Google Docs/Sheets handlers
│   ├── utils/
│   │   └── alias_generator.py       # Semantic alias generator
│   ├── web_app.py                   # Flask web application
│   └── pii_anonymizer_cli.py        # Command-line interface
├── templates/
│   └── index.html                   # Web UI template
├── run_webapp.py                     # Web app launcher
├── requirements.txt
└── README.md
```

## Limitations

- PDF anonymization currently works best with text-based PDFs. Scanned PDFs may require additional OCR processing.
- Google Docs/Sheets processing requires appropriate API credentials and internet access.
- Very large files may consume significant memory during processing.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.