#!/usr/bin/env python3
"""
AI Agent Test Script for File Manager API
==========================================
Demonstrates how an AI agent can interact with the file manager API.
"""

import requests
import json
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
AGENT_ID = "test-agent-001"
AGENT_NAME = "Test AI Agent"
WORKSPACE_NAME = "ai-test-workspace"

class FileManagerAgent:
    def __init__(self, base_url, agent_id, agent_name):
        self.base_url = base_url
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.session = requests.Session()
    
    def register(self):
        """Register the agent with the file manager"""
        response = self.session.post(
            f"{self.base_url}/agents/register",
            params={
                "agent_id": self.agent_id,
                "agent_name": self.agent_name,
                "agent_type": "Python Script"
            }
        )
        return response.json()
    
    def create_workspace(self, workspace_name):
        """Create a new workspace"""
        response = self.session.post(
            f"{self.base_url}/workspaces/{workspace_name}/create",
            params={"agent_id": self.agent_id}
        )
        return response.json()
    
    def activate_workspace(self, workspace_name):
        """Activate a workspace"""
        response = self.session.get(
            f"{self.base_url}/workspaces/{workspace_name}/activate"
        )
        return response.json()
    
    def create_file(self, workspace_name, file_path, content):
        """Create or update a file in the workspace"""
        response = self.session.post(
            f"{self.base_url}/workspaces/{workspace_name}/files/create",
            params={"agent_id": self.agent_id},
            json={
                "file_path": file_path,
                "content": content
            }
        )
        return response.json()
    def read_file(self, workspace_name, file_path):
        """Read a file from the workspace"""
        response = self.session.get(
            f"{self.base_url}/workspaces/{workspace_name}/files/read",
            params={
                "agent_id": self.agent_id,
                "file_path": file_path
            }
        )
        return response.json()
    
    def list_files(self, workspace_name, path=""):
        """List files in a directory"""
        response = self.session.get(
            f"{self.base_url}/workspaces/{workspace_name}/files",
            params={
                "agent_id": self.agent_id,
                "path": path
            }
        )
        return response.json()
    
    def create_directory(self, workspace_name, directory_path):
        """Create a directory in the workspace"""
        response = self.session.post(
            f"{self.base_url}/workspaces/{workspace_name}/directories/create",
            params={"agent_id": self.agent_id},
            json={"directory_path": directory_path}
        )
        return response.json()
    
    def delete_file(self, workspace_name, file_path):
        """Delete a file from the workspace"""
        response = self.session.delete(
            f"{self.base_url}/workspaces/{workspace_name}/files/delete",
            params={
                "agent_id": self.agent_id,
                "file_path": file_path
            }
        )
        return response.json()
    
    def unregister(self):
        """Unregister the agent"""
        response = self.session.post(
            f"{self.base_url}/agents/{self.agent_id}/unregister"
        )
        return response.json()

def main():
    """Main test function"""
    print("🤖 AI Agent File Manager Test")
    print("=" * 40)
    
    # Create agent instance
    agent = FileManagerAgent(API_BASE_URL, AGENT_ID, AGENT_NAME)
    
    try:
        # Register agent
        print(f"\n1. Registering agent '{AGENT_NAME}'...")
        result = agent.register()
        print(f"   ✓ {result}")
        
        # Create workspace
        print(f"\n2. Creating workspace '{WORKSPACE_NAME}'...")
        result = agent.create_workspace(WORKSPACE_NAME)
        print(f"   ✓ {result}")
        
        # Activate workspace
        print(f"\n3. Activating workspace...")
        result = agent.activate_workspace(WORKSPACE_NAME)
        print(f"   ✓ {result}")
        # Create directory structure
        print(f"\n4. Creating directory structure...")
        agent.create_directory(WORKSPACE_NAME, "data")
        agent.create_directory(WORKSPACE_NAME, "data/input")
        agent.create_directory(WORKSPACE_NAME, "data/output")
        agent.create_directory(WORKSPACE_NAME, "logs")
        print("   ✓ Created: data/, data/input/, data/output/, logs/")
        
        # Create some files
        print(f"\n5. Creating files...")
        
        # Create README
        readme_content = f"""# AI Agent Workspace
Created: {datetime.now().isoformat()}
Agent: {AGENT_NAME}

This workspace was created and managed by an AI agent.
"""
        agent.create_file(WORKSPACE_NAME, "README.md", readme_content)
        print("   ✓ Created README.md")
        
        # Create data file
        data_content = json.dumps({
            "timestamp": datetime.now().isoformat(),
            "agent": AGENT_ID,
            "data": [1, 2, 3, 4, 5],
            "status": "processed"
        }, indent=2)
        agent.create_file(WORKSPACE_NAME, "data/input/sample.json", data_content)
        print("   ✓ Created data/input/sample.json")
        
        # Create log file
        log_content = f"""[{datetime.now().isoformat()}] Agent {AGENT_ID} initialized
[{datetime.now().isoformat()}] Workspace created successfully
[{datetime.now().isoformat()}] Starting data processing...
[{datetime.now().isoformat()}] Processing complete
"""
        agent.create_file(WORKSPACE_NAME, "logs/agent.log", log_content)
        print("   ✓ Created logs/agent.log")
        
        # Create Python script
        script_content = '''#!/usr/bin/env python3
"""
Sample processing script created by AI agent
"""

def process_data(data):
    """Process input data"""
    return [x * 2 for x in data]

if __name__ == "__main__":
    sample_data = [1, 2, 3, 4, 5]
    result = process_data(sample_data)
    print(f"Processed: {result}")
'''
        agent.create_file(WORKSPACE_NAME, "process.py", script_content)
        print("   ✓ Created process.py")
        
        # List files
        print(f"\n6. Listing workspace contents...")
        files = agent.list_files(WORKSPACE_NAME, "")
        print(f"   Found {len(files.get('items', []))} items in root")
        
        # Read a file
        print(f"\n7. Reading README.md...")
        file_data = agent.read_file(WORKSPACE_NAME, "README.md")
        print(f"   File size: {len(file_data.get('content', ''))} characters")
        
        # Demonstrate file operations
        print(f"\n8. Performing file operations...")
        
        # Create a report
        report_content = f"""# AI Agent Activity Report
Generated: {datetime.now().isoformat()}

## Summary
- Workspace: {WORKSPACE_NAME}
- Agent: {AGENT_NAME} ({AGENT_ID})
- Files Created: 5
- Directories Created: 4

## Operations Performed
1. Workspace initialization
2. Directory structure creation
3. File generation
4. Data processing setup

## Status
✅ All operations completed successfully
"""
        agent.create_file(WORKSPACE_NAME, "data/output/report.md", report_content)
        print("   ✓ Generated report.md")
        
        print(f"\n✅ All tests completed successfully!")
        print(f"\n📁 Workspace '{WORKSPACE_NAME}' is ready for use")
        print(f"   Access it via the web interface at http://localhost:3000")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Unregister agent
        print(f"\n9. Unregistering agent...")
        try:
            result = agent.unregister()
            print(f"   ✓ Agent unregistered")
        except:
            pass

if __name__ == "__main__":
    main()