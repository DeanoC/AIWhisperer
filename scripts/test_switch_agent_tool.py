#!/usr/bin/env python3
"""
Test the new switch_agent tool functionality.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.core.config import load_config
from ai_whisperer.tools.switch_agent_tool import SwitchAgentTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_switch_agent_tool():
    """Test the switch agent tool."""
    logger.info("Testing SwitchAgentTool")
    
    # Create tool instance
    tool = SwitchAgentTool()
    
    # Test tool definition
    logger.info(f"Tool name: {tool.name}")
    logger.info(f"Tool description: {tool.description}")
    logger.info(f"Parameters schema: {tool.parameters_schema}")
    
    # Test AI instructions
    logger.info("\nAI Instructions:")
    logger.info(tool.get_ai_instructions())
    
    # Test execution without session (should fail gracefully)
    result = await tool.execute(
        agent_id="p",
        reason="Test switch to Patricia",
        context_summary="Testing agent switching functionality"
    )
    
    logger.info(f"\nExecution result: {result}")
    
    # Verify it fails appropriately without session
    assert result['success'] is False
    assert 'session' in result['error'].lower()
    
    logger.info("\nTest completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_switch_agent_tool())