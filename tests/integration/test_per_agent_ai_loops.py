"""
Integration tests for per-agent AI loops functionality.

Tests that different agents can use different AI models and configurations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path

from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.services.execution.ai_loop_factory import AILoopConfig
from ai_whisperer.core.config import load_config
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.utils.path import PathManager


class TestPerAgentAILoops:
    """Test per-agent AI loop functionality."""
    
    @pytest.fixture
    def config(self):
        """Load test configuration."""
        config_path = Path(__file__).parent.parent.parent / "config" / "main.yaml"
        return load_config(config_path)
    
    @pytest.fixture
    def agent_registry(self):
        """Create agent registry."""
        # Initialize PathManager first
        path_manager = PathManager.get_instance()
        project_root = Path(__file__).parent.parent.parent
        path_manager.initialize(config_values={'workspace_path': str(project_root)})
        
        prompts_dir = project_root / "prompts"
        return AgentRegistry(prompts_dir)
    
    @pytest.fixture
    def ai_loop_manager(self, config):
        """Create AI loop manager."""
        return AILoopManager(default_config=config)
    
    def test_agent_registry_loads_ai_configs(self, agent_registry):
        """Test that agent registry correctly loads AI configurations."""
        # Check Debbie has custom AI config
        debbie = agent_registry.get_agent("D")
        assert debbie is not None
        assert debbie.ai_config is not None
        assert debbie.ai_config["model"] == "openai/gpt-3.5-turbo"
        assert debbie.ai_config["generation_params"]["temperature"] == 0.5
        
        # Check Eamonn has custom AI config
        eamonn = agent_registry.get_agent("E")
        assert eamonn is not None
        assert eamonn.ai_config is not None
        assert eamonn.ai_config["model"] == "anthropic/claude-3-opus-20240229"
        assert eamonn.ai_config["generation_params"]["max_tokens"] == 8000
        
        # Check Alice has no custom AI config (uses default)
        alice = agent_registry.get_agent("A")
        assert alice is not None
        assert alice.ai_config is None
    
    def test_ai_loop_config_from_agent_config(self):
        """Test creating AILoopConfig from AgentConfig."""
        agent_config = AgentConfig(
            name="Test Agent",
            description="Test",
            system_prompt="Test prompt",
            model_name="test/model",
            provider="test_provider",
            api_settings={"api_key": "test_key"},
            generation_params={"temperature": 0.8, "max_tokens": 5000},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        
        ai_loop_config = AILoopConfig.from_agent_config(agent_config)
        
        assert ai_loop_config.model == "test/model"
        assert ai_loop_config.provider == "test_provider"
        assert ai_loop_config.temperature == 0.8
        assert ai_loop_config.max_tokens == 5000
        assert ai_loop_config.api_key == "test_key"
    
    def test_ai_loop_manager_creates_different_loops(self, ai_loop_manager, agent_registry):
        """Test that AI loop manager creates different loops for different agents."""
        # Create AI loop for Alice (default config)
        alice_info = agent_registry.get_agent("A")
        alice_loop = ai_loop_manager.get_or_create_ai_loop("A")
        
        # Create AI loop for Debbie (custom config)
        debbie_info = agent_registry.get_agent("D")
        debbie_config = AgentConfig(
            name=debbie_info.name,
            description=debbie_info.description,
            system_prompt="Test",
            model_name="openai/gpt-3.5-turbo",
            provider="openrouter",
            api_settings={"api_key": "test"},
            generation_params={"temperature": 0.5, "max_tokens": 2000},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        debbie_loop = ai_loop_manager.get_or_create_ai_loop("D", debbie_config)
        
        # Create AI loop for Eamonn (custom config)
        eamonn_info = agent_registry.get_agent("E")
        eamonn_config = AgentConfig(
            name=eamonn_info.name,
            description=eamonn_info.description,
            system_prompt="Test",
            model_name="anthropic/claude-3-opus-20240229",
            provider="openrouter",
            api_settings={"api_key": "test"},
            generation_params={"temperature": 0.7, "max_tokens": 8000},
            tool_permissions=[],
            tool_limits={},
            context_settings={}
        )
        eamonn_loop = ai_loop_manager.get_or_create_ai_loop("E", eamonn_config)
        
        # Verify different models are used
        active_models = ai_loop_manager.get_active_models()
        assert len(active_models) == 3
        assert active_models["D"] == "openai/gpt-3.5-turbo"
        assert active_models["E"] == "anthropic/claude-3-opus-20240229"
        
        # Verify configurations
        assert ai_loop_manager._ai_loops["D"].config.temperature == 0.5
        assert ai_loop_manager._ai_loops["D"].config.max_tokens == 2000
        assert ai_loop_manager._ai_loops["E"].config.temperature == 0.7
        assert ai_loop_manager._ai_loops["E"].config.max_tokens == 8000
    
    def test_ai_loop_manager_cleanup(self, ai_loop_manager):
        """Test AI loop manager cleanup."""
        # Create some AI loops
        ai_loop_manager.get_or_create_ai_loop("test1")
        ai_loop_manager.get_or_create_ai_loop("test2")
        
        assert len(ai_loop_manager._ai_loops) == 2
        
        # Remove one
        assert ai_loop_manager.remove_ai_loop("test1") is True
        assert len(ai_loop_manager._ai_loops) == 1
        assert "test1" not in ai_loop_manager._ai_loops
        
        # Cleanup all
        ai_loop_manager.cleanup()
        assert len(ai_loop_manager._ai_loops) == 0
    
    @pytest.mark.asyncio
    async def test_session_uses_per_agent_loops(self, config, agent_registry):
        """Test that interactive session correctly uses per-agent AI loops."""
        from interactive_server.stateless_session_manager import StatelessInteractiveSession
        
        # Create mock websocket
        mock_websocket = Mock()
        mock_websocket.send_json = Mock(return_value=asyncio.Future())
        mock_websocket.send_json.return_value.set_result(None)
        
        # Create prompt system
        prompt_system = PromptSystem(Path(__file__).parent.parent.parent / "prompts")
        
        # Create session
        session = StatelessInteractiveSession(
            session_id="test",
            websocket=mock_websocket,
            config=config,
            agent_registry=agent_registry,
            prompt_system=prompt_system
        )
        
        try:
            # Start session (creates default agent)
            await session.start_ai_session()
            
            # Switch to Debbie
            await session.switch_agent("d")
            
            # Verify Debbie's AI loop uses correct model
            active_models = session.ai_loop_manager.get_active_models()
            # Agent IDs are lowercase in the session
            assert "d" in active_models
            assert active_models["d"] == "openai/gpt-3.5-turbo"
            
            # Switch to Eamonn
            await session.switch_agent("e")
            
            # Verify Eamonn's AI loop uses correct model
            active_models = session.ai_loop_manager.get_active_models()
            assert "e" in active_models
            assert active_models["e"] == "anthropic/claude-3-opus-20240229"
            
            # Verify both AI loops exist
            assert len(active_models) >= 2
            
        finally:
            await session.cleanup()