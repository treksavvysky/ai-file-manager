'use client';

import { useState, useEffect } from 'react';
import { X, Save, Download } from 'lucide-react';
import { FileItem, Workspace } from '@/types';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface FileEditorProps {
  file: FileItem;
  workspace: Workspace;
  onClose: () => void;
  onSave: () => void;
}

export default function FileEditor({ file, workspace, onClose, onSave }: FileEditorProps) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadFile();
  }, [file]);

  const loadFile = async () => {
    try {
      const response = await api.get(`/workspaces/${workspace.name}/files/read`, {
        params: { file_path: file.relative_path }
      });
      setContent(response.data.content || '');
    } catch (error) {
      toast.error('Failed to load file');
    } finally {
      setLoading(false);
    }
  };
  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post(`/workspaces/${workspace.name}/files/create`, {
        file_path: file.relative_path,
        content
      });
      toast.success('File saved successfully');
      onSave();
    } catch (error) {
      toast.error('Failed to save file');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 rounded-xl w-full max-w-4xl h-3/4 flex flex-col shadow-2xl border border-gray-800">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <div>
            <h2 className="text-lg font-semibold">{file.name}</h2>
            <p className="text-sm text-gray-500">{file.relative_path}</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg flex items-center space-x-2 disabled:opacity-50 transition-colors"
            >
              <Save size={16} />
              <span>{saving ? 'Saving...' : 'Save'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 p-4 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="w-full h-full bg-gray-950 text-gray-200 font-mono text-sm p-4 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
              spellCheck={false}
            />
          )}
        </div>
      </div>
    </div>
  );
}