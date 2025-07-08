"""
CLI wrapper for backward compatibility.

This file maintains the original interface while using the new modular structure.
"""
import sys
from src.cli.main import main

if __name__ == '__main__':
    main()