"""
Processor module wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
"""
from src.core.processor import QuestionProcessor, ValidationError

# Re-export for backward compatibility
__all__ = ['QuestionProcessor', 'ValidationError']