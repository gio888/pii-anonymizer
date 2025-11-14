# Quick Start Guide

## Installation (5 minutes)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download spaCy model:**
   ```bash
   python3 -m spacy download en_core_web_md
   ```

## Using the Web Interface (Easiest!)

1. **Start the server:**
   ```bash
   python3 run_webapp.py
   ```

2. **Open your browser:**
   - Go to: http://localhost:5000

3. **Use the app:**
   - Drag and drop your file (or click to browse)
   - Wait for processing to complete
   - Download your anonymized file
   - Download the mapping file (keep it secure!)

## Supported File Types

✅ Text files: `.txt`, `.md`, `.csv`, `.tsv`
✅ PDFs: `.pdf` (outputs as `.md`)
✅ Word documents: `.docx` (outputs as `.txt`)
✅ Excel spreadsheets: `.xlsx` (outputs as `.txt`)

## What Gets Anonymized?

The tool automatically detects and redacts:

- **Contact Information**: emails, phone numbers, addresses
- **Financial Data**: credit cards, SSNs, currency amounts
- **Technical Info**: IP addresses, URLs
- **Named Entities**: people names, company names, product names
- **Numbers**: large numeric values (4+ digits)

## Example

**Original:**
```
John Smith from Microsoft contacted jane.doe@company.com
at (555) 123-4567. The price is $1,250.00.
```

**Anonymized:**
```
MICHAEL_WILLIAMS from ACME_CORP contacted <EMAIL_cd02f5cd>
at <PHONE_fe2dc40a>. The price is <CURRENCY_af64ebd2>.
```

## Important Security Notes

⚠️ **Keep mapping files secure!** They contain the original PII in plaintext.

✅ **All processing is local** - no data is sent to external services.

✅ **Download both files:**
- The anonymized document (for sharing with LLMs)
- The mapping file (for restoration later)

## Next Steps

- **Restore a file**: Use the CLI with `restore` command
- **Batch processing**: Use the CLI with `-b` flag
- **Custom patterns**: Create a `patterns.json` file
- **Read full docs**: Check `README.md` and `CLAUDE.md`

## Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**"spaCy model not found":**
```bash
python3 -m spacy download en_core_web_md
```

**Port 5000 already in use:**
Edit `run_webapp.py` and change the port number on the last line.

**Web interface not loading:**
Make sure you're accessing `http://localhost:5000` (not `https://`).

## Performance Tips

- **Small files** (< 1 MB): Instant processing
- **Medium files** (1-10 MB): A few seconds
- **Large files** (> 10 MB): May take 30+ seconds with NER enabled

For very large files, consider using the CLI instead of the web interface.
