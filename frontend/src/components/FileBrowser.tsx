import React, { useState, useEffect } from 'react';
import { JsonRpcService } from '../services/jsonRpcService';
import { FileNode, DirectoryListingResponse } from '../types/fileSystem';
import './FileBrowser.css';

interface FileBrowserProps {
  jsonRpcService?: JsonRpcService;
  onFileSelect?: (filePath: string) => void;
  onOpenInEditor?: (filePath: string) => void;
}

interface FileContent {
  path: string;
  content: string | null;
  is_binary: boolean;
  size: number;
  total_lines?: number;
  error?: string;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({ jsonRpcService, onFileSelect, onOpenInEditor }) => {
  const [rootNodes, setRootNodes] = useState<FileNode[]>([]);
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [loadingPaths, setLoadingPaths] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    if (jsonRpcService) {
      loadRootDirectory();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jsonRpcService]);

  const loadRootDirectory = async () => {
    if (!jsonRpcService) {
      setError('WebSocket not connected');
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await jsonRpcService.sendRequest('workspace.listDirectory', { 
        path: '.',
        includeHidden: false,
        sortBy: 'name',
        sortDirection: 'asc'
      }) as DirectoryListingResponse;
      
      if (response.error) {
        setError(response.error);
        setRootNodes([]);
      } else {
        setRootNodes(response.nodes || []);
      }
    } catch (err) {
      console.error('Failed to load directory:', err);
      setError(err instanceof Error ? err.message : 'Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  const loadDirectoryContents = async (path: string) => {
    if (!jsonRpcService || loadingPaths.has(path)) return;
    
    setLoadingPaths(prev => new Set(prev).add(path));
    
    try {
      const response = await jsonRpcService.sendRequest('workspace.listDirectory', { 
        path,
        includeHidden: false,
        sortBy: 'name',
        sortDirection: 'asc'
      }) as DirectoryListingResponse;
      
      if (!response.error && response.nodes) {
        // Update the tree structure with the loaded children
        const updateNodes = (nodes: FileNode[]): FileNode[] => {
          return nodes.map(node => {
            if (node.path === path) {
              return {
                ...node,
                children: response.nodes,
                isLoaded: true
              };
            } else if (node.children) {
              return {
                ...node,
                children: updateNodes(node.children)
              };
            }
            return node;
          });
        };
        
        setRootNodes(updateNodes(rootNodes));
      }
    } catch (err) {
      console.error('Failed to load directory contents:', err);
    } finally {
      setLoadingPaths(prev => {
        const next = new Set(prev);
        next.delete(path);
        return next;
      });
    }
  };

  const toggleDirectory = async (node: FileNode) => {
    const isExpanded = expandedPaths.has(node.path);
    
    if (isExpanded) {
      // Collapse
      setExpandedPaths(prev => {
        const next = new Set(prev);
        next.delete(node.path);
        return next;
      });
    } else {
      // Expand
      setExpandedPaths(prev => new Set(prev).add(node.path));
      
      // Load children if not already loaded
      if (!node.isLoaded) {
        await loadDirectoryContents(node.path);
      }
    }
  };

  const loadFileContent = async (path: string) => {
    if (!jsonRpcService) return;
    
    setLoadingContent(true);
    try {
      console.log('Loading file content for path:', path);
      const result = await jsonRpcService.sendRequest('workspace.getFileContent', { path });
      console.log('File content result:', result);
      setFileContent(result);
    } catch (err: any) {
      console.error('Failed to load file content:', err);
      
      // Extract error message from JSON-RPC error object
      let errorMessage = 'Failed to load file';
      if (err && typeof err === 'object') {
        if (err.message) {
          errorMessage = err.message;
        } else if (err.error && err.error.message) {
          errorMessage = err.error.message;
        }
      } else if (err instanceof Error) {
        errorMessage = err.message;
      }
      
      setFileContent({
        path,
        content: null,
        is_binary: false,
        size: 0,
        error: errorMessage
      });
    } finally {
      setLoadingContent(false);
    }
  };

  const handleNodeClick = (node: FileNode) => {
    if (node.isFile) {
      setSelectedPath(node.path);
      loadFileContent(node.path);
      if (onFileSelect) {
        onFileSelect(node.path);
      }
    } else {
      toggleDirectory(node);
    }
  };

  const renderFileNode = (node: FileNode, level: number = 0): React.ReactNode => {
    const isExpanded = expandedPaths.has(node.path);
    const isLoading = loadingPaths.has(node.path);
    const isSelected = selectedPath === node.path;
    const indent = level * 20;
    
    return (
      <div key={node.path}>
        <div
          className={`file-node ${isSelected ? 'selected' : ''} ${node.isFile ? 'file' : 'directory'}`}
          style={{ paddingLeft: `${indent}px` }}
          onClick={() => handleNodeClick(node)}
          title={node.path}
        >
          <span className="file-icon">
            {!node.isFile ? (
              isLoading ? '⏳' : (isExpanded ? '📂' : '📁')
            ) : '📄'}
          </span>
          <span className="file-name">{node.name}</span>
          {node.isFile && node.size !== undefined && (
            <span className="file-size">{formatFileSize(node.size)}</span>
          )}
        </div>
        {!node.isFile && isExpanded && node.children && (
          <div className="file-children">
            {node.children.map(child => renderFileNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  return (
    <div className="file-browser-container" data-testid="file-browser">
      <div className="file-browser-split">
        {/* File Tree Panel */}
        <div className="file-browser">
          <div className="file-browser-header">
            <h3>Files</h3>
            <button 
              className="refresh-button"
              onClick={loadRootDirectory}
              disabled={loading}
              aria-label="Refresh file tree"
              title="Refresh"
            >
              🔄
            </button>
          </div>
          
          <div className="file-browser-content">
            {loading && (
              <div className="loading-state">
                Loading file tree...
              </div>
            )}
            
            {error && (
              <div className="error-state">
                <span className="error-icon">⚠️</span>
                <span>{error}</span>
                <button onClick={loadRootDirectory}>Retry</button>
              </div>
            )}
            
            {!loading && !error && rootNodes.length > 0 && (
              <div className="file-tree-structured">
                {rootNodes.map(node => renderFileNode(node))}
              </div>
            )}
            
            {!loading && !error && rootNodes.length === 0 && (
              <div className="empty-state">
                No files to display
              </div>
            )}
          </div>
        </div>
        
        {/* File Preview Panel */}
        {selectedPath && (
          <div className="file-preview">
            <div className="file-preview-header">
              <div className="file-header-info">
                <h3>{selectedPath}</h3>
                {fileContent && !fileContent.is_binary && fileContent.total_lines && (
                  <span className="file-info">
                    {fileContent.total_lines} lines • {formatFileSize(fileContent.size)}
                  </span>
                )}
              </div>
              
              {/* Button bar */}
              {fileContent && !fileContent.is_binary && !fileContent.error && onOpenInEditor && (
                <div className="file-actions">
                  <button 
                    className="open-editor-button"
                    onClick={() => onOpenInEditor(selectedPath)}
                    title="Open in Code Editor"
                  >
                    📝 Edit
                  </button>
                </div>
              )}
            </div>
            
            <div className="file-preview-content">
              {loadingContent && (
                <div className="loading-state">
                  Loading file content...
                </div>
              )}
              
              {!loadingContent && fileContent && fileContent.error && (
                <div className="error-state">
                  <span className="error-icon">⚠️</span>
                  <span>{fileContent.error}</span>
                </div>
              )}
              
              {!loadingContent && fileContent && fileContent.content && (
                <pre className="file-content">
                  <code>{fileContent.content}</code>
                </pre>
              )}
              
              {!loadingContent && fileContent && fileContent.is_binary && (
                <div className="binary-file-message">
                  <span className="icon">📎</span>
                  <p>Binary file - preview not available</p>
                  <p className="file-size">{formatFileSize(fileContent.size)}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};