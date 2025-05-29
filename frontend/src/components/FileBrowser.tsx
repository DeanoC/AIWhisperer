import React, { useState, useEffect } from 'react';
import { JsonRpcService } from '../services/jsonRpcService';
import './FileBrowser.css';

interface FileBrowserProps {
  jsonRpcService?: JsonRpcService;
  onFileSelect?: (filePath: string) => void;
}

interface TreeNode {
  name: string;
  path: string;
  isFile: boolean;
  depth: number;
}

interface FileContent {
  path: string;
  content: string | null;
  is_binary: boolean;
  size: number;
  total_lines?: number;
  error?: string;
}

export const FileBrowser: React.FC<FileBrowserProps> = ({ jsonRpcService, onFileSelect }) => {
  const [treeData, setTreeData] = useState<string>('');
  const [treeNodes, setTreeNodes] = useState<TreeNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loadingContent, setLoadingContent] = useState(false);

  useEffect(() => {
    if (jsonRpcService) {
      loadFileTree();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jsonRpcService]);

  const parseTreeToNodes = (treeText: string): TreeNode[] => {
    const lines = treeText.split('\n');
    const nodes: TreeNode[] = [];
    const pathStack: string[] = [];
    let lastDepth = -1;
    
    // Create a node for each line, even empty ones, to maintain index alignment
    lines.forEach((line, index) => {
      if (!line.trim()) {
        // Push null for empty lines to maintain index alignment
        nodes.push(null as any);
        return;
      }

      // Calculate depth by counting the tree structure characters
      let depth = 0;
      for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '│' || char === ' ' || char === '├' || char === '└' || char === '─') {
          continue;
        } else {
          // Found the first real character, calculate depth
          // Each level in the tree uses 4 characters (e.g., "│   " or "    ")
          depth = Math.floor(i / 4);
          break;
        }
      }
      
      // Extract the actual name from the line
      const name = line
        .replace(/[│├└─\s]+/g, ' ')
        .trim()
        .split(' ')
        .filter(part => part && !part.match(/^[│├└─]+$/))
        .join(' ');

      if (!name || name === 'AIWhisperer') {
        // Root directory - still push a node to maintain alignment
        nodes.push({
          name: 'AIWhisperer',
          path: '.',
          isFile: false,
          depth: 0
        });
        pathStack[0] = '.';
        return;
      }

      // Adjust path stack based on depth
      if (depth <= lastDepth) {
        // Pop items from stack when going back up the tree
        pathStack.splice(depth + 1);
      }

      // Build the full path
      // Ensure pathStack has entries up to current depth
      while (pathStack.length <= depth) {
        pathStack.push('.');
      }
      
      const parentPath = depth === 0 ? '.' : (pathStack[depth - 1] || '.');
      const fullPath = parentPath === '.' ? name : `${parentPath}/${name}`;
      
      // Update path stack
      pathStack[depth] = fullPath;
      lastDepth = depth;

      // Determine if it's a file (doesn't have children in next lines)
      let isFile = true;
      if (index < lines.length - 1) {
        const nextLine = lines[index + 1];
        if (nextLine.trim()) {
          // Calculate next line's depth using the same method
          let nextDepth = 0;
          for (let i = 0; i < nextLine.length; i++) {
            const char = nextLine[i];
            if (char === '│' || char === ' ' || char === '├' || char === '└' || char === '─') {
              continue;
            } else {
              nextDepth = Math.floor(i / 4);
              break;
            }
          }
          if (nextDepth > depth) {
            isFile = false;
          }
        }
      }

      // Use file extension as a hint when no children are detected
      // This prevents directories like .github or node_modules.old from being marked as files
      if (isFile) {
        // Check if it looks like a file based on extension
        const hasCommonExtension = /\.\w{1,5}$/.test(name);
        const hasDotInName = name.includes('.');
        
        // If no extension and no dots, it's probably a directory
        // Common patterns: directories rarely have extensions, files usually do
        if (!hasCommonExtension && !hasDotInName) {
          isFile = false;
        }
        
        // Special case: hidden directories often start with dot but have no extension
        // e.g., .git, .vscode, .github
        if (hasDotInName && !hasCommonExtension) {
          const parts = name.split('.');
          const lastPart = parts[parts.length - 1];
          // If the part after the last dot is long or contains no numbers, probably a directory
          if (lastPart.length > 5 || !/\d/.test(lastPart)) {
            isFile = false;
          }
        }
      }

      const nodeData = {
        name,
        path: fullPath,
        isFile,
        depth
      };
      
      // Log all nodes for debugging to track path construction
      if (depth <= 3) {
        console.log(`Node (depth ${depth}):`, {
          name,
          fullPath,
          isFile,
          parentPath,
          pathStack: [...pathStack]
        });
      }
      
      nodes.push(nodeData);
    });

    return nodes;
  };

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
        const nodes = parseTreeToNodes(result.tree);
        setTreeNodes(nodes);
      } else if (result && result.error) {
        setError(result.error);
        setTreeData('');
        setTreeNodes([]);
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
      
      console.error('Error details:', {
        message: errorMessage,
        error: err,
        fullError: JSON.stringify(err, null, 2)
      });
      
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

  const handleNodeClick = (node: TreeNode) => {
    if (node.isFile) {
      setSelectedPath(node.path);
      loadFileContent(node.path);
      if (onFileSelect) {
        onFileSelect(node.path);
      }
    } else {
      // For directories, just clear the selection
      setSelectedPath(null);
      setFileContent(null);
    }
  };

  const handleLineClick = (line: string, lineIndex: number) => {
    // Find the corresponding node for this line
    const node = treeNodes[lineIndex];
    if (node && node.isFile) {
      handleNodeClick(node);
    }
  };

  const renderTreeLine = (line: string, index: number) => {
    const node = treeNodes[index];
    const isSelected = node && selectedPath === node.path;
    const isClickable = node && node.isFile;
    
    // Add visual indicators for files vs folders
    let enhancedLine = line;
    if (node) {
      const icon = node.isFile ? '📄' : '📁';
      // Find where to insert the icon (after tree characters)
      const match = line.match(/([│├└─\s]+)(.+)/);
      if (match) {
        enhancedLine = match[1] + icon + ' ' + match[2];
      }
    }
    
    return (
      <div
        key={index}
        className={`tree-line ${isSelected ? 'selected' : ''} ${isClickable ? 'clickable' : ''} ${node && !node.isFile ? 'directory' : ''}`}
        onClick={() => handleLineClick(line, index)}
        title={node ? node.path : ''}
      >
        {enhancedLine}
      </div>
    );
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
        
        {/* File Preview Panel */}
        {selectedPath && (
          <div className="file-preview">
            <div className="file-preview-header">
              <h3>{selectedPath}</h3>
              {fileContent && !fileContent.is_binary && fileContent.total_lines && (
                <span className="file-info">
                  {fileContent.total_lines} lines • {(fileContent.size / 1024).toFixed(1)} KB
                </span>
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
                  <p className="file-size">{(fileContent.size / 1024).toFixed(1)} KB</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};