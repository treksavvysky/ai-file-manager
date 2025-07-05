"""
AI Agent File Manager - Core File Handler Module

This module provides a modular FileHandler class for basic file operations
that AI agents can use safely and efficiently.
"""

import os
import json
from pathlib import Path
from typing import Union, Optional, List, Dict, Any
from datetime import datetime

# Import custom exceptions
try:
    from .exceptions import (
        FileManagerError,
        PathValidationError,
        FileOperationError,
        FileNotFoundError,
        InvalidFileTypeError,
        FileSizeError,
        EncodingError,
        SecurityError,
        convert_standard_exception
    )
except ImportError:
    # Handle direct execution
    from exceptions import (
        FileManagerError,
        PathValidationError,
        FileOperationError,
        FileNotFoundError,
        InvalidFileTypeError,
        FileSizeError,
        EncodingError,
        SecurityError,
        convert_standard_exception
    )


class FileHandler:
    """
    A modular file handler class for AI agents with basic read, write, and append operations.
    
    Features:
    - Safe file operations with comprehensive error handling
    - Support for various file types (text, JSON, etc.)
    - Logging of operations for audit trails
    - Path validation and security checks
    - Custom exception types for specific error handling
    """
    
    def __init__(self, base_directory: Optional[str] = None, max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize the FileHandler with security and size constraints.
        
        Args:
            base_directory: Optional base directory to restrict operations to
            max_file_size: Maximum file size in bytes (default: 10MB)
        """
        self.base_directory = Path(base_directory).resolve() if base_directory else None
        self.max_file_size = max_file_size
        self.operation_log = []
        
        # Validate base directory if provided
        if self.base_directory and not self.base_directory.exists():
            raise PathValidationError(f"Base directory does not exist: {self.base_directory}")
        
    def _validate_path(self, file_path: Union[str, Path]) -> Path:
        """
        Validate and resolve the file path with comprehensive security checks.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Resolved Path object
            
        Raises:
            PathValidationError: If path is invalid or violates security constraints
        """
        try:
            # If we have a base directory and the path is relative, resolve against base directory
            if self.base_directory and not Path(file_path).is_absolute():
                path = (self.base_directory / file_path).resolve()
            else:
                path = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise PathValidationError(f"Invalid path format: {file_path}", file_path) from e
        
        # Check for security violations
        path_str = str(path).lower()
        dangerous_patterns = ['..', '~', '$', '${', '%(', '%{']
        
        if any(pattern in str(file_path) for pattern in dangerous_patterns):
            raise SecurityError(f"Potentially dangerous path pattern detected: {file_path}", file_path)
        
        # Validate against base directory if set
        if self.base_directory:
            try:
                path.relative_to(self.base_directory)
            except ValueError:
                raise PathValidationError(
                    f"Path {path} is outside the allowed base directory {self.base_directory}",
                    file_path
                )
        
        return path
    
    def _validate_file_size(self, file_path: Path, operation: str = "read") -> None:
        """
        Validate file size constraints.
        
        Args:
            file_path: Path to check
            operation: Operation being performed
            
        Raises:
            FileSizeError: If file exceeds size limits
        """
        if file_path.exists():
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise FileSizeError(
                    f"File size ({file_size} bytes) exceeds maximum allowed size",
                    file_path,
                    file_size,
                    self.max_file_size
                )
    
    def _log_operation(self, operation: str, file_path: Path, success: bool, 
                      details: str = "", error_type: str = None):
        """Log file operations for audit purposes."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file_path": str(file_path),
            "success": success,
            "details": details,
            "error_type": error_type
        }
        self.operation_log.append(log_entry)
    
    def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read content from a file with comprehensive error handling.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            PathValidationError: If path is invalid
            FileNotFoundError: If file doesn't exist
            FileOperationError: If read operation fails
            FileSizeError: If file exceeds size limits
            EncodingError: If encoding fails
        """
        path = self._validate_path(file_path)
        
        try:
            # Check if file exists
            if not path.exists():
                raise FileNotFoundError(f"File does not exist: {path}", path)
            
            if not path.is_file():
                raise InvalidFileTypeError(f"Path is not a file: {path}", path)
            
            # Validate file size
            self._validate_file_size(path, "read")
            
            # Attempt to read the file
            with open(path, 'r', encoding=encoding) as file:
                content = file.read()
            
            self._log_operation("read", path, True, f"Read {len(content)} characters")
            return content
            
        except (FileManagerError,):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert standard exceptions to custom ones
            custom_exc = convert_standard_exception(e, path, "read")
            self._log_operation("read", path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def write_file(self, file_path: Union[str, Path], content: str, 
                  encoding: str = 'utf-8', overwrite: bool = True) -> bool:
        """
        Write content to a file with safety checks.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            overwrite: Whether to overwrite existing files (default: True)
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If path is invalid
            FileAlreadyExistsError: If file exists and overwrite=False
            FileOperationError: If write operation fails
            FileSizeError: If content exceeds size limits
            EncodingError: If encoding fails
        """
        path = self._validate_path(file_path)
        
        try:
            # Check if file already exists when overwrite is disabled
            if not overwrite and path.exists():
                try:
                    from .exceptions import FileAlreadyExistsError
                except ImportError:
                    from exceptions import FileAlreadyExistsError
                raise FileAlreadyExistsError(f"File already exists: {path}", path)
            
            # Validate content size
            content_size = len(content.encode(encoding))
            if content_size > self.max_file_size:
                raise FileSizeError(
                    f"Content size ({content_size} bytes) exceeds maximum allowed size",
                    path,
                    content_size,
                    self.max_file_size
                )
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(path, 'w', encoding=encoding) as file:
                file.write(content)
            
            self._log_operation("write", path, True, f"Wrote {len(content)} characters")
            return True
            
        except (FileManagerError,):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert standard exceptions to custom ones
            custom_exc = convert_standard_exception(e, path, "write")
            self._log_operation("write", path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def append_file(self, file_path: Union[str, Path], content: str, 
                   encoding: str = 'utf-8') -> bool:
        """
        Append content to a file with size validation.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If path is invalid
            FileOperationError: If append operation fails
            FileSizeError: If resulting file would exceed size limits
            EncodingError: If encoding fails
        """
        path = self._validate_path(file_path)
        
        try:
            # Check resulting file size if file exists
            if path.exists():
                current_size = path.stat().st_size
                content_size = len(content.encode(encoding))
                total_size = current_size + content_size
                
                if total_size > self.max_file_size:
                    raise FileSizeError(
                        f"Appending would exceed maximum file size",
                        path,
                        total_size,
                        self.max_file_size
                    )
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to the file
            with open(path, 'a', encoding=encoding) as file:
                file.write(content)
            
            self._log_operation("append", path, True, f"Appended {len(content)} characters")
            return True
            
        except (FileManagerError,):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert standard exceptions to custom ones
            custom_exc = convert_standard_exception(e, path, "append")
            self._log_operation("append", path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists with error handling.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            path = self._validate_path(file_path)
            exists = path.exists() and path.is_file()
            self._log_operation("exists_check", path, True, f"Exists: {exists}")
            return exists
        except FileManagerError as e:
            self._log_operation("exists_check", Path(str(file_path)), False, str(e), type(e).__name__)
            return False
        except Exception as e:
            # For exists check, we don't want to raise exceptions for invalid paths
            # Just log and return False
            self._log_operation("exists_check", Path(str(file_path)), False, str(e), "StandardError")
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get comprehensive information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
            
        Raises:
            PathValidationError: If path is invalid
            FileNotFoundError: If file doesn't exist
            FileOperationError: If unable to get file information
        """
        path = self._validate_path(file_path)
        
        try:
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}", path)
            
            stat = path.stat()
            info = {
                "name": path.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_directory": path.is_dir(),
                "absolute_path": str(path.absolute()),
                "extension": path.suffix,
                "stem": path.stem,
                "readable": os.access(path, os.R_OK),
                "writable": os.access(path, os.W_OK),
                "executable": os.access(path, os.X_OK)
            }
            
            self._log_operation("info", path, True, "Retrieved file info")
            return info
            
        except (FileManagerError,):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Convert standard exceptions to custom ones
            custom_exc = convert_standard_exception(e, path, "info")
            self._log_operation("info", path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def get_operation_log(self, filter_by_operation: Optional[str] = None,
                         filter_by_success: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get the operation log with optional filtering.
        
        Args:
            filter_by_operation: Filter by operation type
            filter_by_success: Filter by success status
            
        Returns:
            List of operation log entries
        """
        log = self.operation_log.copy()
        
        if filter_by_operation:
            log = [entry for entry in log if entry['operation'] == filter_by_operation]
        
        if filter_by_success is not None:
            log = [entry for entry in log if entry['success'] == filter_by_success]
        
        return log
    
    def clear_operation_log(self) -> None:
        """Clear the operation log."""
        self.operation_log.clear()
    
    def get_error_summary(self) -> Dict[str, int]:
        """
        Get a summary of errors from the operation log.
        
        Returns:
            Dictionary with error type counts
        """
        error_summary = {}
        for entry in self.operation_log:
            if not entry['success'] and entry.get('error_type'):
                error_type = entry['error_type']
                error_summary[error_type] = error_summary.get(error_type, 0) + 1
        
        return error_summary


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage with custom exceptions
    handler = FileHandler(max_file_size=1024)  # Small size for testing
    
    try:
        # Test various operations and error conditions
        test_file = "test_example.txt"
        
        # Test normal operations
        handler.write_file(test_file, "Hello, AI Agent!\n")
        print(f"✓ Created test file: {test_file}")
        
        content = handler.read_file(test_file)
        print(f"✓ Read content: {content.strip()}")
        
        # Test file info
        info = handler.get_file_info(test_file)
        print(f"✓ File size: {info['size']} bytes")
        
        # Test error handling - try to read non-existent file
        try:
            handler.read_file("nonexistent.txt")
        except FileNotFoundError as e:
            print(f"✓ Caught expected error: {e}")
        
        # Test size limit
        try:
            large_content = "x" * 2000  # Exceeds our 1KB limit
            handler.write_file("large_file.txt", large_content)
        except FileSizeError as e:
            print(f"✓ Caught size error: {e}")
        
        # Show operation log with errors
        print("\n📋 Operation Log Summary:")
        for entry in handler.get_operation_log():
            status = "✓" if entry['success'] else "✗"
            print(f"  {status} {entry['operation']}: {entry['details']}")
        
        # Show error summary
        error_summary = handler.get_error_summary()
        if error_summary:
            print(f"\n⚠️  Error Summary: {error_summary}")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
