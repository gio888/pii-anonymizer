#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from typing import Dict, List, Optional, Any

# Import the core components
from .pii_anonymizer.document_processor import DocumentProcessor, PIIManager, PiiConfig
from .handlers.text_pdf_handlers import TextDocumentHandler, PDFDocumentHandler
from .handlers.google_handlers import GoogleDocsHandler, GoogleSheetsHandler

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
    # Create the PII manager
    pii_manager = PIIManager()
    
    # Create the document processor
    processor = DocumentProcessor(pii_manager)
    
    # Register handlers
    processor.register_handler(TextDocumentHandler(pii_manager))
    processor.register_handler(PDFDocumentHandler(pii_manager))
    
    # Add Google Docs/Sheets handlers if credentials are provided
    if args.google_credentials:
        processor.register_handler(GoogleDocsHandler(pii_manager, args.google_credentials))
        processor.register_handler(GoogleSheetsHandler(pii_manager, args.google_credentials))
    
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
  python pii_anonymizer.py anonymize -i document.txt -o document_anon.txt -m mapping.json
  
  # Restore an anonymized file
  python pii_anonymizer.py restore -i document_anon.txt -o document_restored.txt -m mapping.json
  
  # Process a batch of files
  python pii_anonymizer.py anonymize -i input_folder -o output_folder -m mapping.json -b
  
  # Anonymize a Google Doc (requires credentials)
  python pii_anonymizer.py anonymize -i "https://docs.google.com/document/d/1234..." -o gdoc_anon.txt -m mapping.json -g credentials.json
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


if __name__ == "__main__":
    main()