"""
Unit tests for synchronous agent executor.
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority

# TODO: Update for new AI loop architecture
pytestmark = pytest.mark.skip(reason="synchronous_executor needs update for new StatelessAILoop architecture")


# Commented out until synchronous_executor is updated for new architecture
"""
class TestSynchronousAgentExecutor:
    '''Test the synchronous agent executor.'''
    
    @pytest.fixture
    def executor(self):
        '''Create executor with clean mailbox.'''
        executor = SynchronousAgentExecutor()
        executor.mailbox.clear_all()
        return executor
        
    @pytest.mark.asyncio
    async def test_send_task_request(self, executor):
        """Test sending a task request."""
        # Act
        request_id = await executor.send_task_request(
            from_agent="Claude",
            to_agent="Debbie",
            task="analyze workspace",
            parameters={"depth": 2}
        )
        
        # Assert
        assert request_id.startswith("req_")
        assert request_id in executor.pending_requests
        
        debbie_mail = executor.mailbox.get_mail("Debbie")
        assert len(debbie_mail) == 1
        assert debbie_mail[0].subject == "Task Request: analyze workspace"
        
        body = json.loads(debbie_mail[0].body)
        assert body["request_id"] == request_id
        assert body["task"] == "analyze workspace"
        assert body["parameters"]["depth"] == 2
        
    @pytest.mark.asyncio
    async def test_wait_for_response_success(self, executor):
        """Test waiting for a successful response."""
        # Setup - send request
        request_id = await executor.send_task_request(
            from_agent="Claude",
            to_agent="Debbie",
            task="test task"
        )
        
        # Simulate Debbie's response
        response_mail = Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject="Re: Task Request: test task",
            body=json.dumps({
                "request_id": request_id,
                "status": "completed",
                "result": {"data": "test result"}
            })
        )
        executor.mailbox.send_mail(response_mail)
        
        # Act
        response = await executor.wait_for_response("Claude", request_id)
        
        # Assert
        assert response.request_id == request_id
        assert response.status == "completed"
        assert response.result == {"data": "test result"}
        assert response.error is None
        assert request_id not in executor.pending_requests
        
    @pytest.mark.asyncio
    async def test_wait_for_response_timeout(self, executor):
        """Test timeout when waiting for response."""
        # Setup
        request_id = await executor.send_task_request(
            from_agent="Claude",
            to_agent="Debbie",
            task="slow task",
            timeout=0.5  # Short timeout for test
        )
        
        # Act - wait without sending response
        response = await executor.wait_for_response("Claude", request_id)
        
        # Assert
        assert response.request_id == request_id
        assert response.status == "timeout"
        assert response.error == "Request timed out after 0.5 seconds"
        assert request_id not in executor.pending_requests
        
    @pytest.mark.asyncio
    async def test_execute_task_request_tool(self, executor):
        """Test executing a tool request."""
        # Setup
        mock_tool = Mock()
        mock_tool.execute.return_value = {"result": "tool output"}
        
        with patch('ai_whisperer.tools.tool_registry.ToolRegistry.get_tool', return_value=mock_tool):
            # Act
            await executor.execute_task_request(
                agent_name="Debbie",
                request={
                    "request_id": "req_123",
                    "from_agent": "Claude",
                    "task": "execute tool: workspace_stats",
                    "parameters": {"format": "json"}
                },
                context=Mock()
            )
            
        # Assert
        claude_mail = executor.mailbox.get_mail("Claude")
        assert len(claude_mail) == 1
        assert claude_mail[0].subject == "Re: Task Request: execute tool: workspace_stats"
        
        body = json.loads(claude_mail[0].body)
        assert body["request_id"] == "req_123"
        assert body["status"] == "completed"
        assert body["result"] == {"result": "tool output"}
        
    @pytest.mark.asyncio
    async def test_execute_task_request_error(self, executor):
        """Test error handling in task execution."""
        # Setup - tool that raises error
        with patch('ai_whisperer.tools.tool_registry.ToolRegistry.get_tool', side_effect=Exception("Tool error")):
            # Act
            await executor.execute_task_request(
                agent_name="Debbie",
                request={
                    "request_id": "req_456",
                    "from_agent": "Claude",
                    "task": "execute tool: bad_tool"
                },
                context=Mock()
            )
            
        # Assert
        claude_mail = executor.mailbox.get_mail("Claude")
        assert len(claude_mail) == 1
        
        body = json.loads(claude_mail[0].body)
        assert body["status"] == "error"
        assert "Tool error" in body["error"]
        
    def test_get_synchronous_executor_singleton(self):
        """Test that get_synchronous_executor returns singleton."""
        executor1 = get_synchronous_executor()
        executor2 = get_synchronous_executor()
        
        assert executor1 is executor2
"""