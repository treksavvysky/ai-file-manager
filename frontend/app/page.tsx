'use client';

import { useState, useEffect } from 'react';
import FileManager from '@/components/FileManager';
import ActivityPanel from '@/components/ActivityPanel';
import WorkspaceSelector from '@/components/WorkspaceSelector';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Workspace, AgentActivity } from '@/types';
import api from '@/lib/api';

export default function Home() {
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [agentActivities, setAgentActivities] = useState<AgentActivity[]>([]);
  const [activeAgents, setActiveAgents] = useState<any[]>([]);
  
  const { isConnected, activities } = useWebSocket('ws://localhost:8000/ws/activities');

  useEffect(() => {
    loadWorkspaces();
  }, []);

  useEffect(() => {
    if (activities.length > 0) {
      setAgentActivities(prev => [...activities, ...prev].slice(0, 100));
    }
  }, [activities]);

  const loadWorkspaces = async () => {
    try {
      const response = await api.get('/workspaces');
      setWorkspaces(response.data.workspaces);
    } catch (error) {
      console.error('Failed to load workspaces:', error);
    }
  };
  const handleWorkspaceSelect = async (workspace: Workspace) => {
    try {
      await api.get(`/workspaces/${workspace.name}/activate`);
      setCurrentWorkspace(workspace);
    } catch (error) {
      console.error('Failed to activate workspace:', error);
    }
  };

  const createWorkspace = async (name: string) => {
    try {
      await api.post(`/workspaces/${name}/create`);
      await loadWorkspaces();
    } catch (error) {
      console.error('Failed to create workspace:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-gray-900/50 backdrop-blur-lg border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                AI File Manager
              </h1>
              <WorkspaceSelector
                workspaces={workspaces}
                currentWorkspace={currentWorkspace}
                onSelect={handleWorkspaceSelect}
                onCreate={createWorkspace}
              />
            </div>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
              <span className="text-sm text-gray-400">
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        {/* File Manager */}
        <div className="flex-1 overflow-hidden">
          {currentWorkspace ? (
            <FileManager workspace={currentWorkspace} />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h2 className="text-3xl font-bold text-gray-600 mb-4">Select a Workspace</h2>
                <p className="text-gray-500">Choose or create a workspace to start managing files</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Activity Panel */}
      <ActivityPanel 
        activities={agentActivities} 
        activeAgents={activeAgents}
      />
    </div>
  );
}