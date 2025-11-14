# PII Anonymizer Tests

This directory contains unit tests for the PII Anonymizer project. These tests verify the functionality of the core components and ensure that everything works as expected.

## Test Structure

The test suite is organized as follows:

- `test_pii_manager.py`: Tests for the PII detection and management functionality
- `test_document_processor.py`: Tests for the document processing core
- `test_text_handler.py`: Tests for the text document handler

## Prerequisites

Before running the tests, ensure you have installed all the required dependencies:

```bash
pip install -r ../requirements.txt
```

For running the PDF handler tests, you'll need additional dependencies:

```bash
pip install PyPDF2 pdfplumber reportlab
```

## Running the Tests

### Running All Tests

To run all tests, use the following command from the project root directory:

```bash
python -m unittest discover -s tests
```

### Running Specific Tests

To run a specific test file:

```bash
python -m unittest tests/test_pii_manager.py
```

To run a specific test case:

```bash
python -m unittest tests.test_pii_manager.TestPIIManager
```

To run a specific test method:

```bash
python -m unittest tests.test_pii_manager.TestPIIManager.test_anonymize_text
```

## Test Coverage

To measure test coverage, you can use the `coverage` tool:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run -m unittest discover -s tests

# Generate coverage report
coverage report -m

# Generate HTML report
coverage html
```

The HTML report will be available in the `htmlcov` directory.

## Writing New Tests

When adding new functionality to the project, please add corresponding tests. Tests should:

1. Be independent and not rely on the execution order
2. Clean up after themselves (e.g., remove temporary files)
3. Cover both success and failure scenarios
4. Include comments explaining the purpose of each test

Example of a well-structured test method:

```python
def test_function_name(self):
    """Test that function_name behaves as expected."""
    # Arrange: Set up the test
    input_data = "some input"
    expected_output = "expected result"
    
    # Act: Execute the function
    actual_output = function_name(input_data)
    
    # Assert: Verify the result
    self.assertEqual(actual_output, expected_output)
```

## Troubleshooting

If you encounter issues running the tests:

1. Ensure your Python environment has all the required dependencies.
2. Make sure you're running the tests from the project root directory.
3. Check for import errors that might indicate incorrect import paths.
4. Verify that any test fixtures (like sample files) are correctly set up.

## CI/CD Integration

These tests are integrated with our CI/CD pipeline. Any pull requests must pass all tests before being merged.