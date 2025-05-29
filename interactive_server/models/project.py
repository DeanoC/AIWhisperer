"""Project management models and schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class ProjectSettings(BaseModel):
    """Project-specific settings."""
    default_agent: Optional[str] = Field(None, description="Default agent for the project")
    auto_save: bool = Field(True, description="Auto-save conversations")


class Project(BaseModel):
    """Project model representing an AIWhisperer project."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project ID")
    name: str = Field(..., description="Project display name")
    path: str = Field(..., description="Absolute path to project directory")
    whisper_path: str = Field(..., description="Path to .WHISPER folder")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow, description="Last access timestamp")
    description: Optional[str] = Field(None, description="Project description")
    settings: ProjectSettings = Field(default_factory=ProjectSettings, description="Project settings")


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Project directory path")
    description: Optional[str] = Field(None, description="Project description")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    settings: Optional[ProjectSettings] = Field(None, description="Project settings")


class ProjectSummary(BaseModel):
    """Lightweight project summary for lists."""
    id: str
    name: str
    path: str
    last_accessed_at: datetime


class ProjectHistory(BaseModel):
    """Project history and recent projects."""
    recent_projects: List[ProjectSummary] = Field(default_factory=list)
    last_active_project_id: Optional[str] = None
    max_recent_projects: int = 10


class UISettings(BaseModel):
    """UI-specific settings."""
    auto_load_last_project: bool = Field(True, description="Automatically load last used project")
    show_project_selector: bool = Field(True, description="Show project selector in UI")
    
    
class ProjectResponse(BaseModel):
    """Response model for project operations."""
    project: Project
    message: str = "Success"