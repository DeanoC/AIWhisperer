"""Tool Set management for organizing tools into collections."""
from typing import Dict, List, Set, Optional, Any, Union
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ToolSet:
    """Represents a collection of tools with inheritance support."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize a tool set from configuration.
        
        Args:
            name: The name of the tool set
            config: Configuration dictionary containing:
                - description: Human-readable description
                - inherits: List of parent tool set names
                - tools: List of tool names in this set
                - tags: List of tags to include
                - deny_tags: List of tags to exclude
        """
        self.name = name
        self.description = config.get('description', '')
        self.inherits = config.get('inherits', [])
        self.tools = set(config.get('tools', []))
        self.tags = set(config.get('tags', []))
        self.deny_tags = set(config.get('deny_tags', []))
        
        # Resolved tools will be populated by the manager
        self._resolved_tools: Optional[Set[str]] = None
        self._resolved_tags: Optional[Set[str]] = None
        self._resolved_deny_tags: Optional[Set[str]] = None
    
    def __repr__(self) -> str:
        return f"ToolSet(name='{self.name}', tools={len(self.tools)}, inherits={self.inherits})"


class ToolSetManager:
    """Manages tool sets including loading, inheritance resolution, and lookups."""
    
    def __init__(self, config_path: Optional[Union[Path, str]] = None):
        """Initialize the tool set manager.
        
        Args:
            config_path: Path to tool_sets.yaml file. If None, uses default location.
        """
        self.tool_sets: Dict[str, ToolSet] = {}
        self._inheritance_resolved = False
        
        if config_path is None:
            # Default to tool_sets.yaml in the same directory as this file
            config_path = Path(__file__).parent / 'tool_sets.yaml'
        elif isinstance(config_path, str):
            config_path = Path(config_path)
        
        if config_path.exists():
            self.load_config(config_path)
        else:
            logger.warning(f"Tool sets configuration not found at {config_path}")
    
    def load_config(self, config_path: Path) -> None:
        """Load tool sets from YAML configuration file.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Load base sets
            for name, set_config in config.get('base_sets', {}).items():
                self.tool_sets[name] = ToolSet(name, set_config)
            
            # Load agent sets
            for name, set_config in config.get('agent_sets', {}).items():
                self.tool_sets[name] = ToolSet(name, set_config)
            
            # Load specialized sets
            for name, set_config in config.get('specialized_sets', {}).items():
                self.tool_sets[name] = ToolSet(name, set_config)
            
            logger.info(f"Loaded {len(self.tool_sets)} tool sets from {config_path}")
            
            # Resolve inheritance after loading all sets
            self._resolve_inheritance()
            
        except Exception as e:
            logger.error(f"Failed to load tool sets configuration: {e}")
            raise
    
    def _resolve_inheritance(self) -> None:
        """Resolve inheritance for all tool sets."""
        if self._inheritance_resolved:
            return
        
        # Topological sort to handle inheritance dependencies
        visited = set()
        temp_visited = set()
        sorted_sets = []
        
        def visit(set_name: str) -> None:
            if set_name in temp_visited:
                raise ValueError(f"Circular inheritance detected involving {set_name}")
            if set_name in visited:
                return
            
            temp_visited.add(set_name)
            tool_set = self.tool_sets.get(set_name)
            
            if tool_set:
                for parent in tool_set.inherits:
                    if parent in self.tool_sets:
                        visit(parent)
                    else:
                        logger.warning(f"Tool set '{set_name}' inherits from unknown set '{parent}'")
            
            temp_visited.remove(set_name)
            visited.add(set_name)
            sorted_sets.append(set_name)
        
        # Visit all tool sets
        for set_name in self.tool_sets:
            if set_name not in visited:
                visit(set_name)
        
        # Resolve inheritance in dependency order
        for set_name in sorted_sets:
            tool_set = self.tool_sets[set_name]
            resolved_tools = set(tool_set.tools)
            resolved_tags = set(tool_set.tags)
            resolved_deny_tags = set(tool_set.deny_tags)
            
            # Inherit from parent sets
            for parent_name in tool_set.inherits:
                parent = self.tool_sets.get(parent_name)
                if parent and parent._resolved_tools is not None:
                    resolved_tools.update(parent._resolved_tools)
                    resolved_tags.update(parent._resolved_tags)
                    resolved_deny_tags.update(parent._resolved_deny_tags)
            
            tool_set._resolved_tools = resolved_tools
            tool_set._resolved_tags = resolved_tags
            tool_set._resolved_deny_tags = resolved_deny_tags
        
        self._inheritance_resolved = True
    
    def get_tool_set(self, name: str) -> Optional[ToolSet]:
        """Get a tool set by name.
        
        Args:
            name: Name of the tool set
            
        Returns:
            ToolSet instance or None if not found
        """
        return self.tool_sets.get(name)
    
    def get_tools_for_set(self, name: str) -> Set[str]:
        """Get resolved list of tools for a tool set.
        
        Args:
            name: Name of the tool set
            
        Returns:
            Set of tool names (empty set if not found)
        """
        tool_set = self.get_tool_set(name)
        if tool_set and tool_set._resolved_tools is not None:
            return tool_set._resolved_tools.copy()
        return set()
    
    def get_tags_for_set(self, name: str) -> Set[str]:
        """Get resolved list of tags for a tool set.
        
        Args:
            name: Name of the tool set
            
        Returns:
            Set of tag names (empty set if not found)
        """
        tool_set = self.get_tool_set(name)
        if tool_set and tool_set._resolved_tags is not None:
            return tool_set._resolved_tags.copy()
        return set()
    
    def get_deny_tags_for_set(self, name: str) -> Set[str]:
        """Get resolved list of denied tags for a tool set.
        
        Args:
            name: Name of the tool set
            
        Returns:
            Set of denied tag names (empty set if not found)
        """
        tool_set = self.get_tool_set(name)
        if tool_set and tool_set._resolved_deny_tags is not None:
            return tool_set._resolved_deny_tags.copy()
        return set()
    
    def list_tool_sets(self) -> List[str]:
        """Get list of all available tool set names.
        
        Returns:
            List of tool set names
        """
        return list(self.tool_sets.keys())
    
    def get_tool_set_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool set.
        
        Args:
            name: Name of the tool set
            
        Returns:
            Dictionary with tool set information or None if not found
        """
        tool_set = self.get_tool_set(name)
        if not tool_set:
            return None
        
        return {
            'name': tool_set.name,
            'description': tool_set.description,
            'inherits': tool_set.inherits,
            'direct_tools': list(tool_set.tools),
            'direct_tags': list(tool_set.tags),
            'direct_deny_tags': list(tool_set.deny_tags),
            'resolved_tools': list(tool_set._resolved_tools) if tool_set._resolved_tools else [],
            'resolved_tags': list(tool_set._resolved_tags) if tool_set._resolved_tags else [],
            'resolved_deny_tags': list(tool_set._resolved_deny_tags) if tool_set._resolved_deny_tags else []
        }