"""File service for workspace operations."""
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import time
from threading import Lock
import asyncio
import logging

from ai_whisperer.utils.helpers import build_ascii_directory_tree
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)


class FileService:
    """Service for file system operations within workspace boundaries."""
    
    # Cache configuration
    CACHE_TTL = 30  # Cache time-to-live in seconds
    CACHE_MAX_ENTRIES = 100  # Maximum number of cached directories
    
    # Safety limits to prevent hanging
    MAX_FILES_LIMIT = 1000  # Maximum files to process in recursive listing
    YIELD_INTERVAL = 100  # Yield control to event loop every N files
    
    def __init__(self, path_manager: PathManager):
        """Initialize file service with path manager.
        
        Args:
            path_manager: PathManager instance for secure path resolution
        """
        self.path_manager = path_manager
        
        # Directory listing cache: {path: (nodes, timestamp)}
        self._dir_cache: Dict[str, tuple[List[Dict[str, Any]], float]] = {}
        self._cache_lock = Lock()
        
        # Track access order for LRU eviction
        self._cache_access_order: List[str] = []
    
    def _get_cache_key(self, path: str, recursive: bool, max_depth: int, 
                      include_hidden: bool, file_types: Optional[List[str]]) -> str:
        """Generate a unique cache key for the given parameters."""
        file_types_str = ','.join(sorted(file_types)) if file_types else ''
        return f"{path}|{recursive}|{max_depth}|{include_hidden}|{file_types_str}"
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if a cache entry is still valid."""
        return (time.time() - timestamp) < self.CACHE_TTL
    
    def _update_cache_access(self, key: str) -> None:
        """Update access order for LRU eviction.
        
        NOTE: This method assumes the caller already holds the cache lock.
        """
        if key in self._cache_access_order:
            self._cache_access_order.remove(key)
        self._cache_access_order.append(key)
        
        # Evict oldest entries if cache is too large
        while len(self._dir_cache) > self.CACHE_MAX_ENTRIES:
            oldest_key = self._cache_access_order.pop(0)
            if oldest_key in self._dir_cache:
                del self._dir_cache[oldest_key]
    
    def clear_cache(self, path: Optional[str] = None) -> None:
        """Clear cache entries.
        
        Args:
            path: If provided, only clear entries for this path. Otherwise clear all.
        """
        with self._cache_lock:
            if path:
                # Clear all entries that start with this path
                keys_to_remove = [k for k in self._dir_cache.keys() if k.startswith(path)]
                for key in keys_to_remove:
                    del self._dir_cache[key]
                    if key in self._cache_access_order:
                        self._cache_access_order.remove(key)
            else:
                # Clear everything
                self._dir_cache.clear()
                self._cache_access_order.clear()
    
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
        resolved_path_str = self.path_manager.resolve_path(path)
        
        # Convert to Path and handle relative paths
        resolved_path = Path(resolved_path_str)
        if not resolved_path.is_absolute():
            workspace_path = self.path_manager.workspace_path
            if workspace_path:
                resolved_path = Path(workspace_path) / resolved_path
            else:
                resolved_path = resolved_path.resolve()
        
        # Use existing utility function
        tree = build_ascii_directory_tree(
            start_path=str(resolved_path),
            ignore=[".git", "__pycache__", "node_modules", ".pytest_cache", "*.pyc"]
        )
        
        return tree
    
    async def list_directory(self, path: str = ".", recursive: bool = False, 
                           max_depth: int = 1, include_hidden: bool = False,
                           file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List files and directories in given path with caching support.
        
        Args:
            path: Relative path from workspace root
            recursive: Whether to list recursively
            max_depth: Maximum depth for recursive listing
            include_hidden: Whether to include hidden files (starting with .)
            file_types: List of file extensions to filter (e.g., [".py", ".js"])
            
        Returns:
            List of file/directory information dicts
        """
        # Generate cache key
        cache_key = self._get_cache_key(path, recursive, max_depth, include_hidden, file_types)
        
        # Check cache first
        with self._cache_lock:
            if cache_key in self._dir_cache:
                nodes, timestamp = self._dir_cache[cache_key]
                if self._is_cache_valid(timestamp):
                    self._update_cache_access(cache_key)
                    return nodes.copy()  # Return a copy to prevent external modifications
        
        # Resolve path safely through PathManager
        resolved_path_str = self.path_manager.resolve_path(path)
        
        # Convert to Path and handle relative paths
        resolved_path = Path(resolved_path_str)
        if not resolved_path.is_absolute():
            workspace_path = self.path_manager.workspace_path
            if workspace_path:
                resolved_path = Path(workspace_path) / resolved_path
            else:
                resolved_path = resolved_path.resolve()
        
        # Check if path exists and is a directory
        if not resolved_path.exists():
            raise ValueError(f"Path not found: {path}")
        if not resolved_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        
        nodes = []
        files_processed = 0
        truncated = False
        
        def should_include_file(file_path: Path) -> bool:
            """Check if file should be included based on filters."""
            # Skip hidden files if not requested
            if not include_hidden and file_path.name.startswith('.'):
                return False
            
            # Apply file type filter if specified
            if file_types and file_path.is_file():
                return file_path.suffix.lower() in file_types
            
            return True
        
        def build_node(file_path: Path, base_path: Path) -> Dict[str, Any]:
            """Build a file node dictionary."""
            try:
                stat = file_path.stat()
                relative_path = file_path.relative_to(base_path)
                
                node = {
                    "name": file_path.name,
                    "path": str(relative_path).replace('\\', '/'),
                    "isFile": file_path.is_file(),
                    "lastModified": stat.st_mtime
                }
                
                if file_path.is_file():
                    node["size"] = stat.st_size
                    node["extension"] = file_path.suffix.lower() if file_path.suffix else None
                    
                    # Determine if binary
                    text_extensions = {'.py', '.js', '.ts', '.tsx', '.json', '.md', '.txt', '.yaml', '.yml', 
                                     '.css', '.html', '.xml', '.sh', '.bat', '.ps1', '.java', '.cpp', '.c', 
                                     '.h', '.hpp', '.cs', '.rb', '.go', '.rs', '.swift', '.kt', '.toml', '.ini',
                                     '.cfg', '.conf', '.log', '.csv', '.sql', '.r', '.R', '.m', '.lua', '.bak',
                                     '.backup', '.orig', '.old', '.save', '.tmp', '.temp', '.dist', '.example',
                                     '.sample', '.default', '.tpl', '.template', '.in', '.out', '.lock'}
                    
                    node["isBinary"] = node["extension"] not in text_extensions if node["extension"] else True
                
                return node
            except (OSError, PermissionError):
                # Handle files we can't stat
                return None
        
        async def list_dir_recursive(dir_path: Path, current_depth: int = 0) -> bool:
            """Recursively list directory contents.
            
            Returns:
                bool: True if limit was reached, False otherwise
            """
            nonlocal files_processed, truncated
            
            if current_depth >= max_depth:
                return False
            
            # Check if we've hit the file limit
            if files_processed >= self.MAX_FILES_LIMIT:
                truncated = True
                logger.warning(f"File limit reached ({self.MAX_FILES_LIMIT} files) while listing {dir_path}")
                return True
            
            try:
                # Get all items in directory
                items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                
                for item in items:
                    # Check limit again inside loop
                    if files_processed >= self.MAX_FILES_LIMIT:
                        truncated = True
                        logger.warning(f"File limit reached ({self.MAX_FILES_LIMIT} files) while processing {item}")
                        return True
                    
                    # Skip ignored patterns and common large directories
                    if item.name in ['.git', '__pycache__', '.pytest_cache', 'node_modules', 
                                    '.venv', 'venv', 'env', 'build', 'dist', '.idea', '.vscode',
                                    'coverage', '.nyc_output', 'logs', '.next', '.nuxt']:
                        continue
                    
                    if should_include_file(item):
                        node = build_node(item, self.path_manager.workspace_path or resolved_path)
                        if node:
                            nodes.append(node)
                            files_processed += 1
                            
                            # Yield to event loop periodically
                            if files_processed % self.YIELD_INTERVAL == 0:
                                await asyncio.sleep(0)
                                logger.debug(f"Processed {files_processed} files, yielding control...")
                            
                            # Recurse into directories if requested
                            if recursive and item.is_dir() and current_depth + 1 < max_depth:
                                limit_reached = await list_dir_recursive(item, current_depth + 1)
                                if limit_reached:
                                    return True
                                
            except (OSError, PermissionError) as e:
                # Skip directories we can't read
                logger.debug(f"Skipping unreadable directory {dir_path}: {e}")
                
            return False
        
        # Start listing
        if recursive:
            await list_dir_recursive(resolved_path, 0)
        else:
            try:
                items = sorted(resolved_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
                for item in items:
                    # Check file limit even in non-recursive mode
                    if files_processed >= self.MAX_FILES_LIMIT:
                        truncated = True
                        logger.warning(f"File limit reached ({self.MAX_FILES_LIMIT} files) in non-recursive listing")
                        break
                    
                    # Skip ignored patterns and common large directories
                    if item.name in ['.git', '__pycache__', '.pytest_cache', 'node_modules', 
                                    '.venv', 'venv', 'env', 'build', 'dist', '.idea', '.vscode',
                                    'coverage', '.nyc_output', 'logs', '.next', '.nuxt']:
                        continue
                        
                    if should_include_file(item):
                        node = build_node(item, self.path_manager.workspace_path or resolved_path)
                        if node:
                            nodes.append(node)
                            files_processed += 1
                            
                            # Yield periodically even in non-recursive mode
                            if files_processed % self.YIELD_INTERVAL == 0:
                                await asyncio.sleep(0)
            except (OSError, PermissionError):
                raise RuntimeError(f"Cannot read directory: {path}")
        
        # Log final statistics
        if truncated:
            logger.info(f"Directory listing truncated at {files_processed} files (limit: {self.MAX_FILES_LIMIT})")
        else:
            logger.debug(f"Directory listing completed with {files_processed} files")
        
        # Store in cache with truncation flag
        result_nodes = nodes.copy()
        if truncated:
            # Add a metadata node to indicate truncation
            result_nodes.append({
                "name": "_truncated",
                "path": "_truncated",
                "isFile": False,
                "truncated": True,
                "filesProcessed": files_processed,
                "maxFilesLimit": self.MAX_FILES_LIMIT
            })
        
        with self._cache_lock:
            self._dir_cache[cache_key] = (result_nodes, time.time())
            self._update_cache_access(cache_key)
        
        return result_nodes
    
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
            # First resolve any template strings
            resolved_path_str = self.path_manager.resolve_path(path)
            
            # Convert to Path object
            resolved_path = Path(resolved_path_str)
            
            # If it's a relative path, make it relative to workspace
            if not resolved_path.is_absolute():
                workspace_path = self.path_manager.workspace_path
                if workspace_path:
                    resolved_path = Path(workspace_path) / resolved_path
                else:
                    resolved_path = resolved_path.resolve()
            
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
                             '.cfg', '.conf', '.log', '.csv', '.sql', '.r', '.R', '.m', '.lua', '.bak',
                             '.backup', '.orig', '.old', '.save', '.tmp', '.temp', '.dist', '.example',
                             '.sample', '.default', '.tpl', '.template', '.in', '.out', '.lock'}
            
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
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file within workspace boundaries.
        
        Args:
            path: File path relative to workspace or absolute within workspace
            content: Content to write to the file
            
        Returns:
            Dict with success status and file metadata
            
        Raises:
            ValueError: If path is invalid or outside workspace
            RuntimeError: If file write operation fails
        """
        try:
            # First resolve any template strings
            resolved_path_str = self.path_manager.resolve_path(path)
            
            # Convert to Path object
            resolved_path = Path(resolved_path_str)
            
            # If it's a relative path, make it relative to workspace
            if not resolved_path.is_absolute():
                workspace_path = self.path_manager.workspace_path
                if workspace_path:
                    resolved_path = Path(workspace_path) / resolved_path
                else:
                    resolved_path = resolved_path.resolve()
            
            # Validate that the path is within workspace boundaries
            if not self.path_manager.is_path_within_workspace(str(resolved_path)):
                raise ValueError(f"Path '{path}' is outside the workspace boundaries")
            
            # Ensure parent directory exists
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(resolved_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Get file metadata
            stat = resolved_path.stat()
            
            # Clear any cached directory listing that might include this file
            self._invalidate_cache_for_path(str(resolved_path.parent))
            
            logger.info(f"File written successfully: {resolved_path}")
            
            return {
                "success": True,
                "path": str(resolved_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "message": f"File written successfully to {resolved_path}"
            }
            
        except ValueError as e:
            logger.error(f"Invalid path for write operation: {e}")
            raise
        except PermissionError as e:
            logger.error(f"Permission denied writing to {path}: {e}")
            raise RuntimeError(f"Permission denied: {str(e)}")
        except OSError as e:
            logger.error(f"OS error writing to {path}: {e}")
            raise RuntimeError(f"File system error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error writing to {path}: {e}")
            raise RuntimeError(f"Failed to write file: {str(e)}")

    def _invalidate_cache_for_path(self, dir_path: str):
        """Invalidate cache entries that might be affected by file changes.
        
        Args:
            dir_path: Directory path that was modified
        """
        with self._cache_lock:
            # Remove cache entries for the parent directory and any recursive entries
            keys_to_remove = []
            for cache_key in self._dir_cache.keys():
                if cache_key.startswith(dir_path):
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                if key in self._dir_cache:
                    del self._dir_cache[key]
                if key in self._cache_access_order:
                    self._cache_access_order.remove(key)