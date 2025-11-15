import os
import re
import uuid
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pii_anonymizer')

class PiiConfig:
    """Configuration container for PII detection patterns and settings."""
    
    def __init__(self, custom_patterns: Optional[Dict[str, str]] = None):
        # Standard regex patterns for PII detection
        self.patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Improved PHONE: handles all formats including flexible international numbers
            # Matches: +46 703 97 21 09, +1-555-890-1234, (555) 234-5678, 555 234 5678, 555-1234
            'PHONE': r'\(\d{3}\)\s*\d{3}[-\s.]\d{4}\b|\+\d{1,3}(?:[-\s]\d{2,4})+\b|\b\d{3}[-\s.]\d{3}[-\s.]\d{4}\b|\b\d{3}[-]\d{4}\b',
            'SSN': r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            # CREDIT_CARD: handles both 16-digit (4-4-4-4) and 15-digit Amex (4-6-5) formats
            'CREDIT_CARD': r'\b(?:\d{4}[-\s]?\d{6}[-\s]?\d{5}|\d{4}(?:[-\s]?\d{4}){3})\b',
            'IP_ADDRESS': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            # Improved DATE: handles numeric dates, text-based dates, years, ages, and "Month Year" formats
            'DATE': r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\b(?:19|20)\d{2}\b|\b\d{1,2}\b(?=\s*,)',
            # ADDRESS: matches full addresses with optional city, state, ZIP, and building designations
            # Handles: "123 Main Street", "200 S. Kraemer Blvd., Building E", "123 Main Street, City, ST 12345"
            'ADDRESS': r'\b\d{1,5}\s+(?:[NSEW]\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Avenue|Ave|Road|Rd|Street|St|Blvd|Boulevard|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct)\.?(?:,\s+(?:Building|Bldg|Suite|Ste|Unit|Apt)\.?\s+[A-Z0-9]+)?(?:,\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?)?\b',
            'URL': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
            # CURRENCY: handles $, €, £, ¥ with optional cents/decimals
            'CURRENCY': r'[\$\€\£\¥]\s?\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?'
        }
        
        # Add custom patterns if provided
        if custom_patterns:
            self.patterns.update(custom_patterns)
        
        # Common PII key names (for structured data)
        self.pii_key_patterns = [
            r'.*name.*', r'.*email.*', r'.*phone.*', r'.*address.*',
            r'.*ssn.*', r'.*social.*security.*', r'.*credit.*card.*',
            r'.*card.*number.*', r'.*dob.*', r'.*birth.*', r'.*zip.*',
            r'.*postal.*', r'.*passport.*', r'.*license.*', r'.*id.*number.*'
        ]
        
        # Mapping types to ensure consistent placeholder naming
        self.entity_type_mapping = {
            'PERSON': 'NAME',
            'PER': 'NAME',
            'PERSON_NAME': 'NAME',
            'ORG': 'ORGANIZATION',
            'GPE': 'LOCATION',
            'LOC': 'LOCATION',
            'PHONE_NUMBER': 'PHONE'
        }


class PIIManager:
    """
    Core class responsible for PII detection, anonymization, and mapping storage.
    """

    def __init__(self, config: Optional[PiiConfig] = None, use_semantic_aliases: bool = True, use_ner: bool = True):
        """
        Initialize the PII Manager.

        Args:
            config: PII configuration with patterns and settings
            use_semantic_aliases: If True, use semantic aliases like ACME_CORP instead of <ORG_uuid>
            use_ner: If True, use spaCy NER for detecting entities (people, companies, products)
        """
        self.config = config or PiiConfig()
        self.pii_map = {}  # Original PII to placeholder mapping
        self.reverse_map = {}  # Placeholder to original PII mapping
        self.use_semantic_aliases = use_semantic_aliases
        self.use_ner = use_ner

        # Initialize semantic alias generator if enabled
        if self.use_semantic_aliases:
            try:
                from utils.alias_generator import SemanticAliasGenerator
                self.alias_generator = SemanticAliasGenerator()
            except (ImportError, ValueError):
                logger.warning("Could not import SemanticAliasGenerator, falling back to UUID placeholders")
                self.use_semantic_aliases = False
                self.alias_generator = None
        else:
            self.alias_generator = None

        # Initialize spaCy NER if enabled
        if self.use_ner:
            try:
                import spacy
                self.nlp = spacy.load("en_core_web_md")
                logger.info("spaCy NER model loaded successfully")
            except OSError:
                logger.warning("spaCy model 'en_core_web_md' not found. Run: python -m spacy download en_core_web_md")
                self.use_ner = False
                self.nlp = None
            except ImportError:
                logger.warning("spaCy not installed. NER-based detection will be disabled.")
                self.use_ner = False
                self.nlp = None
        else:
            self.nlp = None
    
    def _detect_entities_with_ner(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect named entities using spaCy NER with pattern-based fallbacks.

        Args:
            text: The text to analyze

        Returns:
            List of tuples (entity_text, entity_type, start_pos, end_pos)
        """
        if not self.use_ner or self.nlp is None:
            return []

        doc = self.nlp(text)
        entities = []
        detected_spans = set()  # Track what we've already detected

        # 1. Get spaCy NER entities
        for ent in doc.ents:
            # We're interested in: PERSON, ORG, PRODUCT, GPE (locations)
            if ent.label_ in ['PERSON', 'ORG', 'PRODUCT', 'GPE']:
                # Skip entities that contain newlines (likely spaCy errors)
                if '\n' in ent.text or '\r' in ent.text:
                    continue
                # Normalize entity type using mapping
                entity_type = self.config.entity_type_mapping.get(ent.label_, ent.label_)
                entities.append((ent.text, entity_type, ent.start_char, ent.end_char))
                detected_spans.add((ent.start_char, ent.end_char))

        # 2. Add pattern-based detection for entities spaCy missed
        # Pattern for proper nouns (capitalized sequences) that might be names/orgs/products
        # Match: "John Smith", "Acme Corporation", "University of Toronto", "That's Nice LLC", etc.
        # Updated to handle: accented chars, apostrophes, and common words like "of", "and", "the"
        # Note: Use [ \t] instead of \s to avoid matching across newlines
        proper_noun_pattern = r'\b[A-Z][A-Za-zÀ-ÿ\']*(?:[ \t]+(?:[A-Z][A-Za-zÀ-ÿ\']*|of|and|the|de|la|le|du)|[ \t]+\d+)*\b'

        # Blacklist of common single words to exclude (articles, prepositions, common words)
        single_word_blacklist = {
            'The', 'A', 'An', 'And', 'Or', 'But', 'For', 'To', 'Of', 'In', 'On', 'At',
            'By', 'With', 'From', 'As', 'Is', 'Was', 'Are', 'Were', 'Be', 'Been',
            'He', 'She', 'It', 'They', 'We', 'I', 'You', 'This', 'That', 'These', 'Those',
            'Have', 'Has', 'Had', 'Do', 'Does', 'Did', 'Will', 'Would', 'Could', 'Should',
            'Can', 'May', 'Might', 'Must', 'Shall'
        }

        for match in re.finditer(proper_noun_pattern, text):
            start, end = match.span()
            # Skip if already detected by spaCy
            if (start, end) in detected_spans:
                continue

            matched_text = match.group(0)

            # For single words, apply blacklist filter
            if ' ' not in matched_text:
                if matched_text in single_word_blacklist:
                    continue
                # Also skip very short single words (2 chars or less) unless they have special chars
                if len(matched_text) <= 2 and not any(c in matched_text for c in 'À-ÿ'):
                    continue

            # Heuristic: classify as NAME, ORG, PRODUCT, or LOCATION based on patterns
            entity_type = 'ORGANIZATION'  # Default

            # Check if it looks like a product name (has product keywords)
            if any(keyword in matched_text for keyword in ['Suite', 'Platform', 'System', 'Tool', 'App', 'Service', 'Solution', 'Engine', 'Framework', 'Hub', 'Portal', 'Cloud', 'Pro', 'Ultra', 'Premium', 'Plus', 'Advanced', 'Elite', 'Mega', 'Super', 'Max', 'Turbo', 'Power', 'Smart']):
                entity_type = 'PRODUCT'
            # Check if it looks like an organization (has org keywords)
            elif any(suffix in matched_text for suffix in ['Inc', 'LLC', 'Corp', 'Corporation', 'Ltd', 'Limited', 'Group', 'Industries', 'Solutions', 'Systems', 'Technologies', 'Enterprises', 'Partners', 'Ventures', 'Company', 'Enterprises', 'Associates']):
                entity_type = 'ORGANIZATION'
            # Check if it looks like a person name (2-3 simple capitalized words)
            elif ' ' in matched_text:
                words = matched_text.split()
                if len(words) == 2 and all(w[0].isupper() and w[1:].islower() for w in words if len(w) > 1):
                    # Likely a person name (First Last)
                    entity_type = 'NAME'
                # Check if it looks like a location (contains location keywords)
                elif any(locword in words for locword in ['America', 'Europe', 'Asia', 'Africa', 'North', 'South', 'East', 'West', 'City', 'Town', 'Island', 'Mountain', 'River', 'Lake', 'Valley']):
                    entity_type = 'LOCATION'
            # Single-word entities: check if it looks like a location
            elif ' ' not in matched_text:
                # Check for 2-letter state/country codes (e.g., CA, NY, US, UK)
                if len(matched_text) == 2 and matched_text.isupper():
                    entity_type = 'LOCATION'

            entities.append((matched_text, entity_type, start, end))
            detected_spans.add((start, end))

        # 3. All-caps abbreviation detection (BXC, IBM, FTSE, etc.)
        # Base blacklist for common words that shouldn't be detected
        COMMON_WORDS_BLACKLIST = {"OK", "AM", "PM", "OR", "IF", "IS", "AS", "AT", "WE", "NO"}

        # Pattern 1: Basic all-caps abbreviations (2-5 letters)
        abbrev_pattern = r'\b[A-Z]{2,5}\b'
        for match in re.finditer(abbrev_pattern, text):
            start, end = match.span()
            if (start, end) in detected_spans:
                continue

            matched_text = match.group(0)

            # Filter common words using blacklist
            if matched_text in COMMON_WORDS_BLACKLIST:
                continue

            # Context-aware filtering for ambiguous words (US, IT, AI)
            if matched_text in {"US", "IT", "AI"}:
                # Check if it appears in organization context (near Inc, Corp, or capitalized words)
                context_before = text[max(0, start-30):start]
                context_after = text[end:min(len(text), end+30)]
                context = context_before + context_after

                # Keep if organization indicators present
                org_indicators = ['Inc', 'LLC', 'Corp', 'Ltd', 'Limited', 'Group', 'Industries',
                                'Solutions', 'Systems', 'Technologies', 'Enterprises', 'Company']
                has_org_context = any(indicator in context for indicator in org_indicators)

                # Keep if surrounded by other capitalized words (likely part of organization name)
                has_caps_context = bool(re.search(r'\b[A-Z][a-z]+\b', context))

                if not (has_org_context or has_caps_context):
                    continue

            # Classify as ORGANIZATION
            entity_type = 'ORGANIZATION'
            entities.append((matched_text, entity_type, start, end))
            detected_spans.add((start, end))

        # Pattern 2: Alphanumeric abbreviations (3M, F5, 401K)
        alphanumeric_pattern = r'\b(?:\d+[A-Z]+|[A-Z]+\d+)\b'
        for match in re.finditer(alphanumeric_pattern, text):
            start, end = match.span()
            if (start, end) in detected_spans:
                continue

            matched_text = match.group(0)
            entity_type = 'ORGANIZATION'
            entities.append((matched_text, entity_type, start, end))
            detected_spans.add((start, end))

        # Pattern 3: Stock ticker format (NYSE: ABBV, NASDAQ: NEON, FTSE 100)
        stock_ticker_pattern = r'\b(?:NYSE|NASDAQ|FTSE|S&P|DOW)(?::\s*|\s+)([A-Z]{1,5}|\d+)\b'
        for match in re.finditer(stock_ticker_pattern, text):
            # Extract the full match (including exchange prefix)
            start, end = match.span()
            if (start, end) in detected_spans:
                continue

            matched_text = match.group(0)
            entity_type = 'ORGANIZATION'
            entities.append((matched_text, entity_type, start, end))
            detected_spans.add((start, end))

        return entities

    def _create_placeholder(self, original: str, pii_type: str) -> str:
        """
        Create a placeholder for a PII value.

        Args:
            original: The original PII value
            pii_type: The type of PII

        Returns:
            A placeholder string
        """
        if original in self.pii_map:
            return self.pii_map[original]

        if self.use_semantic_aliases and self.alias_generator:
            # Use semantic alias for specific entity types
            if pii_type in ['ORGANIZATION', 'PERSON', 'NAME', 'PRODUCT', 'LOCATION']:
                placeholder = self.alias_generator.generate_alias(pii_type, original)
            else:
                # Use UUID-style placeholder for other types
                placeholder = f"<{pii_type}_{uuid.uuid4().hex[:8]}>"
        else:
            # Default UUID-style placeholder
            placeholder = f"<{pii_type}_{uuid.uuid4().hex[:8]}>"

        self.pii_map[original] = placeholder
        self.reverse_map[placeholder] = original
        return placeholder

    def detect_pii_in_text(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Detect PII in a text string using regex patterns and optionally NER.

        Args:
            text: The text to analyze

        Returns:
            List of tuples (pii_value, pii_type, placeholder)
        """
        if not isinstance(text, str):
            return []

        detections = []

        # 1. Apply regex patterns to detect PII
        for pii_type, pattern in self.config.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                original = match.group(0)
                placeholder = self._create_placeholder(original, pii_type)
                detections.append((original, pii_type, placeholder))

        # 2. Apply spaCy NER to detect named entities
        if self.use_ner:
            entities = self._detect_entities_with_ner(text)
            for entity_text, entity_type, start_pos, end_pos in entities:
                # Skip very short entities (likely false positives)
                if len(entity_text.strip()) < 2:
                    continue
                placeholder = self._create_placeholder(entity_text, entity_type)
                detections.append((entity_text, entity_type, placeholder))

        return detections
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize text by replacing detected PII with placeholders.
        
        Args:
            text: The text to anonymize
            
        Returns:
            Anonymized text
        """
        if not isinstance(text, str):
            return text
        
        anonymized_text = text
        detections = self.detect_pii_in_text(text)
        
        # Sort detections by position (reversed) to avoid offset issues
        # when replacing text
        text_indices = [(text.find(original), original, placeholder) 
                        for original, _, placeholder in detections]
        text_indices.sort(reverse=True)  # Sort by position in descending order
        
        # Replace PII with placeholders
        for _, original, placeholder in text_indices:
            anonymized_text = anonymized_text.replace(original, placeholder)
        
        return anonymized_text
    
    def restore_text(self, anonymized_text: str) -> str:
        """
        Restore anonymized text by replacing placeholders with original PII.

        Args:
            anonymized_text: The anonymized text with placeholders

        Returns:
            Restored text with original PII
        """
        if not isinstance(anonymized_text, str):
            return anonymized_text

        restored_text = anonymized_text

        # Find all placeholders - both UUID-style and semantic aliases
        # UUID-style: <EMAIL_a1b2c3d4>
        uuid_pattern = r'<[A-Z_]+_[0-9a-f]{8}>'
        # Semantic aliases: ACME_CORP, JOHN_DOE, etc.
        semantic_pattern = r'\b[A-Z][A-Z_]+[A-Z]\b'

        # Collect all matches
        all_matches = []
        all_matches.extend([(m.span(), m.group(0)) for m in re.finditer(uuid_pattern, restored_text)])
        all_matches.extend([(m.span(), m.group(0)) for m in re.finditer(semantic_pattern, restored_text)])

        # Sort by position (reversed) to avoid offset issues
        all_matches.sort(key=lambda x: x[0][0], reverse=True)

        # Process in reverse order
        for (start, end), placeholder in all_matches:
            # Replace placeholder with original PII if it exists in our map
            if placeholder in self.reverse_map:
                original = self.reverse_map[placeholder]
                restored_text = restored_text[:start] + original + restored_text[end:]

        return restored_text
    
    def save_mapping(self, filename: str) -> None:
        """
        Save the PII mapping to a JSON file.
        
        Args:
            filename: The output file path
        """
        mapping_data = {
            "pii_to_placeholder": self.pii_map,
            "placeholder_to_pii": self.reverse_map
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Mapping saved to {filename}")
    
    def load_mapping(self, filename: str) -> None:
        """
        Load a PII mapping from a JSON file.
        
        Args:
            filename: The input file path
        """
        with open(filename, 'r', encoding='utf-8') as f:
            mapping_data = json.load(f)
        
        self.pii_map = mapping_data.get("pii_to_placeholder", {})
        self.reverse_map = mapping_data.get("placeholder_to_pii", {})
        
        logger.info(f"Loaded mapping from {filename} with {len(self.pii_map)} entries")
    
    def get_mapping(self) -> Dict[str, str]:
        """Get the PII to placeholder mapping."""
        return self.pii_map
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about the detected PII.
        
        Returns:
            Dictionary with counts of different PII types
        """
        from collections import defaultdict
        
        stats = defaultdict(int)
        
        for placeholder in self.reverse_map:
            # Extract PII type from placeholder (format: <TYPE_uuid>)
            try:
                pii_type = placeholder.split('_')[0].strip('<')
                stats[pii_type] += 1
            except (IndexError, AttributeError):
                stats['UNKNOWN'] += 1
        
        stats['TOTAL'] = len(self.pii_map)
        return dict(stats)


class DocumentHandler(ABC):
    """
    Abstract base class for document handlers.
    Each specific document type should implement this interface.
    """
    
    def __init__(self, pii_manager: PIIManager):
        """
        Initialize the document handler.
        
        Args:
            pii_manager: The PII manager to use for detection and anonymization
        """
        self.pii_manager = pii_manager
    
    @abstractmethod
    def can_handle(self, file_path: str) -> bool:
        """
        Check if this handler can process the given file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if this handler can process the file, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extract text content from the document.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Extracted text content
        """
        pass
    
    @abstractmethod
    def anonymize(self, input_path: str, output_path: str) -> None:
        """
        Anonymize the document and save the result.
        
        Args:
            input_path: Path to the input file
            output_path: Path to save the anonymized output
        """
        pass
    
    @abstractmethod
    def restore(self, anonymized_path: str, output_path: str) -> None:
        """
        Restore an anonymized document to its original form.
        
        Args:
            anonymized_path: Path to the anonymized file
            output_path: Path to save the restored output
        """
        pass


class DocumentProcessor:
    """
    Main document processor that delegates to appropriate handlers
    based on document type.
    """
    
    def __init__(self, pii_manager: Optional[PIIManager] = None):
        """
        Initialize the document processor.
        
        Args:
            pii_manager: PII manager for detection and anonymization
        """
        self.pii_manager = pii_manager or PIIManager()
        self.handlers = []  # List of document handlers
    
    def register_handler(self, handler: DocumentHandler) -> None:
        """
        Register a document handler.
        
        Args:
            handler: The document handler to register
        """
        self.handlers.append(handler)
        logger.info(f"Registered handler: {handler.__class__.__name__}")
    
    def get_handler_for_file(self, file_path: str) -> Optional[DocumentHandler]:
        """
        Get the appropriate handler for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            The appropriate document handler, or None if no handler is found
        """
        for handler in self.handlers:
            if handler.can_handle(file_path):
                logger.info(f"Using {handler.__class__.__name__} for {file_path}")
                return handler
        
        logger.warning(f"No handler found for {file_path}")
        return None
    
    def anonymize_document(self, input_path: str, output_path: str) -> bool:
        """
        Anonymize a document.
        
        Args:
            input_path: Path to the input file
            output_path: Path to save the anonymized output
            
        Returns:
            True if successful, False otherwise
        """
        handler = self.get_handler_for_file(input_path)
        if not handler:
            return False
        
        try:
            handler.anonymize(input_path, output_path)
            return True
        except Exception as e:
            logger.error(f"Error anonymizing {input_path}: {str(e)}")
            return False
    
    def restore_document(self, anonymized_path: str, output_path: str) -> bool:
        """
        Restore an anonymized document.
        
        Args:
            anonymized_path: Path to the anonymized file
            output_path: Path to save the restored output
            
        Returns:
            True if successful, False otherwise
        """
        handler = self.get_handler_for_file(anonymized_path)
        if not handler:
            return False
        
        try:
            handler.restore(anonymized_path, output_path)
            return True
        except Exception as e:
            logger.error(f"Error restoring {anonymized_path}: {str(e)}")
            return False
    
    def save_mapping(self, mapping_path: str) -> None:
        """
        Save the PII mapping to a file.
        
        Args:
            mapping_path: Path to save the mapping
        """
        self.pii_manager.save_mapping(mapping_path)
    
    def load_mapping(self, mapping_path: str) -> None:
        """
        Load a PII mapping from a file.
        
        Args:
            mapping_path: Path to the mapping file
        """
        self.pii_manager.load_mapping(mapping_path)
    
    def process_batch(self, input_dir: str, output_dir: str, mapping_path: str, 
                      action: str = 'anonymize') -> Dict[str, List[str]]:
        """
        Process a batch of documents.
        
        Args:
            input_dir: Directory containing input files
            output_dir: Directory to save output files
            mapping_path: Path to save/load the mapping file
            action: 'anonymize' or 'restore'
            
        Returns:
            Dictionary with lists of successful and failed files
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        results = {
            'successful': [],
            'failed': []
        }
        
        # Load mapping if restoring and the mapping file exists
        if action == 'restore' and os.path.exists(mapping_path):
            self.load_mapping(mapping_path)
        
        # Process files
        for filename in os.listdir(input_dir):
            input_path = os.path.join(input_dir, filename)
            
            # Skip directories
            if not os.path.isfile(input_path):
                continue
            
            output_path = os.path.join(output_dir, filename)
            
            # Process the file
            success = False
            if action == 'anonymize':
                success = self.anonymize_document(input_path, output_path)
            elif action == 'restore':
                success = self.restore_document(input_path, output_path)
            
            # Record result
            if success:
                results['successful'].append(filename)
            else:
                results['failed'].append(filename)
        
        # Save mapping if anonymizing
        if action == 'anonymize':
            self.save_mapping(mapping_path)
        
        return results