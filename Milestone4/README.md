# Milestone 4: Testing Suite for IRCTC IVR

This milestone provides a comprehensive testing suite using pytest to validate the IRCTC IVR system's functionality, performance, and reliability.

## Features

- **Unit Tests**: Test individual components and endpoints.
- **Integration Tests**: Validate end-to-end workflows.
- **Error Handling Tests**: Ensure robust error management.
- **Performance Tests**: Measure response times and load handling.
- **E2E Tests**: Simulate full user journeys.

## Setup

1. Install test dependencies:
   ```bash
   pip install -r requirements-text.txt
   ```

2. Run tests:
   ```bash
   pytest
   ```

3. Run specific test files:
   ```bash
   pytest tests/test_error_handling.py
   pytest tests/test_integration.py
   pytest tests/test_performance.py
   pytest tests/tests_e2e.py
   ```

## Test Coverage

- Backend endpoint validation
- Session state management
- PNR, booking, and tracking logic
- Error scenarios and edge cases
- Performance benchmarks

## Files

- `pytest.ini`: Pytest configuration
- `tests/test_error_handling.py`: Error handling tests
- `tests/test_integration.py`: Integration tests
- `tests/test_performance.py`: Performance tests
- `tests/tests_e2e.py`: End-to-end tests
- `requirements-text.txt`: Test dependencies