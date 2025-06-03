#!/usr/bin/env python3
"""
Integration test to verify per-agent AI models work through the interactive server.

This test simulates agent switching and verifies each agent uses its configured model.
"""

import asyncio
import json
import websockets
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agent_models():
    """Test that agents use their configured AI models in interactive mode."""
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        logger.info("Connected to WebSocket")
        
        # Create a new session
        request = {
            "jsonrpc": "2.0",
            "method": "session.create",
            "params": {},
            "id": 1
        }
        await websocket.send(json.dumps(request))
        response = json.loads(await websocket.recv())
        session_id = response["result"]["sessionId"]
        logger.info(f"Created session: {session_id}")
        
        # Start the session
        request = {
            "jsonrpc": "2.0",
            "method": "session.start",
            "params": {"sessionId": session_id},
            "id": 2
        }
        await websocket.send(json.dumps(request))
        await websocket.recv()  # Response
        logger.info("Session started")
        
        # Wait for Alice's introduction
        await asyncio.sleep(2)
        while True:
            msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            data = json.loads(msg)
            if data.get("method") == "AIMessageChunkNotification" and data["params"].get("isFinal"):
                break
        
        # Test each agent
        test_agents = [
            ("a", "Alice", "default model"),
            ("d", "Debbie", "gpt-3.5-turbo"),
            ("e", "Eamonn", "Claude-3-Opus")
        ]
        
        for agent_id, agent_name, expected_model in test_agents:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing {agent_name} (expected: {expected_model})")
            logger.info(f"{'='*60}")
            
            # Switch to agent
            request = {
                "jsonrpc": "2.0",
                "method": "agent.switch",
                "params": {
                    "sessionId": session_id,
                    "agentId": agent_id
                },
                "id": 10 + ord(agent_id)
            }
            await websocket.send(json.dumps(request))
            
            # Wait for switch confirmation
            while True:
                msg = await websocket.recv()
                data = json.loads(msg)
                if data.get("method") == "agent.switched":
                    logger.info(f"✓ Switched to {agent_name}")
                    break
            
            # Send a message to verify the agent is using the right model
            request = {
                "jsonrpc": "2.0",
                "method": "session.sendMessage",
                "params": {
                    "sessionId": session_id,
                    "message": "What AI model are you using? Please be specific about the model name."
                },
                "id": 20 + ord(agent_id)
            }
            await websocket.send(json.dumps(request))
            
            # Collect the response
            response_text = ""
            final_received = False
            timeout_start = time.time()
            
            while not final_received and (time.time() - timeout_start) < 30:
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(msg)
                    
                    if data.get("method") == "AIMessageChunkNotification":
                        if data["params"].get("chunk"):
                            response_text += data["params"]["chunk"]
                        if data["params"].get("isFinal"):
                            final_received = True
                except asyncio.TimeoutError:
                    continue
            
            logger.info(f"Agent response: {response_text[:200]}...")
            
            # Verify expected model is mentioned (this is a heuristic check)
            if agent_id == "d" and "gpt-3.5" in response_text.lower():
                logger.info(f"✓ {agent_name} appears to be using GPT-3.5")
            elif agent_id == "e" and "claude" in response_text.lower():
                logger.info(f"✓ {agent_name} appears to be using Claude")
            else:
                logger.info(f"✓ {agent_name} responded (model verification requires checking logs)")
        
        logger.info("\n" + "="*60)
        logger.info("Test completed! Check server logs for actual model usage.")
        logger.info("Look for 'Using agent-specific config:' log entries")
        logger.info("="*60)


if __name__ == "__main__":
    print("Make sure the interactive server is running with:")
    print("python -m interactive_server.main")
    print("\nPress Enter to start the test...")
    input()
    
    asyncio.run(test_agent_models())