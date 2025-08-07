'use client';

import { useState } from 'react';
import { ChevronDown, Plus, FolderOpen, Check } from 'lucide-react';
import { Workspace } from '@/types';

interface WorkspaceSelectorProps {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  onSelect: (workspace: Workspace) => void;
  onCreate: (name: string) => void;
}

export default function WorkspaceSelector({ 
  workspaces, 
  currentWorkspace, 
  onSelect, 
  onCreate 
}: WorkspaceSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');

  const handleCreate = () => {
    if (newWorkspaceName.trim()) {
      onCreate(newWorkspaceName.trim());
      setNewWorkspaceName('');
      setShowCreateModal(false);
      setIsOpen(false);
    }
  };
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
      >
        <FolderOpen size={18} />
        <span>{currentWorkspace?.name || 'Select Workspace'}</span>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 left-0 w-64 bg-gray-800 rounded-lg shadow-xl border border-gray-700 overflow-hidden z-50">
          <div className="max-h-64 overflow-y-auto">
            {workspaces.map((workspace) => (
              <button
                key={workspace.name}
                onClick={() => {
                  onSelect(workspace);
                  setIsOpen(false);
                }}
                className="w-full px-4 py-2 hover:bg-gray-700 flex items-center justify-between transition-colors"
              >
                <span>{workspace.name}</span>
                {currentWorkspace?.name === workspace.name && (
                  <Check size={16} className="text-green-500" />
                )}
              </button>
            ))}
          </div>
          
          <div className="border-t border-gray-700">
            <button
              onClick={() => {
                setShowCreateModal(true);
                setIsOpen(false);
              }}
              className="w-full px-4 py-2 hover:bg-gray-700 flex items-center space-x-2 text-blue-400 transition-colors"
            >
              <Plus size={16} />
              <span>Create New Workspace</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Create New Workspace</h3>
            <input
              type="text"
              value={newWorkspaceName}
              onChange={(e) => setNewWorkspaceName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              placeholder="Workspace name"
              className="w-full px-3 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <div className="flex justify-end space-x-2 mt-4">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewWorkspaceName('');
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}