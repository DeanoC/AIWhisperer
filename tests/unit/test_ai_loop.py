import pytest
from unittest.mock import MagicMock, patch

from ai_whisperer.context_management import ContextManager

@pytest.fixture
def mock_engine():
    """Fixture for a mock ExecutionEngine."""
    engine = MagicMock()
    # Accept both (key) and (key, default) signatures
    def config_get(key, default=None):
        return default
    engine.config.get.side_effect = config_get # Mock config access
    engine.state_manager = MagicMock() # Mock StateManager
    engine.monitor = MagicMock() # Mock Monitor
    return engine

@pytest.fixture
def mock_context_manager():
    """Fixture for a mock ContextManager."""
    return MagicMock(spec=ContextManager)

@pytest.fixture
def mock_tool_registry():
    """Fixture for a mock ToolRegistry."""
    return MagicMock()

@pytest.fixture
def mock_logger():
    """Fixture for a mock logger."""
    return MagicMock()

import threading
import asyncio

@patch('ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService.call_chat_completion')
def test_ai_loop_handles_content_response(mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop correctly handles an AI response with content."""
    # Ensure every call to call_chat_completion returns the correct structure
    def always_content_response(*args, **kwargs):
        return {
            "response": {
                "choices": [{"message": {"role": "assistant", "content": "This is a response."}, "finish_reason": "stop"}]
            },
            "message": {"role": "assistant", "content": "This is a response."}
        }
    # Patch the actual engine's openrouter_api.call_chat_completion
    mock_engine.openrouter_api = MagicMock()
    mock_engine.openrouter_api.call_chat_completion.side_effect = always_content_response

    initial_prompt = "Test prompt"
    task_definition = {"description": "Test task"}
    task_id = "test-task-123"

    from ai_whisperer.delegate_manager import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    assert final_result is not None
    mock_context_manager.add_message.assert_called() # Verify message was added to context

@patch('ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService.call_chat_completion')
@patch('ai_whisperer.tools.tool_registry.ToolRegistry.get_tool_by_name')
def test_ai_loop_handles_tool_calls(mock_get_tool_by_name, mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop correctly handles AI responses with tool calls."""
    # Configure the mock AI service to return a response with a tool call
    tool_call_response = {
        "response": {
            "choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]
        },
        "message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}
    }
    content_response = {
        "response": {
            "choices": [{"message": {"role": "assistant", "content": "Tool executed."}, "finish_reason": "stop"}]
        },
        "message": {"role": "assistant", "content": "Tool executed."}
    }
    def response_side_effect(*args, **kwargs):
        if not hasattr(response_side_effect, "call_count"):
            response_side_effect.call_count = 0
        response_side_effect.call_count += 1
        if response_side_effect.call_count == 1:
            return tool_call_response
        else:
            return content_response
    # Patch the actual engine's openrouter_api.call_chat_completion
    mock_engine.openrouter_api = MagicMock()
    mock_engine.openrouter_api.call_chat_completion.side_effect = response_side_effect

    # Mock the tool execution
    mock_tool_instance = MagicMock()
    mock_tool_instance.execute.return_value = {"status": "success"}
    mock_get_tool_by_name.return_value = mock_tool_instance
    mock_engine.tool_registry = MagicMock() # Mock the tool_registry attribute
    mock_engine.tool_registry.get_tool_by_name.return_value = mock_tool_instance

    initial_prompt = "Test prompt with tool call"
    task_definition = {"description": "Test task with tool"}
    task_id = "test-task-456"

    from ai_whisperer.delegate_manager import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    # Once run_ai_loop is implemented, assertions would verify:
    # - AI service called twice
    # - ToolRegistry.get_tool_by_name was called
    # - Tool instance execute was called
    # - ContextManager.add_message was called for assistant response and tool output

@patch('ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService.call_chat_completion')
def test_ai_loop_adds_messages_to_context(mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop adds user, assistant, and tool messages to the ContextManager."""
    # Always return the correct structure for every call
    tool_call_response = {
        "response": {
            "choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]
        },
        "message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}
    }
    content_response = {
        "response": {
            "choices": [{"message": {"role": "assistant", "content": "Tool executed."}, "finish_reason": "stop"}]
        },
        "message": {"role": "assistant", "content": "Tool executed."}
    }
    def response_side_effect(*args, **kwargs):
        # First call: tool call, second call: content
        if not hasattr(response_side_effect, "call_count"):
            response_side_effect.call_count = 0
        response_side_effect.call_count += 1
        if response_side_effect.call_count == 1:
            return tool_call_response
        else:
            return content_response
    # Patch the actual engine's openrouter_api.call_chat_completion
    mock_engine.openrouter_api = MagicMock()
    mock_engine.openrouter_api.call_chat_completion.side_effect = response_side_effect

    mock_tool_instance = MagicMock()
    mock_tool_instance.execute.return_value = {"status": "success"}
    mock_engine.tool_registry = MagicMock()
    mock_engine.tool_registry.get_tool_by_name.return_value = mock_tool_instance

    initial_prompt = "Test prompt for message adding"
    task_definition = {"description": "Test message adding"}
    task_id = "test-task-789"
    shutdown_event = threading.Event()

    from ai_whisperer.delegate_manager import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    # Once run_ai_loop is implemented, assertions would verify:
    # - mock_context_manager.add_message was called at least 3 times (user, assistant, tool output)

# Add more tests here for other scenarios like:
# - Handling different task types (if AI loop logic varies)
# - Error handling during AI calls
# - Error handling during tool execution
# - Loop termination conditions (e.g., max turns)