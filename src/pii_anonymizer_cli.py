#!/usr/bin/env python3
"""
PII Anonymizer - Command-line interface for detecting, anonymizing, and restoring PII in documents.
"""
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any

# Import the core components
from src.pii_anonymizer.document_processor import DocumentProcessor, PIIManager, PiiConfig
from src.handlers.text_pdf_handlers import TextDocumentHandler, PDFDocumentHandler
from src.handlers.google_handlers import GoogleDocsHandler, GoogleSheetsHandler
from src.handlers.office_handlers import DocxDocumentHandler, XlsxDocumentHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pii_anonymizer.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('pii_anonymizer.main')


def setup_processor(args: argparse.Namespace) -> DocumentProcessor:
    """
    Set up the document processor with appropriate handlers.
    
    Args:
        args: Command line arguments
        
    Returns:
        Configured DocumentProcessor
    """
    # Create custom patterns if specified
    custom_patterns = None
    if args.custom_patterns:
        try:
            import json
            with open(args.custom_patterns, 'r') as f:
                custom_patterns = json.load(f)
            logger.info(f"Loaded custom patterns from {args.custom_patterns}")
        except Exception as e:
            logger.error(f"Error loading custom patterns: {str(e)}")
    
    # Create the PII config and manager
    pii_config = PiiConfig(custom_patterns=custom_patterns)
    pii_manager = PIIManager(pii_config)
    
    # Create the document processor
    processor = DocumentProcessor(pii_manager)
    
    # Register handlers
    processor.register_handler(TextDocumentHandler(pii_manager))

    # Register PDF handler if dependencies are available
    try:
        import PyPDF2
        import pdfplumber
        processor.register_handler(PDFDocumentHandler(pii_manager))
        logger.info("Registered PDF handler.")
    except ImportError:
        logger.warning("PDF dependencies not found. PDF handling will not be available.")

    # Register Office document handlers if dependencies are available
    try:
        import docx
        processor.register_handler(DocxDocumentHandler(pii_manager))
        logger.info("Registered DOCX handler.")
    except ImportError:
        logger.warning("python-docx not found. DOCX handling will not be available.")

    try:
        import openpyxl
        processor.register_handler(XlsxDocumentHandler(pii_manager))
        logger.info("Registered XLSX handler.")
    except ImportError:
        logger.warning("openpyxl not found. XLSX handling will not be available.")
    
    # Add Google Docs/Sheets handlers if credentials are provided
    if args.google_credentials:
        try:
            processor.register_handler(GoogleDocsHandler(pii_manager, args.google_credentials))
            processor.register_handler(GoogleSheetsHandler(pii_manager, args.google_credentials))
            logger.info("Registered Google Docs/Sheets handlers.")
        except Exception as e:
            logger.error(f"Error registering Google handlers: {str(e)}")
    
    # Load mapping if restoring and the mapping file exists
    if args.action == 'restore' and os.path.exists(args.mapping):
        processor.load_mapping(args.mapping)
    
    return processor


def process_single_file(processor: DocumentProcessor, args: argparse.Namespace) -> bool:
    """
    Process a single file.
    
    Args:
        processor: The document processor
        args: Command line arguments
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process the file
    if args.action == 'anonymize':
        success = processor.anonymize_document(args.input, args.output)
        
        # Save the mapping
        if success and args.mapping:
            processor.save_mapping(args.mapping)
    
    elif args.action == 'restore':
        success = processor.restore_document(args.input, args.output)
    
    return success


def process_batch(processor: DocumentProcessor, args: argparse.Namespace) -> Dict[str, List[str]]:
    """
    Process a batch of files.
    
    Args:
        processor: The document processor
        args: Command line arguments
        
    Returns:
        Dictionary with lists of successful and failed files
    """
    # Process the batch
    results = processor.process_batch(
        args.input, args.output, args.mapping, args.action
    )
    
    return results


def main():
    """Main function to run the PII Anonymizer."""
    parser = argparse.ArgumentParser(
        description='PII Anonymizer: Detect, anonymize, and restore PII in various document types.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Anonymize a text file
  python pii_anonymizer_cli.py anonymize -i document.txt -o document_anon.txt -m mapping.json
  
  # Restore an anonymized file
  python pii_anonymizer_cli.py restore -i document_anon.txt -o document_restored.txt -m mapping.json
  
  # Process a batch of files
  python pii_anonymizer_cli.py anonymize -i input_folder -o output_folder -m mapping.json -b
  
  # Anonymize a Google Doc (requires credentials)
  python pii_anonymizer_cli.py anonymize -i "https://docs.google.com/document/d/1234..." -o gdoc_anon.txt -m mapping.json -g credentials.json
  
  # Use custom PII patterns
  python pii_anonymizer_cli.py anonymize -i document.txt -o document_anon.txt -m mapping.json -p patterns.json
"""
    )
    
    parser.add_argument(
        'action', choices=['anonymize', 'restore'],
        help='Action to perform: anonymize or restore'
    )
    parser.add_argument(
        '--input', '-i', required=True,
        help='Input file or directory to process'
    )
    parser.add_argument(
        '--output', '-o', required=True,
        help='Output file or directory to save results'
    )
    parser.add_argument(
        '--mapping', '-m', required=True,
        help='Mapping file (will be created during anonymization, required for restoration)'
    )
    parser.add_argument(
        '--batch', '-b', action='store_true',
        help='Process files in batch (input and output should be directories)'
    )
    parser.add_argument(
        '--google-credentials', '-g',
        help='Path to Google API credentials file (required for Google Docs/Sheets)'
    )
    parser.add_argument(
        '--custom-patterns', '-p',
        help='Path to JSON file containing custom regex patterns for PII detection'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger('pii_anonymizer').setLevel(logging.DEBUG)
    
    # Initialize the document processor
    processor = setup_processor(args)
    
    # Process the file(s)
    if args.batch:
        # Check if input and output are directories
        if not os.path.isdir(args.input):
            parser.error(f"Input must be a directory in batch mode: {args.input}")
        
        results = process_batch(processor, args)
        
        # Print results
        logger.info(f"Batch processing completed.")
        logger.info(f"Successful: {len(results['successful'])} files")
        logger.info(f"Failed: {len(results['failed'])} files")
        
        if results['failed']:
            logger.warning("Failed files:")
            for file in results['failed']:
                logger.warning(f"  - {file}")
    else:
        # Process a single file
        success = process_single_file(processor, args)
        
        if success:
            logger.info(f"Processing completed successfully.")
        else:
            logger.error(f"Processing failed.")
            sys.exit(1)
    
    # Print PII statistics
    stats = processor.pii_manager.get_statistics()
    logger.info("PII Statistics:")
    for pii_type, count in stats.items():
        logger.info(f"  {pii_type}: {count}")


if __name__ == "__main__":
    main()