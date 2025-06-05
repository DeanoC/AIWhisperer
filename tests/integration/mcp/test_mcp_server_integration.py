"""Integration tests for MCP server with better error handling."""

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
        
    async def _send_request(self, proc, request):
        """Send request and read response with error handling."""
        proc.stdin.write((json.dumps(request) + '\n').encode())
        await proc.stdin.drain()
        
        try:
            response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
            if not response_line:
                # Check stderr for errors
                stderr_data = await proc.stderr.read()
                raise RuntimeError(f"Server closed stdout. Stderr: {stderr_data.decode()}")
            return json.loads(response_line.decode())
        except asyncio.TimeoutError:
            stderr_data = await proc.stderr.read()
            raise RuntimeError(f"Timeout reading response. Stderr: {stderr_data.decode()}")
        except json.JSONDecodeError as e:
            # Read more data to see what we got
            extra_data = await proc.stdout.read(100)
            stderr_data = await proc.stderr.read()
            raise RuntimeError(
                f"Failed to parse JSON: {e}\n"
                f"Got: {response_line.decode()}\n"
                f"Extra stdout: {extra_data.decode()}\n"
                f"Stderr: {stderr_data.decode()}"
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
        
        # Start server subprocess with explicit Python path
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "ai_whisperer.mcp.server.runner",
            "--expose-tool", "read_file",
            "--expose-tool", "list_directory",
            "--workspace", temp_workspace,
            "--log-level", "CRITICAL",  # Suppress logs
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
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
            
            response = await self._send_request(proc, request)
            
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
            
            response = await self._send_request(proc, request)
            
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
            
            response = await self._send_request(proc, request)
            
            assert response["id"] == 3
            assert "result" in response
            assert "content" in response["result"]
            content = response["result"]["content"][0]["text"]
            assert "Hello World" in content
            
        finally:
            # Clean shutdown
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self, server_config, temp_workspace):
        """Test handling multiple concurrent requests."""
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
            "--log-level", "CRITICAL",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        )
        
        try:
            # Initialize first
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                },
                "id": 1
            }
            
            await self._send_request(proc, init_request)
            
            # Send multiple requests without waiting
            requests = []
            for i in range(5):
                req = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "params": {},
                    "id": i + 2
                }
                proc.stdin.write((json.dumps(req) + '\n').encode())
                requests.append(req)
                
            await proc.stdin.drain()
            
            # Read all responses
            responses = []
            for _ in range(5):
                response_line = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
                response = json.loads(response_line.decode())
                responses.append(response)
                
            # Verify all responses
            response_ids = [r["id"] for r in responses]
            assert sorted(response_ids) == list(range(2, 7))
            
            for resp in responses:
                assert "result" in resp
                assert "tools" in resp["result"]
                
        finally:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                
    @pytest.mark.asyncio 
    async def test_error_handling(self, server_config, temp_workspace):
        """Test error handling."""
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
            "--workspace", temp_workspace,
            "--log-level", "CRITICAL",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        )
        
        try:
            # Initialize first
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                },
                "id": 1
            }
            
            await self._send_request(proc, init_request)
            
            # Test invalid method
            request = {
                "jsonrpc": "2.0",
                "method": "invalid/method",
                "params": {},
                "id": 2
            }
            
            response = await self._send_request(proc, request)
            
            assert response["id"] == 2
            assert "error" in response
            assert response["error"]["code"] == -32601
            assert "not found" in response["error"]["message"].lower()
            
            # Test missing required field
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {},  # Missing 'name'
                "id": 3
            }
            
            response = await self._send_request(proc, request)
            
            assert response["id"] == 3
            assert "error" in response
            
            # Test calling non-existent tool
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "non_existent_tool",
                    "arguments": {}
                },
                "id": 4
            }
            
            response = await self._send_request(proc, request)
            
            assert response["id"] == 4
            assert "error" in response
            
        finally:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                
    @pytest.mark.asyncio
    async def test_notification_handling(self, server_config, temp_workspace):
        """Test handling notifications (no id field)."""
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
            "--workspace", temp_workspace,
            "--log-level", "CRITICAL",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        )
        
        try:
            # Initialize first
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05", 
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                },
                "id": 1
            }
            
            await self._send_request(proc, init_request)
            
            # Send notification (no id)
            notification = {
                "jsonrpc": "2.0",
                "method": "ping",
                "params": {}
            }
            
            proc.stdin.write((json.dumps(notification) + '\n').encode())
            await proc.stdin.drain()
            
            # Send a regular request after
            request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2
            }
            
            response = await self._send_request(proc, request)
            
            # Should get response to request, not notification
            assert response["id"] == 2
            assert "result" in response
            
        finally:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()