#!/usr/bin/env python3
"""
Demo script for AI File Manager with custom exception handling.

This script demonstrates the various exception types and how AI agents
can handle different error scenarios gracefully.
"""

import sys
import os
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_handler import FileHandler
from exceptions import (
    FileManagerError,
    PathValidationError,
    FileOperationError,
    FileNotFoundError,
    FileSizeError,
    SecurityError,
    get_error_category,
    is_recoverable_error
)


def demonstrate_exception_handling():
    """Demonstrate various exception scenarios for AI agents."""
    print("🤖 AI File Manager Exception Handling Demo")
    print("=" * 50)
    
    # Create handler with small size limit for testing
    handler = FileHandler(max_file_size=100)  # 100 bytes limit
    
    test_scenarios = [
        ("✅ Valid file operations", test_valid_operations),
        ("🚫 Path validation errors", test_path_validation),
        ("📁 File not found errors", test_file_not_found),
        ("📏 File size limit errors", test_size_limits),
        ("🔒 Security violations", test_security_errors),
        ("🔄 Exception recovery", test_error_recovery),
    ]
    
    for description, test_func in test_scenarios:
        print(f"\n{description}")
        print("-" * 30)
        try:
            test_func(handler)
        except Exception as e:
            print(f"❌ Unexpected error in demo: {e}")
    
    # Show final operation log
    print(f"\n📊 Final Operation Summary")
    print("-" * 30)
    error_summary = handler.get_error_summary()
    if error_summary:
        for error_type, count in error_summary.items():
            print(f"  {error_type}: {count} occurrences")
    else:
        print("  No errors recorded")


def test_valid_operations(handler):
    """Test normal, successful operations."""
    try:
        handler.write_file("demo.txt", "Hello AI!")
        content = handler.read_file("demo.txt")
        handler.append_file("demo.txt", " More text.")
        
        info = handler.get_file_info("demo.txt")
        print(f"✓ Successfully created file: {info['size']} bytes")
        
    except FileManagerError as e:
        print(f"✗ Unexpected error: {e}")


def test_path_validation(handler):
    """Test path validation errors."""
    dangerous_paths = [
        "../../../etc/passwd",  # Directory traversal
        "~/secret_file.txt",     # Home directory expansion
        "file_with_${VAR}.txt",  # Variable expansion
    ]
    
    for path in dangerous_paths:
        try:
            handler.read_file(path)
            print(f"⚠️  Path {path} was unexpectedly allowed!")
        except PathValidationError as e:
            print(f"✓ Blocked dangerous path: {path}")
            print(f"  Category: {get_error_category(e)}")
        except SecurityError as e:
            print(f"✓ Security protection for: {path}")
            print(f"  Category: {get_error_category(e)}")
        except FileManagerError as e:
            print(f"✓ Other protection for {path}: {type(e).__name__}")


def test_file_not_found(handler):
    """Test file not found scenarios."""
    try:
        handler.read_file("nonexistent_file.txt")
        print("⚠️  File should not have been found!")
    except FileNotFoundError as e:
        print(f"✓ Correctly detected missing file")
        print(f"  Error: {e}")
        print(f"  Recoverable: {is_recoverable_error(e)}")


def test_size_limits(handler):
    """Test file size limit enforcement."""
    large_content = "x" * 200  # Exceeds 100-byte limit
    
    try:
        handler.write_file("large_file.txt", large_content)
        print("⚠️  Large file was unexpectedly allowed!")
    except FileSizeError as e:
        print(f"✓ Size limit enforced: {e.current_size} > {e.limit_size}")
        print(f"  Recoverable: {is_recoverable_error(e)}")
    
    # Test append size checking
    try:
        handler.write_file("small_file.txt", "Small content")
        handler.append_file("small_file.txt", "x" * 200)  # Would exceed limit
        print("⚠️  Large append was unexpectedly allowed!")
    except FileSizeError as e:
        print(f"✓ Append size limit enforced")


def test_security_errors(handler):
    """Test security constraint violations."""
    # This would be expanded based on specific security requirements
    suspicious_patterns = [
        "file_with_${HOME}.txt",
        "config_%(user)s.txt",
    ]
    
    for pattern in suspicious_patterns:
        try:
            handler.write_file(pattern, "content")
            print(f"⚠️  Suspicious pattern allowed: {pattern}")
        except SecurityError as e:
            print(f"✓ Blocked suspicious pattern: {pattern}")
        except FileManagerError as e:
            print(f"✓ Other protection for {pattern}: {type(e).__name__}")


def test_error_recovery(handler):
    """Demonstrate how AI agents can recover from errors."""
    print("🔄 Simulating AI agent error recovery...")
    
    # Scenario: Try to read a file, handle missing file gracefully
    filename = "recovery_test.txt"
    
    try:
        content = handler.read_file(filename)
        print(f"✓ File exists, content: {content[:20]}...")
    except FileNotFoundError:
        print(f"ℹ️  File {filename} not found, creating it...")
        try:
            handler.write_file(filename, "Auto-created content for AI agent")
            print("✓ Successfully created missing file")
        except FileManagerError as e:
            print(f"✗ Could not create file: {e}")
    
    # Scenario: Handle size limits by truncating content
    try:
        large_content = "AI generated content " * 10  # Might exceed limit
        handler.write_file("ai_output.txt", large_content)
        print("✓ Content written successfully")
    except FileSizeError as e:
        print(f"ℹ️  Content too large ({e.current_size} bytes), truncating...")
        # Truncate to fit within limits
        max_size = e.limit_size - 50  # Leave some margin
        truncated = large_content[:max_size]
        try:
            handler.write_file("ai_output.txt", truncated)
            print(f"✓ Successfully wrote truncated content ({len(truncated)} bytes)")
        except FileManagerError as e2:
            print(f"✗ Even truncated content failed: {e2}")


if __name__ == "__main__":
    demonstrate_exception_handling()
