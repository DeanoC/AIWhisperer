/**
 * Project management types for AIWhisperer
 */

export interface ProjectSettings {
  defaultAgent?: string;
  autoSave?: boolean;
}

export interface Project {
  id: string;
  name: string;
  path: string;
  whisperPath: string;
  createdAt: string;
  lastAccessedAt: string;
  description?: string;
  settings?: ProjectSettings;
}

export interface ProjectCreate {
  name: string;
  path: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  settings?: ProjectSettings;
}

export interface ProjectSummary {
  id: string;
  name: string;
  path: string;
  lastAccessedAt: string;
}

export interface ProjectHistory {
  recentProjects: ProjectSummary[];
  lastActiveProjectId?: string;
  maxRecentProjects: number;
}

export interface UISettings {
  autoLoadLastProject: boolean;
  showProjectSelector: boolean;
}

export interface ProjectResponse {
  project: Project;
  message: string;
}

export interface DeleteProjectResponse {
  message: string;
  deletedFiles: boolean;
}