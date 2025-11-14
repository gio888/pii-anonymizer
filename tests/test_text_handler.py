import unittest
import os
import sys
import tempfile
import shutil

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import PIIManager
from src.handlers.text_pdf_handlers import TextDocumentHandler


class TestTextDocumentHandler(unittest.TestCase):
    """Tests for the TextDocumentHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pii_manager = PIIManager()
        self.handler = TextDocumentHandler(self.pii_manager)
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample text with PII
        self.sample_text = """
        Hello, my name is Jane Doe and my email is jane.doe@example.com.
        You can reach me at (555) 987-6543 or visit me at 456 Oak Avenue, Anytown.
        """
        
        # Create test files with different extensions
        self.txt_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.txt_file, 'w') as f:
            f.write(self.sample_text)
        
        self.md_file = os.path.join(self.temp_dir, "test.md")
        with open(self.md_file, 'w') as f:
            f.write(self.sample_text)
        
        self.csv_file = os.path.join(self.temp_dir, "test.csv")
        with open(self.csv_file, 'w') as f:
            f.write("Name,Email,Phone\nJane Doe,jane.doe@example.com,(555) 987-6543")
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory and files
        shutil.rmtree(self.temp_dir)
    
    def test_can_handle(self):
        """Test file type detection."""
        # Should handle .txt files
        self.assertTrue(self.handler.can_handle(self.txt_file))
        
        # Should handle .md files
        self.assertTrue(self.handler.can_handle(self.md_file))
        
        # Should handle .csv files
        self.assertTrue(self.handler.can_handle(self.csv_file))
        
        # Should not handle other file types
        pdf_file = os.path.join(self.temp_dir, "test.pdf")
        with open(pdf_file, 'w') as f:
            f.write("PDF content")
        self.assertFalse(self.handler.can_handle(pdf_file))
    
    def test_extract_text(self):
        """Test text extraction."""
        # Extract text from .txt file
        extracted_text = self.handler.extract_text(self.txt_file)
        self.assertEqual(extracted_text, self.sample_text)
        
        # Extract text from .md file
        extracted_text = self.handler.extract_text(self.md_file)
        self.assertEqual(extracted_text, self.sample_text)
        
        # Extract text from .csv file
        extracted_text = self.handler.extract_text(self.csv_file)
        self.assertEqual(extracted_text, "Name,Email,Phone\nJane Doe,jane.doe@example.com,(555) 987-6543")
    
    def test_anonymize(self):
        """Test anonymization."""
        # Output file
        output_file = os.path.join(self.temp_dir, "test_anon.txt")
        
        # Anonymize the file
        self.handler.anonymize(self.txt_file, output_file)
        
        # Check that the output file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read the output file and check that PII was anonymized
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Email should be anonymized
        self.assertNotIn('jane.doe@example.com', content)
        self.assertIn('<EMAIL_', content)
        
        # Phone number should be anonymized
        self.assertNotIn('(555) 987-6543', content)
        self.assertIn('<PHONE_', content)
    
    def test_restore(self):
        """Test restoration."""
        # First anonymize
        anon_file = os.path.join(self.temp_dir, "test_anon.txt")
        self.handler.anonymize(self.txt_file, anon_file)
        
        # Now restore
        restored_file = os.path.join(self.temp_dir, "test_restored.txt")
        self.handler.restore(anon_file, restored_file)
        
        # Check that the restored file was created
        self.assertTrue(os.path.exists(restored_file))
        
        # Read the restored file and check that PII was restored
        with open(restored_file, 'r') as f:
            restored_content = f.read()
        
        # Compare with original
        with open(self.txt_file, 'r') as f:
            original_content = f.read()
        
        self.assertEqual(restored_content, original_content)
    
    def test_csv_processing(self):
        """Test processing of CSV files."""
        # Output file
        output_file = os.path.join(self.temp_dir, "test_anon.csv")
        
        # Anonymize the CSV file
        self.handler.anonymize(self.csv_file, output_file)
        
        # Check that the output file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read the output file and check that PII was anonymized
        with open(output_file, 'r') as f:
            content = f.read()
        
        # Email and phone should be anonymized
        self.assertNotIn('jane.doe@example.com', content)
        self.assertNotIn('(555) 987-6543', content)
        
        # But column headers should remain
        self.assertIn('Name,Email,Phone', content)
        
        # Now restore
        restored_file = os.path.join(self.temp_dir, "test_restored.csv")
        self.handler.restore(output_file, restored_file)
        
        # Read the restored file and check that PII was restored
        with open(restored_file, 'r') as f:
            restored_content = f.read()
        
        # Compare with original
        with open(self.csv_file, 'r') as f:
            original_content = f.read()
        
        self.assertEqual(restored_content, original_content)


if __name__ == '__main__':
    unittest.main()