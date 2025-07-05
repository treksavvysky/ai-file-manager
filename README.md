# AI Agent File Manager

A modular file management system designed for AI agents to perform safe and efficient file operations.

## Project Structure

```
ai-file-manager/
├── __init__.py         # Package initialization
├── file_handler.py     # Core file operations module
├── exceptions.py       # Custom exception classes
├── README.md          # This file
└── tests/             # Unit tests (to be created)
```

## Features

### FileHandler Class
- **Modular Design**: Small, focused class for basic file operations
- **Security**: Path validation and base directory restrictions
- **Audit Trail**: Operation logging for transparency
- **Custom Exceptions**: Specific error types for different failure modes
- **Size Limits**: Configurable file size constraints
- **Type Hints**: Full type annotations for better code clarity

### Custom Exception System
- **FileManagerError**: Base exception for all file manager errors
- **PathValidationError**: Invalid or restricted file paths
- **FileOperationError**: System-level operation failures
- **SecurityError**: Security constraint violations
- **FileSizeError**: File size limit violations
- **EncodingError**: Character encoding issues
- **InvalidFileTypeError**: Unsupported file type operations

### Supported Operations
- `read_file()` - Read file content
- `write_file()` - Write/overwrite file content
- `append_file()` - Append content to existing files
- `file_exists()` - Check file existence
- `get_file_info()` - Retrieve file metadata
- `get_operation_log()` - Access audit logs

## Quick Start

```python
from ai_file_manager import FileHandler
from ai_file_manager.exceptions import FileManagerError, FileSizeError

# Initialize handler with security constraints
handler = FileHandler(
    base_directory="/path/to/safe/directory",
    max_file_size=1024*1024  # 1MB limit
)

try:
    # Basic operations
    handler.write_file("example.txt", "Hello World!")
    content = handler.read_file("example.txt")
    handler.append_file("example.txt", "\nAppended text")
    
    # Check operations
    if handler.file_exists("example.txt"):
        info = handler.get_file_info("example.txt")
        print(f"File size: {info['size']} bytes")
    
except FileSizeError as e:
    print(f"File too large: {e}")
except FileManagerError as e:
    print(f"File operation failed: {e}")

# View audit log with error filtering
for entry in handler.get_operation_log(filter_by_success=False):
    print(f"Failed {entry['operation']}: {entry['error_type']}")

# Get error summary
error_summary = handler.get_error_summary()
if error_summary:
    print(f"Error types encountered: {error_summary}")
```

## Design Principles

1. **Modularity**: Each component handles a specific responsibility
2. **Safety**: Built-in security checks and error handling
3. **Transparency**: All operations are logged
4. **Simplicity**: Clean, intuitive API for AI agents
5. **Extensibility**: Easy to add new file operation modules

## Next Steps

- [ ] Add unit tests
- [ ] Implement JSON file utilities
- [ ] Add CSV/data file handlers
- [ ] Create configuration management
- [ ] Add file backup/versioning
- [ ] Implement directory operations module

## License

TBD
