"""
Output destinations module wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
"""
from src.core.output_destinations import (
    OutputDestination,
    JsonFileDestination,
    ExcelFileDestination,
    PostgreSQLDestination,
    ConsoleDestination,
    OutputDestinationFactory
)

# Re-export for backward compatibility
__all__ = [
    'OutputDestination',
    'JsonFileDestination',
    'ExcelFileDestination', 
    'PostgreSQLDestination',
    'ConsoleDestination',
    'OutputDestinationFactory'
]