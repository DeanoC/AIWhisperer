#!/usr/bin/env python3
"""
MCP stdio-to-websocket bridge.

This script acts as a bridge between Claude CLI (which uses stdio) and
the running AIWhisperer interactive server (which provides MCP via WebSocket).

Claude CLI spawns this as a subprocess and communicates via stdin/stdout,
while this bridge forwards those requests to the WebSocket MCP server.
"""

import asyncio
import json
import sys
import logging
import argparse
from typing import Optional, Dict, Any
import websockets
from websockets.exceptions import WebSocketException

# Configure logging to stderr to avoid interfering with stdio protocol
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class StdioToWebSocketBridge:
    """Bridge between stdio MCP protocol and WebSocket MCP server."""
    
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        
    async def connect(self):
        """Connect to the WebSocket MCP server."""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info(f"Connected to WebSocket MCP server at {self.websocket_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            # Send error response via stdout
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Failed to connect to AIWhisperer server: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            return False
            
    async def disconnect(self):
        """Disconnect from WebSocket."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
    async def read_stdin(self):
        """Read JSON-RPC messages from stdin."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while self.running:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                    
                # Decode and parse JSON
                try:
                    message = json.loads(line.decode('utf-8').strip())
                    logger.debug(f"Received from stdin: {message}")
                    
                    # Forward to WebSocket
                    await self.forward_to_websocket(message)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from stdin: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                    
            except Exception as e:
                logger.error(f"Error reading stdin: {e}")
                break
                
    async def forward_to_websocket(self, message: Dict[str, Any]):
        """Forward a message to the WebSocket server."""
        if not self.websocket:
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": "Not connected to server"
                }
            }
            print(json.dumps(error_response), flush=True)
            return
            
        try:
            # Send to WebSocket
            await self.websocket.send(json.dumps(message))
            
            # Wait for response
            response_text = await self.websocket.recv()
            response = json.loads(response_text)
            
            logger.debug(f"Received from WebSocket: {response}")
            
            # Forward response to stdout
            print(json.dumps(response), flush=True)
            
        except WebSocketException as e:
            logger.error(f"WebSocket error: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"WebSocket error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            
            # Try to reconnect
            await self.disconnect()
            await self.connect()
            
        except Exception as e:
            logger.error(f"Error forwarding to WebSocket: {e}")
            error_response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Bridge error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
            
    async def run(self):
        """Run the bridge."""
        # Connect to WebSocket
        if not await self.connect():
            return
            
        self.running = True
        
        try:
            # Start reading from stdin
            await self.read_stdin()
        except KeyboardInterrupt:
            logger.info("Bridge interrupted")
        except Exception as e:
            logger.error(f"Bridge error: {e}")
        finally:
            self.running = False
            await self.disconnect()


def main():
    """Main entry point for the stdio-to-websocket bridge."""
    parser = argparse.ArgumentParser(
        description="MCP stdio-to-websocket bridge for AIWhisperer",
        prog="aiwhisperer-mcp-bridge"
    )
    
    parser.add_argument(
        '--server-url',
        default='ws://localhost:3001/mcp',
        help='WebSocket URL of the MCP server (default: ws://localhost:3001/mcp)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='WARNING',
        help='Logging level (default: WARNING)'
    )
    
    args = parser.parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create and run bridge
    bridge = StdioToWebSocketBridge(args.server_url)
    
    try:
        asyncio.run(bridge.run())
    except Exception as e:
        logger.error(f"Bridge failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()