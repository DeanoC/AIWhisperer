#!/usr/bin/env python3
"""
Simple test to isolate tool calling issue.

This test:
1. Sends mail to Debbie asking her to use list_directory
2. Switches to Debbie  
3. Debbie should check mail, find the request, execute list_directory, and return results
"""

import asyncio
import json
from ai_whisperer.core.config import load_config
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox


async def test_simple_tool_flow():
    """Test the simple flow: check mail -> execute tool -> return results"""
    
    # Load config
    config = load_config("config/main.yaml")
    
    # Initialize components
    from ai_whisperer.services.agents.registry import AgentRegistry
    from ai_whisperer.prompt_system import PromptSystem
    from ai_whisperer.utils.path import PathManager
    
    path_manager = PathManager()
    tool_registry = ToolRegistry()
    prompt_system = PromptSystem(tool_registry)
    agent_registry = AgentRegistry(path_manager.prompt_path / "agents")
    
    agent_factory = AgentFactory()
    agent_factory.initialize(config, agent_registry, prompt_system, tool_registry)
    
    mailbox = get_mailbox()
    
    print("=== Starting Simple Tool Flow Test ===\n")
    
    # Step 1: Send mail to Debbie
    print("1. Sending mail to Debbie...")
    mailbox.send_mail(
        from_agent="test",
        to_agent="debbie", 
        subject="Simple Tool Request",
        body="Please use the list_directory tool to show the contents of the current directory (path='.').",
        priority="high"
    )
    
    # Check mail was delivered
    debbie_mail = mailbox.check_mail("debbie")
    print(f"   ✓ Mail delivered: {len(debbie_mail)} messages in Debbie's inbox")
    print(f"   Subject: {debbie_mail[0].subject}")
    print(f"   Body: {debbie_mail[0].body}\n")
    
    # Step 2: Create Debbie agent
    print("2. Creating Debbie agent...")
    debbie = await agent_factory.create_agent("d")
    print(f"   ✓ Agent created: {debbie.agent_id}\n")
    
    # Step 3: Have Debbie process the request
    print("3. Debbie processing (checking mail and executing tool)...")
    
    # First, let's see what tools Debbie has
    debbie_tools = debbie._get_agent_tools()
    print(f"   Available tools: {[tool.name for tool in debbie_tools]}")
    
    # Process a simple activation message
    result = await debbie.process_message("You've been activated. Please check your mail and execute any tool requests you find.")
    
    print("\n4. Result from Debbie:")
    print("   Type:", type(result))
    
    if isinstance(result, dict):
        print("   Keys:", result.keys())
        
        if 'response' in result:
            print("   Response:", result['response'])
        
        if 'tool_calls' in result:
            print("   Tool calls:", len(result.get('tool_calls', [])))
            for tc in result.get('tool_calls', []):
                print(f"     - {tc}")
        
        if 'error' in result:
            print("   Error:", result['error'])
            
        if 'finish_reason' in result:
            print("   Finish reason:", result['finish_reason'])
    else:
        print("   Raw result:", result)
    
    # Check if mail was marked as read
    remaining_mail = mailbox.check_mail("debbie", unread_only=True)
    print(f"\n5. Remaining unread mail: {len(remaining_mail)}")
    
    print("\n=== Test Complete ===")


if __name__ == "__main__":
    asyncio.run(test_simple_tool_flow())