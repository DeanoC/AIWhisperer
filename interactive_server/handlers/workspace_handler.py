"""JSON-RPC handlers for workspace operations."""
from typing import Dict, Any, Optional
import logging

from interactive_server.services.file_service import FileService
from ai_whisperer.path_management import PathManager
from interactive_server.handlers.project_handlers import get_project_manager

logger = logging.getLogger(__name__)


class WorkspaceHandler:
    """Handler for workspace-related JSON-RPC methods."""
    
    def __init__(self, path_manager: PathManager):
        """Initialize workspace handler.
        
        Args:
            path_manager: PathManager instance for secure path resolution
        """
        self.file_service = FileService(path_manager)
        self.path_manager = path_manager
    
    async def get_tree(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Get directory tree for workspace.
        
        JSON-RPC method: workspace.getTree
        
        Args:
            params: Dict with optional 'path' key
            websocket: WebSocket connection (optional, unused)
            
        Returns:
            Dict with 'tree' key containing ASCII tree
        """
        # Check if there's an active project
        try:
            project_manager = get_project_manager()
            if not project_manager.get_active_project():
                return {
                    "tree": "",
                    "path": "",
                    "type": "ascii",
                    "error": "No active workspace. Please open a project first."
                }
        except Exception as e:
            logger.error(f"Error checking active project: {e}")
            return {
                "tree": "",
                "path": "",
                "type": "ascii",
                "error": "Unable to access project manager."
            }
            
        path = params.get("path", ".")
        
        try:
            tree = await self.file_service.get_tree_ascii(path)
            return {
                "tree": tree,
                "path": path,
                "type": "ascii"
            }
        except ValueError as e:
            logger.error(f"Invalid path requested: {e}")
            raise ValueError(f"Invalid path: {path}")
        except Exception as e:
            logger.error(f"Error getting tree for path {path}: {e}")
            raise RuntimeError(f"Failed to get directory tree: {str(e)}")
    
    async def list_directory(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """List files in a directory.
        
        JSON-RPC method: workspace.listDirectory
        
        Args:
            params: Dict with 'path' and optional 'recursive' keys
            websocket: WebSocket connection (optional, unused)
            
        Returns:
            Dict with 'files' list
        """
        # Check if there's an active project
        try:
            project_manager = get_project_manager()
            if not project_manager.get_active_project():
                raise RuntimeError("No active workspace. Please open a project first.")
        except Exception as e:
            logger.error(f"Error checking active project: {e}")
            raise RuntimeError("Unable to access project manager.")
            
        path = params.get("path", ".")
        recursive = params.get("recursive", False)
        
        try:
            files = await self.file_service.list_directory(path, recursive)
            return {
                "files": files,
                "path": path,
                "count": len(files)
            }
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise RuntimeError(f"Failed to list directory: {str(e)}")
    
    async def search_files(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Search for files in workspace.
        
        JSON-RPC method: workspace.searchFiles
        
        Args:
            params: Dict with 'query' and optional 'fileTypes' keys
            websocket: WebSocket connection (optional, unused)
            
        Returns:
            Dict with 'results' list
        """
        # Check if there's an active project
        try:
            project_manager = get_project_manager()
            if not project_manager.get_active_project():
                raise RuntimeError("No active workspace. Please open a project first.")
        except Exception as e:
            logger.error(f"Error checking active project: {e}")
            raise RuntimeError("Unable to access project manager.")
            
        query = params.get("query", "")
        file_types = params.get("fileTypes", None)
        
        if not query:
            return {"results": [], "query": query}
        
        try:
            results = await self.file_service.search_files(query, file_types)
            return {
                "results": results,
                "query": query,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error searching files with query '{query}': {e}")
            raise RuntimeError(f"Failed to search files: {str(e)}")
    
    async def get_file_content(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Get file content with optional line range.
        
        JSON-RPC method: workspace.getFileContent
        
        Args:
            params: Dict with 'path' and optional 'startLine', 'endLine' keys
            
        Returns:
            Dict with file content and metadata
        """
        # Check if there's an active project
        try:
            project_manager = get_project_manager()
            if not project_manager.get_active_project():
                raise RuntimeError("No active workspace. Please open a project first.")
        except Exception as e:
            logger.error(f"Error checking active project: {e}")
            raise RuntimeError("Unable to access project manager.")
            
        path = params.get("path")
        if not path:
            raise ValueError("File path is required")
            
        start_line = params.get("startLine")
        end_line = params.get("endLine")
        
        try:
            result = await self.file_service.get_file_content(path, start_line, end_line)
            return result
        except ValueError as e:
            logger.error(f"Invalid file request: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            raise RuntimeError(f"Failed to read file: {str(e)}")
    
    def get_methods(self) -> Dict[str, Any]:
        """Get all methods provided by this handler.
        
        Returns:
            Dict mapping method names to handler functions
        """
        return {
            "workspace.getTree": self.get_tree,
            "workspace.listDirectory": self.list_directory,
            "workspace.searchFiles": self.search_files,
            "workspace.getFileContent": self.get_file_content,
        }