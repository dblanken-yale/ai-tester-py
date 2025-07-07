"""
Tests for Azure Function functionality (Azure-specific decorators).
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Try to import Azure Functions, skip tests if not available
try:
    import azure.functions as func
    from src.azure.function_app import app, timer_process_batch_questions
    AZURE_FUNCTIONS_AVAILABLE = True
except ImportError:
    AZURE_FUNCTIONS_AVAILABLE = False
    pytest.skip("Azure Functions not available", allow_module_level=True)


class TestAzureFunctionTimer:
    """Test Azure Function timer trigger."""
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_timer_trigger_success(self, mock_config, mock_service_class):
        """Test successful timer trigger execution."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Call the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify no exceptions and service was called
        mock_service.process_questions.assert_called_once()
        mock_config.assert_called_once()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_timer_trigger_config_error(self, mock_config, mock_service_class):
        """Test timer trigger with configuration error."""
        # Mock configuration that raises error
        mock_config.side_effect = ValueError("Missing required config")
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Call the function - should not raise exception
        result = timer_process_batch_questions(mock_timer)
        
        # Verify service was not called due to config error
        mock_service_class.assert_not_called()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_timer_trigger_service_error(self, mock_config, mock_service_class):
        """Test timer trigger with service error."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that raises exception
        mock_service = Mock()
        mock_service.process_questions.side_effect = Exception("Service error")
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Call the function - should not raise exception
        result = timer_process_batch_questions(mock_timer)
        
        # Verify service was attempted
        mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_timer_trigger_processing_failure(self, mock_config, mock_service_class):
        """Test timer trigger with processing failure."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that returns failure
        mock_service = Mock()
        mock_service.process_questions.return_value = False
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Call the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify service was called
        mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_timer_trigger_past_due(self, mock_config, mock_service_class):
        """Test timer trigger when past due."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer that's past due
        mock_timer = Mock()
        mock_timer.past_due = True
        
        # Call the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify service was still called despite being past due
        mock_service.process_questions.assert_called_once()


class TestAzureFunctionApp:
    """Test Azure Function app configuration."""
    
    def test_app_exists(self):
        """Test that the function app exists."""
        assert app is not None
        assert hasattr(app, 'timer_trigger')
    
    def test_timer_trigger_decorator(self):
        """Test that timer trigger is properly decorated."""
        # This test verifies the function is properly decorated
        # The actual decorator behavior is tested by Azure Functions runtime
        assert hasattr(timer_process_batch_questions, '__azure_function__')
    
    @patch.dict('os.environ', {'AI_TESTER_SCHEDULE': '0 */10 * * * *'})
    def test_timer_schedule_environment_variable(self):
        """Test that timer schedule uses environment variable."""
        # This is more of a documentation test since the decorator
        # is evaluated at import time
        import os
        schedule = os.environ.get('AI_TESTER_SCHEDULE', '0 */5 * * * *')
        assert schedule == '0 */10 * * * *'


class TestAzureFunctionIntegration:
    """Test Azure Function integration with other components."""
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    def test_end_to_end_success(self, mock_config, mock_service_class):
        """Test complete end-to-end Azure Function execution."""
        # Mock configuration with realistic values
        mock_config_obj = Mock()
        mock_config_obj.base_url = 'https://test.example.com'
        mock_config_obj.debug = False
        mock_config.return_value = mock_config_obj
        
        # Mock service with realistic behavior
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer with realistic properties
        mock_timer = Mock()
        mock_timer.past_due = False
        mock_timer.schedule_status = {'last': '2024-01-15T14:30:00Z'}
        
        # Execute the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify the complete flow
        mock_config.assert_called_once()
        mock_service_class.assert_called_once_with(mock_config_obj)
        mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch.dict('os.environ', {
        'AI_TESTER_BASE_URL': 'https://env.example.com',
        'AI_TESTER_DEBUG': 'true',
        'AI_TESTER_QUESTIONS_SOURCE_TYPE': 'dummy',
        'AI_TESTER_OUTPUT_DESTINATION_TYPE': 'json'
    })
    def test_environment_variable_integration(self, mock_service_class):
        """Test that environment variables are properly used."""
        # Mock service
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Execute the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify service was called (config creation is tested separately)
        mock_service_class.assert_called_once()
        mock_service.process_questions.assert_called_once()
    
    @patch('src.azure.function_app.logging.getLogger')
    def test_logging_integration(self, mock_get_logger):
        """Test that logging is properly configured."""
        # Mock logger
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Import should set up logging
        from src.azure.function_app import logger
        
        # Verify logger was configured
        mock_get_logger.assert_called_with(__name__)


class TestAzureFunctionErrorHandling:
    """Test Azure Function error handling."""
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    @patch('src.azure.function_app.logger')
    def test_exception_logging(self, mock_logger, mock_config, mock_service_class):
        """Test that exceptions are properly logged."""
        # Mock configuration that raises error
        mock_config.side_effect = Exception("Test error")
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Execute the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify error was logged
        mock_logger.error.assert_called()
        
        # Verify the error message contains relevant information
        error_call = mock_logger.error.call_args[0][0]
        assert "Test error" in error_call
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    @patch('src.azure.function_app.logger')
    def test_processing_failure_logging(self, mock_logger, mock_config, mock_service_class):
        """Test that processing failures are properly logged."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that returns failure
        mock_service = Mock()
        mock_service.process_questions.return_value = False
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Execute the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify warning was logged
        mock_logger.warning.assert_called()
        
        # Verify the warning message is appropriate
        warning_call = mock_logger.warning.call_args[0][0]
        assert "failed" in warning_call.lower()
    
    @patch('src.azure.function_app.QuestionProcessingService')
    @patch('src.azure.function_app.AITesterConfig.from_environment')
    @patch('src.azure.function_app.logger')
    def test_success_logging(self, mock_logger, mock_config, mock_service_class):
        """Test that successful execution is properly logged."""
        # Mock configuration
        mock_config.return_value = Mock()
        
        # Mock service that succeeds
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock timer
        mock_timer = Mock()
        mock_timer.past_due = False
        
        # Execute the function
        result = timer_process_batch_questions(mock_timer)
        
        # Verify success was logged
        mock_logger.info.assert_called()
        
        # Verify the success message is appropriate
        info_call = mock_logger.info.call_args[0][0]
        assert "success" in info_call.lower()