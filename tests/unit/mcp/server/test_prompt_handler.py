"""Tests for MCP prompt handler."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from ai_whisperer.mcp.server.config import MCPServerConfig
from ai_whisperer.mcp.server.handlers.prompts import PromptHandler


class TestPromptHandler:
    """Tests for PromptHandler."""
    
    def test_init(self):
        """Test prompt handler initialization."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        assert handler.config == config
        assert handler.prompts_dir.name == "prompts"
        assert isinstance(handler._prompt_cache, dict)
        
    @patch('ai_whisperer.mcp.server.handlers.prompts.Path.exists')
    @patch('ai_whisperer.mcp.server.handlers.prompts.Path.glob')
    def test_load_prompts_with_agent_prompts(self, mock_glob, mock_exists):
        """Test loading agent prompts."""
        # Setup mocks
        mock_exists.return_value = True
        
        # Mock prompt files
        agent_file = Mock(spec=Path)
        agent_file.name = "alice_assistant.prompt.md"
        agent_file.stem = "alice_assistant.prompt"
        agent_file.read_text.return_value = """---
description: Alice the AI Assistant
arguments:
  - name: task
    description: The task to perform
    required: true
---

You are Alice, an AI assistant."""
        agent_file.relative_to.return_value = Path("agents/alice_assistant.prompt.md")
        
        mock_glob.return_value = [agent_file]
        
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Check prompt was loaded
        assert "alice_assistant" in handler._prompt_cache
        prompt = handler._prompt_cache["alice_assistant"]
        assert prompt["name"] == "alice_assistant"
        assert prompt["category"] == "agent"
        assert prompt["description"] == "Alice the AI Assistant"
        assert len(prompt["arguments"]) == 1
        assert "You are Alice" in prompt["content"]
            
    @patch('ai_whisperer.mcp.server.handlers.prompts.Path.exists')
    @patch('ai_whisperer.mcp.server.handlers.prompts.Path.glob')
    def test_load_prompts_skips_private(self, mock_glob, mock_exists):
        """Test that private prompts (starting with _) are skipped."""
        mock_exists.return_value = True
        
        # Mock prompt files including private one
        public_file = Mock(spec=Path)
        public_file.name = "alice.prompt.md"
        public_file.stem = "alice.prompt"
        public_file.read_text.return_value = "Public prompt content"
        public_file.relative_to.return_value = Path("agents/alice.prompt.md")
        
        private_file = Mock(spec=Path)
        private_file.name = "_private.prompt.md"
        private_file.stem = "_private.prompt"
        
        mock_glob.return_value = [public_file, private_file]
        
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Only public prompt should be loaded
        assert "alice" in handler._prompt_cache
        assert "_private" not in handler._prompt_cache
            
    def test_extract_metadata_with_yaml_frontmatter(self):
        """Test extracting metadata from YAML frontmatter."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        content = """---
description: Test prompt
arguments:
  - name: input
    description: Input data
    required: true
  - name: format
    description: Output format
    required: false
---

This is the prompt content."""
        
        metadata = handler._extract_metadata(content)
        
        assert metadata["description"] == "Test prompt"
        assert len(metadata["arguments"]) == 2
        assert metadata["arguments"][0]["name"] == "input"
        assert metadata["arguments"][1]["required"] is False
        
    def test_extract_metadata_without_frontmatter(self):
        """Test extracting metadata from content without frontmatter."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        content = """This is a simple prompt that helps with tasks.

It has multiple paragraphs."""
        
        metadata = handler._extract_metadata(content)
        
        # Should extract description from first paragraph
        assert metadata["description"] == "This is a simple prompt that helps with tasks."
        
        # Should have default arguments
        assert len(metadata["arguments"]) == 2
        assert metadata["arguments"][0]["name"] == "task"
        assert metadata["arguments"][1]["name"] == "context"
        
    def test_extract_metadata_truncates_long_description(self):
        """Test that long descriptions are truncated."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Create a very long first line
        long_line = "This is a very long description " * 10
        content = f"{long_line}\n\nMore content here."
        
        metadata = handler._extract_metadata(content)
        
        # Should be truncated to 100 chars + "..."
        assert len(metadata["description"]) == 103
        assert metadata["description"].endswith("...")
        
    @pytest.mark.asyncio
    async def test_list_prompts_all(self):
        """Test listing all prompts."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Populate cache
        handler._prompt_cache = {
            "alice": {
                "name": "alice",
                "description": "Alice assistant",
                "category": "agent",
                "arguments": []
            },
            "core/planner": {
                "name": "core/planner",
                "description": "Planning prompt",
                "category": "core",
                "arguments": []
            }
        }
        
        result = await handler.list_prompts({})
        
        assert len(result) == 2
        assert any(p["name"] == "alice" for p in result)
        assert any(p["name"] == "core/planner" for p in result)
        
    @pytest.mark.asyncio
    async def test_list_prompts_by_category(self):
        """Test filtering prompts by category."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Populate cache
        handler._prompt_cache = {
            "alice": {
                "name": "alice",
                "description": "Alice assistant",
                "category": "agent",
                "arguments": []
            },
            "bob": {
                "name": "bob",
                "description": "Bob assistant",
                "category": "agent",
                "arguments": []
            },
            "core/planner": {
                "name": "core/planner",
                "description": "Planning prompt",
                "category": "core",
                "arguments": []
            }
        }
        
        # Filter by agent category
        result = await handler.list_prompts({"category": "agent"})
        
        assert len(result) == 2
        assert all(p["category"] == "agent" for p in result)
        
    @pytest.mark.asyncio
    async def test_get_prompt_basic(self):
        """Test getting a prompt without substitution."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Populate cache
        handler._prompt_cache = {
            "test_prompt": {
                "name": "test_prompt",
                "description": "Test prompt",
                "category": "test",
                "arguments": [],
                "content": "This is a test prompt."
            }
        }
        
        result = await handler.get_prompt({"name": "test_prompt"})
        
        assert result["name"] == "test_prompt"
        assert result["content"] == "This is a test prompt."
        assert result["raw_content"] == "This is a test prompt."
        
    @pytest.mark.asyncio
    async def test_get_prompt_with_substitution(self):
        """Test getting a prompt with template substitution."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Populate cache with template
        handler._prompt_cache = {
            "template": {
                "name": "template",
                "description": "Template prompt",
                "category": "test",
                "arguments": [
                    {"name": "task", "description": "Task name", "required": True},
                    {"name": "context", "description": "Additional context", "required": False}
                ],
                "content": "Please complete {{task}}. Context: {{context}}"
            }
        }
        
        # Get with substitution
        result = await handler.get_prompt({
            "name": "template",
            "arguments": {
                "task": "write tests",
                "context": "for the MCP server"
            }
        })
        
        assert result["content"] == "Please complete write tests. Context: for the MCP server"
        assert result["raw_content"] == "Please complete {{task}}. Context: {{context}}"
        
    @pytest.mark.asyncio
    async def test_get_prompt_missing_name(self):
        """Test getting prompt without name parameter."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        with pytest.raises(ValueError, match="Missing required field: name"):
            await handler.get_prompt({})
            
    @pytest.mark.asyncio
    async def test_get_prompt_not_found(self):
        """Test getting non-existent prompt."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        with pytest.raises(ValueError, match="Prompt 'unknown' not found"):
            await handler.get_prompt({"name": "unknown"})
            
    def test_get_available_categories(self):
        """Test getting list of available categories."""
        config = MCPServerConfig()
        handler = PromptHandler(config)
        
        # Populate cache
        handler._prompt_cache = {
            "alice": {"category": "agent"},
            "bob": {"category": "agent"},
            "planner": {"category": "core"},
            "test": {"category": "test"}
        }
        
        categories = handler.get_available_categories()
        
        assert categories == ["agent", "core", "test"]  # Sorted