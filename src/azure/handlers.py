"""
Azure Function handlers - business logic separated from Azure decorators.

This module contains the actual logic for Azure Function triggers,
keeping Azure-specific imports in function_app.py only.
"""
import logging
from typing import Optional, Any
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import AITesterConfig
from src.services.question_service import QuestionProcessingService

logger = logging.getLogger(__name__)


class AzureFunctionHandler:
    """Handler for Azure Function business logic without Azure dependencies."""
    
    def __init__(self):
        """Initialize the handler."""
        self.setup_logging()
    
    def setup_logging(self):
        """Configure logging for Azure Functions."""
        logging.basicConfig(level=logging.INFO)
    
    def handle_timer_trigger(self, timer_request: Optional[Any] = None) -> bool:
        """
        Handle timer trigger logic without Azure Functions dependencies.
        
        Args:
            timer_request: Timer request object (Azure-specific, treated as opaque)
            
        Returns:
            bool: True if processing was successful, False otherwise
        """
        try:
            logger.info("Azure Function timer trigger started")
            
            # Log timer information if available
            if timer_request and hasattr(timer_request, 'past_due'):
                if timer_request.past_due:
                    logger.warning("The timer is past due!")
            
            # Create configuration from environment variables
            config = AITesterConfig.from_environment()
            
            # Log configuration info (without sensitive data)
            logger.info(f"Processing questions for endpoint: {config.base_url}")
            logger.info(f"Question source type: {config.question_source.source_type}")
            logger.info(f"Output destination type: {config.output_destination.destination_type}")
            logger.info(f"Debug mode: {config.debug}")
            
            # Create and run the question processing service
            service = QuestionProcessingService(config)
            success = service.process_questions()
            
            if success:
                logger.info("Azure Function completed successfully")
            else:
                logger.error("Azure Function completed with errors")
                
            return success
            
        except Exception as e:
            logger.error(f"Azure Function failed with error: {e}", exc_info=True)
            return False
    
    def get_configuration_info(self) -> dict:
        """
        Get configuration information for monitoring/debugging.
        
        Returns:
            dict: Safe configuration information (no secrets)
        """
        try:
            config = AITesterConfig.from_environment()
            return {
                'base_url': config.base_url,
                'question_source_type': config.question_source.source_type,
                'output_destination_type': config.output_destination.destination_type,
                'debug_mode': config.debug,
                'endpoint': config.endpoint or config.processing.default_endpoint
            }
        except Exception as e:
            logger.error(f"Failed to get configuration info: {e}")
            return {'error': str(e)}