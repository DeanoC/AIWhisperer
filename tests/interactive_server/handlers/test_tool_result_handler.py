import pytest
import json
import os
from fastapi.testclient import TestClient

def get_app():
    import importlib.util
    import os
    main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../interactive_server/main.py'))
    spec = importlib.util.spec_from_file_location('interactive_server.main', main_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app

@pytest.fixture(scope="module")
def interactive_app():
    return get_app()

def watchdog_recv(websocket, timeout=5):
    import threading
    result = [None]
    exc = [None]
    def target():
        try:
            result[0] = websocket.receive_text()
        except Exception as e:
            exc[0] = e
    t = threading.Thread(target=target)
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError(f"WebSocket receive_text timed out after {timeout} seconds")
    if exc[0]:
        raise exc[0]
    return result[0]

@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", 
                    reason="Socket resource warning in CI with tool registry")
def test_tool_result_flow_real(interactive_app):
    # Register a mock tool before starting the session
    from ai_whisperer.tools.tool_registry import get_tool_registry
    from ai_whisperer.tools.base_tool import AITool
    from unittest.mock import patch, AsyncMock

    class MockTool(AITool):
        @property
        def name(self):
            return "mock_tool"
        @property
        def description(self):
            return "A mock tool for integration test."
        @property
        def parameters_schema(self):
            return {"type": "object", "properties": {"arg1": {"type": "string"}}}
        def get_ai_prompt_instructions(self):
            return "Use this tool for testing."
        def execute(self, arguments):
            return f"mock_tool executed with {arguments}"

    tool_registry = get_tool_registry()
    tool_registry._registered_tools.clear()  # Ensure clean state
    tool_registry.register_tool(MockTool())

    # Patch OpenRouterAIService.stream_chat_completion to yield a tool call for 'tool:run'
    async def fake_stream_chat_completion(self, messages, tools=None, **kwargs):
        # Simulate a tool call chunk
        from ai_whisperer.ai_service.ai_service import AIStreamChunk
        if messages[-1]["content"] == "tool:run":
            yield AIStreamChunk(
                delta_content=None,
                delta_tool_call_part='[{"id": "call-1", "type": "function", "function": {"name": "mock_tool", "arguments": "{\"arg1\": \"value1\"}"}}]',
                finish_reason="tool_calls"
            )
        # Simulate final assistant message after tool result
        yield AIStreamChunk(
            delta_content="Result is 42.",
            delta_tool_call_part=None,
            finish_reason="stop"
        )

        with patch("ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService.stream_chat_completion", new=fake_stream_chat_completion):
            client = TestClient(interactive_app)
            with client.websocket_connect("/ws") as websocket:
                # Start a session
                req = {"jsonrpc": "2.0", "id": 1, "method": "startSession", "params": {"userId": "u", "sessionParams": {"language": "en"}}}
                websocket.send_text(json.dumps(req))
                messages = [json.loads(watchdog_recv(websocket)), json.loads(watchdog_recv(websocket))]
                response = next((m for m in messages if m.get("result") and "sessionId" in m["result"]), None)
                session_id = response["result"]["sessionId"]
                # Send a user message that triggers a tool call (simulate with a special message)
                user_msg = {"jsonrpc": "2.0", "id": 2, "method": "sendUserMessage", "params": {"sessionId": session_id, "message": "tool:run"}}
                websocket.send_text(json.dumps(user_msg))


                # Log and collect all messages until we see ToolCallNotification or hit a limit
                from ai_whisperer.logging_custom import log_event, LogMessage, LogLevel, ComponentType
                received = []
                for _ in range(10):
                    msg = json.loads(watchdog_recv(websocket))
                    received.append(msg)
                    log_event(
                        LogMessage(
                            level=LogLevel.DEBUG,
                            component=ComponentType.USER_INTERACTION,
                            action="websocket_message",
                            event_summary=f"WebSocket message: {msg}",
                            details={"message": msg}
                        ),
                        logger_name="aiwhisperer"
                    )
                    if msg.get("method") == "ToolCallNotification":
                        notif = msg
                        break
                else:
                    raise AssertionError(f"Did not receive ToolCallNotification. Messages: {received}")

                tool_call_id = notif["params"]["toolCallId"]
                # Provide a tool result
                result_req = {"jsonrpc": "2.0", "id": 3, "method": "provideToolResult", "params": {"sessionId": session_id, "toolCallId": tool_call_id, "result": "42"}}
                websocket.send_text(json.dumps(result_req))
                # Should receive a response for provideToolResult
                result_resp = json.loads(watchdog_recv(websocket))
                assert result_resp["result"]["status"] == 0
                # Should receive a final AIMessageChunkNotification
                final_notif = json.loads(watchdog_recv(websocket))
                assert final_notif["method"] == "AIMessageChunkNotification"
                assert final_notif["params"]["isFinal"] is True
