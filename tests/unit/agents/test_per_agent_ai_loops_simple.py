"""
Simple unit tests for per-agent AI loops functionality.

Tests the core per-agent AI loop features without loading real configs.
"""

import pytest
from unittest.mock import Mock, patch
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.services.execution.ai_loop_factory import AILoopConfig


class TestPerAgentAILoopsSimple:
    """Test per-agent AI loop functionality with simple mocks."""
    
    @pytest.fixture
    def default_config(self):
        """Create default test configuration."""
        return {
            "openrouter": {
                "model": "openai/gpt-3.5-turbo",
                "api_key": "test-key",
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 4000
                }
            }
        }
    
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
    
    def test_ai_loop_manager_with_different_configs(self, default_config):
        """Test AI loop manager creates different loops for different agents."""
        ai_loop_manager = AILoopManager(default_config=default_config)
        
        # Mock the AI loop factory
        with patch('ai_whisperer.services.agents.ai_loop_manager.AILoopFactory') as MockFactory:
            # Create mock AI loops
            mock_default_loop = Mock()
            mock_default_loop.config.model_id = "openai/gpt-3.5-turbo"
            
            mock_custom_loop = Mock()
            mock_custom_loop.config.model_id = "anthropic/claude-3-opus"
            
            MockFactory.create_ai_loop.side_effect = [mock_default_loop, mock_custom_loop]
            
            # Create AI loop with default config
            default_loop = ai_loop_manager.get_or_create_ai_loop("agent1")
            
            # Create AI loop with custom config
            custom_config = AgentConfig(
                name="Custom Agent",
                description="Test",
                system_prompt="Test",
                model_name="anthropic/claude-3-opus",
                provider="openrouter",
                api_settings={"api_key": "test"},
                generation_params={"temperature": 0.5, "max_tokens": 8000},
                tool_permissions=[],
                tool_limits={},
                context_settings={}
            )
            custom_loop = ai_loop_manager.get_or_create_ai_loop("agent2", custom_config)
            
            # Verify different models are used
            active_models = ai_loop_manager.get_active_models()
            assert len(active_models) == 2
            assert active_models["agent1"] == "openai/gpt-3.5-turbo"
            assert active_models["agent2"] == "anthropic/claude-3-opus"
            
            # Verify loops are cached
            same_loop = ai_loop_manager.get_or_create_ai_loop("agent1")
            assert same_loop == default_loop
    
    def test_ai_loop_manager_cleanup(self, default_config):
        """Test AI loop manager cleanup operations."""
        ai_loop_manager = AILoopManager(default_config=default_config)
        
        with patch('ai_whisperer.services.agents.ai_loop_manager.AILoopFactory') as MockFactory:
            mock_loop = Mock()
            mock_loop.config.model_id = "test/model"
            MockFactory.create_ai_loop.return_value = mock_loop
            
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