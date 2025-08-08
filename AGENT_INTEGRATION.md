# OpenAPI Schema for AI Agents

## How to Use with Custom GPTs

1. **Get the OpenAPI Schema**
   - Start the backend server
   - Navigate to: `http://localhost:8000/openapi.json`
   - Copy the complete JSON schema

2. **Configure in Custom GPT**
   - Go to GPT Builder
   - Add new Action
   - Paste the OpenAPI schema
   - Set Authentication: None (or configure as needed)
   - Set Base URL: `http://your-server:8000`

3. **Example GPT Instructions**

```
You are a File Manager Assistant with access to a file management system. You can:

1. Create and manage workspaces
2. Create, read, update, and delete files
3. Navigate directory structures
4. Upload and download files

When working with files:
- Always register yourself first using agent_id "gpt-assistant-001"
- Create or activate a workspace before file operations
- Include your agent_id in all operations for tracking

Available operations:
- Register as agent: POST /api/agents/register
- Create workspace: POST /api/workspaces/{name}/create
- List files: GET /api/workspaces/{name}/files
- Create/update file: POST /api/workspaces/{name}/files/create
- Read file: GET /api/workspaces/{name}/files/read
- Delete file: DELETE /api/workspaces/{name}/files/delete
- Create directory: POST /api/workspaces/{name}/directories/create
```

## Example API Calls for LangChain

```python
from langchain.tools import Tool
from langchain.agents import initialize_agent
import requests

class FileManagerTool:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url
        self.agent_id = "langchain-agent-001"
        
    def create_file(self, workspace: str, path: str, content: str) -> str:
        """Create or update a file in the workspace"""
        response = requests.post(
            f"{self.base_url}/workspaces/{workspace}/files/create",
            json={"file_path": path, "content": content},
            params={"agent_id": self.agent_id}
        )
        return f"File {path} created successfully"
    
    def read_file(self, workspace: str, path: str) -> str:
        """Read a file from the workspace"""
        response = requests.get(
            f"{self.base_url}/workspaces/{workspace}/files/read",
            params={"file_path": path, "agent_id": self.agent_id}
        )
        return response.json()["content"]

# Create tools for LangChain
file_manager = FileManagerTool()

create_file_tool = Tool(
    name="CreateFile",
    func=lambda x: file_manager.create_file(*x.split("|")),
    description="Create a file. Input: workspace|path|content"
)

read_file_tool = Tool(
    name="ReadFile", 
    func=lambda x: file_manager.read_file(*x.split("|")),
    description="Read a file. Input: workspace|path"
)
```

## Example for Function Calling

```json
{
  "name": "file_manager",
  "description": "Manage files and workspaces",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "enum": ["create_file", "read_file", "delete_file", "list_files"],
        "description": "The file operation to perform"
      },
      "workspace": {
        "type": "string",
        "description": "The workspace name"
      },
      "path": {
        "type": "string",
        "description": "The file path"
      },
      "content": {
        "type": "string",
        "description": "File content (for create_file)"
      }
    },
    "required": ["action", "workspace", "path"]
  }
}
```

## WebSocket Integration for Real-time Updates

```javascript
// Connect to activity stream
const ws = new WebSocket('ws://localhost:8000/ws/activities');

ws.onmessage = (event) => {
  const activity = JSON.parse(event.data);
  
  if (activity.type === 'initial') {
    console.log('Connected. Active agents:', activity.active_agents);
  } else if (activity.agent_id) {
    console.log(`Agent ${activity.agent_id} performed ${activity.action}`);
  }
};
```

## Rate Limiting and Best Practices

1. **Register Once**: Register your agent at the start of the session
2. **Batch Operations**: When possible, batch multiple file operations
3. **Use Workspace Isolation**: Each agent should work in its own workspace
4. **Include Agent ID**: Always include agent_id for activity tracking
5. **Handle Errors**: Implement proper error handling for network issues
6. **Clean Up**: Unregister agents when done

## Security Considerations

- Files are isolated within workspaces
- No access to system files outside workspace boundaries
- All agent activities are logged
- Consider implementing authentication for production use