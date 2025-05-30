"""Tool for analyzing workspace statistics."""
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from collections import defaultdict
import time
from datetime import datetime, timedelta
import os

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class WorkspaceStatsTool(AITool):
    """Tool for gathering statistics about the workspace."""
    
    def __init__(self, path_manager: PathManager):
        """Initialize the workspace statistics tool.
        
        Args:
            path_manager: PathManager instance for validating and resolving paths
        """
        self.path_manager = path_manager
        
    @property
    def name(self) -> str:
        return "workspace_stats"
        
    @property
    def description(self) -> str:
        return "Analyze workspace statistics including file counts, sizes, and recent changes"
        
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to analyze (default: workspace root)",
                    "default": "."
                },
                "include_hidden": {
                    "type": "boolean",
                    "description": "Include hidden files and directories",
                    "default": False
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum directory depth to analyze",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20
                },
                "recent_days": {
                    "type": "integer", 
                    "description": "Number of days to consider for recent changes",
                    "default": 7,
                    "minimum": 1,
                    "maximum": 365
                },
                "exclude_dirs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Directory names to exclude from analysis",
                    "default": [".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"]
                }
            },
            "required": []
        }
        
    @property
    def tags(self) -> List[str]:
        return ["filesystem", "analysis", "statistics", "workspace_info"]
        
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool."""
        return """Use the workspace_stats tool to analyze workspace structure and statistics.
        
Examples:
- Get overall workspace statistics: (no parameters needed)
- Analyze specific directory: path="src"
- Exclude build directories: exclude_dirs=["build", "dist", "node_modules"]
- Include hidden files: include_hidden=true
- Get recent changes (last 7 days): recent_days=7
- Limit depth of analysis: max_depth=3

The tool provides:
- File and directory counts
- Size analysis by file type
- Largest files list
- Recent modification tracking
- File age distribution
- Directory size breakdown"""
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the workspace statistics analysis.
        
        Returns:
            Dict containing various workspace statistics
        """
        try:
            # Extract parameters
            path = kwargs.get("path", ".")
            include_hidden = kwargs.get("include_hidden", False)
            max_depth = kwargs.get("max_depth", 10)
            recent_days = kwargs.get("recent_days", 7)
            exclude_dirs = set(kwargs.get("exclude_dirs", [".git", "__pycache__", "node_modules", ".venv", "venv", "build", "dist"]))
            
            # Resolve path
            if path == ".":
                # Use workspace path for current directory
                root_path = self.path_manager.workspace_path or Path.cwd()
            else:
                resolved_path = self.path_manager.resolve_path(path)
                root_path = Path(resolved_path)
                # If it's a relative path, make it relative to workspace
                if not root_path.is_absolute():
                    root_path = (self.path_manager.workspace_path or Path.cwd()) / root_path
            
            if not root_path.exists():
                return {"error": f"Path not found: {path}"}
            if not root_path.is_dir():
                return {"error": f"Not a directory: {path}"}
                
            # Initialize statistics
            stats = {
                "total_files": 0,
                "total_directories": 0,
                "total_size": 0,
                "files_by_extension": defaultdict(int),
                "size_by_extension": defaultdict(int),
                "largest_files": [],
                "directory_sizes": {},
                "recent_changes": {
                    "modified_files": [],
                    "created_files": [],
                    "total_modified": 0,
                    "total_created": 0
                },
                "file_age_distribution": {
                    "today": 0,
                    "this_week": 0,
                    "this_month": 0,
                    "this_year": 0,
                    "older": 0
                }
            }
            
            # Calculate time boundaries for recent changes
            now = time.time()
            recent_cutoff = now - (recent_days * 24 * 60 * 60)
            today_cutoff = now - (24 * 60 * 60)
            week_cutoff = now - (7 * 24 * 60 * 60)
            month_cutoff = now - (30 * 24 * 60 * 60)
            year_cutoff = now - (365 * 24 * 60 * 60)
            
            # Collect all files and directories
            all_files = []
            dir_sizes = defaultdict(int)
            
            self._analyze_directory(
                root_path, 
                stats, 
                all_files,
                dir_sizes,
                exclude_dirs,
                include_hidden,
                recent_cutoff,
                today_cutoff,
                week_cutoff,
                month_cutoff,
                year_cutoff,
                current_depth=0,
                max_depth=max_depth
            )
            
            # Sort and limit largest files
            all_files.sort(key=lambda x: x["size"], reverse=True)
            stats["largest_files"] = all_files[:20]  # Top 20 largest files
            
            # Sort and limit recent changes
            stats["recent_changes"]["modified_files"].sort(
                key=lambda x: x["modified_time"], 
                reverse=True
            )
            stats["recent_changes"]["modified_files"] = stats["recent_changes"]["modified_files"][:50]
            
            stats["recent_changes"]["created_files"].sort(
                key=lambda x: x["created_time"],
                reverse=True  
            )
            stats["recent_changes"]["created_files"] = stats["recent_changes"]["created_files"][:50]
            
            # Calculate directory sizes
            sorted_dirs = sorted(
                dir_sizes.items(),
                key=lambda x: x[1],
                reverse=True
            )
            stats["directory_sizes"] = dict(sorted_dirs[:20])  # Top 20 directories
            
            # Convert defaultdicts to regular dicts
            stats["files_by_extension"] = dict(stats["files_by_extension"])
            stats["size_by_extension"] = dict(stats["size_by_extension"])
            
            # Add summary
            stats["summary"] = {
                "path": path,
                "total_items": stats["total_files"] + stats["total_directories"],
                "human_readable_size": self._format_size(stats["total_size"]),
                "average_file_size": self._format_size(
                    stats["total_size"] // stats["total_files"] if stats["total_files"] > 0 else 0
                ),
                "unique_extensions": len(stats["files_by_extension"]),
                "analysis_time": datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in workspace_stats: {e}")
            return {"error": str(e)}
            
    def _analyze_directory(self, directory: Path, stats: Dict, all_files: List,
                          dir_sizes: Dict, exclude_dirs: set, include_hidden: bool,
                          recent_cutoff: float, today_cutoff: float, 
                          week_cutoff: float, month_cutoff: float, year_cutoff: float,
                          current_depth: int, max_depth: int) -> int:
        """Recursively analyze a directory and update statistics.
        
        Returns:
            Total size of the directory
        """
        if current_depth >= max_depth:
            return 0
            
        total_size = 0
        
        try:
            for item in directory.iterdir():
                # Skip hidden files if not included
                if not include_hidden and item.name.startswith('.'):
                    continue
                    
                # Skip excluded directories
                if item.is_dir() and item.name in exclude_dirs:
                    continue
                    
                try:
                    stat = item.stat()
                    
                    if item.is_file():
                        stats["total_files"] += 1
                        file_size = stat.st_size
                        total_size += file_size
                        
                        # Track by extension
                        extension = item.suffix.lower() or '.no_extension'
                        stats["files_by_extension"][extension] += 1
                        stats["size_by_extension"][extension] += file_size
                        
                        # Track file info for largest files
                        try:
                            relative_path = str(item.relative_to(self.path_manager.workspace_path or Path.cwd()))
                        except ValueError:
                            # If item is not relative to workspace, use absolute path
                            relative_path = str(item)
                        file_info = {
                            "path": relative_path,
                            "size": file_size,
                            "human_size": self._format_size(file_size),
                            "modified_time": stat.st_mtime,
                            "extension": extension
                        }
                        all_files.append(file_info)
                        
                        # Track recent changes
                        if stat.st_mtime > recent_cutoff:
                            stats["recent_changes"]["modified_files"].append({
                                "path": relative_path,
                                "modified_time": stat.st_mtime,
                                "modified_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                "size": file_size
                            })
                            stats["recent_changes"]["total_modified"] += 1
                            
                        if hasattr(stat, 'st_birthtime'):  # Creation time (not all systems)
                            if stat.st_birthtime > recent_cutoff:
                                stats["recent_changes"]["created_files"].append({
                                    "path": relative_path,
                                    "created_time": stat.st_birthtime,
                                    "created_date": datetime.fromtimestamp(stat.st_birthtime).isoformat(),
                                    "size": file_size
                                })
                                stats["recent_changes"]["total_created"] += 1
                                
                        # Track file age distribution
                        if stat.st_mtime > today_cutoff:
                            stats["file_age_distribution"]["today"] += 1
                        elif stat.st_mtime > week_cutoff:
                            stats["file_age_distribution"]["this_week"] += 1
                        elif stat.st_mtime > month_cutoff:
                            stats["file_age_distribution"]["this_month"] += 1
                        elif stat.st_mtime > year_cutoff:
                            stats["file_age_distribution"]["this_year"] += 1
                        else:
                            stats["file_age_distribution"]["older"] += 1
                            
                    elif item.is_dir():
                        stats["total_directories"] += 1
                        
                        # Recursively analyze subdirectory
                        subdir_size = self._analyze_directory(
                            item, stats, all_files, dir_sizes, exclude_dirs,
                            include_hidden, recent_cutoff, today_cutoff,
                            week_cutoff, month_cutoff, year_cutoff,
                            current_depth + 1, max_depth
                        )
                        
                        total_size += subdir_size
                        
                        # Track directory size
                        try:
                            relative_dir = str(item.relative_to(self.path_manager.workspace_path or Path.cwd()))
                        except ValueError:
                            # If item is not relative to workspace, use absolute path
                            relative_dir = str(item)
                        dir_sizes[relative_dir] = subdir_size
                        
                except (PermissionError, OSError) as e:
                    logger.debug(f"Cannot access {item}: {e}")
                    
        except (PermissionError, OSError) as e:
            logger.debug(f"Cannot access directory {directory}: {e}")
            
        stats["total_size"] += total_size
        return total_size
        
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"