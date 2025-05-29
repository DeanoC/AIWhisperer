"""JSON-RPC handlers for project management"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from ..services.project_manager import ProjectManager
from ..models.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


def model_to_dict(model) -> dict:
    """Convert a Pydantic model to dict, handling both v1 and v2"""
    if hasattr(model, 'model_dump'):
        return model.model_dump()
    elif hasattr(model, 'dict'):
        return model.dict()
    else:
        return dict(model)

# Global project manager instance
_project_manager: Optional[ProjectManager] = None


def init_project_handlers(data_dir: Path) -> ProjectManager:
    """Initialize the project manager and handlers"""
    global _project_manager
    _project_manager = ProjectManager(data_dir)
    return _project_manager


def get_project_manager() -> ProjectManager:
    """Get the project manager instance"""
    if _project_manager is None:
        raise RuntimeError("Project manager not initialized")
    return _project_manager


async def project_connect_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Connect to an existing workspace"""
    try:
        manager = get_project_manager()
        project_data = ProjectCreate(**params)
        project = manager.create_project(project_data)
        
        return {
            "project": model_to_dict(project),
            "message": f"Connected to workspace '{project.name}' successfully"
        }
    except ValueError as e:
        return {
            "error": {"code": -32602, "message": str(e)}
        }
    except Exception as e:
        logger.error(f"Failed to connect to workspace: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to connect to workspace"}
        }


async def project_list_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """List all projects"""
    try:
        manager = get_project_manager()
        projects = manager.list_projects()
        return {
            "projects": [model_to_dict(p) for p in projects]
        }
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to list projects"}
        }


async def project_recent_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Get recent projects"""
    try:
        manager = get_project_manager()
        recent = manager.get_recent_projects()
        return {
            "projects": [model_to_dict(p) for p in recent]
        }
    except Exception as e:
        logger.error(f"Failed to get recent projects: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to get recent projects"}
        }


async def project_active_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Get the currently active project"""
    try:
        manager = get_project_manager()
        project = manager.get_active_project()
        return {
            "project": model_to_dict(project) if project else None
        }
    except Exception as e:
        logger.error(f"Failed to get active project: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to get active project"}
        }


async def project_get_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Get project details"""
    try:
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {"code": -32602, "message": "Missing project_id parameter"}
            }
        
        manager = get_project_manager()
        project = manager.get_project(project_id)
        
        if not project:
            return {
                "error": {"code": -32001, "message": "Project not found"}
            }
        
        return {
            "project": model_to_dict(project)
        }
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to get project"}
        }


async def project_update_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Update a project"""
    try:
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {"code": -32602, "message": "Missing project_id parameter"}
            }
        
        # Extract update data
        update_data = {k: v for k, v in params.items() if k != "project_id"}
        update = ProjectUpdate(**update_data)
        
        manager = get_project_manager()
        project = manager.update_project(project_id, update)
        
        if not project:
            return {
                "error": {"code": -32001, "message": "Project not found"}
            }
        
        return {
            "project": model_to_dict(project),
            "message": f"Project '{project.name}' updated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to update project"}
        }


async def project_delete_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Delete a project"""
    try:
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {"code": -32602, "message": "Missing project_id parameter"}
            }
        
        delete_files = params.get("delete_files", False)
        
        manager = get_project_manager()
        success = manager.delete_project(project_id, delete_files=delete_files)
        
        if not success:
            return {
                "error": {"code": -32001, "message": "Project not found"}
            }
        
        return {
            "message": "Project deleted successfully",
            "deleted_files": delete_files
        }
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to delete project"}
        }


async def project_activate_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Activate a project"""
    try:
        project_id = params.get("project_id")
        if not project_id:
            return {
                "error": {"code": -32602, "message": "Missing project_id parameter"}
            }
        
        manager = get_project_manager()
        project = manager.activate_project(project_id)
        
        if not project:
            return {
                "error": {"code": -32001, "message": "Project not found"}
            }
        
        # TODO: Update session with project context
        # if websocket:
        #     session = session_manager.get_session_by_websocket(websocket)
        #     if session:
        #         session.project_path = project.path
        
        return {
            "project": model_to_dict(project),
            "message": f"Project '{project.name}' activated"
        }
    except Exception as e:
        logger.error(f"Failed to activate project: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to activate project"}
        }


async def project_settings_get_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Get UI settings"""
    try:
        manager = get_project_manager()
        settings = manager.get_ui_settings()
        return {
            "settings": model_to_dict(settings)
        }
    except Exception as e:
        logger.error(f"Failed to get UI settings: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to get UI settings"}
        }


async def project_settings_update_handler(params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
    """Update UI settings"""
    try:
        manager = get_project_manager()
        settings = manager.update_ui_settings(params)
        return {
            "settings": model_to_dict(settings)
        }
    except Exception as e:
        logger.error(f"Failed to update UI settings: {e}")
        return {
            "error": {"code": -32603, "message": "Failed to update UI settings"}
        }


# Handler registry
PROJECT_HANDLERS = {
    "project.connect": project_connect_handler,
    "project.list": project_list_handler,
    "project.recent": project_recent_handler,
    "project.active": project_active_handler,
    "project.get": project_get_handler,
    "project.update": project_update_handler,
    "project.delete": project_delete_handler,
    "project.activate": project_activate_handler,
    "project.settings.get": project_settings_get_handler,
    "project.settings.update": project_settings_update_handler,
}