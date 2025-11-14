import os
import re
import json
import logging
import tempfile
from typing import Optional, Dict, Any, List, Tuple

# Import the base classes from the document processor
from ..pii_anonymizer.document_processor import DocumentHandler, PIIManager

# Set up logging
logger = logging.getLogger('pii_anonymizer.google_handlers')

class GoogleDocsHandler(DocumentHandler):
    """Handler for Google Docs documents."""
    
    def __init__(self, pii_manager: PIIManager, credentials_path: Optional[str] = None):
        """
        Initialize the Google Docs handler.
        
        Args:
            pii_manager: The PII manager to use
            credentials_path: Path to Google API credentials file
        """
        super().__init__(pii_manager)
        self.credentials_path = credentials_path
        self._check_dependencies()
        self.service = None
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            
            logger.info("Google API dependencies are installed.")
        except ImportError:
            logger.warning("Google API dependencies not found. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            logger.warning("Google Docs handling will not be available.")
    
    def _initialize_service(self) -> None:
        """Initialize the Google Docs API service."""
        if self.service:
            return
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import pickle
            import os
            
            # Define the API scopes
            SCOPES = [
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/drive.readonly',
            ]
            
            creds = None
            # Check if token file exists
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no valid credentials, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if self.credentials_path and os.path.exists(self.credentials_path):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        raise ValueError("Credentials file not found. Please provide a valid credentials file path.")
                
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the service
            self.service = build('docs', 'v1', credentials=creds)
            logger.info("Google Docs API service initialized.")
        
        except Exception as e:
            logger.error(f"Error initializing Google Docs API service: {str(e)}")
            raise
    
    def _extract_url_id(self, file_path: str) -> str:
        """
        Extract the document ID from a Google Docs URL.
        
        Args:
            file_path: Google Docs URL or path
            
        Returns:
            Document ID
        """
        # Check if the file_path is a URL
        if file_path.startswith('https://docs.google.com/document/d/'):
            # Extract document ID from URL
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', file_path)
            if match:
                return match.group(1)
        
        # If not a URL, assume it's a document ID
        return file_path
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this handler can process the given file."""
        # Check if it's a Google Docs URL
        if file_path.startswith('https://docs.google.com/document/d/'):
            return True
        
        # Check if it's a Google Docs ID (string of letters and digits)
        if re.match(r'^[a-zA-Z0-9-_]+$', file_path) and not os.path.exists(file_path):
            return True
        
        return False
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a Google Docs document.
        
        Args:
            file_path: Path to or URL of the Google Docs document
            
        Returns:
            Extracted text content
        """
        self._initialize_service()
        doc_id = self._extract_url_id(file_path)
        
        try:
            # Retrieve the document contents
            document = self.service.documents().get(documentId=doc_id).execute()
            
                            # Extract text from the document
            text_content = ""
            for content in document.get('body', {}).get('content', []):
                if 'paragraph' in content:
                    paragraph = content.get('paragraph', {})
                    for element in paragraph.get('elements', []):
                        if 'textRun' in element:
                            text_content += element.get('textRun', {}).get('content', '')
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from Google Docs: {str(e)}")
            raise
    
    def anonymize(self, input_path: str, output_path: str) -> None:
        """
        Anonymize a Google Docs document.
        
        Args:
            input_path: Path to or URL of the Google Docs document
            output_path: Path to save the anonymized content
        """
        # Extract text
        text = self.extract_text(input_path)
        
        # Anonymize text
        anonymized_text = self.pii_manager.anonymize_text(text)
        
        # Save anonymized text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(anonymized_text)
        
        logger.info(f"Anonymized Google Docs document: {input_path} -> {output_path}")
        
        # Log statistics
        stats = self.pii_manager.get_statistics()
        logger.info(f"PII Statistics: {stats}")
    
    def restore(self, anonymized_path: str, output_path: str) -> None:
        """
        Restore an anonymized Google Docs text file.
        
        Args:
            anonymized_path: Path to the anonymized text file
            output_path: Path to save the restored content
        """
        # Read anonymized text
        with open(anonymized_path, 'r', encoding='utf-8') as f:
            anonymized_text = f.read()
        
        # Restore text
        restored_text = self.pii_manager.restore_text(anonymized_text)
        
        # Save restored text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored_text)
        
        logger.info(f"Restored Google Docs document: {anonymized_path} -> {output_path}")


class GoogleSheetsHandler(DocumentHandler):
    """Handler for Google Sheets documents."""
    
    def __init__(self, pii_manager: PIIManager, credentials_path: Optional[str] = None):
        """
        Initialize the Google Sheets handler.
        
        Args:
            pii_manager: The PII manager to use
            credentials_path: Path to Google API credentials file
        """
        super().__init__(pii_manager)
        self.credentials_path = credentials_path
        self._check_dependencies()
        self.service = None
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are installed."""
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            
            logger.info("Google API dependencies are installed.")
        except ImportError:
            logger.warning("Google API dependencies not found. Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            logger.warning("Google Sheets handling will not be available.")
    
    def _initialize_service(self) -> None:
        """Initialize the Google Sheets API service."""
        if self.service:
            return
        
        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            import pickle
            import os
            
            # Define the API scopes
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly',
            ]
            
            creds = None
            # Check if token file exists
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no valid credentials, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if self.credentials_path and os.path.exists(self.credentials_path):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.credentials_path, SCOPES)
                        creds = flow.run_local_server(port=0)
                    else:
                        raise ValueError("Credentials file not found. Please provide a valid credentials file path.")
                
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Google Sheets API service initialized.")
        
        except Exception as e:
            logger.error(f"Error initializing Google Sheets API service: {str(e)}")
            raise
    
    def _extract_url_id(self, file_path: str) -> str:
        """
        Extract the spreadsheet ID from a Google Sheets URL.
        
        Args:
            file_path: Google Sheets URL or path
            
        Returns:
            Spreadsheet ID
        """
        # Check if the file_path is a URL
        if file_path.startswith('https://docs.google.com/spreadsheets/d/'):
            # Extract spreadsheet ID from URL
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', file_path)
            if match:
                return match.group(1)
        
        # If not a URL, assume it's a spreadsheet ID
        return file_path
    
    def can_handle(self, file_path: str) -> bool:
        """Check if this handler can process the given file."""
        # Check if it's a Google Sheets URL
        if file_path.startswith('https://docs.google.com/spreadsheets/d/'):
            return True
        
        # Check if it's a Google Sheets ID (string of letters and digits)
        if re.match(r'^[a-zA-Z0-9-_]+
                , file_path) and not os.path.exists(file_path):
            return True
        
        return False
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from a Google Sheets document.
        
        Args:
            file_path: Path to or URL of the Google Sheets document
            
        Returns:
            Extracted text content in CSV format
        """
        self._initialize_service()
        sheet_id = self._extract_url_id(file_path)
        
        try:
            # Get the spreadsheet
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            
            # Initialize text content
            text_content = ""
            
            # Process each sheet
            for sheet in spreadsheet.get('sheets', []):
                sheet_name = sheet.get('properties', {}).get('title', 'Sheet')
                range_name = f"{sheet_name}"
                
                # Get the values for this sheet
                result = self.service.spreadsheets().values().get(
                    spreadsheetId=sheet_id, range=range_name).execute()
                values = result.get('values', [])
                
                # Add sheet name as header
                text_content += f"## {sheet_name}\n"
                
                # Convert to CSV-like format
                for row in values:
                    text_content += ','.join([str(cell) for cell in row]) + '\n'
                
                # Add separator between sheets
                text_content += '\n'
            
            return text_content
            
        except Exception as e:
            logger.error(f"Error extracting text from Google Sheets: {str(e)}")
            raise
    
    def anonymize(self, input_path: str, output_path: str) -> None:
        """
        Anonymize a Google Sheets document.
        
        Args:
            input_path: Path to or URL of the Google Sheets document
            output_path: Path to save the anonymized content
        """
        # Extract text
        text = self.extract_text(input_path)
        
        # Anonymize text
        anonymized_text = self.pii_manager.anonymize_text(text)
        
        # Save anonymized text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(anonymized_text)
        
        logger.info(f"Anonymized Google Sheets document: {input_path} -> {output_path}")
        
        # Also save as CSV for easier processing
        csv_output_path = output_path + ".csv"
        with open(csv_output_path, 'w', encoding='utf-8') as f:
            f.write(anonymized_text)
        
        logger.info(f"Saved CSV version: {csv_output_path}")
        
        # Log statistics
        stats = self.pii_manager.get_statistics()
        logger.info(f"PII Statistics: {stats}")
    
    def restore(self, anonymized_path: str, output_path: str) -> None:
        """
        Restore an anonymized Google Sheets text file.
        
        Args:
            anonymized_path: Path to the anonymized text file
            output_path: Path to save the restored content
        """
        # Read anonymized text
        with open(anonymized_path, 'r', encoding='utf-8') as f:
            anonymized_text = f.read()
        
        # Restore text
        restored_text = self.pii_manager.restore_text(anonymized_text)
        
        # Save restored text
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(restored_text)
        
        logger.info(f"Restored Google Sheets document: {anonymized_path} -> {output_path}")