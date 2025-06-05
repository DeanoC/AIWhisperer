"""Integration tests for MCP server."""

import pytest
import asyncio
import json
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ai_whisperer.mcp.server.runner import MCPServerRunner
from ai_whisperer.mcp.server.config import MCPServerConfig, TransportType
from ai_whisperer.utils.path import PathManager


class TestMCPServerIntegration:
    """Integration tests for MCP server."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "test.py").write_text("print('Hello World')")
            Path(tmpdir, "README.md").write_text("# Test Project\n\nA test project.")
            
            # Create output directory
            Path(tmpdir, "output").mkdir()
            
            yield tmpdir
            
    @pytest.fixture
    def server_config(self, temp_workspace):
        """Create server configuration."""
        return MCPServerConfig(
            transport=TransportType.STDIO,
            exposed_tools=["read_file", "list_directory", "write_file"],
            server_name="test-aiwhisperer",
            server_version="1.0.0"
        )
        
    @pytest.mark.asyncio
    async def test_server_lifecycle(self, server_config, temp_workspace):
        """Test complete server lifecycle with subprocess."""
        # Initialize PathManager
        PathManager().initialize(config_values={
            'project_path': temp_workspace,
            'workspace_path': temp_workspace,
            'output_path': os.path.join(temp_workspace, 'output')
        })
        
        # Start server subprocess
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server.runner",
            "--expose-tool", "read_file",
            "--expose-tool", "list_directory",
            "--workspace", temp_workspace,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Test initialize
            request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                },
                "id": 1
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert response["id"] == 1
            assert "result" in response
            assert response["result"]["protocolVersion"] == "2024-11-05"
            assert response["result"]["serverInfo"]["name"] == "aiwhisperer-mcp"
            
            # Test tools/list
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert response["id"] == 2
            assert "result" in response
            tools = response["result"]["tools"]
            assert len(tools) == 2
            tool_names = [t["name"] for t in tools]
            assert "read_file" in tool_names
            assert "list_directory" in tool_names
            
            # Test tool execution
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "read_file",
                    "arguments": {"path": "test.py"}
                },
                "id": 3
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert response["id"] == 3
            assert "result" in response
            assert "content" in response["result"]
            content = response["result"]["content"][0]["text"]
            assert "Hello World" in content
            
        finally:
            proc.terminate()
            await proc.wait()
            
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, temp_workspace):
        """Test handling multiple concurrent requests."""
        # Start server
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server.runner",
            "--expose-tool", "list_directory",
            "--workspace", temp_workspace,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Initialize first
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                },
                "id": "init"
            }
            
            proc.stdin.write((json.dumps(init_request) + '\n').encode())
            await proc.stdin.drain()
            
            init_response = await proc.stdout.readline()
            assert json.loads(init_response.decode())["id"] == "init"
            
            # Send multiple requests rapidly
            requests = []
            for i in range(5):
                request = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": f"req-{i}"
                }
                requests.append(request)
                proc.stdin.write((json.dumps(request) + '\n').encode())
                
            await proc.stdin.drain()
            
            # Read all responses
            responses = []
            for _ in range(5):
                response_line = await proc.stdout.readline()
                responses.append(json.loads(response_line.decode()))
                
            # Verify all requests were handled
            response_ids = [r["id"] for r in responses]
            assert sorted(response_ids) == [f"req-{i}" for i in range(5)]
            
        finally:
            proc.terminate()
            await proc.wait()
            
    @pytest.mark.asyncio
    async def test_error_handling(self, temp_workspace):
        """Test server error handling."""
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server.runner",
            "--expose-tool", "read_file",
            "--workspace", temp_workspace,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Try to call tool before initialization
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert "error" in response
            assert "not initialized" in response["error"]["message"].lower()
            
            # Initialize
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                },
                "id": 2
            }
            
            proc.stdin.write((json.dumps(init_request) + '\n').encode())
            await proc.stdin.drain()
            await proc.stdout.readline()  # Consume response
            
            # Try to call non-existent tool
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "nonexistent_tool",
                    "arguments": {}
                },
                "id": 3
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert "error" in response
            assert "not found" in response["error"]["message"]
            
        finally:
            proc.terminate()
            await proc.wait()
            
    @pytest.mark.asyncio
    async def test_notification_handling(self, temp_workspace):
        """Test handling notifications (requests without id)."""
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server.runner",
            "--expose-tool", "read_file",
            "--workspace", temp_workspace,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            # Send notification (no id)
            notification = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                }
                # No id field
            }
            
            proc.stdin.write((json.dumps(notification) + '\n').encode())
            await proc.stdin.drain()
            
            # For notifications, server should still respond but without id
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert "id" not in response
            assert "result" in response
            
            # Now send a normal request to verify server still works
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }
            
            proc.stdin.write((json.dumps(request) + '\n').encode())
            await proc.stdin.drain()
            
            response_line = await proc.stdout.readline()
            response = json.loads(response_line.decode())
            
            assert response["id"] == 1
            assert "result" in response
            
        finally:
            proc.terminate()
            await proc.wait()