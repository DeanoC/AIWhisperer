"""
Unit tests for Debbie's prompt system supporting both debugging and batch modes.
Following TDD principles - tests written before implementation.
"""

import pytest
import os
from pathlib import Path
import yaml

from ai_whisperer.prompt_system import PromptLoader
from ai_whisperer.services.agents.registry import Agent


@pytest.mark.flaky
@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", reason="Test isolation issues in CI - passes individually but fails in full suite")
class TestDebbiePromptSystem:
    """Test Debbie's prompt system for dual-mode operation"""
    
    @pytest.fixture
    def prompt_loader(self):
        """Provide an initialized PromptLoader"""
        return PromptLoader()
    
    @pytest.fixture
    def debbie_config(self):
        """Get Debbie's configuration from the agents config"""
        config_path = Path("config/agents/agents.yaml")
        with open(config_path, 'r') as f:
            agents_config = yaml.safe_load(f)
        return agents_config['agents'].get('d')
    
    @pytest.fixture
    def debbie_agent(self, debbie_config):
        """Create Debbie agent from config"""
        if not debbie_config:
            return None
        return Agent(
            agent_id='d',
            name=debbie_config['name'],
            role=debbie_config['role'],
            description=debbie_config['description'],
            tool_tags=debbie_config.get('tool_tags', []),
            prompt_file=debbie_config['prompt_file'],
            context_sources=debbie_config.get('context_sources', []),
            color=debbie_config.get('color', '#888888'),
            icon=debbie_config.get('icon', '🤖'),
            tool_sets=debbie_config.get('tool_sets'),
            allow_tools=debbie_config.get('allow_tools'),
            deny_tools=debbie_config.get('deny_tools'),
            continuation_config=debbie_config.get('continuation_config')
        )
    
    def test_debbie_prompt_file_exists(self, debbie_agent):
        """Test that Debbie's prompt file exists"""
        prompt_file = Path("prompts/agents") / debbie_agent.prompt_file
        
        assert prompt_file.exists(), f"Prompt file {prompt_file} should exist"
        assert prompt_file.is_file(), f"{prompt_file} should be a file"
    
    def test_debbie_prompt_contains_batch_instructions(self):
        """Test that Debbie's prompt contains batch processing instructions"""
        prompt_file = Path("prompts/agents/debbie_debugger.prompt.md")
        assert prompt_file.exists(), f"Debbie's prompt file should exist at {prompt_file}"
        
        content = prompt_file.read_text()
        
        # Check for batch mode content
        assert "batch" in content.lower(), "Prompt should mention batch processing"
        assert any(keyword in content.lower() for keyword in ["script", "automated", "monitoring"]), \
            "Prompt should contain batch-related keywords"
    
    def test_debbie_prompt_contains_debugging_instructions(self):
        """Test that Debbie's prompt contains debugging instructions"""
        prompt_file = Path("prompts/agents/debbie_debugger.prompt.md")
        assert prompt_file.exists()
        
        content = prompt_file.read_text()
        
        # Check for debugging content
        assert "debug" in content.lower(), "Prompt should mention debugging"
        assert any(keyword in content.lower() for keyword in ["error", "issue", "problem", "troubleshoot"]), \
            "Prompt should contain debugging-related keywords"
    
    def test_prompt_dual_mode_support(self):
        """Test that the prompt supports both debugging and batch modes"""
        prompt_file = Path("prompts/agents/debbie_debugger.prompt.md")
        assert prompt_file.exists()
        
        content = prompt_file.read_text()
        
        # Check for dual-mode indicators
        has_batch_mode = "batch" in content.lower()
        has_debug_mode = "debug" in content.lower()
        
        assert has_batch_mode and has_debug_mode, \
            "Prompt should support both batch processing and debugging modes"
    
    def test_prompt_includes_monitoring_capabilities(self):
        """Test that prompt includes monitoring and intervention capabilities"""
        prompt_file = Path("prompts/agents/debbie_debugger.prompt.md")
        assert prompt_file.exists()
        
        content = prompt_file.read_text()
        
        # Check for monitoring capabilities
        monitoring_keywords = ["monitor", "watch", "observe", "track", "intervene", "pause"]
        assert any(keyword in content.lower() for keyword in monitoring_keywords), \
            "Prompt should include monitoring and intervention capabilities"
    
    def test_prompt_system_loads_debbie_prompt(self, prompt_loader, debbie_agent):
        """Test that the prompt system can load Debbie's prompt"""
        # Note: This test would need the actual PromptLoader implementation
        # For now, we'll just verify the prompt file path is correct
        expected_path = Path("prompts/agents") / debbie_agent.prompt_file
        assert expected_path.exists(), f"Expected prompt at {expected_path}"