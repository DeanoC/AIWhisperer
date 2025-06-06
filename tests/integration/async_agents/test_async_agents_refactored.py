"""Test refactored async agent implementation."""

import pytest
import asyncio
import json
from datetime import datetime

from ai_whisperer.services.agents.async_session_manager_v2 import (
    AsyncAgentSessionManager, AgentState
)


class TestAsyncAgentsRefactored:
    """Test the refactored async agent implementation."""
    
    @pytest.mark.asyncio
    async def test_agent_creation_with_current_patterns(self):
        """Test that agents are created using current patterns."""
        config = {
            "use_refactored_async_agents": True,
            "ai_service": {
                "provider": "openrouter",
                "api_key": "test-key"
            }
        }
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            # Create agent
            session = await manager.create_agent_session("d", auto_start=False)
            
            # Verify creation
            assert session.agent_id == "d"
            assert session.state == AgentState.IDLE
            assert hasattr(session, 'agent')
            assert hasattr(session, 'ai_loop')
            assert hasattr(session, 'context')
            
            # Verify using StatelessAgent
            assert session.agent.__class__.__name__ == "StatelessAgent"
            
        finally:
            await manager.stop()
            
    @pytest.mark.asyncio
    async def test_task_processing(self):
        """Test task processing through async agent."""
        config = {"use_refactored_async_agents": True}
        
        manager = AsyncAgentSessionManager(config)
        await manager.start()
        
        try:
            # Create agent
            session = await manager.create_agent_session("d")
            
            # Send task
            await manager.send_task_to_agent(
                "d",
                "What is 2 + 2?",
                {"test": True}
            )
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Check state
            states = manager.get_agent_states()
            assert "d" in states
            
        finally:
            await manager.stop()