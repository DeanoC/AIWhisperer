import React, { useEffect, useState } from 'react';
import { ProjectSettingsPanel } from './ProjectSettingsPanel';
import projectService from '../services/projectService';
import { ProjectSettings, UISettings, Project } from '../types/project';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
  const [projectSettings, setProjectSettings] = useState<ProjectSettings>({});
  const [uiSettings, setUISettings] = useState<UISettings>({ autoLoadLastProject: false, showProjectSelector: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  useEffect(() => {
    async function fetchSettings() {
      setLoading(true);
      setError(null);
      try {
        // Get UI settings
        const ui = await projectService.getUISettings();
        setUISettings(ui);
        // Get active project and its settings
        const project: Project | null = await projectService.getActiveProject();
        if (project && project.settings) {
          setProjectSettings(project.settings);
          setActiveProjectId(project.id);
        } else {
          setProjectSettings({});
          setActiveProjectId(null);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load settings');
      } finally {
        setLoading(false);
      }
    }
    fetchSettings();
  }, []);

  const handleChange = (changes: { project?: Partial<ProjectSettings>, ui?: Partial<UISettings> }) => {
    if (changes.project && activeProjectId) {
      setProjectSettings(prev => ({ ...prev, ...changes.project }));
      // Save project settings to backend
      projectService.updateProject(activeProjectId, { settings: { ...projectSettings, ...changes.project } });
    }
    if (changes.ui) {
      setUISettings(prev => ({ ...prev, ...changes.ui }));
      projectService.updateUISettings({ ...uiSettings, ...changes.ui });
    }
  };

  if (loading) {
    return (
      <div className="settings-container">
        <div className="settings-loading">
          <span className="loader"></span>
          <p>Loading settings...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="settings-container">
        <div className="settings-error">
          <span className="error-icon">⚠️</span>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <h2>Settings</h2>
      </div>
      <div className="settings-content">
        <ProjectSettingsPanel
          projectSettings={projectSettings}
          uiSettings={uiSettings}
          onChange={handleChange}
        />
      </div>
    </div>
  );
};
