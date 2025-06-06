#!/usr/bin/env python3
"""Test script to debug check_mail tool return value"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_whisperer.core.config import load_config
from ai_whisperer.tools.send_mail_tool import SendMailTool
from ai_whisperer.tools.check_mail_tool import CheckMailTool
from ai_whisperer.extensions.mailbox.mailbox import reset_mailbox

async def test_mail_flow():
    # Load config
    config = load_config("config/main.yaml")
    
    # Reset mailbox for clean test
    reset_mailbox()
    
    # Create tools
    send_tool = SendMailTool()
    check_tool = CheckMailTool()
    
    # Send a mail from Alice to Debbie
    print("1. Sending mail from Alice to Debbie...")
    send_result = send_tool.execute(
        to_agent="debbie",
        subject="Directory Listing Request",
        body="Please use the list_directory tool to show me the contents of the current directory.",
        _agent_name="a",
        _from_agent="a"
    )
    print(f"Send result: {send_result}")
    
    # Check mail as Debbie
    print("\n2. Checking mail as Debbie...")
    check_result = check_tool.execute(
        _agent_name="d",
        _from_agent="d"
    )
    print(f"Check result: {check_result}")
    
    # Print the message details
    if check_result.get("messages"):
        print("\n3. Message details:")
        for msg in check_result["messages"]:
            print(f"  - From: {msg['from']}")
            print(f"  - Subject: {msg['subject']}")
            print(f"  - Body: {msg['body']}")
    else:
        print("\n3. No messages found!")

if __name__ == "__main__":
    asyncio.run(test_mail_flow())