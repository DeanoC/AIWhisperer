#!/usr/bin/env python3
"""Test script to verify send_mail_with_switch tool registration."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.extensions.mailbox.tools import register_mailbox_tools

# Initialize registry
registry = ToolRegistry()

# Register mailbox tools
register_mailbox_tools()

# Try to get specific tools
print("Testing tool availability:")

# Test send_mail_with_switch
try:
    tool = registry.get_tool("send_mail_with_switch")
    print(f"✅ send_mail_with_switch is available!")
    print(f"   Name: {tool.name}")
    print(f"   Description: {tool.description}")
except Exception as e:
    print(f"❌ send_mail_with_switch error: {e}")

# Test other mail tools
for tool_name in ["send_mail", "check_mail", "reply_mail"]:
    try:
        tool = registry.get_tool(tool_name)
        print(f"✅ {tool_name} is available")
    except Exception as e:
        print(f"❌ {tool_name} error: {e}")