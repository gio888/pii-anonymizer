# PII Anonymizer Examples

This directory contains example scripts demonstrating how to use the PII Anonymizer.

## Example Files

1. `anonymize_text_example.py`: Demonstrates how to anonymize a text file containing PII
2. `restore_text_example.py`: Demonstrates how to restore an anonymized text file using a mapping
3. `batch_processing_example.py`: Demonstrates how to process multiple files in a batch

## Running the Examples

Before running the examples, make sure you have installed all required dependencies:

```bash
pip install -r ../requirements.txt
```

### Example 1: Anonymize a Text File

This example demonstrates how to anonymize a text file containing various types of PII.

```bash
python anonymize_text_example.py
```

The example will:
1. Create a sample text file in `examples/input/sample_text.txt`
2. Anonymize the file and save it to `examples/output/anonymized_text.txt`
3. Save the PII mapping to `examples/output/mapping.json`
4. Display statistics about the detected PII

### Example 2: Restore an Anonymized File

This example demonstrates how to restore an anonymized file using the PII mapping.

```bash
python restore_text_example.py
```

The example will:
1. Load the PII mapping from `examples/output/mapping.json`
2. Restore the anonymized file and save it to `examples/output/restored_text.txt`
3. Compare the original and restored content to verify successful restoration

**Note:** This example requires running the anonymize_text_example.py first.

### Example 3: Batch Processing

This example demonstrates how to process multiple files in a batch.

```bash
python batch_processing_example.py
```

The example will:
1. Create sample files with different types of PII in `examples/input/batch/`
2. Process all files in batch mode, anonymizing them
3. Save the anonymized files to `examples/output/batch/`
4. Save the PII mapping to `examples/output/batch_mapping.json`
5. Restore the anonymized files and save them to `examples/output/batch_restored/`
6. Display statistics about the detected PII

## Creating Your Own Examples

You can use these examples as a starting point for your own applications. Here's a basic template:

```python
from src.pii_anonymizer.document_processor import PIIManager
from src.handlers.text_pdf_handlers import TextDocumentHandler

# Create a PII manager
pii_manager = PIIManager()

# Create a document handler
handler = TextDocumentHandler(pii_manager)

# Anonymize a document
handler.anonymize('input.txt', 'anonymized.txt')

# Save the mapping
pii_manager.save_mapping('mapping.json')

# Later, restore the document
pii_manager.load_mapping('mapping.json')
handler.restore('anonymized.txt', 'restored.txt')
```

## Customizing PII Detection

You can customize PII detection by providing custom regex patterns:

```python
from src.pii_anonymizer.document_processor import PIIManager, PiiConfig

# Define custom patterns
custom_patterns = {
    'PASSPORT': r'\b[A-Z]{2}[0-9]{7}\b',
    'EMPLOYEE_ID': r'\bEMP-[0-9]{5}\b'
}

# Create a config with custom patterns
pii_config = PiiConfig(custom_patterns=custom_patterns)

# Create a PII manager with the config
pii_manager = PIIManager(pii_config)
```

For more examples, check the unit tests in the `tests/` directory.