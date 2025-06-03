"""Tests for AILoopFactory."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ai_whisperer.services.execution.ai_loop_factory import AILoopFactory, AILoopConfig
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.execution.ai_loop import StatelessAILoop


class TestAILoopConfig:
    """Test AILoopConfig dataclass."""
    
    def test_default_values(self):
        """Test default AILoopConfig values."""
        config = AILoopConfig()
        assert config.model == "openai/gpt-3.5-turbo"
        assert config.provider == "openrouter"
        assert config.temperature == 0.7
        assert config.max_tokens == 4000
        assert config.max_reasoning_tokens is None
        assert config.api_key is None
        assert config.api_settings == {}
        assert config.generation_params == {}
    
    def test_custom_values(self):
        """Test AILoopConfig with custom values."""
        config = AILoopConfig(
            model="anthropic/claude-3-opus",
            provider="openrouter",
            temperature=0.5,
            max_tokens=8000,
            max_reasoning_tokens=2000,
            api_key="test-key",
            api_settings={"timeout": 30},
            generation_params={"top_p": 0.9}
        )
        
        assert config.model == "anthropic/claude-3-opus"
        assert config.temperature == 0.5
        assert config.max_tokens == 8000
        assert config.max_reasoning_tokens == 2000
        assert config.api_key == "test-key"
        assert config.api_settings == {"timeout": 30}
        assert config.generation_params == {"top_p": 0.9}
    
    def test_from_agent_config(self):
        """Test creating AILoopConfig from AgentConfig."""
        # Create mock AgentConfig
        agent_config = Mock(spec=AgentConfig)
        agent_config.model_name = "anthropic/claude-3-opus"
        agent_config.provider = "openrouter"
        agent_config.api_settings = {"api_key": "test-key", "timeout": 30}
        agent_config.generation_params = {
            "temperature": 0.8,
            "max_tokens": 6000,
            "max_reasoning_tokens": 1500,
            "top_p": 0.95
        }
        
        # Create AILoopConfig from AgentConfig
        loop_config = AILoopConfig.from_agent_config(agent_config)
        
        # Verify values were transferred correctly
        assert loop_config.model == "anthropic/claude-3-opus"
        assert loop_config.provider == "openrouter"
        assert loop_config.temperature == 0.8
        assert loop_config.max_tokens == 6000
        assert loop_config.max_reasoning_tokens == 1500
        assert loop_config.api_key == "test-key"
        assert loop_config.api_settings == {"api_key": "test-key", "timeout": 30}
        assert loop_config.generation_params == agent_config.generation_params


class TestAILoopFactory:
    """Test AILoopFactory functionality."""
    
    def test_create_ai_loop_openrouter(self):
        """Test creating an AI loop with OpenRouter provider."""
        config = AILoopConfig(
            model="openai/gpt-3.5-turbo",
            provider="openrouter",
            api_key="test-key",
            temperature=0.7,
            max_tokens=4000
        )
        
        agent_context = {"agent_id": "test_agent", "agent_name": "Test Agent"}
        
        # Mock the entire class lookup in _providers
        mock_service_instance = Mock()
        mock_loop_instance = Mock()
        
        # Create a mock provider class that returns our mock service
        MockProviderClass = Mock(return_value=mock_service_instance)
        
        with patch.object(AILoopFactory, '_providers', {'openrouter': MockProviderClass}):
            with patch('ai_whisperer.services.execution.ai_loop_factory.StatelessAILoop') as MockLoop:
                MockLoop.return_value = mock_loop_instance
                
                # Create AI loop
                ai_loop = AILoopFactory.create_ai_loop(config, agent_context)
                
                # Verify provider class was instantiated
                MockProviderClass.assert_called_once()
                call_kwargs = MockProviderClass.call_args[1]
                assert 'config' in call_kwargs
                ai_config = call_kwargs['config']
                
                # Verify the AIConfig has correct values
                assert isinstance(ai_config, AIConfig)
                assert ai_config.api_key == "test-key"
                assert ai_config.model_id == "openai/gpt-3.5-turbo"
                assert ai_config.temperature == 0.7
                assert ai_config.max_tokens == 4000
                assert ai_config.max_reasoning_tokens is None
                
                # Verify StatelessAILoop was created
                MockLoop.assert_called_once_with(
                    config=ai_config,
                    ai_service=mock_service_instance,
                    agent_context=agent_context
                )
                
                assert ai_loop == mock_loop_instance
    
    def test_create_ai_loop_unsupported_provider(self):
        """Test creating an AI loop with unsupported provider."""
        config = AILoopConfig(
            model="some/model",
            provider="unsupported_provider",
            api_key="test-key"
        )
        
        with pytest.raises(ValueError, match="Unsupported AI provider: unsupported_provider"):
            AILoopFactory.create_ai_loop(config)
    
    def test_create_ai_loop_without_agent_context(self):
        """Test creating an AI loop without agent context."""
        config = AILoopConfig(
            model="openai/gpt-3.5-turbo",
            provider="openrouter",
            api_key="test-key"
        )
        
        # Mock the entire class lookup in _providers
        mock_service_instance = Mock()
        mock_loop_instance = Mock()
        
        # Create a mock provider class that returns our mock service
        MockProviderClass = Mock(return_value=mock_service_instance)
        
        with patch.object(AILoopFactory, '_providers', {'openrouter': MockProviderClass}):
            with patch('ai_whisperer.services.execution.ai_loop_factory.StatelessAILoop') as MockLoop:
                MockLoop.return_value = mock_loop_instance
                
                # Create AI loop without agent context
                ai_loop = AILoopFactory.create_ai_loop(config, agent_context=None)
                
                # Verify StatelessAILoop was created with None agent_context
                MockLoop.assert_called_once()
                call_args = MockLoop.call_args[1]
                assert call_args['agent_context'] is None
                
                assert ai_loop == mock_loop_instance
    
    def test_register_provider(self):
        """Test registering a new AI provider."""
        # Create a mock provider class
        MockProvider = Mock()
        
        # Register it
        AILoopFactory.register_provider("test_provider", MockProvider)
        
        # Verify it's in the registry
        assert "test_provider" in AILoopFactory._providers
        assert AILoopFactory._providers["test_provider"] == MockProvider
        
        # Test using the registered provider
        config = AILoopConfig(
            model="test/model",
            provider="test_provider",
            api_key="test-key"
        )
        
        # Set up mocks
        mock_service_instance = Mock()
        MockProvider.return_value = mock_service_instance
        
        with patch('ai_whisperer.services.execution.ai_loop_factory.StatelessAILoop') as MockLoop:
            mock_loop_instance = Mock()
            MockLoop.return_value = mock_loop_instance
            
            # Create AI loop with custom provider
            ai_loop = AILoopFactory.create_ai_loop(config)
            
            # Verify custom provider was used
            MockProvider.assert_called_once()
            assert ai_loop == mock_loop_instance
        
        # Clean up - remove the test provider
        del AILoopFactory._providers["test_provider"]