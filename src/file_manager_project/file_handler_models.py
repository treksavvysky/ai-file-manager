"""
Pydantic models for FileHandler requests and responses.
"""
from typing import Optional, List, Dict, Any, Union
from typing_extensions import TypeAlias # For Python < 3.10
from pydantic import BaseModel, Field, FilePath as PydanticFilePath # Renamed to avoid conflict
from datetime import datetime
from enum import Enum

# Enums

class FileOperation(str, Enum):
    """Enum for file operations, used in logging."""
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    EXISTS_CHECK = "exists_check"
    INFO = "info"
    LIST_ITEM_ERROR = "list_item_error" # From WorkspaceManager, but good to have a general one

class LogSortField(str, Enum):
    """Enum for sorting log entries."""
    TIMESTAMP = "timestamp"
    OPERATION = "operation"
    FILE_PATH = "file_path"
    SUCCESS = "success"

# Base Models

class BaseRequest(BaseModel):
    """Base model for requests, can include common fields like user_id if needed later."""
    pass

class BaseResponse(BaseModel):
    """Base model for responses, includes success status and optional message."""
    success: bool = Field(..., description="Indicates whether the operation was successful.")
    message: Optional[str] = Field(None, description="An optional message providing more details about the operation's outcome.")

# Use PydanticFilePath directly where StrictFilePath was used.
# Pydantic's FilePath is generally strict enough.

# Models for FileHandler methods

# read_file
class ReadFileRequest(BaseRequest):
    file_path: PydanticFilePath = Field(..., description="Path to the file to read.")
    encoding: str = Field('utf-8', description="File encoding.")

class ReadFileResponse(BaseResponse):
    content: Optional[str] = Field(None, description="File content as a string, if successful.")
    file_path: str = Field(..., description="The validated, absolute path of the file read.")
    encoding: str = Field(..., description="The encoding used to read the file.")
    size_bytes: Optional[int] = Field(None, description="Size of the read content in bytes.")

# write_file
class WriteFileRequest(BaseRequest):
    file_path: PydanticFilePath = Field(..., description="Path to the file to write.")
    content: str = Field(..., description="Content to write to the file.")
    encoding: str = Field('utf-8', description="File encoding.")
    overwrite: bool = Field(True, description="Whether to overwrite the file if it already exists.")

class WriteFileResponse(BaseResponse):
    file_path: str = Field(..., description="The validated, absolute path of the written file.")
    bytes_written: Optional[int] = Field(None, description="Number of bytes written, if successful.")
    overwrite_used: bool = Field(..., description="Indicates if the overwrite flag was effectively used (i.e., file existed and was overwritten).")

# append_file
class AppendFileRequest(BaseRequest):
    file_path: PydanticFilePath = Field(..., description="Path to the file to append to.")
    content: str = Field(..., description="Content to append.")
    encoding: str = Field('utf-8', description="File encoding.")

class AppendFileResponse(BaseResponse):
    file_path: str = Field(..., description="The validated, absolute path of the appended file.")
    bytes_appended: Optional[int] = Field(None, description="Number of bytes appended, if successful.")

# file_exists
class FileExistsRequest(BaseRequest):
    file_path: PydanticFilePath = Field(..., description="Path to the file to check for existence.")

class FileExistsResponse(BaseResponse):
    exists: bool = Field(..., description="True if the file exists, False otherwise.")
    file_path: str = Field(..., description="The validated, absolute path that was checked.")
    is_file: Optional[bool] = Field(None, description="True if the path points to a file, False if a directory, None if path doesn't exist.")

# get_file_info
class GetFileInfoRequest(BaseRequest):
    file_path: PydanticFilePath = Field(..., description="Path to the file to get information for.")

class FileInfo(BaseModel):
    name: str = Field(..., description="Name of the file or directory.")
    size_bytes: int = Field(..., description="Size of the file in bytes.")
    created_at: datetime = Field(..., description="Timestamp of when the file was created.")
    modified_at: datetime = Field(..., description="Timestamp of when the file was last modified.")
    is_file: bool = Field(..., description="True if the path is a file.")
    is_directory: bool = Field(..., description="True if the path is a directory.")
    absolute_path: str = Field(..., description="Absolute path to the file.")
    extension: Optional[str] = Field(None, description="File extension, if applicable.")
    stem: str = Field(..., description="File name without the extension.")
    is_readable: bool = Field(..., description="True if the file is readable.")
    is_writable: bool = Field(..., description="True if the file is writable.")
    is_executable: bool = Field(..., description="True if the file is executable.")

class GetFileInfoResponse(BaseResponse):
    file_info: Optional[FileInfo] = Field(None, description="Detailed information about the file, if successful.")
    file_path: str = Field(..., description="The validated, absolute path for which info was requested.")

# Operation Log Models
class OperationLogEntry(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the operation.")
    operation: FileOperation = Field(..., description="Type of operation performed.")
    file_path: str = Field(..., description="File path involved in the operation.")
    success: bool = Field(..., description="Whether the operation was successful.")
    details: str = Field(..., description="Additional details about the operation.")
    error_type: Optional[str] = Field(None, description="Type of error if the operation failed.")
    # Potentially add user_id, request_id, etc. in a real system

class GetOperationLogRequest(BaseRequest):
    filter_by_operation: Optional[FileOperation] = Field(None, description="Filter log entries by operation type.")
    filter_by_success: Optional[bool] = Field(None, description="Filter log entries by success status.")
    sort_by: Optional[LogSortField] = Field(LogSortField.TIMESTAMP, description="Field to sort the log entries by.")
    sort_ascending: bool = Field(True, description="Whether to sort in ascending order.")
    limit: Optional[int] = Field(None, description="Maximum number of log entries to return.")

class GetOperationLogResponse(BaseResponse):
    log_entries: List[OperationLogEntry] = Field(..., description="List of operation log entries.")
    total_entries: int = Field(..., description="Total number of entries matching the filter before applying limit.")

# clear_operation_log
class ClearOperationLogRequest(BaseRequest):
    pass

class ClearOperationLogResponse(BaseResponse):
    cleared_count: int = Field(..., description="Number of log entries cleared.")

# get_error_summary
class GetErrorSummaryRequest(BaseRequest):
    pass

class ErrorSummary(BaseModel):
    error_type: str = Field(..., description="The type of error.")
    count: int = Field(..., description="Number of times this error occurred.")

class GetErrorSummaryResponse(BaseResponse):
    error_summaries: List[ErrorSummary] = Field(..., description="Summary of errors from the operation log.")
    total_errors: int = Field(..., description="Total number of errors recorded.")

from pydantic_settings import BaseSettings, SettingsConfigDict

# Model for FileHandler constructor arguments, using pydantic-settings
class FileHandlerSettings(BaseSettings):
    base_directory: Optional[PydanticFilePath] = Field(default=None, description="Optional base directory to restrict operations to. If set, all file paths will be relative to this directory.")
    max_file_size: int = Field(default=10 * 1024 * 1024, gt=0, description="Maximum file size in bytes (default: 10MB).")

    model_config = SettingsConfigDict(
        env_prefix='FILE_HANDLER_',
        env_file='.env', # Example: load from .env file
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra fields from .env or environment
    )

# Example of a discriminated union if FileHandler had a more complex return type
# (Commented out example block removed to prevent parsing issues)

# Note: The current FileHandler methods are fairly straightforward and might not
# heavily benefit from discriminated unions in their immediate return types,
# but the concept is noted for potential future complexity or for WorkspaceManager.
# The OperationLogEntry.operation uses an Enum, which is a form of "rich enum".
# The FileInfo model is a "rich" structure for file details.
# StrictFilePath provides path validation. Descriptions are added to all fields.
# mypy-strict will be handled during the mypy configuration and checking phase.
# pydantic-settings usage will be more prominent when we refactor the class __init__.
# For now, FileHandlerSettings is a placeholder for that.
# """ # Removed, as this seems to be the source of the unterminated string literal error.
# The file should end after the last relevant code or comment.
