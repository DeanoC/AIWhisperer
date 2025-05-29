"""Project management service for handling AIWhisperer projects."""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from contextlib import contextmanager

from ..models.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectSummary,
    ProjectHistory, UISettings, ProjectSettings
)


logger = logging.getLogger(__name__)


class ProjectManager:
    """Manages AIWhisperer projects and their associated data."""
    
    def __init__(self, data_dir: Path):
        """Initialize project manager with data directory."""
        self.data_dir = Path(data_dir)
        self.projects_file = self.data_dir / "projects.json"
        self.history_file = self.data_dir / "project_history.json"
        self.ui_settings_file = self.data_dir / "ui_settings.json"
        self.active_project: Optional[Project] = None
        
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing data
        self._load_projects()
        self._load_history()
        self._load_ui_settings()
    
    def _load_projects(self) -> Dict[str, Project]:
        """Load projects from disk."""
        if not self.projects_file.exists():
            self.projects = {}
            return self.projects
            
        try:
            with open(self.projects_file, 'r') as f:
                data = json.load(f)
                self.projects = {
                    pid: Project(**pdata) for pid, pdata in data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
            self.projects = {}
        
        return self.projects
    
    def _save_projects(self):
        """Save projects to disk."""
        try:
            data = {
                pid: proj.dict() for pid, proj in self.projects.items()
            }
            with open(self.projects_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save projects: {e}")
    
    def _load_history(self) -> ProjectHistory:
        """Load project history from disk."""
        if not self.history_file.exists():
            self.history = ProjectHistory()
            return self.history
            
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.history = ProjectHistory(**data)
        except Exception as e:
            logger.error(f"Failed to load project history: {e}")
            self.history = ProjectHistory()
        
        return self.history
    
    def _save_history(self):
        """Save project history to disk."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save project history: {e}")
    
    def _load_ui_settings(self) -> UISettings:
        """Load UI settings from disk."""
        if not self.ui_settings_file.exists():
            self.ui_settings = UISettings()
            return self.ui_settings
            
        try:
            with open(self.ui_settings_file, 'r') as f:
                data = json.load(f)
                self.ui_settings = UISettings(**data)
        except Exception as e:
            logger.error(f"Failed to load UI settings: {e}")
            self.ui_settings = UISettings()
        
        return self.ui_settings
    
    def _save_ui_settings(self):
        """Save UI settings to disk."""
        try:
            with open(self.ui_settings_file, 'w') as f:
                json.dump(self.ui_settings.dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save UI settings: {e}")
    
    def _create_whisper_structure(self, project_path: Path) -> Path:
        """Create .WHISPER directory structure for a project."""
        whisper_path = project_path / ".WHISPER"
        
        # Create directory structure
        directories = [
            whisper_path,
            whisper_path / "plans" / "initial",
            whisper_path / "plans" / "refined",
            whisper_path / "sessions",
            whisper_path / "agents" / "alice",
            whisper_path / "agents" / "patricia",
            whisper_path / "agents" / "tessa",
            whisper_path / "artifacts"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        return whisper_path
    
    def _update_recent_projects(self, project: Project):
        """Update recent projects list."""
        # Remove if already in list
        self.history.recent_projects = [
            p for p in self.history.recent_projects 
            if p.id != project.id
        ]
        
        # Add to front
        summary = ProjectSummary(
            id=project.id,
            name=project.name,
            path=project.path,
            last_accessed_at=project.last_accessed_at
        )
        self.history.recent_projects.insert(0, summary)
        
        # Trim to max size
        if len(self.history.recent_projects) > self.history.max_recent_projects:
            self.history.recent_projects = self.history.recent_projects[:self.history.max_recent_projects]
        
        self._save_history()
    
    def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        project_path = Path(project_data.path)
        
        # Validate path
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")
        
        # Check if .WHISPER already exists
        whisper_path = project_path / ".WHISPER"
        if whisper_path.exists():
            raise ValueError(f"Project already exists at {project_path}")
        
        # Create .WHISPER structure
        whisper_path = self._create_whisper_structure(project_path)
        
        # Create project
        project = Project(
            name=project_data.name,
            path=str(project_path),
            whisper_path=str(whisper_path),
            description=project_data.description
        )
        
        # Save project metadata
        project_file = whisper_path / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project.dict(), f, indent=2, default=str)
        
        # Add to projects
        self.projects[project.id] = project
        self._save_projects()
        
        # Update recent projects
        self._update_recent_projects(project)
        
        logger.info(f"Created project: {project.name} at {project.path}")
        
        return project
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[Project]:
        """List all projects."""
        return list(self.projects.values())
    
    def get_recent_projects(self) -> List[ProjectSummary]:
        """Get recent projects."""
        # Update list to remove any deleted projects
        valid_summaries = []
        for summary in self.history.recent_projects:
            if summary.id in self.projects:
                valid_summaries.append(summary)
        
        self.history.recent_projects = valid_summaries
        return valid_summaries
    
    def update_project(self, project_id: str, update_data: ProjectUpdate) -> Optional[Project]:
        """Update a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update fields
        if update_data.name is not None:
            project.name = update_data.name
        
        if update_data.description is not None:
            project.description = update_data.description
        
        if update_data.settings is not None:
            project.settings = update_data.settings
        
        # Save changes
        self._save_projects()
        
        # Update project.json in .WHISPER
        project_file = Path(project.whisper_path) / "project.json"
        with open(project_file, 'w') as f:
            json.dump(project.dict(), f, indent=2, default=str)
        
        logger.info(f"Updated project: {project.name}")
        
        return project
    
    def delete_project(self, project_id: str, delete_files: bool = False) -> bool:
        """Delete a project."""
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Delete .WHISPER folder if requested
        if delete_files:
            whisper_path = Path(project.whisper_path)
            if whisper_path.exists():
                shutil.rmtree(whisper_path)
                logger.info(f"Deleted .WHISPER folder: {whisper_path}")
        
        # Remove from projects
        del self.projects[project_id]
        self._save_projects()
        
        # Remove from recent projects
        self.history.recent_projects = [
            p for p in self.history.recent_projects 
            if p.id != project_id
        ]
        
        # Clear last active if it was this project
        if self.history.last_active_project_id == project_id:
            self.history.last_active_project_id = None
        
        self._save_history()
        
        # Clear active project if it was this one
        if self.active_project and self.active_project.id == project_id:
            self.active_project = None
        
        logger.info(f"Deleted project: {project.name}")
        
        return True
    
    def activate_project(self, project_id: str) -> Optional[Project]:
        """Activate a project."""
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Update last accessed time
        project.last_accessed_at = datetime.utcnow()
        self._save_projects()
        
        # Set as active
        self.active_project = project
        
        # Update history
        self.history.last_active_project_id = project_id
        self._update_recent_projects(project)
        
        logger.info(f"Activated project: {project.name}")
        
        return project
    
    def get_active_project(self) -> Optional[Project]:
        """Get the currently active project."""
        return self.active_project
    
    def get_last_project(self) -> Optional[Project]:
        """Get the last active project."""
        if self.history.last_active_project_id:
            return self.get_project(self.history.last_active_project_id)
        return None
    
    def get_ui_settings(self) -> UISettings:
        """Get UI settings."""
        return self.ui_settings
    
    def update_ui_settings(self, settings: UISettings) -> UISettings:
        """Update UI settings."""
        self.ui_settings = settings
        self._save_ui_settings()
        return self.ui_settings
    
    @contextmanager
    def project_context(self, project_id: str):
        """Context manager for working within a project."""
        previous_project = self.active_project
        
        try:
            # Activate project
            project = self.activate_project(project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            yield project
            
        finally:
            # Restore previous project
            if previous_project:
                self.active_project = previous_project