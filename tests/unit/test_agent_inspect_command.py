import pytest
from unittest.mock import MagicMock
from ai_whisperer.commands import agent as agent_commands

@pytest.mark.asyncio
class TestAgentInspectCommand:
    async def test_returns_context_for_valid_agent(self):
        # Arrange: mock context manager and agent
        mock_context_manager = MagicMock()
        mock_context_manager.get_history.return_value = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"}
        ]
        # Simulate agent registry/lookup if needed
        agent_id = "P"
        # Act: call the inspect command handler
        result = await agent_commands.inspect_agent_context(agent_id=agent_id, info_type="context", context_manager=mock_context_manager)
        # Assert: correct context is returned
        assert result["agent_id"] == agent_id
        assert result["info_type"] == "context"
        assert result["context"] == mock_context_manager.get_history.return_value

    async def test_handles_invalid_agent_id(self):
        # Arrange: simulate agent lookup failure
        agent_id = "INVALID"
        # Act: call the inspect command handler
        result = await agent_commands.inspect_agent_context(agent_id=agent_id, info_type="context", context_manager=None)
        # Assert: returns error or empty context
        assert result["agent_id"] == agent_id
        assert result["context"] == [] or result.get("error")

    async def test_handles_unknown_info_type(self):
        # Arrange: valid agent, unknown info_type
        mock_context_manager = MagicMock()
        agent_id = "P"
        # Act: call the inspect command handler
        result = await agent_commands.inspect_agent_context(agent_id=agent_id, info_type="unknown", context_manager=mock_context_manager)
        # Assert: returns error or default behavior
        assert result["agent_id"] == agent_id
        assert result["info_type"] == "unknown"
        assert "error" in result or result["context"] == []
