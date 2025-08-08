"""
FastAPI Backend for AI File Manager
====================================
A REST API backend that provides file management capabilities for both human users
and AI agents. Includes OpenAPI/Swagger documentation for easy integration.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import os
import sys
import json
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
import asyncio
from collections import deque

# Add the parent directory to the path to import our existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.file_manager_project.workspace_manager import WorkspaceManager, WorkspaceManagerSettings
from src.file_manager_project.file_handler_models import (
    WriteFileRequest, ReadFileRequest,
    WriteFileResponse, ReadFileResponse
)
from src.file_manager_project.workspace_manager_models import (
    CreateDirectoryRequest, ListDirectoryRequest, MoveItemRequest,
    CreateDirectoryResponse, ListDirectoryResponse, MoveItemResponse
)

# Import additional models that don't exist in the original
from pathlib import Path
import os
# Activity tracking for AI agents
class ActivityTracker:
    def __init__(self, max_size: int = 100):
        self.activities = deque(maxlen=max_size)
        self.active_agents: Dict[str, Dict] = {}
        self.websocket_connections: List[WebSocket] = []
    
    async def log_activity(self, agent_id: str, action: str, details: Dict[str, Any]):
        activity = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action,
            "details": details
        }
        self.activities.append(activity)
        
        # Broadcast to all connected websockets
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(activity)
            except:
                # Remove disconnected websockets
                self.websocket_connections.remove(websocket)
    
    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        self.active_agents[agent_id] = {
            "info": agent_info,
            "last_activity": datetime.now().isoformat()
        }
    
    def unregister_agent(self, agent_id: str):
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]

activity_tracker = ActivityTracker()

# Workspace configuration
WORKSPACES_ROOT = Path.home() / "ai-workspaces"
WORKSPACES_ROOT.mkdir(exist_ok=True)

# Store active workspace managers
workspace_managers: Dict[str, WorkspaceManager] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting AI File Manager API...")
    yield
    # Shutdown
    print("Shutting down AI File Manager API...")

app = FastAPI(
    title="AI File Manager API",
    description="File management API for human and AI agent collaboration",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Workspace Management Endpoints
@app.post("/api/workspaces/{workspace_name}/create")
async def create_workspace(workspace_name: str, agent_id: Optional[str] = None):
    """Create a new workspace"""
    workspace_path = WORKSPACES_ROOT / workspace_name
    
    if workspace_path.exists():
        raise HTTPException(status_code=400, detail="Workspace already exists")
    
    workspace_path.mkdir(parents=True)
    settings = WorkspaceManagerSettings(workspace_root=str(workspace_path))
    workspace_managers[workspace_name] = WorkspaceManager(settings=settings)
    
    if agent_id:
        await activity_tracker.log_activity(
            agent_id, "CREATE_WORKSPACE", 
            {"workspace": workspace_name}
        )
    
    return {"status": "success", "workspace": workspace_name, "path": str(workspace_path)}

@app.get("/api/workspaces")
async def list_workspaces():
    """List all available workspaces"""
    workspaces = []
    for workspace_dir in WORKSPACES_ROOT.iterdir():
        if workspace_dir.is_dir():
            workspaces.append({
                "name": workspace_dir.name,
                "path": str(workspace_dir),
                "created": datetime.fromtimestamp(workspace_dir.stat().st_ctime).isoformat()
            })
    return {"workspaces": workspaces}
@app.get("/api/workspaces/{workspace_name}/activate")
async def activate_workspace(workspace_name: str):
    """Activate a workspace for use"""
    workspace_path = WORKSPACES_ROOT / workspace_name
    
    if not workspace_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    if workspace_name not in workspace_managers:
        settings = WorkspaceManagerSettings(workspace_root=str(workspace_path))
        workspace_managers[workspace_name] = WorkspaceManager(settings=settings)
    
    return {"status": "active", "workspace": workspace_name}

# File Operations Endpoints
@app.get("/api/workspaces/{workspace_name}/files")
async def list_files(
    workspace_name: str, 
    path: str = "", 
    agent_id: Optional[str] = None
):
    """List files and directories in a workspace path"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    request = ListDirectoryRequest(relative_path=path or ".")
    
    try:
        response = manager.list_directory(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "LIST_FILES", 
                {"workspace": workspace_name, "path": path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/api/workspaces/{workspace_name}/files/create")
async def create_file(
    workspace_name: str,
    file_path: str,
    content: str = "",
    agent_id: Optional[str] = None
):
    """Create or update a file in the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    request = WriteFileRequest(file_path=file_path, content=content)
    
    try:
        response = manager.file_handler.write_file(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "CREATE_FILE", 
                {"workspace": workspace_name, "file": file_path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/workspaces/{workspace_name}/files/read")
async def read_file(
    workspace_name: str,
    file_path: str,
    agent_id: Optional[str] = None
):
    """Read a file from the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    request = ReadFileRequest(file_path=file_path)
    
    try:
        response = manager.file_handler.read_file(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "READ_FILE", 
                {"workspace": workspace_name, "file": file_path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.delete("/api/workspaces/{workspace_name}/files/delete")
async def delete_file(
    workspace_name: str,
    file_path: str,
    agent_id: Optional[str] = None
):
    """Delete a file from the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    workspace_path = WORKSPACES_ROOT / workspace_name
    full_path = workspace_path / file_path
    
    try:
        if full_path.exists() and full_path.is_file():
            full_path.unlink()
            
            if agent_id:
                await activity_tracker.log_activity(
                    agent_id, "DELETE_FILE", 
                    {"workspace": workspace_name, "file": file_path}
                )
            
            return {"success": True, "message": "File deleted", "file_path": file_path}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/workspaces/{workspace_name}/files/move")
async def move_file(
    workspace_name: str,
    source_path: str,
    destination_path: str,
    agent_id: Optional[str] = None
):
    """Move or rename a file in the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    request = MoveItemRequest(source_relative_path=source_path, destination_relative_path=destination_path)
    
    try:
        response = manager.move_item(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "MOVE_FILE", 
                {"workspace": workspace_name, "source": source_path, "destination": destination_path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.post("/api/workspaces/{workspace_name}/directories/create")
async def create_directory(
    workspace_name: str,
    directory_path: str,
    agent_id: Optional[str] = None
):
    """Create a directory in the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    request = CreateDirectoryRequest(relative_path=directory_path)
    
    try:
        response = manager.create_directory(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "CREATE_DIRECTORY", 
                {"workspace": workspace_name, "directory": directory_path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# File Upload/Download Endpoints
@app.post("/api/workspaces/{workspace_name}/upload")
async def upload_file(
    workspace_name: str,
    file: UploadFile = File(...),
    path: str = "",
    agent_id: Optional[str] = None
):
    """Upload a file to the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    file_path = os.path.join(path, file.filename) if path else file.filename
    
    content = await file.read()
    request = WriteFileRequest(file_path=file_path, content=content.decode('utf-8'))
    
    try:
        response = manager.file_handler.write_file(request)
        
        if agent_id:
            await activity_tracker.log_activity(
                agent_id, "UPLOAD_FILE", 
                {"workspace": workspace_name, "file": file_path}
            )
        
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@app.get("/api/workspaces/{workspace_name}/download")
async def download_file(
    workspace_name: str,
    file_path: str,
    agent_id: Optional[str] = None
):
    """Download a file from the workspace"""
    if workspace_name not in workspace_managers:
        raise HTTPException(status_code=404, detail="Workspace not active")
    
    manager = workspace_managers[workspace_name]
    workspace_path = WORKSPACES_ROOT / workspace_name
    full_path = workspace_path / file_path
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    if agent_id:
        await activity_tracker.log_activity(
            agent_id, "DOWNLOAD_FILE", 
            {"workspace": workspace_name, "file": file_path}
        )
    
    return FileResponse(
        path=str(full_path),
        filename=os.path.basename(file_path),
        media_type='application/octet-stream'
    )

# Agent Activity Endpoints
@app.post("/api/agents/register")
async def register_agent(agent_id: str, agent_name: str, agent_type: str = "AI"):
    """Register an AI agent"""
    activity_tracker.register_agent(agent_id, {
        "name": agent_name,
        "type": agent_type,
        "registered_at": datetime.now().isoformat()
    })
    
    return {"status": "registered", "agent_id": agent_id}

@app.post("/api/agents/{agent_id}/unregister")
async def unregister_agent(agent_id: str):
    """Unregister an AI agent"""
    activity_tracker.unregister_agent(agent_id)
    return {"status": "unregistered", "agent_id": agent_id}

@app.get("/api/agents/active")
async def get_active_agents():
    """Get list of active agents"""
    return {"agents": activity_tracker.active_agents}

@app.get("/api/agents/activities")
async def get_recent_activities(limit: int = 50):
    """Get recent agent activities"""
    activities = list(activity_tracker.activities)[-limit:]
    return {"activities": activities}
# WebSocket for real-time activity updates
@app.websocket("/ws/activities")
async def websocket_activities(websocket: WebSocket):
    """WebSocket endpoint for real-time activity streaming"""
    await websocket.accept()
    activity_tracker.websocket_connections.append(websocket)
    
    try:
        # Send initial state
        await websocket.send_json({
            "type": "initial",
            "active_agents": activity_tracker.active_agents,
            "recent_activities": list(activity_tracker.activities)[-20:]
        })
        
        # Keep connection alive
        while True:
            await asyncio.sleep(1)
            await websocket.send_json({"type": "ping"})
            
    except WebSocketDisconnect:
        activity_tracker.websocket_connections.remove(websocket)

# Health Check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "workspaces": len(workspace_managers),
        "active_agents": len(activity_tracker.active_agents)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)