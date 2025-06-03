/**
 * CodeEditor Component
 * 
 * This component provides a Monaco-based code editor that integrates with the agent-first architecture.
 * File operations (save, etc.) are routed through the AI agent system, which uses tools like write_file
 * to perform actual file operations. This ensures all file changes go through the proper agent workflow
 * and can be logged, tracked, and processed by the agent system.
 * 
 * Architecture notes:
 * - Primary: Uses onSendMessage to send natural language requests to agents
 * - Fallback: Uses direct JSON-RPC for systems without agent integration
 * - Agent Integration: Messages are processed by agents who have access to file operation tools
 */

import React, { useRef, useEffect, useState } from 'react';
import Editor, { loader } from '@monaco-editor/react';
import { JsonRpcService } from '../services/jsonRpcService';
import { useProject } from '../contexts/ProjectContext';
import './CodeEditor.css';

interface CodeEditorProps {
  filePath: string;
  jsonRpcService?: JsonRpcService;
  onClose?: () => void;
  onSendMessage?: (message: string) => void; // For sending commands through chat
  theme?: 'light' | 'dark';
}

interface FileContent {
  path: string;
  content: string | null;
  is_binary: boolean;
  size: number;
  total_lines?: number;
  error?: string;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  filePath,
  jsonRpcService,
  onClose,
  onSendMessage,
  theme = 'light'
}) => {
  const [fileContent, setFileContent] = useState<FileContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [currentContent, setCurrentContent] = useState<string>('');
  const editorRef = useRef<any>(null);

  const { uiSettings } = useProject();

  useEffect(() => {
    loadFileContent();
  }, [filePath, jsonRpcService]);

  const loadFileContent = async () => {
    if (!jsonRpcService) {
      setFileContent({
        path: filePath,
        content: null,
        is_binary: false,
        size: 0,
        error: 'WebSocket not connected'
      });
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const response = await jsonRpcService.sendRequest('workspace.getFileContent', { 
        path: filePath
      });
      
      setFileContent(response);
      setCurrentContent(response.content || '');
      setHasUnsavedChanges(false);
    } catch (err: any) {
      console.error('Failed to load file:', err);
      const errorMessage = err?.message || 'Failed to load file';
      setFileContent({
        path: filePath,
        content: null,
        is_binary: false,
        size: 0,
        error: errorMessage
      });
    } finally {
      setLoading(false);
    }
  };

  const saveFile = async () => {
    if (!hasUnsavedChanges) return;
    
    const currentContent = editorRef.current?.getValue() || '';

    try {
      setSaving(true);
      
      // Use agent system to write file (agent-first architecture)
      if (uiSettings?.alwaysUseClassicFileWrite && jsonRpcService) {
        // Force fallback to direct JSON-RPC if user setting is enabled
        console.log('[CodeEditor] Forcing classic file write due to user setting');
        await jsonRpcService.sendRequest('workspace.writeFile', {
          path: filePath,
          content: currentContent
        });
        setHasUnsavedChanges(false);
        setFileContent(prev => prev ? { ...prev, content: currentContent } : null);
      } else if (onSendMessage) {
        // Primary approach: Send a natural language request to the agent
        // The agent will use the write_file tool to handle this operation
        const writeRequest = `Please use the write_file tool to save the following content to "${filePath}":\n\n${currentContent}`;
        // Alternative approach: Use the direct /write_file command
        // const writeCommand = `/write_file ${filePath} ${currentContent}`;
        console.log('[CodeEditor] Sending file save request to agent system');
        onSendMessage(writeRequest);
        // Optimistically update the UI - the agent system will handle the actual save
        // Note: In a full implementation, we might want to wait for agent confirmation
        setHasUnsavedChanges(false);
        setFileContent(prev => prev ? { ...prev, content: currentContent } : null);
        // Show user feedback that the request was sent to the agent
        console.log('[CodeEditor] File save request sent to agent system');
      } else if (jsonRpcService) {
        // Fallback to direct JSON-RPC if no agent system available
        console.log('[CodeEditor] Using JSON-RPC fallback for file save');
        await jsonRpcService.sendRequest('workspace.writeFile', {
          path: filePath,
          content: currentContent
        });
        setHasUnsavedChanges(false);
        setFileContent(prev => prev ? { ...prev, content: currentContent } : null);
      } else {
        throw new Error('No save method available - neither agent system nor JSON-RPC');
      }
    } catch (err: any) {
      console.error('[CodeEditor] Failed to save file:', err);
      alert(`Failed to save file: ${err?.message || 'Unknown error'}`);
      // Revert optimistic update on error
      setHasUnsavedChanges(true);
    } finally {
      setSaving(false);
    }
  };

  const handleEditorChange = (value: string | undefined) => {
    const newContent = value || '';
    setCurrentContent(newContent);
    setHasUnsavedChanges(newContent !== (fileContent?.content || ''));
  };

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor;
    // Use the global monaco instance for keybindings
    loader.init().then(monaco => {
      editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
        saveFile();
      });
    });
  };

  const getLanguageFromFilePath = (path: string): string => {
    const extension = path.split('.').pop()?.toLowerCase();
    
    const languageMap: Record<string, string> = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'json': 'json',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'sass': 'sass',
      'md': 'markdown',
      'yaml': 'yaml',
      'yml': 'yaml',
      'xml': 'xml',
      'sh': 'shell',
      'bash': 'shell',
      'sql': 'sql',
      'php': 'php',
      'java': 'java',
      'c': 'c',
      'cpp': 'cpp',
      'h': 'c',
      'hpp': 'cpp',
      'cs': 'csharp',
      'go': 'go',
      'rs': 'rust',
      'rb': 'ruby',
      'kt': 'kotlin',
      'swift': 'swift',
      'r': 'r',
      'dockerfile': 'dockerfile'
    };

    return languageMap[extension || ''] || 'plaintext';
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="code-editor-container">
        <div className="code-editor-header">
          <h3>{filePath}</h3>
        </div>
        <div className="code-editor-loading">
          Loading file content...
        </div>
      </div>
    );
  }

  if (fileContent?.error) {
    return (
      <div className="code-editor-container">
        <div className="code-editor-header">
          <h3>{filePath}</h3>
          {onClose && (
            <button className="close-button" onClick={onClose}>×</button>
          )}
        </div>
        <div className="code-editor-error">
          <span className="error-icon">⚠️</span>
          <span>{fileContent.error}</span>
          <button onClick={async () => { 
            console.log('[CodeEditor] Retrying load for', filePath); 
            await loadFileContent();
            // Clear error state if load is successful
            setFileContent(fc => {
              if (fc && fc.error) {
                // Only clear error if file loaded successfully
                return { ...fc, error: undefined, path: fc.path || filePath, content: fc.content || '', is_binary: fc.is_binary || false, size: fc.size || 0 };
              }
              return fc;
            });
          }}>Retry</button>
        </div>
      </div>
    );
  }

  if (fileContent?.is_binary) {
    return (
      <div className="code-editor-container">
        <div className="code-editor-header">
          <h3>{filePath}</h3>
          {onClose && (
            <button className="close-button" onClick={onClose}>×</button>
          )}
        </div>
        <div className="code-editor-binary">
          <span className="icon">📎</span>
          <p>Binary file - cannot be edited</p>
          <p className="file-size">{formatFileSize(fileContent.size)}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="code-editor-container">
      <div className="code-editor-header">
        <div className="file-info">
          <h3>{filePath}</h3>
          {fileContent && (
            <span className="file-stats">
              {fileContent.total_lines} lines • {formatFileSize(fileContent.size)}
              {hasUnsavedChanges && <span className="unsaved-indicator">• Modified</span>}
            </span>
          )}
        </div>
        <div className="editor-actions">
          {hasUnsavedChanges && (
            <button 
              className="save-button"
              onClick={saveFile}
              disabled={saving}
              title={onSendMessage ? "Save via Agent System (Ctrl+S)" : "Save (Ctrl+S)"}
            >
              {saving ? 'Saving...' : (onSendMessage ? 'Save via Agent' : 'Save')}
            </button>
          )}
          <button 
            className="reload-button"
            onClick={loadFileContent}
            title="Reload file"
          >
            ↻
          </button>
          {onClose && (
            <button className="close-button" onClick={onClose} title="Close">×</button>
          )}
        </div>
      </div>
      
      <div className="code-editor-content">
        <Editor
          height="100%"
          language={getLanguageFromFilePath(filePath)}
          value={currentContent}
          onChange={handleEditorChange}
          onMount={handleEditorDidMount}
          theme={theme === 'dark' ? 'vs-dark' : 'vs'}
          options={{
            fontSize: 14,
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 2,
            insertSpaces: true,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderWhitespace: 'boundary',
            bracketPairColorization: { enabled: true },
            formatOnType: true,
            formatOnPaste: true,
            suggest: {
              insertMode: 'replace'
            }
          }}
        />
      </div>
    </div>
  );
};
