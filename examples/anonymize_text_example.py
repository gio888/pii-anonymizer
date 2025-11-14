#!/usr/bin/env python3
"""
Example script demonstrating how to anonymize a text file with PII.
"""
import os
import sys

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import PIIManager, PiiConfig
from src.handlers.text_pdf_handlers import TextDocumentHandler


def main():
    """Run the example."""
    # Create a config with default patterns
    pii_config = PiiConfig()
    
    # Add a custom pattern if needed
    custom_patterns = {
        'PASSPORT': r'\b[A-Z]{2}[0-9]{7}\b',  # Example format: AB1234567
    }
    pii_config = PiiConfig(custom_patterns=custom_patterns)
    
    # Create a PII manager with the config
    pii_manager = PIIManager(pii_config)
    
    # Create a text document handler
    text_handler = TextDocumentHandler(pii_manager)
    
    # Define input and output files
    input_file = 'examples/input/sample_text.txt'
    output_file = 'examples/output/anonymized_text.txt'
    mapping_file = 'examples/output/mapping.json'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create a sample text file if it doesn't exist
    if not os.path.exists(input_file):
        os.makedirs(os.path.dirname(input_file), exist_ok=True)
        with open(input_file, 'w') as f:
            f.write("""
            Hello, my name is Alice Johnson and my email is alice.johnson@example.com.
            You can reach me at (555) 123-4567 or visit me at 789 Pine Street, Sometown.
            My passport number is AB1234567 and I was born on 03/15/1985.
            """)
    
    print(f"Anonymizing file: {input_file}")
    
    # Anonymize the file
    text_handler.anonymize(input_file, output_file)
    
    # Save the PII mapping
    pii_manager.save_mapping(mapping_file)
    
    print(f"Anonymized file saved to: {output_file}")
    print(f"PII mapping saved to: {mapping_file}")
    
    # Display statistics
    stats = pii_manager.get_statistics()
    print("\nPII Statistics:")
    for pii_type, count in stats.items():
        print(f"  {pii_type}: {count}")


if __name__ == '__main__':
    main()