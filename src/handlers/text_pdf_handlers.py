import os
import re
import logging
import tempfile
from typing import Optional

# Import the base classes from the document processor
from ..pii_anonymizer.document_processor import DocumentHandler, PIIManager

# Set up logging
logger = logging.getLogger('pii_anonymizer.handlers')

class TextDocumentHandler(DocumentHandler):
    """Handler for plain text documents."""
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this handler can process the given file."""
        _, ext = os.path.splitext(file_path.lower())
        return ext in ['.txt', '.text', '.md', '.csv', '.tsv']
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from a plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def anonymize(self, input_path: str, output_path: str) -> None:
        """Anonymize a text document."""
        # Extract text
        text = self.extract_text(input_path)
        
        # Anonymize text
        anonymized_text = self.pii_manager.anonymize_text(text)
        
        # Save anonymized text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(anonymized_text)
        
        logger.info(f"Anonymized text document: {input_path} -> {output_path}")
        
        # Log statistics
        stats = self.pii_manager.get_statistics()
        logger.info(f"PII Statistics: {stats}")
    
    def restore(self, anonymized_path: str, output_path: str) -> None:
        """Restore an anonymized text document."""
        # Read anonymized text
        anonymized_text = self.extract_text(anonymized_path)
        
        # Restore text
        restored_text = self.pii_manager.restore_text(anonymized_text)
        
        # Save restored text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored_text)
        
        logger.info(f"Restored text document: {anonymized_path} -> {output_path}")


class PDFDocumentHandler(DocumentHandler):
    """Handler for PDF documents."""
    
    def __init__(self, pii_manager: PIIManager):
        """Initialize the PDF document handler."""
        super().__init__(pii_manager)
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        try:
            import PyPDF2
            logger.info("PyPDF2 is installed.")
        except ImportError:
            logger.warning("PyPDF2 is not installed. Please install it with: pip install PyPDF2")
            logger.warning("PDF handling capabilities will be limited.")
        
        try:
            import pdfplumber
            logger.info("pdfplumber is installed.")
        except ImportError:
            logger.warning("pdfplumber is not installed. Please install it with: pip install pdfplumber")
            logger.warning("PDF handling capabilities will be limited.")
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this handler can process the given file."""
        _, ext = os.path.splitext(file_path.lower())
        return ext == '.pdf'
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from a PDF file."""
        extracted_text = ""
        
        # Try using pdfplumber first (better text extraction)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    extracted_text += page_text + "\n\n"
            
            logger.info(f"Extracted text from PDF using pdfplumber: {file_path}")
            return extracted_text
        except ImportError:
            logger.warning("pdfplumber not available, falling back to PyPDF2")
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {str(e)}")
            logger.warning("Falling back to PyPDF2")
        
        # Fall back to PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    page_text = page.extract_text() or ""
                    extracted_text += page_text + "\n\n"
            
            logger.info(f"Extracted text from PDF using PyPDF2: {file_path}")
            return extracted_text
        except ImportError:
            logger.error("PyPDF2 is not installed. Cannot extract text from PDF.")
            raise ImportError("PyPDF2 is required for PDF processing.")
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {str(e)}")
            raise
    
    def anonymize(self, input_path: str, output_path: str) -> None:
        """Anonymize a PDF document."""
        # Extract text
        text = self.extract_text(input_path)

        # Anonymize text
        anonymized_text = self.pii_manager.anonymize_text(text)

        # Save as markdown file for LLM processing
        if not output_path.endswith('.md'):
            output_path = output_path.rsplit('.', 1)[0] + '.md'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(anonymized_text)
        logger.info(f"Saved anonymized markdown version: {output_path}")

        # Log statistics
        stats = self.pii_manager.get_statistics()
        logger.info(f"PII Statistics: {stats}")
    
    def restore(self, anonymized_path: str, output_path: str) -> None:
        """Restore an anonymized PDF document."""
        # For PDF files, we restore from the .md version
        md_path = anonymized_path
        if not md_path.endswith('.md'):
            md_path = anonymized_path.rsplit('.', 1)[0] + '.md'
            if not os.path.exists(md_path):
                logger.error(f"Cannot find markdown version of anonymized PDF: {md_path}")
                raise FileNotFoundError(f"Markdown version not found: {md_path}")

        # Read anonymized text
        with open(md_path, 'r', encoding='utf-8') as f:
            anonymized_text = f.read()

        # Restore text
        restored_text = self.pii_manager.restore_text(anonymized_text)

        # Save as markdown file
        if not output_path.endswith('.md'):
            output_path = output_path.rsplit('.', 1)[0] + '.md'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored_text)

        logger.info(f"Restored text from PDF: {anonymized_path} -> {output_path}")