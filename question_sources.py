"""
Question sources module wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
"""
from src.core.question_sources import (
    QuestionSource,
    YamlQuestionSource,
    DummyQuestionSource,
    PostgreSQLQuestionSource,
    QuestionSourceFactory
)

# Re-export for backward compatibility
__all__ = [
    'QuestionSource',
    'YamlQuestionSource', 
    'DummyQuestionSource',
    'PostgreSQLQuestionSource',
    'QuestionSourceFactory'
]