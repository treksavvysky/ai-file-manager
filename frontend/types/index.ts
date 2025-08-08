export interface Workspace {
  name: string;
  path: string;
  created?: string;
}

export interface FileItem {
  name: string;
  relative_path: string;  // Changed from 'path' to match backend
  type: 'file' | 'directory';
  size_bytes?: number;    // Changed from 'size' to match backend
  modified_at?: string;    // Changed from 'modified' to match backend
  extension?: string;
  is_hidden?: boolean;     // Added from backend
  permissions?: string;    // Added from backend
}

export interface AgentActivity {
  timestamp: string;
  agent_id: string;
  action: string;
  details: {
    workspace?: string;
    file?: string;
    path?: string;
    source?: string;
    destination?: string;
    [key: string]: any;
  };
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  last_activity: string;
  info?: any;
}