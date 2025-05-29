/**
 * Project selector component for switching between workspaces
 */

import React, { useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import './ProjectSelector.css';

export function ProjectSelector() {
  const { activeProject, recentProjects, activateProject, closeWorkspace, isLoading } = useProject();
  const [isOpen, setIsOpen] = useState(false);
  const [showConnectDialog, setShowConnectDialog] = useState(false);

  const handleProjectSelect = async (projectId: string) => {
    try {
      await activateProject(projectId);
      setIsOpen(false);
    } catch (err) {
      console.error('Failed to activate project:', err);
    }
  };

  const handleCloseWorkspace = async () => {
    try {
      await closeWorkspace();
      setIsOpen(false);
    } catch (err) {
      console.error('Failed to close workspace:', err);
    }
  };

  return (
    <>
      <div className="project-selector">
        <button
          className="project-selector-button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading}
        >
          <span className="project-icon">📁</span>
          <span className="project-name">
            {activeProject ? activeProject.name : 'No Workspace'}
          </span>
          <span className="dropdown-arrow">▼</span>
        </button>

        {isOpen && (
          <div className="project-dropdown">
            <div className="project-dropdown-header">
              <h3>Workspaces</h3>
              <div className="header-buttons">
                {activeProject && (
                  <button
                    className="close-button"
                    onClick={handleCloseWorkspace}
                  >
                    Close Workspace
                  </button>
                )}
                <button
                  className="connect-button"
                  onClick={() => {
                    setShowConnectDialog(true);
                    setIsOpen(false);
                  }}
                >
                  Connect Workspace
                </button>
              </div>
            </div>

            {recentProjects.length > 0 ? (
              <div className="project-list">
                {recentProjects.map(project => (
                  <div
                    key={project.id}
                    className={`project-item ${project.id === activeProject?.id ? 'active' : ''}`}
                    onClick={() => handleProjectSelect(project.id)}
                  >
                    <div className="project-item-name">{project.name}</div>
                    <div className="project-item-path">{project.path}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-projects">
                <p>No workspaces connected yet.</p>
                <p>Click "Connect Workspace" to get started.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {showConnectDialog && (
        <ConnectWorkspaceDialog onClose={() => setShowConnectDialog(false)} />
      )}
    </>
  );
}

interface ConnectWorkspaceDialogProps {
  onClose: () => void;
}

function ConnectWorkspaceDialog({ onClose }: ConnectWorkspaceDialogProps) {
  const { connectWorkspace } = useProject();
  const [name, setName] = useState('');
  const [path, setPath] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsConnecting(true);

    try {
      await connectWorkspace(name, path, description);
      onClose();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleBrowse = () => {
    // In a real implementation, this would open a file browser dialog
    // For now, we'll just show a placeholder message
    alert('File browser integration coming soon. Please type the path manually.');
  };

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog" onClick={e => e.stopPropagation()}>
        <div className="dialog-header">
          <h2>Connect to Workspace</h2>
          <button className="dialog-close" onClick={onClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="name">Workspace Name</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="My React App"
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label htmlFor="path">Workspace Path</label>
            <div className="path-input-group">
              <input
                id="path"
                type="text"
                value={path}
                onChange={e => setPath(e.target.value)}
                placeholder="/home/user/projects/my-app"
                required
              />
              <button type="button" onClick={handleBrowse} className="browse-button">
                Browse
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="description">Description (optional)</label>
            <textarea
              id="description"
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Brief description of the workspace"
              rows={3}
            />
          </div>

          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="dialog-actions">
            <button type="button" onClick={onClose} disabled={isConnecting}>
              Cancel
            </button>
            <button type="submit" disabled={isConnecting || !name || !path}>
              {isConnecting ? 'Connecting...' : 'Connect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}