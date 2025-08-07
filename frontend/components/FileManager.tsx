'use client';

import { useState, useEffect } from 'react';
import { 
  Folder, File, Download, Upload, Trash2, Edit3, 
  Plus, Move, Eye, Code, Image, FileText, Archive,
  ChevronRight, ChevronDown, MoreVertical
} from 'lucide-react';
import { Workspace, FileItem } from '@/types';
import api from '@/lib/api';
import toast from 'react-hot-toast';
import FileEditor from './FileEditor';
import ContextMenu from './ContextMenu';
import UploadModal from './UploadModal';

interface FileManagerProps {
  workspace: Workspace;
}

export default function FileManager({ workspace }: FileManagerProps) {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [items, setItems] = useState<FileItem[]>([]);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [editingFile, setEditingFile] = useState<FileItem | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');

  useEffect(() => {
    loadDirectory(currentPath);
  }, [workspace, currentPath]);
  const loadDirectory = async (path: string) => {
    setLoading(true);
    try {
      const response = await api.get(`/workspaces/${workspace.name}/files`, {
        params: { path }
      });
      setItems(response.data.items || []);
    } catch (error) {
      toast.error('Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (item: FileItem) => {
    try {
      await api.delete(`/workspaces/${workspace.name}/files/delete`, {
        params: { file_path: item.path }
      });
      toast.success(`Deleted ${item.name}`);
      loadDirectory(currentPath);
    } catch (error) {
      toast.error('Failed to delete item');
    }
  };

  const handleDownload = async (item: FileItem) => {
    try {
      const response = await api.get(`/workspaces/${workspace.name}/download`, {
        params: { file_path: item.path },
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', item.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Failed to download file');
    }
  };

  const getFileIcon = (item: FileItem) => {
    if (item.type === 'directory') return Folder;
    const ext = item.name.split('.').pop()?.toLowerCase();
    
    switch (ext) {
      case 'js':
      case 'ts':
      case 'jsx':
      case 'tsx':
      case 'py':
      case 'java':
        return Code;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
      case 'svg':
        return Image;
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
        return FileText;
      case 'zip':
      case 'tar':
      case 'gz':
        return Archive;
      default:
        return File;
    }
  };
  const breadcrumbs = currentPath.split('/').filter(Boolean);

  return (
    <div className="h-full flex flex-col bg-gray-900/30">
      {/* Toolbar */}
      <div className="bg-gray-900/50 border-b border-gray-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowUpload(true)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center space-x-2 transition-colors"
            >
              <Upload size={16} />
              <span>Upload</span>
            </button>
            <button
              onClick={() => loadDirectory(currentPath)}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
            >
              Refresh
            </button>
          </div>
          
          {/* Breadcrumbs */}
          <div className="flex items-center space-x-1 text-sm">
            <button
              onClick={() => setCurrentPath('')}
              className="text-gray-400 hover:text-gray-200"
            >
              {workspace.name}
            </button>
            {breadcrumbs.map((crumb, index) => (
              <span key={index} className="flex items-center">
                <ChevronRight size={14} className="text-gray-600 mx-1" />
                <button
                  onClick={() => setCurrentPath(breadcrumbs.slice(0, index + 1).join('/'))}
                  className="text-gray-400 hover:text-gray-200"
                >
                  {crumb}
                </button>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* File List */}
      <div className="flex-1 overflow-auto p-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Folder size={48} className="mb-2" />
            <p>Empty directory</p>
          </div>
        ) : (
          <div className="grid gap-2">
            {items.map((item) => {
              const Icon = getFileIcon(item);
              return (
                <div
                  key={item.path}
                  className="group flex items-center px-3 py-2 rounded-lg hover:bg-gray-800/50 cursor-pointer transition-colors"
                  onClick={() => {
                    if (item.type === 'directory') {
                      setCurrentPath(item.path);
                    } else {
                      setEditingFile(item);
                    }
                  }}
                >
                  <Icon size={18} className="mr-3 text-gray-400" />
                  <span className="flex-1">{item.name}</span>
                  <div className="opacity-0 group-hover:opacity-100 flex items-center space-x-1">
                    {item.type === 'file' && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownload(item);
                          }}
                          className="p-1 hover:bg-gray-700 rounded"
                        >
                          <Download size={14} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(item);
                          }}
                          className="p-1 hover:bg-red-900/50 rounded text-red-400"
                        >
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modals */}
      {editingFile && (
        <FileEditor
          file={editingFile}
          workspace={workspace}
          onClose={() => setEditingFile(null)}
          onSave={() => {
            loadDirectory(currentPath);
            setEditingFile(null);
          }}
        />
      )}

      {showUpload && (
        <UploadModal
          workspace={workspace}
          path={currentPath}
          onClose={() => setShowUpload(false)}
          onUpload={() => {
            loadDirectory(currentPath);
            setShowUpload(false);
          }}
        />
      )}
    </div>
  );
}