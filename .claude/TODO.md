# TODO List

Last updated: 2025-11-15

## High Priority

- [ ] Integrate phonenumbers library for robust international phone parsing
- [ ] Add common name dictionary for single-word name detection
- [ ] Improve location/GPE detection (Europe, Austin, etc.)
- [ ] Test web application with real documents (all formats)
- [ ] Add error handling for malformed files in web UI
- [ ] Create user guide with screenshots for web interface

## Medium Priority

- [ ] Fine-tune spaCy NER model on domain-specific product/org data
- [ ] Implement confidence scoring to reduce false positives
- [ ] Add optional Ollama integration for improved entity detection
- [ ] Implement file size validation before upload
- [ ] Add session cleanup for temp files older than 24 hours
- [ ] Add support for batch upload in web UI

## Low Priority

- [ ] Add dark mode toggle to web interface
- [ ] Export statistics as downloadable report
- [ ] Add preview pane showing detected PII before anonymization
- [ ] Support for additional currencies (₹, ₽, etc.)

## Completed ✅

- [x] Add all-caps pattern detection for abbreviations (BXC, IBM, 3M, FTSE, NYSE: ABBV) (2025-11-15)
- [x] Add alphanumeric abbreviation detection (3M, F5, 401K) (2025-11-15)
- [x] Add stock ticker pattern detection (NYSE: ABBV, NASDAQ: NEON) (2025-11-15)
- [x] Implement context-aware filtering for abbreviations (2025-11-15)
- [x] Build automated evaluation framework with metrics tracking (2025-11-14)
- [x] Generate synthetic test data (20 docs, 380 PII instances) (2025-11-14)
- [x] Annotate real-world test data (7 docs, 228 PII instances) (2025-11-14)
- [x] Create comprehensive eval test suite (2025-11-14)
- [x] Improve PII detection from 15.84% → 78.03% through 3 iterations (2025-11-14)
- [x] Enhance PHONE regex pattern for international formats (2025-11-14)
- [x] Enhance DATE regex pattern for text-based dates and years (2025-11-14)
- [x] Add pattern-based NER fallback for products/orgs/names (2025-11-14)
- [x] Build web interface with drag-and-drop (2025-11-14)
- [x] Add DOCX and XLSX support (2025-11-14)
- [x] Implement semantic alias generator (2025-11-14)
- [x] Integrate spaCy NER for entity detection (2025-11-14)
- [x] Add CURRENCY and NUMBER patterns (2025-11-14)
- [x] Update documentation with web UI instructions (2025-11-14)
