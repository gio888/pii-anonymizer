import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import MagicMock, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import DocumentProcessor, PIIManager, DocumentHandler


class MockDocumentHandler(DocumentHandler):
    """Mock document handler for testing."""
    
    def __init__(self, pii_manager, file_extensions=None):
        super().__init__(pii_manager)
        self.file_extensions = file_extensions or ['.mock']
        self.anonymize_called = False
        self.restore_called = False
    
    def can_handle(self, file_path):
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.file_extensions
    
    def extract_text(self, file_path):
        return "This is mock text with PII: test@example.com"
    
    def anonymize(self, input_path, output_path):
        self.anonymize_called = True
        text = self.extract_text(input_path)
        anonymized_text = self.pii_manager.anonymize_text(text)
        with open(output_path, 'w') as f:
            f.write(anonymized_text)
    
    def restore(self, anonymized_path, output_path):
        self.restore_called = True
        with open(anonymized_path, 'r') as f:
            anonymized_text = f.read()
        restored_text = self.pii_manager.restore_text(anonymized_text)
        with open(output_path, 'w') as f:
            f.write(restored_text)


class TestDocumentProcessor(unittest.TestCase):
    """Tests for the DocumentProcessor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pii_manager = PIIManager()
        self.processor = DocumentProcessor(self.pii_manager)
        self.mock_handler = MockDocumentHandler(self.pii_manager)
        self.processor.register_handler(self.mock_handler)
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temp directory and files
        shutil.rmtree(self.temp_dir)
    
    def test_register_handler(self):
        """Test registering a document handler."""
        # Check that our mock handler was registered
        self.assertIn(self.mock_handler, self.processor.handlers)
        
        # Register another handler and check that it's added
        another_handler = MockDocumentHandler(self.pii_manager, ['.test'])
        self.processor.register_handler(another_handler)
        self.assertIn(another_handler, self.processor.handlers)
    
    def test_get_handler_for_file(self):
        """Test getting the appropriate handler for a file."""
        # Create a mock file that our handler can process
        mock_file = os.path.join(self.temp_dir, "test.mock")
        with open(mock_file, 'w') as f:
            f.write("This is a test file.")
        
        # Get handler for the file
        handler = self.processor.get_handler_for_file(mock_file)
        
        # Check that we got the right handler
        self.assertEqual(handler, self.mock_handler)
        
        # Create a file that no handler can process
        unknown_file = os.path.join(self.temp_dir, "unknown.xyz")
        with open(unknown_file, 'w') as f:
            f.write("This is an unknown file type.")
        
        # Try to get a handler for the unknown file
        handler = self.processor.get_handler_for_file(unknown_file)
        
        # Check that no handler was found
        self.assertIsNone(handler)
    
    def test_anonymize_document(self):
        """Test anonymizing a document."""
        # Create a mock file
        mock_file = os.path.join(self.temp_dir, "test.mock")
        with open(mock_file, 'w') as f:
            f.write("This is a test file with email: user@example.com")
        
        # Output file
        output_file = os.path.join(self.temp_dir, "test_anon.mock")
        
        # Anonymize the document
        result = self.processor.anonymize_document(mock_file, output_file)
        
        # Check that anonymization was successful
        self.assertTrue(result)
        self.assertTrue(self.mock_handler.anonymize_called)
        
        # Check that the output file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Read the output file and check that PII was anonymized
        with open(output_file, 'r') as f:
            content = f.read()
        self.assertNotIn('test@example.com', content)
        self.assertIn('<EMAIL_', content)
    
    def test_restore_document(self):
        """Test restoring an anonymized document."""
        # Create a mock anonymized file
        mock_anon_file = os.path.join(self.temp_dir, "test_anon.mock")
        original_text = "This is mock text with PII: test@example.com"
        anonymized_text = self.pii_manager.anonymize_text(original_text)
        with open(mock_anon_file, 'w') as f:
            f.write(anonymized_text)
        
        # Output file for restored content
        restored_file = os.path.join(self.temp_dir, "test_restored.mock")
        
        # Restore the document
        result = self.processor.restore_document(mock_anon_file, restored_file)
        
        # Check that restoration was successful
        self.assertTrue(result)
        self.assertTrue(self.mock_handler.restore_called)
        
        # Check that the output file was created
        self.assertTrue(os.path.exists(restored_file))
        
        # Read the output file and check that PII was restored
        with open(restored_file, 'r') as f:
            content = f.read()
        self.assertIn('test@example.com', content)
        self.assertNotIn('<EMAIL_', content)
    
    def test_process_batch(self):
        """Test batch processing of documents."""
        # Create input directory with test files
        input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(input_dir)
        
        # Create a couple of mock files
        mock_file1 = os.path.join(input_dir, "test1.mock")
        with open(mock_file1, 'w') as f:
            f.write("This is test file 1 with email: user1@example.com")
        
        mock_file2 = os.path.join(input_dir, "test2.mock")
        with open(mock_file2, 'w') as f:
            f.write("This is test file 2 with email: user2@example.com")
        
        # Create an unknown file that should be skipped
        unknown_file = os.path.join(input_dir, "unknown.xyz")
        with open(unknown_file, 'w') as f:
            f.write("This is an unknown file type.")
        
        # Output directory
        output_dir = os.path.join(self.temp_dir, "output")
        
        # Mapping file
        mapping_file = os.path.join(self.temp_dir, "mapping.json")
        
        # Process the batch
        results = self.processor.process_batch(input_dir, output_dir, mapping_file)
        
        # Check that the successful and failed files are correctly identified
        self.assertEqual(len(results['successful']), 2)
        self.assertEqual(len(results['failed']), 1)
        self.assertIn('test1.mock', results['successful'])
        self.assertIn('test2.mock', results['successful'])
        self.assertIn('unknown.xyz', results['failed'])
        
        # Check that output files were created
        self.assertTrue(os.path.exists(os.path.join(output_dir, "test1.mock")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "test2.mock")))
        
        # Check that mapping file was created
        self.assertTrue(os.path.exists(mapping_file))


if __name__ == '__main__':
    unittest.main()