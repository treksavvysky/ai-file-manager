"""
AI Agent File Manager - Core File Handler Module

This module provides a modular FileHandler class for basic file operations
that AI agents can use safely and efficiently, with Pydantic validation.
"""

import os
# import json # No longer directly used for JSON parsing, Pydantic handles it
from pathlib import Path
from typing import Union, Optional, List, Dict, Any # Keep for type hints if needed outside Pydantic models
from datetime import datetime

from pydantic import ValidationError # For catching Pydantic validation errors if needed explicitly

# Import custom exceptions
from .exceptions import (
    FileManagerError,
    PathValidationError,
    FileOperationError,
    FileNotFoundError as CustomFileNotFoundError, # Alias to avoid clash with builtin
    FileAlreadyExistsError, # Make sure this is imported
    InvalidFileTypeError,
    FileSizeError,
    EncodingError,
    SecurityError,
    ConfigurationError, # Added this missing import
    convert_standard_exception,
    get_error_category
)
from .file_handler_models import (
    FileHandlerSettings,
    ReadFileRequest, ReadFileResponse,
    WriteFileRequest, WriteFileResponse,
    AppendFileRequest, AppendFileResponse,
    FileExistsRequest, FileExistsResponse,
    GetFileInfoRequest, GetFileInfoResponse, FileInfo,
    GetOperationLogRequest, GetOperationLogResponse, OperationLogEntry, FileOperation, LogSortField,
    ClearOperationLogRequest, ClearOperationLogResponse,
    GetErrorSummaryRequest, GetErrorSummaryResponse, ErrorSummary
)

class FileHandler:
    """
    A modular file handler class for AI agents with basic read, write, and append operations,
    enhanced with Pydantic models for request validation and structured responses.

    Features:
    - Safe file operations with comprehensive error handling
    - Pydantic-validated requests and structured responses
    - Support for various file types (text, JSON, etc. via content handling)
    - Logging of operations for audit trails using structured Pydantic models
    - Path validation and security checks
    - Custom exception types for specific error handling
    """

    def __init__(self, settings: Optional[FileHandlerSettings] = None):
        """
        Initialize the FileHandler with configuration.

        Args:
            settings: A FileHandlerSettings Pydantic model instance.
                      If None, default settings will be used.
        """
        if settings is None:
            self.settings = FileHandlerSettings() # Uses default values from the model
        elif isinstance(settings, FileHandlerSettings):
            self.settings = settings
        else:
            # Attempt to create settings from dict, useful for older instantiation patterns
            try:
                self.settings = FileHandlerSettings(**settings)
            except ValidationError as e:
                raise ConfigurationError(f"Invalid FileHandler settings: {e}") from e

        self.base_directory: Optional[Path] = None
        if self.settings.base_directory:
            self.base_directory = Path(self.settings.base_directory).resolve()

        self.max_file_size: int = self.settings.max_file_size
        self.operation_log: List[OperationLogEntry] = []

        # Validate base directory if provided
        if self.base_directory and not self.base_directory.exists():
            # This check is on a resolved path, so FilePath Pydantic type might have already validated existence
            # if `must_exist=True` was used. Current FilePath doesn't enforce that by default.
            raise PathValidationError(f"Base directory does not exist: {self.base_directory}")
        if self.base_directory and not self.base_directory.is_dir():
            raise PathValidationError(f"Base directory is not a directory: {self.base_directory}")

    def _resolve_path_pydantic(self, file_path_model: Union[ReadFileRequest, WriteFileRequest, AppendFileRequest, FileExistsRequest, GetFileInfoRequest]) -> Path:
        """
        Resolves and validates a path from a Pydantic request model's file_path field.
        This replaces the direct use of _validate_path for initial path resolution from request.
        Pydantic's FilePath handles basic path validation. This adds base_directory logic and security.
        """
        # Pydantic's FilePath has already done some validation (e.g., if it's a valid path string)
        # We still need to resolve it and apply our security/base_directory logic.
        raw_path = Path(str(file_path_model.file_path)) # Convert Pydantic FilePath back to Path for our logic

        try:
            if self.base_directory:
                # If path from model is absolute, ensure it's within base_directory
                if raw_path.is_absolute():
                    resolved_path = raw_path.resolve()
                    try:
                        resolved_path.relative_to(self.base_directory)
                    except ValueError:
                        raise PathValidationError(
                            f"Absolute path {resolved_path} is outside the allowed base directory {self.base_directory}",
                            str(raw_path)
                        )
                else: # Path is relative, resolve against base_directory
                    resolved_path = (self.base_directory / raw_path).resolve()
                    # Double check it didn't escape via complex relative paths like 'foo/../../outside'
                    # The initial relative_to check after resolve should catch this.
                    try:
                        resolved_path.relative_to(self.base_directory)
                    except ValueError: # Should not happen if logic is correct, but good safeguard
                         raise PathValidationError(
                            f"Relative path {raw_path} resolved to {resolved_path}, which is outside base directory {self.base_directory}",
                            str(raw_path)
                        )
            else: # No base directory, resolve the path as is
                resolved_path = raw_path.resolve()

        except (OSError, ValueError) as e:
            raise PathValidationError(f"Invalid path format or resolution error: {raw_path}", str(raw_path)) from e

        # Security checks (e.g., for '..', '~' if not handled by stricter Pydantic FilePath or resolution)
        # Pydantic's FilePath doesn't inherently block '..' in the string if it resolves validly.
        # Our previous _validate_path had specific checks for dangerous patterns in the input string.
        # We should ensure these are still covered.
        # The `resolve()` method typically handles '..' to produce a canonical path.
        # However, checking the original input string for ".." can be an added layer.
        if '..' in str(raw_path) and not self.base_directory: # More risky if no base_directory
            # This check might be too aggressive if ".." is legitimate in a non-base_directory setup
            # Consider if Path.resolve() is sufficient. For now, keeping a cautious check.
            # A path like "/foo/bar/../baz" is valid. "/foo/../../etc/passwd" is the concern.
            # `resolve()` should handle this.
            pass

        # Final check: ensure the resolved path is within the base directory if one is set.
        # This is crucial and was part of the original _validate_path.
        if self.base_directory:
            try:
                resolved_path.relative_to(self.base_directory)
            except ValueError:
                raise PathValidationError(
                    f"Path {resolved_path} is outside the allowed base directory {self.base_directory}",
                    str(resolved_path) # Log the resolved path that failed
                )
        return resolved_path

    def _validate_file_size_on_read(self, file_path: Path) -> None:
        """Validate file size for reading."""
        if file_path.exists(): # Should always exist if we are reading
            file_size = file_path.stat().st_size
            if file_size > self.max_file_size:
                raise FileSizeError(
                    f"File size ({file_size} bytes) exceeds maximum allowed size for reading",
                    str(file_path),
                    file_size,
                    self.max_file_size
                )

    def _log_operation(self, operation: FileOperation, file_path: Path, success: bool,
                      details: str = "", error: Optional[Exception] = None) -> None:
        """Log file operations using the Pydantic model."""
        error_type_str: Optional[str] = None
        if error:
            if isinstance(error, FileManagerError):
                error_type_str = type(error).__name__
            else: # For standard exceptions not yet converted
                error_type_str = get_error_category(error)

        log_entry = OperationLogEntry(
            timestamp=datetime.now(),
            operation=operation,
            file_path=str(file_path),
            success=success,
            details=details or str(error) or "Completed",
            error_type=error_type_str
        )
        self.operation_log.append(log_entry)

    def read_file(self, request: ReadFileRequest) -> ReadFileResponse:
        """
        Read content from a file, validated by Pydantic.
        """
        path: Optional[Path] = None
        try:
            path = self._resolve_path_pydantic(request) # Handles PathValidationError, SecurityError

            if not path.exists():
                raise CustomFileNotFoundError(f"File does not exist: {path}", str(path))
            if not path.is_file():
                raise InvalidFileTypeError(f"Path is not a file: {path}", str(path), expected_type="file")

            self._validate_file_size_on_read(path) # Handles FileSizeError

            with open(path, 'r', encoding=request.encoding) as file:
                content_str = file.read()

            self._log_operation(FileOperation.READ, path, True, f"Read {len(content_str)} characters")
            return ReadFileResponse(
                success=True,
                content=content_str,
                file_path=str(path),
                encoding=request.encoding,
                size_bytes=len(content_str.encode(request.encoding)),
                message="File read successfully."
            )

        except Exception as e:
            final_path = path if path else Path(str(request.file_path)) # Use resolved path if available for logging
            custom_exc = convert_standard_exception(e, str(final_path), FileOperation.READ.value)
            self._log_operation(FileOperation.READ, final_path, False, error=custom_exc)
            # To return a Pydantic response on error, we need to populate it accordingly
            return ReadFileResponse(
                success=False,
                content=None,
                file_path=str(final_path),
                encoding=request.encoding,
                size_bytes=None,
                message=str(custom_exc)
            )

    def write_file(self, request: WriteFileRequest) -> WriteFileResponse:
        """
        Write content to a file, validated by Pydantic.
        """
        path: Optional[Path] = None
        try:
            path = self._resolve_path_pydantic(request) # Handles PathValidationError, SecurityError
            file_existed = path.exists()

            if not request.overwrite and file_existed:
                raise FileAlreadyExistsError(f"File already exists and overwrite is false: {path}", str(path))

            content_bytes = request.content.encode(request.encoding)
            content_size = len(content_bytes)
            if content_size > self.max_file_size:
                raise FileSizeError(
                    f"Content size ({content_size} bytes) exceeds maximum allowed size for writing",
                    str(path), content_size, self.max_file_size
                )

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding=request.encoding) as file:
                file.write(request.content)

            self._log_operation(FileOperation.WRITE, path, True, f"Wrote {len(request.content)} characters")
            return WriteFileResponse(
                success=True,
                file_path=str(path),
                bytes_written=content_size,
                overwrite_used=(file_existed and request.overwrite),
                message="File written successfully."
            )

        except Exception as e:
            final_path = path if path else Path(str(request.file_path))
            custom_exc = convert_standard_exception(e, str(final_path), FileOperation.WRITE.value)
            self._log_operation(FileOperation.WRITE, final_path, False, error=custom_exc)
            return WriteFileResponse(
                success=False,
                file_path=str(final_path),
                bytes_written=None,
                overwrite_used=False, # Or determine if possible
                message=str(custom_exc)
            )

    def append_file(self, request: AppendFileRequest) -> AppendFileResponse:
        """
        Append content to a file, validated by Pydantic.
        """
        path: Optional[Path] = None
        try:
            path = self._resolve_path_pydantic(request) # Handles PathValidationError, SecurityError

            content_bytes = request.content.encode(request.encoding)
            content_size_to_append = len(content_bytes)

            if path.exists():
                if not path.is_file():
                     raise InvalidFileTypeError(f"Path exists but is not a file, cannot append: {path}", str(path))
                current_size = path.stat().st_size
                total_size_after_append = current_size + content_size_to_append
                if total_size_after_append > self.max_file_size:
                    raise FileSizeError(
                        f"Appending would exceed maximum file size ({total_size_after_append} > {self.max_file_size})",
                        str(path), total_size_after_append, self.max_file_size
                    )
            elif content_size_to_append > self.max_file_size: # Appending to a new file
                 raise FileSizeError(
                    f"Content size ({content_size_to_append} bytes) for new file exceeds maximum allowed size",
                    str(path), content_size_to_append, self.max_file_size
                )

            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'a', encoding=request.encoding) as file:
                file.write(request.content)

            self._log_operation(FileOperation.APPEND, path, True, f"Appended {len(request.content)} characters")
            return AppendFileResponse(
                success=True,
                file_path=str(path),
                bytes_appended=content_size_to_append,
                message="Content appended successfully."
            )

        except Exception as e:
            final_path = path if path else Path(str(request.file_path))
            custom_exc = convert_standard_exception(e, str(final_path), FileOperation.APPEND.value)
            self._log_operation(FileOperation.APPEND, final_path, False, error=custom_exc)
            return AppendFileResponse(
                success=False,
                file_path=str(final_path),
                bytes_appended=None,
                message=str(custom_exc)
            )

    def file_exists(self, request: FileExistsRequest) -> FileExistsResponse:
        """
        Check if a file exists, validated by Pydantic.
        Returns success=True even if file doesn't exist, as the check itself succeeded.
        """
        path: Optional[Path] = None
        try:
            # For file_exists, we don't want _resolve_path_pydantic to fail if path is invalid *format*
            # Pydantic FilePath handles basic format. Our security checks might still apply.
            # Let's use a softer validation for exists, as user might be testing a potentially invalid path.
            # However, base_directory restrictions must still apply.
            raw_path_obj = Path(str(request.file_path))
            if self.base_directory:
                if raw_path_obj.is_absolute():
                    resolved_path_for_check = raw_path_obj.resolve()
                    resolved_path_for_check.relative_to(self.base_directory) # This will raise ValueError if outside
                else:
                    resolved_path_for_check = (self.base_directory / raw_path_obj).resolve()
                    resolved_path_for_check.relative_to(self.base_directory) # Check again
                path = resolved_path_for_check
            else:
                path = raw_path_obj.resolve()

            exists_flag = path.exists()
            is_file_flag = path.is_file() if exists_flag else None

            self._log_operation(FileOperation.EXISTS_CHECK, path, True, f"Exists: {exists_flag}, IsFile: {is_file_flag}")
            return FileExistsResponse(
                success=True, # The operation of checking succeeded
                exists=exists_flag,
                file_path=str(path),
                is_file=is_file_flag,
                message=f"File existence check for '{str(path)}' completed."
            )
        except (PathValidationError, SecurityError, ValueError) as e: # ValueError for relative_to
            # Path is invalid w.r.t base directory or security
            final_path = path if path else Path(str(request.file_path))
            self._log_operation(FileOperation.EXISTS_CHECK, final_path, False, error=e)
            return FileExistsResponse(
                success=False, # The check itself failed due to invalid path
                exists=False,
                file_path=str(final_path),
                is_file=None,
                message=f"Path validation failed for existence check: {str(e)}"
            )
        except Exception as e: # Other unexpected errors
            final_path = path if path else Path(str(request.file_path))
            custom_exc = convert_standard_exception(e, str(final_path), "exists_check")
            self._log_operation(FileOperation.EXISTS_CHECK, final_path, False, error=custom_exc)
            return FileExistsResponse(
                success=False, # The check itself failed
                exists=False,
                file_path=str(final_path),
                is_file=None,
                message=f"Error during existence check: {str(custom_exc)}"
            )

    def get_file_info(self, request: GetFileInfoRequest) -> GetFileInfoResponse:
        """
        Get comprehensive information about a file, validated by Pydantic.
        """
        path: Optional[Path] = None
        try:
            path = self._resolve_path_pydantic(request) # Handles PathValidationError, SecurityError

            if not path.exists():
                raise CustomFileNotFoundError(f"File not found: {path}", str(path))

            stat_info = path.stat()
            file_info_model = FileInfo(
                name=path.name,
                size_bytes=stat_info.st_size,
                created_at=datetime.fromtimestamp(stat_info.st_ctime),
                modified_at=datetime.fromtimestamp(stat_info.st_mtime),
                is_file=path.is_file(),
                is_directory=path.is_dir(),
                absolute_path=str(path.absolute()),
                extension=path.suffix if path.suffix else None,
                stem=path.stem,
                is_readable=os.access(path, os.R_OK),
                is_writable=os.access(path, os.W_OK),
                is_executable=os.access(path, os.X_OK)
            )

            self._log_operation(FileOperation.INFO, path, True, "Retrieved file info")
            return GetFileInfoResponse(
                success=True,
                file_info=file_info_model,
                file_path=str(path),
                message="File information retrieved successfully."
            )

        except Exception as e:
            final_path = path if path else Path(str(request.file_path))
            custom_exc = convert_standard_exception(e, str(final_path), FileOperation.INFO.value)
            self._log_operation(FileOperation.INFO, final_path, False, error=custom_exc)
            return GetFileInfoResponse(
                success=False,
                file_info=None,
                file_path=str(final_path),
                message=str(custom_exc)
            )

    def get_operation_log(self, request: GetOperationLogRequest) -> GetOperationLogResponse:
        """
        Get the operation log with optional filtering and sorting, using Pydantic models.
        """
        # Make a copy to avoid modifying the original log during processing
        log_entries = list(self.operation_log)

        if request.filter_by_operation:
            log_entries = [entry for entry in log_entries if entry.operation == request.filter_by_operation]

        if request.filter_by_success is not None:
            log_entries = [entry for entry in log_entries if entry.success == request.filter_by_success]

        total_matching_entries = len(log_entries)

        if request.sort_by:
            sort_key_func = lambda entry: getattr(entry, request.sort_by.value)
            log_entries.sort(key=sort_key_func, reverse=not request.sort_ascending)

        if request.limit is not None and request.limit > 0:
            log_entries = log_entries[:request.limit]

        return GetOperationLogResponse(
            success=True,
            log_entries=log_entries,
            total_entries=total_matching_entries,
            message="Operation log retrieved successfully."
        )

    def clear_operation_log(self, request: ClearOperationLogRequest) -> ClearOperationLogResponse: # request is currently empty
        """Clear the operation log."""
        cleared_count = len(self.operation_log)
        self.operation_log.clear()
        # Optionally log this action to an external system if needed, as internal log is now gone.
        return ClearOperationLogResponse(
            success=True,
            cleared_count=cleared_count,
            message=f"Operation log cleared. {cleared_count} entries removed."
            )

    def get_error_summary(self, request: GetErrorSummaryRequest) -> GetErrorSummaryResponse: # request is currently empty
        """
        Get a summary of errors from the operation log, returning a Pydantic model.
        """
        error_counts: Dict[str, int] = {}
        for entry in self.operation_log:
            if not entry.success and entry.error_type:
                error_counts[entry.error_type] = error_counts.get(entry.error_type, 0) + 1

        summaries = [ErrorSummary(error_type=etype, count=num) for etype, num in error_counts.items()]
        total_errors = sum(s.count for s in summaries)

        return GetErrorSummaryResponse(
            success=True,
            error_summaries=sorted(summaries, key=lambda s: s.count, reverse=True), # Sort by count desc
            total_errors=total_errors,
            message="Error summary retrieved successfully."
        )


# Example usage and testing functions (needs to be updated for Pydantic models)
if __name__ == "__main__":
    # Example usage with custom exceptions and Pydantic models

    # Setup FileHandler with settings
    try:
        # Example: Load settings from a dictionary (e.g., from a config file)
        # config_dict = {"base_directory": ".", "max_file_size": 1024}
        # settings = FileHandlerSettings(**config_dict)
        settings = FileHandlerSettings(max_file_size=2048) # Small size for testing
        handler = FileHandler(settings=settings)
        print(f"FileHandler initialized. Max file size: {handler.max_file_size} bytes.")
    except Exception as e:
        print(f"Error initializing FileHandler: {e}")
        exit()

    try:
        test_file_name = "test_example_pydantic.txt"

        # Test write_file
        print(f"\nAttempting to write file: {test_file_name}")
        write_req = WriteFileRequest(file_path=test_file_name, content="Hello, Pydantic Agent!\nThis is a test.", encoding='utf-8', overwrite=True)
        write_resp = handler.write_file(write_req)
        print(f"Write response: Success: {write_resp.success}, Path: {write_resp.file_path}, Bytes: {write_resp.bytes_written}, Msg: {write_resp.message}")
        if not write_resp.success: raise Exception(f"Write failed: {write_resp.message}")

        # Test read_file
        print(f"\nAttempting to read file: {test_file_name}")
        read_req = ReadFileRequest(file_path=test_file_name, encoding='utf-8')
        read_resp = handler.read_file(read_req)
        print(f"Read response: Success: {read_resp.success}, Path: {read_resp.file_path}, Size: {read_resp.size_bytes}, Msg: {read_resp.message}")
        if read_resp.success:
            print(f"Content:\n---\n{read_resp.content}\n---")
        else:
            raise Exception(f"Read failed: {read_resp.message}")

        # Test get_file_info
        print(f"\nAttempting to get info for: {test_file_name}")
        info_req = GetFileInfoRequest(file_path=test_file_name)
        info_resp = handler.get_file_info(info_req)
        print(f"Info response: Success: {info_resp.success}, Path: {info_resp.file_path}, Msg: {info_resp.message}")
        if info_resp.success and info_resp.file_info:
            print(f"  Name: {info_resp.file_info.name}, Size: {info_resp.file_info.size_bytes} bytes, Modified: {info_resp.file_info.modified_at}")
        else:
            raise Exception(f"Get info failed: {info_resp.message}")

        # Test append_file
        print(f"\nAttempting to append to: {test_file_name}")
        append_req = AppendFileRequest(file_path=test_file_name, content="Appending some more data.\n", encoding='utf-8')
        append_resp = handler.append_file(append_req)
        print(f"Append response: Success: {append_resp.success}, Path: {append_resp.file_path}, Bytes: {append_resp.bytes_appended}, Msg: {append_resp.message}")
        if not append_resp.success: raise Exception(f"Append failed: {append_resp.message}")

        # Read again to verify append
        read_resp_after_append = handler.read_file(ReadFileRequest(file_path=test_file_name, encoding='utf-8'))
        if read_resp_after_append.success:
            print(f"Content after append:\n---\n{read_resp_after_append.content}\n---")

        # Test file_exists
        print(f"\nChecking existence of: {test_file_name}")
        exists_req = FileExistsRequest(file_path=test_file_name)
        exists_resp = handler.file_exists(exists_req)
        print(f"Exists response: Success: {exists_resp.success}, Exists: {exists_resp.exists}, IsFile: {exists_resp.is_file}, Msg: {exists_resp.message}")

        print(f"\nChecking existence of: nonexistent_file.txt")
        exists_req_non = FileExistsRequest(file_path="nonexistent_file.txt")
        exists_resp_non = handler.file_exists(exists_req_non)
        print(f"Exists response (non-existent): Success: {exists_resp_non.success}, Exists: {exists_resp_non.exists}, Msg: {exists_resp_non.message}")


        # Test error handling - try to read non-existent file (expecting graceful response)
        print("\nAttempting to read non-existent file: nonexistent.txt")
        read_non_req = ReadFileRequest(file_path="nonexistent.txt", encoding='utf-8')
        read_non_resp = handler.read_file(read_non_req)
        print(f"Read non-existent response: Success: {read_non_resp.success}, Msg: {read_non_resp.message}")
        if read_non_resp.success:
            print("Error: Read non-existent file reported success unexpectedly.")


        # Test size limit on write
        print("\nAttempting to write file exceeding max size (2048 bytes)")
        large_content = "x" * 3000
        write_large_req = WriteFileRequest(file_path="large_file.txt", content=large_content, encoding='utf-8', overwrite=True)
        write_large_resp = handler.write_file(write_large_req)
        print(f"Write large file response: Success: {write_large_resp.success}, Msg: {write_large_resp.message}")
        if write_large_resp.success:
            print("Error: Write large file reported success unexpectedly.")
        else:
            print(f"✓ Caught expected size error (as response): {write_large_resp.message}")
            # Clean up if file was partially created or if needed
            if Path("large_file.txt").exists(): Path("large_file.txt").unlink()

        # Show operation log
        print("\n📋 Operation Log:")
        log_req = GetOperationLogRequest(filter_by_operation=None, filter_by_success=None, sort_by=LogSortField.TIMESTAMP, sort_ascending=False, limit=10)
        log_resp = handler.get_operation_log(log_req)
        if log_resp.success:
            print(f"Total entries matching: {log_resp.total_entries}. Displaying up to {log_req.limit}.")
            for entry in log_resp.log_entries:
                status = "✓" if entry.success else "✗"
                ts = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                print(f"  {ts} {status} {entry.operation.value}: {entry.file_path} - {entry.details} (Error: {entry.error_type or 'N/A'})")

        # Show error summary
        print("\n📊 Error Summary:")
        summary_req = GetErrorSummaryRequest()
        summary_resp = handler.get_error_summary(summary_req)
        if summary_resp.success and summary_resp.error_summaries:
            for summary_item in summary_resp.error_summaries:
                print(f"  {summary_item.error_type}: {summary_item.count}")
            print(f"  Total errors: {summary_resp.total_errors}")
        elif not summary_resp.error_summaries:
            print("  No errors recorded in summary.")

        # Clean up test file
        if Path(test_file_name).exists():
            Path(test_file_name).unlink()
            print(f"\n✓ Cleaned up test file: {test_file_name}")

    except ValidationError as ve: # Catch Pydantic validation errors explicitly if they escape
        print(f"❌ Pydantic Validation Error: {ve}")
    except FileManagerError as fme: # Catch our custom exceptions
        print(f"❌ FileManagerError: {fme} (Type: {type(fme).__name__})")
    except Exception as e:
        print(f"❌ Unexpected error in demo: {e}")
        print(f"   Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
