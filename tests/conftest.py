"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
from typing import Dict, Any
from unittest.mock import Mock

from src.config.settings import AITesterConfig, QuestionSourceConfig, OutputDestinationConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return AITesterConfig(
        base_url="https://test.example.com",
        endpoint="/conversation",
        debug=False,
        question_source=QuestionSourceConfig(
            source_type="dummy",
            file_path="test_questions.yml"
        ),
        output_destination=OutputDestinationConfig(
            destination_type="console",
            file_path=None
        )
    )


@pytest.fixture
def temp_yaml_file():
    """Create a temporary YAML file with test questions."""
    yaml_content = """
- "What is the capital of France?"
- "How do you reverse a string in Python?"
- "What is machine learning?"
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write(yaml_content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def sample_ai_response():
    """Sample AI endpoint response for testing."""
    return [
        '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
        '{"response": "This is a test response from the AI endpoint."}'
    ]


@pytest.fixture
def mock_requests_response():
    """Mock requests response for testing HTTP calls."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_response.text = '\n'.join([
        '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
        '{"response": "This is a test response from the AI endpoint."}'
    ])
    return mock_response


@pytest.fixture
def env_vars():
    """Environment variables for testing."""
    return {
        'AI_TESTER_BASE_URL': 'https://test.example.com',
        'AI_TESTER_SCHEDULE': '0 */5 * * * *',
        'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'yaml',
        'AI_TESTER_QUESTIONS_FILE': './questions.yml',
        'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'json',
        'AI_TESTER_DEBUG': 'false'
    }