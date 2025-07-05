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
    from workspace_manager import WorkspaceManager
    from file_handler import FileHandler
    from exceptions import FileManagerError
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
            # Test 1: Initialize workspace
            workspace = WorkspaceManager(temp_dir)
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")
            print(f"✅ FileHandler base directory: {workspace.file_handler.base_directory}")
            
            # Test 2: Create a directory
            workspace.create_directory("test_dir")
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
