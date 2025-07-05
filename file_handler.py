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


class FileHandler:
    """
    A modular file handler class for AI agents with basic read, write, and append operations.
    
    Features:
    - Safe file operations with error handling
    - Support for various file types (text, JSON, etc.)
    - Logging of operations for audit trails
    - Path validation and security checks
    """
    
    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize the FileHandler with an optional base directory.
        
        Args:
            base_directory: Optional base directory to restrict operations to
        """
        self.base_directory = Path(base_directory) if base_directory else None
        self.operation_log = []
        
    def _validate_path(self, file_path: Union[str, Path]) -> Path:
        """
        Validate and resolve the file path.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Resolved Path object
            
        Raises:
            ValueError: If path is invalid or outside base directory
        """
        path = Path(file_path).resolve()
        
        if self.base_directory:
            try:
                path.relative_to(self.base_directory.resolve())
            except ValueError:
                raise ValueError(f"Path {path} is outside the allowed base directory")
        
        return path
    
    def _log_operation(self, operation: str, file_path: Path, success: bool, details: str = ""):
        """Log file operations for audit purposes."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "file_path": str(file_path),
            "success": success,
            "details": details
        }
        self.operation_log.append(log_entry)
    
    def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read content from a file.
        
        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If no read permission
            ValueError: If path is invalid
        """
        path = self._validate_path(file_path)
        
        try:
            with open(path, 'r', encoding=encoding) as file:
                content = file.read()
            
            self._log_operation("read", path, True, f"Read {len(content)} characters")
            return content
            
        except Exception as e:
            self._log_operation("read", path, False, str(e))
            raise
    
    def write_file(self, file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """
        Write content to a file (overwrites existing content).
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful
            
        Raises:
            PermissionError: If no write permission
            ValueError: If path is invalid
        """
        path = self._validate_path(file_path)
        
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as file:
                file.write(content)
            
            self._log_operation("write", path, True, f"Wrote {len(content)} characters")
            return True
            
        except Exception as e:
            self._log_operation("write", path, False, str(e))
            raise
    
    def append_file(self, file_path: Union[str, Path], content: str, encoding: str = 'utf-8') -> bool:
        """
        Append content to a file.
        
        Args:
            file_path: Path to the file to append to
            content: Content to append
            encoding: File encoding (default: utf-8)
            
        Returns:
            True if successful
            
        Raises:
            PermissionError: If no write permission
            ValueError: If path is invalid
        """
        path = self._validate_path(file_path)
        
        try:
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'a', encoding=encoding) as file:
                file.write(content)
            
            self._log_operation("append", path, True, f"Appended {len(content)} characters")
            return True
            
        except Exception as e:
            self._log_operation("append", path, False, str(e))
            raise
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists.
        
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
        except Exception as e:
            self._log_operation("exists_check", Path(file_path), False, str(e))
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        path = self._validate_path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = path.stat()
        info = {
            "name": path.name,
            "size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": path.is_file(),
            "is_directory": path.is_dir(),
            "absolute_path": str(path.absolute())
        }
        
        self._log_operation("info", path, True, "Retrieved file info")
        return info
    
    def get_operation_log(self) -> List[Dict[str, Any]]:
        """
        Get the operation log for audit purposes.
        
        Returns:
            List of operation log entries
        """
        return self.operation_log.copy()
    
    def clear_operation_log(self) -> None:
        """Clear the operation log."""
        self.operation_log.clear()


# Example usage and testing functions
if __name__ == "__main__":
    # Example usage
    handler = FileHandler()
    
    # Test file operations
    test_file = "test_example.txt"
    
    try:
        # Write a test file
        handler.write_file(test_file, "Hello, AI Agent!\n")
        print(f"Created test file: {test_file}")
        
        # Read the file
        content = handler.read_file(test_file)
        print(f"File content: {content.strip()}")
        
        # Append to the file
        handler.append_file(test_file, "This is an appended line.\n")
        
        # Read again
        content = handler.read_file(test_file)
        print(f"Updated content:\n{content}")
        
        # Get file info
        info = handler.get_file_info(test_file)
        print(f"File info: {info}")
        
        # Show operation log
        print("\nOperation Log:")
        for entry in handler.get_operation_log():
            print(f"  {entry['timestamp']}: {entry['operation']} - {entry['success']}")
            
    except Exception as e:
        print(f"Error: {e}")
