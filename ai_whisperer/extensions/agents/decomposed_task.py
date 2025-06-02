"""
Module: ai_whisperer/agents/decomposed_task.py
Purpose: AI agent implementation for specialized task handling

DecomposedTask data model for Agent E.
Represents a task that has been decomposed for external agent execution.

Key Components:
- TaskStatus: Status of a decomposed task.
- DecomposedTask: A task decomposed by Agent E for execution by external agents.

Usage:
    taskstatus = TaskStatus()

Dependencies:
- dataclasses
- uuid
- enum

Related:
- See docs/agent-e-consolidated-implementation.md
- See docs/archive/phase2_consolidation/agent-e-implementation-summary.md

"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

class TaskStatus(Enum):
    """Status of a decomposed task."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

@dataclass
class DecomposedTask:
    """A task decomposed by Agent E for execution by external agents."""
    
    # Required fields
    task_id: str
    parent_task_name: str
    title: str
    description: str
    context: Dict[str, Any]
    acceptance_criteria: List[Dict[str, Any]]
    estimated_complexity: str
    status: str
    
    # Optional fields
    execution_strategy: Dict[str, Any] = field(default_factory=dict)
    external_agent_prompts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    execution_result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate the task after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate task fields."""
        # Validate required fields
        if not self.task_id:
            raise ValueError("task_id is required")
        if not self.parent_task_name:
            raise ValueError("parent_task_name is required")
        if not self.title:
            raise ValueError("title is required")
        if not self.description:
            raise ValueError("description is required")
        
        # Validate complexity
        valid_complexities = ["trivial", "simple", "moderate", "complex", "very_complex"]
        if self.estimated_complexity not in valid_complexities:
            raise ValueError(f"estimated_complexity must be one of {valid_complexities}")
        
        # Validate status
        valid_statuses = [s.value for s in TaskStatus]
        if self.status not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        
        # Ensure context has required fields
        required_context_fields = ["files_to_read", "files_to_modify", "technology_stack", "constraints"]
        for field in required_context_fields:
            if field not in self.context:
                self.context[field] = [] if field != "technology_stack" else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert task to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecomposedTask':
        """Create a DecomposedTask from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DecomposedTask':
        """Create a DecomposedTask from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def update_status(self, new_status: str):
        """Update task status with validation."""
        valid_statuses = [s.value for s in TaskStatus]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        # Validate state transitions
        if self.status == "completed" and new_status in ["pending", "assigned", "in_progress"]:
            raise ValueError(f"Cannot transition from completed to {new_status}")
        
        if self.status == "failed" and new_status == "pending":
            raise ValueError("Cannot transition from failed to pending without reset")
        
        self.status = new_status
    
    def record_execution_result(self, agent_used: str, success: bool, 
                              files_changed: List[str], tests_passed: bool,
                              notes: str = ""):
        """Record the result of task execution."""
        start_time = self.execution_result.get('start_time') if self.execution_result else datetime.now(timezone.utc).isoformat()
        
        self.execution_result = {
            'agent_used': agent_used,
            'start_time': start_time,
            'end_time': datetime.now(timezone.utc).isoformat(),
            'success': success,
            'files_changed': files_changed,
            'tests_passed': tests_passed,
            'notes': notes
        }
        
        # Update status based on success
        if success:
            self.update_status('completed')
        else:
            self.update_status('failed')
    
    def add_external_agent_prompt(self, agent_name: str, prompt_data: Dict[str, Any]):
        """Add or update prompt for a specific external agent."""
        self.external_agent_prompts[agent_name] = prompt_data
    
    def get_dependencies(self) -> List[str]:
        """Get list of task dependencies."""
        return self.context.get('dependencies', [])
