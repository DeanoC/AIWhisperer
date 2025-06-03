"""
AI Loop Manager for managing per-agent AI loop instances.

This manager maintains a registry of AI loops for each agent,
enabling different AI models and configurations per agent.
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.services.execution.ai_loop_factory import AILoopFactory, AILoopConfig
from ai_whisperer.services.agents.config import AgentConfig

logger = logging.getLogger(__name__)


@dataclass
class AILoopEntry:
    """Entry for tracking an AI loop instance."""
    agent_id: str
    ai_loop: StatelessAILoop
    config: AILoopConfig
    

class AILoopManager:
    """
    Manages AI loop instances for agents.
    
    This manager ensures each agent has its own AI loop instance
    with potentially different AI models and configurations.
    """
    
    def __init__(self, default_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Loop Manager.
        
        Args:
            default_config: Default configuration for AI loops when agent
                          doesn't specify custom settings
        """
        self._ai_loops: Dict[str, AILoopEntry] = {}
        self._default_config = default_config or {}
        logger.info("AILoopManager initialized")
    
    def get_or_create_ai_loop(
        self,
        agent_id: str,
        agent_config: Optional[AgentConfig] = None,
        fallback_config: Optional[Dict[str, Any]] = None
    ) -> StatelessAILoop:
        """
        Get existing AI loop for agent or create a new one.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_config: Optional agent configuration with AI settings
            fallback_config: Fallback configuration if agent config missing
            
        Returns:
            StatelessAILoop instance for the agent
        """
        # Check if we already have an AI loop for this agent
        if agent_id in self._ai_loops:
            logger.debug(f"Returning existing AI loop for agent {agent_id}")
            return self._ai_loops[agent_id].ai_loop
        
        # Create new AI loop
        logger.info(f"Creating new AI loop for agent {agent_id}")
        
        # Determine configuration
        if agent_config:
            # Use agent-specific configuration
            loop_config = AILoopConfig.from_agent_config(agent_config)
            logger.info(
                f"Using agent-specific config: model={loop_config.model}, "
                f"provider={loop_config.provider}"
            )
        else:
            # Use fallback or default configuration
            config_dict = fallback_config or self._default_config
            loop_config = self._create_config_from_dict(config_dict)
            logger.info(
                f"Using default config: model={loop_config.model}, "
                f"provider={loop_config.provider}"
            )
        
        # Create agent context
        agent_context = {
            'agent_id': agent_id,
            'agent_name': agent_config.name if agent_config else agent_id
        }
        
        # Create AI loop
        ai_loop = AILoopFactory.create_ai_loop(loop_config, agent_context)
        
        # Store in registry
        self._ai_loops[agent_id] = AILoopEntry(
            agent_id=agent_id,
            ai_loop=ai_loop,
            config=loop_config
        )
        
        return ai_loop
    
    def _create_config_from_dict(self, config_dict: Dict[str, Any]) -> AILoopConfig:
        """Create AILoopConfig from a configuration dictionary."""
        openrouter_config = config_dict.get("openrouter", {})
        params = openrouter_config.get("params", {})
        
        return AILoopConfig(
            model=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
            provider="openrouter",  # Default for now
            temperature=params.get("temperature", 0.7),
            max_tokens=params.get("max_tokens", 4000),
            max_reasoning_tokens=params.get("max_reasoning_tokens"),
            api_key=openrouter_config.get("api_key"),
            generation_params=params
        )
    
    def remove_ai_loop(self, agent_id: str) -> bool:
        """
        Remove an AI loop from the manager.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if removed, False if not found
        """
        if agent_id in self._ai_loops:
            del self._ai_loops[agent_id]
            logger.info(f"Removed AI loop for agent {agent_id}")
            return True
        return False
    
    def get_ai_loop(self, agent_id: str) -> Optional[StatelessAILoop]:
        """
        Get AI loop for an agent without creating.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AI loop instance or None if not found
        """
        entry = self._ai_loops.get(agent_id)
        return entry.ai_loop if entry else None
    
    def get_active_models(self) -> Dict[str, str]:
        """
        Get a summary of active models by agent.
        
        Returns:
            Dictionary mapping agent_id to model name
        """
        return {
            agent_id: entry.config.model
            for agent_id, entry in self._ai_loops.items()
        }
    
    def cleanup(self):
        """Clean up all AI loops."""
        for agent_id in list(self._ai_loops.keys()):
            self.remove_ai_loop(agent_id)
        logger.info("AILoopManager cleaned up")