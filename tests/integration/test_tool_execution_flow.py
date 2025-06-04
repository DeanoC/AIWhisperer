"""
Integration test for tool execution flow.

This tests the fundamental tool calling pattern to ensure:
1. Tools are executed when requested
2. Tool results are processed by the AI
3. No empty user messages are sent
4. The conversation completes properly
"""
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.ai.openrouter import OpenRouterAIService
from interactive_server.stateless_session_manager import StatelessInteractiveSession


class TestToolExecutionFlow:
    """Test the complete tool execution flow."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock websocket."""
        ws = AsyncMock()
        ws.send_json = AsyncMock()
        return ws
    
    @pytest.fixture
    def session_config(self):
        """Create test configuration."""
        return {
            "openrouter": {
                "api_key": "test-key",
                "model": "test-model",
                "params": {}
            }
        }
    
    
    @pytest.mark.asyncio
    async def test_tool_execution_with_fetch_url(self, mock_websocket, session_config):
        """Test that fetch_url tool executes properly and results are shown."""
        # Create the session directly
        session = StatelessInteractiveSession(
            session_id="test-session",
            websocket=mock_websocket,
            config=session_config
        )
        
        # Create a test agent
        agent_config = AgentConfig(
            name="test",
            description="Test agent",
            system_prompt="You are a test agent",
            model_name="test-model",
            provider="openrouter",
            api_settings={"api_key": "test-key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        
        await session.create_agent("test", "You are a test agent", agent_config)
        test_session = session
        
        # Mock the AI responses
        with patch('ai_whisperer.services.ai.openrouter.OpenRouterAIService.stream_chat_completion') as mock_stream:
            
            # First response: AI decides to use fetch_url tool
            async def first_response():
                yield Mock(
                    delta_content="[ANALYSIS]\nUser wants to see README. I'll use fetch_url.\n\n[COMMENTARY]\n",
                    delta_tool_call_part=None,
                    finish_reason=None,
                    delta_reasoning=None
                )
                yield Mock(
                    delta_content="",
                    delta_tool_call_part=[{
                        "index": 0,
                        "id": "tool_0_fetch_url",
                        "type": "function",
                        "function": {
                            "name": "fetch_url",
                            "arguments": '{"url":"https://github.com/test/repo"}'
                        }
                    }],
                    finish_reason="tool_calls",
                    delta_reasoning=None
                )
            
            # Second response: AI processes tool results
            async def second_response():
                yield Mock(
                    delta_content="[FINAL]\nHere is the README content:\n\n# Test Repository\n\nThis is a test.",
                    delta_tool_call_part=None,
                    finish_reason="stop",
                    delta_reasoning=None
                )
            
            # Mock tool execution
            with patch('ai_whisperer.tools.fetch_url_tool.FetchURLTool.execute') as mock_tool:
                mock_tool.return_value = {
                    "url": "https://github.com/test/repo",
                    "content": "# Test Repository\n\nThis is a test.",
                    "extract_mode": "markdown"
                }
                
                # Set up the mock to return different responses
                mock_stream.side_effect = [first_response(), second_response()]
                
                # Send the user message
                result = await test_session.send_user_message(
                    "Can you show me the readme from https://github.com/test/repo"
                )
                
                # Verify the flow
                assert result is not None
                assert "Test Repository" in result.get('response', '')
                assert result.get('tool_calls') is not None
                assert len(result['tool_calls']) == 1
                assert result['tool_calls'][0]['function']['name'] == 'fetch_url'
                
                # Verify AI was called twice (once for tool decision, once for processing results)
                assert mock_stream.call_count == 2
                
                # Verify no empty user messages were added
                messages = test_session.agents['test'].context.retrieve_messages()
                user_messages = [m for m in messages if m.get('role') == 'user']
                
                # Should only have the actual request (no automatic introduction anymore)
                assert len(user_messages) == 1
                assert user_messages[0]['content'] == "Can you show me the readme from https://github.com/test/repo"
                
                # Verify tool message was stored
                tool_messages = [m for m in messages if m.get('role') == 'tool']
                assert len(tool_messages) == 1
                
                # Verify final assistant response was stored
                assistant_messages = [m for m in messages if m.get('role') == 'assistant']
                assert len(assistant_messages) >= 2  # Introduction + tool call + final response
                assert "Test Repository" in assistant_messages[-1]['content']
    
    @pytest.mark.asyncio
    async def test_tool_execution_with_read_file(self, mock_websocket, session_config):
        """Test that read_file tool executes properly."""
        # Create the session directly
        session = StatelessInteractiveSession(
            session_id="test-session",
            websocket=mock_websocket,
            config=session_config
        )
        
        # Create a test agent
        agent_config = AgentConfig(
            name="test",
            description="Test agent",
            system_prompt="You are a test agent",
            model_name="test-model",
            provider="openrouter",
            api_settings={"api_key": "test-key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        
        await session.create_agent("test", "You are a test agent", agent_config)
        test_session = session
        
        with patch('ai_whisperer.services.ai.openrouter.OpenRouterAIService.stream_chat_completion') as mock_stream:
            
            # First response: AI decides to use read_file tool
            async def first_response():
                yield Mock(
                    delta_content="[ANALYSIS]\nUser wants to read README.md. I'll use read_file.\n\n[COMMENTARY]\n",
                    delta_tool_call_part=None,
                    finish_reason=None,
                    delta_reasoning=None
                )
                yield Mock(
                    delta_content="",
                    delta_tool_call_part=[{
                        "index": 0,
                        "id": "tool_0_read_file",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"path":"README.md"}'
                        }
                    }],
                    finish_reason="tool_calls",
                    delta_reasoning=None
                )
            
            # Second response: AI processes tool results
            async def second_response():
                yield Mock(
                    delta_content="[FINAL]\nThe README.md file contains information about AIWhisperer.",
                    delta_tool_call_part=None,
                    finish_reason="stop",
                    delta_reasoning=None
                )
            
            # Mock tool execution
            with patch('ai_whisperer.tools.read_file_tool.ReadFileTool.execute') as mock_tool:
                mock_tool.return_value = {
                    "content": "# AIWhisperer\n\nAI development tool.",
                    "path": "README.md",
                    "exists": True
                }
                
                mock_stream.side_effect = [first_response(), second_response()]
                
                result = await test_session.send_user_message("Please read README.md")
                
                # Verify the result
                assert result is not None
                assert "AIWhisperer" in result.get('response', '')
                assert result.get('tool_calls') is not None
                assert result['tool_calls'][0]['function']['name'] == 'read_file'
                
                # Verify proper message flow
                messages = test_session.agents['test'].context.retrieve_messages()
                
                # Check we don't have empty user messages
                for msg in messages:
                    if msg.get('role') == 'user' and msg != messages[0]:  # Skip system prompt
                        assert msg.get('content', '').strip() != ''
    
    @pytest.mark.asyncio
    async def test_no_continuation_after_simple_tool_use(self, mock_websocket, session_config):
        """Test that simple tool use doesn't trigger continuation logic."""
        # Create the session directly
        session = StatelessInteractiveSession(
            session_id="test-session",
            websocket=mock_websocket,
            config=session_config
        )
        
        # Create a test agent
        agent_config = AgentConfig(
            name="test",
            description="Test agent",
            system_prompt="You are a test agent",
            model_name="test-model",
            provider="openrouter",
            api_settings={"api_key": "test-key"},
            generation_params={},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        
        await session.create_agent("test", "You are a test agent", agent_config)
        test_session = session
        
        with patch('ai_whisperer.services.ai.openrouter.OpenRouterAIService.stream_chat_completion') as mock_stream:
            
            # Mock responses
            async def tool_response():
                yield Mock(
                    delta_content="[ANALYSIS]\nReading file.\n\n[COMMENTARY]\n",
                    delta_tool_call_part=[{
                        "index": 0,
                        "id": "tool_0",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path":"test.txt"}'}
                    }],
                    finish_reason="tool_calls",
                    delta_reasoning=None
                )
            
            async def final_response():
                yield Mock(
                    delta_content="[FINAL]\nThe file contains: test content",
                    delta_tool_call_part=None,
                    finish_reason="stop",
                    delta_reasoning=None
                )
            
            with patch('ai_whisperer.tools.read_file_tool.ReadFileTool.execute') as mock_tool:
                mock_tool.return_value = {"content": "test content", "path": "test.txt", "exists": True}
                
                mock_stream.side_effect = [tool_response(), final_response()]
                
                # Track continuation depth
                initial_depth = test_session._continuation_depth
                
                result = await test_session.send_user_message("Read test.txt")
                
                # Verify no continuation was triggered
                assert test_session._continuation_depth == 0
                assert initial_depth == 0
                
                # Verify clean completion
                assert "test content" in result.get('response', '')
                assert result.get('finish_reason') == 'stop'