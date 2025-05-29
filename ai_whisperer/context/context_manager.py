"""Context manager for tracking agent context items."""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

from ai_whisperer.context.context_item import ContextItem
from ai_whisperer.path_management import PathManager

logger = logging.getLogger(__name__)


class AgentContextManager:
    """Manages context items for agents in a session.
    
    This tracks what files and content each agent is aware of,
    manages freshness, and provides context history.
    """
    
    def __init__(self, session_id: str, path_manager: PathManager):
        """Initialize context manager.
        
        Args:
            session_id: Session identifier
            path_manager: PathManager for file operations
        """
        self.session_id = session_id
        self.path_manager = path_manager
        self.contexts: Dict[str, List[ContextItem]] = {}
        self.max_context_size = 50000  # characters
        self.max_context_age = timedelta(hours=24)
    
    def add_file_reference(
        self, 
        agent_id: str, 
        file_path: str, 
        line_range: Optional[Tuple[int, int]] = None
    ) -> ContextItem:
        """Add a file reference to agent context.
        
        Args:
            agent_id: Agent identifier
            file_path: Path to the file
            line_range: Optional (start, end) line numbers
            
        Returns:
            Created ContextItem
        """
        # Ensure agent context exists
        if agent_id not in self.contexts:
            self.contexts[agent_id] = []
        
        try:
            # Resolve file path
            resolved_path = self.path_manager.resolve_path(file_path)
            file_path_obj = Path(resolved_path)
            
            # Validate file exists and is within workspace
            if not file_path_obj.exists():
                raise ValueError(f"File not found: {file_path}")
            
            if not self.path_manager.is_path_within_workspace(str(file_path_obj)):
                raise ValueError(f"File is outside workspace: {file_path}")
            
            # Get file stats
            stat = file_path_obj.stat()
            file_size = stat.st_size
            file_mtime = datetime.fromtimestamp(stat.st_mtime)
            
            # Read file content
            try:
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_lines = len(lines)
                    
                    # Apply line range if specified
                    if line_range:
                        start_line, end_line = line_range
                        # Validate line numbers
                        if start_line < 1 or start_line > total_lines:
                            raise ValueError(f"Invalid start line: {start_line}")
                        if end_line < start_line:
                            raise ValueError(f"End line must be >= start line")
                        
                        # Extract lines (convert to 0-based)
                        selected_lines = lines[start_line-1:end_line]
                        content = ''.join(selected_lines)
                    else:
                        content = ''.join(lines)
                        
            except UnicodeDecodeError:
                raise ValueError(f"Cannot read binary file: {file_path}")
            
            # Detect language from extension
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.cpp': 'cpp',
                '.c': 'c',
                '.cs': 'csharp',
                '.rb': 'ruby',
                '.go': 'go',
                '.rs': 'rust',
                '.php': 'php',
                '.swift': 'swift',
                '.kt': 'kotlin',
                '.md': 'markdown',
                '.json': 'json',
                '.yaml': 'yaml',
                '.yml': 'yaml',
                '.xml': 'xml',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
                '.ps1': 'powershell'
            }
            
            language = language_map.get(file_path_obj.suffix.lower(), 'text')
            
            # Create context item
            item = ContextItem(
                session_id=self.session_id,
                agent_id=agent_id,
                type="file_section" if line_range else "file",
                path=file_path,
                content=content,
                line_range=line_range,
                file_modified_time=file_mtime,
                metadata={
                    "size": file_size,
                    "lines": total_lines,
                    "language": language
                }
            )
            
            # Calculate content hash
            item.content_hash = item.calculate_hash()
            
            # Add to context
            self.contexts[agent_id].append(item)
            
            # Clean up old items if needed
            self._cleanup_old_items(agent_id)
            
            logger.info(f"Added {item.type} to agent {agent_id} context: {file_path}")
            
            return item
            
        except Exception as e:
            logger.error(f"Failed to add file reference: {e}")
            raise
    
    def parse_file_references(self, message: str) -> List[Tuple[str, Optional[Tuple[int, int]]]]:
        """Parse @ file references from a message.
        
        Args:
            message: User message potentially containing @file references
            
        Returns:
            List of (file_path, line_range) tuples
        """
        references = []
        
        # Pattern to match @filepath or @filepath:start-end
        pattern = r'@([^\s:]+)(?::(\d+)-(\d+))?'
        
        for match in re.finditer(pattern, message):
            file_path = match.group(1)
            
            # Parse line range if present
            line_range = None
            if match.group(2) and match.group(3):
                start = int(match.group(2))
                end = int(match.group(3))
                line_range = (start, end)
            
            references.append((file_path, line_range))
        
        return references
    
    def process_message_references(self, agent_id: str, message: str) -> List[ContextItem]:
        """Process @ references in a message and add to context.
        
        Args:
            agent_id: Agent identifier
            message: User message with potential @ references
            
        Returns:
            List of created ContextItems
        """
        references = self.parse_file_references(message)
        items = []
        
        for file_path, line_range in references:
            try:
                item = self.add_file_reference(agent_id, file_path, line_range)
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to add reference {file_path}: {e}")
        
        return items
    
    def get_agent_context(self, agent_id: str) -> List[ContextItem]:
        """Get all context items for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of context items
        """
        return self.contexts.get(agent_id, [])
    
    def refresh_stale_items(self, agent_id: str) -> List[ContextItem]:
        """Refresh any stale context items.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of refreshed items
        """
        if agent_id not in self.contexts:
            return []
        
        refreshed = []
        
        for item in self.contexts[agent_id]:
            if item.type in ["file", "file_section"]:
                try:
                    # Check current file modification time
                    file_path = Path(self.path_manager.resolve_path(item.path))
                    if file_path.exists():
                        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        
                        if item.is_stale(current_mtime):
                            # Refresh the item
                            new_item = self.add_file_reference(
                                agent_id, 
                                item.path, 
                                item.line_range
                            )
                            
                            # Replace old item
                            self.contexts[agent_id].remove(item)
                            refreshed.append(new_item)
                            
                            logger.info(f"Refreshed stale item: {item.path}")
                            
                except Exception as e:
                    logger.error(f"Error refreshing item {item.path}: {e}")
        
        return refreshed
    
    def remove_item(self, agent_id: str, item_id: str) -> bool:
        """Remove a context item.
        
        Args:
            agent_id: Agent identifier
            item_id: Context item ID
            
        Returns:
            True if removed, False if not found
        """
        if agent_id not in self.contexts:
            return False
        
        for item in self.contexts[agent_id]:
            if item.id == item_id:
                self.contexts[agent_id].remove(item)
                logger.info(f"Removed context item {item_id} from agent {agent_id}")
                return True
        
        return False
    
    def get_context_summary(self, agent_id: str) -> Dict[str, any]:
        """Get summary of agent's context.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Summary dictionary
        """
        items = self.get_agent_context(agent_id)
        
        if not items:
            return {
                "total_items": 0,
                "total_size": 0,
                "oldest_item": None,
                "newest_item": None,
                "stale_items": 0
            }
        
        total_size = sum(len(item.content) for item in items)
        oldest = min(items, key=lambda x: x.timestamp)
        newest = max(items, key=lambda x: x.timestamp)
        
        # Count stale items
        stale_count = 0
        for item in items:
            if item.type in ["file", "file_section"]:
                try:
                    file_path = Path(self.path_manager.resolve_path(item.path))
                    if file_path.exists():
                        current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if item.is_stale(current_mtime):
                            stale_count += 1
                except:
                    pass
        
        return {
            "total_items": len(items),
            "total_size": total_size,
            "oldest_item": oldest.timestamp.isoformat(),
            "newest_item": newest.timestamp.isoformat(),
            "stale_items": stale_count,
            "items_by_type": self._count_by_type(items)
        }
    
    def _cleanup_old_items(self, agent_id: str):
        """Remove items that are too old or exceed size limit.
        
        Args:
            agent_id: Agent identifier
        """
        if agent_id not in self.contexts:
            return
        
        items = self.contexts[agent_id]
        now = datetime.now()
        
        # Remove items older than max age
        items[:] = [
            item for item in items 
            if now - item.timestamp < self.max_context_age
        ]
        
        # Check total size and remove oldest if needed
        while items:
            total_size = sum(len(item.content) for item in items)
            if total_size <= self.max_context_size:
                break
            
            # Remove oldest item
            oldest = min(items, key=lambda x: x.timestamp)
            items.remove(oldest)
            logger.info(f"Removed old context item to stay under size limit: {oldest.path}")
    
    def _count_by_type(self, items: List[ContextItem]) -> Dict[str, int]:
        """Count items by type."""
        counts = {}
        for item in items:
            counts[item.type] = counts.get(item.type, 0) + 1
        return counts