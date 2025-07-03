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
        assert service.question_source is None
        assert service.output_destination is None
    
    def test_create_question_source_yaml(self):
        """Test creating a YAML question source."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(
                source_type="yaml",
                file_path="test.yml"
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
        assert dest.get_destination_info()['type'] == 'console_output'
    
    @patch('src.services.question_service.requests.post')
    def test_send_question_success(self, mock_post, sample_config):
        """Test successfully sending a question to the AI endpoint."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
            '{"response": "This is a test response."}'
        ])
        mock_post.return_value = mock_response
        
        service = QuestionProcessingService(sample_config)
        result = service._send_question("What is the capital of France?")
        
        assert result is not None
        assert result['question'] == "What is the capital of France?"
        assert result['response'] == "This is a test response."
        assert len(result['citations']) == 1
        assert result['citations'][0]['title'] == "Test Source"
    
    @patch('src.services.question_service.requests.post')
    def test_send_question_http_error(self, mock_post, sample_config):
        """Test handling HTTP errors when sending questions."""
        mock_post.side_effect = Exception("Connection error")
        
        service = QuestionProcessingService(sample_config)
        result = service._send_question("Test question?")
        
        assert result is not None
        assert result['question'] == "Test question?"
        assert 'error' in result
        assert 'Connection error' in result['error']
    
    @patch('src.services.question_service.requests.post')
    def test_send_question_invalid_response(self, mock_post, sample_config):
        """Test handling invalid response format."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON response"
        mock_post.return_value = mock_response
        
        service = QuestionProcessingService(sample_config)
        result = service._send_question("Test question?")
        
        assert result is not None
        assert result['question'] == "Test question?"
        assert 'error' in result
    
    def test_parse_response_success(self, sample_config):
        """Test successfully parsing AI response."""
        response_text = '\n'.join([
            '{"citations": [{"title": "Test", "url": "https://example.com"}]}',
            '{"response": "Test response"}'
        ])
        
        service = QuestionProcessingService(sample_config)
        citations, response = service._parse_response(response_text)
        
        assert len(citations) == 1
        assert citations[0]['title'] == "Test"
        assert response == "Test response"
    
    def test_parse_response_no_citations(self, sample_config):
        """Test parsing response without citations."""
        response_text = '{"response": "Test response without citations"}'
        
        service = QuestionProcessingService(sample_config)
        citations, response = service._parse_response(response_text)
        
        assert citations == []
        assert response == "Test response without citations"
    
    def test_parse_response_invalid_json(self, sample_config):
        """Test parsing invalid JSON response."""
        response_text = "Invalid JSON"
        
        service = QuestionProcessingService(sample_config)
        citations, response = service._parse_response(response_text)
        
        assert citations == []
        assert response == "Invalid JSON"
    
    @patch('src.utils.file_naming.generate_unique_filename')
    def test_get_smart_file_path(self, mock_generate, sample_config):
        """Test getting smart file path."""
        mock_generate.return_value = "results_test_example_com_2024-01-15_143022.json"
        
        service = QuestionProcessingService(sample_config)
        file_path = service._get_smart_file_path(sample_config, 'json')
        
        assert file_path == "results_test_example_com_2024-01-15_143022.json"
        mock_generate.assert_called_once()
    
    @patch('src.services.question_service.QuestionProcessingService._create_question_source')
    @patch('src.services.question_service.QuestionProcessingService._create_output_destination')
    @patch('src.services.question_service.QuestionProcessingService._send_question')
    def test_process_questions_success(self, mock_send, mock_create_dest, mock_create_source, sample_config):
        """Test successfully processing questions."""
        # Mock question source
        mock_source = Mock()
        mock_source.get_questions.return_value = ["Question 1?", "Question 2?"]
        mock_source.get_source_info.return_value = {"type": "dummy"}
        mock_create_source.return_value = mock_source
        
        # Mock output destination
        mock_dest = Mock()
        mock_dest.write_results.return_value = True
        mock_create_dest.return_value = mock_dest
        
        # Mock question responses
        mock_send.side_effect = [
            {"question": "Question 1?", "response": "Answer 1", "citations": []},
            {"question": "Question 2?", "response": "Answer 2", "citations": []}
        ]
        
        service = QuestionProcessingService(sample_config)
        success = service.process_questions()
        
        assert success is True
        assert mock_send.call_count == 2
        mock_dest.write_results.assert_called_once()
    
    @patch('src.services.question_service.QuestionProcessingService._create_question_source')
    def test_process_questions_no_questions(self, mock_create_source, sample_config):
        """Test processing when no questions are available."""
        mock_source = Mock()
        mock_source.get_questions.return_value = []
        mock_create_source.return_value = mock_source
        
        service = QuestionProcessingService(sample_config)
        success = service.process_questions()
        
        assert success is False
    
    @patch('src.services.question_service.QuestionProcessingService._create_question_source')
    @patch('src.services.question_service.QuestionProcessingService._create_output_destination')
    @patch('src.services.question_service.QuestionProcessingService._send_question')
    def test_process_questions_output_failure(self, mock_send, mock_create_dest, mock_create_source, sample_config):
        """Test processing when output destination fails."""
        # Mock question source
        mock_source = Mock()
        mock_source.get_questions.return_value = ["Question 1?"]
        mock_source.get_source_info.return_value = {"type": "dummy"}
        mock_create_source.return_value = mock_source
        
        # Mock output destination that fails
        mock_dest = Mock()
        mock_dest.write_results.return_value = False
        mock_create_dest.return_value = mock_dest
        
        # Mock question response
        mock_send.return_value = {"question": "Question 1?", "response": "Answer 1", "citations": []}
        
        service = QuestionProcessingService(sample_config)
        success = service.process_questions()
        
        assert success is False
    
    def test_validate_config_valid(self, sample_config):
        """Test validating a valid configuration."""
        service = QuestionProcessingService(sample_config)
        
        # Should not raise any exceptions
        service._validate_config()
    
    def test_validate_config_missing_base_url(self):
        """Test validating configuration with missing base URL."""
        config = AITesterConfig(
            base_url="",  # Empty base URL
            question_source=QuestionSourceConfig(source_type="dummy")
        )
        
        service = QuestionProcessingService(config)
        
        with pytest.raises(ValidationError, match="Base URL is required"):
            service._validate_config()
    
    def test_validate_config_invalid_source_type(self):
        """Test validating configuration with invalid source type."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="invalid_type")
        )
        
        service = QuestionProcessingService(config)
        
        with pytest.raises(ValidationError, match="Invalid question source type"):
            service._validate_config()
    
    def test_validate_config_invalid_destination_type(self):
        """Test validating configuration with invalid destination type."""
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="invalid_type")
        )
        
        service = QuestionProcessingService(config)
        
        with pytest.raises(ValidationError, match="Invalid output destination type"):
            service._validate_config()