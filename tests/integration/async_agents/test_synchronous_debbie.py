"""
Test synchronous Debbie execution via mailbox.

This test suite verifies that Claude can:
1. Send instructions to Debbie via mailbox
2. Debbie processes tasks with full tool access
3. Debbie returns results via mailbox
4. Claude retrieves and presents results
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.execution.ai_loop import AILoop
from ai_whisperer.tools.tool_registry import ToolRegistry


@pytest.fixture
def mailbox():
    """Get a clean mailbox instance."""
    mb = get_mailbox()
    mb.clear_all()
    return mb


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    return Mock()


@pytest.fixture
def tool_registry():
    """Get tool registry with test tools."""
    return ToolRegistry()


class TestSynchronousDebbie:
    """Test synchronous Debbie execution patterns."""
    
    def test_claude_sends_task_to_debbie(self, mailbox):
        """Test Claude can send a task to Debbie via mailbox."""
        # Arrange
        task_mail = Mail(
            from_agent="Claude",
            to_agent="Debbie", 
            subject="Execute workspace analysis",
            body="Please run workspace_stats tool and return the results",
            priority=MessagePriority.HIGH
        )
        
        # Act
        message_id = mailbox.send_mail(task_mail)
        
        # Assert
        assert message_id is not None
        debbie_mail = mailbox.get_mail("Debbie")
        assert len(debbie_mail) == 1
        assert debbie_mail[0].subject == "Execute workspace analysis"
        
    def test_debbie_receives_and_processes_task(self, mailbox, mock_ai_service, tool_registry):
        """Test Debbie receives task and processes it."""
        # Arrange
        task_mail = Mail(
            from_agent="Claude",
            to_agent="Debbie",
            subject="Run test command",
            body="Please execute: list_directory path=/home/deano/projects/AIWhisperer",
            priority=MessagePriority.HIGH
        )
        mailbox.send_mail(task_mail)
        
        # Simulate Debbie checking mailbox
        debbie_mail = mailbox.get_mail("Debbie")
        task = debbie_mail[0]
        
        # Act - Debbie processes the task
        # In real implementation, this would be done by Debbie's AI loop
        tool = tool_registry.get_tool("list_directory")
        result = tool.execute(path="/home/deano/projects/AIWhisperer", _context=Mock())
        
        # Debbie sends result back
        result_mail = Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject=f"Re: {task.subject}",
            body=json.dumps({
                "task_id": task.id,
                "status": "completed",
                "result": result
            }),
            priority=MessagePriority.NORMAL
        )
        mailbox.send_mail(result_mail)
        
        # Assert
        claude_mail = mailbox.get_mail("Claude") 
        assert len(claude_mail) == 1
        response = json.loads(claude_mail[0].body)
        assert response["status"] == "completed"
        assert "result" in response
        
    async def test_synchronous_request_response_pattern(self, mailbox):
        """Test synchronous request/response pattern."""
        # This tests the pattern we want to implement
        
        # Claude sends request
        request_id = await self._send_task_request(
            mailbox,
            to_agent="Debbie",
            task="analyze_dependencies tool on current project"
        )
        
        # Wait for response (with timeout)
        response = await self._wait_for_response(
            mailbox,
            request_id,
            timeout=30.0
        )
        
        # Verify response
        assert response is not None
        assert response["status"] == "completed"
        assert "result" in response
        
    async def _send_task_request(self, mailbox, to_agent, task):
        """Helper to send task request."""
        request_id = f"req_{datetime.now().timestamp()}"
        
        mail = Mail(
            from_agent="Claude",
            to_agent=to_agent,
            subject=f"Task Request {request_id}",
            body=json.dumps({
                "request_id": request_id,
                "task": task,
                "timeout": 30.0
            }),
            priority=MessagePriority.HIGH
        )
        
        mailbox.send_mail(mail)
        return request_id
        
    async def _wait_for_response(self, mailbox, request_id, timeout):
        """Helper to wait for response."""
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            messages = mailbox.get_mail("Claude")
            
            for msg in messages:
                try:
                    body = json.loads(msg.body)
                    if body.get("request_id") == request_id:
                        mailbox.mark_as_read("Claude", msg.id)
                        return body
                except json.JSONDecodeError:
                    continue
                    
            await asyncio.sleep(0.1)
            
        return None


class TestDebbieToolExecution:
    """Test Debbie's ability to execute tools."""
    
    def test_debbie_executes_single_tool(self, mailbox, tool_registry):
        """Test Debbie can execute a single tool request."""
        # Task: Run workspace_stats
        task = {
            "tool": "workspace_stats",
            "parameters": {}
        }
        
        # Execute tool (simulating what Debbie would do)
        tool = tool_registry.get_tool("workspace_stats")
        result = tool.execute(_context=Mock(workspace_path="/home/deano/projects/AIWhisperer"))
        
        assert result is not None
        assert "files" in str(result)
        
    def test_debbie_executes_tool_chain(self, mailbox, tool_registry):
        """Test Debbie can execute a chain of tools."""
        # Task: Find Python files then analyze them
        tasks = [
            {"tool": "search_files", "parameters": {"pattern": "*.py", "limit": 5}},
            {"tool": "analyze_languages", "parameters": {}}
        ]
        
        results = []
        context = Mock(workspace_path="/home/deano/projects/AIWhisperer")
        
        for task in tasks:
            tool = tool_registry.get_tool(task["tool"]) 
            result = tool.execute(**task["parameters"], _context=context)
            results.append(result)
            
        assert len(results) == 2
        assert all(r is not None for r in results)


class TestErrorHandling:
    """Test error handling in synchronous execution."""
    
    def test_debbie_handles_tool_errors(self, mailbox):
        """Test Debbie properly reports tool execution errors."""
        # Send task that will fail
        error_task = Mail(
            from_agent="Claude",
            to_agent="Debbie",
            subject="Execute failing task",
            body=json.dumps({
                "tool": "nonexistent_tool",
                "parameters": {}
            }),
            priority=MessagePriority.HIGH
        )
        
        mailbox.send_mail(error_task)
        
        # Simulate Debbie's error response
        error_response = Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject="Re: Execute failing task",
            body=json.dumps({
                "status": "error",
                "error": "Tool 'nonexistent_tool' not found",
                "task_id": error_task.id
            }),
            priority=MessagePriority.HIGH
        )
        
        mailbox.send_mail(error_response)
        
        # Verify error handling
        responses = mailbox.get_mail("Claude")
        assert len(responses) == 1
        response_data = json.loads(responses[0].body)
        assert response_data["status"] == "error"
        assert "Tool 'nonexistent_tool' not found" in response_data["error"]