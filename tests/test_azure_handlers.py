"""
Tests for Azure Function handlers (business logic without Azure dependencies).
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import os
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.azure.handlers import AzureFunctionHandler
from src.config.settings import AITesterConfig


class TestAzureFunctionHandler:
    """Test Azure Function business logic handler."""
    
    def test_handler_creation(self):
        """Test that handler can be created."""
        handler = AzureFunctionHandler()
        assert handler is not None
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_handle_timer_trigger_success(self, mock_config, mock_service_class):
        """Test successful timer trigger handling."""
        # Mock configuration
        mock_config_obj = Mock()
        mock_config_obj.base_url = 'https://test.example.com'
        mock_config_obj.question_source.source_type = 'yaml'
        mock_config_obj.output_destination.destination_type = 'json'
        mock_config_obj.debug = False
        mock_config.return_value = mock_config_obj
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger(mock_timer)
        
        # Verify success
        assert result is True
        mock_service.process_questions.assert_called_once()
        mock_config.assert_called_once()
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_handle_timer_trigger_failure(self, mock_config, mock_service_class):
        """Test timer trigger handling with service failure."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that returns failure
        mock_service = Mock()
        mock_service.process_questions.return_value = False
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger(mock_timer)
        
        # Verify failure
        assert result is False
        mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_handle_timer_trigger_exception(self, mock_config, mock_service_class):
        """Test timer trigger handling with exception."""
        # Mock configuration that raises error
        mock_config.side_effect = ValueError("Configuration error")
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger(mock_timer)
        
        # Verify failure due to exception
        assert result is False
        mock_service_class.assert_not_called()
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_handle_timer_trigger_past_due(self, mock_config, mock_service_class):
        """Test timer trigger handling when past due."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer that's past due
        mock_timer = Mock()
        mock_timer.past_due = True
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger(mock_timer)
        
        # Verify processing continues despite past due
        assert result is True
        mock_service.process_questions.assert_called_once()
    
    def test_handle_timer_trigger_without_timer_object(self):
        """Test timer trigger handling without timer object."""
        handler = AzureFunctionHandler()
        
        with patch('src.azure.handlers.QuestionProcessingService') as mock_service_class, \
             patch('src.azure.handlers.AITesterConfig.from_environment') as mock_config:
            
            # Mock configuration
            mock_config.return_value = Mock()
            
            # Mock service
            mock_service = Mock()
            mock_service.process_questions.return_value = True
            mock_service_class.return_value = mock_service
            
            # Test with None timer
            result = handler.handle_timer_trigger(None)
            
            # Should still work
            assert result is True
            mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_get_configuration_info_success(self, mock_config):
        """Test getting configuration information."""
        # Mock configuration
        mock_config_obj = Mock()
        mock_config_obj.base_url = 'https://test.example.com'
        mock_config_obj.question_source.source_type = 'yaml'
        mock_config_obj.output_destination.destination_type = 'json'
        mock_config_obj.debug = True
        mock_config_obj.endpoint = None
        mock_config_obj.processing.default_endpoint = '/conversation'
        mock_config.return_value = mock_config_obj
        
        # Test getting config info
        handler = AzureFunctionHandler()
        info = handler.get_configuration_info()
        
        # Verify information
        assert info['base_url'] == 'https://test.example.com'
        assert info['question_source_type'] == 'yaml'
        assert info['output_destination_type'] == 'json'
        assert info['debug_mode'] is True
        assert info['endpoint'] == '/conversation'
    
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_get_configuration_info_error(self, mock_config):
        """Test getting configuration information with error."""
        # Mock configuration that raises error
        mock_config.side_effect = Exception("Config error")
        
        # Test getting config info
        handler = AzureFunctionHandler()
        info = handler.get_configuration_info()
        
        # Verify error information
        assert 'error' in info
        assert 'Config error' in info['error']


class TestAzureFunctionHandlerIntegration:
    """Test Azure Function handler integration."""
    
    @patch.dict('os.environ', {
        'AI_TESTER_BASE_URL': 'https://env.example.com',
        'AI_TESTER_DEBUG': 'true',
        'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'dummy',
        'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'console'
    })
    @patch('src.azure.handlers.QuestionProcessingService')
    def test_environment_variable_integration(self, mock_service_class):
        """Test that environment variables are properly used."""
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger()
        
        # Verify service was called with environment config
        assert result is True
        mock_service_class.assert_called_once()
        
        # Verify configuration was created from environment
        config_arg = mock_service_class.call_args[0][0]
        assert config_arg.base_url == 'https://env.example.com'
        assert config_arg.debug is True
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_logging_integration(self, mock_config, mock_service_class):
        """Test that logging works properly."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Test the handler with logging capture
        with patch('src.azure.handlers.logger') as mock_logger:
            handler = AzureFunctionHandler()
            result = handler.handle_timer_trigger()
            
            # Verify logging occurred
            assert result is True
            mock_logger.info.assert_called()
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_service_integration(self, mock_config, mock_service_class):
        """Test integration with QuestionProcessingService."""
        # Mock configuration with realistic values
        mock_config_obj = Mock()
        mock_config_obj.base_url = 'https://integration.test.com'
        mock_config_obj.question_source.source_type = 'yaml'
        mock_config_obj.output_destination.destination_type = 'excel'
        mock_config_obj.debug = False
        mock_config.return_value = mock_config_obj
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Test the complete flow
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger()
        
        # Verify the complete integration
        assert result is True
        mock_config.assert_called_once()
        mock_service_class.assert_called_once_with(mock_config_obj)
        mock_service.process_questions.assert_called_once()


class TestAzureFunctionHandlerErrorScenarios:
    """Test Azure Function handler error scenarios."""
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_service_exception_handling(self, mock_config, mock_service_class):
        """Test handling of service exceptions."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that raises exception
        mock_service = Mock()
        mock_service.process_questions.side_effect = RuntimeError("Service error")
        mock_service_class.return_value = mock_service
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger()
        
        # Verify failure is handled gracefully
        assert result is False
    
    @patch('src.azure.handlers.QuestionProcessingService')
    @patch('src.azure.handlers.AITesterConfig.from_environment')
    def test_configuration_creation_failure(self, mock_config, mock_service_class):
        """Test handling of configuration creation failure."""
        # Mock configuration that fails
        mock_config.side_effect = ValueError("Invalid configuration")
        
        # Test the handler
        handler = AzureFunctionHandler()
        result = handler.handle_timer_trigger()
        
        # Verify failure is handled gracefully
        assert result is False
        mock_service_class.assert_not_called()
    
    @patch('src.azure.handlers.logging.basicConfig')
    def test_logging_setup(self, mock_basic_config):
        """Test that logging is properly set up."""
        handler = AzureFunctionHandler()
        
        # Verify logging was configured
        mock_basic_config.assert_called_once()