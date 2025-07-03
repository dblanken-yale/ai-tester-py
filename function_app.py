"""
Azure Function wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
The timer schedule is now configurable via the AI_TESTER_SCHEDULE environment variable.
"""
import logging
import azure.functions as func
from src.azure.function_app import app

# Re-export the function app for backward compatibility
__all__ = ['app']

# Set up logging
logging.basicConfig(level=logging.INFO)

# The actual timer function is now defined in src/azure/function_app.py
# This file serves as a backward-compatible entry point
# Schedule is configurable via AI_TESTER_SCHEDULE environment variable