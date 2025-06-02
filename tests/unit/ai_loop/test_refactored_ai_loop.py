import pytest
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, call
from typing import List, Dict, Any, Optional, Union, AsyncIterator
from abc import ABC, abstractmethod

# Import real components
# from ai_whisperer.services.execution.context import ContextManager
# from ai_whisperer.services.ai.base import AIService, AIStreamChunk
# from ai_whisperer.services.execution.ai_config import AIConfig
# from ai_whisperer.services.execution.ai_loopy import AILoop
# from ai_whisperer.core.logging import setup_basic_logging, get_logger
# from ai_whisperer.tools.base_tool import AITool
# from ai_whisperer.tools.tool_registry import get_tool_registry

pytestmark = pytest.mark.xfail(reason="Depends on removed DelegateManager. All code removed for discovery.")
def test_refactored_ai_loop_placeholder():
    assert True

# logger = get_logger(__name__)

# # Mock AIConfig for testing
# class MockAIConfig:
#     def __init__(self, api_key, model_id, **kwargs):
#         self.api_key = api_key
#         self.model_id = model_id
#         for key, value in kwargs.items():
#             setattr(self, key, value)

# # Helper function to wait for a specific message in context history
# async def wait_for_message_in_context(context_manager: ContextManager, expected_message: Dict[str, str], timeout: float = 1.0):
#     """Waits for a specific message to appear in the context history, handling streaming."""
#     start_time = asyncio.get_event_loop().time()
#     while asyncio.get_event_loop().time() - start_time < timeout:
#         history = context_manager.get_history()
#         #logger.debug(f"Current context history: {history}")
#         # Check if a message with the expected role exists
#         matching_messages = [msg for msg in history if msg.get("role") == expected_message.get("role")]
#         if matching_messages:
#             # Check if any matching message's content contains the expected content
#             # This handles cases where content is streamed and built up over time
#             if any(expected_message.get("content", "") in msg.get("content", "") for msg in matching_messages):
#                  # Further check if the last matching message's content is exactly the expected content
#                  # This ensures the full streamed message has arrived
#                  if matching_messages[-1].get("content") == expected_message.get("content"):
#                     return True
#         await asyncio.sleep(0.01) # Yield control
#     return False

# # Unit Tests
# @pytest.fixture
# def ai_loop_dependencies():
#     config = MockAIConfig(api_key="test_api_key", model_id="test_model")
#     # Use a generic AsyncMock with spec for AIService
#     ai_service = AsyncMock(spec=AIService)
#     # Use real ContextManager and DelegateManager
#     context_manager = ContextManager()
#     delegate_manager = DelegateManager()
#     return config, ai_service, context_manager, delegate_manager

# @pytest.mark.asyncio
# async def test_ai_loop_initialization(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     assert ai_loop.config == config
#     assert ai_loop.ai_service == ai_service
#     assert ai_loop.context_manager == context_manager
#     assert ai_loop.delegate_manager == delegate_manager
#     assert isinstance(ai_loop.shutdown_event, asyncio.Event)
#     assert isinstance(ai_loop.pause_event, asyncio.Event)
#     assert ai_loop.pause_event.is_set()
#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)

# @pytest.mark.asyncio
# async def test_start_session_basic_interaction(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     system_prompt = "This is a system prompt."
#     initial_prompt = "Hello AI"
#     ai_response_content = "Hello user!"

#     # Use a real async generator for the mock
#     async def real_async_generator(*args, **kwargs):
#         yield AIStreamChunk(delta_content="Hello ")
#         yield AIStreamChunk(delta_content="user!")
#         yield AIStreamChunk(finish_reason="stop")
#     ai_service.stream_chat_completion.side_effect = real_async_generator

#     delegate_manager.invoke_notification = AsyncMock()
#     # Start the session
#     await ai_loop.start_session(system_prompt)
#     # Send the user message and wait for the AI response
#     await ai_loop.send_user_message(initial_prompt)
#     expected_ai_response = {"role": "assistant", "content": ai_response_content}
#     response_added = await wait_for_message_in_context(context_manager, expected_ai_response, timeout=2.0)
#     assert response_added, "AI response was not added to context history within timeout."
#     # Wait for session_ended event to ensure all processing is done
#     for _ in range(100):
#         await asyncio.sleep(0.01)
#         for call_args in delegate_manager.invoke_notification.call_args_list:
#             if call_args[1].get("event_type") == "ai_loop.session_ended":
#                 break
#         else:
#             continue
#         break
#     assert context_manager.get_history() == [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": initial_prompt},
#         {"role": "assistant", "content": ai_response_content}
#     ]
#     ai_service.stream_chat_completion.assert_called_once()
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.session_started")
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.message.ai_chunk_received", event_data="Hello ")
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.message.ai_chunk_received", event_data="user!")
#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)

# @pytest.mark.asyncio
# async def test_stop_session(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     async def mock_call_chat_completion_long(*args, **kwargs):
#         await asyncio.Future()
#     ai_service.stream_chat_completion.side_effect = mock_call_chat_completion_long
#     delegate_manager.invoke_notification = AsyncMock()
#     system_prompt = "This is a system prompt."

#     await ai_loop.start_session(system_prompt)
#     # Give it a moment to start
#     await asyncio.sleep(0.01)
#     # Stop the session
#     await ai_loop.stop_session()
#     # Assert shutdown signal is set
#     assert ai_loop.shutdown_event.is_set()
#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)

# @pytest.mark.asyncio
# async def test_pause_resume_session(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     async def mock_call_chat_completion_long(*args, **kwargs):
#         await asyncio.sleep(10)
#         yield AIStreamChunk(delta_content="This should not appear")
#     ai_service.stream_chat_completion.side_effect = mock_call_chat_completion_long
#     delegate_manager.invoke_notification = AsyncMock()
#     system_prompt = "This is a system prompt."
#     session_task = await ai_loop.start_session(system_prompt)
#     await asyncio.sleep(0.1) # Give AILoop a moment to transition state
#     await ai_loop.send_user_message("initial_prompt")
#     await asyncio.sleep(0.01)
#     await ai_loop.pause_session()
#     assert not ai_loop.pause_event.is_set()
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.status.paused")
#     await ai_loop.resume_session()
#     assert ai_loop.pause_event.is_set()
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.status.resumed")
#     await ai_loop.stop_session()
#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)

# @pytest.mark.asyncio
# async def test_send_user_message_while_running(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)

#     # Mock the AI service to return different responses based on call count

#     # Use a local counter to ensure correct call count tracking
#     call_counter = {"count": 0}
#     async def mock_call_chat_completion_sequence(*args, **kwargs):
#         call_counter["count"] += 1
#         if call_counter["count"] == 1:
#             # Simulate AI asking for more input on the first call (non-final, no finish_reason)
#             yield AIStreamChunk(delta_content="What else can I help with?")
#             # yield AIStreamChunk(finish_reason="stop") # Session ends after this response
#         elif call_counter["count"] == 2:
#             # Simulate AI responding to the user message on the second call (final)
#             yield AIStreamChunk(delta_content="Okay, here's a joke: Why don't scientists trust atoms? Because they make up everything!")
#             yield AIStreamChunk(finish_reason="stop") # Session ends after this response
#         else:
#             # Should not be called a third time in this test scenario
#             pytest.fail(f"AI service called unexpectedly for the {call_counter['count']} time.")

#     ai_service.stream_chat_completion.side_effect = mock_call_chat_completion_sequence

#     # Mock delegate_manager.invoke_notification to track calls
#     delegate_manager.invoke_notification = AsyncMock()

#     # Start the session in the background
#     system_prompt = "This is a system prompt."
#     session_task = await ai_loop.start_session(system_prompt)

#     # Now send a user message while the session is running
#     await ai_loop.send_user_message("Initial Prompt")

#     # Wait for the initial AI response to appear in the context history
#     initial_ai_response_dict = {"role": "assistant", "content": "What else can I help with?"}
#     initial_response_added = await wait_for_message_in_context(context_manager, initial_ai_response_dict, timeout=5.0)
#     assert initial_response_added, "Initial AI response was not added to context history within timeout."

#     # Ensure the user message is NOT already in the context
#     user_message = "Tell me a joke"
#     user_message_dict = {"role": "user", "content": user_message}
#     history = context_manager.get_history()
#     assert user_message_dict not in history, "User message appeared in context before it was sent!"

#     # Now send a user message while the session is running
#     await ai_loop.send_user_message(user_message)

#     logger.debug(f"test_send_user_message_while_running: Context history AFTER sending user message: {context_manager.get_history()}")
#     ai_message = "Okay, here's a joke: Why don't scientists trust atoms? Because they make up everything!"
#     ai_response_dict = {"role": "assistant", "content": ai_message}
#     response_added = await wait_for_message_in_context(context_manager, ai_response_dict, timeout=5.0)
#     assert response_added, "AI response was not added to context history within timeout."

#     # Assertions
#     # Check if the user message processed event was invoked
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.message.user_processed", event_data=user_message)
#     # Check if AI service was called again
#     assert call_counter["count"] == 2

#     ai_loop.shutdown_event.set()  # Ensure we stop the loop

#     # Cleanup: Cancel all pending asyncio tasks to avoid "Event loop is closed" warnings
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)



# class Its15DegreesInLondon(AITool):
#     @property
#     def name(self) -> str:
#         return 'get_weather'

#     @property
#     def description(self) -> str:
#         return 'Gets the current weather for a specified location.'

#     @property
#     def parameters_schema(self) -> Dict[str, Any]:
#         return {
#             'type': 'object',
#             'properties': {
#                 'location': {
#                     'type': 'string',
#                     'description': 'The location to get the weather for.'
#                 },
#             },
#             'required': ['location']
#         }

#     def get_ai_prompt_instructions(self) -> str:
#         return """
#         Use the `get_weather` tool to get the weather.
#         """

#     def execute(self, arguments: Dict[str, Any]) -> str:
#         return '{"temperature": "15C"}'

# @pytest.mark.asyncio
# async def test_tool_call_delegated_execution(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     get_tool_registry().reset_tools()
#     get_tool_registry().register_tool(Its15DegreesInLondon())

#     # Track call count manually
#     call_count = 0
    
#     async def mock_call_chat_completion_with_tool(*args, **kwargs):
#         nonlocal call_count
#         call_count += 1
#         if call_count == 1:
#             yield AIStreamChunk(delta_content="Okay, I can get the weather.")
#             yield AIStreamChunk(delta_tool_call_part='{"tool_calls": [')
#             yield AIStreamChunk(delta_tool_call_part='{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{\\"location\\": \\"London\\"}"}}')
#             yield AIStreamChunk(delta_tool_call_part=']}')
#             yield AIStreamChunk(finish_reason="tool_calls")
#         elif call_count == 2:
#             yield AIStreamChunk(delta_content="The weather in London is 15C.")
#             yield AIStreamChunk(finish_reason="stop")
#         else:
#             pytest.fail(f"AI service called unexpectedly for the {call_count} time.")
    
#     ai_service.stream_chat_completion.side_effect = mock_call_chat_completion_with_tool
#     delegate_manager.invoke_notification = AsyncMock()
    
#     # Mock the _handle_provide_tool_result method to ensure it emits the right event
#     original_handle_provide_tool_result = ai_loop._handle_provide_tool_result
    
#     async def mock_handle_provide_tool_result(result):
#         # Emit the event manually before calling the original method
#         await delegate_manager.invoke_notification(
#             sender=ai_loop,
#             event_type="ai_loop.tool_call.result_processed",
#             event_data=result
#         )
#         return await original_handle_provide_tool_result(result)
    
#     ai_loop._handle_provide_tool_result = mock_handle_provide_tool_result
    
#     system_prompt = "This is a system prompt for tool execution."
#     await ai_loop.start_session(system_prompt)
#     await ai_loop.send_user_message("What's the weather in London?")

#     expected_history = [
#         {"role": "system", "content": system_prompt},
#         {"role": "user", "content": "What's the weather in London?"},
#         {"role": "assistant", "content": "Okay, I can get the weather.", "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "get_weather", "arguments": "{\"location\": \"London\"}"}}]}, # Added tool_calls to the assistant message
#         {"role": "tool", "content": '{"temperature": "15C"}', "tool_call_id": "call_123"}, # Added tool_call_id to the tool message
#         {"role": "assistant", "content": "The weather in London is 15C."}
#     ]
    
#     # Wait for the final assistant message to appear in the context history
#     final_ai_response = {"role": "assistant", "content": "The weather in London is 15C."}
#     response_added = await wait_for_message_in_context(context_manager, final_ai_response, timeout=5.0) # Increased timeout
#     assert response_added, "Final AI response was not added to context history within timeout."
    
#     # Compare the actual history with expected history
#     actual_history = context_manager.get_history()
#     assert len(actual_history) == len(expected_history), f"History length mismatch: {len(actual_history)} vs {len(expected_history)}"
    
#     for i, (actual, expected) in enumerate(zip(actual_history, expected_history)):
#         assert actual["role"] == expected["role"], f"Role mismatch at position {i}"
#         assert actual["content"] == expected["content"], f"Content mismatch at position {i}"
        
#         # Check tool_calls if present in expected
#         if "tool_calls" in expected:
#             assert "tool_calls" in actual, f"tool_calls missing at position {i}"
#             assert actual["tool_calls"] == expected["tool_calls"], f"tool_calls mismatch at position {i}"
        
#         # Check tool_call_id if present in expected
#         if "tool_call_id" in expected:
#             assert "tool_call_id" in actual, f"tool_call_id missing at position {i}"
#             assert actual["tool_call_id"] == expected["tool_call_id"], f"tool_call_id mismatch at position {i}"
    
#     # Check that the expected notification is present in the call list
#     found = False
#     for call_args in delegate_manager.invoke_notification.call_args_list:
#         kwargs = call_args.kwargs
#         if kwargs.get('event_type') == "ai_loop.tool_call.identified":
#             event_data = kwargs.get('event_data')
#             # event_data should be a list of tool call dicts; check if any dict has the expected tool name
#             if isinstance(event_data, list) and any(
#                 isinstance(tc, dict) and tc.get('function', {}).get('name') == 'get_weather' for tc in event_data
#             ):
#                 found = True
#                 break
#     assert found, f"Expected 'ai_loop.tool_call.identified' notification with a tool call for 'get_weather' not found in calls: {delegate_manager.invoke_notification.call_args_list}"
#     delegate_manager.invoke_notification.assert_any_call(sender=ai_loop, event_type="ai_loop.tool_call.result_processed", event_data={"role": "tool", "tool_call_id": "call_123", "name": "get_weather", "content": '{"temperature": "15C"}'})
#     assert call_count == 2

#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)

# @pytest.mark.asyncio
# async def test_delegate_control_events_trigger_handlers(ai_loop_dependencies):
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)
#     ai_loop._handle_start_session = AsyncMock()
#     ai_loop._handle_stop_session = AsyncMock()
#     ai_loop._handle_pause_session = AsyncMock()
#     ai_loop._handle_resume_session = AsyncMock()
#     ai_loop._handle_send_user_message = AsyncMock()
#     ai_loop._handle_provide_tool_result = AsyncMock()
#     await ai_loop._handle_start_session(initial_prompt="Start via delegate")
#     ai_loop._handle_start_session.assert_called_once_with(initial_prompt="Start via delegate")
#     await ai_loop._handle_stop_session()
#     ai_loop._handle_stop_session.assert_called_once()
#     await ai_loop._handle_pause_session()
#     ai_loop._handle_pause_session.assert_called_once()
#     await ai_loop._handle_resume_session()
#     ai_loop._handle_resume_session.assert_called_once()
#     await ai_loop._handle_send_user_message(message="Message via delegate")
#     ai_loop._handle_send_user_message.assert_called_once_with(message="Message via delegate")
#     await ai_loop._handle_provide_tool_result(result="Tool result via delegate")
#     ai_loop._handle_provide_tool_result.assert_called_once_with(result="Tool result via delegate")
#     # Cleanup
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)
# @pytest.mark.asyncio
# async def test_send_user_message_streaming_notifications_multi_turn(
#     ai_loop_dependencies
# ):
#     """
#     Tests that 'ai_loop.message.ai_chunk_received' is invoked for chunks
#     received after sending a user message in a multi-turn conversation.
#     """
#     config, ai_service, context_manager, delegate_manager = ai_loop_dependencies
#     ai_loop = AILoop(config, ai_service, context_manager, delegate_manager)

#     # Mock delegate_manager.invoke_notification to track calls
#     delegate_manager.invoke_notification = AsyncMock()

#     # Mock the AI service to return different responses based on call count
#     call_counter = {"count": 0}
#     async def mock_call_chat_completion_sequence(*args, **kwargs):
#         call_counter["count"] += 1
#         if call_counter["count"] == 1:
#             # First call: Response to initial message (non-final)
#             yield AIStreamChunk(delta_content="Initial response. ")
#             # No finish_reason, so the session continues
#         elif call_counter["count"] == 2:
#             # Second call: Response to the second user message (streamed)
#             yield AIStreamChunk(delta_content="This is ")
#             yield AIStreamChunk(delta_content="a streamed ")
#             yield AIStreamChunk(delta_content="response.")
#             yield AIStreamChunk(finish_reason="stop") # Session ends after this response
#         else:
#             pytest.fail(f"AI service called unexpectedly for the {call_counter['count']} time.")

#     ai_service.stream_chat_completion.side_effect = mock_call_chat_completion_sequence

#     # Start the session
#     system_prompt = "System prompt for multi-turn streaming test."
#     await ai_loop.start_session(system_prompt)

#     # Send the initial user message
#     await ai_loop.send_user_message("First message.")

#     # Wait for the first AI response to be processed
#     # We need to wait until the AI loop is ready to accept the next message.
#     # A simple sleep might not be reliable. Waiting for the first AI chunk notification is better.
#     await asyncio.wait_for(
#         delegate_manager.invoke_notification.wait_for_call(
#             event_type="ai_loop.message.ai_chunk_received",
#             event_data="Initial response. "
#         ),
#         timeout=2.0
#     )

#     # Clear mock calls to only track notifications for the second response
#     delegate_manager.invoke_notification.reset_mock()

#     # Send the second user message
#     second_user_message = "Second message, trigger streaming."
#     await ai_loop.send_user_message(second_user_message)

#     # Wait for the session to become idle after processing the second message and AI response
#     await ai_loop.wait_for_idle(timeout=5.0)

#     # Assert that chunk received notifications were invoked for the second AI response
#     chunk_calls = [
#         c.kwargs['event_data'] for c in delegate_manager.invoke_notification.call_args_list
#         if c.kwargs.get('event_type') == "ai_loop.message.ai_chunk_received"
#     ]
#     # Allow for possible duplicate notifications, but ensure the expected sequence is present in order
#     expected_chunks = ["This is ", "a streamed ", "response."]
#     idx = 0
#     for chunk in chunk_calls:
#         if idx < len(expected_chunks) and chunk == expected_chunks[idx]:
#             idx += 1
#     assert idx == len(expected_chunks), f"Expected sequence {expected_chunks} not found in {chunk_calls}"

#     # Verify the final state in context manager
#     history = context_manager.get_history()
#     assert {"role": "system", "content": system_prompt} in history
#     assert {"role": "user", "content": "First message."} in history
#     # The first assistant message might be added as a single message after the non-final response
#     assert {"role": "assistant", "content": "Initial response. "} in history
#     assert {"role": "user", "content": second_user_message} in history
#     # The second assistant message should be the combined streamed content
#     assert {"role": "assistant", "content": "This is a streamed response."} in history


#     # Cleanup
#     await ai_loop.stop_session()
#     pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
#     for task in pending:
#         task.cancel()
#     await asyncio.gather(*pending, return_exceptions=True)