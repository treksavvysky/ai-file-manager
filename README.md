# AI Agent File Manager

A modular file management system designed for AI agents to perform safe and efficient file operations.

## Project Structure

```
ai-file-manager/
├── file_handler.py      # Core file operations module
├── README.md           # This file
└── tests/              # Unit tests (to be created)
```

## Features

### FileHandler Class
- **Modular Design**: Small, focused class for basic file operations
- **Security**: Path validation and base directory restrictions
- **Audit Trail**: Operation logging for transparency
- **Error Handling**: Comprehensive exception handling
- **Type Hints**: Full type annotations for better code clarity

### Supported Operations
- `read_file()` - Read file content
- `write_file()` - Write/overwrite file content
- `append_file()` - Append content to existing files
- `file_exists()` - Check file existence
- `get_file_info()` - Retrieve file metadata
- `get_operation_log()` - Access audit logs

## Quick Start

```python
from file_handler import FileHandler

# Initialize handler
handler = FileHandler(base_directory="/path/to/safe/directory")

# Basic operations
handler.write_file("example.txt", "Hello World!")
content = handler.read_file("example.txt")
handler.append_file("example.txt", "\nAppended text")

# Check operations
if handler.file_exists("example.txt"):
    info = handler.get_file_info("example.txt")
    print(f"File size: {info['size']} bytes")

# View audit log
for entry in handler.get_operation_log():
    print(f"{entry['operation']}: {entry['success']}")
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
