'use client';

import { useState, useEffect } from 'react';
import { Activity, Bot, User, Clock, FileText, Folder, Upload, Download, Trash2 } from 'lucide-react';
import { AgentActivity } from '@/types';

interface ActivityPanelProps {
  activities: AgentActivity[];
  activeAgents: any[];
}

export default function ActivityPanel({ activities, activeAgents }: ActivityPanelProps) {
  const [collapsed, setCollapsed] = useState(false);

  const getActivityIcon = (action: string) => {
    switch (action) {
      case 'CREATE_FILE':
      case 'WRITE_FILE':
        return FileText;
      case 'CREATE_DIRECTORY':
      case 'CREATE_WORKSPACE':
        return Folder;
      case 'UPLOAD_FILE':
        return Upload;
      case 'DOWNLOAD_FILE':
        return Download;
      case 'DELETE_FILE':
        return Trash2;
      default:
        return Activity;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      second: '2-digit'
    });
  };
  return (
    <div className={`${collapsed ? 'w-16' : 'w-96'} bg-gray-900/50 border-l border-gray-800 flex flex-col transition-all duration-300`}>
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className={`flex items-center space-x-2 ${collapsed ? 'hidden' : ''}`}>
            <Activity className="text-purple-500" size={20} />
            <h2 className="font-semibold">Agent Activity</h2>
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 hover:bg-gray-800 rounded"
          >
            <Activity size={18} />
          </button>
        </div>
      </div>

      {!collapsed && (
        <>
          {/* Active Agents */}
          <div className="px-4 py-3 border-b border-gray-800">
            <h3 className="text-sm font-medium text-gray-400 mb-2">Active Agents</h3>
            {activeAgents.length === 0 ? (
              <p className="text-sm text-gray-500">No active agents</p>
            ) : (
              <div className="space-y-2">
                {activeAgents.map((agent) => (
                  <div key={agent.id} className="flex items-center space-x-2">
                    <Bot size={16} className="text-green-500" />
                    <span className="text-sm">{agent.name}</span>
                    <span className="text-xs text-gray-500">{agent.type}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Activity Feed */}
          <div className="flex-1 overflow-y-auto px-4 py-3">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Recent Activity</h3>
            {activities.length === 0 ? (
              <p className="text-sm text-gray-500">No recent activity</p>
            ) : (
              <div className="space-y-3">
                {activities.map((activity, index) => {
                  const Icon = getActivityIcon(activity.action);
                  return (
                    <div key={index} className="group relative">
                      <div className="flex items-start space-x-3">
                        <div className="flex-shrink-0 p-1.5 bg-gray-800 rounded">
                          <Icon size={14} className="text-gray-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <Bot size={12} className="text-blue-500" />
                            <span className="text-xs font-medium text-blue-400">
                              {activity.agent_id}
                            </span>
                          </div>
                          <p className="text-xs text-gray-300 mt-1">
                            {activity.action.replace(/_/g, ' ').toLowerCase()}
                          </p>
                          {activity.details?.file && (
                            <p className="text-xs text-gray-500 truncate mt-1">
                              {activity.details.file}
                            </p>
                          )}
                          <p className="text-xs text-gray-600 mt-1">
                            {formatTime(activity.timestamp)}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Status Footer */}
          <div className="px-4 py-3 border-t border-gray-800 bg-gray-950/50">
            <div className="flex items-center justify-between text-xs text-gray-500">
              <span>{activities.length} activities</span>
              <span>{activeAgents.length} agents</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}