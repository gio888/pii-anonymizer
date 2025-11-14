# Real-World PII Test Dataset

## Overview

This directory contains a manually annotated dataset of real-world press releases for evaluating PII (Personally Identifiable Information) detection and anonymization systems. All documents are publicly available press releases from reputable organizations.

## Dataset Composition

**Total Documents:** 7
**Total PII Entities:** 228
**Date Created:** 2025-11-14
**Source Type:** Corporate press releases (CEO appointments, executive transitions)

### Documents

| ID | Source | Industry | PII Count | Key Features |
|----|--------|----------|-----------|--------------|
| realworld_001 | Bio X Cell | Biotechnology | 41 | Phone, email, URL, company names |
| realworld_002 | CISOs Connect | Cybersecurity | 30 | Phone, email, multiple executives |
| realworld_003 | Envista Holdings | Healthcare/Dental | 37 | Phone, email, full address |
| realworld_004 | Vanguard | Financial Services | 32 | Multiple organizations, dates |
| realworld_005 | Estée Lauder | Beauty/Consumer Goods | 26 | International names, brands |
| realworld_006 | Neonode | Technology | 31 | Phone, email, international |
| realworld_007 | AbbVie | Pharmaceutical | 31 | Financial data, dates |

### PII Type Distribution

| PII Type | Count | Description |
|----------|-------|-------------|
| PERSON | 76 | Individual names (executives, contacts) |
| ORG | 93 | Companies, organizations, institutions |
| GPE | 26 | Geographical locations (cities, states, countries) |
| DATE | 43 | Specific dates and years |
| EMAIL | 5 | Email addresses |
| PHONE | 5 | Phone numbers (various formats) |
| ADDRESS | 2 | Physical addresses |
| URL | 1 | Website URLs |
| PRODUCT | 2 | Product/brand names |

## File Structure

```
realworld/
├── README.md                    # This file
├── ground_truth.json            # Comprehensive annotations
├── realworld_001.txt            # Bio X Cell press release
├── realworld_002.txt            # CISOs Connect press release
├── realworld_003.txt            # Envista Holdings press release
├── realworld_004.txt            # Vanguard press release
├── realworld_005.txt            # Estée Lauder press release
├── realworld_006.txt            # Neonode press release
└── realworld_007.txt            # AbbVie press release
```

## Ground Truth Format

The `ground_truth.json` file contains manually annotated PII entities for each document:

```json
[
  {
    "document_id": "realworld_001",
    "source_url": "https://...",
    "text": "Full document text...",
    "pii_entities": [
      {
        "text": "John Smith",
        "type": "PERSON",
        "start": 10,
        "end": 20
      }
    ],
    "metadata": {
      "fetched_at": "2025-11-14T00:00:00Z",
      "total_pii_count": 41,
      "source_type": "press_release",
      "industry": "biotechnology"
    }
  }
]
```

### Entity Types

- **PERSON**: Individual names (e.g., "Christopher Conway", "Klaus Lubbe")
- **ORG**: Organizations, companies, institutions (e.g., "Bio X Cell, LLC", "McKinsey & Company")
- **GPE**: Geopolitical entities - cities, states, countries (e.g., "LEBANON", "California", "Stockholm")
- **DATE**: Dates and temporal expressions (e.g., "Aug. 12, 2024", "2008", "February")
- **EMAIL**: Email addresses (e.g., "connor@thatsnice.com")
- **PHONE**: Phone numbers (e.g., "+1 212 366 4455", "(714) 817-7000")
- **ADDRESS**: Physical addresses (e.g., "200 S. Kraemer Blvd., Building E")
- **URL**: Web URLs (e.g., "https://bioxcell.com/")
- **PRODUCT**: Product or brand names (e.g., "The Ordinary", "Security Shark Tank")

## Annotation Methodology

### Quality Standards

1. **Completeness**: ALL PII instances are annotated, including repeated occurrences
2. **Precision**: Character positions (start/end) are exact and validated
3. **Consistency**: Same entity types used consistently across all documents
4. **Verification**: Each annotation manually verified against source text

### Annotation Rules

1. **Names**: Full names annotated as single PERSON entity (e.g., "Robert A. Michael")
2. **Abbreviations**: State abbreviations marked as GPE (e.g., "N.H.", "PA", "CA")
3. **Companies**: Full legal names when present (e.g., "Bio X Cell, LLC")
4. **Dates**: Various formats captured (e.g., "Aug. 12, 2024", "2008", "July 31, 2024")
5. **Phone Numbers**: All formats including international (e.g., "+46 703 97 21 09")
6. **Email**: Complete email addresses as single entity
7. **Addresses**: Multi-line addresses annotated as single ADDRESS entity when appropriate

### Edge Cases Handled

- **Repeated Names**: Same person mentioned multiple times - all instances annotated
- **Partial Names**: First name only references still annotated as PERSON
- **Abbreviated Organizations**: Both full names and abbreviations annotated (e.g., "AMRI/Curia")
- **Compound Locations**: Multi-word locations as single GPE (e.g., "NEW YORK", "NORTH CHICAGO")

## Usage Examples

### Python - Load and Validate

```python
import json

# Load ground truth
with open('ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

# Access specific document
doc = ground_truth[0]
print(f"Document: {doc['document_id']}")
print(f"Total PII: {doc['metadata']['total_pii_count']}")

# Validate entity positions
for entity in doc['pii_entities']:
    extracted = doc['text'][entity['start']:entity['end']]
    assert extracted == entity['text'], f"Mismatch: {extracted} != {entity['text']}"
    print(f"{entity['type']}: {entity['text']}")
```

### Evaluation Metrics

```python
def evaluate_pii_detection(predicted_entities, ground_truth_entities):
    """
    Compare predicted entities against ground truth.

    Args:
        predicted_entities: List of predicted entities
        ground_truth_entities: List of ground truth entities

    Returns:
        dict: Precision, recall, F1 scores
    """
    # Exact match: same text, type, start, and end
    true_positives = 0

    for pred in predicted_entities:
        for gt in ground_truth_entities:
            if (pred['text'] == gt['text'] and
                pred['type'] == gt['type'] and
                pred['start'] == gt['start'] and
                pred['end'] == gt['end']):
                true_positives += 1
                break

    precision = true_positives / len(predicted_entities) if predicted_entities else 0
    recall = true_positives / len(ground_truth_entities) if ground_truth_entities else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'true_positives': true_positives,
        'false_positives': len(predicted_entities) - true_positives,
        'false_negatives': len(ground_truth_entities) - true_positives
    }
```

### Test PII Anonymization

```python
from pii_anonymizer.document_processor import PIIManager, PiiConfig

# Load a test document
with open('realworld_001.txt', 'r') as f:
    text = f.read()

# Anonymize
pii_manager = PIIManager(PiiConfig())
anonymized = pii_manager.anonymize_text(text)

# Load ground truth
with open('ground_truth.json', 'r') as f:
    ground_truth = json.load(f)

doc_gt = next(d for d in ground_truth if d['document_id'] == 'realworld_001')

# Compare detected entities
detected = pii_manager.detect_pii_in_text(text)
metrics = evaluate_pii_detection(detected, doc_gt['pii_entities'])

print(f"Precision: {metrics['precision']:.2%}")
print(f"Recall: {metrics['recall']:.2%}")
print(f"F1 Score: {metrics['f1']:.2%}")
```

## Dataset Characteristics

### Strengths

1. **Real-world content**: Authentic corporate communications, not synthetic data
2. **Diverse PII types**: 9 different entity types across multiple categories
3. **Professional writing**: Well-formatted, grammatically correct text
4. **Industry variety**: 7 different industries represented
5. **Contact information**: Real-world examples of phones, emails, addresses
6. **International scope**: Multiple countries, phone formats, naming conventions
7. **Manual verification**: Every annotation manually created and verified

### Limitations

1. **Domain specificity**: All press releases, may not generalize to other text types
2. **Formal language**: Professional communications, not casual or social media text
3. **English only**: All documents in English
4. **Limited sensitive PII**: No SSNs, credit cards, or highly sensitive data types
5. **Small scale**: 7 documents, suitable for testing but not large-scale ML training

## Test Scenarios

This dataset is ideal for testing:

1. **Named Entity Recognition (NER)**: Person, organization, location detection
2. **Contact Information Extraction**: Emails, phones, addresses
3. **Date/Time Extraction**: Various date formats
4. **PII Anonymization**: Replace sensitive info with placeholders
5. **De-identification Accuracy**: Ensure all PII is detected
6. **Format Preservation**: Maintain document structure during anonymization

## Citation

If you use this dataset in your research or testing, please cite:

```
Real-World PII Test Dataset for Anonymization Systems
Created: 2025-11-14
Source: Publicly available corporate press releases
Annotations: Manually verified character-level annotations
```

## Sources and Attribution

All documents are publicly available press releases from:

- **Bio X Cell** - https://www.prnewswire.com/news-releases/bio-x-cell-announces-ceo-appointment-302219367.html
- **CISOs Connect** - https://www.prnewswire.com/news-releases/cisos-connect-announces-three-new-appointments-to-meet-needs-of-growing-cybersecurity-executive-community-302211035.html
- **Envista Holdings** - https://investors.envistaco.com/2024-04-15-Envista-Announces-CEO-Appointment
- **Vanguard** - https://corporate.vanguard.com/content/corporatesite/us/en/corp/who-we-are/pressroom/press-release-vanguard-announces-appointment-salim-ramji-new-ceo-05142024.html
- **Estée Lauder** - https://www.elcompanies.com/en/news-and-media/newsroom/press-releases/2024/10-30-2024-103030698
- **Neonode** - https://www.prnewswire.com/news-releases/neonode-announces-appointment-of-new-president-and-ceo-302409296.html
- **AbbVie** - https://www.prnewswire.com/news-releases/abbvie-announces-appointment-of-robert-a-michael-as-chief-executive-officer-302066116.html

## Updates and Maintenance

- **Version**: 1.0
- **Last Updated**: 2025-11-14
- **Maintainer**: PII Anonymizer Project

## License

The original press releases are copyrighted by their respective companies. This dataset is provided for testing and evaluation purposes only. Annotations are provided under MIT License for research and development use.
