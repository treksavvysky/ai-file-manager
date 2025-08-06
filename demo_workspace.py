#!/usr/bin/env python3
"""
Comprehensive demo for AI File Manager with WorkspaceManager and FileHandler,
updated to use Pydantic models for requests and responses.

This script demonstrates how AI agents can use both classes together
to manage complex file system operations safely and efficiently with typed interfaces.
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add the 'src' directory to Python path for imports
# This allows us to import 'file_manager_project' as a top-level package.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from file_manager_project.workspace_manager import WorkspaceManager, WorkspaceManagerSettings
from file_manager_project.file_handler import FileHandlerSettings
from file_manager_project.exceptions import FileManagerError, PathValidationError, FileSizeError, ConfigurationError

# Import Pydantic models for requests
from file_manager_project.file_handler_models import (
    ReadFileRequest as FH_ReadFileRequest,
    WriteFileRequest as FH_WriteFileRequest,
    AppendFileRequest as FH_AppendFileRequest,
    GetFileInfoRequest as FH_GetFileInfoRequest,
    GetOperationLogRequest as FH_GetOperationLogRequest,
    GetErrorSummaryRequest as FH_GetErrorSummaryRequest,
    LogSortField as FH_LogSortField
)
from file_manager_project.file_handler_models import BaseResponse as FH_BaseResponse
from file_manager_project.workspace_manager_models import (
    ListDirectoryRequest, CreateDirectoryRequest, CopyItemRequest, MoveItemRequest,
    DeleteItemRequest, FindItemsRequest, GetWorkspaceInfoRequest,
    CleanupEmptyDirectoriesRequest, GetWorkspaceOperationLogRequest, WorkspaceItemType,
    BaseResponse as WM_BaseResponse
)
from typing import Union, Any # Added Any for now, Union for future refinement

# Define a TypeVar or Union for better response type hinting if desired, for now using a common base or Any
DemoResponseType = Union[FH_BaseResponse, WM_BaseResponse, Any] # Using Any as a broad fallback for now


def _handle_response(op_name: str, response: DemoResponseType, raise_on_error: bool = True) -> bool:
    """Helper to print response status and optionally raise error."""
    # Check if response has 'success' and 'message' attributes, common to our BaseResponse models
    success = getattr(response, 'success', False)
    message = getattr(response, 'message', 'No message attribute found')

    print(f"{op_name} Response: Success: {success}, Msg: {message or 'OK'}")
    if not response.success and raise_on_error:
        raise Exception(f"{op_name} failed: {response.message}")
    return response.success


def demonstrate_workspace_management():
    """Demonstrate comprehensive workspace management for AI agents using Pydantic models."""
    print("🤖 AI File Manager - Workspace Management Demo (Pydantic Edition)")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir_path = Path(temp_dir_str)
        print(f"📁 Demo workspace: {temp_dir_path}")
        
        try:
            ws_settings = WorkspaceManagerSettings(
                workspace_root=temp_dir_path, # type: ignore # DirectoryPath expects existing dir, WorkspaceManager handles creation
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json', '.csv']
            )
            workspace = WorkspaceManager(settings=ws_settings)
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")
            
            demo_scenarios = [
                ("🏗️  Project Structure Creation", demo_project_setup),
                ("📝 File Operations", demo_file_operations),
                ("📂 Directory Management", demo_directory_operations),
                ("🔍 Item Discovery", demo_item_discovery), # Renamed from File Discovery
                ("🔄 Item Organization", demo_item_organization), # Renamed
                ("🧹 Workspace Cleanup", demo_workspace_cleanup),
                ("📊 Workspace Analytics", demo_workspace_analytics),
                ("⚠️  Error Handling", demo_error_scenarios),
            ]
            
            for description, demo_func in demo_scenarios:
                print(f"\n{description}")
                print("-" * 40)
                try:
                    demo_func(workspace)
                except Exception as e:
                    print(f"❌ Demo scenario '{description}' error: {e}")
                    # import traceback
                    # traceback.print_exc() # Uncomment for detailed traceback during debugging
                    
        except ConfigurationError as ce:
             print(f"❌ Workspace setup failed (ConfigurationError): {ce}")
        except Exception as e:
            print(f"❌ Workspace setup failed (Unexpected Error): {e}")
            # import traceback
            # traceback.print_exc()


def demo_project_setup(workspace: WorkspaceManager):
    """Demonstrate setting up a project structure using Pydantic requests."""
    project_structure = [
        "src/models", "src/utils", "data/raw", "data/processed",
        "docs", "tests", "config", "logs"
    ]
    print("Creating AI project structure...")
    for directory in project_structure:
        req = CreateDirectoryRequest(relative_path=directory, parents=True)
        resp = workspace.create_directory(req)
        if resp.success:
            print(f"  ✓ Created/Exists: {resp.created_path} (AlreadyExisted: {resp.already_existed})")
        else:
            print(f"  ✗ Failed to create {directory}: {resp.message}")
    
    initial_files = {
        "README.md": "# AI Agent Project\nThis is an AI agent workspace.",
        "src/main.py": "#!/usr/bin/env python3\nprint('AI Agent starting...')",
        "config/settings.json": '{\n  "model_name": "ai-agent-v1"\n}',
        "data/raw/sample.csv": "id,value\n1,100\n2,200",
    }
    print("\nCreating initial files...")
    for file_path, content in initial_files.items():
        req = FH_WriteFileRequest(file_path=file_path, content=content) # Uses FileHandler's model
        resp = workspace.file_handler.write_file(req) # Accessing internal FileHandler
        if resp.success:
            print(f"  ✓ Created: {resp.file_path} ({resp.bytes_written} bytes)")
        else:
            print(f"  ✗ Failed to create {file_path}: {resp.message}")


def demo_file_operations(workspace: WorkspaceManager):
    """Demonstrate file-level operations using FileHandler via WorkspaceManager."""
    # Read config file
    read_req = FH_ReadFileRequest(file_path="config/settings.json")
    read_resp = workspace.file_handler.read_file(read_req)
    if _handle_response("Read config", read_resp) and read_resp.content:
        print(f"📖 Config content ({read_resp.size_bytes} bytes): {read_resp.content[:50]}...")

    # Append to a log file (create if not exists)
    log_file = "logs/activity.log"
    append_req1 = FH_AppendFileRequest(file_path=log_file, content=f"{datetime.now().isoformat()}: Agent started\n")
    _handle_response("Append log1", workspace.file_handler.append_file(append_req1))

    append_req2 = FH_AppendFileRequest(file_path=log_file, content=f"{datetime.now().isoformat()}: Processing data\n")
    _handle_response("Append log2", workspace.file_handler.append_file(append_req2))
    print("📝 Updated activity log")
    
    # Get file information
    info_req = FH_GetFileInfoRequest(file_path="src/main.py")
    info_resp = workspace.file_handler.get_file_info(info_req)
    if _handle_response("Get main.py info", info_resp) and info_resp.file_info:
        fi = info_resp.file_info
        print(f"📊 File 'src/main.py': Size: {fi.size_bytes}B, Modified: {fi.modified_at.strftime('%Y-%m-%d')}")


def demo_directory_operations(workspace: WorkspaceManager):
    """Demonstrate directory-level operations."""
    # List directory contents
    list_req = ListDirectoryRequest(relative_path="src")
    list_resp = workspace.list_directory(list_req)
    if _handle_response("List src/", list_resp):
        print(f"📂 src/ contains {len(list_resp.items)} items:")
        for item in list_resp.items:
            print(f"  - {item.name} (Type: {item.type.value}, Path: {item.relative_path})")
    
    # Copy and move operations
    copy_req = CopyItemRequest(source_relative_path="src/main.py", destination_relative_path="src/main_backup.py")
    _handle_response("Copy main.py", workspace.copy_item(copy_req))
    print("📋 Created backup of main.py")
    
    # Create archive dir first
    _handle_response("Create archive dir", workspace.create_directory(CreateDirectoryRequest(relative_path="archive")))

    move_req = MoveItemRequest(source_relative_path="src/main_backup.py", destination_relative_path="archive/main_v1.py")
    _handle_response("Move backup", workspace.move_item(move_req))
    print("📦 Moved backup to archive")


def demo_item_discovery(workspace: WorkspaceManager):
    """Demonstrate item search and discovery."""
    # Find all Python files
    find_py_req = FindItemsRequest(pattern="*.py", recursive=True, item_types=[WorkspaceItemType.FILE])
    find_py_resp = workspace.find_items(find_py_req)
    if _handle_response("Find Python files", find_py_resp):
        print(f"🐍 Found {len(find_py_resp.found_items)} Python files:")
        for item in find_py_resp.found_items:
            print(f"  - {item.relative_path} (Size: {item.size_bytes}B)")

    # Find all config-related items (files or dirs)
    find_conf_req = FindItemsRequest(pattern="*config*", recursive=True) # All item types
    find_conf_resp = workspace.find_items(find_conf_req)
    if _handle_response("Find config items", find_conf_resp):
        print(f"⚙️  Found {len(find_conf_resp.found_items)} config-related items:")
        for item in find_conf_resp.found_items:
            print(f"  - {item.relative_path} (Type: {item.type.value})")


def demo_item_organization(workspace: WorkspaceManager):
    """Demonstrate item organization and management."""
    temp_files_content = {
        "temp_data_1.txt": "Temporary data 1",
        "temp_analysis_2.txt": "Temporary analysis 2",
        "work_file_3.txt": "Work file 3",
    }
    print("Creating temporary files...")
    for file_path, content in temp_files_content.items():
        _handle_response(f"Write {file_path}", workspace.file_handler.write_file(FH_WriteFileRequest(file_path=file_path, content=content)))

    _handle_response("Create temp_work dir", workspace.create_directory(CreateDirectoryRequest(relative_path="temp_work")))

    print("\nOrganizing 'temp_*' files...")
    find_temp_req = FindItemsRequest(pattern="temp_*", item_types=[WorkspaceItemType.FILE])
    find_temp_resp = workspace.find_items(find_temp_req)
    if find_temp_resp.success:
        for item in find_temp_resp.found_items:
            move_req = MoveItemRequest(source_relative_path=item.relative_path, destination_relative_path=f"temp_work/{item.name}")
            if _handle_response(f"Move {item.name}", workspace.move_item(move_req), raise_on_error=False):
                 print(f"  Moved {item.relative_path} -> temp_work/{item.name}")


def demo_workspace_cleanup(workspace: WorkspaceManager):
    """Demonstrate workspace cleanup operations."""
    empty_dirs_to_create = ["empty1", "empty2/nested_empty", "temp_processing/level2/level3"]
    print("Creating empty directories for cleanup demo...")
    for edir in empty_dirs_to_create:
        _handle_response(f"Create {edir}", workspace.create_directory(CreateDirectoryRequest(relative_path=edir, parents=True)))

    cleanup_req = CleanupEmptyDirectoriesRequest(relative_path=".") # Cleanup from root
    cleanup_resp = workspace.cleanup_empty_directories(cleanup_req)
    if _handle_response("Cleanup empty dirs", cleanup_resp):
        if cleanup_resp.removed_directories:
            print(f"🧹 Cleaned up {len(cleanup_resp.removed_directories)} empty directories:")
            for dir_path in cleanup_resp.removed_directories: print(f"  🗑️  Removed: {dir_path}")
        else:
            print("🧹 No empty directories found to clean from specified path.")


def demo_workspace_analytics(workspace: WorkspaceManager):
    """Demonstrate workspace analytics and reporting."""
    info_req = GetWorkspaceInfoRequest()
    info_resp = workspace.get_workspace_info(info_req)
    if _handle_response("Get workspace info", info_resp) and info_resp.workspace_info:
        ws_info = info_resp.workspace_info
        print("📊 Workspace Analytics:")
        print(f"  Root: {ws_info.workspace_root_path}")
        print(f"  Files: {ws_info.total_files}, Dirs: {ws_info.total_directories}, Total Size: {ws_info.total_size_human}")
        print(f"  Allowed Extensions: {ws_info.configured_allowed_extensions or 'All'}")

    # Show recent WorkspaceManager operations
    log_req = GetWorkspaceOperationLogRequest(limit=10) # Get last 10 WM ops
    log_resp = workspace.get_operation_log(log_req)
    if _handle_response("Get WM op log", log_resp):
        print(f"\n📝 Recent Workspace Operations (last {len(log_resp.log_entries)} of {log_resp.total_entries_before_limit}):")
        for op in log_resp.log_entries:
            status = "✅" if op.success else "❌"
            print(f"  {op.timestamp.strftime('%H:%M:%S')} {status} {op.operation.value}: {op.relative_path or op.path} - {op.details[:50]}...")

    # Show FileHandler error summary (if any errors occurred)
    fh_err_req = FH_GetErrorSummaryRequest()
    fh_err_resp = workspace.file_handler.get_error_summary(fh_err_req)
    if fh_err_resp.success and fh_err_resp.error_summaries:
        print("\n📈 FileHandler Error Summary:")
        for es in fh_err_resp.error_summaries: print(f"  {es.error_type}: {es.count}")


def demo_error_scenarios(workspace: WorkspaceManager):
    """Demonstrate error handling with Pydantic responses."""
    print("🔧 Testing error handling scenarios (expecting graceful failures)...")

    # Test path validation (listing outside workspace) - should be caught by _resolve_path
    # This depends on how strictly WorkspaceManager's _resolve_path handles this.
    # If _resolve_path raises PathValidationError, it won't return a Pydantic response.
    # Let's try an operation that uses _resolve_path.
    print("\nAttempting to list directory outside workspace (../../etc):")
    # This path is intentionally malicious / problematic for _resolve_path
    # A well-behaved client should not send such paths.
    # Our _resolve_path is designed to catch this and raise PathValidationError.
    try:
        list_outside_req = ListDirectoryRequest(relative_path="../../../etc") # This path is problematic
        list_outside_resp = workspace.list_directory(list_outside_req)
        # We expect _resolve_path to raise an exception before a response model is formed for this specific path
        _handle_response("List ../../../etc", list_outside_resp, raise_on_error=False) # Should not reach here if _resolve_path raises
    except PathValidationError as pve:
        print(f"✅ Correctly caught PathValidationError for '../../etc': {pve}")
    except Exception as e:
        print(f"⚠️ Unexpected error for '../../etc': {type(e).__name__} - {e}")

    # Test File Not Found (for an operation that returns a Pydantic response)
    print("\nAttempting to copy a non-existent file:")
    copy_nonexistent_req = CopyItemRequest(source_relative_path="nonexistent.txt", destination_relative_path="copy.txt")
    copy_nonexistent_resp = workspace.copy_item(copy_nonexistent_req)
    _handle_response("Copy nonexistent.txt", copy_nonexistent_resp, raise_on_error=False)
    if not copy_nonexistent_resp.success and "FileNotFoundError" in (copy_nonexistent_resp.message or ""):
         print("✅ Correctly handled non-existent source file for copy via response.")

    # Test delete protection (workspace root)
    print("\nAttempting to delete workspace root (.):")
    delete_root_req = DeleteItemRequest(relative_path=".")
    delete_root_resp = workspace.delete_item(delete_root_req)
    _handle_response("Delete .", delete_root_resp, raise_on_error=False)
    if not delete_root_resp.success and "SecurityError" in (delete_root_resp.message or ""):
         print("✅ Correctly prevented workspace root deletion via response.")

    # Test FileHandler size limits
    print(f"\nAttempting to write file larger than FileHandler's max_file_size ({workspace.file_handler.max_file_size}B):")
    large_content = "x" * (workspace.file_handler.max_file_size + 100)
    fh_write_large_req = FH_WriteFileRequest(file_path="large_test.txt", content=large_content)
    fh_write_large_resp = workspace.file_handler.write_file(fh_write_large_req)
    _handle_response("FH Write large_test.txt", fh_write_large_resp, raise_on_error=False)
    if not fh_write_large_resp.success and "FileSizeError" in (fh_write_large_resp.message or ""):
        print(f"✅ FileHandler correctly enforced size limit via response: {fh_write_large_resp.message[:100]}...")
        # Clean up if file was partially created (though it shouldn't be by current FH logic)
        if (workspace.workspace_root / "large_test.txt").exists():
            (workspace.workspace_root / "large_test.txt").unlink()


def demo_ai_agent_workflow(workspace: WorkspaceManager):
    """Demonstrate a typical AI agent workflow using Pydantic models."""
    print("\n🤖 AI Agent Workflow Simulation (Pydantic Edition)")
    print("-" * 40)
    
    task_dir = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"1️⃣ Agent receives task: 'Process customer data in {task_dir}'")
    
    _handle_response("Create task dir", workspace.create_directory(CreateDirectoryRequest(relative_path=f"{task_dir}/input", parents=True)))
    _handle_response("Create task output dir", workspace.create_directory(CreateDirectoryRequest(relative_path=f"{task_dir}/output")))
    _handle_response("Create task logs dir", workspace.create_directory(CreateDirectoryRequest(relative_path=f"{task_dir}/logs")))
    print(f"2️⃣ Created task workspace structure under ./{task_dir}")
    
    sample_data = "customer_id,name,email,score\n1001,John Doe,j.doe@e.com,85\n1002,Jane Smith,j.smith@e.com,92"
    input_file_path = f"{task_dir}/input/customers.csv"
    write_resp = workspace.file_handler.write_file(FH_WriteFileRequest(file_path=input_file_path, content=sample_data))
    _handle_response("Write customers.csv", write_resp)
    print(f"3️⃣ Prepared input data: {input_file_path}")
    
    read_resp = workspace.file_handler.read_file(FH_ReadFileRequest(file_path=input_file_path))
    if not (_handle_response("Read customers.csv", read_resp) and read_resp.content): return
    
    lines = read_resp.content.strip().split('\n')
    if len(lines) <= 1:
        print("⚠️ No data to process in input file.")
        return

    scores = [int(line.split(',')[3]) for line in lines[1:]]
    avg_score = sum(scores) / len(scores) if scores else 0

    result_content = f"Analysis Results:\nTotal customers: {len(scores)}\nAverage score: {avg_score:.2f}"
    output_file_path = f"{task_dir}/output/analysis.txt"
    _handle_response("Write analysis.txt", workspace.file_handler.write_file(FH_WriteFileRequest(file_path=output_file_path, content=result_content)))
    print(f"4️⃣ Generated analysis: {output_file_path}")

    log_entry_content = f"[{datetime.now().isoformat()}] Task completed. Processed {len(scores)} customers.\n"
    log_file_path = f"{task_dir}/logs/activity.log"
    _handle_response("Append to activity.log", workspace.file_handler.append_file(FH_AppendFileRequest(file_path=log_file_path, content=log_entry_content)))
    print(f"5️⃣ Logged activity to: {log_file_path}")

    find_task_files_req = FindItemsRequest(relative_path=task_dir, recursive=True)
    find_task_files_resp = workspace.find_items(find_task_files_req)
    if find_task_files_resp.success:
        print(f"6️⃣ Task '{task_dir}' completed. Contains {len(find_task_files_resp.found_items)} items.")


if __name__ == "__main__":
    demonstrate_workspace_management()
    
    print("\n" + "=" * 60)
    with tempfile.TemporaryDirectory() as temp_dir_str_agent:
        temp_dir_path_agent = Path(temp_dir_str_agent)
        try:
            ws_settings_agent = WorkspaceManagerSettings(workspace_root=temp_dir_path_agent) # type: ignore
            workspace_agent = WorkspaceManager(settings=ws_settings_agent)
            demo_ai_agent_workflow(workspace_agent)
        except Exception as e:
            print(f"❌ Error in AI Agent Workflow Demo: {e}")
            # import traceback
            # traceback.print_exc()
