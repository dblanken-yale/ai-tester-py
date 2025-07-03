# Testing Documentation

## Test Suite Overview

The AI Tester project includes a comprehensive test suite covering all major components of the refactored system.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini              # Pytest configuration
├── requirements-test.txt    # Testing dependencies
├── test_config.py           # Configuration management tests
├── test_question_sources.py # Question source tests
├── test_output_destinations.py # Output destination tests
├── test_file_naming.py      # Smart file naming tests
├── test_question_service.py # Service layer tests
├── test_cli.py              # CLI functionality tests
├── test_azure_function.py   # Azure Function tests
└── test_integration.py      # End-to-end integration tests
```

## Running Tests

### Prerequisites

Install testing dependencies:
```bash
pip install -r requirements-test.txt
```

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/test_config.py

# Run specific test class
python -m pytest tests/test_config.py::TestAITesterConfig

# Run specific test method
python -m pytest tests/test_config.py::TestAITesterConfig::test_default_config_creation
```

### Test Coverage

```bash
# Run tests with coverage
python -m pytest --cov=src

# Generate HTML coverage report
python -m pytest --cov=src --cov-report=html
```

## Test Categories

### Unit Tests

- **Configuration Tests** (`test_config.py`): Test typed configuration classes and environment variable parsing
- **Question Source Tests** (`test_question_sources.py`): Test YAML, dummy, and PostgreSQL question sources
- **Output Destination Tests** (`test_output_destinations.py`): Test JSON, Excel, console, and database outputs
- **File Naming Tests** (`test_file_naming.py`): Test smart file naming utilities
- **Service Tests** (`test_question_service.py`): Test core business logic orchestration

### Integration Tests

- **CLI Tests** (`test_cli.py`): Test command-line interface functionality
- **Azure Function Tests** (`test_azure_function.py`): Test Azure Function timer triggers
- **End-to-End Tests** (`test_integration.py`): Test complete workflows

## Test Fixtures

### Configuration Fixtures

- `sample_config`: Basic configuration for testing
- `env_vars`: Environment variables for testing
- `temp_yaml_file`: Temporary YAML file with test questions

### Mock Fixtures

- `mock_requests_response`: Mock HTTP responses
- `sample_ai_response`: Sample AI endpoint responses

## Current Test Status

As of implementation:
- **60+ tests passing**: Core functionality verified
- **Test coverage**: Comprehensive coverage of key components
- **Remaining work**: Some integration tests need refinement to match exact implementation details

## Test Development Guidelines

### Writing New Tests

1. **Follow naming conventions**: Use descriptive test names that explain the scenario
2. **Use appropriate fixtures**: Leverage shared fixtures for common setup
3. **Mock external dependencies**: Use mocks for HTTP requests, file system operations
4. **Test both success and failure paths**: Include error handling tests
5. **Keep tests isolated**: Each test should be independent

### Test Structure Example

```python
class TestComponentName:
    """Test description for the component."""
    
    def test_method_success_scenario(self, fixture_name):
        """Test successful execution of method."""
        # Arrange
        setup_code()
        
        # Act
        result = method_under_test()
        
        # Assert
        assert result == expected_value
    
    def test_method_error_scenario(self):
        """Test error handling of method."""
        with pytest.raises(ExpectedError):
            method_under_test()
```

### Mocking Guidelines

```python
# Mock external HTTP requests
@patch('module.requests.post')
def test_http_call(self, mock_post):
    mock_post.return_value = Mock(status_code=200, text="response")
    
# Mock file operations
@patch('builtins.open', mock_open(read_data='test data'))
def test_file_read(self):
    result = read_file('test.txt')
    
# Mock environment variables
@patch.dict(os.environ, {'VAR': 'value'})
def test_env_var(self):
    config = load_from_env()
```

## Continuous Integration

### GitHub Actions

The test suite is designed to work with GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: python -m pytest -v --cov=src
```

### Pre-commit Hooks

Consider adding pre-commit hooks to run tests automatically:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: tests
        entry: python -m pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Testing Best Practices

1. **Test Pyramid**: More unit tests, fewer integration tests, minimal end-to-end tests
2. **Fast Feedback**: Keep test execution time under 30 seconds for the full suite
3. **Deterministic Tests**: Avoid flaky tests by properly mocking time-dependent operations
4. **Clear Assertions**: Use descriptive assertion messages
5. **Test Data Management**: Use fixtures for consistent test data

## Troubleshooting Common Issues

### Import Errors

- Ensure `src/` directory is in Python path
- Check that all `__init__.py` files exist
- Verify relative imports are correct

### Mock Issues

- Use `patch` decorators correctly
- Mock at the right level (where objects are used, not where they're defined)
- Check mock call arguments match actual function signatures

### Fixture Problems

- Ensure fixtures are properly scoped (function, class, module, session)
- Use `autouse=True` sparingly
- Clean up resources in fixture teardown

## Future Improvements

1. **Performance Tests**: Add tests for response time and memory usage
2. **Load Tests**: Test behavior under high question volumes
3. **Security Tests**: Validate input sanitization and error handling
4. **Compatibility Tests**: Test across different Python versions
5. **Documentation Tests**: Verify code examples in documentation work