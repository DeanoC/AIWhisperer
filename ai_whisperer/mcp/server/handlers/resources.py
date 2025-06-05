"""Resource handler for MCP server."""

import os
import logging
import mimetypes
from typing import Dict, Any, List
from pathlib import Path
import fnmatch

from ....utils.path import PathManager
from ..config import MCPServerConfig, ResourcePermission

logger = logging.getLogger(__name__)


class ResourceHandler:
    """Handles MCP resource-related requests."""
    
    def __init__(self, path_manager: PathManager, config: MCPServerConfig):
        self.path_manager = path_manager
        self.config = config
        self.permissions = config.resource_permissions
        
    async def list_resources(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List available resources."""
        resources = []
        
        # Get workspace path
        workspace_path = self.path_manager.workspace_path
        
        # Walk through workspace files
        for root, dirs, files in os.walk(workspace_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # Skip hidden files
                if file.startswith('.'):
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, workspace_path)
                
                # Check if file matches any permission pattern
                if self._has_permission(rel_path, "read"):
                    resources.append({
                        "uri": f"file:///{rel_path}",
                        "name": rel_path,
                        "mimeType": self._get_mime_type(file),
                    })
                    
        return resources
        
    async def read_resource(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Read a resource."""
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing required field: uri")
            
        # Parse URI
        file_path = self._parse_uri(uri)
        
        # Check permissions
        if not self._has_permission(file_path, "read"):
            raise PermissionError(f"Access denied to resource: {uri}")
            
        # Resolve full path
        full_path = self.path_manager.resolve_path(file_path)
        
        # Check if file exists
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Resource not found: {uri}")
            
        # Read file content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            return [{
                "uri": uri,
                "mimeType": self._get_mime_type(file_path),
                "text": content,
            }]
            
        except UnicodeDecodeError:
            # Binary file - return base64 encoded
            import base64
            with open(full_path, 'rb') as f:
                content = f.read()
                
            return [{
                "uri": uri,
                "mimeType": self._get_mime_type(file_path),
                "blob": base64.b64encode(content).decode('ascii'),
            }]
            
    async def write_resource(self, params: Dict[str, Any]) -> None:
        """Write a resource."""
        uri = params.get("uri")
        if not uri:
            raise ValueError("Missing required field: uri")
            
        contents = params.get("contents")
        if not contents or not isinstance(contents, list):
            raise ValueError("Missing or invalid field: contents")
            
        # Parse URI
        file_path = self._parse_uri(uri)
        
        # Check permissions
        if not self._has_permission(file_path, "write"):
            raise PermissionError(f"Write access denied to resource: {uri}")
            
        # Get content
        if not contents:
            raise ValueError("No content provided")
            
        content_item = contents[0]
        
        # Resolve full path
        full_path = self.path_manager.resolve_path(file_path)
        
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write content
        if "text" in content_item:
            # Text content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content_item["text"])
                
        elif "blob" in content_item:
            # Binary content
            import base64
            content = base64.b64decode(content_item["blob"])
            with open(full_path, 'wb') as f:
                f.write(content)
                
        else:
            raise ValueError("Content must have either 'text' or 'blob' field")
            
        logger.info(f"Wrote resource: {uri}")
        
    def _parse_uri(self, uri: str) -> str:
        """Parse file URI to get path."""
        if uri.startswith("file:///"):
            return uri[8:]  # Remove file:///
        elif uri.startswith("file://"):
            return uri[7:]  # Remove file://
        else:
            raise ValueError(f"Invalid resource URI: {uri}")
            
    def _get_mime_type(self, file_path: str) -> str:
        """Get MIME type for file."""
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or "application/octet-stream"
        
    def _has_permission(self, file_path: str, operation: str) -> bool:
        """Check if operation is allowed on file path."""
        # Convert to Path for consistent handling
        path = Path(file_path)
        path_str = str(path)
        
        # Check each permission rule
        for perm in self.permissions:
            # Handle ** glob pattern specially
            pattern = perm.pattern
            if "**" in pattern:
                # Convert ** to match any path depth
                # e.g., "output/**/*" should match "output/data.bin" and "output/sub/data.bin"
                if pattern.startswith("**/"):
                    # Pattern like "**/*.py" - match anywhere
                    suffix_pattern = pattern[3:]  # Remove "*/"
                    if fnmatch.fnmatch(path_str, suffix_pattern) or fnmatch.fnmatch(path.name, suffix_pattern):
                        if operation in perm.operations:
                            return True
                elif "/**/" in pattern:
                    # Pattern like "output/**/*.py"
                    parts = pattern.split("/**/")
                    prefix = parts[0]
                    suffix = parts[1]
                    if path_str.startswith(prefix + "/"):
                        # Check if the remaining path matches the suffix
                        remaining = path_str[len(prefix)+1:]
                        if fnmatch.fnmatch(remaining, suffix):
                            if operation in perm.operations:
                                return True
                elif pattern.endswith("/**/*"):
                    # Pattern like "output/**/*" - match everything under output
                    prefix = pattern[:-5]  # Remove "/**/*"
                    if path_str == prefix or path_str.startswith(prefix + "/"):
                        if operation in perm.operations:
                            return True
                elif pattern.endswith("/**"):
                    # Pattern like "output/**"
                    prefix = pattern[:-3]  # Remove "/**"
                    if path_str == prefix or path_str.startswith(prefix + "/"):
                        if operation in perm.operations:
                            return True
            else:
                # Regular fnmatch for patterns without **
                if fnmatch.fnmatch(path_str, pattern):
                    if operation in perm.operations:
                        return True
                    
        # Default deny
        return False