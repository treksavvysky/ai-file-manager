"""
AI Agent File Manager Package

A modular file management system designed for AI agents to perform
safe and efficient file operations with comprehensive error handling.

Main Components:
- FileHandler: Core file operations class
- Custom Exceptions: Specific error types for better error handling

Usage:
    from ai_file_manager import FileHandler
    from ai_file_manager.exceptions import FileManagerError
    
    handler = FileHandler(base_directory="/safe/path")
    try:
        content = handler.read_file("example.txt")
    except FileManagerError as e:
        print(f"File operation failed: {e}")
"""

from .file_handler import FileHandler
from .exceptions import (
    FileManagerError,
    PathValidationError,
    FileOperationError,
    FileNotFoundError,
    FileAlreadyExistsError,
    InvalidFileTypeError,
    FileSizeError,
    EncodingError,
    ConfigurationError,
    SecurityError,
    ConcurrencyError,
)

__version__ = "0.1.0"
__author__ = "AI File Manager Project"
__description__ = "Modular file management system for AI agents"

__all__ = [
    "FileHandler",
    "FileManagerError",
    "PathValidationError", 
    "FileOperationError",
    "FileNotFoundError",
    "FileAlreadyExistsError",
    "InvalidFileTypeError",
    "FileSizeError",
    "EncodingError",
    "ConfigurationError",
    "SecurityError",
    "ConcurrencyError",
]
