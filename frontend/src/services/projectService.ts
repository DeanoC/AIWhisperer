/**
 * Project management service using JSON-RPC over WebSocket
 */

import {
  Project,
  ProjectCreate,
  ProjectJoin,
  ProjectCreateNew,
  ProjectTemplate,
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

  async closeWorkspace(): Promise<void> {
    try {
      await this.ensureJsonRpc().sendRequest('project.close', {});
    } catch (error: any) {
      throw new Error(error.message || 'Failed to close workspace');
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

  async joinProject(data: ProjectJoin): Promise<ProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.join', data);
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to join project');
    }
  }

  async createNewProject(data: ProjectCreateNew): Promise<ProjectResponse> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.create_new', data);
      return result;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create new project');
    }
  }

  async getProjectTemplates(): Promise<ProjectTemplate[]> {
    try {
      const result = await this.ensureJsonRpc().sendRequest('project.templates', {});
      return result.templates;
    } catch (error: any) {
      throw new Error(error.message || 'Failed to get project templates');
    }
  }

  async checkForExistingWhisper(path: string): Promise<{ hasWhisper: boolean; projectName?: string }> {
    try {
      // Use workspace.listDirectory to check if .WHISPER exists
      const result = await this.ensureJsonRpc().sendRequest('workspace.listDirectory', {
        path: path,
        show_hidden: true
      });
      
      const files = result.files || [];
      const whisperFolder = files.find((file: any) => file.name === '.WHISPER' && file.type === 'directory');
      
      if (whisperFolder) {
        // Try to read project.json to get the project name
        try {
          const projectJsonResult = await this.ensureJsonRpc().sendRequest('workspace.getFileContent', {
            path: `${path}/.WHISPER/project.json`
          });
          
          const projectData = JSON.parse(projectJsonResult.content);
          return { hasWhisper: true, projectName: projectData.name };
        } catch {
          // If we can't read project.json, just return that whisper exists
          return { hasWhisper: true };
        }
      }
      
      return { hasWhisper: false };
    } catch (error: any) {
      // If we can't check the directory, assume no whisper folder
      console.warn('Failed to check for existing .WHISPER folder:', error);
      return { hasWhisper: false };
    }
  }
}

const projectService = new ProjectService();
export default projectService;