"""
Pydantic models describing the data carried by custom exceptions.
These models can be used for serializing error details or for structured error responses.
"""
from typing import Optional, Union, List
from typing_extensions import Literal # For Python < 3.8, Literal is in typing_extensions
from pydantic import BaseModel, Field, FilePath as PydanticFilePath, DirectoryPath as PydanticDirectoryPath
from pathlib import Path

# A generic Path type for fields that could be file or directory
# Pydantic's FilePath and DirectoryPath are strict about existence by default in some contexts,
# so using a simple string or a custom validator might be needed if the path doesn't always exist.
# For now, we'll use string and specify in description.
GeneralPath = str # Or Union[PydanticFilePath, PydanticDirectoryPath] if paths are validated to exist

class BaseErrorDetail(BaseModel):
    """Base model for error details."""
    error_type: str = Field(..., description="The class name of the exception that was raised.")
    message: str = Field(..., description="The main error message.")
    file_path: Optional[GeneralPath] = Field(None, description="File or directory path related to the error, if applicable.")

class PathValidationErrorDetail(BaseErrorDetail):
    error_type: Literal["PathValidationError"] = "PathValidationError"
    # file_path: GeneralPath = Field(..., description="The problematic path that failed validation.") # Already in BaseErrorDetail

class FileOperationErrorDetail(BaseErrorDetail):
    error_type: Literal["FileOperationError"] = "FileOperationError"
    operation: Optional[str] = Field(None, description="The file operation that failed (e.g., 'read', 'write').")

class FileNotFoundErrorDetail(BaseErrorDetail):
    error_type: Literal["FileNotFoundError"] = "FileNotFoundError" # CustomFileNotFoundError
    # file_path: GeneralPath = Field(..., description="The path that was not found.")

class FileAlreadyExistsErrorDetail(BaseErrorDetail):
    error_type: Literal["FileAlreadyExistsError"] = "FileAlreadyExistsError"
    # file_path: GeneralPath = Field(..., description="The path that already exists.")

class InvalidFileTypeErrorDetail(BaseErrorDetail):
    error_type: Literal["InvalidFileTypeError"] = "InvalidFileTypeError"
    expected_type: Optional[str] = Field(None, description="Expected file type or format.")
    actual_type: Optional[str] = Field(None, description="Actual detected file type or format.")

class FileSizeErrorDetail(BaseErrorDetail):
    error_type: Literal["FileSizeError"] = "FileSizeError"
    current_size_bytes: Optional[int] = Field(None, description="Current file or content size in bytes.")
    limit_size_bytes: Optional[int] = Field(None, description="The size limit that was exceeded in bytes.")

class EncodingErrorDetail(BaseErrorDetail):
    error_type: Literal["EncodingError"] = "EncodingError"
    encoding: Optional[str] = Field(None, description="The encoding that caused the error.")

class ConfigurationErrorDetail(BaseErrorDetail):
    error_type: Literal["ConfigurationError"] = "ConfigurationError"
    # No specific extra fields defined for ConfigurationError in existing exceptions.py

class SecurityErrorDetail(BaseErrorDetail):
    error_type: Literal["SecurityError"] = "SecurityError"
    # No specific extra fields defined for SecurityError in existing exceptions.py

class ConcurrencyErrorDetail(BaseErrorDetail): # Assuming ConcurrencyError exists or might be added
    error_type: Literal["ConcurrencyError"] = "ConcurrencyError"
    # Details like resource_id, conflicting_process_id could be added if applicable

# A discriminated union for all possible error details
# This could be useful if an API endpoint always returns a structured error from this set.
ErrorDetail = Union[
    PathValidationErrorDetail,
    FileOperationErrorDetail,
    FileNotFoundErrorDetail,
    FileAlreadyExistsErrorDetail,
    InvalidFileTypeErrorDetail,
    FileSizeErrorDetail,
    EncodingErrorDetail,
    ConfigurationErrorDetail,
    SecurityErrorDetail,
    ConcurrencyErrorDetail, # Add if ConcurrencyError is used
    BaseErrorDetail # Fallback for generic FileManagerError or other exceptions
]

# Example of how an API might structure an error response:
# class APIErrorResponse(BaseModel):
#     request_id: str
#     timestamp: datetime
#     error: ErrorDetail = Field(..., discriminator='error_type')

# For now, the primary use of these models will be to potentially structure
# the 'message' field in our existing `BaseResponse` models when `success=False`.
# For example, a method could catch an exception, populate one of these detail models,
# and then set `response.message = error_detail_model.model_dump_json()`.

# It's important to note that the custom exception classes themselves (`PathValidationError`, etc.)
# will NOT inherit from these Pydantic models directly in this approach.
# They remain standard Python exceptions. These models are for describing their data.
# """ <--- Removed this problematic line and the one above it.
# The previous content was a multiline comment using triple quotes,
# which is fine, but it seems mypy detected it as an unterminated string literal
# if there was any issue with its formatting or if it was meant to be a docstring for something.
# Ensuring it's just comments or properly formatted docstrings.
# The actual issue was likely an extra `"""` at the very end of the file or similar.
# For now, I'll assume the file should end after the last relevant comment.
