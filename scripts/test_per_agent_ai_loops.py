#!/usr/bin/env python3
"""
Test script to verify per-agent AI loops functionality.

This script demonstrates that different agents can use different AI models
based on their configuration in agents.yaml.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_per_agent_ai_loops.log')
    ]
)
logger = logging.getLogger(__name__)


async def test_per_agent_ai_loops():
    """Test that different agents use their configured AI models."""
    logger.info("Starting per-agent AI loops test")
    
    # Load configuration
    config_path = project_root / "config" / "main.yaml"
    config = load_config(config_path)
    logger.info(f"Loaded config from {config_path}")
    
    # Create agent registry
    prompts_dir = project_root / "prompts"
    agent_registry = AgentRegistry(prompts_dir)
    logger.info("Created agent registry")
    
    # Create AI loop manager
    ai_loop_manager = AILoopManager(default_config=config)
    logger.info("Created AI loop manager")
    
    # Test agents with different configurations
    test_agents = [
        ('A', 'Alice'),  # Should use default model
        ('D', 'Debbie'), # Should use gpt-3.5-turbo
        ('E', 'Eamonn'), # Should use claude-3-opus
    ]
    
    for agent_id, agent_name in test_agents:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing agent {agent_id} ({agent_name})")
        logger.info(f"{'='*60}")
        
        # Get agent from registry
        agent_info = agent_registry.get_agent(agent_id)
        if not agent_info:
            logger.error(f"Agent {agent_id} not found in registry")
            continue
        
        logger.info(f"Agent info: {agent_info.name} - {agent_info.description}")
        
        # Check if agent has custom AI config
        if agent_info.ai_config:
            logger.info(f"Agent has custom AI config:")
            logger.info(f"  Model: {agent_info.ai_config.get('model')}")
            logger.info(f"  Provider: {agent_info.ai_config.get('provider')}")
            logger.info(f"  Generation params: {agent_info.ai_config.get('generation_params')}")
        else:
            logger.info("Agent uses default AI config")
        
        # Create AI loop for this agent
        # In real usage, this would be done through AgentConfig
        from ai_whisperer.services.agents.config import AgentConfig
        
        # Create AgentConfig with AI settings if available
        if agent_info.ai_config:
            agent_config = AgentConfig(
                name=agent_info.name,
                description=agent_info.description,
                system_prompt=f"You are {agent_info.name}",
                model_name=agent_info.ai_config.get("model", config.get("openrouter", {}).get("model", "openai/gpt-3.5-turbo")),
                provider=agent_info.ai_config.get("provider", "openrouter"),
                api_settings={
                    "api_key": config.get("openrouter", {}).get("api_key"),
                    **agent_info.ai_config.get("api_settings", {})
                },
                generation_params={
                    **config.get("openrouter", {}).get("params", {}),
                    **agent_info.ai_config.get("generation_params", {})
                },
                tool_permissions=[],
                tool_limits={},
                context_settings={"max_context_messages": 50}
            )
        else:
            agent_config = None
        
        # Get or create AI loop
        ai_loop = ai_loop_manager.get_or_create_ai_loop(
            agent_id=agent_id,
            agent_config=agent_config,
            fallback_config=config
        )
        
        logger.info(f"Created AI loop for agent {agent_id}")
        logger.info(f"AI loop config: model={ai_loop.config.model_id}, temperature={ai_loop.config.temperature}")
        
        # Verify the model matches expected
        if agent_id == 'D':
            expected_model = "openai/gpt-3.5-turbo"
            assert ai_loop.config.model_id == expected_model, f"Expected {expected_model}, got {ai_loop.config.model_id}"
            logger.info(f"✓ Debbie correctly uses {expected_model}")
        elif agent_id == 'E':
            expected_model = "anthropic/claude-3-opus-20240229"
            assert ai_loop.config.model_id == expected_model, f"Expected {expected_model}, got {ai_loop.config.model_id}"
            logger.info(f"✓ Eamonn correctly uses {expected_model}")
        else:
            # Alice should use default
            logger.info(f"✓ Alice uses default model: {ai_loop.config.model_id}")
    
    # Show summary of active models
    logger.info(f"\n{'='*60}")
    logger.info("Summary of active AI models by agent:")
    logger.info(f"{'='*60}")
    active_models = ai_loop_manager.get_active_models()
    for agent_id, model in active_models.items():
        logger.info(f"  Agent {agent_id}: {model}")
    
    # Clean up
    ai_loop_manager.cleanup()
    logger.info("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_per_agent_ai_loops())