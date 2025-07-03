"""
Integration tests for the complete AI Tester system.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch

from src.services.question_service import QuestionProcessingService
from src.config.settings import AITesterConfig, QuestionSourceConfig, OutputDestinationConfig
from src.cli.main import main
from src.azure.function_app import timer_process_batch_questions


class TestEndToEndIntegration:
    """Test complete end-to-end functionality."""
    
    @patch('src.services.question_service.requests.post')
    def test_complete_workflow_cli(self, mock_post, temp_yaml_file):
        """Test complete workflow through CLI."""
        # Mock AI endpoint response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
            '{"response": "Paris is the capital of France."}'
        ])
        mock_post.return_value = mock_response
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            # Configure the service
            config = AITesterConfig(
                base_url="https://test.example.com",
                question_source=QuestionSourceConfig(
                    source_type="yaml",
                    file_path=temp_yaml_file
                ),
                output_destination=OutputDestinationConfig(
                    destination_type="json",
                    file_path=output_file
                )
            )
            
            # Run the service
            service = QuestionProcessingService(config)
            success = service.process_questions()
            
            # Verify success
            assert success is True
            
            # Verify output file was created
            assert os.path.exists(output_file)
            
            # Verify output content
            with open(output_file, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert data['total_results'] == 3
            assert len(data['results']) == 3
            
            # Verify first result
            first_result = data['results'][0]
            assert first_result['question'] == "What is the capital of France?"
            assert first_result['response'] == "Paris is the capital of France."
            assert len(first_result['citations']) == 1
            
        finally:
            # Clean up
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @patch('src.services.question_service.requests.post')
    def test_complete_workflow_azure_function(self, mock_post):
        """Test complete workflow through Azure Function."""
        # Mock AI endpoint response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
            '{"response": "This is a test response."}'
        ])
        mock_post.return_value = mock_response
        
        # Mock environment variables
        env_vars = {
            'AI_TESTER_BASE_URL': 'https://test.example.com',
            'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'dummy',
            'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'console'
        }
        
        with patch.dict(os.environ, env_vars):
            # Mock timer
            mock_timer = Mock()
            mock_timer.past_due = False
            
            # Execute Azure Function
            result = timer_process_batch_questions(mock_timer)
            
            # Verify it executed without errors
            # (Success is indicated by no exceptions)
            assert True
    
    @patch('src.services.question_service.requests.post')
    def test_error_handling_integration(self, mock_post):
        """Test error handling throughout the system."""
        # Mock AI endpoint that returns errors
        mock_post.side_effect = Exception("Network error")
        
        # Configure service with dummy questions
        config = AITesterConfig(
            base_url="https://test.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="console")
        )
        
        # Run service
        service = QuestionProcessingService(config)
        success = service.process_questions()
        
        # Should still succeed (writes error results to output)
        assert success is True
    
    @patch('src.services.question_service.requests.post')
    def test_multiple_formats_integration(self, mock_post):
        """Test integration with multiple output formats."""
        # Mock AI endpoint response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '\n'.join([
            '{"citations": [{"title": "Test Source", "url": "https://example.com"}]}',
            '{"response": "Test response for multiple formats."}'
        ])
        mock_post.return_value = mock_response
        
        # Test JSON output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_file = f.name
        
        try:
            config = AITesterConfig(
                base_url="https://test.example.com",
                question_source=QuestionSourceConfig(source_type="dummy"),
                output_destination=OutputDestinationConfig(
                    destination_type="json",
                    file_path=json_file
                )
            )
            
            service = QuestionProcessingService(config)
            success = service.process_questions()
            
            assert success is True
            assert os.path.exists(json_file)
            
            # Verify JSON content
            with open(json_file, 'r') as f:
                data = json.load(f)
            assert 'results' in data
            assert len(data['results']) > 0
            
        finally:
            if os.path.exists(json_file):
                os.unlink(json_file)
        
        # Test Excel output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
            excel_file = f.name
        
        try:
            config = AITesterConfig(
                base_url="https://test.example.com",
                question_source=QuestionSourceConfig(source_type="dummy"),
                output_destination=OutputDestinationConfig(
                    destination_type="excel",
                    file_path=excel_file
                )
            )
            
            service = QuestionProcessingService(config)
            success = service.process_questions()
            
            assert success is True
            assert os.path.exists(excel_file)
            
        finally:
            if os.path.exists(excel_file):
                os.unlink(excel_file)


class TestConfigurationIntegration:
    """Test configuration integration across components."""
    
    @patch.dict(os.environ, {
        'AI_TESTER_BASE_URL': 'https://env.example.com',
        'AI_TESTER_DEBUG': 'true',
        'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'dummy',
        'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'console'
    })
    def test_environment_variable_integration(self):
        """Test that environment variables work across all components."""
        # Test config creation from environment
        config = AITesterConfig.from_environment()
        
        assert config.base_url == 'https://env.example.com'
        assert config.debug is True
        assert config.question_source.source_type == 'dummy'
        assert config.output_destination.destination_type == 'console'
        
        # Test service creation with environment config
        service = QuestionProcessingService(config)
        assert service.config == config
    
    def test_cli_argument_integration(self):
        """Test CLI argument parsing integration."""
        from src.cli.main import parse_arguments
        from src.config.settings import AITesterConfig
        
        # Parse CLI arguments
        args = parse_arguments([
            'https://cli.example.com',
            '--debug',
            '--questions', 'cli_test.yml',
            '--format', 'excel',
            '--outfile', 'cli_output.xlsx'
        ])
        
        # Create config from CLI args
        config = AITesterConfig.from_cli_args(args)
        
        assert config.base_url == 'https://cli.example.com'
        assert config.debug is True
        assert config.question_source.file_path == 'cli_test.yml'
        assert config.output_destination.destination_type == 'excel'
        assert config.output_destination.file_path == 'cli_output.xlsx'


class TestSmartFileNamingIntegration:
    """Test smart file naming integration."""
    
    @patch('src.utils.file_naming.datetime')
    def test_smart_naming_with_service(self, mock_datetime):
        """Test smart file naming integration with service."""
        from datetime import datetime
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        # Configure service without explicit file path
        config = AITesterConfig(
            base_url="https://test-api.example.com",
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="json")
        )
        
        service = QuestionProcessingService(config)
        
        # Test smart file path generation
        file_path = service._get_smart_file_path(config, 'json')
        
        # Verify smart naming pattern
        assert 'test_api_example_com' in file_path
        assert '2024-01-15_143022' in file_path
        assert file_path.endswith('.json')
    
    @patch('src.utils.file_naming.datetime')
    def test_smart_naming_different_formats(self, mock_datetime):
        """Test smart naming with different file formats."""
        from datetime import datetime
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        base_url = "https://api.mycompany.com"
        
        # Test JSON format
        config_json = AITesterConfig(
            base_url=base_url,
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="json")
        )
        
        service = QuestionProcessingService(config_json)
        json_path = service._get_smart_file_path(config_json, 'json')
        
        assert json_path.endswith('.json')
        assert 'api_mycompany_com' in json_path
        
        # Test Excel format
        config_excel = AITesterConfig(
            base_url=base_url,
            question_source=QuestionSourceConfig(source_type="dummy"),
            output_destination=OutputDestinationConfig(destination_type="excel")
        )
        
        service = QuestionProcessingService(config_excel)
        excel_path = service._get_smart_file_path(config_excel, 'xlsx')
        
        assert excel_path.endswith('.xlsx')
        assert 'api_mycompany_com' in excel_path


class TestBackwardCompatibilityIntegration:
    """Test backward compatibility integration."""
    
    def test_wrapper_imports(self):
        """Test that all wrapper imports work correctly."""
        # Test config wrapper
        from config import get_config, DEFAULT_CONFIG
        assert get_config is not None
        assert DEFAULT_CONFIG is not None
        
        # Test processor wrapper
        from processor import QuestionProcessor, ValidationError
        assert QuestionProcessor is not None
        assert ValidationError is not None
        
        # Test question sources wrapper
        from question_sources import QuestionSourceFactory
        assert QuestionSourceFactory is not None
        
        # Test output destinations wrapper
        from output_destinations import OutputDestinationFactory
        assert OutputDestinationFactory is not None
        
        # Test function app wrapper
        from function_app import app
        assert app is not None
    
    def test_legacy_interfaces(self):
        """Test that legacy interfaces still work."""
        from processor import QuestionProcessor
        from config import get_config
        
        # Test legacy processor interface
        config = get_config()
        processor = QuestionProcessor(config)
        
        # Should work without errors
        assert processor is not None