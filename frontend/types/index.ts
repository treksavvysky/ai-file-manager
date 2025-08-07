export interface Workspace {
  name: string;
  path: string;
  created?: string;
}

export interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
  extension?: string;
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