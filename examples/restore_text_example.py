#!/usr/bin/env python3
"""
Example script demonstrating how to restore an anonymized text file.
"""
import os
import sys

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import PIIManager
from src.handlers.text_pdf_handlers import TextDocumentHandler


def main():
    """Run the example."""
    # Create a PII manager
    pii_manager = PIIManager()
    
    # Create a text document handler
    text_handler = TextDocumentHandler(pii_manager)
    
    # Define input, output, and mapping files
    anonymized_file = 'examples/output/anonymized_text.txt'
    restored_file = 'examples/output/restored_text.txt'
    mapping_file = 'examples/output/mapping.json'
    
    # Check if the anonymized file and mapping file exist
    if not os.path.exists(anonymized_file):
        print(f"Error: Anonymized file not found: {anonymized_file}")
        print("Please run the anonymize_text_example.py script first.")
        return
    
    if not os.path.exists(mapping_file):
        print(f"Error: Mapping file not found: {mapping_file}")
        print("Please run the anonymize_text_example.py script first.")
        return
    
    print(f"Loading PII mapping from: {mapping_file}")
    
    # Load the PII mapping
    pii_manager.load_mapping(mapping_file)
    
    print(f"Restoring anonymized file: {anonymized_file}")
    
    # Restore the file
    text_handler.restore(anonymized_file, restored_file)
    
    print(f"Restored file saved to: {restored_file}")
    
    # Compare original and restored content
    with open('examples/input/sample_text.txt', 'r') as f:
        original_content = f.read()
    
    with open(restored_file, 'r') as f:
        restored_content = f.read()
    
    if original_content == restored_content:
        print("\nSuccess! The restored content matches the original.")
    else:
        print("\nWarning: The restored content does not match the original.")


if __name__ == '__main__':
    main()