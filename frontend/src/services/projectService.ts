/**
 * Project management service for API interactions
 */

import {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  ProjectSummary,
  UISettings,
  DeleteProjectResponse
} from '../types/project';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ProjectService {
  private baseUrl = `${API_BASE}/api/projects`;

  async connectWorkspace(data: ProjectCreate): Promise<ProjectResponse> {
    const response = await fetch(`${this.baseUrl}/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to connect to workspace');
    }

    return response.json();
  }

  async listProjects(): Promise<Project[]> {
    const response = await fetch(this.baseUrl);
    
    if (!response.ok) {
      throw new Error('Failed to list projects');
    }

    return response.json();
  }

  async getRecentProjects(): Promise<ProjectSummary[]> {
    const response = await fetch(`${this.baseUrl}/recent`);
    
    if (!response.ok) {
      throw new Error('Failed to get recent projects');
    }

    return response.json();
  }

  async getActiveProject(): Promise<Project | null> {
    const response = await fetch(`${this.baseUrl}/active`);
    
    if (!response.ok) {
      throw new Error('Failed to get active project');
    }

    const data = await response.json();
    return data || null;
  }

  async getProject(id: string): Promise<Project> {
    const response = await fetch(`${this.baseUrl}/${id}`);
    
    if (!response.ok) {
      throw new Error('Failed to get project');
    }

    return response.json();
  }

  async updateProject(id: string, data: ProjectUpdate): Promise<ProjectResponse> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update project');
    }

    return response.json();
  }

  async deleteProject(id: string, deleteFiles: boolean = false): Promise<DeleteProjectResponse> {
    const response = await fetch(`${this.baseUrl}/${id}?delete_files=${deleteFiles}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete project');
    }

    return response.json();
  }

  async activateProject(id: string): Promise<ProjectResponse> {
    const response = await fetch(`${this.baseUrl}/${id}/activate`, {
      method: 'POST'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to activate project');
    }

    return response.json();
  }

  async getUISettings(): Promise<UISettings> {
    const response = await fetch(`${this.baseUrl}/settings/ui`);
    
    if (!response.ok) {
      throw new Error('Failed to get UI settings');
    }

    return response.json();
  }

  async updateUISettings(settings: UISettings): Promise<UISettings> {
    const response = await fetch(`${this.baseUrl}/settings/ui`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update UI settings');
    }

    return response.json();
  }
}

export default new ProjectService();