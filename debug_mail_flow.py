#!/usr/bin/env python3
"""Debug mail flow between agents"""

import asyncio
import json
from ai_whisperer.extensions.mailbox.mailbox import get_mailbox

# Get the mailbox
mailbox = get_mailbox()

print("=== Checking Mailbox State ===")
print(f"Mailbox type: {type(mailbox)}")
print(f"Mailbox singleton: {mailbox}")

# Check all agents' mail
agents = ['a', 'alice', 'd', 'debbie', 'p', 'patricia', 't', 'tessa', 'e', 'eamonn']

for agent in agents:
    all_mail = mailbox.check_mail(agent)  # Default shows unread
    unread_mail = mailbox.check_mail(agent)
    print(f"\n{agent}:")
    print(f"  Total messages: {len(all_mail)}")
    print(f"  Unread messages: {len(unread_mail)}")
    
    if all_mail:
        for mail in all_mail[:3]:  # Show first 3
            print(f"    - From: {mail.from_agent}, Subject: {mail.subject}, Read: {mail.read}")
            print(f"      Body: {mail.body[:50]}...")

# Test sending mail
print("\n=== Testing Mail Delivery ===")
message_id = mailbox.send_mail(
    from_agent="test",
    to_agent="debbie",
    subject="Debug Test",
    body="This is a test message"
)
print(f"Sent mail with ID: {message_id}")

# Check if it was delivered
debbie_mail = mailbox.check_mail("debbie", unread_only=True)
print(f"Debbie's unread messages after send: {len(debbie_mail)}")

if debbie_mail:
    latest = debbie_mail[0]
    print(f"Latest message: From={latest.from_agent}, Subject={latest.subject}")
    print(f"Body: {latest.body}")