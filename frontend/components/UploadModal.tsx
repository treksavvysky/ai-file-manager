'use client';

import { useState, useRef } from 'react';
import { X, Upload, File } from 'lucide-react';
import { Workspace } from '@/types';
import api from '@/lib/api';
import toast from 'react-hot-toast';

interface UploadModalProps {
  workspace: Workspace;
  path: string;
  onClose: () => void;
  onUpload: () => void;
}

export default function UploadModal({ workspace, path, onClose, onUpload }: UploadModalProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('path', path);

        await api.post(`/workspaces/${workspace.name}/upload`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      }
      toast.success(`Uploaded ${files.length} file(s)`);
      onUpload();
    } catch (error) {
      toast.error('Failed to upload files');
    } finally {
      setUploading(false);
    }
  };            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {files.length > 0 && (
          <div className="mt-4 max-h-48 overflow-y-auto">
            <p className="text-sm text-gray-400 mb-2">Selected files:</p>
            <div className="space-y-1">
              {files.map((file, index) => (
                <div key={index} className="flex items-center space-x-2 text-sm">
                  <File size={14} className="text-gray-500" />
                  <span className="text-gray-300">{file.name}</span>
                  <span className="text-gray-600">({(file.size / 1024).toFixed(1)} KB)</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpload}
            disabled={files.length === 0 || uploading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50 transition-colors flex items-center space-x-2"
          >
            <Upload size={16} />
            <span>{uploading ? 'Uploading...' : 'Upload'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}