#!/usr/bin/env python3
"""
Validation script for real-world PII test dataset.

This script verifies that:
1. All character positions (start/end) match the actual text
2. Entity counts match metadata
3. No overlapping entities
4. All referenced files exist
"""

import json
import os
from pathlib import Path
from collections import Counter

def validate_ground_truth(ground_truth_path):
    """Validate the ground truth annotations."""

    # Load ground truth
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    print(f"Loaded {len(ground_truth)} documents from ground truth\n")

    total_errors = 0
    total_entities = 0
    entity_type_counts = Counter()

    for doc in ground_truth:
        doc_id = doc['document_id']
        print(f"\n{'='*60}")
        print(f"Validating: {doc_id}")
        print(f"{'='*60}")

        errors = []

        # 1. Validate text file exists
        text_file = Path(ground_truth_path).parent / f"{doc_id}.txt"
        if not text_file.exists():
            errors.append(f"ERROR: Text file not found: {text_file}")

        # 2. Validate entity positions
        text = doc['text']
        entities = doc['pii_entities']

        for i, entity in enumerate(entities):
            # Check character positions
            start = entity['start']
            end = entity['end']
            expected_text = entity['text']
            actual_text = text[start:end]

            if actual_text != expected_text:
                errors.append(
                    f"  Entity {i}: Position mismatch\n"
                    f"    Expected: '{expected_text}'\n"
                    f"    Actual:   '{actual_text}'\n"
                    f"    Position: [{start}:{end}]"
                )

            # Track entity types
            entity_type_counts[entity['type']] += 1
            total_entities += 1

        # 3. Check for overlapping entities
        sorted_entities = sorted(entities, key=lambda x: x['start'])
        for i in range(len(sorted_entities) - 1):
            if sorted_entities[i]['end'] > sorted_entities[i+1]['start']:
                errors.append(
                    f"  OVERLAP: Entities {i} and {i+1} overlap\n"
                    f"    {sorted_entities[i]['text']} [{sorted_entities[i]['start']}:{sorted_entities[i]['end']}]\n"
                    f"    {sorted_entities[i+1]['text']} [{sorted_entities[i+1]['start']}:{sorted_entities[i+1]['end']}]"
                )

        # 4. Validate metadata counts
        metadata_count = doc['metadata']['total_pii_count']
        actual_count = len(entities)
        if metadata_count != actual_count:
            errors.append(
                f"  COUNT MISMATCH: Metadata says {metadata_count}, "
                f"but found {actual_count} entities"
            )

        # Report results for this document
        if errors:
            print(f"❌ FAILED - {len(errors)} error(s):")
            for error in errors:
                print(error)
            total_errors += len(errors)
        else:
            print(f"✅ PASSED - {len(entities)} entities validated")
            print(f"   Source: {doc.get('source_url', 'N/A')}")
            print(f"   Industry: {doc['metadata'].get('industry', 'N/A')}")

    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total Documents: {len(ground_truth)}")
    print(f"Total Entities:  {total_entities}")
    print(f"Total Errors:    {total_errors}")

    print(f"\nEntity Type Distribution:")
    for entity_type, count in sorted(entity_type_counts.items()):
        print(f"  {entity_type:12s}: {count:3d} ({count/total_entities*100:5.1f}%)")

    if total_errors == 0:
        print(f"\n{'='*60}")
        print("✅ ALL VALIDATIONS PASSED!")
        print(f"{'='*60}")
        return True
    else:
        print(f"\n{'='*60}")
        print(f"❌ VALIDATION FAILED - {total_errors} error(s) found")
        print(f"{'='*60}")
        return False

def main():
    """Main validation function."""
    script_dir = Path(__file__).parent
    ground_truth_path = script_dir / "ground_truth.json"

    if not ground_truth_path.exists():
        print(f"ERROR: Ground truth file not found: {ground_truth_path}")
        return False

    success = validate_ground_truth(ground_truth_path)
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
