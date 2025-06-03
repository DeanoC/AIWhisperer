"""
AI Loop Factory for creating configured AI loop instances.

This factory enables creation of AI loops with different configurations,
supporting the per-agent AI loop architecture.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass, field

from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.services.ai.base import AIService
from ai_whisperer.services.ai.openrouter import OpenRouterAIService

if TYPE_CHECKING:
    from ai_whisperer.services.agents.config import AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class AILoopConfig:
    """Configuration for creating an AI loop instance."""
    model: str = "openai/gpt-3.5-turbo"
    provider: str = "openrouter"
    temperature: float = 0.7
    max_tokens: int = 4000
    max_reasoning_tokens: Optional[int] = None
    api_key: Optional[str] = None
    api_settings: Dict[str, Any] = field(default_factory=dict)
    generation_params: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_agent_config(cls, agent_config: 'AgentConfig') -> 'AILoopConfig':
        """Create AILoopConfig from an AgentConfig."""
        # Merge generation params with explicit settings
        generation_params = agent_config.generation_params.copy()
        
        return cls(
            model=agent_config.model_name,
            provider=agent_config.provider,
            temperature=generation_params.get('temperature', 0.7),
            max_tokens=generation_params.get('max_tokens', 4000),
            max_reasoning_tokens=generation_params.get('max_reasoning_tokens'),
            api_key=agent_config.api_settings.get('api_key'),
            api_settings=agent_config.api_settings,
            generation_params=generation_params
        )


class AILoopFactory:
    """Factory for creating AI loop instances with different configurations."""
    
    # Registry of AI service providers
    _providers = {
        'openrouter': OpenRouterAIService,
        # Future: Add more providers here
        # 'anthropic': AnthropicAIService,
        # 'openai': OpenAIService,
    }
    
    @classmethod
    def create_ai_loop(
        cls,
        config: AILoopConfig,
        agent_context: Optional[Dict[str, Any]] = None
    ) -> StatelessAILoop:
        """
        Create a configured AI loop instance.
        
        Args:
            config: AI loop configuration
            agent_context: Optional agent context information
            
        Returns:
            Configured StatelessAILoop instance
            
        Raises:
            ValueError: If provider is not supported
        """
        # Create AI config
        ai_config = AIConfig(
            api_key=config.api_key,
            model_id=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            max_reasoning_tokens=config.max_reasoning_tokens
        )
        
        # Create AI service
        provider_class = cls._providers.get(config.provider)
        if not provider_class:
            raise ValueError(f"Unsupported AI provider: {config.provider}")
            
        ai_service = provider_class(config=ai_config)
        
        # Create and return AI loop
        ai_loop = StatelessAILoop(
            config=ai_config,
            ai_service=ai_service,
            agent_context=agent_context
        )
        
        logger.info(
            f"Created AI loop with model={config.model}, "
            f"provider={config.provider}, temperature={config.temperature}"
        )
        
        return ai_loop
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a new AI service provider."""
        cls._providers[name] = provider_class
        logger.info(f"Registered AI provider: {name}")