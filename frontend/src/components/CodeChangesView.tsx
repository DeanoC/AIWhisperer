import React, { useState, useCallback, useRef, useEffect } from 'react';
import DiffViewer from 'react-diff-viewer-continued';
import './CodeChangesView.css';

interface FileChange {
  id: string;
  path: string;
  status: 'added' | 'modified' | 'deleted';
  additions: number;
  deletions: number;
  oldContent?: string;
  newContent?: string;
}

interface CodeChangesData {
  files: FileChange[];
  summary: {
    totalFiles: number;
    totalAdditions: number;
    totalDeletions: number;
  };
}

export interface CodeChangesViewProps {
  data?: CodeChangesData;
}

interface FileListItemProps {
  file: FileChange;
  isSelected: boolean;
  isFocused: boolean;
  onClick: () => void;
  onFocus: () => void;
}

const FileListItem: React.FC<FileListItemProps> = ({ 
  file, 
  isSelected, 
  isFocused,
  onClick,
  onFocus
}) => {
  const statusIcon = {
    added: '+',
    modified: 'M',
    deleted: '-'
  };

  const statusClass = `status-${file.status}`;

  return (
    <li
      className={`file-item ${statusClass} ${isSelected ? 'selected' : ''} ${isFocused ? 'focused' : ''}`}
      data-testid={`file-item-${file.id}`}
      onClick={onClick}
      onFocus={onFocus}
      tabIndex={0}
    >
      <span className="status-icon">{statusIcon[file.status]}</span>
      <span className="file-path">{file.path}</span>
      <span className="file-stats">
        {file.additions > 0 && <span className="additions">+{file.additions}</span>}
        {file.deletions > 0 && <span className="deletions">-{file.deletions}</span>}
      </span>
    </li>
  );
};

export const CodeChangesView: React.FC<CodeChangesViewProps> = ({ data }) => {
  const [selectedFile, setSelectedFile] = useState<FileChange | null>(null);
  const [focusedIndex, setFocusedIndex] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [showFileList, setShowFileList] = useState(true);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');
  const fileListRef = useRef<HTMLDivElement>(null);

  // Filter files based on search
  const filteredFiles = data?.files.filter(file => 
    file.path.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!fileListRef.current || !fileListRef.current.contains(document.activeElement)) return;

      const maxIndex = filteredFiles.length - 1;
      let newIndex = focusedIndex;

      switch (e.key) {
        case 'ArrowDown':
        case 'j':
          e.preventDefault();
          newIndex = Math.min(focusedIndex + 1, maxIndex);
          break;
        case 'ArrowUp':
        case 'k':
          e.preventDefault();
          newIndex = Math.max(focusedIndex - 1, 0);
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredFiles[focusedIndex]) {
            setSelectedFile(filteredFiles[focusedIndex]);
          }
          break;
      }

      if (newIndex !== focusedIndex) {
        setFocusedIndex(newIndex);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [focusedIndex, filteredFiles]);

  // Copy diff to clipboard
  const handleCopyDiff = useCallback(() => {
    if (!selectedFile) return;

    const diff = `--- ${selectedFile.path}\n+++ ${selectedFile.path}\n${selectedFile.oldContent || ''}\n${selectedFile.newContent || ''}`;
    navigator.clipboard.writeText(diff);
  }, [selectedFile]);

  // Export all changes
  const handleExport = useCallback(() => {
    if (!data) return;

    const exportData = JSON.stringify(data, null, 2);
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code-changes-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  if (!data) {
    return (
      <div className="code-changes-view empty" data-testid="code-view">
        <p>No code changes available</p>
      </div>
    );
  }

  if (data.files.length === 0) {
    return (
      <div className="code-changes-view empty" data-testid="code-view">
        <p>No files changed</p>
      </div>
    );
  }

  // For virtualization of long lists (simplified version)
  const visibleFiles = filteredFiles.length > 50 ? filteredFiles.slice(0, 50) : filteredFiles;

  return (
    <div className="code-changes-view supports-high-contrast" data-testid="code-changes-view">
      <div className="code-changes-header">
        <div className="summary">
          <span>{filteredFiles.length === data.files.length ? 
            `${data.summary.totalFiles} files changed` : 
            `${filteredFiles.length} file${filteredFiles.length !== 1 ? 's' : ''} shown`}</span>
          <span className="additions">+{data.summary.totalAdditions} additions</span>
          <span className="deletions">-{data.summary.totalDeletions} deletions</span>
        </div>

        <div className="controls">
          <input
            type="text"
            placeholder="Search files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button onClick={() => setShowFileList(!showFileList)}>
            {showFileList ? 'Hide Files' : 'Show Files'}
          </button>
          {selectedFile && (
            <>
              <button onClick={() => setViewMode(viewMode === 'split' ? 'unified' : 'split')}>
                {viewMode === 'split' ? 'Unified View' : 'Split View'}
              </button>
              <button onClick={handleCopyDiff}>Copy Diff</button>
            </>
          )}
          <button onClick={handleExport}>Export Changes</button>
        </div>
      </div>

      <div className="code-changes-content">
        {showFileList && (
          <div 
            ref={fileListRef}
            className="file-list-container"
            data-testid="file-list"
          >
            <ul role="list" aria-label="Changed files">
              {visibleFiles.map((file, index) => (
                <FileListItem
                  key={file.id}
                  file={file}
                  isSelected={selectedFile?.id === file.id}
                  isFocused={focusedIndex === index}
                  onClick={() => setSelectedFile(file)}
                  onFocus={() => setFocusedIndex(index)}
                />
              ))}
            </ul>
          </div>
        )}

        <div className="diff-container" role="region" aria-label="Code diff viewer">
          {selectedFile ? (
            <>
              <div className="diff-header">
                <h3>{selectedFile.path}</h3>
                <span className={`status status-${selectedFile.status}`}>
                  {selectedFile.status}
                </span>
              </div>
              
              {selectedFile.oldContent !== undefined && selectedFile.newContent !== undefined ? (
                <DiffViewer
                  oldValue={selectedFile.oldContent}
                  newValue={selectedFile.newContent}
                  splitView={viewMode === 'split'}
                  hideLineNumbers={false}
                  showDiffOnly={true}
                  useDarkTheme={true}
                />
              ) : (
                <div className="no-content">Content not available</div>
              )}
            </>
          ) : (
            <div className="no-selection">
              Select a file to view changes
            </div>
          )}
        </div>
      </div>

      <div role="status" className="sr-only" aria-live="polite">
        {selectedFile && `Viewing ${selectedFile.path}`}
      </div>
    </div>
  );
};