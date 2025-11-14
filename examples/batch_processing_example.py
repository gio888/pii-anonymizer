#!/usr/bin/env python3
"""
Example script demonstrating batch processing of multiple files.
"""
import os
import sys
import time

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import DocumentProcessor, PIIManager
from src.handlers.text_pdf_handlers import TextDocumentHandler, PDFDocumentHandler


def create_sample_files():
    """Create sample files for the example."""
    # Create directories
    input_dir = 'examples/input/batch'
    os.makedirs(input_dir, exist_ok=True)
    
    # Sample files with different PII types
    files = {
        'employee.txt': """
        Employee Information:
        Name: Robert Smith
        Email: robert.smith@company.com
        Phone: (123) 456-7890
        SSN: 123-45-6789
        Address: 123 Main St, Anytown, CA 12345
        """,
        
        'customer.txt': """
        Customer Information:
        Name: Sarah Johnson
        Email: sarah.j@example.com
        Phone: 555-987-6543
        Credit Card: 4111-1111-1111-1111
        Shipping Address: 456 Oak Ave, Somewhere, NY 54321
        """,
        
        'contacts.csv': """Name,Email,Phone,Address
        John Doe,john.doe@gmail.com,(800) 555-1234,789 Pine Lane Boston MA 02108
        Jane Smith,jsmith@example.org,555-222-3333,101 Maple Street Chicago IL 60601
        """
    }
    
    # Create the sample files
    for filename, content in files.items():
        file_path = os.path.join(input_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
    
    return input_dir


def main():
    """Run the batch processing example."""
    # Create a PII manager
    pii_manager = PIIManager()
    
    # Create a document processor
    processor = DocumentProcessor(pii_manager)
    
    # Register handlers
    processor.register_handler(TextDocumentHandler(pii_manager))
    
    # Try to register PDF handler if dependencies are available
    try:
        import PyPDF2
        import pdfplumber
        processor.register_handler(PDFDocumentHandler(pii_manager))
        print("PDF handler registered successfully.")
    except ImportError:
        print("PDF dependencies not found. PDF handling will not be available.")
    
    # Define input, output, and mapping paths
    input_dir = create_sample_files()
    output_dir = 'examples/output/batch'
    mapping_file = 'examples/output/batch_mapping.json'
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Processing files in: {input_dir}")
    print(f"Anonymized files will be saved to: {output_dir}")
    
    # Start timer
    start_time = time.time()
    
    # Process the batch (anonymize)
    results = processor.process_batch(input_dir, output_dir, mapping_file, action='anonymize')
    
    # End timer
    end_time = time.time()
    
    # Print results
    print("\nBatch anonymization completed:")
    print(f"- Successful: {len(results['successful'])} files")
    for file in results['successful']:
        print(f"  - {file}")
    
    print(f"- Failed: {len(results['failed'])} files")
    for file in results['failed']:
        print(f"  - {file}")
    
    print(f"\nPII mapping saved to: {mapping_file}")
    print(f"Processing time: {end_time - start_time:.2f} seconds")
    
    # Get PII statistics
    stats = pii_manager.get_statistics()
    print("\nPII Statistics:")
    for pii_type, count in stats.items():
        if pii_type != 'TOTAL':
            print(f"  {pii_type}: {count}")
    print(f"  TOTAL: {stats.get('TOTAL', 0)}")
    
    # Now restore the files
    print("\nRestoring anonymized files...")
    
    # Create a new PII manager and document processor for restoration
    restore_manager = PIIManager()
    restore_processor = DocumentProcessor(restore_manager)
    
    # Register the same handlers
    restore_processor.register_handler(TextDocumentHandler(restore_manager))
    try:
        import PyPDF2
        import pdfplumber
        restore_processor.register_handler(PDFDocumentHandler(restore_manager))
    except ImportError:
        pass
    
    # Define restore output directory
    restore_dir = 'examples/output/batch_restored'
    os.makedirs(restore_dir, exist_ok=True)
    
    # Load the mapping file
    restore_manager.load_mapping(mapping_file)
    
    # Process the batch (restore)
    restore_results = restore_processor.process_batch(
        output_dir, restore_dir, mapping_file, action='restore'
    )
    
    # Print restore results
    print("\nBatch restoration completed:")
    print(f"- Successful: {len(restore_results['successful'])} files")
    print(f"- Failed: {len(restore_results['failed'])} files")
    
    print(f"\nRestored files saved to: {restore_dir}")


if __name__ == '__main__':
    main()