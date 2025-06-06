"""
Module: ai_whisperer/services/agents/state_persistence.py
Purpose: State persistence manager for async agents

TDD REFACTOR Phase: Clean, extensible implementation with proper design patterns.
Refactored from GREEN phase for better maintainability and integration.

Key Components:
- StatePersistenceManager: Main class for saving/loading agent states
- StateSerializer: Handles serialization/deserialization with validation
- StateValidator: Validates state integrity and consistency
- File-based JSON storage with atomic operations
- Comprehensive error handling and recovery

Architecture:
- Uses dependency injection for testability
- Follows single responsibility principle
- Extensible for different storage backends
- Thread-safe operations with proper locking

Usage:
    manager = StatePersistenceManager(state_dir="/path/to/state")
    manager.save_agent_state("agent_123", state_data)
    state = manager.load_agent_state("agent_123")
"""

import json
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Protocol
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# === REFACTOR PHASE: Clean Architecture Components ===

class StateSerializer(Protocol):
    """Protocol for state serialization/deserialization."""
    
    def serialize(self, data: Dict[str, Any]) -> str:
        """Serialize state data to string format."""
        ...
    
    def deserialize(self, data: str) -> Dict[str, Any]:
        """Deserialize string data to state dictionary."""
        ...


class JSONStateSerializer:
    """JSON implementation of StateSerializer."""
    
    def serialize(self, data: Dict[str, Any]) -> str:
        """Serialize state data to JSON string."""
        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
    
    def deserialize(self, data: str) -> Dict[str, Any]:
        """Deserialize JSON string to state dictionary."""
        return json.loads(data)


class StateValidator:
    """Validates state data integrity and consistency."""
    
    @staticmethod
    def validate_agent_state(state: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate agent session state.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['agent_id']
        for field in required_fields:
            if field not in state:
                return False, f"Missing required field: {field}"
        
        # Validate agent_id format
        agent_id = state.get('agent_id', '')
        if not isinstance(agent_id, str) or not agent_id.strip():
            return False, "agent_id must be a non-empty string"
        
        return True, None
    
    @staticmethod
    def validate_task_queue_state(state: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate task queue state.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['agent_id']
        for field in required_fields:
            if field not in state:
                return False, f"Missing required field: {field}"
        
        # Validate list fields if present
        list_fields = ['pending_tasks', 'in_progress_tasks', 'completed_tasks']
        for field in list_fields:
            if field in state and not isinstance(state[field], list):
                return False, f"{field} must be a list"
        
        return True, None
    
    @staticmethod 
    def validate_sleep_state(state: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate sleep state.
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = ['agent_id', 'is_sleeping']
        for field in required_fields:
            if field not in state:
                return False, f"Missing required field: {field}"
        
        # Validate is_sleeping is boolean
        if not isinstance(state.get('is_sleeping'), bool):
            return False, "is_sleeping must be a boolean"
        
        return True, None


@dataclass
class StateMetadata:
    """Metadata for persisted state."""
    saved_at: str
    session_id: str
    version: str = "1.0"
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return asdict(self)


class StatePersistenceManager:
    """
    Manages persistence of agent states to file system.
    
    REFACTOR Phase: Clean, extensible implementation with dependency injection.
    
    Directory structure:
    state_dir/
    ├── agents/          # Agent session states
    ├── tasks/           # Task queue states  
    ├── sleep/           # Sleep states
    └── system/          # System-wide state
    """
    
    def __init__(self, 
                 state_dir: Path, 
                 serializer: Optional[StateSerializer] = None,
                 validator: Optional[StateValidator] = None):
        """
        Initialize state persistence manager.
        
        Args:
            state_dir: Root directory for state files
            serializer: Custom serializer (defaults to JSON)
            validator: Custom validator (defaults to StateValidator)
        """
        self.state_dir = Path(state_dir)
        self.serializer = serializer or JSONStateSerializer()
        self.validator = validator or StateValidator()
        self._file_locks = {}  # Per-file locks for thread safety
        self._lock_mutex = threading.Lock()  # Protects the locks dict
        
        self._ensure_directories()
        logger.info(f"StatePersistenceManager initialized with state_dir: {self.state_dir}")
    
    def _ensure_directories(self):
        """Create necessary state directories if they don't exist."""
        for subdir in ['agents', 'tasks', 'sleep', 'system']:
            dir_path = self.state_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def _get_file_lock(self, file_path: Path) -> threading.Lock:
        """Get or create a lock for the given file path."""
        with self._lock_mutex:
            if str(file_path) not in self._file_locks:
                self._file_locks[str(file_path)] = threading.Lock()
            return self._file_locks[str(file_path)]
    
    def _add_metadata(self, state_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Add persistence metadata to state data."""
        metadata = StateMetadata(
            saved_at=datetime.now().isoformat(),
            session_id=session_id
        )
        
        # Create a copy to avoid modifying original
        state_with_metadata = state_data.copy()
        
        # Add metadata with underscore prefix to avoid conflicts
        for key, value in metadata.to_dict().items():
            state_with_metadata[f'_{key}'] = value
        
        return state_with_metadata
    
    def _remove_metadata(self, state_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove persistence metadata from state data."""
        if not state_data:
            return state_data
        
        # Create a copy without metadata fields
        clean_state = {}
        for key, value in state_data.items():
            if not key.startswith('_'):
                clean_state[key] = value
        
        return clean_state
    
    def _write_state_file(self, file_path: Path, state_data: Dict[str, Any]) -> bool:
        """Write state data to file with atomic operation."""
        try:
            file_lock = self._get_file_lock(file_path)
            
            with file_lock:
                # Serialize data
                serialized_data = self.serializer.serialize(state_data)
                
                # Atomic write: write to temp file then rename
                temp_file = file_path.with_suffix('.tmp')
                
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(serialized_data)
                    f.flush()  # Ensure data is written to disk
                
                # Atomic rename
                temp_file.rename(file_path)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to write state file {file_path}: {e}")
            # Clean up temp file if it exists
            temp_file = file_path.with_suffix('.tmp')
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            return False
    
    def _read_state_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read state data from file with validation."""
        try:
            if not file_path.exists():
                return None
            
            file_lock = self._get_file_lock(file_path)
            
            with file_lock:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Deserialize data
                state_data = self.serializer.deserialize(content)
                
            return state_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted state file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to read state file {file_path}: {e}")
            return None
    
    # === AGENT SESSION STATE METHODS ===
    
    def save_agent_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Save agent session state to file.
        
        Args:
            session_id: Unique identifier for the agent session
            state_data: Dictionary containing agent state
            
        Returns:
            True if saved successfully, False otherwise
        """
        # Validate state data
        is_valid, error_msg = self.validator.validate_agent_state(state_data)
        if not is_valid:
            logger.error(f"Invalid agent state for {session_id}: {error_msg}")
            return False
        
        try:
            agents_dir = self.state_dir / 'agents'
            state_file = agents_dir / f"{session_id}.json"
            
            # Add metadata and write to file
            state_with_metadata = self._add_metadata(state_data, session_id)
            success = self._write_state_file(state_file, state_with_metadata)
            
            if success:
                logger.debug(f"Saved agent state for session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save agent state for {session_id}: {e}")
            return False
    
    def load_agent_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent session state from file.
        
        Args:
            session_id: Unique identifier for the agent session
            
        Returns:
            Dictionary containing agent state, or None if not found/corrupted
        """
        try:
            agents_dir = self.state_dir / 'agents'
            state_file = agents_dir / f"{session_id}.json"
            
            # Read state data
            state_data = self._read_state_file(state_file)
            
            if state_data is None:
                logger.debug(f"No state file found for session {session_id}")
                return None
            
            # Validate loaded state
            is_valid, error_msg = self.validator.validate_agent_state(state_data)
            if not is_valid:
                logger.error(f"Invalid loaded agent state for {session_id}: {error_msg}")
                return None
            
            logger.debug(f"Loaded agent state for session {session_id}")
            return state_data
            
        except Exception as e:
            logger.error(f"Failed to load agent state for {session_id}: {e}")
            return None
    
    def list_persisted_agents(self) -> List[str]:
        """
        List all persisted agent session IDs.
        
        Returns:
            List of session IDs that have persisted state
        """
        try:
            agents_dir = self.state_dir / 'agents'
            if not agents_dir.exists():
                return []
            
            session_ids = []
            for state_file in agents_dir.glob('*.json'):
                session_id = state_file.stem  # filename without extension
                session_ids.append(session_id)
            
            logger.debug(f"Found {len(session_ids)} persisted agents")
            return sorted(session_ids)
            
        except Exception as e:
            logger.error(f"Failed to list persisted agents: {e}")
            return []
    
    # === TASK QUEUE STATE METHODS ===
    
    def save_task_queue_state(self, agent_id: str, task_state: Dict[str, Any]) -> bool:
        """
        Save task queue state for an agent.
        
        Args:
            agent_id: Agent identifier
            task_state: Dictionary containing task queue state
            
        Returns:
            True if saved successfully, False otherwise
        """
        # Validate state data
        is_valid, error_msg = self.validator.validate_task_queue_state(task_state)
        if not is_valid:
            logger.error(f"Invalid task queue state for {agent_id}: {error_msg}")
            return False
        
        try:
            tasks_dir = self.state_dir / 'tasks'
            task_file = tasks_dir / f"{agent_id}_tasks.json"
            
            # Add metadata and write to file
            task_with_metadata = self._add_metadata(task_state, agent_id)
            success = self._write_state_file(task_file, task_with_metadata)
            
            if success:
                logger.debug(f"Saved task queue state for agent {agent_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save task queue state for {agent_id}: {e}")
            return False
    
    def load_task_queue_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load task queue state for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary containing task queue state, or None if not found
        """
        try:
            tasks_dir = self.state_dir / 'tasks'
            task_file = tasks_dir / f"{agent_id}_tasks.json"
            
            task_data = self._read_state_file(task_file)
            if task_data is None:
                logger.debug(f"No task queue state found for agent {agent_id}")
                return None
            
            is_valid, error_msg = self.validator.validate_task_queue_state(task_data)
            if not is_valid:
                logger.error(f"Invalid loaded task queue state for {agent_id}: {error_msg}")
                return None
            
            logger.debug(f"Loaded task queue state for agent {agent_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"Failed to load task queue state for {agent_id}: {e}")
            return None
    
    # === SLEEP STATE METHODS ===
    
    def save_sleep_state(self, agent_id: str, sleep_state: Dict[str, Any]) -> bool:
        """
        Save sleep state for an agent.
        
        Args:
            agent_id: Agent identifier
            sleep_state: Dictionary containing sleep state
            
        Returns:
            True if saved successfully, False otherwise
        """
        is_valid, error_msg = self.validator.validate_sleep_state(sleep_state)
        if not is_valid:
            logger.error(f"Invalid sleep state for {agent_id}: {error_msg}")
            return False
            
        try:
            sleep_dir = self.state_dir / 'sleep'
            sleep_file = sleep_dir / f"{agent_id}_sleep.json"
            
            sleep_with_metadata = self._add_metadata(sleep_state, agent_id)
            success = self._write_state_file(sleep_file, sleep_with_metadata)
            
            if success:
                logger.debug(f"Saved sleep state for agent {agent_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save sleep state for {agent_id}: {e}")
            return False
    
    def load_sleep_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load sleep state for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary containing sleep state, or None if not found
        """
        try:
            sleep_dir = self.state_dir / 'sleep'
            sleep_file = sleep_dir / f"{agent_id}_sleep.json"
            
            sleep_data = self._read_state_file(sleep_file)
            if sleep_data is None:
                logger.debug(f"No sleep state found for agent {agent_id}")
                return None
            
            is_valid, error_msg = self.validator.validate_sleep_state(sleep_data)
            if not is_valid:
                logger.error(f"Invalid loaded sleep state for {agent_id}: {error_msg}")
                return None
            
            logger.debug(f"Loaded sleep state for agent {agent_id}")
            return sleep_data
            
        except Exception as e:
            logger.error(f"Failed to load sleep state for {agent_id}: {e}")
            return None
    
    # === ASYNC METHODS ===
    
    async def save_agent_state_async(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Async version of save_agent_state.
        
        Args:
            session_id: Unique identifier for the agent session
            state_data: Dictionary containing agent state
            
        Returns:
            True if saved successfully, False otherwise
        """
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save_agent_state, session_id, state_data)
    
    async def load_agent_state_async(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Async version of load_agent_state.
        
        Args:
            session_id: Unique identifier for the agent session
            
        Returns:
            Dictionary containing agent state, or None if not found
        """
        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.load_agent_state, session_id)
    
    # === CLEANUP METHODS ===
    
    def cleanup_old_states(self, max_age_hours: int = 24) -> int:
        """
        Clean up old state files.
        
        Args:
            max_age_hours: Maximum age of state files to keep
            
        Returns:
            Number of files cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cleanup_count = 0
            
            for subdir in ['agents', 'tasks', 'sleep']:
                dir_path = self.state_dir / subdir
                if not dir_path.exists():
                    continue
                
                for state_file in dir_path.glob('*.json'):
                    try:
                        # Check file modification time
                        file_mtime = datetime.fromtimestamp(state_file.stat().st_mtime)
                        if file_mtime < cutoff_time:
                            state_file.unlink()
                            cleanup_count += 1
                            logger.debug(f"Cleaned up old state file: {state_file}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up {state_file}: {e}")
            
            logger.info(f"Cleaned up {cleanup_count} old state files")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")
            return 0


# === AGENT STATE DATA CLASSES ===
# These are placeholder classes for the GREEN phase
# Will be properly implemented in REFACTOR phase

class AgentSessionState:
    """Placeholder for agent session state class."""
    pass


class TaskQueueState:
    """Placeholder for task queue state class."""
    pass