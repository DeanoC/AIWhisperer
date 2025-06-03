/**
 * Project context for managing active project state
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Project, ProjectSummary, UISettings } from '../types/project';
import projectService from '../services/projectService';
import { JsonRpcService } from '../services/jsonRpcService';

interface ProjectContextType {
  activeProject: Project | null;
  recentProjects: ProjectSummary[];
  uiSettings: UISettings | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  connectWorkspace: (name: string, path: string, description?: string, outputPath?: string) => Promise<void>;
  joinProject: (path: string) => Promise<void>;
  createNewProject: (name: string, parentPath: string, template: string, description?: string, gitInit?: boolean) => Promise<void>;
  activateProject: (projectId: string) => Promise<void>;
  updateProject: (projectId: string, updates: any) => Promise<void>;
  deleteProject: (projectId: string, deleteFiles?: boolean) => Promise<void>;
  closeWorkspace: () => Promise<void>;
  refreshProjects: () => Promise<void>;
  updateUISettings: (settings: UISettings) => Promise<void>;
  
  // WebSocket integration
  setJsonRpcService: (service: JsonRpcService | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}

interface ProjectProviderProps {
  children: ReactNode;
}

export function ProjectProvider({ children }: ProjectProviderProps) {
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [recentProjects, setRecentProjects] = useState<ProjectSummary[]>([]);
  const [uiSettings, setUiSettings] = useState<UISettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [jsonRpcService, setJsonRpcServiceState] = useState<JsonRpcService | null>(null);

  // Set JSON-RPC service
  const setJsonRpcService = useCallback((service: JsonRpcService | null) => {
    setJsonRpcServiceState(service);
    if (service) {
      projectService.setJsonRpcService(service);
    }
  }, []);

  // Load initial data when JSON-RPC service is available
  useEffect(() => {
    if (jsonRpcService) {
      loadInitialData();
    }
  }, [jsonRpcService]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load UI settings
      const settings = await projectService.getUISettings();
      console.log('[ProjectContext] UI Settings:', settings);
      setUiSettings(settings);

      // Load recent projects
      const recent = await projectService.getRecentProjects();
      console.log('[ProjectContext] Recent projects:', recent);
      setRecentProjects(recent);

      // Load active project or last project if auto-load is enabled
      const active = await projectService.getActiveProject();
      console.log('[ProjectContext] Active project:', active);
      
      if (active) {
        setActiveProject(active);
      } else if (settings.autoLoadLastProject && recent.length > 0) {
        // Auto-load last project
        console.log('[ProjectContext] Auto-loading last project:', recent[0]);
        const lastProject = await projectService.getProject(recent[0].id);
        await projectService.activateProject(lastProject.id);
        setActiveProject(lastProject);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Failed to load project data');
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProjects = useCallback(async () => {
    try {
      const recent = await projectService.getRecentProjects();
      setRecentProjects(recent);
    } catch (err) {
      console.error('Failed to refresh projects:', err);
    }
  }, []);

  const connectWorkspace = useCallback(async (name: string, path: string, description?: string, outputPath?: string) => {
    try {
      setError(null);
      const response = await projectService.connectWorkspace({ name, path, description, outputPath });
      setActiveProject(response.project);
      await refreshProjects();
      
      // Trigger a custom event to notify other components
      window.dispatchEvent(new CustomEvent('workspace-changed', { 
        detail: { workspace: response.project } 
      }));
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const joinProject = useCallback(async (path: string) => {
    try {
      setError(null);
      const response = await projectService.joinProject({ path });
      setActiveProject(response.project);
      await refreshProjects();
      
      // Trigger a custom event to notify other components
      window.dispatchEvent(new CustomEvent('workspace-changed', { 
        detail: { workspace: response.project } 
      }));
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const createNewProject = useCallback(async (name: string, parentPath: string, template: string, description?: string, gitInit: boolean = false) => {
    try {
      setError(null);
      const response = await projectService.createNewProject({ 
        name, 
        path: parentPath, 
        template, 
        description,
        git_init: gitInit
      });
      setActiveProject(response.project);
      await refreshProjects();
      
      // Trigger a custom event to notify other components
      window.dispatchEvent(new CustomEvent('workspace-changed', { 
        detail: { workspace: response.project } 
      }));
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const activateProject = useCallback(async (projectId: string) => {
    try {
      setError(null);
      const response = await projectService.activateProject(projectId);
      setActiveProject(response.project);
      await refreshProjects();
      
      // Trigger a custom event to notify other components
      window.dispatchEvent(new CustomEvent('workspace-changed', { 
        detail: { workspace: response.project } 
      }));
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const updateProject = useCallback(async (projectId: string, updates: any) => {
    try {
      setError(null);
      const response = await projectService.updateProject(projectId, updates);
      if (activeProject?.id === projectId) {
        setActiveProject(response.project);
      }
      await refreshProjects();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [activeProject]);

  const deleteProject = useCallback(async (projectId: string, deleteFiles: boolean = false) => {
    try {
      setError(null);
      await projectService.deleteProject(projectId, deleteFiles);
      if (activeProject?.id === projectId) {
        setActiveProject(null);
      }
      await refreshProjects();
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [activeProject]);

  const closeWorkspace = useCallback(async () => {
    try {
      setError(null);
      await projectService.closeWorkspace();
      setActiveProject(null);
      
      // Trigger a custom event to notify other components
      window.dispatchEvent(new CustomEvent('workspace-changed', { 
        detail: { workspace: null } 
      }));
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const updateUISettings = useCallback(async (settings: UISettings) => {
    try {
      setError(null);
      const updated = await projectService.updateUISettings(settings);
      setUiSettings(updated);
    } catch (err: any) {
      setError(err.message);
      throw err;
    }
  }, [refreshProjects]);

  const value: ProjectContextType = {
    activeProject,
    recentProjects,
    uiSettings,
    isLoading,
    error,
    connectWorkspace,
    joinProject,
    createNewProject,
    activateProject,
    updateProject,
    deleteProject,
    closeWorkspace,
    refreshProjects,
    updateUISettings,
    setJsonRpcService
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
}