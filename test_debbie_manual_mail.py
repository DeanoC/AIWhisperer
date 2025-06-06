#!/usr/bin/env python3
"""Test Debbie by manually adding mail to the mailbox before she checks"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ai_whisperer.extensions.mailbox.mailbox import get_mailbox, Mail, MessagePriority, MessageStatus
from datetime import datetime
import subprocess
import time

print("=== Manual Mail Test for Debbie ===")

# Get the mailbox instance
mailbox = get_mailbox()
print(f"✓ Got mailbox instance")

# Create a test mail
test_mail = Mail(
    message_id="manual-test-001",
    from_agent="alice",
    to_agent="d",  # Try "d" which is Debbie's agent ID
    subject="Tool Request",
    body="Please use the list_directory tool to show the contents of the current directory.",
    timestamp=datetime.now(),
    priority=MessagePriority.NORMAL,
    status=MessageStatus.UNREAD
)

# Add the mail to Debbie's inbox
mailbox.send_mail(test_mail)
print(f"✓ Added test mail to mailbox for agent 'd'")

# Also try "debbie" in case that's the issue
test_mail2 = Mail(
    message_id="manual-test-002", 
    from_agent="alice",
    to_agent="debbie",  # Try full name
    subject="Tool Request",
    body="Please use the list_directory tool to show the contents of the current directory.",
    timestamp=datetime.now(),
    priority=MessagePriority.NORMAL,
    status=MessageStatus.UNREAD
)
mailbox.send_mail(test_mail2)
print(f"✓ Added test mail to mailbox for agent 'debbie'")

# Check what's in the mailbox
print("\n=== Checking mailbox state ===")
for agent_name in ["d", "debbie", "Debbie", "D"]:
    messages = mailbox.get_all_mail(agent_name, include_read=True, include_archived=True)
    print(f"Agent '{agent_name}': {len(messages)} messages")
    if messages:
        for msg in messages:
            print(f"  - ID: {msg.message_id}, From: {msg.from_agent}, Status: {msg.status}")

# Now run Debbie to check her mail
print("\n=== Running Debbie to check mail ===")
result = subprocess.run([
    sys.executable, "-m", "ai_whisperer.interfaces.cli.main",
    "--config", "config/main.yaml", 
    "replay", "test_debbie_check_separate.txt"
], env={**os.environ, "AIWHISPERER_DEFAULT_AGENT": "d"})

print(f"\n✓ Test completed with exit code: {result.returncode}")