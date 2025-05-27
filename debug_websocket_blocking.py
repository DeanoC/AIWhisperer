#!/usr/bin/env python3
"""
Debug script to identify where WebSocket blocking occurs.
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_websocket_blocking():
    """Test WebSocket communication to identify blocking issues."""
    uri = "ws://127.0.0.1:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket")
            
            # Send startSession
            start_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "startSession",
                "params": {"userId": "debug_user", "sessionParams": {"language": "en"}}
            }
            
            logger.info("Sending startSession...")
            await websocket.send(json.dumps(start_req))
            
            # Receive startSession responses
            session_id = None
            for i in range(10):  # Wait for up to 10 messages
                try:
                    msg_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    msg = json.loads(msg_text)
                    logger.info(f"Received message {i+1}: {msg}")
                    
                    if msg.get("result") and msg["result"].get("sessionId"):
                        session_id = msg["result"]["sessionId"]
                        logger.info(f"Got session ID: {session_id}")
                        break
                except asyncio.TimeoutError:
                    logger.error(f"Timeout waiting for message {i+1}")
                    break
                except Exception as e:
                    logger.error(f"Error receiving message {i+1}: {e}")
                    break
            
            if not session_id:
                logger.error("Failed to get session ID")
                return
            
            # Small delay to ensure session is ready
            await asyncio.sleep(1.0)
              # Send sendUserMessage
            user_msg = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "sendUserMessage",
                "params": {"sessionId": session_id, "message": "simulate_timeout"}  # Use timeout message
            }
            
            logger.info("Sending sendUserMessage...")
            await websocket.send(json.dumps(user_msg))
            logger.info("sendUserMessage sent successfully")
            
            # Wait for response
            try:
                response_text = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response = json.loads(response_text)
                logger.info(f"Received sendUserMessage response: {response}")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for sendUserMessage response - this indicates the blocking issue!")
            except Exception as e:
                logger.error(f"Error receiving sendUserMessage response: {e}")
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

if __name__ == "__main__":
    print("Starting WebSocket blocking debug test...")
    print("Make sure the interactive server is running on port 8000")
    asyncio.run(test_websocket_blocking())
