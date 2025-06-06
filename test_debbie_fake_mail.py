#!/usr/bin/env python3
"""Test Debbie with a fake mail response to isolate tool execution"""

import asyncio
import json
from datetime import datetime, timezone
from ai_whisperer.core.config import load_config
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.utils.path import PathManager
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, MessageStatus

async def test_debbie_with_fake_mail():
    """Test Debbie's response to a fake mail asking for tool execution"""
    
    # Load config
    config = load_config("config/main.yaml")
    
    # Initialize components
    path_manager = PathManager()
    tool_registry = ToolRegistry()
    prompt_system = PromptSystem(tool_registry)
    agent_registry = AgentRegistry(path_manager.prompt_path / "agents")
    
    # Create Debbie
    from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
    from ai_whisperer.services.execution.ai_loop_factory import AILoopFactory
    
    # Get Debbie's config
    debbie_info = agent_registry.get_agent('d')
    
    # Create AI loop manager
    ai_loop_manager = AILoopManager(config)
    
    # Create Debbie agent
    debbie = StatelessAgent(
        agent_id='d',
        agent_registry_info=debbie_info,
        config=config,
        prompt_system=prompt_system,
        tool_registry=tool_registry,
        ai_loop_manager=ai_loop_manager
    )
    
    print("=== Testing Debbie with Fake Mail ===\n")
    
    # Create a fake mail object that matches what Alice would send
    fake_mail = Mail(
        message_id="fake-123",
        from_agent="alice",
        to_agent="debbie",
        subject="Tool Request",
        body="Please use the list_directory tool to show the contents of the current directory.",
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(timezone.utc),
        status=MessageStatus.UNREAD
    )
    
    # Create a fake check_mail response
    fake_check_mail_response = {
        "messages": [fake_mail.to_dict()],
        "count": 1,
        "total_count": 1,
        "unread_only": True,
        "truncated": False
    }
    
    print("1. Fake mail created:")
    print(f"   From: {fake_mail.from_agent}")
    print(f"   To: {fake_mail.to_agent}")
    print(f"   Subject: {fake_mail.subject}")
    print(f"   Body: {fake_mail.body}\n")
    
    # Now we need to monkey-patch the check_mail tool to return our fake response
    original_check_mail = None
    for tool in tool_registry._tools.values():
        if tool.name == "check_mail":
            original_check_mail = tool.execute
            
            async def fake_check_mail_execute(**kwargs):
                print("   [FAKE] check_mail called, returning fake mail")
                return fake_check_mail_response
            
            tool.execute = fake_check_mail_execute
            break
    
    print("2. check_mail tool patched to return fake mail\n")
    
    # Process message asking Debbie to check mail
    print("3. Asking Debbie to check mail and execute tool requests...\n")
    
    result = await debbie.process_message(
        "Check your mail and execute any tool requests you find."
    )
    
    print("\n4. Result from Debbie:")
    print(f"   Type: {type(result)}")
    
    if isinstance(result, dict):
        print(f"   Keys: {result.keys()}")
        
        if 'response' in result:
            print(f"   Response: {result['response']}")
        
        if 'tool_calls' in result:
            print(f"   Tool calls: {len(result.get('tool_calls', []))}")
            for i, tc in enumerate(result.get('tool_calls', [])):
                print(f"     [{i+1}] {tc}")
        
        if 'error' in result:
            print(f"   Error: {result['error']}")
            
        if 'finish_reason' in result:
            print(f"   Finish reason: {result['finish_reason']}")
    else:
        print(f"   Raw result: {result}")
    
    # Restore original check_mail
    if original_check_mail:
        for tool in tool_registry._tools.values():
            if tool.name == "check_mail":
                tool.execute = original_check_mail
                break
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_debbie_with_fake_mail())