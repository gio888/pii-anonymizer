import unittest
import os
import sys
import tempfile
import json

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pii_anonymizer.document_processor import PIIManager, PiiConfig


class TestPIIManager(unittest.TestCase):
    """Tests for the PIIManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pii_manager = PIIManager()
        
        # Sample text with various PII types
        self.sample_text = """
        Hello, my name is John Smith and my email is john.smith@example.com.
        You can reach me at (555) 123-4567 or visit me at 123 Main Street, Springfield.
        My SSN is 123-45-6789 and my credit card number is 4111-1111-1111-1111.
        The server IP address is 192.168.1.1 and my date of birth is 01/15/1980.
        Visit my website at https://www.johnsmith.com for more information.
        """
    
    def test_detect_pii_in_text(self):
        """Test PII detection in text."""
        detections = self.pii_manager.detect_pii_in_text(self.sample_text)
        
        # Check if we detected the expected types of PII
        pii_types = set(pii_type for _, pii_type, _ in detections)
        expected_types = {'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'IP_ADDRESS', 'DATE', 'URL'}
        
        # We may not detect all types, but should detect most
        self.assertTrue(len(pii_types.intersection(expected_types)) >= 4,
                        f"Expected to detect at least 4 PII types, but got {pii_types}")
        
        # Check that we detected at least one instance of each major type
        email_detected = any(pii_type == 'EMAIL' for _, pii_type, _ in detections)
        phone_detected = any(pii_type == 'PHONE' for _, pii_type, _ in detections)
        
        self.assertTrue(email_detected, "Failed to detect email address")
        self.assertTrue(phone_detected, "Failed to detect phone number")
    
    def test_anonymize_text(self):
        """Test text anonymization."""
        anonymized_text = self.pii_manager.anonymize_text(self.sample_text)
        
        # The anonymized text should not contain the original PII
        self.assertNotIn('john.smith@example.com', anonymized_text)
        self.assertNotIn('(555) 123-4567', anonymized_text)
        self.assertNotIn('123-45-6789', anonymized_text)
        
        # The anonymized text should contain placeholders
        self.assertIn('<EMAIL_', anonymized_text)
        self.assertIn('<PHONE_', anonymized_text)
        self.assertIn('<SSN_', anonymized_text)
    
    def test_restore_text(self):
        """Test text restoration."""
        anonymized_text = self.pii_manager.anonymize_text(self.sample_text)
        restored_text = self.pii_manager.restore_text(anonymized_text)
        
        # The restored text should be identical to the original
        self.assertEqual(self.sample_text, restored_text)
    
    def test_save_load_mapping(self):
        """Test saving and loading the PII mapping."""
        # Anonymize text to create mappings
        anonymized_text = self.pii_manager.anonymize_text(self.sample_text)
        
        # Save the mapping to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
            mapping_path = temp_file.name
        
        self.pii_manager.save_mapping(mapping_path)
        
        # Create a new PII manager and load the mapping
        new_manager = PIIManager()
        new_manager.load_mapping(mapping_path)
        
        # Restore using the new manager
        restored_text = new_manager.restore_text(anonymized_text)
        
        # The restored text should be identical to the original
        self.assertEqual(self.sample_text, restored_text)
        
        # Clean up
        os.unlink(mapping_path)
    
    def test_get_statistics(self):
        """Test getting statistics about detected PII."""
        # Anonymize text to create detections
        anonymized_text = self.pii_manager.anonymize_text(self.sample_text)

        # Get statistics
        stats = self.pii_manager.get_statistics()

        # Check that we have statistics for the PII types we expect
        self.assertIn('EMAIL', stats)
        self.assertIn('PHONE', stats)
        self.assertIn('TOTAL', stats)

        # Total should be the sum of all individual types
        total = sum(count for pii_type, count in stats.items() if pii_type != 'TOTAL')
        self.assertEqual(stats['TOTAL'], total)

    def test_abbreviation_detection(self):
        """Test detection of all-caps abbreviations."""
        # Test with spaCy NER enabled
        pii_manager_ner = PIIManager(use_ner=True)

        text = "BXC announced a partnership with IBM today. The 3M company also joined, along with FTSE leaders."

        detections = pii_manager_ner.detect_pii_in_text(text)
        detected_texts = [d[0] for d in detections]

        # Should detect all-caps abbreviations
        self.assertIn("BXC", detected_texts, "Failed to detect BXC")
        self.assertIn("IBM", detected_texts, "Failed to detect IBM")
        self.assertIn("3M", detected_texts, "Failed to detect 3M (alphanumeric)")
        self.assertIn("FTSE", detected_texts, "Failed to detect FTSE")

        # All should be classified as ORGANIZATION
        for text, pii_type, _ in detections:
            if text in ["BXC", "IBM", "3M", "FTSE"]:
                self.assertEqual(pii_type, "ORGANIZATION",
                               f"{text} should be classified as ORGANIZATION, got {pii_type}")

    def test_abbreviation_context_filtering(self):
        """Test that common words are not detected as abbreviations unless in organization context."""
        pii_manager_ner = PIIManager(use_ner=True)

        # Test 1: Common words without context should NOT be detected
        text1 = "I am OK with this decision. We can proceed."
        detections1 = pii_manager_ner.detect_pii_in_text(text1)
        detected_texts1 = [d[0] for d in detections1]

        self.assertNotIn("I", detected_texts1, "Should not detect 'I' as abbreviation")
        self.assertNotIn("OK", detected_texts1, "Should not detect 'OK' as abbreviation")
        self.assertNotIn("We", detected_texts1, "Should not detect 'We' as abbreviation")

        # Test 2: Ambiguous words WITH organization context SHOULD be detected
        text2 = "US Steel Corporation is a major producer. IT Solutions Inc provides services."
        detections2 = pii_manager_ner.detect_pii_in_text(text2)
        detected_texts2 = [d[0] for d in detections2]

        # "US Steel Corporation" should be detected as organization (by pattern-based NER)
        # "US" alone might be detected if context is strong enough
        # "IT Solutions Inc" should be detected
        has_us_or_steel = any("US" in text or "Steel" in text for text in detected_texts2)
        has_it_or_solutions = any("IT" in text or "Solutions" in text for text in detected_texts2)

        self.assertTrue(has_us_or_steel, "Should detect organization with US in context")
        self.assertTrue(has_it_or_solutions, "Should detect organization with IT in context")

    def test_stock_ticker_detection(self):
        """Test stock ticker format detection."""
        pii_manager_ner = PIIManager(use_ner=True)

        text = "Shares of NASDAQ: NEON rose today. NYSE: ABBV also performed well. The FTSE 100 index climbed."

        detections = pii_manager_ner.detect_pii_in_text(text)
        detected_texts = [d[0] for d in detections]

        # Should detect stock ticker patterns
        has_nasdaq_neon = any("NASDAQ" in text and "NEON" in text for text in detected_texts)
        has_nyse_abbv = any("NYSE" in text and "ABBV" in text for text in detected_texts)
        has_ftse = any("FTSE" in text for text in detected_texts)

        self.assertTrue(has_nasdaq_neon, "Should detect NASDAQ: NEON ticker")
        self.assertTrue(has_nyse_abbv, "Should detect NYSE: ABBV ticker")
        self.assertTrue(has_ftse, "Should detect FTSE 100")

    def test_alphanumeric_abbreviations(self):
        """Test alphanumeric abbreviation detection (3M, F5, etc.)."""
        pii_manager_ner = PIIManager(use_ner=True)

        text = "3M and F5 Networks are technology companies. The 401K plan is available."

        detections = pii_manager_ner.detect_pii_in_text(text)
        detected_texts = [d[0] for d in detections]

        self.assertIn("3M", detected_texts, "Should detect 3M")
        self.assertIn("F5", detected_texts, "Should detect F5")
        self.assertIn("401K", detected_texts, "Should detect 401K")


class TestPiiConfig(unittest.TestCase):
    """Tests for the PiiConfig class."""
    
    def test_default_patterns(self):
        """Test default regex patterns."""
        config = PiiConfig()
        
        # Check that we have the expected default patterns
        expected_patterns = ['EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'IP_ADDRESS', 'DATE', 'URL']
        for pattern_name in expected_patterns:
            self.assertIn(pattern_name, config.patterns)
    
    def test_custom_patterns(self):
        """Test custom regex patterns."""
        custom_patterns = {
            'PASSPORT': r'\b[A-Z]{2}[0-9]{7}\b',
            'CUSTOM_ID': r'\bID-[0-9]{5}\b'
        }
        
        config = PiiConfig(custom_patterns=custom_patterns)
        
        # Check that our custom patterns were added
        self.assertIn('PASSPORT', config.patterns)
        self.assertIn('CUSTOM_ID', config.patterns)
        
        # And that default patterns are still there
        self.assertIn('EMAIL', config.patterns)
        self.assertIn('PHONE', config.patterns)


if __name__ == '__main__':
    unittest.main()