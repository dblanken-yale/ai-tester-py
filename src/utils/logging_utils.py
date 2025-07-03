"""Logging utilities for AI Tester."""
import logging
import json
import time
from typing import Any, Dict, Optional
from src.config.settings import LoggingConfig


class StructuredLogger:
    """Enhanced logger with structured output capabilities."""
    
    def __init__(self, name: str, config: LoggingConfig):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.config = config
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on configuration."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=self.config.log_format
        )
    
    def log_error(self, question: str, error_message: str, context: Optional[Dict[str, Any]] = None):
        """Log error with structured format."""
        try:
            log_entry = {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'question': question,
                'error': error_message,
                'context': context or {}
            }
            
            with open(self.config.error_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            self.logger.error(f"Question failed: {question[:50]}... - {error_message}")
            
        except Exception as e:
            self.logger.warning(f"Failed to log error: {e}")
    
    def log_success(self, question: str, context: Optional[Dict[str, Any]] = None):
        """Log successful question processing."""
        try:
            log_entry = {
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'question': question,
                'context': context or {}
            }
            
            with open(self.config.success_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            self.logger.debug(f"Question successful: {question[:50]}...")
            
        except Exception as e:
            self.logger.warning(f"Failed to log success: {e}")
    
    def log_configuration(self, config: Dict[str, Any]):
        """Log configuration information."""
        self.logger.info("AI Tester Configuration:")
        for key, value in config.items():
            # Mask sensitive information
            if 'password' in key.lower() or 'secret' in key.lower() or 'key' in key.lower():
                value = '***MASKED***'
            self.logger.info(f"  {key}: {value}")


class ErrorTracker:
    """Track and categorize errors for reporting."""
    
    def __init__(self):
        """Initialize error tracker."""
        self.errors = []
        self.error_counts = {}
    
    def add_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Add an error to the tracker."""
        error_entry = {
            'type': error_type,
            'message': message,
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'context': context or {}
        }
        
        self.errors.append(error_entry)
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors."""
        return {
            'total_errors': len(self.errors),
            'error_types': self.error_counts,
            'recent_errors': self.errors[-5:] if self.errors else []
        }
    
    def clear_errors(self):
        """Clear all tracked errors."""
        self.errors.clear()
        self.error_counts.clear()