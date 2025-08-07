"""
Pydantic models for WorkspaceManager requests and responses.
"""
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, DirectoryPath, FilePath
from datetime import datetime
from enum import Enum

# Assuming FileHandler models might be relevant for parts of WorkspaceManager,
# especially if it exposes FileHandler's log or settings.
# For now, focusing on WorkspaceManager specific models.
try:
    from .file_handler_models import FileHandlerSettings, OperationLogEntry as FileHandlerOperationLogEntry, FileOperation as FileHandlerFileOperation
except ImportError:
    # Fallback for direct execution or different structure
    # This might mean some types are less specific if not found
    FileHandlerSettings = Any # type: ignore
    FileHandlerOperationLogEntry = Any # type: ignore
    FileHandlerFileOperation = Any # type: ignore


# Enums
class WorkspaceItemType(str, Enum):
    """Type of item in the workspace."""
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink" # For list_directory potentially
    OTHER = "other"

class WorkspaceOperation(str, Enum):
    """Enum for workspace operations, used in logging."""
    WORKSPACE_CREATED = "workspace_created"
    WORKSPACE_VALIDATED = "workspace_validated"
    LIST_DIRECTORY = "list_directory"
    LIST_ITEM_ERROR = "list_item_error" # Error listing a specific item
    CREATE_DIRECTORY = "create_directory"
    MOVE_ITEM = "move_item"
    COPY_ITEM = "copy_item"
    DELETE_ITEM = "delete_item"
    FIND_FILES = "find_files"
    WORKSPACE_INFO = "workspace_info"
    CLEANUP_EMPTY_DIRS = "cleanup_empty_directories"
    # Add others as needed

# Base Models (can be shared or defined in a common models file)
class BaseRequest(BaseModel):
    pass

class BaseResponse(BaseModel):
    success: bool = Field(..., description="Indicates whether the operation was successful.")
    message: Optional[str] = Field(None, description="An optional message providing more details about the operation's outcome.")

# Path types specific to workspace
# Pydantic's DirectoryPath validates if a path exists and is a directory.
# This might be too strict for paths that are *to be created*.
# We'll use simple str for relative paths within the workspace for now,
# and resolve/validate them inside WorkspaceManager.
# Absolute paths can use DirectoryPath or FilePath if they must exist.

RelativePath = str # For paths relative to workspace root

from pydantic_settings import BaseSettings, SettingsConfigDict

# Models for WorkspaceManager constructor arguments
class WorkspaceManagerSettings(BaseSettings):
    workspace_root: DirectoryPath = Field(..., description="Root directory for all workspace operations. Must exist and be a directory if not created by logic.")
    # file_handler_settings: Optional[FileHandlerSettings] = Field(None, description="Settings for the internal FileHandler. If None, FileHandler uses defaults.") # If we pass settings down
    create_if_missing: bool = Field(default=True, description="If True, WorkspaceManager will attempt to create workspace_root if it doesn't exist. Note: DirectoryPath by default validates existence, so custom validation or pre-creation logic might be needed in WorkspaceManager.__init__ if this is True and path doesn't exist.")
    max_depth: int = Field(default=10, gt=0, description="Maximum directory traversal depth for safety.")
    allowed_extensions: Optional[List[str]] = Field(default=None, description="Optional list of allowed file extensions (e.g., ['.txt', '.py']). Case-insensitive.")

    model_config = SettingsConfigDict(
        env_prefix='WORKSPACE_MANAGER_',
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

# list_directory
class ItemInfoBase(BaseModel):
    name: str = Field(..., description="Name of the file or directory.")
    relative_path: RelativePath = Field(..., description="Path relative to the workspace root.")
    is_hidden: bool = Field(..., description="True if the item is hidden (starts with a dot).")
    modified_at: datetime = Field(..., description="Timestamp of when the item was last modified.")
    permissions: Optional[str] = Field(None, description="Permissions string (e.g., '755'), if available.")

class FileItemInfo(ItemInfoBase):
    type: Literal[WorkspaceItemType.FILE] = WorkspaceItemType.FILE
    size_bytes: int = Field(..., description="Size of the file in bytes.")
    extension: Optional[str] = Field(None, description="File extension.")

class DirectoryItemInfo(ItemInfoBase):
    type: Literal[WorkspaceItemType.DIRECTORY] = WorkspaceItemType.DIRECTORY
    # size_bytes: Optional[int] = Field(None, description="Size of directory contents (often None or not easily calculated).") # Typically not provided for dirs

class OtherItemInfo(ItemInfoBase):
    type: Literal[WorkspaceItemType.SYMLINK, WorkspaceItemType.OTHER] # More specific types can be added
    actual_type_detail: str = Field(..., description="Detailed type if not file or directory (e.g., 'symlink', 'socket').")


# Using discriminated union for items in a directory listing
ListItem = Union[FileItemInfo, DirectoryItemInfo, OtherItemInfo]

class ListDirectoryRequest(BaseRequest):
    relative_path: RelativePath = Field(".", description="Directory path relative to workspace root. Defaults to workspace root.")
    include_hidden: bool = Field(False, description="Whether to include hidden files/directories (those starting with a dot).")
    filter_types: Optional[List[WorkspaceItemType]] = Field(None, description="Optional filter for item types (e.g., ['file', 'directory']).")

class ListDirectoryResponse(BaseResponse):
    path_listed: RelativePath = Field(..., description="The relative path of the directory that was listed.")
    items: List[ListItem] = Field([], description="List of items in the directory. Empty if directory is empty or on failure.")
    # Replaced files, directories, other with a single items list using discriminated union
    # files: List[FileItemInfo] = Field(default_factory=list, description="List of files in the directory.")
    # directories: List[DirectoryItemInfo] = Field(default_factory=list, description="List of sub-directories.")
    # other_items: List[OtherItemInfo] = Field(default_factory=list, description="List of other item types (symlinks, etc.).")


# create_directory
class CreateDirectoryRequest(BaseRequest):
    relative_path: RelativePath = Field(..., description="Directory path to create, relative to workspace root.")
    parents: bool = Field(True, description="If True, create parent directories as needed. If False, raises error if parent doesn't exist.")

class CreateDirectoryResponse(BaseResponse):
    created_path: Optional[RelativePath] = Field(None, description="The relative path of the directory that was created/confirmed to exist.")
    already_existed: Optional[bool] = Field(None, description="True if the directory already existed and was not newly created.")


# move_item
class MoveItemRequest(BaseRequest):
    source_relative_path: RelativePath = Field(..., description="Source path relative to workspace root.")
    destination_relative_path: RelativePath = Field(..., description="Destination path relative to workspace root.")
    overwrite: bool = Field(False, description="Whether to overwrite the destination if it already exists.")

class MoveItemResponse(BaseResponse):
    source_path: Optional[RelativePath] = Field(None, description="The source relative path of the item that was moved.")
    destination_path: Optional[RelativePath] = Field(None, description="The destination relative path.")


# copy_item
class CopyItemRequest(BaseRequest):
    source_relative_path: RelativePath = Field(..., description="Source path relative to workspace root.")
    destination_relative_path: RelativePath = Field(..., description="Destination path relative to workspace root.")
    overwrite: bool = Field(False, description="Whether to overwrite the destination if it already exists.")

class CopyItemResponse(BaseResponse):
    source_path: Optional[RelativePath] = Field(None, description="The source relative path of the item that was copied.")
    destination_path: Optional[RelativePath] = Field(None, description="The new relative path of the copied item.")


# delete_item
class DeleteItemRequest(BaseRequest):
    relative_path: RelativePath = Field(..., description="Path to delete, relative to workspace root.")
    force: bool = Field(False, description="If True, allows deletion of non-empty directories. Use with caution.")

class DeleteItemResponse(BaseResponse):
    deleted_path: Optional[RelativePath] = Field(None, description="The relative path of the item that was deleted.")
    item_type: Optional[WorkspaceItemType] = Field(None, description="Type of the item that was deleted.")


# find_files (now find_items to be more general)
class FoundItemInfo(BaseModel): # Similar to ListItem, but might include absolute_path or depth
    name: str = Field(..., description="Name of the found item.")
    relative_path: RelativePath = Field(..., description="Path relative to the workspace root.")
    absolute_path: str = Field(..., description="Absolute path of the found item.")
    type: WorkspaceItemType = Field(..., description="Type of the found item (file, directory).")
    size_bytes: Optional[int] = Field(None, description="Size in bytes, if a file.")
    modified_at: datetime = Field(..., description="Timestamp of last modification.")
    extension: Optional[str] = Field(None, description="File extension, if applicable and a file.")
    depth: int = Field(..., description="Search depth at which the item was found (0 for items in the immediate relative_path).")

class FindItemsRequest(BaseRequest):
    pattern: str = Field("*", description="Glob pattern to match (e.g., '*.txt', 'data_*'). Case-insensitive matching for names.")
    relative_path: RelativePath = Field(".", description="Directory to search in, relative to workspace root. Defaults to workspace root.")
    recursive: bool = Field(True, description="Whether to search subdirectories.")
    item_types: Optional[List[WorkspaceItemType]] = Field(None, description="Filter by item types (e.g., ['file', 'directory']). If None, matches all types.")
    # Consider adding max_results, content_search_keyword, etc. for advanced find

class FindItemsResponse(BaseResponse):
    search_path: RelativePath = Field(..., description="The relative path where the search was performed.")
    pattern_used: str = Field(..., description="The glob pattern used for searching.")
    found_items: List[FoundItemInfo] = Field(default_factory=list, description="List of items matching the criteria.")


# get_workspace_info
class WorkspaceInfo(BaseModel):
    workspace_root_path: str = Field(..., description="Absolute path to the workspace root.")
    total_items: int = Field(..., description="Total number of files and directories in the workspace (approximate, may vary based on scan depth/filters).")
    total_files: int = Field(..., description="Total number of files.")
    total_directories: int = Field(..., description="Total number of directories (excluding root).")
    total_size_bytes: int = Field(..., description="Total size of all files in bytes.")
    total_size_human: str = Field(..., description="Total size in human-readable format (e.g., MB, GB).")
    # created_at: datetime = Field(..., description="Timestamp of workspace root creation.") # Not always reliable or available across OS
    # modified_at: datetime = Field(..., description="Timestamp of last modification in workspace (heuristic).")
    max_depth_setting: int = Field(..., description="Configured maximum directory traversal depth.")
    configured_allowed_extensions: Optional[List[str]] = Field(None, description="Configured list of allowed file extensions.")
    operations_logged_count: int = Field(..., description="Number of operations logged in this session for WorkspaceManager.")

class GetWorkspaceInfoRequest(BaseRequest):
    pass # No specific parameters for now

class GetWorkspaceInfoResponse(BaseResponse):
    workspace_info: Optional[WorkspaceInfo] = Field(None, description="Comprehensive information about the workspace.")


# cleanup_empty_directories
class CleanupEmptyDirectoriesRequest(BaseRequest):
    relative_path: RelativePath = Field(".", description="Directory to start cleanup from, relative to workspace root. Defaults to workspace root.")
    # dry_run: bool = Field(False, description="If True, simulate cleanup and report what would be deleted without actual deletion.") # Future enhancement

class CleanupEmptyDirectoriesResponse(BaseResponse):
    cleaned_from_path: RelativePath = Field(..., description="The relative path from which cleanup was initiated.")
    removed_directories: List[RelativePath] = Field(default_factory=list, description="List of relative paths of empty directories that were removed.")
    # candidate_directories: Optional[List[RelativePath]] = Field(None, description="List of directories that would be removed if dry_run was True.")


# Operation Log for WorkspaceManager
class WorkspaceOperationLogEntry(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the operation.")
    operation: WorkspaceOperation = Field(..., description="Type of workspace operation performed.")
    path: str = Field(..., description="Main path involved in the operation (absolute or context-dependent).")
    relative_path: Optional[RelativePath] = Field(None, description="Path relative to workspace root, if applicable.")
    success: bool = Field(..., description="Whether the operation was successful.")
    details: str = Field(..., description="Additional details about the operation.")
    error_type: Optional[str] = Field(None, description="Type of error if the operation failed.")

class GetWorkspaceOperationLogRequest(BaseRequest):
    filter_by_operation: Optional[WorkspaceOperation] = Field(None, description="Filter log entries by operation type.")
    filter_by_success: Optional[bool] = Field(None, description="Filter log entries by success status.")
    # sort_by, limit etc. can be added similar to FileHandler's log request
    limit: Optional[int] = Field(None, gt=0, description="Limit the number of log entries returned.")

class GetWorkspaceOperationLogResponse(BaseResponse):
    log_entries: List[WorkspaceOperationLogEntry] = Field(default_factory=list, description="List of workspace operation log entries.")
    total_entries_before_limit: int = Field(0, description="Total number of entries matching filters before applying any limit.")


class ClearWorkspaceOperationLogRequest(BaseRequest):
    pass

class ClearWorkspaceOperationLogResponse(BaseResponse):
    cleared_count: int = Field(..., description="Number of workspace log entries cleared.")

# Combining FileHandler logs if WorkspaceManager exposes them
class GetCombinedOperationLogRequest(BaseRequest):
    # Add filters for both FileHandler and WorkspaceManager logs if needed
    limit_per_log_type: Optional[int] = Field(None, gt=0, description="Limit entries from each log type (FileHandler, WorkspaceManager).")

class CombinedOperationLogResponse(BaseResponse):
    file_handler_logs: List[FileHandlerOperationLogEntry] = Field(default_factory=list) # Type with actual model if available
    workspace_manager_logs: List[WorkspaceOperationLogEntry] = Field(default_factory=list)
    # Could also merge and sort them if timestamps are compatible

# """ # Removed, as this seems to be the source of the unterminated string literal error.
