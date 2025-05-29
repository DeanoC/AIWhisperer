"""File service for workspace operations."""
from typing import Dict, List, Optional, Any
import os
from pathlib import Path

from ai_whisperer.utils import build_ascii_directory_tree
from ai_whisperer.path_management import PathManager


class FileService:
    """Service for file system operations within workspace boundaries."""
    
    def __init__(self, path_manager: PathManager):
        """Initialize file service with path manager.
        
        Args:
            path_manager: PathManager instance for secure path resolution
        """
        self.path_manager = path_manager
    
    async def get_tree_ascii(self, path: str = ".", max_depth: Optional[int] = None) -> str:
        """Get ASCII representation of directory tree.
        
        Args:
            path: Relative path from workspace root
            max_depth: Maximum depth to traverse (not yet implemented)
            
        Returns:
            ASCII tree string
            
        Raises:
            ValueError: If path is outside workspace
        """
        # Resolve path safely through PathManager
        resolved_path = self.path_manager.resolve_path(path)
        
        # Use existing utility function
        tree = build_ascii_directory_tree(
            start_path=str(resolved_path),
            ignore=[".git", "__pycache__", "node_modules", ".pytest_cache", "*.pyc"]
        )
        
        return tree
    
    async def list_directory(self, path: str = ".", recursive: bool = False) -> List[Dict[str, Any]]:
        """List files and directories in given path.
        
        Args:
            path: Relative path from workspace root
            recursive: Whether to list recursively
            
        Returns:
            List of file/directory information dicts
        """
        # TODO: Implement structured directory listing
        # For now, return empty list as placeholder
        return []
    
    async def search_files(self, query: str, file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search for files by name pattern.
        
        Args:
            query: Search query (supports wildcards)
            file_types: List of file extensions to filter (e.g., [".py", ".js"])
            
        Returns:
            List of matching files with paths
        """
        # TODO: Implement file search
        # For now, return empty list as placeholder
        return []
    
    async def get_file_content(self, path: str, start_line: Optional[int] = None, 
                               end_line: Optional[int] = None) -> Dict[str, Any]:
        """Get file content with optional line range.
        
        Args:
            path: Relative path to file
            start_line: Starting line number (1-indexed)
            end_line: Ending line number (inclusive)
            
        Returns:
            Dict with content, total_lines, and metadata
        """
        try:
            resolved_path = self.path_manager.resolve_path(path)
            
            # Check if file exists and is a file
            if not resolved_path.exists():
                raise ValueError(f"File not found: {path}")
            if not resolved_path.is_file():
                raise ValueError(f"Not a file: {path}")
            
            # Get file metadata
            stat = resolved_path.stat()
            file_size = stat.st_size
            
            # Check if it's likely a text file
            text_extensions = {'.py', '.js', '.ts', '.tsx', '.json', '.md', '.txt', '.yaml', '.yml', 
                             '.css', '.html', '.xml', '.sh', '.bat', '.ps1', '.java', '.cpp', '.c', 
                             '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.swift', '.kt', '.toml', '.ini',
                             '.cfg', '.conf', '.log', '.csv', '.sql', '.r', '.R', '.m', '.lua'}
            
            is_text = resolved_path.suffix.lower() in text_extensions or file_size == 0
            
            # Check for common binary file signatures if no extension
            if not resolved_path.suffix and file_size > 0:
                with open(resolved_path, 'rb') as f:
                    header = f.read(min(8, file_size))
                    # Common binary file signatures
                    binary_signatures = [
                        b'\x7fELF',      # ELF
                        b'MZ',           # DOS/Windows executable
                        b'\x89PNG',      # PNG
                        b'\xff\xd8\xff', # JPEG
                        b'GIF8',         # GIF
                        b'PK',           # ZIP
                        b'\x50\x4b\x03\x04', # ZIP
                    ]
                    is_text = not any(header.startswith(sig) for sig in binary_signatures)
            
            if not is_text:
                return {
                    "path": path,
                    "content": None,
                    "is_binary": True,
                    "size": file_size,
                    "error": "Binary file - content preview not available"
                }
            
            # Read text file
            try:
                with open(resolved_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines = len(lines)
                    
                    # Apply line range if specified
                    if start_line is not None:
                        start_idx = max(0, start_line - 1)  # Convert to 0-indexed
                    else:
                        start_idx = 0
                        
                    if end_line is not None:
                        end_idx = min(total_lines, end_line)  # end_line is inclusive
                    else:
                        end_idx = min(total_lines, start_idx + 100)  # Default to 100 lines
                    
                    selected_lines = lines[start_idx:end_idx]
                    content = ''.join(selected_lines)
                    
                    return {
                        "path": path,
                        "content": content.rstrip(),
                        "is_binary": False,
                        "size": file_size,
                        "total_lines": total_lines,
                        "start_line": start_idx + 1,
                        "end_line": min(end_idx, total_lines),
                        "truncated": end_idx < total_lines
                    }
                    
            except UnicodeDecodeError:
                return {
                    "path": path,
                    "content": None,
                    "is_binary": True,
                    "size": file_size,
                    "error": "Unable to decode file as UTF-8 text"
                }
                
        except Exception as e:
            raise RuntimeError(f"Failed to read file: {str(e)}")