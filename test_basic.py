#!/usr/bin/env python3
"""
Simple test to debug the import and path issues.
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
        ReadFileRequest as FH_ReadFileRequest,
        WriteFileRequest as FH_WriteFileRequest,
        AppendFileRequest as FH_AppendFileRequest,
        GetFileInfoRequest as FH_GetFileInfoRequest,
        GetOperationLogRequest as FH_GetOperationLogRequest,
        GetErrorSummaryRequest as FH_GetErrorSummaryRequest,
        LogSortField as FH_LogSortField
    )
    from src.file_manager_project.file_handler_models import BaseResponse as FH_BaseResponse
    from src.file_manager_project.workspace_manager_models import (
        ListDirectoryRequest, CreateDirectoryRequest, CopyItemRequest, MoveItemRequest,
        DeleteItemRequest, FindItemsRequest, GetWorkspaceInfoRequest,
        CleanupEmptyDirectoriesRequest, GetWorkspaceOperationLogRequest, WorkspaceItemType,
        BaseResponse as WM_BaseResponse
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_basic_functionality():
    """Test basic functionality with proper error handling."""
    print("\n🧪 Testing Basic Functionality")
    print("-" * 40)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Temp workspace: {temp_dir}")
        
        try:
            ws_settings = WorkspaceManagerSettings(
                workspace_root=temp_dir, # type: ignore # DirectoryPath expects existing dir, WorkspaceManager handles creation
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json', '.csv']
            )
            workspace = WorkspaceManager(settings=ws_settings)
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")
            print(f"✅ FileHandler base directory: {workspace.file_handler.base_directory}")
            
            # Test 2: Create a directory
            test_dir = CreateDirectoryRequest(
                relative_path="testing/test_dir")
            workspace.create_directory(test_dir)
            print("✅ Directory created successfully")
            
            # Test 3: Write a file using relative path
            workspace.file_handler.write_file("test_file.txt", "Hello, world!")
            print("✅ File written successfully")
            
            # Test 4: Read the file back
            content = workspace.file_handler.read_file("test_file.txt")
            print(f"✅ File read successfully: '{content.strip()}'")
            
            # Test 5: List directory contents
            contents = workspace.list_directory()
            print(f"✅ Directory listing: {len(contents['files'])} files, {len(contents['directories'])} dirs")
            
            # Test 6: Find files
            files = workspace.find_files("*.txt")
            print(f"✅ File search: Found {len(files)} txt files")
            
            print("\n🎉 All basic tests passed!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality()
