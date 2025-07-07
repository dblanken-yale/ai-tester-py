"""
Tests for the question processing service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from src.services.question_service import QuestionProcessingService
from src.config.settings import AITesterConfig, QuestionSourceConfig, OutputDestinationConfig
from src.utils.exceptions import ValidationError


class TestQuestionProcessingService:
    """Test the question processing service."""
    
    def test_service_creation(self, sample_config):
        """Test creating a service instance."""
        service = QuestionProcessingService(sample_config)
        
        assert service.config == sample_config
        # Service creates sources and destinations dynamically, not as instance attributes
        assert hasattr(service, '_create_question_source')
        assert hasattr(service, '_create_output_destination')
    
    def test_create_question_source_yaml(self, temp_yaml_file):
        """Test creating a YAML question source."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(
                source_type="yaml",
                file_path=temp_yaml_file
            )
        )
        
        service = QuestionProcessingService(config)
        source = service._create_question_source()
        
        assert source is not None
        assert source.get_source_info()['type'] == 'yaml_file'
    
    def test_create_question_source_dummy(self):
        """Test creating a dummy question source."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy")
        )
        
        service = QuestionProcessingService(config)
        source = service._create_question_source()
        
        assert source is not None
        assert source.get_source_info()['type'] == 'dummy_static'
    
    def test_create_output_destination_json(self):
        """Test creating a JSON output destination."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            output_destination=OutputDestinationConfig(
                destination_type="json",
                file_path="output.json"
            )
        )
        
        service = QuestionProcessingService(config)
        dest = service._create_output_destination()
        
        assert dest is not None
        assert dest.get_destination_info()['type'] == 'json_file'
    
    def test_create_output_destination_console(self):
        """Test creating a console output destination."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            output_destination=OutputDestinationConfig(destination_type="console")
        )
        
        service = QuestionProcessingService(config)
        dest = service._create_output_destination()
        
        assert dest is not None
        assert dest.get_destination_info()['type'] == 'console'
    
    @patch('src.core.processor.requests.post')
    def test_process_questions_integration(self, mock_post, sample_config):
        """Test the complete question processing workflow."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        response_text = '\n'.join([
            '{"choices": [{"messages": [{"content": "{\\"citations\\": [{\\"title\\": \\"Test Source\\", \\"url\\": \\"https://example.com\\"}]}"}]}]}',
            '{"choices": [{"messages": [{"content": "{\\"response\\": \\"This is a test response.\\"}"}]}]}'
        ])
        mock_response.content = response_text.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        service = QuestionProcessingService(sample_config)
        success = service.process_questions()
        
        # Should complete successfully
        assert success is True
    
    @patch('src.core.processor.requests.post')
    def test_process_questions_with_errors(self, mock_post, sample_config):
        """Test handling HTTP errors during question processing."""
        mock_post.side_effect = Exception("Connection error")
        
        service = QuestionProcessingService(sample_config)
        success = service.process_questions()
        
        # Should handle errors gracefully and still return True
        # (service writes error results to output)
        assert success is True
    
    def test_service_configuration_validation(self):
        """Test service validates configuration properly."""
        # Test that service can be created with minimal valid config
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="console")
        )
        
        service = QuestionProcessingService(config)
        assert service.config == config
    
    def test_service_factory_methods(self):
        """Test service factory methods work correctly."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="console")
        )
        
        service = QuestionProcessingService(config)
        
        # Test factory methods can create sources and destinations
        source = service._create_question_source()
        assert source is not None
        
        destination = service._create_output_destination()
        assert destination is not None
    
    def test_service_methods_exist(self):
        """Test that expected service methods exist."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="console")
        )
        
        service = QuestionProcessingService(config)
        
        # Test that key methods exist
        assert hasattr(service, 'process_questions')
        assert hasattr(service, '_create_question_source')
        assert hasattr(service, '_create_output_destination')
        assert callable(service.process_questions)
    
