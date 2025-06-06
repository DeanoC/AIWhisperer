"""
Test module: test_agent_state_persistence.py
Purpose: TDD tests for async agent state persistence

Phase 4 - RED phase: Write failing tests first for agent state persistence functionality.
These tests will fail initially until we implement the StatePersistenceManager.

Test Coverage:
- Basic agent session state save/load
- Task queue state persistence
- Sleep state restoration
- Mail state preservation
- Error handling for corrupted/missing state files
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import the implemented classes (GREEN phase)
from ai_whisperer.services.agents.state_persistence import StatePersistenceManager, AgentSessionState, TaskQueueState


class TestAgentStatePersistence:
    """Test agent state persistence functionality using TDD approach."""
    
    @pytest.fixture
    def temp_state_dir(self):
        """Create temporary directory for state files."""
        temp_dir = tempfile.mkdtemp(prefix="agent_state_test_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def state_manager(self, temp_state_dir):
        """Create StatePersistenceManager instance."""
        return StatePersistenceManager(state_dir=temp_state_dir)
    
    @pytest.fixture
    def sample_agent_state(self):
        """Sample agent session state for testing."""
        return {
            "agent_id": "alice_123",
            "agent_name": "Alice the AI Assistant", 
            "status": "ACTIVE",
            "created_at": "2025-06-06T13:30:00Z",
            "last_activity": "2025-06-06T13:45:00Z",
            "configuration": {
                "model": "openai/gpt-4o",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "context": {
                "conversation_history": ["Hello", "Hi there!", "How can I help?"],
                "working_memory": {"current_task": "code_review", "file_count": 15}
            },
            "tool_sets": ["general_assistant", "agent_switching"]
        }
    
    @pytest.fixture 
    def sample_task_queue_state(self):
        """Sample task queue state for testing."""
        return {
            "agent_id": "alice_123",
            "pending_tasks": [
                {"id": "task_1", "type": "analysis", "priority": "high", "data": {"file": "main.py"}},
                {"id": "task_2", "type": "review", "priority": "medium", "data": {"pr": 123}}
            ],
            "in_progress_tasks": [
                {"id": "task_3", "type": "debug", "priority": "high", "started_at": "2025-06-06T13:40:00Z"}
            ],
            "completed_tasks": [
                {"id": "task_4", "type": "test", "priority": "low", "completed_at": "2025-06-06T13:35:00Z"}
            ]
        }
    
    # === BASIC STATE PERSISTENCE TESTS ===
    
    def test_save_agent_session_state(self, state_manager, sample_agent_state, temp_state_dir):
        """Test saving agent session state to persistence layer."""
        # RED: This test will fail - StatePersistenceManager.save_agent_state() doesn't exist
        session_id = "alice_123"
        
        # Should save state and return success
        result = state_manager.save_agent_state(session_id, sample_agent_state)
        assert result is True
        
        # Should create state file in correct location
        expected_file = temp_state_dir / "agents" / f"{session_id}.json"
        assert expected_file.exists()
        
        # Should contain correct data
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data["agent_id"] == "alice_123"
        assert saved_data["status"] == "ACTIVE"
        assert saved_data["agent_name"] == "Alice the AI Assistant"
    
    def test_load_agent_session_state(self, state_manager, sample_agent_state, temp_state_dir):
        """Test loading agent session state from persistence layer."""
        # RED: This test will fail - StatePersistenceManager.load_agent_state() doesn't exist
        session_id = "alice_123"
        
        # Manually create state file
        agents_dir = temp_state_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        state_file = agents_dir / f"{session_id}.json"
        with open(state_file, 'w') as f:
            json.dump(sample_agent_state, f)
        
        # Should load state successfully
        loaded_state = state_manager.load_agent_state(session_id)
        assert loaded_state is not None
        assert loaded_state["agent_id"] == "alice_123"
        assert loaded_state["status"] == "ACTIVE"
        assert loaded_state["agent_name"] == "Alice the AI Assistant"
        assert loaded_state["context"]["working_memory"]["current_task"] == "code_review"
    
    def test_agent_state_roundtrip(self, state_manager, sample_agent_state):
        """Test complete save → load cycle maintains data integrity."""
        session_id = "alice_123"
        
        # Save state
        save_result = state_manager.save_agent_state(session_id, sample_agent_state)
        assert save_result is True
        
        # Load state
        loaded_state = state_manager.load_agent_state(session_id)
        
        # Should contain all original data (ignoring metadata)
        for key, value in sample_agent_state.items():
            assert loaded_state[key] == value
        
        # Should have persistence metadata
        assert '_saved_at' in loaded_state
        assert '_session_id' in loaded_state
        assert loaded_state['_session_id'] == session_id
    
    def test_list_persisted_agents(self, state_manager, sample_agent_state, temp_state_dir):
        """Test listing all persisted agent sessions."""
        # RED: This will fail - list_persisted_agents() doesn't exist
        
        # Create multiple agent state files
        agents_dir = temp_state_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        for agent_id in ["alice_123", "debbie_456", "patricia_789"]:
            state_file = agents_dir / f"{agent_id}.json"
            test_state = sample_agent_state.copy()
            test_state["agent_id"] = agent_id
            with open(state_file, 'w') as f:
                json.dump(test_state, f)
        
        # Should return all agent IDs
        agent_list = state_manager.list_persisted_agents()
        assert len(agent_list) == 3
        assert "alice_123" in agent_list
        assert "debbie_456" in agent_list
        assert "patricia_789" in agent_list
    
    # === TASK QUEUE PERSISTENCE TESTS ===
    
    def test_save_task_queue_state(self, state_manager, sample_task_queue_state, temp_state_dir):
        """Test saving task queue state."""
        # RED: This will fail - save_task_queue_state() doesn't exist
        agent_id = "alice_123"
        
        result = state_manager.save_task_queue_state(agent_id, sample_task_queue_state)
        assert result is True
        
        # Should create task queue file
        expected_file = temp_state_dir / "tasks" / f"{agent_id}_tasks.json"
        assert expected_file.exists()
        
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        assert len(saved_data["pending_tasks"]) == 2
        assert len(saved_data["in_progress_tasks"]) == 1
        assert len(saved_data["completed_tasks"]) == 1
    
    def test_load_task_queue_state(self, state_manager, sample_task_queue_state, temp_state_dir):
        """Test loading task queue state."""
        # RED: This will fail - load_task_queue_state() doesn't exist
        agent_id = "alice_123"
        
        # Create task queue file
        tasks_dir = temp_state_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = tasks_dir / f"{agent_id}_tasks.json"
        with open(task_file, 'w') as f:
            json.dump(sample_task_queue_state, f)
        
        loaded_state = state_manager.load_task_queue_state(agent_id)
        assert loaded_state is not None
        assert loaded_state["agent_id"] == "alice_123"
        assert len(loaded_state["pending_tasks"]) == 2
        assert loaded_state["pending_tasks"][0]["type"] == "analysis"
    
    # === SLEEP STATE PERSISTENCE TESTS ===
    
    def test_save_sleep_state(self, state_manager, temp_state_dir):
        """Test saving agent sleep state."""
        # RED: This will fail - save_sleep_state() doesn't exist
        agent_id = "alice_123"
        sleep_state = {
            "agent_id": agent_id,
            "is_sleeping": True,
            "sleep_start": "2025-06-06T13:40:00Z",
            "sleep_duration": 300,  # 5 minutes
            "wake_events": ["mail_received", "high_priority_mail"],
            "wake_time": "2025-06-06T13:45:00Z"
        }
        
        result = state_manager.save_sleep_state(agent_id, sleep_state)
        assert result is True
        
        # Should create sleep state file
        expected_file = temp_state_dir / "sleep" / f"{agent_id}_sleep.json"
        assert expected_file.exists()
    
    def test_load_sleep_state(self, state_manager, temp_state_dir):
        """Test loading agent sleep state."""
        # RED: This will fail - load_sleep_state() doesn't exist
        agent_id = "alice_123"
        sleep_state = {
            "agent_id": agent_id,
            "is_sleeping": True,
            "sleep_start": "2025-06-06T13:40:00Z",
            "sleep_duration": 300,
            "wake_events": ["mail_received"]
        }
        
        # Create sleep state file
        sleep_dir = temp_state_dir / "sleep"
        sleep_dir.mkdir(parents=True, exist_ok=True)
        sleep_file = sleep_dir / f"{agent_id}_sleep.json"
        with open(sleep_file, 'w') as f:
            json.dump(sleep_state, f)
        
        loaded_state = state_manager.load_sleep_state(agent_id)
        assert loaded_state is not None
        assert loaded_state["is_sleeping"] is True
        assert loaded_state["sleep_duration"] == 300
        assert "mail_received" in loaded_state["wake_events"]
    
    # === ERROR HANDLING TESTS ===
    
    def test_load_nonexistent_agent_state(self, state_manager):
        """Test loading state for non-existent agent."""
        # RED: This will fail - load_agent_state() doesn't exist
        result = state_manager.load_agent_state("nonexistent_agent")
        assert result is None  # Should return None for missing agents
    
    def test_load_corrupted_state_file(self, state_manager, temp_state_dir):
        """Test handling corrupted state files."""
        # RED: This will fail - error handling doesn't exist
        session_id = "alice_123"
        
        # Create corrupted state file
        agents_dir = temp_state_dir / "agents" 
        agents_dir.mkdir(parents=True, exist_ok=True)
        state_file = agents_dir / f"{session_id}.json"
        with open(state_file, 'w') as f:
            f.write("{ invalid json content")
        
        # Should handle corruption gracefully
        result = state_manager.load_agent_state(session_id)
        assert result is None  # Should return None for corrupted files
    
    def test_save_state_with_permission_error(self, state_manager, temp_state_dir):
        """Test handling permission errors during save."""
        # RED: This will fail - error handling doesn't exist
        session_id = "alice_123"
        state_data = {"agent_id": "alice_123", "status": "ACTIVE"}
        
        # Make state directory read-only
        agents_dir = temp_state_dir / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        agents_dir.chmod(0o444)  # Read-only
        
        try:
            # Should handle permission error gracefully
            result = state_manager.save_agent_state(session_id, state_data)
            assert result is False  # Should return False on save failure
        finally:
            # Restore permissions for cleanup
            agents_dir.chmod(0o755)
    
    # === INTEGRATION TESTS ===
    
    @pytest.mark.asyncio
    async def test_async_state_operations(self, state_manager, sample_agent_state):
        """Test async operations for state persistence."""
        session_id = "alice_123"
        
        # Should support async save/load operations
        save_result = await state_manager.save_agent_state_async(session_id, sample_agent_state)
        assert save_result is True
        
        loaded_state = await state_manager.load_agent_state_async(session_id)
        
        # Should contain all original data (ignoring metadata)
        for key, value in sample_agent_state.items():
            assert loaded_state[key] == value
        
        # Should have persistence metadata
        assert '_saved_at' in loaded_state
    
    def test_state_cleanup(self, state_manager, temp_state_dir):
        """Test cleaning up old state files."""
        # RED: This will fail - cleanup_old_states() doesn't exist
        session_id = "alice_123"
        state_data = {"agent_id": "alice_123", "status": "STOPPED"}
        
        # Save and then cleanup
        state_manager.save_agent_state(session_id, state_data)
        
        cleanup_result = state_manager.cleanup_old_states(max_age_hours=0)  # Cleanup immediately
        assert cleanup_result > 0  # Should clean up at least one file
        
        # State should be gone
        result = state_manager.load_agent_state(session_id)
        assert result is None


# === MOCK CLASSES FOR TESTING ===
# These will be used during GREEN phase to test integration

class MockAgentSession:
    """Mock agent session for testing integration."""
    
    def __init__(self, agent_id: str, status: str = "ACTIVE"):
        self.agent_id = agent_id
        self.status = status
        self.configuration = {"model": "test", "temperature": 0.5}
        self.context = {"test": True}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for persistence."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "configuration": self.configuration,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MockAgentSession':
        """Create from dictionary."""
        session = cls(data["agent_id"], data["status"])
        session.configuration = data.get("configuration", {})
        session.context = data.get("context", {})
        return session


if __name__ == "__main__":
    # Run the tests to see them fail (RED phase)
    pytest.main([__file__, "-v"])