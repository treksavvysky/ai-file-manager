#!/usr/bin/env python3
"""
Corrected test that uses the proper Pydantic model API.
"""

import sys
import os
import tempfile

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.file_manager_project.workspace_manager import WorkspaceManager, WorkspaceManagerSettings
    from src.file_manager_project.file_handler import FileHandlerSettings
    from src.file_manager_project.exceptions import FileManagerError, PathValidationError, FileSizeError, ConfigurationError

    # Import Pydantic models for requests
    from src.file_manager_project.file_handler_models import (
        ReadFileRequest,
        WriteFileRequest,
        AppendFileRequest,
        GetFileInfoRequest,
        GetOperationLogRequest,
        GetErrorSummaryRequest,
        LogSortField
    )
    from src.file_manager_project.workspace_manager_models import (
        ListDirectoryRequest, CreateDirectoryRequest, CopyItemRequest, MoveItemRequest,
        DeleteItemRequest, FindItemsRequest, GetWorkspaceInfoRequest,
        CleanupEmptyDirectoriesRequest, GetWorkspaceOperationLogRequest, WorkspaceItemType
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic functionality with proper error handling and Pydantic models."""
    print("\n🧪 Testing Basic Functionality")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Temp workspace: {temp_dir}")
        
        try:
            # Initialize workspace
            ws_settings = WorkspaceManagerSettings(
                workspace_root=temp_dir,
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json', '.csv']
            )
            workspace = WorkspaceManager(settings=ws_settings)
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")
            print(f"✅ FileHandler base directory: {workspace.file_handler.base_directory}")
            
            # Test 1: Create a directory
            create_req = CreateDirectoryRequest(relative_path="testing/test_dir")
            workspace.create_directory(create_req)
            print("✅ Directory created successfully")
            
            # Test 2: Write a file using Pydantic request model
            write_req = WriteFileRequest(
                file_path="test_file.txt",
                content="Hello, world!",
                encoding="utf-8",
                overwrite=True
            )
            write_response = workspace.file_handler.write_file(write_req)
            print(f"✅ File written successfully: {write_response.bytes_written} bytes")
            
            # Test 3: Read the file back
            read_req = ReadFileRequest(file_path="test_file.txt")
            read_response = workspace.file_handler.read_file(read_req)
            print(f"✅ File read successfully: '{read_response.content.strip()}'")
            
            # Test 4: Append to the file
            append_req = AppendFileRequest(
                file_path="test_file.txt",
                content="\nAppended content!"
            )
            append_response = workspace.file_handler.append_file(append_req)
            print(f"✅ Content appended: {append_response.bytes_appended} bytes")
            
            # Test 5: List directory contents
            list_req = ListDirectoryRequest(relative_path=".")
            contents = workspace.list_directory(list_req)
            file_count = len([item for item in contents.items if item.type.value == 'file'])
            dir_count = len([item for item in contents.items if item.type.value == 'directory'])
            print(f"✅ Directory listing: {file_count} files, {dir_count} dirs")
            
            # Test 6: Find files
            find_req = FindItemsRequest(pattern="*.txt", relative_path=".")
            files = workspace.find_items(find_req)
            txt_file_count = len([item for item in files.found_items if item.type.value == 'file'])
            print(f"✅ File search: Found {txt_file_count} txt files")
            
            # Test 7: Get file info
            info_req = GetFileInfoRequest(file_path="test_file.txt")
            info_response = workspace.file_handler.get_file_info(info_req)
            file_info = info_response.file_info
            print(f"✅ File info: {file_info.size_bytes} bytes, modified: {file_info.modified_at}")
            
            # Test 8: Get workspace info
            workspace_info_req = GetWorkspaceInfoRequest()
            workspace_info = workspace.get_workspace_info(workspace_info_req)
            info = workspace_info.workspace_info
            print(f"✅ Workspace info: {info.total_files} files, {info.total_size_bytes} bytes")
            
            print("\n🎉 All basic tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality()
