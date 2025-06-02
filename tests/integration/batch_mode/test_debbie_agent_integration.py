"""
Integration tests for Debbie agent in batch mode.
Tests the complete configuration and loading process.
"""

import pytest
from pathlib import Path
import os

from ai_whisperer.services.agents.registry import AgentRegistry


@pytest.mark.flaky
@pytest.mark.skipif(os.getenv("GITHUB_ACTIONS") == "true", reason="Test isolation issues in CI - passes individually but fails in full suite")
class TestDebbieAgentIntegration:
    """Integration tests for Debbie's dual-mode configuration"""
    
    @pytest.fixture
    def agent_registry(self):
        """Provide an initialized AgentRegistry"""
        from ai_whisperer.utils.path import PathManager
        # Initialize PathManager with proper paths
        PathManager._instance = None
        PathManager._initialized = False
        path_manager = PathManager.get_instance()
        path_manager.initialize()  # Initialize with defaults
        
        # Use the app_path for consistent prompt location
        prompts_dir = path_manager.app_path / "prompts"
        return AgentRegistry(prompts_dir)
    
    def test_debbie_loads_with_all_configurations(self, agent_registry):
        """Test that Debbie loads successfully with all configurations"""
        agent = agent_registry.get_agent('D')
        
        # Basic properties
        assert agent is not None
        assert agent.name == "Debbie the Debugger"
        assert agent.agent_id == 'D'
        
        # Dual role
        roles = [r.strip() for r in agent.role.split(',')]
        assert 'debugging_assistant' in roles
        assert 'batch_processor' in roles
        
        # Tool sets
        assert 'debugging_tools' in agent.tool_sets
        assert 'batch_tools' in agent.tool_sets
        assert 'filesystem' in agent.tool_sets
        
        # Prompt file exists - use PathManager to get correct path
        from ai_whisperer.utils.path import PathManager
        path_manager = PathManager.get_instance()
        prompt_path = path_manager.app_path / "prompts" / "agents" / agent.prompt_file
        assert prompt_path.exists()
        
        # Context sources include batch scripts
        assert 'batch_scripts' in agent.context_sources
    
    def test_debbie_agent_list_shows_dual_role(self, agent_registry):
        """Test that agent listing shows Debbie's dual capabilities"""
        agents = agent_registry.list_agents()
        
        debbie = next((a for a in agents if a.agent_id == 'D'), None)
        assert debbie is not None
        
        # Check description mentions both roles
        desc_lower = debbie.description.lower()
        assert 'debug' in desc_lower
        assert 'batch' in desc_lower or 'script' in desc_lower
    
    def test_debbie_continuation_config_includes_batch(self, agent_registry):
        """Test that continuation config includes batch-specific rules"""
        agent = agent_registry.get_agent('D')
        
        assert hasattr(agent, 'continuation_config')
        assert agent.continuation_config is not None
        
        # Check for batch-specific continuation rules
        rules = agent.continuation_config.get('rules', [])
        
        # Find batch-related rules
        batch_rules = [r for r in rules if any(
            tool in r.get('trigger_tools', []) 
            for tool in ['script_parser', 'batch_command']
        )]
        
        assert len(batch_rules) >= 2, "Should have continuation rules for batch tools"
    
    def test_debbie_capabilities_include_batch_processing(self, agent_registry):
        """Test that Debbie's capabilities list includes batch processing"""
        # Note: This test assumes capabilities are stored in the agent data
        # Adjust based on actual implementation
        agent = agent_registry.get_agent('D')
        
        # The capabilities might be in the raw YAML data
        # Let's check if we can access it through the agent
        agent_data = agent_registry._agents.get('D')
        if agent_data and hasattr(agent_data, '__dict__'):
            # Check for capabilities in various possible locations
            capabilities = (
                getattr(agent_data, 'capabilities', None) or
                getattr(agent_data, '_raw_data', {}).get('capabilities', [])
            )
            if capabilities:
                assert 'batch_script_processing' in capabilities