"""
Legacy output options wrapper for backward compatibility.

This module provides the same interface as the original output_options.py
but now uses the new output_destinations module under the hood.
"""
import json
from typing import Any, Callable, Dict, List
from src.core.output_destinations import OutputDestinationFactory

# Legacy output format registry
output_registry: Dict[str, Callable[[Any, Dict[str, Any]], None]] = {}


def register_output_format(name: str):
    """Decorator to register a new output format (legacy compatibility)."""
    def decorator(func: Callable[[Any, Dict[str, Any]], None]):
        output_registry[name] = func
        return func
    return decorator


@register_output_format('json')
def to_json(results: List[dict], options: Dict[str, Any]) -> None:
    """Convert results to JSON format using new output destination system."""
    if 'filename' in options and options['filename'] is not None:
        destination = OutputDestinationFactory.create_destination(
            'json', 
            file_path=options['filename'],
            pretty_print=True
        )
        destination.write_results(results)
    else:
        destination = OutputDestinationFactory.create_destination(
            'console',
            format_type='json'
        )
        destination.write_results(results)


@register_output_format('excel')
def to_excel(content: List[dict], options: Dict[str, Any]) -> None:
    """Convert results to Excel format using new output destination system."""
    if 'filename' in options and options['filename'] is not None:
        destination = OutputDestinationFactory.create_destination(
            'excel',
            file_path=options['filename']
        )
        destination.write_results(content)
        print("Data written to file: ", options['filename'])
    else:
        # For console output, fall back to JSON format
        destination = OutputDestinationFactory.create_destination(
            'console',
            format_type='json'
        )
        destination.write_results(content)


@register_output_format('raw')
def to_raw(content: Any, _options: Dict[str, Any]) -> None:
    """Print raw content to console (legacy compatibility)."""
    print(content)


def get_output_function(format_name: str) -> Callable[[Any, Dict[str, Any]], None]:
    """Get the output function for a given format name (legacy compatibility)."""
    return output_registry.get(format_name, to_raw)


# Deprecated function kept for backward compatibility
def resize_excel(filename: str) -> None:
    """
    Resize Excel columns and rows (legacy compatibility).
    
    Note: This functionality is now handled automatically by ExcelFileDestination.
    This function is kept for backward compatibility but does nothing.
    """
    pass  # Functionality moved to ExcelFileDestination._format_excel_file()