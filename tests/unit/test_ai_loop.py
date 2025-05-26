import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
import threading
from typing import Dict, Any

from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.ai_loop.ai_loopy import AILoop, SessionState
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.ai_service import AIService, AIStreamChunk
from ai_whisperer.tools.tool_registry import get_tool_registry, ToolRegistry
from ai_whisperer.tools.base_tool import AITool

# Helper for asyncio cleanup
async def cleanup_tasks():
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pending:
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

# Helper function (can be moved to a conftest.py or a shared utility)
async def wait_for_message_in_context(context_manager: ContextManager, expected_message: Dict[str, Any], timeout: float = 2.0, exact_content_match: bool = True):
    """Waits for a specific message to appear in the context history."""
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start_time < timeout:
        history = context_manager.get_history()
        for msg in history:
            # Check role first
            if msg.get("role") == expected_message.get("role"):
                # Handle different roles
                if msg.get("role") == "tool":
                    # For tool messages, check tool_call_id and content
                    if "tool_call_id" in expected_message and msg.get("tool_call_id") != expected_message.get("tool_call_id"):
                        continue # Mismatch on tool_call_id
                    if exact_content_match:
                        if msg.get("content") == expected_message.get("content"):
                            return True
                    else: # content contains expected_message content
                        if expected_message.get("content","") in msg.get("content", ""):
                            return True
                elif msg.get("role") == "assistant":
                    # For assistant messages, check content and tool_calls
                    content_match = False
                    if exact_content_match:
                        if msg.get("content") == expected_message.get("content"):
                            return True
                    else: # content contains expected_message content
                        if expected_message.get("content","") in msg.get("content", ""):
                            return True

                    tool_calls_match = False
                    if "tool_calls" in expected_message:
                        if "tool_calls" in expected_message and "tool_calls" in msg:
                            if msg.get("tool_calls") == expected_message.get("tool_calls"):
                                return True
                        elif "tool_calls" not in expected_message: # only match content if no tool_calls expected
                             return True
                else: # content contains expected_message content
                    # Other roles (system, user) - just check content
                    if exact_content_match:
                        if msg.get("content") == expected_message.get("content"):
                            return True
                    else: # content contains expected_message content
                        if expected_message.get("content","") in msg.get("content", ""):
                            return True
        await asyncio.sleep(0.01)
    return False

@pytest.fixture
def mock_ai_config():
    """Fixture for a mock AIConfig."""
    return AIConfig(api_key="test_key", model_id="test_model", temperature=0.7)

@pytest.fixture
def mock_ai_service():
    """Fixture for a mock AIService."""
    service = AsyncMock(spec=AIService)
    # Default behavior for stream_chat_completion if not overridden in a test
    async def default_stream_generator(*args, **kwargs):
        yield AIStreamChunk(delta_content="Default AI response.")
        yield AIStreamChunk(finish_reason="stop")
    service.stream_chat_completion.side_effect = default_stream_generator
    return service

@pytest.fixture
def context_manager():
    """Fixture for a real ContextManager."""
    return ContextManager()

@pytest.fixture
def delegate_manager():
    """Fixture for a DelegateManager."""
    return DelegateManager()

@pytest.fixture
def mock_tool_registry_fixture():
    """Fixture to provide a ToolRegistry instance and ensure it's clean."""
    # Use the global get_tool_registry but reset it for test isolation
    registry = get_tool_registry()
    registry.reset_tools()
    return registry

# Dummy Tool for testing
class MockTestTool(AITool):
    @property
    def name(self) -> str:
        return "test_tool"

    @property
    def description(self) -> str:
        return "A mock tool for testing."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"arg1": {"type": "string"}}}

    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for the AI on how to use this tool."""
        return "Use this tool to perform a test action with 'arg1'."

    def execute(self, arguments: Dict[str, Any]) -> str:
        return f"test_tool executed with {arguments}"

@pytest.mark.asyncio
async def test_ai_loop_handles_tool_calls(mock_ai_config, mock_ai_service, context_manager, delegate_manager, mock_tool_registry_fixture):
    """Tests that the AI loop correctly handles AI responses with tool calls."""

    # Register the mock tool
    mock_tool_instance = MockTestTool()
    mock_tool_registry_fixture.register_tool(mock_tool_instance)

    # Mock the execute method of the tool instance if needed for specific return values or side effects
    # For this test, the default execute is fine.

    # Define variables in the test function's scope
    tool_call_id = "call_abc"
    tool_name = "test_tool"
    tool_args_str = '{"arg1": "value1"}'
    simulated_error_message = f"test_tool executed with {{'arg1': 'value1'}}" # Corrected expected content


    async def tool_call_then_content_generator(*args, **kwargs):
        # First call: AI requests tool
        # Check if this is the call after a tool result has been processed
        messages = kwargs.get("messages", [])
        is_after_tool_call = any(msg.get("role") == "tool" for msg in messages)

        if not is_after_tool_call:
            yield AIStreamChunk(delta_tool_call_part='{"tool_calls": [') # Start of tool_calls array
            yield AIStreamChunk(delta_tool_call_part=f'{{"id": "{tool_call_id}", "type": "function", "function": {{"name": "{tool_name}", "arguments": {json.dumps(tool_args_str)}}}}}')
            yield AIStreamChunk(delta_tool_call_part=']}') # End of tool_calls array
            yield AIStreamChunk(finish_reason="tool_calls")
        else:
            # Second call: AI responds after tool execution
            yield AIStreamChunk(delta_content="Tool executed successfully.")
            yield AIStreamChunk(finish_reason="stop")

    mock_ai_service.stream_chat_completion.side_effect = tool_call_then_content_generator

    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)

    system_prompt = "System: Use tools if necessary."
    initial_user_prompt = "Test prompt with tool call"

    await ai_loop.start_session(system_prompt=system_prompt)
    await ai_loop.send_user_message(initial_user_prompt)
    await ai_loop.wait_for_idle(timeout=5.0) # Increased timeout for multi-turn

    history = context_manager.get_history()

    # Expected history: system, user, assistant (tool_call), tool (result), assistant (final_response)
    expected_tool_call_msg = {
        "role": "assistant",
        "content": None, # Or empty string, depending on AILoop's behavior
        "tool_calls": [{'id': tool_call_id, 'type': 'function', 'function': {'name': tool_name, 'arguments': '{"arg1": "value1"}'}}]
    }
    # We need to find the message that contains the tool_calls part.
    # The exact number might vary slightly depending on timing, but it should be at least the first chunk.
    # Let's be flexible with the content part of the assistant's tool call message.
    found_tool_call_msg = False
    for msg in history:
        if msg.get("role") == "assistant" and msg.get("tool_calls") == expected_tool_call_msg["tool_calls"]:
            found_tool_call_msg = True
            break
    assert found_tool_call_msg, f"Expected assistant tool call message not found in history: {history}"

    # Check for the tool message indicating the error
    expected_tool_result_msg = {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": simulated_error_message
    }
    assert await wait_for_message_in_context(context_manager, expected_tool_result_msg, exact_content_match=False), f"Expected tool result message not found in history: {history}"

    # Check for the final assistant message acknowledging the error
    assert await wait_for_message_in_context(context_manager, {"role": "assistant", "content": "Tool executed successfully."})

    await ai_loop.stop_session()
    await cleanup_tasks()


# Add more tests here for other scenarios like:
# - Handling different task types (if AI loop logic varies)
# - Error handling during AI calls
# - Error handling during tool execution
# - Loop termination conditions (e.g., max turns)

class MockErrorTool(AITool):
    @property
    def name(self) -> str:
        return "error_tool"

    @property
    def description(self) -> str:
        return "A mock tool that always raises an error."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"arg": {"type": "string"}}}

    def get_ai_prompt_instructions(self) -> str:
        return "Use this tool to simulate an error."

    def execute(self, arguments: Dict[str, Any]) -> str:
        raise RuntimeError(f"Simulated tool execution error with args: {arguments}")

@pytest.mark.asyncio
async def test_ai_loop_handles_tool_execution_error(mock_ai_config, mock_ai_service, context_manager, delegate_manager, mock_tool_registry_fixture):
    """Tests that the AI loop gracefully handles errors during tool execution."""

    # Register the mock error tool
    mock_error_tool_instance = MockErrorTool()
    mock_tool_registry_fixture.register_tool(mock_error_tool_instance)

    tool_call_id = "call_error_test"
    tool_name = "error_tool"
    tool_args_str = '{"arg": "some_value"}'
    simulated_error_message = f"Error executing tool {tool_name}: Simulated tool execution error with args: {{'arg': 'some_value'}}"


    call_count = 0
    async def tool_call_error_generator(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: AI requests the error tool
            yield AIStreamChunk(delta_tool_call_part='{"tool_calls": [')
            yield AIStreamChunk(delta_tool_call_part=f'{{"id": "{tool_call_id}", "type": "function", "function": {{"name": "{tool_name}", "arguments": {json.dumps(tool_args_str)}}}}}')
            yield AIStreamChunk(delta_tool_call_part=']}')
            yield AIStreamChunk(finish_reason="tool_calls")
        elif call_count == 2:
            # Second call: Simulate the AI responding after receiving the tool error message.
            yield AIStreamChunk(delta_content="Okay, there was an error with the tool.")
            yield AIStreamChunk(finish_reason="stop")
        else:
            pytest.fail(f"AI service called unexpectedly for the {call_count} time.")


    mock_ai_service.stream_chat_completion.side_effect = tool_call_error_generator
    delegate_manager.invoke_notification = AsyncMock()

    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)

    system_prompt = "System: Handle tool errors gracefully."
    initial_user_prompt = "Test prompt with error tool call"

    await ai_loop.start_session(system_prompt=system_prompt)
    await ai_loop.send_user_message(initial_user_prompt)

    # Wait for the AILoop to process the tool call, encounter the error,
    # add the error message to context, and potentially make the next AI call.
    # We can wait for the final AI response that acknowledges the error.
    await ai_loop.wait_for_idle(timeout=5.0) # Increased timeout for multi-turn with error

    history = context_manager.get_history()

    # Check for the assistant message requesting the tool call
    expected_tool_call_msg = {
        "role": "assistant",
        "content": None, # Or empty string
        "tool_calls": [{'id': tool_call_id, 'type': 'function', 'function': {'name': tool_name, 'arguments': tool_args_str}}]
    }
    found_tool_call_msg = False
    for msg in history:
        if msg.get("role") == "assistant" and msg.get("tool_calls") == expected_tool_call_msg["tool_calls"]:
            found_tool_call_msg = True
            break
    assert found_tool_call_msg, f"Expected assistant tool call message not found in history: {history}"

    # Check for the tool message indicating the error
    expected_error_tool_msg = {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": simulated_error_message
    }
    assert await wait_for_message_in_context(context_manager, expected_error_tool_msg, exact_content_match=False), f"Expected error tool message not found in history: {history}"

    # Check for the final assistant message acknowledging the error
    assert await wait_for_message_in_context(context_manager, {"role": "assistant", "content": "Okay, there was an error with the tool."})

    # Check that the ai_loop.error delegate was invoked
    error_delegate_calls = [
        c.kwargs['event_data'] for c in delegate_manager.invoke_notification.call_args_list
        if c.kwargs.get('event_type') == "ai_loop.error"
    ]
    assert len(error_delegate_calls) > 0, "ai_loop.error delegate was not invoked."
    # Check that at least one of the error calls is a RuntimeError
    assert any(isinstance(e, RuntimeError) for e in error_delegate_calls), "ai_loop.error delegate was not invoked with a RuntimeError."


    await ai_loop.stop_session()
    await cleanup_tasks()


@pytest.mark.asyncio
async def test_start_session_when_already_running(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that calling start_session when a session is already running does not start a new task."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    initial_task = ai_loop._session_task
    await ai_loop.start_session(system_prompt)
    assert ai_loop._session_task is initial_task, "A new session task was created when one was already running."
    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_stop_session_when_not_running(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that calling stop_session when no session is running does not raise an error."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    # Should not raise an exception
    await ai_loop.stop_session()
    assert ai_loop._session_task is None, "Session task should remain None."
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_pause_session_when_not_running(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that calling pause_session when no session is running does not raise an error."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()
    # Should not raise an exception
    await ai_loop.pause_session()
    delegate_manager.invoke_notification.assert_not_called()
    assert not ai_loop.pause_event.is_set(), "Pause event should be cleared if session not running but pause is called."
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_resume_session_when_not_running(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that calling resume_session when no session is running does not raise an error."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()
    # Should not raise an exception
    await ai_loop.resume_session()
    delegate_manager.invoke_notification.assert_not_called()
    assert ai_loop.pause_event.is_set(), "Pause event should remain set if session not running."
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_stop_session_immediately_after_start(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that stopping a session immediately after starting it works correctly."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()
    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    await ai_loop.stop_session()
    assert ai_loop._session_task is None, "Session task should be None after stopping."
    delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.session_started")
    delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.session_ended", event_data="stopped")
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_pause_resume_during_ai_stream(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests pausing and resuming the session during an AI stream."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)

    stream_chunks = [
        AIStreamChunk(delta_content="Chunk 1. "),
        AIStreamChunk(delta_content="Chunk 2. "),
        AIStreamChunk(delta_content="Chunk 3."),
        AIStreamChunk(finish_reason="stop")
    ]

    async def pausing_stream_generator(*args, **kwargs):
        for chunk in stream_chunks:
            yield chunk
            await asyncio.sleep(0.1) # Yield control after each chunk
            # Simulate pausing after the first chunk
            if chunk.delta_content and "Chunk 1" in chunk.delta_content:
                await ai_loop.pause_event.wait() # Wait here if paused

    mock_ai_service.stream_chat_completion.side_effect = pausing_stream_generator
    delegate_manager.invoke_notification = AsyncMock()

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    # Reset mock after initial session start notifications
    delegate_manager.invoke_notification.reset_mock()

    await ai_loop.send_user_message("User message")

    # Wait for the first chunk notification before pausing
    await asyncio.wait_for(
        delegate_manager.invoke_notification.wait_for_call(
            event_type="ai_loop.message.ai_chunk_received",
            event_data="Chunk 1. "
        ),
        timeout=2.0
    )

    # Pause the session
    await ai_loop.pause_session()
    assert not ai_loop.pause_event.is_set()

    # Wait for the pause notification to be invoked
    await asyncio.wait_for(
        delegate_manager.invoke_notification.wait_for_call(
            event_type="ai_loop.status.paused"
        ),
        timeout=2.0 # Increased timeout for waiting for notification
    )
    # Reset mock after pause notification to check notifications during pause
    delegate_manager.invoke_notification.reset_mock()

    # Ensure no more chunks are processed while paused
    await asyncio.sleep(0.5) # Increased sleep duration
    chunk_calls_paused = [
        c.kwargs['event_data'] for c in delegate_manager.invoke_notification.call_args_list
        if c.kwargs.get('event_type') == "ai_loop.message.ai_chunk_received"
    ]
    # We expect no chunks to be processed while paused
    assert len(chunk_calls_paused) == 0

    # Resume the session
    await ai_loop.resume_session()
    assert ai_loop.pause_event.is_set()
    delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.status.resumed")

    # Reset mock calls to only track notifications after resuming
    delegate_manager.invoke_notification.reset_mock()

    # Wait for the remaining chunks and the session to finish
    await ai_loop.wait_for_idle(timeout=5.0)

    chunk_calls_resumed = [
        c.kwargs['event_data'] for c in delegate_manager.invoke_notification.call_args_list
        if c.kwargs.get('event_type') == "ai_loop.message.ai_chunk_received"
    ]
    # After resuming and waiting for idle, the remaining chunks should have been processed.
    assert chunk_calls_resumed == ["Chunk 2. ", "Chunk 3."] # Expecting chunks after the first one

    expected_final_content = "Chunk 1. Chunk 2. Chunk 3."
    assert await wait_for_message_in_context(context_manager, {"role": "assistant", "content": expected_final_content})

    await ai_loop.stop_session()
    await cleanup_tasks()


@pytest.mark.asyncio
async def test_ai_loop_cancellation_while_waiting_for_input(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop session task is cancelled when stopped while waiting for user/tool input."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)

    # Wait for the loop to reach the WAIT_FOR_INPUT state
    # This state is reached after processing initial system/user messages and potentially an AI response.
    # Since our mock AI service yields a 'stop' reason by default, the loop should return to WAIT_FOR_INPUT
    # after the first AI call triggered by the initial user message.
    initial_user_prompt = "Start the loop and wait."
    await ai_loop.send_user_message(initial_user_prompt)

    # Wait until the loop is idle (waiting for input)
    await ai_loop.wait_for_idle(timeout=5.0)
    assert ai_loop.is_waiting_for_input()

    # Now stop the session while streaming is in progress
    stop_task = asyncio.create_task(ai_loop.stop_session())

    # Wait for the stop task to complete. This should cancel the session task.
    await asyncio.wait_for(stop_task, timeout=5.0)

    # Assert that the session task is done and was cancelled
    assert ai_loop._session_task is None or ai_loop._session_task.done()
    # Check if the task was cancelled (this might be tricky depending on how stop_session handles it)
    # The stop_session method explicitly calls task.cancel() if timeout occurs, or waits otherwise.
    # If it waits successfully, the task finishes normally after processing the None from the queue.
    # If it times out, it cancels. Let's check for the 'stopped' session_ended event.
    found_session_ended_stopped = any(
        c.kwargs.get('event_type') == "ai_loop.session_ended" and c.kwargs.get('event_data') == "stopped"
        for c in delegate_manager.invoke_notification.call_args_list
    )
    assert found_session_ended_stopped, "Session ended with 'stopped' reason not notified."

    # Cleanup is handled by stop_session and the test fixture's cleanup_tasks (if used)
    # Ensure no other tasks are left hanging
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)


@pytest.mark.asyncio
async def test_ai_loop_cancellation_during_ai_stream(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop session task is cancelled when stopped while processing an AI stream."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications

    # Mock the AI service to yield chunks slowly and indefinitely (or for a long time)
    async def slow_stream_generator(*args, **kwargs):
        for i in range(100): # Yield many chunks
            yield AIStreamChunk(delta_content=f"Chunk {i}. ")
            await asyncio.sleep(0.1) # Slow down streaming
        yield AIStreamChunk(finish_reason="stop") # Eventually finish

    mock_ai_service.stream_chat_completion.side_effect = slow_stream_generator

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)

    # Send a user message to trigger the AI call and streaming
    initial_user_prompt = "Start streaming."
    await ai_loop.send_user_message(initial_user_prompt)

    # Wait for the streaming to start (e.g., wait for the first chunk notification)
    await asyncio.wait_for(
        delegate_manager.invoke_notification.wait_for_call(
            event_type="ai_loop.message.ai_chunk_received",
            event_data="Chunk 0. "
        ),
        timeout=5.0
    )

    # Now stop the session while streaming is in progress
    stop_task = asyncio.create_task(ai_loop.stop_session())

    # Wait for the stop task to complete. This should cancel the session task.
    await asyncio.wait_for(stop_task, timeout=5.0)

    # Assert that the session task is done and was cancelled
    assert ai_loop._session_task is None or ai_loop._session_task.done()
    # Check if the task was cancelled (this might be tricky depending on how stop_session handles it)
    # The stop_session method explicitly calls task.cancel() if timeout occurs, or waits otherwise.
    # If it waits successfully, the task finishes normally after processing the None from the queue.
    # If it times out, it cancels. Let's check for the 'stopped' session_ended event.
    found_session_ended_stopped = any(
        c.kwargs.get('event_type') == "ai_loop.session_ended" and c.kwargs.get('event_data') == "stopped"
        for c in delegate_manager.invoke_notification.call_args_list
    )
    assert found_session_ended_stopped, "Session ended with 'stopped' reason not notified."

    # Cleanup is handled by stop_session and the test fixture's cleanup_tasks (if used)
    # Ensure no other tasks are left hanging
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    for task in pending:
        task.cancel()
    await asyncio.gather(*pending, return_exceptions=True)

@pytest.mark.asyncio
async def test_send_user_message_invalid_input(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that send_user_message handles invalid input gracefully and notifies delegate."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)

    # Send invalid input (e.g., a number)
    invalid_message = 12345
    await ai_loop.send_user_message(invalid_message)

    # Wait briefly to allow the message to be processed (or attempted)
    await asyncio.sleep(0.1)

    # Check that the ai_loop.error delegate was invoked with a TypeError
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError) # Using a helper for type check
    )

    # Ensure the invalid message was NOT added to the context history
    history = context_manager.get_history()
    assert not any(msg.get("content") == invalid_message for msg in history)

    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_handle_start_session_missing_initial_prompt(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that _handle_start_session handles missing initial_prompt and notifies delegate."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    # Invoke the control handler without initial_prompt
    await ai_loop._handle_start_session()

    # Check that the ai_loop.error delegate was invoked with a TypeError
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError)
    )

    # Ensure session did not start
    assert ai_loop._session_task is None

    await cleanup_tasks()

@pytest.mark.asyncio
async def test_handle_start_session_invalid_initial_prompt_type(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that _handle_start_session handles invalid initial_prompt type and notifies delegate."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    # Invoke the control handler with invalid initial_prompt type
    await ai_loop._handle_start_session(initial_prompt={"invalid": "prompt"})

    # Check that the ai_loop.error delegate was invoked with a TypeError
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError)
    )

    # Ensure session did not start
    assert ai_loop._session_task is None

    await cleanup_tasks()


@pytest.mark.asyncio
async def test_handle_send_user_message_missing_message(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that _handle_send_user_message handles missing message and does nothing."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    delegate_manager.invoke_notification.reset_mock() # Reset after session_started

    # Invoke the control handler without message
    await ai_loop._handle_send_user_message()

    # Wait briefly
    await asyncio.sleep(0.1)


    # Ensure no error notification was sent (as per current implementation, it just logs a warning)
    # Update this assertion to expect the TypeError notification

    # Update this assertion to expect the TypeError notification

    # Update this assertion to expect the TypeError notification
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError)
    )
    assert ai_loop._user_message_queue.empty()

    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_handle_send_user_message_invalid_message_type(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that _handle_send_user_message handles invalid message type and notifies delegate."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    delegate_manager.invoke_notification.reset_mock() # Reset after session_started

    # Invoke the control handler with invalid message type
    await ai_loop._handle_send_user_message(message=123)

    # Wait briefly
    await asyncio.sleep(0.1)

    # Check that the ai_loop.error delegate was invoked with a TypeError
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError)
    )
    assert ai_loop._user_message_queue.empty() # Ensure invalid message was not queued

    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_handle_provide_tool_result_invalid_result_type(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that _handle_provide_tool_result handles invalid result type and notifies delegate."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock()

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    delegate_manager.invoke_notification.reset_mock() # Reset after session_started

    # Invoke the control handler with invalid result type (e.g., a string)
    await ai_loop._handle_provide_tool_result(result="invalid result string")

    # Wait briefly
    await asyncio.sleep(0.1)

    # Check that the ai_loop.error delegate was invoked with a TypeError
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(TypeError)
    )
    assert ai_loop._tool_result_queue.empty() # Ensure invalid result was not queued

    await ai_loop.stop_session()
    await cleanup_tasks()

# Add a helper for checking exception types in mock calls (Ideally in conftest.py)
class AssertExceptionType:
    """Helper to assert the type of an exception passed to a mock call."""
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __eq__(self, other):
        return isinstance(other, self.expected_type)

# Add this helper to pytest.helpers if it's not already there (e.g., in conftest.py)
# pytest.helpers.assert_exception_type = AssertExceptionType

@pytest.mark.asyncio
async def test_ai_loop_handles_ai_service_error_during_stream(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop gracefully handles errors raised by the AI service during streaming."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications
    # Reset mock after initial session start notifications
    delegate_manager.invoke_notification.reset_mock()

    # Mock the AI service to raise an exception during streaming
    async def error_stream_generator(*args, **kwargs):
        yield AIStreamChunk(delta_content="Some initial content. ")
        await asyncio.sleep(0.1)
        raise Exception("Simulated AI service streaming error")
        yield AIStreamChunk(delta_content="This should not be yielded.") # This line should not be reached
        yield AIStreamChunk(finish_reason="stop")

    mock_ai_service.stream_chat_completion.side_effect = error_stream_generator

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    delegate_manager.invoke_notification.reset_mock() # Reset after session_started

    # Send a user message to trigger the AI call and streaming
    initial_user_prompt = "Trigger AI error."
    await ai_loop.send_user_message(initial_user_prompt)

    # Wait for the loop to process the error and return to a stable state (WAIT_FOR_INPUT)
    # The error handling in _assemble_ai_stream should catch the exception,
    # notify the delegate, add an error message to context, and return "stop" as finish_reason,
    # which transitions the loop back to WAIT_FOR_INPUT.
    await ai_loop.wait_for_idle(timeout=5.0)
    assert ai_loop.is_waiting_for_input()

    # Check that the ai_loop.error delegate was invoked with the simulated exception
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(Exception) # Check for a generic Exception or the specific one
    )

    # Check that an error message was added to the context history
    # The message content should indicate an error occurred during AI response processing.
    assert await wait_for_message_in_context(
        context_manager,
        {"role": "assistant", "content": "An error occurred while processing the AI response:"},
        exact_content_match=False # Content will include the exception details
    )

    # Check that the session ended gracefully (not crashed)
    # The loop should transition back to WAIT_FOR_INPUT, not SHUTDOWN, unless the error handling changes.
    # The test waits for idle, which implies it didn't crash.
    # We can also check for the session_ended event if the error caused a shutdown,
    # but the current implementation aims to recover.
    # Let's just confirm the loop is still running and waiting for input.
    assert ai_loop._session_task is not None and not ai_loop._session_task.done()
    assert ai_loop.is_waiting_for_input()

    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_ai_loop_handles_ai_service_error_before_stream(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop gracefully handles errors raised by the AI service before streaming starts."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications
    # Reset mock after initial session start notifications
    delegate_manager.invoke_notification.reset_mock()

    # Mock the AI service to raise an exception immediately when called
    mock_ai_service.stream_chat_completion.side_effect = Exception("Simulated AI service call error")

    system_prompt = "System prompt."
    await ai_loop.start_session(system_prompt)
    delegate_manager.invoke_notification.reset_mock() # Reset after session_started

    # Send a user message to trigger the AI call
    initial_user_prompt = "Trigger AI call error."
    await ai_loop.send_user_message(initial_user_prompt)

    # Wait for the loop to process the error and return to a stable state (WAIT_FOR_INPUT)
    # The error handling in _run_session should catch the exception,
    # notify the delegate, add an error message to context, and transition back to WAIT_FOR_INPUT.
    await ai_loop.wait_for_idle(timeout=5.0)
    assert ai_loop.is_waiting_for_input()

    # Check that the ai_loop.error delegate was invoked with the simulated exception
    delegate_manager.invoke_notification.assert_any_call(
        sender=ai_loop,
        event_type="ai_loop.error",
        event_data=pytest.helpers.assert_exception_type(Exception) # Check for a generic Exception or the specific one
    )

    # Check that an error message was added to the context history
    # The message content should indicate an error occurred while communicating with the AI service.
    # Check that an error message was added to the context history by _assemble_ai_stream
    assert await wait_for_message_in_context(
        context_manager,
        {"role": "assistant", "content": "An error occurred while processing the AI response:"},
        exact_content_match=False # Content will include the exception details
    )

    # Check that the session ended gracefully (not crashed)
    # The loop should transition back to WAIT_FOR_INPUT.
    assert ai_loop._session_task is not None and not ai_loop._session_task.done()
    assert ai_loop.is_waiting_for_input()

    await ai_loop.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_ai_loop_handles_invalid_initial_state(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop gracefully handles invalid initial state in _run_session."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications

    # Manually set an invalid state before starting the session task
    ai_loop._state = AILoop.SessionState.ASSEMBLE_AI_STREAM

    # We need to bypass the start_session check that prevents starting if a task exists,
    # and directly create and run the _run_session task to test the internal handling.
    # This is a bit of an internal test, but necessary to cover this specific error path.
    # We'll mock the internal _run_session to allow us to control its execution.
    with patch.object(ai_loop, '_run_session', wraps=ai_loop._run_session) as mock_run_session:
        # Create the session task manually, bypassing start_session's check
        ai_loop._session_task = asyncio.create_task(mock_run_session())

        # Wait for the task to complete (it should exit due to the error handling)
        await asyncio.wait_for(ai_loop._session_task, timeout=2.0)

        # Check that the ai_loop.error delegate was invoked with a RuntimeError
        delegate_manager.invoke_notification.assert_any_call(
            sender=ai_loop,
            event_type="ai_loop.error",
            event_data=pytest.helpers.assert_exception_type(RuntimeError)
        )

        # Check that the session task is done
        assert ai_loop._session_task.done()

    await cleanup_tasks()
@pytest.mark.asyncio
async def test_ai_loop_handles_invalid_initial_state(mock_ai_config, mock_ai_service, context_manager, delegate_manager):
    """Tests that the AI loop gracefully handles invalid initial state in _run_session."""
    ai_loop = AILoop(mock_ai_config, mock_ai_service, context_manager, delegate_manager)
    delegate_manager.invoke_notification = AsyncMock() # Mock notifications

    # Manually set an invalid state before starting the session task
    ai_loop._state = SessionState.ASSEMBLE_AI_STREAM

    # We need to bypass the start_session check that prevents starting if a task exists,
    # and directly create and run the _run_session task to test the internal handling.
    # This is a bit of an internal test, but necessary to cover this specific error path.
    # We'll mock the internal _run_session to allow us to control its execution.
    with patch.object(ai_loop, '_run_session', wraps=ai_loop._run_session) as mock_run_session:
        # Create the session task manually, bypassing start_session's check
        ai_loop._session_task = asyncio.create_task(mock_run_session())

        # Wait for the task to complete (it should exit due to the error handling)
        await asyncio.wait_for(ai_loop._session_task, timeout=2.0)

        # Check that the ai_loop.error delegate was invoked with a RuntimeError
        delegate_manager.invoke_notification.assert_any_call(
            sender=ai_loop,
            event_type="ai_loop.error",
            event_data=pytest.helpers.assert_exception_type(RuntimeError)
        )

        # Check that the session task is done
        assert ai_loop._session_task.done()

    await cleanup_tasks()