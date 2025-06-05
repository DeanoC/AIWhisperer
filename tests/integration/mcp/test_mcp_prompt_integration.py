"""Integration tests for MCP prompt functionality."""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import patch

from ai_whisperer.mcp.server.server import MCPServer
from ai_whisperer.mcp.server.config import MCPServerConfig, TransportType


class TestMCPPromptIntegration:
    """Integration tests for MCP prompt exposure."""
    
    @pytest.mark.asyncio
    async def test_prompts_list(self, tmp_path):
        """Test listing prompts from the real prompts directory."""
        config = MCPServerConfig(
            transport=TransportType.STDIO
        )
        
        server = MCPServer(config)
        
        # Initialize the server
        init_result = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        })
        
        assert "error" not in init_result
        assert init_result["result"]["capabilities"]["prompts"] == {}
        
        # List prompts
        list_result = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "params": {},
            "id": 2
        })
        
        assert "error" not in list_result
        # Should return prompts from real directory
        prompts = list_result["result"]["prompts"]
        assert len(prompts) > 0  # We have some prompts loaded
        
        # Check structure of a prompt
        first_prompt = prompts[0]
        assert "name" in first_prompt
        assert "description" in first_prompt
        assert "category" in first_prompt
        assert "arguments" in first_prompt
        
    @pytest.mark.asyncio
    async def test_prompts_with_real_files(self, tmp_path):
        """Test prompts with actual prompt files."""
        # Create prompts directory structure
        prompts_dir = tmp_path / "prompts"
        agents_dir = prompts_dir / "agents"
        agents_dir.mkdir(parents=True)
        
        # Create a test prompt file
        prompt_file = agents_dir / "test_agent.prompt.md"
        prompt_content = """---
description: Test Agent for unit tests
arguments:
  - name: task
    description: The task to perform
    required: true
  - name: verbose
    description: Whether to output verbose logs
    required: false
---

You are a test agent designed for unit testing.

Your task is: {{task}}
Verbose mode: {{verbose}}"""
        
        prompt_file.write_text(prompt_content)
        
        # Patch the prompts directory path
        with patch('ai_whisperer.mcp.server.handlers.prompts.Path') as mock_path:
            # Make the patched Path return our tmp_path when looking for prompts
            def path_side_effect(*args):
                if len(args) > 0 and "prompts" in str(args[0]):
                    return prompts_dir
                # For other paths, return the real Path
                return Path(*args) if args else Path()
                
            mock_path.side_effect = path_side_effect
            mock_path.return_value = prompts_dir
            
            # Also need to handle the __file__ parent chain
            mock_file_path = tmp_path
            for _ in range(5):  # 5 parent() calls in the handler
                mock_file_path = mock_file_path.parent
            mock_path.__file__ = mock_file_path / "dummy.py"
            
            config = MCPServerConfig(
                transport=TransportType.STDIO
            )
            
            server = MCPServer(config)
            
            # Manually reinitialize the prompt handler with our test directory
            server.prompt_handler.prompts_dir = prompts_dir
            server.prompt_handler._prompt_cache = {}
            server.prompt_handler._load_prompts()
            
            # Initialize
            await server.handle_request({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                },
                "id": 1
            })
            
            # List prompts
            list_result = await server.handle_request({
                "jsonrpc": "2.0",
                "method": "prompts/list",
                "params": {},
                "id": 2
            })
            
            assert "error" not in list_result
            prompts = list_result["result"]["prompts"]
            assert len(prompts) == 1
            assert prompts[0]["name"] == "test_agent"
            assert prompts[0]["description"] == "Test Agent for unit tests"
            assert prompts[0]["category"] == "agent"
            assert len(prompts[0]["arguments"]) == 2
            
            # Get specific prompt
            get_result = await server.handle_request({
                "jsonrpc": "2.0",
                "method": "prompts/get",
                "params": {
                    "name": "test_agent",
                    "arguments": {
                        "task": "run tests",
                        "verbose": "true"
                    }
                },
                "id": 3
            })
            
            assert "error" not in get_result
            prompt = get_result["result"]
            assert prompt["name"] == "test_agent"
            assert "Your task is: run tests" in prompt["content"]
            assert "Verbose mode: true" in prompt["content"]
            assert prompt["raw_content"] == prompt_content
            
    @pytest.mark.asyncio
    async def test_prompt_not_found(self, tmp_path):
        """Test getting non-existent prompt."""
        config = MCPServerConfig(
            transport=TransportType.STDIO
        )
        
        server = MCPServer(config)
        
        # Initialize
        await server.handle_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        })
        
        # Try to get non-existent prompt
        result = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "does_not_exist"
            },
            "id": 2
        })
        
        assert "error" in result
        assert "not found" in result["error"]["message"]
        
    @pytest.mark.asyncio
    async def test_prompt_missing_name(self, tmp_path):
        """Test getting prompt without name parameter."""
        config = MCPServerConfig(
            transport=TransportType.STDIO
        )
        
        server = MCPServer(config)
        
        # Initialize
        await server.handle_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        })
        
        # Try to get prompt without name
        result = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {},
            "id": 2
        })
        
        assert "error" in result
        assert "Missing required field: name" in result["error"]["message"]
        
    @pytest.mark.asyncio  
    async def test_prompts_list_with_category_filter(self, tmp_path):
        """Test filtering prompts by category."""
        # Create prompts with different categories
        prompts_dir = tmp_path / "prompts"
        agents_dir = prompts_dir / "agents"
        core_dir = prompts_dir / "core"
        agents_dir.mkdir(parents=True)
        core_dir.mkdir(parents=True)
        
        # Create agent prompt
        (agents_dir / "alice.prompt.md").write_text("Alice agent prompt")
        
        # Create core prompt  
        (core_dir / "planner.prompt.md").write_text("Planning prompt")
        
        config = MCPServerConfig(
            transport=TransportType.STDIO
        )
        
        server = MCPServer(config)
        
        # Manually set prompts directory
        server.prompt_handler.prompts_dir = prompts_dir
        server.prompt_handler._prompt_cache = {}
        server.prompt_handler._load_prompts()
        
        # Initialize
        await server.handle_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {}
            },
            "id": 1
        })
        
        # List only agent prompts
        result = await server.handle_request({
            "jsonrpc": "2.0",
            "method": "prompts/list",
            "params": {"category": "agent"},
            "id": 2
        })
        
        assert "error" not in result
        prompts = result["result"]["prompts"]
        assert len(prompts) == 1
        assert prompts[0]["name"] == "alice"
        assert prompts[0]["category"] == "agent"