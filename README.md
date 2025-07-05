# AI Agent File Manager

A modular file management system designed for AI agents to perform safe and efficient file operations.

## Project Structure

```
ai-file-manager/
├── __init__.py              # Package initialization
├── file_handler.py          # Core file operations module
├── workspace_manager.py     # Workspace & directory operations
├── exceptions.py            # Custom exception classes
├── demo_exceptions.py       # Exception handling demonstrations
├── demo_workspace.py        # Workspace management demonstrations
├── README.md               # This file
└── tests/                  # Unit tests (to be created)
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

### WorkspaceManager Class
- **Directory Management**: Create, list, move, copy, and delete directories
- **File Organization**: Find, organize, and manage files across directory structures
- **Path Resolution**: Safe path handling relative to workspace root
- **Workspace Analytics**: Comprehensive workspace statistics and reporting
- **Integration**: Seamless integration with FileHandler for file operations
- **Security**: Path validation and workspace boundary enforcement

### Supported Operations

#### FileHandler Operations
- `read_file()` - Read file content
- `write_file()` - Write/overwrite file content
- `append_file()` - Append content to existing files
- `file_exists()` - Check file existence
- `get_file_info()` - Retrieve file metadata
- `get_operation_log()` - Access audit logs

#### WorkspaceManager Operations
- `list_directory()` - List directory contents with details
- `create_directory()` - Create directories with parent support
- `move_item()` / `copy_item()` - Move and copy files/directories
- `delete_item()` - Delete files and directories
- `find_files()` - Search files with pattern matching
- `get_workspace_info()` - Comprehensive workspace analytics
- `cleanup_empty_directories()` - Remove empty directories

## Quick Start

```python
from ai_file_manager import FileHandler, WorkspaceManager
from ai_file_manager.exceptions import FileManagerError, FileSizeError

# Method 1: Use WorkspaceManager (recommended for directory operations)
workspace = WorkspaceManager(
    workspace_root="/path/to/workspace",
    max_depth=10,
    allowed_extensions=[".py", ".txt", ".json"]
)

try:
    # Directory operations
    workspace.create_directory("projects/ai-agent")
    workspace.create_directory("data/input")
    
    # File operations via integrated FileHandler
    workspace.file_handler.write_file("projects/ai-agent/main.py", "print('Hello AI!')")
    workspace.file_handler.write_file("data/input/data.json", '{"key": "value"}')
    
    # Directory listing and organization
    contents = workspace.list_directory("projects")
    print(f"Projects directory: {len(contents['files'])} files, {len(contents['directories'])} dirs")
    
    # File discovery
    python_files = workspace.find_files("*.py", recursive=True)
    print(f"Found {len(python_files)} Python files")
    
    # File organization
    workspace.copy_item("projects/ai-agent/main.py", "projects/ai-agent/main_backup.py")
    workspace.move_item("data/input/data.json", "projects/ai-agent/config.json")
    
    # Workspace analytics
    info = workspace.get_workspace_info()
    print(f"Workspace: {info['total_files']} files, {info['total_size_mb']} MB")
    
except FileSizeError as e:
    print(f"File too large: {e}")
except FileManagerError as e:
    print(f"Operation failed: {e}")

# Method 2: Use FileHandler standalone (for simple file operations)
handler = FileHandler(
    base_directory="/path/to/safe/directory",
    max_file_size=1024*1024  # 1MB limit
)

try:
    # Basic file operations
    handler.write_file("example.txt", "Hello World!")
    content = handler.read_file("example.txt")
    handler.append_file("example.txt", "\nAppended text")
    
    # File information
    if handler.file_exists("example.txt"):
        info = handler.get_file_info("example.txt")
        print(f"File size: {info['size']} bytes")
        
except FileManagerError as e:
    print(f"File operation failed: {e}")

# View operation logs
for entry in workspace.get_operation_log(filter_by_success=False):
    print(f"Failed {entry['operation']}: {entry['error_type']}")

# Get error summaries
workspace_errors = {}
for entry in workspace.get_operation_log():
    if not entry['success'] and entry.get('error_type'):
        error_type = entry['error_type']
        workspace_errors[error_type] = workspace_errors.get(error_type, 0) + 1

file_errors = handler.get_error_summary()
print(f"Workspace errors: {workspace_errors}")
print(f"File handler errors: {file_errors}")
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
