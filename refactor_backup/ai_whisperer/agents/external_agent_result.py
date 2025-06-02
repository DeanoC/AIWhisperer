"""
External Agent Result class.
Represents the result of executing a task with an external agent.
"""
from typing import Dict, List, Any, Optional


class ExternalAgentResult:
    """Result from external agent execution."""
    
    def __init__(self, success: bool, files_changed: List[str], 
                 output: str, error: Optional[str] = None,
                 metadata: Dict[str, Any] = None):
        """Initialize external agent result.
        
        Args:
            success: Whether execution was successful
            files_changed: List of files that were modified
            output: Output from the agent
            error: Error message if any
            metadata: Additional metadata
        """
        self.success = success
        self.files_changed = files_changed
        self.output = output
        self.error = error
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'files_changed': self.files_changed,
            'output': self.output,
            'error': self.error,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExternalAgentResult':
        """Create from dictionary."""
        return cls(
            success=data.get('success', False),
            files_changed=data.get('files_changed', []),
            output=data.get('output', ''),
            error=data.get('error'),
            metadata=data.get('metadata', {})
        )