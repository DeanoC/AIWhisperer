#!/usr/bin/env python3
"""Test MCP server integration with interactive server."""

import asyncio
import json
import websockets
import sys
import time


async def test_interactive_server_mcp():
    """Test MCP server control via interactive server."""
    
    print("Testing MCP server integration...")
    
    # Connect to interactive server
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to interactive server at {uri}")
            
            # Test 1: Check MCP status (should not be running)
            print("\n1. Checking initial MCP status...")
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.status",
                "params": {},
                "id": 1
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"Response: {response}")
            assert response["result"]["running"] == False
            
            # Test 2: Start MCP server
            print("\n2. Starting MCP server...")
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.start",
                "params": {
                    "transport": "websocket",
                    "port": 3001,
                    "exposed_tools": ["read_file", "list_directory", "search_files"],
                    "workspace": "/tmp"
                },
                "id": 2
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"Response: {response}")
            assert response["result"]["success"] == True
            assert response["result"]["server_url"] == "ws://localhost:3001/mcp"
            
            # Give server time to fully start
            await asyncio.sleep(1)
            
            # Test 3: Check MCP status (should be running)
            print("\n3. Checking MCP status after start...")
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.status",
                "params": {},
                "id": 3
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"Response: {response}")
            assert response["result"]["running"] == True
            assert response["result"]["transport"] == "websocket"
            assert response["result"]["port"] == 3001
            
            # Test 4: Connect to MCP server
            print("\n4. Testing connection to MCP server...")
            mcp_uri = "ws://localhost:3001/mcp"
            try:
                async with websockets.connect(mcp_uri) as mcp_ws:
                    print(f"Connected to MCP server at {mcp_uri}")
                    
                    # Initialize MCP session
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "test-client",
                                "version": "1.0.0"
                            }
                        },
                        "id": 1
                    }
                    await mcp_ws.send(json.dumps(mcp_request))
                    mcp_response = json.loads(await mcp_ws.recv())
                    print(f"MCP Initialize response: {mcp_response}")
                    assert "result" in mcp_response
                    
                    # List tools
                    mcp_request = {
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "params": {},
                        "id": 2
                    }
                    await mcp_ws.send(json.dumps(mcp_request))
                    mcp_response = json.loads(await mcp_ws.recv())
                    print(f"MCP Tools response: {mcp_response}")
                    assert len(mcp_response["result"]["tools"]) == 3
                    
            except Exception as e:
                print(f"Failed to connect to MCP server: {e}")
                raise
                
            # Test 5: Stop MCP server
            print("\n5. Stopping MCP server...")
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.stop",
                "params": {},
                "id": 5
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"Response: {response}")
            assert response["result"]["success"] == True
            
            # Test 6: Check MCP status (should not be running)
            print("\n6. Checking MCP status after stop...")
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.status",
                "params": {},
                "id": 6
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"Response: {response}")
            assert response["result"]["running"] == False
            
            print("\n✅ All tests passed!")
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


async def test_mcp_server_startup():
    """Test starting interactive server with MCP enabled."""
    
    print("\nTesting MCP server startup with interactive server...")
    print("This requires starting the server with: python -m interactive_server.main --mcp")
    print("Then checking if MCP is running...")
    
    # Wait a moment for server to start
    await asyncio.sleep(2)
    
    # Connect to interactive server
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to interactive server at {uri}")
            
            # Check MCP status
            request = {
                "jsonrpc": "2.0",
                "method": "mcp.status",
                "params": {},
                "id": 1
            }
            await websocket.send(json.dumps(request))
            response = json.loads(await websocket.recv())
            print(f"MCP Status: {response}")
            
            if response["result"]["running"]:
                print(f"✅ MCP server is running on {response['result']['transport']} transport")
                print(f"   Server URL: {response['result']['server_url']}")
                print(f"   Exposed tools: {response['result']['exposed_tools']}")
            else:
                print("❌ MCP server is not running (start with --mcp flag)")
                
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Make sure the interactive server is running on port 8000")


if __name__ == "__main__":
    # Run the appropriate test based on command line args
    if len(sys.argv) > 1 and sys.argv[1] == "startup":
        asyncio.run(test_mcp_server_startup())
    else:
        asyncio.run(test_interactive_server_mcp())