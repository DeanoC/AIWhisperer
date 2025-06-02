"""
Unit tests for Debbie agent configuration in batch mode.
Following TDD principles - tests written before implementation.
"""

import pytest
from pathlib import Path

from ai_whisperer.services.agents.registry import AgentRegistry


class TestDebbieAgentConfig:
    """Test Debbie's configuration for batch processing capabilities"""
    
    @pytest.fixture
    def agent_registry(self):
        """Provide an initialized AgentRegistry"""
        prompts_dir = Path("prompts")
        return AgentRegistry(prompts_dir)
    
    @pytest.fixture
    def debbie_agent(self, agent_registry):
        """Get Debbie agent from registry"""
        return agent_registry.get_agent('D')
    
    def test_debbie_agent_exists_in_config(self, debbie_agent):
        """Test that Debbie agent exists in the agent configuration"""
        assert debbie_agent is not None, "Debbie agent should exist with key 'D'"
        assert debbie_agent.name == "Debbie the Debugger"
    
    def test_debbie_agent_has_required_properties(self, debbie_agent):
        """Test that Debbie has all required agent properties"""
        assert hasattr(debbie_agent, 'name')
        assert hasattr(debbie_agent, 'role')
        assert hasattr(debbie_agent, 'description')
        assert hasattr(debbie_agent, 'prompt_file')
        assert hasattr(debbie_agent, 'tool_sets')
    
    def test_debbie_agent_role_includes_batch_processor(self, debbie_agent):
        """Test that Debbie has batch_processor role"""
        # Currently Debbie only has debugging_assistant role
        # This test should fail until we add batch_processor
        roles = debbie_agent.role.split(',') if isinstance(debbie_agent.role, str) else [debbie_agent.role]
        roles = [r.strip() for r in roles]
        
        assert 'batch_processor' in roles, "Debbie should have batch_processor role"
        assert 'debugging_assistant' in roles, "Debbie should retain debugging_assistant role"
    
    def test_debbie_agent_has_batch_tools(self, debbie_agent):
        """Test that Debbie has batch processing tools configured"""
        # This should fail until we add batch_tools to tool_sets
        assert 'batch_tools' in debbie_agent.tool_sets, "Should have batch processing tools"
        assert 'debugging_tools' in debbie_agent.tool_sets, "Should retain debugging tools"
        assert 'filesystem' in debbie_agent.tool_sets, "Should have filesystem tools"
    
    def test_debbie_agent_prompt_supports_batch_mode(self, debbie_agent):
        """Test that Debbie's prompt file supports batch operations"""
        assert debbie_agent.prompt_file is not None
        # For now, we expect the same prompt file
        # Later we might want a combined prompt or multiple files
        assert 'debbie' in debbie_agent.prompt_file.lower()
    
    def test_debbie_agent_dual_role_configuration(self, debbie_agent):
        """Test that Debbie is configured for dual-role operation"""
        # Check that Debbie has configurations for both roles
        roles = debbie_agent.role.split(',') if isinstance(debbie_agent.role, str) else [debbie_agent.role]
        roles = [r.strip() for r in roles]
        
        # Should have at least 2 roles
        assert len(roles) >= 2, f"Debbie should have multiple roles, found: {roles}"
        
        # Should have multiple tool sets
        assert len(debbie_agent.tool_sets) >= 3, \
            f"Should have multiple tool sets for dual functionality, found: {debbie_agent.tool_sets}"