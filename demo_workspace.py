#!/usr/bin/env python3
"""
Comprehensive demo for AI File Manager with WorkspaceManager and FileHandler.

This script demonstrates how AI agents can use both classes together
to manage complex file system operations safely and efficiently.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workspace_manager import WorkspaceManager
from file_handler import FileHandler
from exceptions import FileManagerError, PathValidationError, FileSizeError


def demonstrate_workspace_management():
    """Demonstrate comprehensive workspace management for AI agents."""
    print("🤖 AI File Manager - Workspace Management Demo")
    print("=" * 60)
    
    # Create a temporary workspace for the demo
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Demo workspace: {temp_dir}")
        
        try:
            # Initialize workspace manager
            workspace = WorkspaceManager(
                workspace_root=temp_dir,
                max_depth=5,
                allowed_extensions=['.py', '.txt', '.md', '.json', '.csv']
            )
            
            print(f"✅ Workspace initialized at: {workspace.workspace_root}")
            
            # Demonstrate each major functionality
            demo_scenarios = [
                ("🏗️  Project Structure Creation", demo_project_setup),
                ("📝 File Operations", demo_file_operations),
                ("📂 Directory Management", demo_directory_operations),
                ("🔍 File Discovery", demo_file_discovery),
                ("🔄 File Organization", demo_file_organization),
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
                    print(f"❌ Demo error: {e}")
                    
        except Exception as e:
            print(f"❌ Workspace setup failed: {e}")


def demo_project_setup(workspace: WorkspaceManager):
    """Demonstrate setting up a project structure."""
    # Create a typical AI project structure
    project_structure = [
        "src/models",
        "src/utils", 
        "data/raw",
        "data/processed",
        "docs",
        "tests",
        "config",
        "logs"
    ]
    
    print("Creating AI project structure...")
    for directory in project_structure:
        workspace.create_directory(directory)
        print(f"  ✓ Created: {directory}")
    
    # Create some initial files (using relative paths within workspace)
    initial_files = {
        "README.md": "# AI Agent Project\n\nThis is an AI agent workspace.",
        "src/main.py": "#!/usr/bin/env python3\n# Main AI agent entry point\nprint('AI Agent starting...')",
        "src/models/__init__.py": "# Models package",
        "src/utils/helpers.py": "# Utility functions\ndef process_data(data):\n    return data",
        "config/settings.json": '{\n  "model_name": "ai-agent-v1",\n  "max_tokens": 1000\n}',
        "data/raw/sample.csv": "name,value\ntest1,100\ntest2,200",
        "tests/test_main.py": "# Unit tests\ndef test_basic():\n    assert True"
    }
    
    print("\nCreating initial files...")
    for file_path, content in initial_files.items():
        workspace.file_handler.write_file(file_path, content)
        print(f"  ✓ Created: {file_path}")


def demo_file_operations(workspace: WorkspaceManager):
    """Demonstrate file-level operations."""
    # Read and modify files
    config_content = workspace.file_handler.read_file("config/settings.json")
    print(f"📖 Read config file ({len(config_content)} chars)")
    
    # Append to log file
    workspace.file_handler.write_file("logs/activity.log", "")  # Create empty log
    workspace.file_handler.append_file("logs/activity.log", "2024-01-01 10:00: AI Agent started\n")
    workspace.file_handler.append_file("logs/activity.log", "2024-01-01 10:01: Processing data\n")
    print("📝 Updated activity log")
    
    # Get file information
    main_info = workspace.file_handler.get_file_info("src/main.py")
    print(f"📊 Main file: {main_info['size']} bytes, modified {main_info['modified'][:10]}")


def demo_directory_operations(workspace: WorkspaceManager):
    """Demonstrate directory-level operations."""
    # List directory contents
    src_contents = workspace.list_directory("src")
    print(f"📂 src/ contains: {len(src_contents['directories'])} dirs, {len(src_contents['files'])} files")
    
    for directory in src_contents['directories']:
        print(f"  📁 {directory['name']} ({directory['relative_path']})")
    
    for file in src_contents['files']:
        print(f"  📄 {file['name']} ({file['size']} bytes)")
    
    # Copy and move operations
    workspace.copy_item("src/main.py", "src/main_backup.py")
    print("📋 Created backup of main.py")
    
    workspace.create_directory("archive")
    workspace.move_item("src/main_backup.py", "archive/main_v1.py")
    print("📦 Moved backup to archive")


def demo_file_discovery(workspace: WorkspaceManager):
    """Demonstrate file search and discovery."""
    # Find all Python files
    python_files = workspace.find_files("*.py", recursive=True)
    print(f"🐍 Found {len(python_files)} Python files:")
    for file in python_files:
        print(f"  {file['relative_path']} ({file['size']} bytes)")
    
    # Find all config files
    config_files = workspace.find_files("*config*", recursive=True)
    print(f"⚙️  Found {len(config_files)} config-related items:")
    for item in config_files:
        print(f"  {item['relative_path']} ({item['type']})")
    
    # Find files in specific directory
    test_files = workspace.find_files("test_*", relative_path="tests", recursive=False)
    print(f"🧪 Found {len(test_files)} test files in tests/")


def demo_file_organization(workspace: WorkspaceManager):
    """Demonstrate file organization and management."""
    # Create some temporary/work files to organize
    temp_files = [
        "temp_data_1.txt",
        "temp_analysis_2.txt", 
        "work_file_3.txt",
        "output_results.txt"
    ]
    
    print("Creating temporary files...")
    for temp_file in temp_files:
        workspace.file_handler.write_file(temp_file, f"Temporary content for {temp_file}")
        print(f"  ✓ Created: {temp_file}")
    
    # Organize temp files into a directory
    workspace.create_directory("temp_work")
    print("\nOrganizing temporary files...")
    
    temp_pattern_files = workspace.find_files("temp_*", recursive=False, file_types=['file'])
    for file in temp_pattern_files:
        old_path = file['relative_path']
        new_path = f"temp_work/{file['name']}"
        workspace.move_item(old_path, new_path)
        print(f"  📁 Moved {old_path} → {new_path}")
    
    # Archive work files
    workspace.create_directory("archive/work_files")
    work_files = workspace.find_files("work_*", recursive=False)
    for file in work_files:
        old_path = file['relative_path']
        new_path = f"archive/work_files/{file['name']}"
        workspace.move_item(old_path, new_path)
        print(f"  📦 Archived {old_path} → {new_path}")


def demo_workspace_cleanup(workspace: WorkspaceManager):
    """Demonstrate workspace cleanup operations."""
    # Create some empty directories
    empty_dirs = ["empty1", "empty2/nested_empty", "temp_processing"]
    for empty_dir in empty_dirs:
        workspace.create_directory(empty_dir)
    
    print("Created empty directories for cleanup demo")
    
    # Run cleanup
    removed = workspace.cleanup_empty_directories()
    if removed:
        print(f"🧹 Cleaned up {len(removed)} empty directories:")
        for dir_path in removed:
            print(f"  🗑️  Removed: {dir_path}")
    else:
        print("🧹 No empty directories to clean")
    
    # Show current workspace structure
    print("\n📋 Current workspace structure:")
    all_items = workspace.find_files("*", recursive=True)
    directories = [item for item in all_items if item['type'] == 'directory']
    files = [item for item in all_items if item['type'] == 'file']
    
    print(f"  📁 {len(directories)} directories")
    print(f"  📄 {len(files)} files")


def demo_workspace_analytics(workspace: WorkspaceManager):
    """Demonstrate workspace analytics and reporting."""
    # Get comprehensive workspace info
    info = workspace.get_workspace_info()
    
    print("📊 Workspace Analytics:")
    print(f"  📁 Root: {info['workspace_root']}")
    print(f"  📄 Files: {info['total_files']}")
    print(f"  📂 Directories: {info['total_directories']}")
    print(f"  💾 Total Size: {info['total_size_mb']} MB ({info['total_size_bytes']} bytes)")
    print(f"  📝 Operations Logged: {info['operations_logged']}")
    print(f"  🔧 Max Depth: {info['max_depth']}")
    print(f"  📋 Allowed Extensions: {', '.join(info['allowed_extensions']) if info['allowed_extensions'] else 'All'}")
    
    # Analyze file types
    all_files = workspace.find_files("*", recursive=True, file_types=['file'])
    file_types = {}
    for file in all_files:
        ext = file['extension'] or 'no_extension'
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print(f"\n📈 File Type Distribution:")
    for ext, count in sorted(file_types.items()):
        print(f"  {ext}: {count} files")
    
    # Show recent operations
    recent_ops = workspace.get_operation_log()[-10:]  # Last 10 operations
    print(f"\n📝 Recent Operations ({len(recent_ops)} of {len(workspace.get_operation_log())}):")
    for op in recent_ops:
        status = "✅" if op['success'] else "❌"
        print(f"  {status} {op['operation']}: {op['relative_path']} - {op['details']}")


def demo_error_scenarios(workspace: WorkspaceManager):
    """Demonstrate error handling scenarios."""
    print("🔧 Testing error handling scenarios...")
    
    # Test path validation
    try:
        workspace.list_directory("../../../etc")
        print("⚠️  Path traversal was unexpectedly allowed!")
    except PathValidationError:
        print("✅ Path traversal blocked correctly")
    
    # Test file not found
    try:
        workspace.copy_item("nonexistent.txt", "copy.txt")
        print("⚠️  Copy of nonexistent file was unexpectedly allowed!")
    except FileManagerError as e:
        print(f"✅ Nonexistent file error caught: {type(e).__name__}")
    
    # Test delete protection
    try:
        workspace.delete_item(".")  # Try to delete workspace root
        print("⚠️  Workspace root deletion was unexpectedly allowed!")
    except FileManagerError as e:
        print(f"✅ Workspace root protected: {type(e).__name__}")
    
    # Test file size limits (if FileHandler has size limits)
    try:
        large_content = "x" * 1000000  # 1MB of data
        workspace.file_handler.write_file("large_test.txt", large_content)
        print("📝 Large file written successfully")
        workspace.delete_item("large_test.txt")  # Clean up
    except FileSizeError as e:
        print(f"✅ File size limit enforced: {e}")
    except FileManagerError as e:
        print(f"⚠️  Other file error: {type(e).__name__}")
    
    # Show error summary
    file_errors = workspace.file_handler.get_error_summary()
    workspace_errors = {}
    for entry in workspace.get_operation_log():
        if not entry['success'] and entry.get('error_type'):
            error_type = entry['error_type']
            workspace_errors[error_type] = workspace_errors.get(error_type, 0) + 1
    
    print(f"\n📊 Error Summary:")
    if file_errors:
        print(f"  FileHandler errors: {file_errors}")
    if workspace_errors:
        print(f"  Workspace errors: {workspace_errors}")
    if not file_errors and not workspace_errors:
        print("  No errors recorded")


def demo_ai_agent_workflow(workspace: WorkspaceManager):
    """Demonstrate a typical AI agent workflow."""
    print("\n🤖 AI Agent Workflow Simulation")
    print("-" * 40)
    
    # 1. Agent receives a task
    print("1️⃣  Agent receives task: 'Process customer data'")
    
    # 2. Agent sets up workspace
    workspace.create_directory("task_20240101/input")
    workspace.create_directory("task_20240101/output")
    workspace.create_directory("task_20240101/logs")
    print("2️⃣  Created task workspace structure")
    
    # 3. Agent creates input data
    sample_data = """customer_id,name,email,score
1001,John Doe,john@example.com,85
1002,Jane Smith,jane@example.com,92
1003,Bob Wilson,bob@example.com,78"""
    
    workspace.file_handler.write_file("task_20240101/input/customers.csv", sample_data)
    print("3️⃣  Prepared input data")
    
    # 4. Agent processes data (simulation)
    input_data = workspace.file_handler.read_file("task_20240101/input/customers.csv")
    lines = input_data.strip().split('\n')
    
    # Simple processing - calculate average score
    scores = [int(line.split(',')[3]) for line in lines[1:]]  # Skip header
    avg_score = sum(scores) / len(scores)
    
    # 5. Agent saves results
    result = f"Data Processing Results\n" \
            f"======================\n" \
            f"Total customers: {len(scores)}\n" \
            f"Average score: {avg_score:.2f}\n" \
            f"Highest score: {max(scores)}\n" \
            f"Lowest score: {min(scores)}\n"
    
    workspace.file_handler.write_file("task_20240101/output/analysis.txt", result)
    print("4️⃣  Generated analysis results")
    
    # 6. Agent logs activity
    log_entry = f"[{datetime.now().isoformat()}] Task completed: Processed {len(scores)} customers\n"
    workspace.file_handler.append_file("task_20240101/logs/activity.log", log_entry)
    print("5️⃣  Logged activity")
    
    # 7. Agent cleans up temporary files (if any existed)
    temp_files = workspace.find_files("temp_*", relative_path="task_20240101", recursive=True)
    for temp_file in temp_files:
        workspace.delete_item(temp_file['relative_path'])
    print("6️⃣  Cleaned up temporary files")
    
    # 8. Agent reports completion
    task_files = workspace.find_files("*", relative_path="task_20240101", recursive=True)
    print(f"7️⃣  Task completed: {len(task_files)} files in task directory")


if __name__ == "__main__":
    from datetime import datetime
    demonstrate_workspace_management()
    
    # Also demonstrate AI agent workflow
    print("\n" + "=" * 60)
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = WorkspaceManager(temp_dir)
        demo_ai_agent_workflow(workspace)
