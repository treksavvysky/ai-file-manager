# AI File Manager - Next.js + FastAPI Edition

A modern, collaborative file management system designed for both human users and AI agents. Built with Next.js for the frontend and FastAPI for the backend, providing a seamless interface for file operations with real-time activity monitoring.

## 🚀 Features

### For Humans
- **Modern Web Interface**: Beautiful, responsive UI built with Next.js and Tailwind CSS
- **Workspace Management**: Create and switch between isolated workspaces
- **File Operations**: Upload, download, edit, move, rename, and delete files
- **Real-time Updates**: Live activity feed showing AI agent operations
- **In-browser Editor**: Edit text files directly in the browser
- **Visual File Browser**: Navigate directories with an intuitive interface

### For AI Agents
- **RESTful API**: Complete file management API with OpenAPI/Swagger documentation
- **Agent Registration**: Register and track AI agents working in the system
- **Activity Logging**: All agent operations are logged and broadcast in real-time
- **Workspace Isolation**: Agents work in designated workspaces
- **Tool Integration**: Compatible with LLM tool-calling capabilities

## 🏗️ Architecture

```
ai-file-manager/
├── backend/                 # FastAPI backend
│   ├── main.py             # API endpoints and WebSocket server
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── hooks/            # Custom React hooks
│   ├── lib/              # Utilities and API client
│   └── types/            # TypeScript definitions
└── src/                   # Original Python file management modules
    └── file_manager_project/
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and serialization
- **WebSockets**: Real-time activity streaming
- **CORS**: Cross-origin resource sharing for frontend integration

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Lucide Icons**: Beautiful icon library
- **Axios**: HTTP client for API calls
- **Socket.io Client**: WebSocket connection for real-time updates
## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- OpenAPI Schema: `http://localhost:8000/openapi.json`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The web interface will be available at `http://localhost:3000`

## 🔌 API Endpoints

### Workspace Management
- `POST /api/workspaces/{name}/create` - Create a new workspace
- `GET /api/workspaces` - List all workspaces
- `GET /api/workspaces/{name}/activate` - Activate a workspace

### File Operations
- `GET /api/workspaces/{name}/files` - List files in directory
- `POST /api/workspaces/{name}/files/create` - Create/update file
- `GET /api/workspaces/{name}/files/read` - Read file content
- `DELETE /api/workspaces/{name}/files/delete` - Delete file
- `POST /api/workspaces/{name}/files/move` - Move/rename file
- `POST /api/workspaces/{name}/directories/create` - Create directory

### File Transfer
- `POST /api/workspaces/{name}/upload` - Upload file
- `GET /api/workspaces/{name}/download` - Download file

### Agent Management
- `POST /api/agents/register` - Register an AI agent
- `POST /api/agents/{id}/unregister` - Unregister an agent
- `GET /api/agents/active` - List active agents
- `GET /api/agents/activities` - Get recent activities

### Real-time Updates
- `WS /ws/activities` - WebSocket for activity streaming
## 🤖 AI Agent Integration

### Using with Custom GPTs

1. Add the API specification to your GPT:
   - Use the OpenAPI schema from `http://localhost:8000/openapi.json`
   - Configure the base URL as your server address

2. Register your agent:
```json
POST /api/agents/register
{
  "agent_id": "gpt-assistant-001",
  "agent_name": "File Assistant",
  "agent_type": "GPT"
}
```

3. All file operations will be tracked with the agent ID

### Using with LangChain/LlamaIndex

```python
import requests

# Register agent
response = requests.post("http://localhost:8000/api/agents/register", json={
    "agent_id": "langchain-agent-001",
    "agent_name": "LangChain Assistant",
    "agent_type": "LangChain"
})

# Create workspace
workspace = "agent-workspace"
requests.post(f"http://localhost:8000/api/workspaces/{workspace}/create",
              params={"agent_id": "langchain-agent-001"})

# Write file
requests.post(f"http://localhost:8000/api/workspaces/{workspace}/files/create",
              json={"file_path": "output.txt", "content": "Hello from AI!"},
              params={"agent_id": "langchain-agent-001"})
```

## 🎨 Design Features

- **Dark Mode**: Elegant dark theme optimized for long working sessions
- **Glassmorphism**: Modern glass effects with backdrop blur
- **Gradient Accents**: Beautiful gradient text and buttons
- **Smooth Animations**: Subtle transitions and hover effects
- **Responsive Layout**: Works seamlessly on desktop and tablet devices
- **Real-time Indicators**: Live connection status and activity updates

## 🔒 Security Considerations

- Workspaces are isolated in separate directories
- File operations are restricted to workspace boundaries
- Agent activities are logged for audit purposes
- CORS configured for specific origins only

## 🚧 Roadmap

- [ ] File sharing and collaboration features
- [ ] Advanced file search and filtering
- [ ] File versioning and history
- [ ] Multi-file operations (bulk delete, move)
- [ ] Image preview and media handling
- [ ] Code syntax highlighting in editor
- [ ] Agent permissions and access control
- [ ] Export/import workspace archives
- [ ] Integration with cloud storage providers

## 📝 License

MIT License - feel free to use this in your projects!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ for human-AI collaboration