#!/usr/bin/env python3
"""
Simple MCP Aggregator using FastMCP - properly handles async initialization.
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional
import re

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


# Global state for the upstream connection
upstream_url = "http://localhost:8002"
upstream_session: Optional[aiohttp.ClientSession] = None
upstream_session_id: Optional[str] = None
upstream_available = False
cached_tools: List[Dict[str, Any]] = []


async def check_upstream():
    """Check if upstream is available and get session ID."""
    global upstream_session_id, upstream_available
    
    try:
        async with upstream_session.get(f"{upstream_url}/sse") as resp:
            if resp.status == 200:
                # Read first few lines to get session ID
                count = 0
                async for chunk in resp.content.iter_any():
                    if chunk and count < 5:
                        chunk_str = chunk.decode('utf-8', errors='ignore')
                        if 'session_id=' in chunk_str:
                            match = re.search(r'session_id=([a-f0-9-]+)', chunk_str)
                            if match:
                                upstream_session_id = match.group(1)
                                upstream_available = True
                                logger.info(f"Connected to upstream, session: {upstream_session_id}")
                                return True
                        count += 1
                        
    except Exception as e:
        logger.error(f"Failed to connect to upstream: {e}")
        upstream_available = False
        
    return False


async def initialize_upstream():
    """Initialize the upstream MCP session."""
    if not upstream_session_id:
        return False
        
    try:
        url = f"{upstream_url}/messages/?session_id={upstream_session_id}"
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "clientInfo": {
                    "name": "mcp-aggregator",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }
        
        async with upstream_session.post(url, json=request) as resp:
            if resp.status in [200, 202]:
                logger.info("Initialized upstream connection")
                await refresh_tools()
                return True
                
    except Exception as e:
        logger.error(f"Failed to initialize upstream: {e}")
        
    return False


async def refresh_tools():
    """Get tools from upstream."""
    global cached_tools
    
    if not upstream_session_id:
        return
        
    try:
        url = f"{upstream_url}/messages/?session_id={upstream_session_id}"
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": 2
        }
        
        async with upstream_session.post(url, json=request) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "result" in data:
                    cached_tools = data["result"].get("tools", [])
                    logger.info(f"Got {len(cached_tools)} tools from upstream")
                    
    except Exception as e:
        logger.error(f"Failed to get tools: {e}")


async def call_upstream_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool on the upstream server."""
    global upstream_available
    
    if not upstream_available:
        # Try to reconnect
        if await check_upstream():
            await initialize_upstream()
            
    if not upstream_session_id:
        return {"error": "Upstream server not available"}
        
    try:
        url = f"{upstream_url}/messages/?session_id={upstream_session_id}"
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 3
        }
        
        async with upstream_session.post(url, json=request) as resp:
            if resp.status == 200:
                data = await resp.json()
                if "result" in data:
                    return data["result"]
                elif "error" in data:
                    return {"error": data["error"].get("message", "Unknown error")}
            elif resp.status == 202:
                # Accepted but async - for now return success
                return {"status": "processing"}
            else:
                return {"error": f"HTTP {resp.status}"}
                
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        upstream_available = False
        return {"error": str(e)}


# Create FastMCP instance
mcp = FastMCP(name="mcp-aggregator", port=3002)


@mcp.tool(description="Get aggregator status and connected servers")
async def aggregator_status() -> str:
    """Get the status of the aggregator and its connections."""
    status = {
        "aggregator": "MCP Aggregator v1.0",
        "upstream": {
            "url": upstream_url,
            "available": upstream_available,
            "session_id": upstream_session_id,
            "tools_count": len(cached_tools)
        }
    }
    return json.dumps(status, indent=2)


@mcp.tool(description="List directories in the workspace")
async def list_directory(path: str = ".") -> str:
    """List directory contents."""
    result = await call_upstream_tool("list_directory", {"path": path})
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


@mcp.tool(description="Read a file from the workspace")
async def read_file(path: str) -> str:
    """Read file contents."""
    result = await call_upstream_tool("read_file", {"path": path})
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        elif "content" in result:
            return result["content"]
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


@mcp.tool(description="Write a file to the workspace")
async def write_file(path: str, content: str) -> str:
    """Write file contents."""
    result = await call_upstream_tool("write_file", {"path": path, "content": content})
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


@mcp.tool(description="Search for files matching patterns")
async def search_files(pattern: str, file_types: Optional[List[str]] = None) -> str:
    """Search for files."""
    args = {"pattern": pattern}
    if file_types:
        args["file_types"] = file_types
        
    result = await call_upstream_tool("search_files", args)
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


@mcp.tool(description="Execute a shell command")
async def execute_command(command: str, working_directory: Optional[str] = None) -> str:
    """Execute a command."""
    args = {"command": command}
    if working_directory:
        args["working_directory"] = working_directory
        
    result = await call_upstream_tool("execute_command", args)
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


@mcp.tool(description="Execute Python code")
async def python_executor(code: str) -> str:
    """Execute Python code."""
    result = await call_upstream_tool("python_executor", {"code": code})
    
    if isinstance(result, dict):
        if "error" in result:
            return f"Error: {result['error']}"
        else:
            return json.dumps(result, indent=2)
    else:
        return str(result)


async def startup():
    """Initialize the aggregator on startup."""
    global upstream_session
    
    # Create session
    upstream_session = aiohttp.ClientSession()
    
    # Try to connect to upstream
    logger.info("Connecting to upstream server...")
    if await check_upstream():
        await initialize_upstream()
    else:
        logger.warning("Upstream server not available at startup")
        
    # Start background task to monitor upstream
    asyncio.create_task(monitor_upstream())
    

async def monitor_upstream():
    """Background task to monitor and reconnect to upstream."""
    global upstream_available
    
    while True:
        try:
            if not upstream_available:
                logger.info("Attempting to reconnect to upstream...")
                if await check_upstream():
                    await initialize_upstream()
                    
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Monitor error: {e}")
            await asyncio.sleep(5)


def main():
    """Main entry point."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    
    logger.info("Starting MCP Aggregator (Simple)")
    
    # Run with startup hook
    import nest_asyncio
    nest_asyncio.apply()
    
    # Initialize in the background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(startup())
    
    # Run the server
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()