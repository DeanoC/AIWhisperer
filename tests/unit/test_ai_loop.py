import pytest
from unittest.mock import MagicMock, patch

# Assuming the refactored AI loop will be in src/ai_whisperer/ai_loop.py
# and ContextManager is in src/ai_whisperer/context_management.py
# from ai_whisperer.ai_loop import run_ai_loop 
from ai_whisperer.ai_loop import run_ai_loop
from ai_whisperer.context_management import ContextManager

@pytest.fixture
def mock_engine():
    """Fixture for a mock ExecutionEngine."""
    engine = MagicMock()
    engine.config.get.side_effect = lambda key, default: default # Mock config access
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

@patch('ai_whisperer.ai_service_interaction.OpenRouterAPI.call_chat_completion')
def test_ai_loop_handles_content_response(mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop correctly handles an AI response with content."""
    # Configure the mock AI service to return a response with content
    mock_call_chat_completion.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "This is a response."}, "finish_reason": "stop"}]
    }

    initial_prompt = "Test prompt"
    task_definition = {"description": "Test task"}
    task_id = "test-task-123"

    from project_dev.notes.thread_safe_delegates import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    assert final_result is not None
    mock_context_manager.add_message.assert_called() # Verify message was added to context

@patch('ai_whisperer.ai_service_interaction.OpenRouterAPI.call_chat_completion')
@patch('ai_whisperer.tools.tool_registry.ToolRegistry.get_tool_by_name')
def test_ai_loop_handles_tool_calls(mock_get_tool_by_name, mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop correctly handles AI responses with tool calls."""
    # Configure the mock AI service to return a response with a tool call
    mock_call_chat_completion.side_effect = [
        { # First response: tool call
            "choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]
        },
        { # Second response: content after tool output
            "choices": [{"message": {"role": "assistant", "content": "Tool executed."}, "finish_reason": "stop"}]
        }
    ]

    # Mock the tool execution
    mock_tool_instance = MagicMock()
    mock_tool_instance.execute.return_value = {"status": "success"}
    mock_get_tool_by_name.return_value = mock_tool_instance
    mock_engine.tool_registry = MagicMock() # Mock the tool_registry attribute
    mock_engine.tool_registry.get_tool_by_name.return_value = mock_tool_instance

    initial_prompt = "Test prompt with tool call"
    task_definition = {"description": "Test task with tool"}
    task_id = "test-task-456"

    from project_dev.notes.thread_safe_delegates import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    # Once run_ai_loop is implemented, assertions would verify:
    # - AI service called twice
    # - ToolRegistry.get_tool_by_name was called
    # - Tool instance execute was called
    # - ContextManager.add_message was called for assistant response and tool output

@patch('ai_whisperer.ai_service_interaction.OpenRouterAPI.call_chat_completion')
def test_ai_loop_adds_messages_to_context(mock_call_chat_completion, mock_engine, mock_context_manager, mock_logger):
    """Tests that the AI loop adds user, assistant, and tool messages to the ContextManager."""
    mock_call_chat_completion.side_effect = [
        { # First response: tool call
            "choices": [{"message": {"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}]
        },
        { # Second response: content after tool output
            "choices": [{"message": {"role": "assistant", "content": "Tool executed."}, "finish_reason": "stop"}]
        }
    ]
    mock_tool_instance = MagicMock()
    mock_tool_instance.execute.return_value = {"status": "success"}
    mock_engine.tool_registry = MagicMock()
    mock_engine.tool_registry.get_tool_by_name.return_value = mock_tool_instance

    initial_prompt = "Test prompt for message adding"
    task_definition = {"description": "Test message adding"}
    task_id = "test-task-789"
    shutdown_event = threading.Event()

    from project_dev.notes.thread_safe_delegates import DelegateManager
    delegate_manager = DelegateManager()
    final_result = run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_logger, mock_context_manager, delegate_manager)
    # Once run_ai_loop is implemented, assertions would verify:
    # - mock_context_manager.add_message was called at least 3 times (user, assistant, tool output)
    # mock_context_manager.add_message.assert_any_call({"role": "user", "content": initial_prompt})
    # mock_context_manager.add_message.assert_any_call({"role": "assistant", "tool_calls": [{"id": "call_abc", "function": {"name": "test_tool", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}) # Adjust based on actual AI response structure
    # mock_context_manager.add_message.assert_any_call({"role": "tool", "tool_call_id": "call_abc", "content": '{"status": "success"}'}) # Adjust based on actual tool output format

# Add more tests here for other scenarios like:
# - Handling different task types (if AI loop logic varies)
# - Error handling during AI calls
# - Error handling during tool execution
# - Loop termination conditions (e.g., max turns)