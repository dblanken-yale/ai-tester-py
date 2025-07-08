"""
Configuration module wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
"""
from src.config.config import get_config, DEFAULT_CONFIG

# Re-export for backward compatibility
__all__ = ['get_config', 'DEFAULT_CONFIG']