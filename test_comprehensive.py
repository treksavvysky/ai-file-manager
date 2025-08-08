#!/usr/bin/env python3
"""
Comprehensive test suite for ai-file-manager to verify all functionality works.
"""

import sys
import os
import tempfile

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_comprehensive_tests():
    """Run a comprehensive test suite to verify the ai-file-manager works correctly."""
    print("🧪 AI File Manager - Comprehensive Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        from src.file_manager_project.workspace_manager import WorkspaceManager, WorkspaceManagerSettings
        from src.file_manager_project.file_handler import FileHandlerSettings
        from src.file_manager_project.exceptions import FileManagerError, PathValidationError, FileSizeError
        from src.file_manager_project.file_handler_models import (
            WriteFileRequest, ReadFileRequest, AppendFileRequest, FileExistsRequest, 
            GetFileInfoRequest, GetOperationLogRequest
        )
        from src.file_manager_project.workspace_manager_models import (
            CreateDirectoryRequest, ListDirectoryRequest, FindItemsRequest, GetWorkspaceInfoRequest
        )
        print("✅ All imports successful")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        tests_failed += 1
        return tests_passed, tests_failed

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"\n📁 Test workspace: {temp_dir}")
        
        try:
            # Initialize workspace
            ws_settings = WorkspaceManagerSettings(
                workspace_root=temp_dir,
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json', '.csv']
            )
            workspace = WorkspaceManager(settings=ws_settings)
            print("✅ Workspace initialization")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Workspace initialization failed: {e}")
            tests_failed += 1
            return tests_passed, tests_failed

        # Test 1: Basic file operations
        try:
            # Write file
            write_req = WriteFileRequest(file_path="test.txt", content="Hello World!", overwrite=True)
            write_resp = workspace.file_handler.write_file(write_req)
            assert write_resp.success, f"Write failed: {write_resp.message}"
            
            # Read file
            read_req = ReadFileRequest(file_path="test.txt")
            read_resp = workspace.file_handler.read_file(read_req)
            assert read_resp.success and read_resp.content == "Hello World!", f"Read failed: {read_resp.message}"
            
            # Append to file
            append_req = AppendFileRequest(file_path="test.txt", content="\nAppended!")
            append_resp = workspace.file_handler.append_file(append_req)
            assert append_resp.success, f"Append failed: {append_resp.message}"
            
            # Check file exists
            exists_req = FileExistsRequest(file_path="test.txt")
            exists_resp = workspace.file_handler.file_exists(exists_req)
            assert exists_resp.success and exists_resp.exists, f"File exists check failed: {exists_resp.message}"
            
            print("✅ Basic file operations")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Basic file operations failed: {e}")
            tests_failed += 1

        # Test 2: Directory operations
        try:
            # Create directory
            create_dir_req = CreateDirectoryRequest(relative_path="test_dir/subdir")
            create_dir_resp = workspace.create_directory(create_dir_req)
            assert create_dir_resp.success, f"Create directory failed: {create_dir_resp.message}"
            
            # List directory
            list_req = ListDirectoryRequest(relative_path=".")
            list_resp = workspace.list_directory(list_req)
            assert list_resp.success, f"List directory failed: {list_resp.message}"
            
            print("✅ Directory operations")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Directory operations failed: {e}")
            tests_failed += 1

        # Test 3: File search and organization
        try:
            # Create test files
            for i in range(3):
                write_req = WriteFileRequest(file_path=f"file_{i}.py", content=f"# Python file {i}", overwrite=True)
                workspace.file_handler.write_file(write_req)
            
            # Find files
            find_req = FindItemsRequest(pattern="*.py", relative_path=".")
            find_resp = workspace.find_items(find_req)
            assert find_resp.success, f"Find files failed: {find_resp.message}"
            py_files = [item for item in find_resp.found_items if item.name.endswith('.py')]
            assert len(py_files) == 3, f"Expected 3 Python files, found {len(py_files)}"
            
            print("✅ File search and organization")
            tests_passed += 1
        except Exception as e:
            print(f"❌ File search and organization failed: {e}")
            tests_failed += 1

        # Test 4: File info and metadata
        try:
            info_req = GetFileInfoRequest(file_path="test.txt")
            info_resp = workspace.file_handler.get_file_info(info_req)
            assert info_resp.success, f"Get file info failed: {info_resp.message}"
            assert info_resp.file_info.size_bytes > 0, "File size should be > 0"
            
            print("✅ File info and metadata")
            tests_passed += 1
        except Exception as e:
            print(f"❌ File info and metadata failed: {e}")
            tests_failed += 1

        # Test 5: Workspace analytics
        try:
            workspace_info_req = GetWorkspaceInfoRequest()
            workspace_info_resp = workspace.get_workspace_info(workspace_info_req)
            assert workspace_info_resp.success, f"Workspace info failed: {workspace_info_resp.message}"
            assert workspace_info_resp.workspace_info.total_files > 0, "Should have files in workspace"
            
            print("✅ Workspace analytics")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Workspace analytics failed: {e}")
            tests_failed += 1

        # Test 6: Error handling
        try:
            # Try to read non-existent file
            read_bad_req = ReadFileRequest(file_path="nonexistent.txt")
            read_bad_resp = workspace.file_handler.read_file(read_bad_req)
            assert not read_bad_resp.success, "Should fail when reading non-existent file"
            
            # Try to access path outside workspace
            list_bad_req = ListDirectoryRequest(relative_path="../../../etc")
            list_bad_resp = workspace.list_directory(list_bad_req)
            assert not list_bad_resp.success, "Should fail when accessing outside workspace"
            
            print("✅ Error handling")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Error handling failed: {e}")
            tests_failed += 1

        # Test 7: Operation logging
        try:
            log_req = GetOperationLogRequest()
            log_resp = workspace.file_handler.get_operation_log(log_req)
            assert log_resp.success, f"Get operation log failed: {log_resp.message}"
            assert len(log_resp.log_entries) > 0, "Should have operation log entries"
            
            print("✅ Operation logging")
            tests_passed += 1
        except Exception as e:
            print(f"❌ Operation logging failed: {e}")
            tests_failed += 1

    print(f"\n🎯 Test Results:")
    print(f"✅ Tests passed: {tests_passed}")
    print(f"❌ Tests failed: {tests_failed}")
    print(f"📊 Success rate: {(tests_passed/(tests_passed+tests_failed)*100):.1f}%")
    
    return tests_passed, tests_failed

if __name__ == "__main__":
    passed, failed = run_comprehensive_tests()
    if failed == 0:
        print("\n🎉 All tests passed! ai-file-manager is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the errors above.")
        sys.exit(1)
