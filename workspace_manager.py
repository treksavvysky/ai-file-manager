"""
AI Agent File Manager - Workspace Manager Module

This module provides a WorkspaceManager class for high-level directory operations
and workspace management that AI agents can use to organize and manipulate
file system structures safely.
"""

import os
import shutil
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple
from datetime import datetime
import fnmatch

try:
    from .file_handler import FileHandler
    from .exceptions import (
        FileManagerError,
        PathValidationError,
        FileOperationError,
        FileNotFoundError,
        SecurityError,
        ConfigurationError,
        convert_standard_exception
    )
except ImportError:
    # Handle direct execution
    from file_handler import FileHandler
    from exceptions import (
        FileManagerError,
        PathValidationError,
        FileOperationError,
        FileNotFoundError,
        SecurityError,
        ConfigurationError,
        convert_standard_exception
    )


class WorkspaceManager:
    """
    A comprehensive workspace manager for AI agents to perform directory-level operations.
    
    Features:
    - Directory listing and traversal
    - File and directory creation, moving, deletion
    - Workspace organization and cleanup
    - Path resolution relative to workspace root
    - Integration with FileHandler for file operations
    - Comprehensive logging and error handling
    """
    
    def __init__(self, workspace_root: Union[str, Path], 
                 file_handler: Optional[FileHandler] = None,
                 create_if_missing: bool = True,
                 max_depth: int = 10,
                 allowed_extensions: Optional[List[str]] = None):
        """
        Initialize the WorkspaceManager.
        
        Args:
            workspace_root: Root directory for all workspace operations
            file_handler: Optional FileHandler instance (creates new one if None)
            create_if_missing: Whether to create workspace_root if it doesn't exist
            max_depth: Maximum directory traversal depth for safety
            allowed_extensions: Optional list of allowed file extensions
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.max_depth = max_depth
        self.allowed_extensions = allowed_extensions or []
        self.operation_log = []
        
        # Initialize or use provided FileHandler
        if file_handler:
            self.file_handler = file_handler
        else:
            self.file_handler = FileHandler(base_directory=str(self.workspace_root))
        
        # Validate and setup workspace
        self._setup_workspace(create_if_missing)
    
    def _setup_workspace(self, create_if_missing: bool) -> None:
        """Setup and validate the workspace directory."""
        try:
            if not self.workspace_root.exists():
                if create_if_missing:
                    self.workspace_root.mkdir(parents=True, exist_ok=True)
                    self._log_operation("workspace_created", self.workspace_root, True, 
                                      "Created workspace directory")
                else:
                    raise ConfigurationError(f"Workspace root does not exist: {self.workspace_root}")
            
            if not self.workspace_root.is_dir():
                raise ConfigurationError(f"Workspace root is not a directory: {self.workspace_root}")
            
            # Test write permissions
            test_file = self.workspace_root / ".workspace_test"
            try:
                test_file.touch()
                test_file.unlink()
                self._log_operation("workspace_validated", self.workspace_root, True, 
                                  "Workspace permissions verified")
            except Exception as e:
                raise ConfigurationError(f"No write permission in workspace: {e}")
                
        except FileManagerError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to setup workspace: {e}")
    
    def _resolve_path(self, relative_path: Union[str, Path]) -> Path:
        """
        Resolve a path relative to the workspace root with validation.
        
        Args:
            relative_path: Path relative to workspace root
            
        Returns:
            Absolute resolved path
            
        Raises:
            PathValidationError: If path is invalid or outside workspace
        """
        try:
            if Path(relative_path).is_absolute():
                # Allow absolute paths if they're within workspace
                abs_path = Path(relative_path).resolve()
            else:
                # Resolve relative to workspace root
                abs_path = (self.workspace_root / relative_path).resolve()
            
            # Ensure path is within workspace
            try:
                abs_path.relative_to(self.workspace_root)
            except ValueError:
                raise PathValidationError(
                    f"Path {abs_path} is outside workspace {self.workspace_root}",
                    relative_path
                )
            
            return abs_path
            
        except Exception as e:
            if isinstance(e, FileManagerError):
                raise
            raise PathValidationError(f"Invalid path: {relative_path}", relative_path) from e
    
    def _check_extension(self, file_path: Path) -> bool:
        """Check if file extension is allowed."""
        if not self.allowed_extensions:
            return True
        return file_path.suffix.lower() in [ext.lower() for ext in self.allowed_extensions]
    
    def _log_operation(self, operation: str, path: Path, success: bool, 
                      details: str = "", error_type: str = None):
        """Log workspace operations for audit purposes."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "path": str(path),
            "relative_path": str(path.relative_to(self.workspace_root)) if path != self.workspace_root else ".",
            "success": success,
            "details": details,
            "error_type": error_type
        }
        self.operation_log.append(log_entry)
    
    def list_directory(self, relative_path: str = ".", 
                      include_hidden: bool = False,
                      file_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        List contents of a directory with detailed information.
        
        Args:
            relative_path: Directory path relative to workspace root
            include_hidden: Whether to include hidden files/directories
            file_types: Optional filter for file types ('file', 'directory', 'symlink')
            
        Returns:
            Dictionary with 'files', 'directories', and 'other' lists
            
        Raises:
            PathValidationError: If path is invalid
            FileNotFoundError: If directory doesn't exist
            FileOperationError: If listing fails
        """
        abs_path = self._resolve_path(relative_path)
        
        try:
            if not abs_path.exists():
                raise FileNotFoundError(f"Directory not found: {relative_path}", abs_path)
            
            if not abs_path.is_dir():
                raise FileOperationError(f"Path is not a directory: {relative_path}", abs_path, "list")
            
            result = {"files": [], "directories": [], "other": []}
            
            for item in abs_path.iterdir():
                # Skip hidden files if not requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Get item info
                try:
                    stat = item.stat()
                    item_info = {
                        "name": item.name,
                        "relative_path": str(item.relative_to(self.workspace_root)),
                        "size": stat.st_size if item.is_file() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "permissions": oct(stat.st_mode)[-3:],
                        "extension": item.suffix if item.is_file() else None,
                        "is_hidden": item.name.startswith('.')
                    }
                    
                    # Categorize item
                    if item.is_file():
                        if not file_types or 'file' in file_types:
                            result["files"].append(item_info)
                    elif item.is_dir():
                        if not file_types or 'directory' in file_types:
                            result["directories"].append(item_info)
                    else:
                        if not file_types or 'other' in file_types:
                            item_info["type"] = "symlink" if item.is_symlink() else "other"
                            result["other"].append(item_info)
                            
                except Exception as e:
                    # Log but don't fail for individual items
                    self._log_operation("list_item_error", item, False, str(e))
            
            # Sort results by name
            for category in result.values():
                category.sort(key=lambda x: x["name"].lower())
            
            self._log_operation("list_directory", abs_path, True, 
                              f"Listed {len(result['files'])} files, {len(result['directories'])} dirs")
            return result
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_path, "list")
            self._log_operation("list_directory", abs_path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def create_directory(self, relative_path: str, parents: bool = True) -> bool:
        """
        Create a new directory in the workspace.
        
        Args:
            relative_path: Directory path relative to workspace root
            parents: Whether to create parent directories if needed
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If path is invalid
            FileOperationError: If creation fails
        """
        abs_path = self._resolve_path(relative_path)
        
        try:
            if abs_path.exists():
                if abs_path.is_dir():
                    self._log_operation("create_directory", abs_path, True, "Directory already exists")
                    return True
                else:
                    raise FileOperationError(f"Path exists but is not a directory: {relative_path}", 
                                           abs_path, "create_directory")
            
            abs_path.mkdir(parents=parents, exist_ok=True)
            self._log_operation("create_directory", abs_path, True, "Created directory")
            return True
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_path, "create_directory")
            self._log_operation("create_directory", abs_path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def move_item(self, source_path: str, destination_path: str, 
                  overwrite: bool = False) -> bool:
        """
        Move a file or directory within the workspace.
        
        Args:
            source_path: Source path relative to workspace root
            destination_path: Destination path relative to workspace root
            overwrite: Whether to overwrite existing destination
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If paths are invalid
            FileNotFoundError: If source doesn't exist
            FileOperationError: If move fails
        """
        abs_source = self._resolve_path(source_path)
        abs_dest = self._resolve_path(destination_path)
        
        try:
            if not abs_source.exists():
                raise FileNotFoundError(f"Source not found: {source_path}", abs_source)
            
            if abs_dest.exists() and not overwrite:
                raise FileOperationError(f"Destination exists: {destination_path}", 
                                        abs_dest, "move")
            
            # Ensure destination parent exists
            abs_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform the move
            shutil.move(str(abs_source), str(abs_dest))
            
            self._log_operation("move", abs_source, True, f"Moved to {abs_dest.relative_to(self.workspace_root)}")
            return True
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_source, "move")
            self._log_operation("move", abs_source, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def copy_item(self, source_path: str, destination_path: str, 
                  overwrite: bool = False) -> bool:
        """
        Copy a file or directory within the workspace.
        
        Args:
            source_path: Source path relative to workspace root
            destination_path: Destination path relative to workspace root
            overwrite: Whether to overwrite existing destination
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If paths are invalid
            FileNotFoundError: If source doesn't exist
            FileOperationError: If copy fails
        """
        abs_source = self._resolve_path(source_path)
        abs_dest = self._resolve_path(destination_path)
        
        try:
            if not abs_source.exists():
                raise FileNotFoundError(f"Source not found: {source_path}", abs_source)
            
            if abs_dest.exists() and not overwrite:
                raise FileOperationError(f"Destination exists: {destination_path}", 
                                        abs_dest, "copy")
            
            # Ensure destination parent exists
            abs_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform the copy
            if abs_source.is_file():
                shutil.copy2(str(abs_source), str(abs_dest))
            elif abs_source.is_dir():
                if abs_dest.exists():
                    shutil.rmtree(str(abs_dest))
                shutil.copytree(str(abs_source), str(abs_dest))
            
            self._log_operation("copy", abs_source, True, f"Copied to {abs_dest.relative_to(self.workspace_root)}")
            return True
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_source, "copy")
            self._log_operation("copy", abs_source, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def delete_item(self, relative_path: str, force: bool = False) -> bool:
        """
        Delete a file or directory from the workspace.
        
        Args:
            relative_path: Path relative to workspace root
            force: Whether to force deletion of non-empty directories
            
        Returns:
            True if successful
            
        Raises:
            PathValidationError: If path is invalid
            FileNotFoundError: If item doesn't exist
            FileOperationError: If deletion fails
        """
        abs_path = self._resolve_path(relative_path)
        
        try:
            if not abs_path.exists():
                raise FileNotFoundError(f"Item not found: {relative_path}", abs_path)
            
            # Safety check - don't delete workspace root
            if abs_path == self.workspace_root:
                raise SecurityError("Cannot delete workspace root directory", abs_path)
            
            if abs_path.is_file():
                abs_path.unlink()
                self._log_operation("delete", abs_path, True, "Deleted file")
            elif abs_path.is_dir():
                if force:
                    shutil.rmtree(str(abs_path))
                    self._log_operation("delete", abs_path, True, "Force deleted directory")
                else:
                    abs_path.rmdir()  # Only works on empty directories
                    self._log_operation("delete", abs_path, True, "Deleted empty directory")
            
            return True
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_path, "delete")
            self._log_operation("delete", abs_path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def find_files(self, pattern: str = "*", 
                   relative_path: str = ".",
                   recursive: bool = True,
                   file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Find files matching a pattern in the workspace.
        
        Args:
            pattern: Glob pattern to match (e.g., "*.txt", "test_*")
            relative_path: Directory to search in (relative to workspace root)
            recursive: Whether to search subdirectories
            file_types: Filter by types ('file', 'directory')
            
        Returns:
            List of matching items with details
            
        Raises:
            PathValidationError: If path is invalid
            FileOperationError: If search fails
        """
        abs_path = self._resolve_path(relative_path)
        
        try:
            if not abs_path.exists() or not abs_path.is_dir():
                raise FileOperationError(f"Search path is not a valid directory: {relative_path}", 
                                        abs_path, "find")
            
            matches = []
            search_pattern = pattern.lower()
            
            def _search_directory(directory: Path, current_depth: int = 0):
                if current_depth > self.max_depth:
                    return
                
                try:
                    for item in directory.iterdir():
                        # Skip hidden files
                        if item.name.startswith('.'):
                            continue
                        
                        # Check if item matches pattern
                        if fnmatch.fnmatch(item.name.lower(), search_pattern):
                            # Check file type filter
                            if file_types:
                                if item.is_file() and 'file' not in file_types:
                                    continue
                                if item.is_dir() and 'directory' not in file_types:
                                    continue
                            
                            # Check extension filter
                            if item.is_file() and not self._check_extension(item):
                                continue
                            
                            try:
                                stat = item.stat()
                                match_info = {
                                    "name": item.name,
                                    "relative_path": str(item.relative_to(self.workspace_root)),
                                    "absolute_path": str(item),
                                    "type": "file" if item.is_file() else "directory",
                                    "size": stat.st_size if item.is_file() else None,
                                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    "extension": item.suffix if item.is_file() else None,
                                    "depth": current_depth
                                }
                                matches.append(match_info)
                            except Exception:
                                # Skip items we can't stat
                                continue
                        
                        # Recurse into subdirectories
                        if recursive and item.is_dir():
                            _search_directory(item, current_depth + 1)
                            
                except PermissionError:
                    # Skip directories we can't access
                    pass
            
            _search_directory(abs_path)
            
            # Sort by relative path
            matches.sort(key=lambda x: x["relative_path"])
            
            self._log_operation("find_files", abs_path, True, f"Found {len(matches)} matches for '{pattern}'")
            return matches
            
        except FileManagerError:
            raise
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_path, "find")
            self._log_operation("find_files", abs_path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def get_workspace_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about the workspace.
        
        Returns:
            Dictionary with workspace statistics and information
        """
        try:
            total_size = 0
            file_count = 0
            dir_count = 0
            
            def _analyze_directory(directory: Path):
                nonlocal total_size, file_count, dir_count
                try:
                    for item in directory.rglob("*"):
                        if item.is_file():
                            file_count += 1
                            try:
                                total_size += item.stat().st_size
                            except:
                                pass
                        elif item.is_dir():
                            dir_count += 1
                except:
                    pass
            
            _analyze_directory(self.workspace_root)
            
            workspace_stat = self.workspace_root.stat()
            
            info = {
                "workspace_root": str(self.workspace_root),
                "total_files": file_count,
                "total_directories": dir_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(workspace_stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(workspace_stat.st_mtime).isoformat(),
                "max_depth": self.max_depth,
                "allowed_extensions": self.allowed_extensions,
                "operations_logged": len(self.operation_log)
            }
            
            self._log_operation("workspace_info", self.workspace_root, True, "Retrieved workspace info")
            return info
            
        except Exception as e:
            self._log_operation("workspace_info", self.workspace_root, False, str(e))
            raise FileOperationError(f"Failed to get workspace info: {e}", self.workspace_root, "info")
    
    def cleanup_empty_directories(self, relative_path: str = ".") -> List[str]:
        """
        Remove empty directories from the workspace.
        
        Args:
            relative_path: Directory to clean (relative to workspace root)
            
        Returns:
            List of removed directory paths
            
        Raises:
            PathValidationError: If path is invalid
            FileOperationError: If cleanup fails
        """
        abs_path = self._resolve_path(relative_path)
        removed_dirs = []
        
        try:
            def _remove_empty_dirs(directory: Path):
                try:
                    for item in directory.iterdir():
                        if item.is_dir():
                            _remove_empty_dirs(item)
                            try:
                                if not any(item.iterdir()):  # Directory is empty
                                    item.rmdir()
                                    removed_dirs.append(str(item.relative_to(self.workspace_root)))
                            except OSError:
                                pass  # Directory not empty or permission error
                except PermissionError:
                    pass
            
            _remove_empty_dirs(abs_path)
            
            self._log_operation("cleanup", abs_path, True, f"Removed {len(removed_dirs)} empty directories")
            return removed_dirs
            
        except Exception as e:
            custom_exc = convert_standard_exception(e, abs_path, "cleanup")
            self._log_operation("cleanup", abs_path, False, str(e), type(custom_exc).__name__)
            raise custom_exc
    
    def get_operation_log(self, filter_by_operation: Optional[str] = None,
                         filter_by_success: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Get the workspace operation log with optional filtering.
        
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


# Example usage and testing functions
if __name__ == "__main__":
    import tempfile
    
    # Example usage with temporary workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = WorkspaceManager(temp_dir)
        
        try:
            print(f"🏗️  Created workspace at: {workspace.workspace_root}")
            
            # Create some test structure
            workspace.create_directory("projects/ai-agent")
            workspace.create_directory("data/input")
            workspace.create_directory("data/output")
            
            # Use FileHandler to create some test files
            workspace.file_handler.write_file("projects/ai-agent/main.py", "# AI Agent Main File\nprint('Hello!')")
            workspace.file_handler.write_file("data/input/data.txt", "Sample data content")
            workspace.file_handler.write_file("README.md", "# Workspace README")
            
            # List directory contents
            contents = workspace.list_directory()
            print(f"📁 Root contains {len(contents['directories'])} directories, {len(contents['files'])} files")
            
            # Find Python files
            py_files = workspace.find_files("*.py", recursive=True)
            print(f"🐍 Found {len(py_files)} Python files")
            
            # Get workspace info
            info = workspace.get_workspace_info()
            print(f"📊 Workspace: {info['total_files']} files, {info['total_size_mb']} MB")
            
            # Show operation log
            print(f"📝 Performed {len(workspace.get_operation_log())} operations")
            
        except Exception as e:
            print(f"❌ Error: {e}")
