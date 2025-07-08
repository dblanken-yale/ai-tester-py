"""
Tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch

from src.config.settings import AITesterConfig, QuestionSourceConfig, OutputDestinationConfig


class TestAITesterConfig:
    """Test configuration classes."""
    
    def test_default_config_creation(self):
        """Test creating a config with default values."""
        config = AITesterConfig(base_url="https://test.example.com")
        
        assert config.base_url == "https://test.example.com"
        assert config.processing.default_endpoint == "/conversation"
        assert config.debug is False
        assert config.question_source.source_type == "yaml"
        assert config.output_destination.destination_type == "console"
    
    def test_config_with_custom_values(self):
        """Test creating config with custom values."""
        question_source = QuestionSourceConfig(
            source_type="dummy",
            file_path="custom.yml"
        )
        output_dest = OutputDestinationConfig(
            destination_type="excel",
            file_path="output.xlsx"
        )
        
        config = AITesterConfig(
            base_url="https://custom.example.com",
            endpoint="/api/test",
            debug=True,
            question_source=question_source,
            output_destination=output_dest
        )
        
        assert config.base_url == "https://custom.example.com"
        assert config.endpoint == "/api/test"
        assert config.debug is True
        assert config.question_source.source_type == "dummy"
        assert config.output_destination.destination_type == "excel"
    
    @patch.dict(os.environ, {
        'AI_TESTER_BASE_URL': 'https://env.example.com',
        'AI_TESTER_ENDPOINT': '/env/api',
        'AI_TESTER_DEBUG': 'true',
        'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'dummy',
        'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'excel'
    })
    def test_config_from_environment(self):
        """Test creating config from environment variables."""
        config = AITesterConfig.from_environment()
        
        assert config.base_url == "https://env.example.com"
        assert config.endpoint == "/env/api"
        assert config.debug is True
        assert config.question_source.source_type == "dummy"
        assert config.output_destination.destination_type == "excel"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_environment_missing_required(self):
        """Test creating config from environment with missing required values."""
        # Environment config should handle missing base URL gracefully
        # The actual behavior depends on implementation
        config = AITesterConfig.from_environment()
        # This test is implementation-specific - just ensure it doesn't crash
    
    def test_config_from_cli_args(self):
        """Test creating config from CLI arguments."""
        # Mock argparse.Namespace
        class MockArgs:
            url = "https://cli.example.com"
            endpoint = "/cli/api"
            debug = True
            questions = "cli_questions.yml"
            source_type = "yaml"
            format = "excel"
            outfile = "cli_output.xlsx"
            filename = None
        
        args = MockArgs()
        config = AITesterConfig.from_cli_args(args)
        
        assert config.base_url == "https://cli.example.com"
        assert config.endpoint == "/cli/api"
        assert config.debug is True
        assert config.question_source.source_type == "yaml"
        assert config.question_source.file_path == "cli_questions.yml"
        assert config.output_destination.destination_type == "excel"
        assert config.output_destination.file_path == "cli_output.xlsx"


class TestQuestionSourceConfig:
    """Test question source configuration."""
    
    def test_default_question_source_config(self):
        """Test default question source configuration."""
        config = QuestionSourceConfig()
        
        assert config.source_type == "yaml"
        assert config.file_path == "./questions.yml"
        assert config.custom_questions is None
    
    def test_custom_question_source_config(self):
        """Test custom question source configuration."""
        custom_questions = ["Question 1?", "Question 2?"]
        config = QuestionSourceConfig(
            source_type="dummy",
            file_path="custom.yml",
            custom_questions=custom_questions
        )
        
        assert config.source_type == "dummy"
        assert config.file_path == "custom.yml"
        assert config.custom_questions == custom_questions


class TestOutputDestinationConfig:
    """Test output destination configuration."""
    
    def test_default_output_destination_config(self):
        """Test default output destination configuration."""
        config = OutputDestinationConfig()
        
        assert config.destination_type == "console"
        assert config.file_path is None
        assert config.database is None
    
    def test_custom_output_destination_config(self):
        """Test custom output destination configuration."""
        from src.config.settings import DatabaseConfig
        database_config = DatabaseConfig(connection_string="postgresql://test")
        config = OutputDestinationConfig(
            destination_type="json",
            file_path="output.json",
            database=database_config
        )
        
        assert config.destination_type == "json"
        assert config.file_path == "output.json"
        assert config.database == database_config