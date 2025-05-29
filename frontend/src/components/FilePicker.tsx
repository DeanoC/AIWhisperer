import React, { useState, useEffect, useRef } from 'react';
import { JsonRpcService } from '../services/jsonRpcService';
import { FileNode, DirectoryListingResponse } from '../types/fileSystem';
import './FilePicker.css';

interface FilePickerProps {
  jsonRpcService?: JsonRpcService;
  onSelect: (filePath: string) => void;
  onClose: () => void;
  isOpen: boolean;
}

export const FilePicker: React.FC<FilePickerProps> = ({ 
  jsonRpcService, 
  onSelect, 
  onClose,
  isOpen 
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [allNodes, setAllNodes] = useState<FileNode[]>([]);
  const [filteredNodes, setFilteredNodes] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPath, setCurrentPath] = useState('.');
  const searchInputRef = useRef<HTMLInputElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  // Load files when modal opens or path changes
  useEffect(() => {
    if (isOpen && jsonRpcService) {
      loadAllFiles();
    }
  }, [isOpen, jsonRpcService, currentPath]);

  // Focus search input when modal opens and reset state
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    } else if (!isOpen) {
      // Reset state when closing
      setCurrentPath('.');
      setSearchQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Handle click outside modal
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  const loadAllFiles = async () => {
    if (!jsonRpcService) return;

    setLoading(true);
    setError(null);
    
    try {
      const response = await jsonRpcService.sendRequest('workspace.listDirectory', {
        path: currentPath,
        recursive: false,  // Don't recurse, just show current directory
        maxDepth: 1,
        includeHidden: false,
        sortBy: 'name',
        sortDirection: 'asc'
      }) as DirectoryListingResponse;

      if (response.error) {
        setError(response.error);
      } else {
        // Include both files and directories for navigation
        const nodes = response.nodes || [];
        setAllNodes(nodes);
        setFilteredNodes(nodes);
      }
    } catch (err) {
      console.error('Failed to load files:', err);
      setError(err instanceof Error ? err.message : 'Failed to load files');
    } finally {
      setLoading(false);
    }
  };

  // Filter files based on search query
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredNodes(allNodes);
      setSelectedIndex(0);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = allNodes.filter(node => {
      const fileName = node.name.toLowerCase();
      const filePath = node.path.toLowerCase();
      
      // Simple fuzzy matching
      if (fileName.includes(query) || filePath.includes(query)) {
        return true;
      }
      
      // Match if all query characters appear in order
      let queryIndex = 0;
      for (let i = 0; i < filePath.length && queryIndex < query.length; i++) {
        if (filePath[i] === query[queryIndex]) {
          queryIndex++;
        }
      }
      return queryIndex === query.length;
    });

    // Sort by relevance (exact matches first, then by path length)
    filtered.sort((a, b) => {
      const aExact = a.name.toLowerCase() === query;
      const bExact = b.name.toLowerCase() === query;
      if (aExact && !bExact) return -1;
      if (!aExact && bExact) return 1;
      
      const aContains = a.name.toLowerCase().includes(query);
      const bContains = b.name.toLowerCase().includes(query);
      if (aContains && !bContains) return -1;
      if (!aContains && bContains) return 1;
      
      return a.path.length - b.path.length;
    });

    setFilteredNodes(filtered);
    setSelectedIndex(0);
  }, [searchQuery, allNodes]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(i => Math.min(i + 1, filteredNodes.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(i => Math.max(i - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (filteredNodes[selectedIndex]) {
          // Shift+Enter selects directories, Enter navigates into them
          handleSelect(filteredNodes[selectedIndex], e.shiftKey);
        }
        break;
      case 'Backspace':
        // Only navigate up if search is empty and we're not at root
        if (currentPath !== '.' && searchQuery === '') {
          e.preventDefault();
          const parentPath = currentPath.includes('/') 
            ? currentPath.substring(0, currentPath.lastIndexOf('/')) || '.'
            : '.';
          setCurrentPath(parentPath);
        }
        // Otherwise, let backspace work normally in the search field
        break;
      case 'Escape':
        e.preventDefault();
        onClose();
        break;
    }
  };

  const handleSelect = (node: FileNode, forceSelect: boolean = false) => {
    if (node.isFile || forceSelect) {
      // Select the file or directory
      onSelect(node.path);
      onClose();
    } else {
      // Navigate into the directory
      setCurrentPath(node.path);
      setSearchQuery(''); // Clear search when navigating
    }
  };

  if (!isOpen) return null;

  return (
    <div className="file-picker-overlay">
      <div className="file-picker-modal" ref={modalRef}>
        <div className="file-picker-header">
          <div className="file-picker-breadcrumb">
            <button 
              className="breadcrumb-item"
              onClick={() => setCurrentPath('.')}
              disabled={currentPath === '.'}
            >
              Root
            </button>
            {currentPath !== '.' && (
              <>
                <span className="breadcrumb-separator">/</span>
                <span className="breadcrumb-current">{currentPath}</span>
                <button
                  className="breadcrumb-up"
                  onClick={() => {
                    const parentPath = currentPath.includes('/') 
                      ? currentPath.substring(0, currentPath.lastIndexOf('/')) || '.'
                      : '.';
                    setCurrentPath(parentPath);
                  }}
                  title="Go up one level (Backspace)"
                >
                  ↑
                </button>
              </>
            )}
          </div>
          <div className="file-picker-search-row">
            <input
              ref={searchInputRef}
              type="text"
              className="file-picker-search"
              placeholder="Search in current directory..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button className="file-picker-close" onClick={onClose} aria-label="Close">
              ✕
            </button>
          </div>
        </div>
        
        <div className="file-picker-content">
          {loading && (
            <div className="file-picker-loading">
              Loading files...
            </div>
          )}
          
          {error && (
            <div className="file-picker-error">
              <span className="error-icon">⚠️</span>
              <span>{error}</span>
            </div>
          )}
          
          {!loading && !error && filteredNodes.length === 0 && (
            <div className="file-picker-empty">
              {searchQuery ? 'No files match your search' : 'No files available'}
            </div>
          )}
          
          {!loading && !error && filteredNodes.length > 0 && (
            <div className="file-picker-list">
              {filteredNodes.map((node, index) => (
                <div
                  key={node.path}
                  className={`file-picker-item ${index === selectedIndex ? 'selected' : ''}`}
                  onClick={() => handleSelect(node)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <span className="file-picker-icon">{node.isFile ? '📄' : '📁'}</span>
                  <div className="file-picker-item-info">
                    <div className="file-picker-name">{node.name}</div>
                    <div className="file-picker-path">{node.path}</div>
                  </div>
                  {!node.isFile && (
                    <button
                      className="file-picker-select-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelect(node, true);
                      }}
                      title="Select this directory"
                    >
                      Select
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="file-picker-footer">
          <div className="file-picker-hint">
            ↑↓ Navigate • Enter to open/select • Shift+Enter to select dir • Backspace to go up • Esc to cancel
          </div>
        </div>
      </div>
    </div>
  );
};