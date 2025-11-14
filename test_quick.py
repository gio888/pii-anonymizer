#!/usr/bin/env python3
"""
Quick test script to verify PII anonymizer functionality.
"""
import sys
import os

# Add src directory to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from pii_anonymizer.document_processor import PIIManager, PiiConfig

def test_basic_anonymization():
    """Test basic anonymization with semantic aliases."""
    print("=" * 70)
    print("Testing PII Anonymization")
    print("=" * 70)

    # Sample text with PII
    sample_text = """
    John Smith from Microsoft contacted jane.doe@company.com at (555) 123-4567.
    The price is $1,250.00 and the server IP is 192.168.1.100.
    He works at Acme Corporation on the CloudSync Pro product.
    """

    print("\n📝 Original Text:")
    print(sample_text)

    # Initialize PII Manager with semantic aliases and NER
    print("\n🔄 Initializing PII Manager with semantic aliases and NER...")
    pii_manager = PIIManager(use_semantic_aliases=True, use_ner=True)

    # Anonymize
    print("\n🔒 Anonymizing...")
    anonymized = pii_manager.anonymize_text(sample_text)

    print("\n✅ Anonymized Text:")
    print(anonymized)

    # Show mapping
    print("\n🗂️  PII Mapping:")
    for original, placeholder in pii_manager.pii_map.items():
        print(f"   {original:<30} → {placeholder}")

    # Restore
    print("\n🔓 Restoring...")
    restored = pii_manager.restore_text(anonymized)

    print("\n✅ Restored Text:")
    print(restored)

    # Verify restoration
    if restored.strip() == sample_text.strip():
        print("\n✅ SUCCESS: Restoration matches original!")
    else:
        print("\n❌ WARNING: Restoration doesn't match original")

    print("\n📊 Statistics:")
    stats = pii_manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)

if __name__ == '__main__':
    test_basic_anonymization()
