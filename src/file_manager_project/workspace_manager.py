"""
AI Agent File Manager - Workspace Manager Module

This module provides a WorkspaceManager class for high-level directory operations
and workspace management that AI agents can use to organize and manipulate
file system structures safely, using Pydantic for validation and structured data.
"""

import os
import shutil
from pathlib import Path
from typing import Union, List, Dict, Any, Optional, Tuple # Kept for internal type hints if necessary
from datetime import datetime
import fnmatch
from pydantic import ValidationError

from .file_handler import FileHandler
from .file_handler_models import FileHandlerSettings # Corrected import
from .exceptions import (
    FileManagerError,
    PathValidationError,
    FileOperationError,
    FileNotFoundError as CustomFileNotFoundError,
    FileAlreadyExistsError,
    SecurityError,
    ConfigurationError,
    InvalidFileTypeError, # Added for completeness
    convert_standard_exception,
    get_error_category
)
from .workspace_manager_models import (
    WorkspaceManagerSettings,
    ListDirectoryRequest, ListDirectoryResponse, ListItem, FileItemInfo, DirectoryItemInfo, OtherItemInfo, WorkspaceItemType,
    CreateDirectoryRequest, CreateDirectoryResponse,
    MoveItemRequest, MoveItemResponse,
    CopyItemRequest, CopyItemResponse,
    DeleteItemRequest, DeleteItemResponse,
    FindItemsRequest, FindItemsResponse, FoundItemInfo,
    GetWorkspaceInfoRequest, GetWorkspaceInfoResponse, WorkspaceInfo,
    CleanupEmptyDirectoriesRequest, CleanupEmptyDirectoriesResponse,
    GetWorkspaceOperationLogRequest, GetWorkspaceOperationLogResponse, WorkspaceOperationLogEntry, WorkspaceOperation,
    ClearWorkspaceOperationLogRequest, ClearWorkspaceOperationLogResponse,
    RelativePath
)

class WorkspaceManager:
    """
    A comprehensive workspace manager for AI agents to perform directory-level operations,
    enhanced with Pydantic models for request validation and structured responses.
    """

    def __init__(self, settings: WorkspaceManagerSettings, file_handler_instance: Optional[FileHandler] = None):
        """
        Initialize the WorkspaceManager with Pydantic settings.

        Args:
            settings: A WorkspaceManagerSettings Pydantic model instance.
            file_handler_instance: Optional pre-configured FileHandler instance.
                                   If None, a new FileHandler is created using settings derived
                                   from WorkspaceManagerSettings (e.g., base_directory).
        """
        self.settings = settings
        self.workspace_root: Path = settings.workspace_root.resolve() # Pydantic's DirectoryPath ensures it exists and is a dir
        self.max_depth: int = settings.max_depth
        self.allowed_extensions: List[str] = [ext.lower() for ext in settings.allowed_extensions] if settings.allowed_extensions else []

        self.operation_log: List[WorkspaceOperationLogEntry] = []

        if file_handler_instance:
            self.file_handler = file_handler_instance
            # Optionally, validate if file_handler_instance.base_directory matches workspace_root
            if self.file_handler.base_directory != self.workspace_root:
                # This could be a warning or a ConfigurationError depending on strictness
                print(f"Warning: Provided FileHandler's base_directory ('{self.file_handler.base_directory}') "
                      f"differs from WorkspaceManager's root ('{self.workspace_root}').")
        else:
            # Create a FileHandler scoped to the workspace root
            fh_settings = FileHandlerSettings(base_directory=str(self.workspace_root), max_file_size=10*1024*1024) # Default max size or from config
            self.file_handler = FileHandler(settings=fh_settings)

        self._setup_workspace() # Initial validation like write permissions

    def _setup_workspace(self) -> None:
        """Validate the workspace directory post-initialization (e.g., write permissions)."""
        # Workspace root existence and type (directory) is already validated by Pydantic's DirectoryPath in settings.
        # We might still want to create it if `create_if_missing` was part of settings and handled by a model_validator.
        # For now, Pydantic DirectoryPath implies it must exist.
        # The create_if_missing logic in old init is somewhat superseded by DirectoryPath.
        # If WorkspaceManagerSettings.workspace_root was just a `Path`, then this logic would be more relevant here.

        if not self.workspace_root.exists(): # Should not happen if DirectoryPath(must_exist=True)
             self._log_operation(WorkspaceOperation.WORKSPACE_CREATED, self.workspace_root, True, "Workspace directory (expected by settings).")
             # self.workspace_root.mkdir(parents=True, exist_ok=True) # This would be if DirectoryPath didn't ensure existence

        # Test write permissions
        test_file_path = self.workspace_root / f".workspace_write_test_{os.getpid()}"
        try:
            test_file_path.touch()
            test_file_path.unlink()
            self._log_operation(WorkspaceOperation.WORKSPACE_VALIDATED, self.workspace_root, True, "Workspace permissions verified.")
        except Exception as e:
            err_msg = f"No write permission in workspace '{self.workspace_root}': {e}"
            self._log_operation(WorkspaceOperation.WORKSPACE_VALIDATED, self.workspace_root, False, err_msg, e)
            raise ConfigurationError(err_msg) from e

    def _resolve_path(self, relative_path_str: RelativePath) -> Path:
        """
        Resolve a path string (assumed relative to workspace root) to an absolute Path object.
        Validates that the resolved path is within the workspace root.
        """
        if not isinstance(relative_path_str, str):
            # This should ideally be caught by Pydantic if request models type hint RelativePath as str
            raise PathValidationError(f"Path must be a string, got {type(relative_path_str)}: '{relative_path_str}'", str(relative_path_str))

        # Normalize: remove leading/trailing slashes to prevent issues like '//path' or 'path/'
        # However, Path object handles this well. '.' is fine. Empty string could be an issue.
        if not relative_path_str: # Treat empty string as workspace root
            relative_path_str = "."

        # Disallow absolute paths passed as relative_path_str to prevent potential confusion/bypass.
        # Pydantic models should use `FilePath` or `DirectoryPath` for absolute paths if ever needed.
        if Path(relative_path_str).is_absolute():
            raise PathValidationError(
                f"Expected a relative path, but got absolute: '{relative_path_str}'",
                relative_path_str
            )

        try:
            # Resolve relative to workspace root. `resolve()` canonicalizes (e.g. handles '..')
            abs_path = (self.workspace_root / relative_path_str).resolve()
        except Exception as e: # Catch potential OS errors during path resolution
            raise PathValidationError(f"Invalid path format or resolution error for '{relative_path_str}': {e}", relative_path_str) from e

        # Crucial security check: ensure the resolved path is genuinely within the workspace.
        # `relative_to` will raise ValueError if `abs_path` is not under `self.workspace_root`.
        try:
            abs_path.relative_to(self.workspace_root)
        except ValueError:
            raise PathValidationError(
                f"Path '{abs_path}' (resolved from '{relative_path_str}') is outside workspace '{self.workspace_root}'",
                relative_path_str # Original input that caused the issue
            )
        return abs_path

    def _check_extension(self, file_path: Path) -> bool:
        """Check if file extension is allowed. Extensions in self.allowed_extensions are lowercased."""
        if not self.allowed_extensions:
            return True # All extensions allowed if list is empty
        return file_path.suffix.lower() in self.allowed_extensions

    def _log_operation(self, operation: WorkspaceOperation, path: Path, success: bool,
                      details: str = "", error: Optional[Exception] = None) -> None:
        """Log workspace operations using Pydantic model."""
        error_type_str: Optional[str] = None
        if error:
            error_type_str = get_error_category(error) if isinstance(error, FileManagerError) else type(error).__name__

        rel_path_str: Optional[str] = None
        try:
            if path == self.workspace_root:
                rel_path_str = "."
            else:
                rel_path_str = str(path.relative_to(self.workspace_root))
        except ValueError: # Path might be outside workspace (e.g. during a failed resolve)
            rel_path_str = None # Or keep original problematic path string if available

        log_entry = WorkspaceOperationLogEntry(
            timestamp=datetime.now(),
            operation=operation,
            path=str(path), # Absolute path
            relative_path=rel_path_str,
            success=success,
            details=details or str(error) or "Completed",
            error_type=error_type_str
        )
        self.operation_log.append(log_entry)

    def list_directory(self, request: ListDirectoryRequest) -> ListDirectoryResponse:
        abs_path: Optional[Path] = None
        try:
            abs_path = self._resolve_path(request.relative_path)

            if not abs_path.exists():
                raise CustomFileNotFoundError(f"Directory not found: {request.relative_path}", str(abs_path))
            if not abs_path.is_dir():
                raise InvalidFileTypeError(f"Path is not a directory: {request.relative_path}", str(abs_path), expected_type="directory")

            listed_items: List[ListItem] = []
            for item_path in abs_path.iterdir():
                if not request.include_hidden and item_path.name.startswith('.'):
                    continue

                item_type_enum: WorkspaceItemType
                item_info_data: Dict[str, Any] = {
                    "name": item_path.name,
                    "relative_path": str(item_path.relative_to(self.workspace_root)),
                    "is_hidden": item_path.name.startswith('.'),
                    "modified_at": datetime.fromtimestamp(item_path.stat().st_mtime),
                    "permissions": oct(item_path.stat().st_mode)[-3:]
                }

                if item_path.is_file():
                    item_type_enum = WorkspaceItemType.FILE
                    if request.filter_types and item_type_enum not in request.filter_types: continue
                    if not self._check_extension(item_path): continue # Check allowed extensions for files
                    item_info_data.update({
                        "type": WorkspaceItemType.FILE,
                        "size_bytes": item_path.stat().st_size,
                        "extension": item_path.suffix or None
                    })
                    listed_items.append(FileItemInfo(**item_info_data))
                elif item_path.is_dir():
                    item_type_enum = WorkspaceItemType.DIRECTORY
                    if request.filter_types and item_type_enum not in request.filter_types: continue
                    item_info_data["type"] = WorkspaceItemType.DIRECTORY
                    listed_items.append(DirectoryItemInfo(**item_info_data))
                else: # Symlinks, other types
                    actual_type_detail = "symlink" if item_path.is_symlink() else "other"
                    item_type_enum = WorkspaceItemType.SYMLINK if actual_type_detail == "symlink" else WorkspaceItemType.OTHER
                    if request.filter_types and item_type_enum not in request.filter_types: continue
                    item_info_data.update({
                        "type": item_type_enum,
                        "actual_type_detail": actual_type_detail
                    })
                    listed_items.append(OtherItemInfo(**item_info_data))

            listed_items.sort(key=lambda x: (x.type.value, x.name.lower())) # Sort by type then name

            self._log_operation(WorkspaceOperation.LIST_DIRECTORY, abs_path, True, f"Listed {len(listed_items)} items.")
            return ListDirectoryResponse(success=True, path_listed=request.relative_path, items=listed_items, message="Directory listed successfully.")

        except Exception as e:
            final_path = abs_path if abs_path else (self.workspace_root / request.relative_path)
            custom_exc = convert_standard_exception(e, str(final_path), WorkspaceOperation.LIST_DIRECTORY.value)
            self._log_operation(WorkspaceOperation.LIST_DIRECTORY, final_path, False, error=custom_exc)
            return ListDirectoryResponse(success=False, path_listed=request.relative_path, items=[], message=str(custom_exc))

    def create_directory(self, request: CreateDirectoryRequest) -> CreateDirectoryResponse:
        abs_path: Optional[Path] = None
        try:
            abs_path = self._resolve_path(request.relative_path)
            already_existed = False

            if abs_path.exists():
                if abs_path.is_dir():
                    already_existed = True
                    self._log_operation(WorkspaceOperation.CREATE_DIRECTORY, abs_path, True, "Directory already exists.")
                else: # Path exists but is a file
                    raise FileAlreadyExistsError(f"Path exists but is not a directory: {request.relative_path}", str(abs_path))
            else:
                abs_path.mkdir(parents=request.parents, exist_ok=True) # exist_ok=True is fine even if we check existence first
                self._log_operation(WorkspaceOperation.CREATE_DIRECTORY, abs_path, True, "Directory created.")

            return CreateDirectoryResponse(success=True, created_path=request.relative_path, already_existed=already_existed, message="Directory operation successful.")

        except Exception as e:
            final_path = abs_path if abs_path else (self.workspace_root / request.relative_path)
            custom_exc = convert_standard_exception(e, str(final_path), WorkspaceOperation.CREATE_DIRECTORY.value)
            self._log_operation(WorkspaceOperation.CREATE_DIRECTORY, final_path, False, error=custom_exc)
            return CreateDirectoryResponse(success=False, created_path=request.relative_path, already_existed=None, message=str(custom_exc))

    def move_item(self, request: MoveItemRequest) -> MoveItemResponse:
        abs_source: Optional[Path] = None
        abs_dest: Optional[Path] = None
        try:
            abs_source = self._resolve_path(request.source_relative_path)
            abs_dest = self._resolve_path(request.destination_relative_path)

            if not abs_source.exists():
                raise CustomFileNotFoundError(f"Source not found: {request.source_relative_path}", str(abs_source))

            if abs_dest.exists() and not request.overwrite:
                raise FileAlreadyExistsError(f"Destination exists and overwrite is false: {request.destination_relative_path}", str(abs_dest))

            if abs_dest.parent != self.workspace_root and not abs_dest.parent.exists(): # Check parent of dest, not dest itself for mkdir
                 abs_dest.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(abs_source), str(abs_dest))

            self._log_operation(WorkspaceOperation.MOVE_ITEM, abs_source, True, f"Moved to {request.destination_relative_path}")
            return MoveItemResponse(success=True, source_path=request.source_relative_path, destination_path=request.destination_relative_path, message="Item moved successfully.")

        except Exception as e:
            # Determine which path was problematic or use a generic one for logging
            log_path = abs_source or (self.workspace_root / request.source_relative_path)
            custom_exc = convert_standard_exception(e, str(log_path), WorkspaceOperation.MOVE_ITEM.value)
            self._log_operation(WorkspaceOperation.MOVE_ITEM, log_path, False, error=custom_exc)
            return MoveItemResponse(success=False, source_path=request.source_relative_path, destination_path=request.destination_relative_path, message=str(custom_exc))

    def copy_item(self, request: CopyItemRequest) -> CopyItemResponse:
        abs_source: Optional[Path] = None
        abs_dest: Optional[Path] = None
        try:
            abs_source = self._resolve_path(request.source_relative_path)
            abs_dest = self._resolve_path(request.destination_relative_path)

            if not abs_source.exists():
                raise CustomFileNotFoundError(f"Source not found: {request.source_relative_path}", str(abs_source))

            if abs_source.is_file() and not self._check_extension(abs_source):
                raise SecurityError(f"Source file type '{abs_source.suffix}' is not allowed for copy.", str(abs_source))

            if abs_dest.exists() and not request.overwrite:
                raise FileAlreadyExistsError(f"Destination exists and overwrite is false: {request.destination_relative_path}", str(abs_dest))

            if abs_dest.parent != self.workspace_root and not abs_dest.parent.exists():
                abs_dest.parent.mkdir(parents=True, exist_ok=True)

            if abs_source.is_file():
                shutil.copy2(str(abs_source), str(abs_dest))
            elif abs_source.is_dir():
                if abs_dest.exists() and request.overwrite: # shutil.copytree fails if dest exists
                    shutil.rmtree(str(abs_dest))
                shutil.copytree(str(abs_source), str(abs_dest), dirs_exist_ok=request.overwrite) # dirs_exist_ok for Python 3.8+
            else:
                raise InvalidFileTypeError(f"Source is not a file or directory: {request.source_relative_path}", str(abs_source))

            self._log_operation(WorkspaceOperation.COPY_ITEM, abs_source, True, f"Copied to {request.destination_relative_path}")
            return CopyItemResponse(success=True, source_path=request.source_relative_path, destination_path=request.destination_relative_path, message="Item copied successfully.")

        except Exception as e:
            log_path = abs_source or (self.workspace_root / request.source_relative_path)
            custom_exc = convert_standard_exception(e, str(log_path), WorkspaceOperation.COPY_ITEM.value)
            self._log_operation(WorkspaceOperation.COPY_ITEM, log_path, False, error=custom_exc)
            return CopyItemResponse(success=False, source_path=request.source_relative_path, destination_path=request.destination_relative_path, message=str(custom_exc))

    def delete_item(self, request: DeleteItemRequest) -> DeleteItemResponse:
        abs_path: Optional[Path] = None
        item_type_deleted: Optional[WorkspaceItemType] = None
        try:
            abs_path = self._resolve_path(request.relative_path)

            if not abs_path.exists():
                raise CustomFileNotFoundError(f"Item to delete not found: {request.relative_path}", str(abs_path))

            if abs_path == self.workspace_root:
                raise SecurityError("Cannot delete workspace root directory.", str(abs_path))

            if abs_path.is_file():
                item_type_deleted = WorkspaceItemType.FILE
                if not self._check_extension(abs_path): # Check extension before deleting
                    raise SecurityError(f"File type '{abs_path.suffix}' is not allowed for deletion.", str(abs_path))
                abs_path.unlink()
                details = "Deleted file."
            elif abs_path.is_dir():
                item_type_deleted = WorkspaceItemType.DIRECTORY
                if request.force:
                    shutil.rmtree(str(abs_path))
                    details = "Force deleted directory and its contents."
                else:
                    try:
                        abs_path.rmdir() # Only works on empty directories
                        details = "Deleted empty directory."
                    except OSError: # Directory not empty
                         raise FileOperationError(f"Directory not empty: {request.relative_path}. Use force=True to delete non-empty directories.", str(abs_path), "delete")
            else: # Symlink or other, treat as file for unlink
                item_type_deleted = WorkspaceItemType.OTHER # Or more specific if is_symlink() etc.
                abs_path.unlink() # Unlink works for symlinks too
                details = f"Deleted item of type {item_type_deleted.value}."

            self._log_operation(WorkspaceOperation.DELETE_ITEM, abs_path, True, details)
            return DeleteItemResponse(success=True, deleted_path=request.relative_path, item_type=item_type_deleted, message="Item deleted successfully.")

        except Exception as e:
            final_path = abs_path if abs_path else (self.workspace_root / request.relative_path)
            custom_exc = convert_standard_exception(e, str(final_path), WorkspaceOperation.DELETE_ITEM.value)
            self._log_operation(WorkspaceOperation.DELETE_ITEM, final_path, False, error=custom_exc)
            return DeleteItemResponse(success=False, deleted_path=request.relative_path, item_type=None, message=str(custom_exc))

    def find_items(self, request: FindItemsRequest) -> FindItemsResponse:
        search_root_abs_path: Optional[Path] = None
        found_item_list: List[FoundItemInfo] = []
        try:
            search_root_abs_path = self._resolve_path(request.relative_path)

            if not search_root_abs_path.is_dir():
                raise InvalidFileTypeError(f"Search path is not a directory: {request.relative_path}", str(search_root_abs_path))

            # Normalize pattern for case-insensitivity later if needed, fnmatch is case-sensitive by default on some OS
            # For simplicity, we'll rely on fnmatch's behavior or user providing correct case pattern.
            # os.path.normcase can be used for pattern and item names for true case-insensitivity.

            def _search_dir_recursive(current_dir: Path, current_depth: int) -> None:
                if current_depth > self.max_depth: return

                for item_path in current_dir.iterdir():
                    # Skip hidden files typically, unless find_hidden is a param
                    # if item_path.name.startswith('.'): continue

                    item_type: Optional[WorkspaceItemType] = None
                    if item_path.is_file(): item_type = WorkspaceItemType.FILE
                    elif item_path.is_dir(): item_type = WorkspaceItemType.DIRECTORY
                    # else: item_type = WorkspaceItemType.OTHER # Or symlink

                    if request.item_types and item_type not in request.item_types:
                        pass # continue without matching name if type doesn't fit
                    elif fnmatch.fnmatch(item_path.name, request.pattern): # fnmatch.fnmatchcase for explicit case-sensitivity
                        if item_type == WorkspaceItemType.FILE and not self._check_extension(item_path):
                           pass # Skip if extension not allowed
                        else:
                            stat_info = item_path.stat()
                            found_item_list.append(FoundItemInfo(
                                name=item_path.name,
                                relative_path=str(item_path.relative_to(self.workspace_root)),
                                absolute_path=str(item_path.resolve()),
                                type=item_type if item_type else WorkspaceItemType.OTHER, # Default if not file/dir after filter
                                size_bytes=stat_info.st_size if item_type == WorkspaceItemType.FILE else None,
                                modified_at=datetime.fromtimestamp(stat_info.st_mtime),
                                extension=item_path.suffix if item_type == WorkspaceItemType.FILE else None,
                                depth=current_depth
                            ))

                    if item_path.is_dir() and request.recursive:
                        _search_dir_recursive(item_path, current_depth + 1)

            _search_dir_recursive(search_root_abs_path, 0)
            found_item_list.sort(key=lambda x: x.relative_path)

            self._log_operation(WorkspaceOperation.FIND_FILES, search_root_abs_path, True, f"Found {len(found_item_list)} items matching pattern '{request.pattern}'.")
            return FindItemsResponse(success=True, search_path=request.relative_path, pattern_used=request.pattern, found_items=found_item_list, message="Search completed.")

        except Exception as e:
            final_path = search_root_abs_path or (self.workspace_root / request.relative_path)
            custom_exc = convert_standard_exception(e, str(final_path), WorkspaceOperation.FIND_FILES.value)
            self._log_operation(WorkspaceOperation.FIND_FILES, final_path, False, error=custom_exc)
            return FindItemsResponse(success=False, search_path=request.relative_path, pattern_used=request.pattern, found_items=[], message=str(custom_exc))

    def get_workspace_info(self, request: GetWorkspaceInfoRequest) -> GetWorkspaceInfoResponse:
        try:
            file_count = 0
            dir_count = 0
            total_size_bytes = 0

            for item in self.workspace_root.rglob('*'): # rglob includes subdirectories
                if item.is_file():
                    if self._check_extension(item): # Only count allowed files for size/count
                        file_count += 1
                        try: total_size_bytes += item.stat().st_size
                        except OSError: pass # File might be gone or inaccessible
                elif item.is_dir():
                    dir_count += 1

            # Human readable size
            if total_size_bytes < 1024: size_human = f"{total_size_bytes} B"
            elif total_size_bytes < 1024**2: size_human = f"{total_size_bytes/1024:.2f} KB"
            elif total_size_bytes < 1024**3: size_human = f"{total_size_bytes/1024**2:.2f} MB"
            else: size_human = f"{total_size_bytes/1024**3:.2f} GB"

            ws_info = WorkspaceInfo(
                workspace_root_path=str(self.workspace_root),
                total_items=file_count + dir_count,
                total_files=file_count,
                total_directories=dir_count,
                total_size_bytes=total_size_bytes,
                total_size_human=size_human,
                max_depth_setting=self.max_depth,
                configured_allowed_extensions=self.settings.allowed_extensions, # Original setting
                operations_logged_count=len(self.operation_log)
            )
            self._log_operation(WorkspaceOperation.WORKSPACE_INFO, self.workspace_root, True, "Retrieved workspace info.")
            return GetWorkspaceInfoResponse(success=True, workspace_info=ws_info, message="Workspace information retrieved.")
        except Exception as e:
            custom_exc = convert_standard_exception(e, str(self.workspace_root), WorkspaceOperation.WORKSPACE_INFO.value)
            self._log_operation(WorkspaceOperation.WORKSPACE_INFO, self.workspace_root, False, error=custom_exc)
            return GetWorkspaceInfoResponse(success=False, workspace_info=None, message=str(custom_exc))

    def cleanup_empty_directories(self, request: CleanupEmptyDirectoriesRequest) -> CleanupEmptyDirectoriesResponse:
        abs_start_path: Optional[Path] = None
        removed_dir_paths: List[RelativePath] = []
        try:
            abs_start_path = self._resolve_path(request.relative_path)
            if not abs_start_path.is_dir():
                raise InvalidFileTypeError("Path for cleanup must be a directory.", str(abs_start_path))

            # Iterate in reverse order (bottom-up) to remove child directories first
            for dirpath, _, _ in os.walk(str(abs_start_path), topdown=False):
                current_dir_path = Path(dirpath)
                # Ensure we don't try to remove the start_path itself unless it's empty and not workspace root
                # And also ensure it's within workspace (os.walk can go anywhere if start_path is not well contained)
                if not str(current_dir_path).startswith(str(self.workspace_root)): continue # Safety
                if current_dir_path == self.workspace_root and current_dir_path == abs_start_path : # Don't remove root if it's the start path
                     pass # Or if we are cleaning up workspace root itself, check if it's empty

                try:
                    if not any(current_dir_path.iterdir()): # Check if directory is empty
                        # Do not remove the root of the cleanup if it's the workspace root itself
                        if current_dir_path == self.workspace_root and abs_start_path == self.workspace_root:
                             continue # Skip deleting workspace root even if empty and targeted

                        current_dir_path.rmdir()
                        removed_dir_paths.append(str(current_dir_path.relative_to(self.workspace_root)))
                except OSError: # Not empty, or permission error
                    pass

            removed_dir_paths.sort()
            self._log_operation(WorkspaceOperation.CLEANUP_EMPTY_DIRS, abs_start_path, True, f"Removed {len(removed_dir_paths)} empty directories.")
            return CleanupEmptyDirectoriesResponse(success=True, cleaned_from_path=request.relative_path, removed_directories=removed_dir_paths, message="Cleanup completed.")
        except Exception as e:
            final_path = abs_start_path or (self.workspace_root / request.relative_path)
            custom_exc = convert_standard_exception(e, str(final_path), WorkspaceOperation.CLEANUP_EMPTY_DIRS.value)
            self._log_operation(WorkspaceOperation.CLEANUP_EMPTY_DIRS, final_path, False, error=custom_exc)
            return CleanupEmptyDirectoriesResponse(success=False, cleaned_from_path=request.relative_path, removed_directories=[], message=str(custom_exc))

    def get_operation_log(self, request: GetWorkspaceOperationLogRequest) -> GetWorkspaceOperationLogResponse:
        log_entries_copy = list(self.operation_log) # Work with a copy

        if request.filter_by_operation:
            log_entries_copy = [entry for entry in log_entries_copy if entry.operation == request.filter_by_operation]
        if request.filter_by_success is not None:
            log_entries_copy = [entry for entry in log_entries_copy if entry.success == request.filter_by_success]

        total_before_limit = len(log_entries_copy)

        # Add sorting if defined in model/request, e.g., by timestamp
        log_entries_copy.sort(key=lambda entry: entry.timestamp, reverse=True) # Default sort: newest first

        if request.limit is not None and request.limit > 0:
            log_entries_copy = log_entries_copy[:request.limit]

        return GetWorkspaceOperationLogResponse(
            success=True,
            log_entries=log_entries_copy,
            total_entries_before_limit=total_before_limit,
            message="Workspace operation log retrieved."
        )

    def clear_operation_log(self, request: ClearWorkspaceOperationLogRequest) -> ClearWorkspaceOperationLogResponse:
        count = len(self.operation_log)
        self.operation_log.clear()
        # Consider logging this action to an external system or FileHandler's log if appropriate
        return ClearWorkspaceOperationLogResponse(success=True, cleared_count=count, message=f"{count} workspace log entries cleared.")


# Example usage and testing functions (needs to be updated for Pydantic models)
if __name__ == "__main__":
    import tempfile
    # To run this __main__ block directly (e.g. `python src/file_manager_project/workspace_manager.py`),
    # Python needs to find sibling modules. This typically requires the parent of
    # 'file_manager_project' (i.e., 'src') to be in PYTHONPATH, or using `python -m file_manager_project.workspace_manager`.
    # For simplicity in direct execution, one might add:
    # import sys
    # sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) # Adds 'src' to path

    from .file_handler_models import WriteFileRequest as FH_WriteFileRequest # Corrected relative import

    # Example usage with temporary workspace and Pydantic models
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir_path = Path(temp_dir_str)
        print(f"Attempting to initialize WorkspaceManager in: {temp_dir_path}")

        try:
            # 1. Initialize Settings
            ws_settings = WorkspaceManagerSettings(
                workspace_root=temp_dir_path,
                create_if_missing=True,  # Explicitly provide, though it has a default
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json']
            )

            # 2. Initialize WorkspaceManager
            workspace = WorkspaceManager(settings=ws_settings)
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")

            # 3. Demonstrate Create Directory
            print("\n--- Create Directory ---")
            create_dir_req = CreateDirectoryRequest(relative_path="projects/ai-agent", parents=True)
            create_dir_resp = workspace.create_directory(create_dir_req)
            print(f"Create Dir Response: Success: {create_dir_resp.success}, Path: {create_dir_resp.created_path}, Existed: {create_dir_resp.already_existed}, Msg: {create_dir_resp.message}")
            if not create_dir_resp.success: raise Exception(f"Create dir failed: {create_dir_resp.message}")

            create_dir_req_data = CreateDirectoryRequest(relative_path="data/raw_data", parents=True)
            workspace.create_directory(create_dir_req_data) # Ignoring response for brevity

            # 4. Use FileHandler (via WorkspaceManager) to create a file
            print("\n--- Write File (via FileHandler) ---")
            # FileHandler methods now also expect Pydantic request models

            # Correct way: FileHandler's paths are relative to its base_directory (which is workspace_root)
            # So, "projects/ai-agent/main.py" is correct if FileHandler is based at workspace_root.
            write_file_req = FH_WriteFileRequest(file_path="projects/ai-agent/main.py", content="# AI Agent Main File\nprint('Hello Pydantic World!')", encoding="utf-8", overwrite=True)
            write_file_resp = workspace.file_handler.write_file(write_file_req)
            print(f"Write File Response: Success: {write_file_resp.success}, Path: {write_file_resp.file_path}, Msg: {write_file_resp.message}")
            if not write_file_resp.success: raise Exception(f"Write file failed: {write_file_resp.message}")

            workspace.file_handler.write_file(FH_WriteFileRequest(file_path="README.md", content="# Main Readme", encoding="utf-8", overwrite=True))

            # 5. List Directory
            print("\n--- List Directory (Root) ---")
            list_req_root = ListDirectoryRequest(relative_path=".", include_hidden=False, filter_types=None)
            list_resp_root = workspace.list_directory(list_req_root)
            print(f"List Dir (Root) Response: Success: {list_resp_root.success}, Path: {list_resp_root.path_listed}, Items: {len(list_resp_root.items)}, Msg: {list_resp_root.message}")
            if list_resp_root.success:
                for item_model in list_resp_root.items: # Renamed to avoid clash with loop var below
                    print(f"  - {item_model.name} (Type: {item_model.type}, RelPath: {item_model.relative_path})")
            else: raise Exception(f"List dir root failed: {list_resp_root.message}")

            print("\n--- List Directory (projects/ai-agent) ---")
            list_req_proj = ListDirectoryRequest(relative_path="projects/ai-agent", include_hidden=False, filter_types=None)
            list_resp_proj = workspace.list_directory(list_req_proj)
            print(f"List Dir (Proj) Response: Success: {list_resp_proj.success}, Items: {len(list_resp_proj.items)}")
            if list_resp_proj.success:
                 for item_model in list_resp_proj.items: print(f"  - {item_model.name} (Type: {item_model.type})")


            # 6. Find Items
            print("\n--- Find Items (*.py) ---")
            find_req = FindItemsRequest(pattern="*.py", recursive=True, relative_path=".", item_types=[WorkspaceItemType.FILE])
            find_resp = workspace.find_items(find_req)
            print(f"Find Items Response: Success: {find_resp.success}, Found: {len(find_resp.found_items)}, Msg: {find_resp.message}")
            if find_resp.success:
                for found_item in find_resp.found_items: # Renamed for clarity
                    print(f"  - {found_item.relative_path} (Size: {found_item.size_bytes if found_item.size_bytes else 'N/A'})")

            # 7. Get Workspace Info
            print("\n--- Get Workspace Info ---")
            info_req = GetWorkspaceInfoRequest()
            info_resp = workspace.get_workspace_info(info_req)
            print(f"Workspace Info Response: Success: {info_resp.success}, Msg: {info_resp.message}")
            if info_resp.success and info_resp.workspace_info:
                print(f"  Root: {info_resp.workspace_info.workspace_root_path}")
                print(f"  Total Files: {info_resp.workspace_info.total_files}, Total Dirs: {info_resp.workspace_info.total_directories}")
                print(f"  Total Size: {info_resp.workspace_info.total_size_human}")

            # 8. Copy and Move Item
            print("\n--- Copy & Move Item ---")
            copy_req = CopyItemRequest(source_relative_path="README.md", destination_relative_path="README_backup.md", overwrite=False)
            copy_resp = workspace.copy_item(copy_req)
            print(f"Copy Response: {copy_resp.success} - {copy_resp.message}")

            move_req = MoveItemRequest(source_relative_path="README_backup.md", destination_relative_path="data/README_moved.md", overwrite=False)
            move_resp = workspace.move_item(move_req)
            print(f"Move Response: {move_resp.success} - {move_resp.message}")

            # 9. Delete Item
            print("\n--- Delete Item ---")
            # delete_req = DeleteItemRequest(relative_path="data/README_moved.md")
            # delete_resp = workspace.delete_item(delete_req)
            # print(f"Delete File Response: {delete_resp.success} - {delete_resp.message}")

            # Delete a directory (force=True for non-empty, or ensure it's empty)
            # Forcing deletion of 'projects' which contains 'ai-agent/main.py'
            delete_dir_req = DeleteItemRequest(relative_path="projects", force=True)
            delete_dir_resp = workspace.delete_item(delete_dir_req)
            print(f"Delete Dir Response: {delete_dir_resp.success} - {delete_dir_resp.message}")


            # 10. Cleanup Empty Directories (data/raw_data should be empty now)
            print("\n--- Cleanup Empty Directories ---")
            cleanup_req = CleanupEmptyDirectoriesRequest(relative_path="data") # Target 'data'
            cleanup_resp = workspace.cleanup_empty_directories(cleanup_req)
            print(f"Cleanup Response: Success: {cleanup_resp.success}, Removed: {cleanup_resp.removed_directories}, Msg: {cleanup_resp.message}")


            # 11. Show Operation Log
            print("\n--- Workspace Operation Log ---")
            log_req = GetWorkspaceOperationLogRequest(limit=15, filter_by_operation=None, filter_by_success=None)
            log_resp = workspace.get_operation_log(log_req)
            if log_resp.success:
                print(f"Displaying last {len(log_resp.log_entries)} of {log_resp.total_entries_before_limit} workspace operations:")
                for entry in log_resp.log_entries:
                    status = "✅" if entry.success else "❌"
                    ts = entry.timestamp.strftime('%H:%M:%S')
                    print(f"  {ts} {status} {entry.operation.value}: {entry.relative_path or entry.path} - {entry.details} (Err: {entry.error_type or 'N/A'})")

        except ValidationError as ve:
             print(f"❌ Pydantic Validation Error during setup or operation: {ve}")
        except ConfigurationError as ce:
            print(f"❌ Configuration Error: {ce}")
        except FileManagerError as fme:
            print(f"❌ FileManagerError: {fme}")
        except Exception as e:
            print(f"❌ An unexpected error occurred in the demo: {e}")
            import traceback
            traceback.print_exc()
