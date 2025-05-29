"""Project management API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import logging
from pathlib import Path

from ..models.project import (
    Project, ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectSummary, UISettings
)
from ..services.project_manager import ProjectManager


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Dependency to get project manager
_project_manager: Optional[ProjectManager] = None


def get_project_manager() -> ProjectManager:
    """Get the project manager instance."""
    if _project_manager is None:
        raise HTTPException(status_code=500, detail="Project manager not initialized")
    return _project_manager


def init_project_manager(data_dir: Path):
    """Initialize the project manager."""
    global _project_manager
    _project_manager = ProjectManager(data_dir)
    return _project_manager


@router.post("/connect", response_model=ProjectResponse)
async def connect_workspace(
    project_data: ProjectCreate,
    manager: ProjectManager = Depends(get_project_manager)
) -> ProjectResponse:
    """Connect AIWhisperer to an existing code workspace."""
    try:
        project = manager.create_project(project_data)
        return ProjectResponse(
            project=project,
            message=f"Connected to workspace '{project.name}' successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to connect to workspace: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect to workspace")


@router.get("/", response_model=List[Project])
async def list_projects(
    manager: ProjectManager = Depends(get_project_manager)
) -> List[Project]:
    """List all projects."""
    return manager.list_projects()


@router.get("/recent", response_model=List[ProjectSummary])
async def get_recent_projects(
    manager: ProjectManager = Depends(get_project_manager)
) -> List[ProjectSummary]:
    """Get recent projects."""
    return manager.get_recent_projects()


@router.get("/active", response_model=Optional[Project])
async def get_active_project(
    manager: ProjectManager = Depends(get_project_manager)
) -> Optional[Project]:
    """Get the currently active project."""
    return manager.get_active_project()


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    manager: ProjectManager = Depends(get_project_manager)
) -> Project:
    """Get project details."""
    project = manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    manager: ProjectManager = Depends(get_project_manager)
) -> ProjectResponse:
    """Update a project."""
    project = manager.update_project(project_id, update_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        project=project,
        message=f"Project '{project.name}' updated successfully"
    )


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    delete_files: bool = False,
    manager: ProjectManager = Depends(get_project_manager)
):
    """Delete a project."""
    success = manager.delete_project(project_id, delete_files=delete_files)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "message": "Project deleted successfully",
        "deleted_files": delete_files
    }


@router.post("/{project_id}/activate", response_model=ProjectResponse)
async def activate_project(
    project_id: str,
    manager: ProjectManager = Depends(get_project_manager)
) -> ProjectResponse:
    """Activate a project."""
    project = manager.activate_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ProjectResponse(
        project=project,
        message=f"Project '{project.name}' activated"
    )


# Settings endpoints
@router.get("/settings/ui", response_model=UISettings)
async def get_ui_settings(
    manager: ProjectManager = Depends(get_project_manager)
) -> UISettings:
    """Get UI settings."""
    return manager.get_ui_settings()


@router.put("/settings/ui", response_model=UISettings)
async def update_ui_settings(
    settings: UISettings,
    manager: ProjectManager = Depends(get_project_manager)
) -> UISettings:
    """Update UI settings."""
    return manager.update_ui_settings(settings)