"""Project management models and schemas."""

from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class ProjectSettings(BaseModel):
    """Project-specific settings."""
    default_agent: Optional[str] = Field(None, description="Default agent for the project")
    auto_save: bool = Field(True, description="Auto-save conversations")
    external_agent_type: Optional[str] = Field(None, description="External agent type")


class Project(BaseModel):
    """Project model representing an AIWhisperer project."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique project ID")
    name: str = Field(..., description="Project display name")
    path: str = Field(..., description="Absolute path to project directory")
    whisper_path: str = Field(..., description="Path to .WHISPER folder")
    output_path: Optional[str] = Field(None, description="Output path for generated files (defaults to project path)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last access timestamp")
    description: Optional[str] = Field(None, description="Project description")
    settings: ProjectSettings = Field(default_factory=ProjectSettings, description="Project settings")


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Project directory path")
    output_path: Optional[str] = Field(None, description="Output path for generated files")
    description: Optional[str] = Field(None, description="Project description")
    custom_whisper_path: Optional[str] = Field(None, description="Custom .WHISPER folder location (outside project)")


class ProjectJoin(BaseModel):
    """Schema for joining an existing project with .WHISPER folder."""
    path: str = Field(..., description="Path to directory containing .WHISPER folder")


class ProjectCreateNew(BaseModel):
    """Schema for creating a brand new project with directory structure."""
    name: str = Field(..., description="Project name")
    path: str = Field(..., description="Directory path where project will be created")
    template: str = Field("basic", description="Project template to use")
    description: Optional[str] = Field(None, description="Project description")
    git_init: bool = Field(False, description="Initialize Git repository")
    custom_whisper_path: Optional[str] = Field(None, description="Custom .WHISPER folder location (outside project)")
    workspace_path: Optional[str] = Field(None, description="Existing workspace path (use instead of creating new project folder)")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, description="Project name")
    output_path: Optional[str] = Field(None, description="Output path for generated files")
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