#!/usr/bin/env python3
"""
Launcher script for PII Anonymizer Web Application.
"""
import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

if __name__ == '__main__':
    from web_app import app

    print("\n" + "=" * 70)
    print(" " * 15 + "🔒 PII ANONYMIZER WEB APPLICATION")
    print("=" * 70)
    print("\n📋 Features:")
    print("   • Drag-and-drop file upload")
    print("   • Support for TXT, MD, CSV, TSV, PDF, DOCX, XLSX")
    print("   • Automatic detection of PII (emails, phones, names, companies, etc.)")
    print("   • Semantic aliases (e.g., ACME_CORP, JOHN_DOE)")
    print("   • Download anonymized documents and mapping files")
    print("\n🚀 Starting server...")
    print("   URL: http://localhost:5000")
    print("\n💡 Tips:")
    print("   • Upload a document using drag-and-drop or file browser")
    print("   • Download both the anonymized file and mapping file")
    print("   • Keep the mapping file secure - it contains the original PII!")
    print("\n⌨️  Press CTRL+C to stop the server")
    print("=" * 70 + "\n")

    app.run(debug=False, host='127.0.0.1', port=5000)
