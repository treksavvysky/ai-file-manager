"""
AI Agent File Manager - Custom Exceptions Module

This module defines custom exceptions for the file manager system,
providing specific error types that AI agents can handle appropriately.
"""

from typing import Optional, Union
from pathlib import Path


class FileManagerError(Exception):
    """
    Base exception class for all file manager errors.
    
    This serves as the parent class for all custom exceptions in the file manager,
    allowing for broad exception catching when needed.
    """
    
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None):
        """
        Initialize the base exception.
        
        Args:
            message: Error description
            file_path: Optional file path related to the error
        """
        super().__init__(message)
        self.message = message
        self.file_path = str(file_path) if file_path else None
        
    def __str__(self) -> str:
        if self.file_path:
            return f"{self.message} (File: {self.file_path})"
        return self.message


class PathValidationError(FileManagerError):
    """
    Raised when a file path fails validation checks.
    
    This includes:
    - Paths outside the allowed base directory
    - Invalid path formats
    - Security-related path violations
    """
    pass


class FileOperationError(FileManagerError):
    """
    Raised when a file operation fails due to system-level issues.
    
    This includes:
    - Permission denied errors
    - Disk space issues
    - Network-related failures for remote paths
    """
    
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None, 
                 operation: Optional[str] = None):
        """
        Initialize file operation error.
        
        Args:
            message: Error description
            file_path: File path where error occurred
            operation: The operation that failed (read, write, append, etc.)
        """
        super().__init__(message, file_path)
        self.operation = operation
        
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.operation:
            return f"{base_msg} (Operation: {self.operation})"
        return base_msg


class FileNotFoundError(FileManagerError):
    """
    Raised when attempting to access a file that doesn't exist.
    
    This is more specific than the built-in FileNotFoundError and includes
    additional context for AI agents.
    """
    pass


class FileAlreadyExistsError(FileManagerError):
    """
    Raised when attempting to create a file that already exists
    in contexts where this should be prevented.
    """
    pass


class InvalidFileTypeError(FileManagerError):
    """
    Raised when attempting to perform operations on unsupported file types.
    
    For example, trying to append to a binary file or parse JSON from a text file.
    """
    
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None,
                 expected_type: Optional[str] = None, actual_type: Optional[str] = None):
        """
        Initialize invalid file type error.
        
        Args:
            message: Error description
            file_path: File path with type issue
            expected_type: Expected file type/format
            actual_type: Actual detected file type/format
        """
        super().__init__(message, file_path)
        self.expected_type = expected_type
        self.actual_type = actual_type
        
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.expected_type and self.actual_type:
            return f"{base_msg} (Expected: {self.expected_type}, Got: {self.actual_type})"
        elif self.expected_type:
            return f"{base_msg} (Expected: {self.expected_type})"
        return base_msg


class FileSizeError(FileManagerError):
    """
    Raised when file size constraints are violated.
    
    This includes:
    - Files exceeding maximum size limits
    - Attempting to create files larger than available space
    - Size-related validation failures
    """
    
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None,
                 current_size: Optional[int] = None, limit_size: Optional[int] = None):
        """
        Initialize file size error.
        
        Args:
            message: Error description
            file_path: File path with size issue
            current_size: Current file size in bytes
            limit_size: Size limit that was exceeded in bytes
        """
        super().__init__(message, file_path)
        self.current_size = current_size
        self.limit_size = limit_size
        
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.current_size is not None and self.limit_size is not None:
            return f"{base_msg} (Size: {self.current_size} bytes, Limit: {self.limit_size} bytes)"
        elif self.current_size is not None:
            return f"{base_msg} (Size: {self.current_size} bytes)"
        return base_msg


class EncodingError(FileManagerError):
    """
    Raised when file encoding/decoding operations fail.
    
    This includes:
    - Unsupported character encodings
    - Corrupted file encoding
    - Encoding mismatches
    """
    
    def __init__(self, message: str, file_path: Optional[Union[str, Path]] = None,
                 encoding: Optional[str] = None):
        """
        Initialize encoding error.
        
        Args:
            message: Error description
            file_path: File path with encoding issue
            encoding: The encoding that failed
        """
        super().__init__(message, file_path)
        self.encoding = encoding
        
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.encoding:
            return f"{base_msg} (Encoding: {self.encoding})"
        return base_msg


class ConfigurationError(FileManagerError):
    """
    Raised when file manager configuration is invalid or missing.
    
    This includes:
    - Invalid base directory settings
    - Missing required configuration parameters
    - Conflicting configuration options
    """
    pass


class SecurityError(FileManagerError):
    """
    Raised when security constraints are violated.
    
    This includes:
    - Attempting to access restricted paths
    - Security policy violations
    - Potential security threats detected
    """
    pass


class ConcurrencyError(FileManagerError):
    """
    Raised when file access conflicts occur in concurrent scenarios.
    
    This includes:
    - File locked by another process
    - Race conditions in file operations
    - Concurrent modification conflicts
    """
    pass


# Exception mapping for converting standard exceptions to custom ones
EXCEPTION_MAPPING = {
    PermissionError: FileOperationError,
    OSError: FileOperationError,
    UnicodeDecodeError: EncodingError,
    UnicodeEncodeError: EncodingError,
}


def convert_standard_exception(exc: Exception, file_path: Optional[Union[str, Path]] = None,
                             operation: Optional[str] = None) -> FileManagerError:
    """
    Convert a standard Python exception to a custom FileManagerError.
    
    Args:
        exc: The original exception
        file_path: File path related to the error
        operation: The operation that was being performed
        
    Returns:
        Appropriate custom exception instance
    """
    exc_type = type(exc)
    
    if exc_type in EXCEPTION_MAPPING:
        custom_exc_class = EXCEPTION_MAPPING[exc_type]
        
        if custom_exc_class == FileOperationError:
            return FileOperationError(str(exc), file_path, operation)
        elif custom_exc_class == EncodingError:
            encoding = getattr(exc, 'encoding', None)
            return EncodingError(str(exc), file_path, encoding)
    
    # Handle built-in FileNotFoundError specifically
    if isinstance(exc, FileNotFoundError):
        return FileNotFoundError(str(exc), file_path)
    
    # Default to generic FileManagerError for unknown exceptions
    return FileManagerError(f"Unexpected error: {str(exc)}", file_path)


# Utility functions for exception handling
def is_recoverable_error(exc: Exception) -> bool:
    """
    Determine if an exception represents a recoverable error.
    
    Args:
        exc: Exception to check
        
    Returns:
        True if the error might be recoverable with retry or different approach
    """
    recoverable_types = (
        FileOperationError,
        ConcurrencyError,
        EncodingError,  # Might be recoverable with different encoding
    )
    
    return isinstance(exc, recoverable_types)


def get_error_category(exc: Exception) -> str:
    """
    Get a category string for an exception type.
    
    Args:
        exc: Exception to categorize
        
    Returns:
        Category string for logging/reporting purposes
    """
    if isinstance(exc, PathValidationError):
        return "path_validation"
    elif isinstance(exc, FileOperationError):
        return "file_operation"
    elif isinstance(exc, SecurityError):
        return "security"
    elif isinstance(exc, ConfigurationError):
        return "configuration"
    elif isinstance(exc, InvalidFileTypeError):
        return "file_type"
    elif isinstance(exc, FileSizeError):
        return "file_size"
    elif isinstance(exc, EncodingError):
        return "encoding"
    elif isinstance(exc, ConcurrencyError):
        return "concurrency"
    elif isinstance(exc, FileNotFoundError):
        return "file_not_found"
    elif isinstance(exc, FileAlreadyExistsError):
        return "file_exists"
    else:
        return "unknown"


# Example usage and testing
if __name__ == "__main__":
    # Example of custom exception usage
    try:
        raise PathValidationError("Path is outside allowed directory", "/dangerous/path")
    except FileManagerError as e:
        print(f"Caught FileManagerError: {e}")
        print(f"Category: {get_error_category(e)}")
        print(f"Recoverable: {is_recoverable_error(e)}")
        
    # Example of exception conversion
    try:
        # Simulate a permission error
        standard_exc = PermissionError("Permission denied")
        custom_exc = convert_standard_exception(standard_exc, "/some/file.txt", "write")
        print(f"Converted exception: {custom_exc}")
        print(f"Type: {type(custom_exc).__name__}")
    except Exception as e:
        print(f"Error in example: {e}")
