'use client';

import { useEffect, useRef } from 'react';
import { Copy, Cut, Trash2, Edit3, Download, FolderOpen } from 'lucide-react';

interface ContextMenuProps {
  x: number;
  y: number;
  onAction: (action: string) => void;
  onClose: () => void;
  itemType: 'file' | 'directory';
}

export default function ContextMenu({ x, y, onAction, onClose, itemType }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const menuItems = [
    { icon: FolderOpen, label: 'Open', action: 'open' },
    { icon: Edit3, label: 'Rename', action: 'rename' },
    { icon: Copy, label: 'Copy', action: 'copy' },
    { icon: Cut, label: 'Move', action: 'move' },
    ...(itemType === 'file' ? [{ icon: Download, label: 'Download', action: 'download' }] : []),
    { icon: Trash2, label: 'Delete', action: 'delete', className: 'text-red-400' },
  ];

  return (
    <div
      ref={menuRef}
      className="fixed bg-gray-800 rounded-lg shadow-xl border border-gray-700 py-1 z-50"
      style={{ left: x, top: y }}
    >
      {menuItems.map((item) => {
        const Icon = item.icon;
        return (
          <button
            key={item.action}
            onClick={() => {
              onAction(item.action);
              onClose();
            }}
            className={`w-full px-3 py-2 hover:bg-gray-700 flex items-center space-x-2 transition-colors ${item.className || ''}`}
          >
            <Icon size={14} />
            <span className="text-sm">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}