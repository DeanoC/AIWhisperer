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
    const result = await this.ensureJsonRpc().call('project.connect', data);
    if (result.error) {
      throw new Error(result.error.message || 'Failed to connect to workspace');
    }
    return result;
  }

  async listProjects(): Promise<Project[]> {
    const result = await this.ensureJsonRpc().call('project.list', {});
    if (result.error) {
      throw new Error(result.error.message || 'Failed to list projects');
    }
    return result.projects;
  }

  async getRecentProjects(): Promise<ProjectSummary[]> {
    const result = await this.ensureJsonRpc().call('project.recent', {});
    if (result.error) {
      throw new Error(result.error.message || 'Failed to get recent projects');
    }
    return result.projects;
  }

  async getActiveProject(): Promise<Project | null> {
    const result = await this.ensureJsonRpc().call('project.active', {});
    if (result.error) {
      throw new Error(result.error.message || 'Failed to get active project');
    }
    return result.project || null;
  }

  async getProject(id: string): Promise<Project> {
    const result = await this.ensureJsonRpc().call('project.get', { project_id: id });
    if (result.error) {
      throw new Error(result.error.message || 'Failed to get project');
    }
    return result.project;
  }

  async updateProject(id: string, data: ProjectUpdate): Promise<ProjectResponse> {
    const result = await this.ensureJsonRpc().call('project.update', { 
      project_id: id,
      ...data 
    });
    if (result.error) {
      throw new Error(result.error.message || 'Failed to update project');
    }
    return result;
  }

  async deleteProject(id: string, deleteFiles: boolean = false): Promise<DeleteProjectResponse> {
    const result = await this.ensureJsonRpc().call('project.delete', { 
      project_id: id,
      delete_files: deleteFiles 
    });
    if (result.error) {
      throw new Error(result.error.message || 'Failed to delete project');
    }
    return result;
  }

  async activateProject(id: string): Promise<ProjectResponse> {
    const result = await this.ensureJsonRpc().call('project.activate', { project_id: id });
    if (result.error) {
      throw new Error(result.error.message || 'Failed to activate project');
    }
    return result;
  }

  async getUISettings(): Promise<UISettings> {
    const result = await this.ensureJsonRpc().call('project.settings.get', {});
    if (result.error) {
      throw new Error(result.error.message || 'Failed to get UI settings');
    }
    return result.settings;
  }

  async updateUISettings(settings: UISettings): Promise<UISettings> {
    const result = await this.ensureJsonRpc().call('project.settings.update', settings);
    if (result.error) {
      throw new Error(result.error.message || 'Failed to update UI settings');
    }
    return result.settings;
  }
}

export default new ProjectService();