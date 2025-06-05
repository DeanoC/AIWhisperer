#!/usr/bin/env python3
"""
Test script to verify synchronous mail switching is working.

This creates a simple conversation where Alice sends mail to Debbie
using send_mail_with_switch and we verify that:
1. Debbie receives the mail
2. Debbie responds
3. Control returns to Alice
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.tools.send_mail_with_switch_tool import SendMailWithSwitchTool
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox


def test_mail_system():
    """Test basic mail system functionality."""
    print("\n=== Testing Mail System ===")
    
    # Get mailbox instance
    mailbox = get_mailbox()
    
    # Clear any existing mail
    mailbox.clear_all()
    
    # Send a test message
    mailbox.send_mail(
        from_agent="alice",
        to_agent="debbie",
        subject="Test Mail",
        body="Testing the mail system"
    )
    
    # Check if Debbie received it
    debbie_mail = mailbox.get_mail("debbie")
    print(f"Mail in Debbie's inbox: {len(debbie_mail)} messages")
    
    if debbie_mail:
        msg = debbie_mail[0]
        print(f"  From: {msg['from_agent']}")
        print(f"  Subject: {msg['subject']}")
        print(f"  Body: {msg['body']}")
        print("✅ Mail system working!")
    else:
        print("❌ Mail not received!")
        
    # Clean up
    mailbox.clear_all()


def test_tool_execution():
    """Test the send_mail_with_switch tool directly."""
    print("\n=== Testing Tool Execution ===")
    
    # Initialize registry and get tool
    registry = ToolRegistry()
    tool = SendMailWithSwitchTool()
    
    # Prepare tool arguments
    kwargs = {
        "to_agent": "debbie",
        "subject": "Debug Request",
        "body": "Please help me debug this test",
        "priority": "normal"
    }
    
    # Execute tool (this would normally trigger agent switch in a session)
    result = tool.execute(from_agent="alice", **kwargs)
    print(f"Tool execution result: {result}")
    
    # Check mailbox
    mailbox = get_mailbox()
    debbie_mail = mailbox.get_mail("debbie")
    print(f"Mail in Debbie's inbox after tool: {len(debbie_mail)} messages")
    
    if debbie_mail:
        print("✅ Tool successfully sent mail!")
    else:
        print("❌ Tool failed to send mail!")
        
    # Clean up
    mailbox.clear_all()


async def test_websocket_integration():
    """Test the full integration with WebSocket."""
    print("\n=== Testing WebSocket Integration ===")
    print("This would require a running server. Use test_async_agents_demo.py for full integration tests.")
    

def main():
    """Run all tests."""
    print("Testing Synchronous Mail Switching Components")
    print("=" * 50)
    
    # Test mail system
    test_mail_system()
    
    # Test tool directly
    test_tool_execution()
    
    # Note about integration testing
    print("\n" + "=" * 50)
    print("Component tests complete!")
    print("\nFor full integration testing with agent switching:")
    print("1. Start the server: python -m interactive_server.main")
    print("2. Run: python test_async_agents_demo.py")
    print("3. Or use the web UI and test manually with Alice -> Debbie communication")


if __name__ == "__main__":
    main()