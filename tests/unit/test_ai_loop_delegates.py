import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch # Added patch
import json # Added for tool argument stringification

# Import real components
from ai_whisperer.state_management import StateManager # Not strictly needed for these tests but good for context
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.ai_service.ai_service import AIService, AIStreamChunk
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_loop.ai_loopy import AILoop
from ai_whisperer.context_management import ContextManager
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.tool_registry import get_tool_registry, ToolRegistry
from typing import Dict, Any # Added for MockTestTool


@pytest.fixture
def mock_ai_config_fixture(): # Renamed to avoid conflict
    """Fixture for an AIConfig."""
    return AIConfig(api_key="test_api_key", model_id="test_model", temperature=0.7)

@pytest.fixture
def mock_ai_service_fixture(): # Renamed
    """Fixture for a mock AIService."""
    service = AsyncMock(spec=AIService)
    # Default behavior for stream_chat_completion
    async def default_stream_generator(*args, **kwargs):
        yield AIStreamChunk(delta_content="Default AI response.")
        yield AIStreamChunk(finish_reason="stop")
    service.stream_chat_completion.side_effect = default_stream_generator
    return service

@pytest.fixture
def context_manager_fixture(): # Renamed
    """Fixture for a real ContextManager."""
    return ContextManager()

@pytest.fixture
def delegate_manager_fixture(): # Renamed
    """Fixture for a real DelegateManager."""
    return DelegateManager()

@pytest.fixture
def mock_tool_registry_fixture():
    """Fixture to provide a ToolRegistry instance and ensure it's clean."""
    registry = get_tool_registry()
    registry.reset_tools()
    return registry

# Dummy Tool for testing tool-related delegates
class MockTestTool(AITool):
    @property
    def name(self) -> str:
        return "test_tool_for_delegates"

    @property
    def description(self) -> str:
        return "A mock tool for testing delegate invocations."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"arg1": {"type": "string"}}}

    def get_ai_prompt_instructions(self) -> str:
        return "Use this tool to perform a test action with 'arg1'."

    def execute(self, arguments: Dict[str, Any]) -> str:
        return f"test_tool_for_delegates executed with {arguments}"

@pytest.fixture
def ai_loop_fixture(mock_ai_config_fixture, mock_ai_service_fixture, context_manager_fixture, delegate_manager_fixture):
    """Fixture to create an AILoop instance."""
    loop = AILoop(
        config=mock_ai_config_fixture,
        ai_service=mock_ai_service_fixture,
        context_manager=context_manager_fixture,
        delegate_manager=delegate_manager_fixture
    )
    loop._tool_registry = get_tool_registry() # Ensure AILoop has a tool registry
    return loop

# Helper for asyncio cleanup
async def cleanup_tasks():
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pending:
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

# --- Tests for Notification Delegates Invoked BY AILoop ---

@pytest.mark.asyncio
async def test_session_started_notification_invoked(ai_loop_fixture: AILoop, delegate_manager_fixture: DelegateManager):
    """Tests that 'ai_loop.session_started' notification is invoked."""
    delegate_manager_fixture.invoke_notification = AsyncMock() # Spy on invoke_notification

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await asyncio.sleep(0) # Yield to allow the session task to run and emit the notification

    delegate_manager_fixture.invoke_notification.assert_any_call(
        sender=ai_loop_fixture,
        event_type="ai_loop.session_started" # Removed event_data=None
    )
    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_session_ended_notification_invoked_on_stop(ai_loop_fixture: AILoop, delegate_manager_fixture: DelegateManager):
    """Tests that 'ai_loop.session_ended' is invoked with 'stopped' on normal stop."""
    delegate_manager_fixture.invoke_notification = AsyncMock()

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await ai_loop_fixture.stop_session()

    found_session_ended = False
    for mock_call in delegate_manager_fixture.invoke_notification.call_args_list:
        args, kwargs = mock_call
        if kwargs.get('sender') == ai_loop_fixture and \
           kwargs.get('event_type') == "ai_loop.session_ended" and \
           kwargs.get('event_data') == "stopped":
            found_session_ended = True
            break
    assert found_session_ended, "ai_loop.session_ended with event_data='stopped' not invoked"
    await cleanup_tasks()


@pytest.mark.asyncio
async def test_user_message_processed_notification_invoked(ai_loop_fixture: AILoop, delegate_manager_fixture: DelegateManager):
    """Tests that 'ai_loop.message.user_processed' notification is invoked."""
    delegate_manager_fixture.invoke_notification = AsyncMock()
    user_msg = "Hello AI!"

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await ai_loop_fixture.send_user_message(user_msg)
    await ai_loop_fixture.wait_for_idle(timeout=2.0)

    delegate_manager_fixture.invoke_notification.assert_any_call(
        sender=ai_loop_fixture,
        event_type="ai_loop.message.user_processed",
        event_data=user_msg
    )
    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_ai_chunk_received_notification_invoked(
    ai_loop_fixture: AILoop,
    delegate_manager_fixture: DelegateManager,
    mock_ai_service_fixture: AsyncMock
):
    """Tests that 'ai_loop.message.ai_chunk_received' is invoked for each content chunk."""
    delegate_manager_fixture.invoke_notification = AsyncMock()

    async def custom_stream_generator(*args, **kwargs):
        yield AIStreamChunk(delta_content="Chunk 1. ")
        yield AIStreamChunk(delta_content="Chunk 2.")
        yield AIStreamChunk(finish_reason="stop")
    mock_ai_service_fixture.stream_chat_completion.side_effect = custom_stream_generator

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await ai_loop_fixture.send_user_message("User message")
    await ai_loop_fixture.wait_for_idle(timeout=2.0)

    chunk_calls = [
        c.kwargs['event_data'] for c in delegate_manager_fixture.invoke_notification.call_args_list
        if c.kwargs.get('event_type') == "ai_loop.message.ai_chunk_received"
    ]
    # Allow for possible duplicate notifications, but ensure the expected sequence is present in order
    expected_chunks = ["Chunk 1. ", "Chunk 2."]
    idx = 0
    for chunk in chunk_calls:
        if idx < len(expected_chunks) and chunk == expected_chunks[idx]:
            idx += 1
    assert idx == len(expected_chunks), f"Expected sequence {expected_chunks} not found in {chunk_calls}"

    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_tool_call_identified_notification_invoked(
    ai_loop_fixture: AILoop,
    delegate_manager_fixture: DelegateManager,
    mock_ai_service_fixture: AsyncMock,
    mock_tool_registry_fixture: ToolRegistry
):
    """Tests that 'ai_loop.tool_call.identified' is invoked."""
    delegate_manager_fixture.invoke_notification = AsyncMock()

    mock_tool_instance = MockTestTool()
    mock_tool_registry_fixture.register_tool(mock_tool_instance)
    ai_loop_fixture._tool_registry = mock_tool_registry_fixture

    tool_call_id = "call_deleg_test"
    tool_name = "test_tool_for_delegates"
    tool_args_str = '{"arg1": "val_deleg"}'

    # Counter for AI service calls
    ai_call_count = 0
    async def tool_call_generator(*args, **kwargs):
        nonlocal ai_call_count
        ai_call_count += 1
        if ai_call_count == 1: # First call, request tool
            yield AIStreamChunk(delta_tool_call_part='{"tool_calls": [')
            yield AIStreamChunk(delta_tool_call_part=f'{{"id": "{tool_call_id}", "type": "function", "function": {{"name": "{tool_name}", "arguments": {json.dumps(tool_args_str)}}}}}')
            yield AIStreamChunk(delta_tool_call_part=']}')
            yield AIStreamChunk(finish_reason="tool_calls")
        else: # Subsequent calls, respond normally to stop the loop
            yield AIStreamChunk(delta_content="AI response after tool call.")
            yield AIStreamChunk(finish_reason="stop")
    mock_ai_service_fixture.stream_chat_completion.side_effect = tool_call_generator

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await ai_loop_fixture.send_user_message("User message invoking tool")
    await ai_loop_fixture.wait_for_idle(timeout=3.0)
    # Check that the expected notification is present in the call list
    found = False
    for call_args in delegate_manager_fixture.invoke_notification.call_args_list:
        kwargs = call_args.kwargs
        if kwargs.get('event_type') == "ai_loop.tool_call.identified":
            event_data = kwargs.get('event_data')
            # event_data should be a list of tool call dicts; check if any dict has the expected tool name
            if isinstance(event_data, list) and any(
                isinstance(tc, dict) and tc.get('function', {}).get('name') == tool_name for tc in event_data
            ):
                found = True
                break
    assert found, f"Expected 'ai_loop.tool_call.identified' notification with a tool call for '{tool_name}' not found in calls: {delegate_manager_fixture.invoke_notification.call_args_list}"
    # Optionally, check that the event was present at least once, not necessarily only once
    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_tool_result_processed_notification_invoked(
    ai_loop_fixture: AILoop,
    delegate_manager_fixture: DelegateManager,
    mock_ai_service_fixture: AsyncMock,
    mock_tool_registry_fixture: ToolRegistry,
    context_manager_fixture: ContextManager
):
    """Tests that 'ai_loop.tool_call.result_processed' is invoked."""
    delegate_manager_fixture.invoke_notification = AsyncMock()

    mock_tool_instance = MockTestTool()
    mock_tool_registry_fixture.register_tool(mock_tool_instance)
    ai_loop_fixture._tool_registry = mock_tool_registry_fixture

    tool_call_id = "call_res_proc"
    tool_name = "test_tool_for_delegates"
    tool_args_dict = {"arg1": "val_res_proc"}
    tool_args_str_for_ai = json.dumps(tool_args_dict) # This is what AI would see as string arg
    expected_tool_result_content = mock_tool_instance.execute(arguments=tool_args_dict)

    expected_tool_message_in_context = {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": expected_tool_result_content
    }

    call_count = 0
    async def multi_turn_ai_response(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            yield AIStreamChunk(delta_tool_call_part='{"tool_calls": [')
            yield AIStreamChunk(delta_tool_call_part=f'{{"id": "{tool_call_id}", "type": "function", "function": {{"name": "{tool_name}", "arguments": {json.dumps(tool_args_str_for_ai)}}}}}')
            yield AIStreamChunk(delta_tool_call_part=']}')
            yield AIStreamChunk(finish_reason="tool_calls")
        elif call_count == 2:
            yield AIStreamChunk(delta_content="Tool was executed.")
            yield AIStreamChunk(finish_reason="stop")
        else:
            pytest.fail("AI service called too many times.")

    mock_ai_service_fixture.stream_chat_completion.side_effect = multi_turn_ai_response

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await ai_loop_fixture.send_user_message("User message invoking tool")
    await ai_loop_fixture.wait_for_idle(timeout=3.0)

    found_result_processed = any(
        c.kwargs.get('event_type') == "ai_loop.tool_call.result_processed" and \
        c.kwargs.get('event_data') == expected_tool_message_in_context
        for c in delegate_manager_fixture.invoke_notification.call_args_list
    )
    assert found_result_processed, f"ai_loop.tool_call.result_processed not invoked with correct data. Expected: {expected_tool_message_in_context}, Got: {[c.kwargs for c in delegate_manager_fixture.invoke_notification.call_args_list if c.kwargs.get('event_type') == 'ai_loop.tool_call.result_processed']}"

    history = context_manager_fixture.get_history()
    assert expected_tool_message_in_context in history, f"Tool result message not found in context. History: {history}"

    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

@pytest.mark.asyncio
async def test_status_paused_resumed_notifications_invoked(ai_loop_fixture: AILoop, delegate_manager_fixture: DelegateManager):
    """Tests that 'ai_loop.status.paused' and 'ai_loop.status.resumed' are invoked."""
    delegate_manager_fixture.invoke_notification = AsyncMock()

    await ai_loop_fixture.start_session(system_prompt="System prompt")
    await asyncio.sleep(0.1) # Give AILoop a moment to transition state

    await ai_loop_fixture.pause_session()
    await asyncio.sleep(0) # Yield to allow the session task to process pause and emit notification
    delegate_manager_fixture.invoke_notification.assert_any_call(
        sender=ai_loop_fixture,
        event_type="ai_loop.status.paused" # Removed event_data=None
    )

    await asyncio.sleep(0) # Yield before resuming
    await ai_loop_fixture.resume_session()
    delegate_manager_fixture.invoke_notification.assert_any_call(
        sender=ai_loop_fixture,
        event_type="ai_loop.status.resumed" # Removed event_data=None
    )

    await ai_loop_fixture.stop_session()
    await cleanup_tasks()

# --- Test for Control Delegates Handled BY AILoop ---

@pytest.mark.asyncio
async def test_control_delegates_trigger_ailoop_handlers(
    delegate_manager_fixture: DelegateManager,
    mock_ai_config_fixture: AIConfig, # Use renamed fixture
    mock_ai_service_fixture: AsyncMock,
    context_manager_fixture: ContextManager
):
    """
    Tests that invoking control events through DelegateManager triggers AILoop's internal handlers.
    """
    with patch.object(AILoop, '_handle_start_session', new_callable=AsyncMock) as mock_handle_start, \
         patch.object(AILoop, '_handle_stop_session', new_callable=AsyncMock) as mock_handle_stop, \
         patch.object(AILoop, '_handle_pause_session', new_callable=AsyncMock) as mock_handle_pause, \
         patch.object(AILoop, '_handle_resume_session', new_callable=AsyncMock) as mock_handle_resume, \
         patch.object(AILoop, '_handle_send_user_message', new_callable=AsyncMock) as mock_handle_send_user, \
         patch.object(AILoop, '_handle_provide_tool_result', new_callable=AsyncMock) as mock_handle_tool_result:

        ai_loop_instance = AILoop(
            config=mock_ai_config_fixture,
            ai_service=mock_ai_service_fixture,
            context_manager=context_manager_fixture,
            delegate_manager=delegate_manager_fixture
        )
        sender_obj = object()

        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.start", initial_prompt="Start via delegate")
        mock_handle_start.assert_called_once_with(sender=sender_obj, initial_prompt="Start via delegate")

        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.stop")
        mock_handle_stop.assert_called_once_with(sender=sender_obj)

        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.pause")
        mock_handle_pause.assert_called_once_with(sender=sender_obj)

        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.resume")
        mock_handle_resume.assert_called_once_with(sender=sender_obj)

        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.send_user_message", message="Message via delegate")
        mock_handle_send_user.assert_called_once_with(sender=sender_obj, message="Message via delegate")

        tool_result_data = {"role": "tool", "tool_call_id": "t1", "content": "Tool result via delegate"}
        await delegate_manager_fixture.invoke_control(sender_obj, "ai_loop.control.provide_tool_result", result=tool_result_data)
        mock_handle_tool_result.assert_called_once_with(sender=sender_obj, result=tool_result_data)

    await cleanup_tasks()
