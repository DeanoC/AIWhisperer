

import pytest
import asyncio
import websockets
import json
from ai_whisperer.logging_custom import get_test_logger

logger = get_test_logger()

async def recv_until(ws, match_id=None, timeout=5):
    """
    Receive messages from ws until a message with 'id' == match_id is found (or any response if match_id is None).
    Returns the matching message, or raises asyncio.TimeoutError.
    """
    import time
    start = time.monotonic()
    while True:
        if time.monotonic() - start > timeout:
            raise asyncio.TimeoutError(f"Timeout waiting for response with id={match_id}")
        msg = await ws.recv()
        data = json.loads(msg)
        logger.info(f"recv_until: got message: {data}")
        if match_id is None or data.get("id") == match_id:
            return data

WS_URL = "ws://localhost:8000/ws"

@pytest.mark.asyncio
async def test_agent_list_ws():
    logger.info("Starting test_agent_list_ws")
    async with websockets.connect(WS_URL) as ws:
        req = {"jsonrpc": "2.0", "id": 1, "method": "agent.list", "params": {}}
        await ws.send(json.dumps(req))
        data = await recv_until(ws, match_id=1)
        logger.info(f"agent.list response: {data}")
        assert data["result"]
        assert "agents" in data["result"]
        assert any(a["agent_id"] == "P" for a in data["result"]["agents"])

@pytest.mark.asyncio
async def test_session_switch_agent_ws():
    logger.info("Starting test_session_switch_agent_ws")
    async with websockets.connect(WS_URL) as ws:
        req = {"jsonrpc": "2.0", "id": 2, "method": "session.switch_agent", "params": {"agent_id": "T"}}
        await ws.send(json.dumps(req))
        data = await recv_until(ws, match_id=2)
        logger.info(f"session.switch_agent response: {data}")
        assert data["result"]["success"]
        assert data["result"]["current_agent"] == "T"

@pytest.mark.asyncio
async def test_session_current_agent_ws():
    logger.info("Starting test_session_current_agent_ws")
    async with websockets.connect(WS_URL) as ws:
        req = {"jsonrpc": "2.0", "id": 3, "method": "session.current_agent", "params": {}}
        await ws.send(json.dumps(req))
        data = await recv_until(ws, match_id=3)
        logger.info(f"session.current_agent response: {data}")
        assert "current_agent" in data["result"]

@pytest.mark.asyncio
async def test_session_handoff_ws():
    logger.info("Starting test_session_handoff_ws")
    async with websockets.connect(WS_URL) as ws:
        req = {"jsonrpc": "2.0", "id": 4, "method": "session.handoff", "params": {"to_agent": "T"}}
        await ws.send(json.dumps(req))
        data = await recv_until(ws, match_id=4)
        logger.info(f"session.handoff response: {data}")
        assert data["result"]["success"]
        assert data["result"]["to_agent"] == "T"
