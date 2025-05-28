import pytest
import asyncio
import json
from interactive_server.session_manager import InteractiveSessionManager, InteractiveSession
from interactive_server.main import process_json_rpc_request, handle_websocket_message # Import the actual handler functions
from ai_whisperer.agents.agent import Agent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.context.provider import ContextProvider
from unittest.mock import AsyncMock, MagicMock

# Mock WebSocket connection for testing
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def send_text(self, message: str):
        self.sent_messages.append(message)

    async def receive_text(self):
        # For testing purposes, we might need to simulate incoming messages
        # This can be extended as needed for specific test cases
        return "simulated_client_message"

    async def close(self):
        self.closed = True

@pytest.fixture
async def setup_session_components():
    mock_config = {"agent": {"preset_name": "default"}} # Mock config for SessionManager
    session_manager = InteractiveSessionManager(mock_config)
    context_provider = ContextProvider() # This is not used in main.py, but might be needed for other tests
    # We will directly use process_json_rpc_request and handle_websocket_message
    yield session_manager, context_provider, process_json_rpc_request, handle_websocket_message
    # Cleanup: Ensure all sessions are closed
    for session_id in list(session_manager.sessions.keys()):
        await session_manager.cleanup_session(session_id) # Use cleanup_session

@pytest.fixture
def mock_agent_config():
    return AgentConfig(
        name="test_agent",
        model="mock_model",
        description="A mock agent for testing.",
        tools=[]
    )

@pytest.fixture
def mock_agent(mock_agent_config):
    agent = Agent(mock_agent_config)
    agent.run_ai_loop = AsyncMock(return_value="Agent response")
    return agent

@pytest.fixture
def mock_interactive_session(mock_agent):
    # InteractiveSession now expects session_id, websocket, and config
    mock_config = {"agent": {"preset_name": "default"}}
    session = InteractiveSession(
        session_id="test_session_id",
        websocket=MockWebSocket(),
        config=mock_config
    )
    # Manually set the agent for the mock session for testing purposes
    session.agents["default"] = mock_agent
    session.active_agent = mock_agent
    session.is_started = True # Mark as started for tests that expect it
    return session

class TestSessionIntegration:

    async def test_multi_agent_conversation_workflow(self, setup_session_components, mock_agent_config):
        session_manager, context_provider, process_json_rpc_request_func, handle_websocket_message_func = setup_session_components
        mock_ws = MockWebSocket()

        # Simulate session creation
        session_id = "conv_session_1"
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/start",
            "params": {"session_id": session_id, "agent_config": mock_agent_config.to_dict()},
            "id": 1
        }, websocket=mock_ws)
        assert response["result"]["sessionId"] == session_id
        assert session_id in session_manager.sessions
        session = session_manager.sessions[session_id]
        session.agent.run_ai_loop = AsyncMock(return_value="Agent 1 response")

        # Simulate first agent message
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": session_id, "message": "Hello from user"},
            "id": 2
        }, websocket=mock_ws)
        # The actual agent response is sent as a notification, not directly in the response to send_message
        # We need to check mock_ws.sent_messages for the notification
        assert any("Agent 1 response" in msg for msg in mock_ws.sent_messages)

        # Simulate agent switching and second agent message
        mock_agent_config_2 = AgentConfig(
            name="test_agent_2",
            model="mock_model_2",
            description="Another mock agent.",
            tools=[]
        )
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/switch_agent",
            "params": {"session_id": session_id, "agent_config": mock_agent_config_2.to_dict()},
            "id": 3
        }, websocket=mock_ws)
        assert response["result"]["success"] == True
        session.agent.run_ai_loop = AsyncMock(return_value="Agent 2 response")
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": session_id, "message": "Continue conversation"},
            "id": 4
        }, websocket=mock_ws)
        assert any("Agent 2 response" in msg for msg in mock_ws.sent_messages)

        # Simulate session end
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/end",
            "params": {"session_id": session_id},
            "id": 5
        }, websocket=mock_ws)
        assert response["result"]["status"] == "Stopped"
        assert session_id not in session_manager.sessions

    async def test_session_persistence_and_recovery(self, setup_session_components, mock_agent_config):
        session_manager, context_provider, process_json_rpc_request_func, handle_websocket_message_func = setup_session_components
        mock_ws = MockWebSocket()
        session_id = "persistence_session_1"

        # Start a session and send a message
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/start",
            "params": {"session_id": session_id, "agent_config": mock_agent_config.to_dict()},
            "id": 1
        }, websocket=mock_ws)
        assert response["result"]["sessionId"] == session_id
        assert session_id in session_manager.sessions
        session = session_manager.sessions[session_id]
        session.agent.run_ai_loop = AsyncMock(return_value="Initial agent response")
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": session_id, "message": "Message for persistence"},
            "id": 2
        }, websocket=mock_ws)
        assert any("Initial agent response" in msg for msg in mock_ws.sent_messages)

        # Simulate server shutdown (session manager clears sessions, but context should persist)
        # In a real scenario, context persistence would involve saving to disk.
        # For this integration test, we'll simulate by clearing the session manager
        # and then re-initializing it, expecting the context provider to retain data.
        # This requires the ContextProvider to be able to load previous contexts.
        # For now, we'll just check if the session object itself can be "recovered"
        # by re-creating it with the same ID and expecting its internal state to be consistent.
        # This part needs more detailed implementation if context persistence is file-based.

        # For now, we'll simulate by ending the session and then trying to restart it
        # and verify if the context is reloaded or if it's a fresh start.
        # This test needs to be refined based on actual persistence mechanism.
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/end", # This method calls cleanup_session internally
            "params": {"session_id": session_id},
            "id": 3
        }, websocket=mock_ws)
        assert response["result"]["status"] == "Stopped"
        assert session_id not in session_manager.sessions

        # Simulate recovery by restarting the session with the same ID
        # This assumes the context provider would load the previous context.
        # As current ContextProvider doesn't have persistence, this will be a fresh session.
        # This test needs to be updated once persistence is implemented in ContextProvider.
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/start",
            "params": {"session_id": session_id, "agent_config": mock_agent_config.to_dict()},
            "id": 4
        }, websocket=mock_ws)
        assert response["result"]["sessionId"] == session_id
        assert session_id in session_manager.sessions
        recovered_session = session_manager.sessions[session_id]
        # Verify that the recovered session is a new instance but uses the same session_id
        assert recovered_session.session_id == session_id
        # Further assertions would depend on how context persistence is handled.

    async def test_concurrent_session_operations(self, setup_session_components, mock_agent_config):
        session_manager, context_provider, process_json_rpc_request_func, handle_websocket_message_func = setup_session_components
        mock_ws_1 = MockWebSocket()
        mock_ws_2 = MockWebSocket()
        session_id_1 = "concurrent_session_1"
        session_id_2 = "concurrent_session_2"

        # Start two sessions concurrently
        await asyncio.gather(
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/start",
                "params": {"session_id": session_id_1, "agent_config": mock_agent_config.to_dict()},
                "id": 1
            }, websocket=mock_ws_1),
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/start",
                "params": {"session_id": session_id_2, "agent_config": mock_agent_config.to_dict()},
                "id": 1
            }, websocket=mock_ws_2)
        )
        assert session_id_1 in session_manager.sessions
        assert session_id_2 in session_manager.sessions

        session_1 = session_manager.sessions[session_id_1]
        session_2 = session_manager.sessions[session_id_2]
        session_1.agent.run_ai_loop = AsyncMock(return_value="Response from session 1")
        session_2.agent.run_ai_loop = AsyncMock(return_value="Response from session 2")

        # Send messages to both sessions concurrently
        await asyncio.gather(
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/send_message",
                "params": {"session_id": session_id_1, "message": "Message for session 1"},
                "id": 2
            }, websocket=mock_ws_1),
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/send_message",
                "params": {"session_id": session_id_2, "message": "Message for session 2"},
                "id": 2
            }, websocket=mock_ws_2)
        )
        assert any("Response from session 1" in msg for msg in mock_ws_1.sent_messages)
        assert any("Response from session 2" in msg for msg in mock_ws_2.sent_messages)

        # End sessions concurrently
        await asyncio.gather(
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/end",
                "params": {"session_id": session_id_1},
                "id": 3
            }, websocket=mock_ws_1),
            process_json_rpc_request_func({
                "jsonrpc": "2.0",
                "method": "session/end",
                "params": {"session_id": session_id_2},
                "id": 3
            }, websocket=mock_ws_2)
        )
        assert session_id_1 not in session_manager.sessions
        assert session_id_2 not in session_manager.sessions

    async def test_websocket_streaming_validation(self, setup_session_components, mock_agent_config):
        session_manager, context_provider, process_json_rpc_request_func, handle_websocket_message_func = setup_session_components
        mock_ws = MockWebSocket()
        session_id = "streaming_session_1"

        # Start a session
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/start",
            "params": {"session_id": session_id, "agent_config": mock_agent_config.to_dict()},
            "id": 1
        }, websocket=mock_ws)
        assert response["result"]["sessionId"] == session_id
        session = session_manager.sessions[session_id]

        # Simulate agent streaming response
        async def mock_streaming_run_ai_loop(message: str, session_id: str, websocket: MockWebSocket):
            # The actual send_notification is called by the InteractiveSession
            # We need to mock the send_notification method of the session itself
            # to capture the streamed chunks.
            # For this test, we'll directly simulate the messages that would be sent
            # by the websocket_endpoint.
            await websocket.send_text(json.dumps({"jsonrpc": "2.0", "method": "session/stream_chunk", "params": {"sessionId": session_id, "chunk": "Streamed "}}))
            await websocket.send_text(json.dumps({"jsonrpc": "2.0", "method": "session/stream_chunk", "params": {"sessionId": session_id, "chunk": "response."}}))
            return "Streamed response."

        session.agent.run_ai_loop = AsyncMock(side_effect=mock_streaming_run_ai_loop)

        # Send a message to trigger streaming
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": session_id, "message": "Test streaming"},
            "id": 2
        }, websocket=mock_ws)

        # Verify streamed messages
        # The last message should be the final response, previous ones should be chunks
        # This requires inspecting the mock_ws.sent_messages list
        stream_chunks = [msg for msg in mock_ws.sent_messages if '"method": "session/stream_chunk"' in msg]
        assert len(stream_chunks) >= 2 # At least two chunks
        assert json.loads(stream_chunks[0])["params"]["chunk"] == "Streamed "
        assert json.loads(stream_chunks[1])["params"]["chunk"] == "response."

        # Simulate session end
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/end",
            "params": {"session_id": session_id},
            "id": 3
        }, websocket=mock_ws)
        assert response["result"]["status"] == "Stopped"
        assert session_id not in session_manager.sessions

    async def test_error_recovery_and_edge_cases(self, setup_session_components, mock_agent_config):
        session_manager, context_provider, process_json_rpc_request_func, handle_websocket_message_func = setup_session_components
        mock_ws = MockWebSocket()
        session_id = "error_session_1"

        # Test: Sending message to non-existent session
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": "non_existent_session", "message": "Hello"},
            "id": 1
        }, websocket=mock_ws)
        # Expect an error response
        assert response["error"]["code"] == -32001 # Example error code for session not found

        # Test: Agent raises an exception during run_ai_loop
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/start",
            "params": {"session_id": session_id, "agent_config": mock_agent_config.to_dict()},
            "id": 2
        }, websocket=mock_ws)
        assert response["result"]["sessionId"] == session_id
        session = session_manager.sessions[session_id]
        session.agent.run_ai_loop = AsyncMock(side_effect=Exception("Agent internal error"))

        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/send_message",
            "params": {"session_id": session_id, "message": "Trigger error"},
            "id": 3
        }, websocket=mock_ws)
        # Expect an error response from the server
        assert response["error"]["message"] == "Failed to send message: Agent internal error"

        # Verify session is still active after agent error (should not crash the session)
        assert session_id in session_manager.sessions
        # Try to end the session to ensure it's recoverable
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "session/end",
            "params": {"session_id": session_id},
            "id": 4
        }, websocket=mock_ws)
        assert response["result"]["status"] == "Stopped"
        assert session_id not in session_manager.sessions

        # Test: Invalid JSON-RPC request (using handle_websocket_message directly)
        response = await handle_websocket_message_func(mock_ws, "invalid json string")
        assert response["error"]["code"] == -32700 # Parse error

        # Test: Method not found
        response = await process_json_rpc_request_func({
            "jsonrpc": "2.0",
            "method": "nonExistentMethod",
            "params": {},
            "id": 5
        }, websocket=mock_ws)
        assert response["error"]["code"] == -32601 # Method not found