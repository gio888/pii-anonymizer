"""
Flask web application for PII anonymization with drag-and-drop interface.
"""
import os
import uuid
import json
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Import PII anonymizer components
from pii_anonymizer.document_processor import PIIManager, PiiConfig, DocumentProcessor
from handlers.text_pdf_handlers import TextDocumentHandler, PDFDocumentHandler
from handlers.office_handlers import DocxDocumentHandler, XlsxDocumentHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('pii_anonymizer.webapp')

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='pii_uploads_')
app.config['OUTPUT_FOLDER'] = tempfile.mkdtemp(prefix='pii_outputs_')

# Allowed extensions
ALLOWED_EXTENSIONS = {'txt', 'md', 'csv', 'tsv', 'pdf', 'docx', 'xlsx'}

# Store processing results (in production, use Redis or database)
processing_results = {}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_processor():
    """Set up the document processor with all handlers."""
    # Create PII manager with semantic aliases and NER enabled
    pii_manager = PIIManager(use_semantic_aliases=True, use_ner=True)

    # Create document processor
    processor = DocumentProcessor(pii_manager)

    # Register handlers
    processor.register_handler(TextDocumentHandler(pii_manager))
    processor.register_handler(PDFDocumentHandler(pii_manager))
    processor.register_handler(DocxDocumentHandler(pii_manager))
    processor.register_handler(XlsxDocumentHandler(pii_manager))

    return processor


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and anonymization."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400

        # Generate unique session ID
        session_id = str(uuid.uuid4())

        # Save uploaded file
        filename = secure_filename(file.filename)
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(upload_path)

        logger.info(f"File uploaded: {filename} (session: {session_id})")

        # Process file
        processor = setup_processor()

        # Determine output paths
        output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
        os.makedirs(output_dir, exist_ok=True)

        # Get base name and extension
        base_name = os.path.splitext(filename)[0]
        extension = os.path.splitext(filename)[1]

        # Set output paths based on file type
        if extension.lower() == '.pdf':
            output_file = os.path.join(output_dir, f"{base_name}_anonymized.md")
        elif extension.lower() in ['.docx', '.xlsx']:
            output_file = os.path.join(output_dir, f"{base_name}_anonymized.txt")
        else:
            output_file = os.path.join(output_dir, f"{base_name}_anonymized{extension}")

        mapping_file = os.path.join(output_dir, 'mapping.json')

        # Anonymize the document
        try:
            processor.anonymize_document(upload_path, output_file)
            processor.pii_manager.save_mapping(mapping_file)

            # Also save as CSV for easier viewing
            csv_mapping_file = os.path.join(output_dir, 'mapping.csv')
            save_mapping_as_csv(processor.pii_manager.pii_map, csv_mapping_file)

            logger.info(f"File anonymized successfully: {filename}")

            # Get statistics
            stats = processor.pii_manager.get_statistics()

            # Store results
            processing_results[session_id] = {
                'original_filename': filename,
                'output_file': output_file,
                'mapping_file': mapping_file,
                'csv_mapping_file': csv_mapping_file,
                'stats': stats
            }

            return jsonify({
                'success': True,
                'session_id': session_id,
                'original_filename': filename,
                'stats': stats,
                'message': 'File anonymized successfully'
            })

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}", exc_info=True)
            return jsonify({'error': f'Processing error: {str(e)}'}), 500

    except Exception as e:
        logger.error(f"Upload error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """Download anonymized file or mapping."""
    if session_id not in processing_results:
        return jsonify({'error': 'Session not found'}), 404

    result = processing_results[session_id]

    if file_type == 'anonymized':
        file_path = result['output_file']
        download_name = os.path.basename(file_path)
    elif file_type == 'mapping_json':
        file_path = result['mapping_file']
        download_name = 'mapping.json'
    elif file_type == 'mapping_csv':
        file_path = result['csv_mapping_file']
        download_name = 'mapping.csv'
    else:
        return jsonify({'error': 'Invalid file type'}), 400

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(file_path, as_attachment=True, download_name=download_name)


@app.route('/stats/<session_id>')
def get_stats(session_id):
    """Get processing statistics for a session."""
    if session_id not in processing_results:
        return jsonify({'error': 'Session not found'}), 404

    result = processing_results[session_id]
    return jsonify({
        'success': True,
        'stats': result['stats'],
        'original_filename': result['original_filename']
    })


def save_mapping_as_csv(pii_map, csv_file):
    """Save PII mapping as CSV file."""
    import csv

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Original PII', 'Placeholder/Alias'])
        for original, placeholder in sorted(pii_map.items()):
            writer.writerow([original, placeholder])


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    print("=" * 60)
    print("PII Anonymizer Web Application")
    print("=" * 60)
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Output folder: {app.config['OUTPUT_FOLDER']}")
    print("=" * 60)
    print("Open your browser and navigate to: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='127.0.0.1', port=5000)
