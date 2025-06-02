"""
Unit tests for Debbie agent configuration in batch mode.
Following TDD principles - tests written before implementation.
"""

import pytest
from pathlib import Path

try:
    from .test_debbie_agent_config_fixture import agents_config, debbie_config, debbie_agent
except ImportError:
    from test_debbie_agent_config_fixture import agents_config, debbie_config, debbie_agent


class TestDebbieAgentConfig:
    """Test Debbie's configuration for batch processing capabilities"""
    
    # Fixtures are imported from test_debbie_agent_config_fixture.py
    
    def test_debbie_agent_exists_in_config(self, debbie_agent):
        """Test that Debbie agent exists in the agent configuration"""
        assert debbie_agent is not None, "Debbie agent should exist with key 'd'"
        assert debbie_agent.name == "Debbie the Debugger"
    
    def test_debbie_agent_has_required_properties(self, debbie_agent):
        """Test that Debbie has all required agent properties"""
        assert debbie_agent.agent_id == 'd'
        assert debbie_agent.role == "debugging_assistant, batch_processor"
        assert debbie_agent.prompt_file == "debbie_debugger.prompt.md"
        assert debbie_agent.description
    
    def test_debbie_agent_role_includes_batch_processor(self, debbie_agent):
        """Test that Debbie's role includes batch processing"""
        assert "batch_processor" in debbie_agent.role
    
    def test_debbie_agent_has_batch_tools(self, debbie_agent):
        """Test that Debbie has tools needed for batch processing"""
        # Check for batch-specific tool tags
        assert "batch" in debbie_agent.tool_tags
        assert "monitoring" in debbie_agent.tool_tags
        assert "filesystem" in debbie_agent.tool_tags
        assert "command" in debbie_agent.tool_tags
    
    def test_debbie_agent_prompt_supports_batch_mode(self, debbie_agent):
        """Test that Debbie's prompt file exists and is configured"""
        prompt_path = Path("prompts/agents") / debbie_agent.prompt_file
        assert prompt_path.exists(), f"Prompt file {prompt_path} should exist"
    
    def test_debbie_agent_dual_role_configuration(self, debbie_agent):
        """Test that Debbie can function as both debugger and batch processor"""
        roles = [r.strip() for r in debbie_agent.role.split(',')]
        assert "debugging_assistant" in roles
        assert "batch_processor" in roles