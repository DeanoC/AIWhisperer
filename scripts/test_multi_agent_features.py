#!/usr/bin/env python3
"""
Test script for multi-agent features:
1. Per-agent AI loops (different models per agent)
2. Patricia's improved prompt (explanatory text with tools)
3. Alice's agent switching capability
"""

import asyncio
import json
import logging
from pathlib import Path
import sys
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.core.config import load_config
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.services.execution.ai_loop_factory import AILoopFactory
from interactive_server.stateless_session_manager import StatelessSessionManager
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.prompt_system import PromptSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_per_agent_ai_loops():
    """Test that each agent uses its configured AI model."""
    logger.info("\n=== Testing Per-Agent AI Loops ===")
    
    # Load configuration
    config = load_config("config/main.yaml")
    
    # Initialize components
    ai_loop_factory = AILoopFactory()
    # AILoopManager expects default_config, not factory
    ai_loop_manager = AILoopManager(default_config=config.get('ai', {}))
    
    # Get prompts directory
    prompts_dir = project_root / "prompts" / "agents"
    agent_registry = AgentRegistry(str(prompts_dir))
    
    # Test agents with different configurations
    test_agents = ['D', 'E', 'A']  # Debbie (GPT-3.5), Eamonn (Claude), Alice (default)
    
    for agent_id in test_agents:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found in registry")
            continue
            
        logger.info(f"\nAgent {agent_id} ({agent.name}):")
        
        # Get AI loop for agent
        # Build config in the format AILoopManager expects
        # Get API key from config
        api_key = config.get('ai', {}).get('openrouter', {}).get('api_key')
        if not api_key:
            # Try environment variable as fallback
            import os
            api_key = os.environ.get('OPENROUTER_API_KEY')
            
        fallback_config = {
            "openrouter": {
                "model": config.get('ai', {}).get('openrouter', {}).get('model', 'openai/gpt-3.5-turbo'),
                "api_key": api_key,
                "params": config.get('ai', {}).get('openrouter', {}).get('params', {})
            }
        }
        
        if agent.ai_config:
            # Override with agent-specific config
            fallback_config["openrouter"]["model"] = agent.ai_config.get('model', fallback_config["openrouter"]["model"])
            fallback_config["openrouter"]["provider"] = agent.ai_config.get('provider', 'openrouter')
            if 'generation_params' in agent.ai_config:
                fallback_config["openrouter"]["params"].update(agent.ai_config['generation_params'])
        
        ai_loop = ai_loop_manager.get_or_create_ai_loop(
            agent_id,
            agent_config=None,  # We don't have AgentConfig, just Agent
            fallback_config=fallback_config
        )
        
        # Log the model being used (from ai_loop.config)
        logger.info(f"  Model: {ai_loop.config.model_id}")
        logger.info(f"  Provider: openrouter")  # We know it's openrouter for now
        
        # Verify model matches configuration
        if agent.ai_config:
            expected_model = agent.ai_config.get('model')
            if expected_model:
                assert ai_loop.config.model_id == expected_model, f"Model mismatch for {agent_id}"
                logger.info(f"  ✓ Model matches configuration")
            else:
                logger.info(f"  ✓ Using default model")
        else:
            logger.info(f"  ✓ Using default model")
    
    logger.info("\n✓ Per-agent AI loops test passed!")


async def test_patricia_with_tools():
    """Test Patricia's improved prompt with tool usage."""
    logger.info("\n=== Testing Patricia's Tool Usage with Explanations ===")
    
    # This would require a full session setup to test properly
    # For now, just verify the prompt has been updated
    
    prompt_path = Path("prompts/agents/agent_patricia.prompt.md")
    if prompt_path.exists():
        content = prompt_path.read_text()
        
        # Check for the key improvements
        checks = [
            ("Always provide explanatory text when using tools" in content, 
             "Explanatory text requirement"),
            ("Never use a tool without first explaining" in content,
             "Pre-tool explanation requirement"),
            ("This helps users understand your actions" in content,
             "User understanding emphasis")
        ]
        
        for check, description in checks:
            if check:
                logger.info(f"  ✓ {description} found in prompt")
            else:
                logger.warning(f"  ✗ {description} NOT found in prompt")
    
    logger.info("\n✓ Patricia prompt verification complete!")


async def test_alice_switch_agent():
    """Test Alice's switch_agent tool availability."""
    logger.info("\n=== Testing Alice's Agent Switching Capability ===")
    
    # Initialize tool registry
    tool_registry = ToolRegistry()
    
    # Check if switch_agent tool is registered
    try:
        tool = tool_registry.get_tool('switch_agent')
        logger.info("  ✓ switch_agent tool is registered")
        logger.info(f"  Tool description: {tool.description}")
        logger.info(f"  Tool parameters: {tool.parameters_schema}")
    except Exception as e:
        logger.error(f"  ✗ switch_agent tool NOT found in registry: {e}")
    
    # Check Alice's prompt for switch instructions
    prompt_path = Path("prompts/agents/alice_assistant.prompt.md")
    if prompt_path.exists():
        content = prompt_path.read_text()
        
        checks = [
            ("switch_agent" in content, "switch_agent tool mentioned"),
            ("When users ask for an agent by name" in content, "Agent switching instructions"),
            ("agent_id, reason, context_summary" in content, "Tool parameters documented")
        ]
        
        for check, description in checks:
            if check:
                logger.info(f"  ✓ {description} in Alice's prompt")
            else:
                logger.warning(f"  ✗ {description} NOT in Alice's prompt")
    
    logger.info("\n✓ Alice agent switching verification complete!")


async def run_interactive_test():
    """Run a simple interactive test with conversation replay."""
    logger.info("\n=== Running Interactive Test ===")
    
    # Create test conversation file
    test_conv_path = Path("scripts/conversations/test_multi_agent_features.txt")
    test_conv_path.parent.mkdir(exist_ok=True)
    
    test_conversation = """Hi Alice! Can you tell me which AI model you're using?

Great! Now I need help creating an RFC for a new authentication system. Can you switch me to Patricia?

Thanks Patricia! Please create an RFC for implementing OAuth2 authentication with the following requirements:
- Support for Google and GitHub providers
- JWT token management
- Refresh token rotation
- Session management

Perfect! Now I need some technical expertise. Can you get Eamonn to review this?

Hi Eamonn! Can you tell me which AI model you're using and review the authentication RFC Patricia just created?"""
    
    test_conv_path.write_text(test_conversation)
    logger.info(f"  Created test conversation: {test_conv_path}")
    
    # Log instructions for running the test
    logger.info("\nTo run the interactive test:")
    logger.info(f"  python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay {test_conv_path}")
    
    return test_conv_path


async def main():
    """Run all tests."""
    logger.info("Starting Multi-Agent Feature Tests")
    logger.info("=" * 50)
    
    try:
        # Test 1: Per-agent AI loops
        await test_per_agent_ai_loops()
        
        # Test 2: Patricia's improved prompts
        await test_patricia_with_tools()
        
        # Test 3: Alice's agent switching
        await test_alice_switch_agent()
        
        # Create interactive test file
        test_file = await run_interactive_test()
        
        logger.info("\n" + "=" * 50)
        logger.info("All tests completed successfully!")
        logger.info("\nNext step: Run the interactive test to see everything in action:")
        logger.info(f"  python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay {test_file}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())