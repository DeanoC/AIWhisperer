/**
 * Project management service using JSON-RPC over WebSocket
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
import { JsonRpcService } from './jsonRpcService';

class ProjectService {
  private jsonRpc: JsonRpcService | null = null;

  setJsonRpcService(service: JsonRpcService) {
    this.jsonRpc = service;
  }

  private ensureJsonRpc(): JsonRpcService {
    if (!this.jsonRpc) {
      throw new Error('JsonRpcService not initialized. WebSocket connection required.');
    }
    return this.jsonRpc;
  }

  async connectWorkspace(data: ProjectCreate): Promise<ProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.connect', data);
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to connect to workspace');
    }
  }

  async listProjects(): Promise<Project[]> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.list', {});
      return result.projects;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to list projects');
    }
  }

  async getRecentProjects(): Promise<ProjectSummary[]> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.recent', {});
      return result.projects;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get recent projects');
    }
  }

  async getActiveProject(): Promise<Project | null> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.active', {});
      return result.project || null;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get active project');
    }
  }

  async getProject(id: string): Promise<Project> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.get', { project_id: id });
      return result.project;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get project');
    }
  }

  async updateProject(id: string, data: ProjectUpdate): Promise<ProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.update', { 
        project_id: id,
        ...data 
      });
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update project');
    }
  }

  async deleteProject(id: string, deleteFiles: boolean = false): Promise<DeleteProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.delete', { 
        project_id: id,
        delete_files: deleteFiles 
      });
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete project');
    }
  }

  async activateProject(id: string): Promise<ProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.activate', { project_id: id });
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to activate project');
    }
  }

  async getUISettings(): Promise<UISettings> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.settings.get', {});
      return result.settings;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get UI settings');
    }
  }

  async updateUISettings(settings: UISettings): Promise<UISettings> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.settings.update', settings);
      return result.settings;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to update UI settings');
    }
  }
}

export default new ProjectService();