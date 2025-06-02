

import asyncio
import json
import pytest
import websockets
import time
import os
from unittest.mock import patch
from tests.interactive_server.performance_metrics_utils import MetricsCollector
from ai_whisperer.core.logging import LogMessage, LogLevel, ComponentType


def log_event(message, logger_name="aiwhisperer"):
    """Simple log function for tests"""
    import logging
    logger = logging.getLogger(logger_name)
    if message.level == LogLevel.DEBUG:
        logger.debug(message.event_summary)
    elif message.level == LogLevel.INFO:
        logger.info(message.event_summary)
    elif message.level == LogLevel.WARNING:
        logger.warning(message.event_summary)
    elif message.level == LogLevel.ERROR:
        logger.error(message.event_summary)
    elif message.level == LogLevel.CRITICAL:
        logger.critical(message.event_summary)

import pytest
@pytest.mark.performance
@pytest.mark.asyncio
@pytest.mark.xfail(reason="Known failure: see test run 2025-05-30, CI error", strict=False)
async def test_ai_service_timeout_handling(start_interactive_server):
    """
    Simulate an AI service timeout by sending a message that triggers a long-running operation.
    The server should handle the timeout gracefully and notify the client.
    """
    WATCHDOG_TIMEOUT = 40  # seconds (test will fail if it takes longer)

    async def inner():
        uri = "ws://127.0.0.1:8000/ws"
        session_id = None
        msg_id = 1
        metrics = MetricsCollector(csv_path="ai_service_timeout_metrics.csv")
        received_messages = []
        log_path = os.path.join("logs", "aiwhisperer_debug.log")
        
        # Mock the OpenRouterAIService to bypass API key requirement for timeout test
        from ai_whisperer.services.execution.ai_config import AIConfig
        
        def mock_init(self, config=None, shutdown_event=None):
            # Bypass API key validation for test
            self.api_key = "test_key"  # Mock API key
            self.model = getattr(config, 'model_id', 'test_model')
            self.params = {
                "temperature": getattr(config, 'temperature', 0.7),
                "max_tokens": getattr(config, 'max_tokens', 100),
            }
            self.shutdown_event = shutdown_event
            self._last_input_tokens = None
            self._last_output_tokens = None
            self.site_url = getattr(config, "site_url", "http://AIWhisperer:8000")
        
        try:
            with patch("ai_whisperer.services.ai.openrouter.OpenRouterAIService.__init__", mock_init):
                async with websockets.connect(uri) as websocket:
                    # Start session
                    start_req = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "method": "startSession",
                        "params": {"userId": "timeout_user", "sessionParams": {"language": "en"}}
                    }
                    metrics.start_timer("start_session")
                    await websocket.send(json.dumps(start_req))
                    msg_id += 1
                    # Wait for sessionId
                    for _ in range(10):
                        msg = json.loads(await websocket.recv())
                        received_messages.append(msg)
                        log_event(LogMessage(
                            level=LogLevel.DEBUG,
                            component=ComponentType.USER_INTERACTION,
                            action="websocket_message",
                            event_summary=f"WebSocket message: {msg}",
                            details={"message": msg}
                        ), logger_name="aiwhisperer")
                        if msg.get("result") and msg["result"].get("sessionId"):
                            session_id = msg["result"]["sessionId"]
                            metrics.stop_timer("start_session")
                            break
                    assert session_id, "Session ID not received."
                    # Send a message that should trigger a timeout (server must be configured to simulate this)
                    user_msg = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "method": "sendUserMessage",
                        "params": {"sessionId": session_id, "message": "simulate_timeout"}
                    }
                    metrics.start_timer("timeout_trigger")
                    await websocket.send(json.dumps(user_msg))
                    msg_id += 1
                    # Wait for error notification or timeout response
                    got_timeout = False
                    for _ in range(20):
                        try:
                            msg = json.loads(await websocket.recv())
                            received_messages.append(msg)
                            log_event(LogMessage(
                                level=LogLevel.DEBUG,
                                component=ComponentType.USER_INTERACTION,
                                action="websocket_message",
                                event_summary=f"WebSocket message: {msg}",
                                details={"message": msg}
                            ), logger_name="aiwhisperer")
                        except websockets.ConnectionClosed:
                            # Connection closed by server, break and check what we received
                            break
                        if msg.get("method") == "SessionStatusNotification" and "timeout" in str(msg["params"]):
                            got_timeout = True
                            metrics.stop_timer("timeout_trigger")
                            break
                        if msg.get("method") == "ErrorNotification" and "timeout" in str(msg["params"]):
                            got_timeout = True
                            metrics.stop_timer("timeout_trigger")
                            break
                        await asyncio.sleep(0.2)
                    if not got_timeout:
                        metrics.record_error("no_timeout_notification")
                    assert got_timeout, "No timeout notification received from server."
                    metrics.save()
        except Exception as e:
            # On failure, print last 30 lines of server log for debugging
            print(f"\n[TEST FAILURE] Exception: {e}")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    print("\n[SERVER LOG TAIL]")
                    print("".join(lines[-30:]))
            raise

    try:
        await asyncio.wait_for(inner(), timeout=WATCHDOG_TIMEOUT)
    except asyncio.TimeoutError:
        pytest.fail(f"Test exceeded watchdog timeout of {WATCHDOG_TIMEOUT} seconds (possible hang)")
