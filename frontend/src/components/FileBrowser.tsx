import React, { useState, useEffect } from 'react';
import { JsonRpcService } from '../services/jsonRpcService';
import './FileBrowser.css';

interface FileBrowserProps {
  jsonRpcService?: JsonRpcService;
  onFileSelect?: (filePath: string) => void;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({ jsonRpcService, onFileSelect }) => {
  const [treeData, setTreeData] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  useEffect(() => {
    if (jsonRpcService) {
      loadFileTree();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jsonRpcService]);

  const loadFileTree = async () => {
    if (!jsonRpcService) {
      setError('WebSocket not connected');
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await jsonRpcService.sendRequest('workspace.getTree', { path: '.' });
      
      if (result && result.tree) {
        setTreeData(result.tree);
      } else {
        setError('No tree data received');
      }
    } catch (err) {
      console.error('Failed to load file tree:', err);
      setError(err instanceof Error ? err.message : 'Failed to load file tree');
    } finally {
      setLoading(false);
    }
  };

  const handleLineClick = (line: string, lineIndex: number) => {
    // Extract file path from the line if possible
    // This is a simple implementation - can be enhanced later
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.includes('Error') && !trimmedLine.includes('[')) {
      // Remove tree characters like ├──, └──, │
      const cleanedLine = trimmedLine.replace(/[├└│─\s]+/g, ' ').trim();
      
      if (cleanedLine && onFileSelect) {
        setSelectedPath(cleanedLine);
        onFileSelect(cleanedLine);
      }
    }
  };

  const renderTreeLine = (line: string, index: number) => {
    const isSelected = selectedPath && line.includes(selectedPath);
    
    return (
      <div
        key={index}
        className={`tree-line ${isSelected ? 'selected' : ''}`}
        onClick={() => handleLineClick(line, index)}
      >
        {line}
      </div>
    );
  };

  return (
    <div className="file-browser" data-testid="file-browser">
      <div className="file-browser-header">
        <h3>Files</h3>
        <button 
          className="refresh-button"
          onClick={loadFileTree}
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
            <button onClick={loadFileTree}>Retry</button>
          </div>
        )}
        
        {!loading && !error && treeData && (
          <pre className="file-tree">
            {treeData.split('\n').map((line, index) => renderTreeLine(line, index))}
          </pre>
        )}
        
        {!loading && !error && !treeData && (
          <div className="empty-state">
            No files to display
          </div>
        )}
      </div>
    </div>
  );
};