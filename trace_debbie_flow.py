#!/usr/bin/env python3
"""Trace Debbie's mail processing flow with detailed logging."""

import subprocess
import sys
import time
import re
import os
import glob

# Create test conversation
test_file = 'test_trace_debbie.txt'
with open(test_file, 'w') as f:
    f.write("Use send_mail_with_switch to send a message to agent 'd' with subject 'Trace Test' and body 'Please answer: What is 3 + 3?'")

print("🔍 Running test to trace Debbie's flow...\n")

# Run the test
cmd = [
    sys.executable, '-m', 'ai_whisperer.interfaces.cli.main',
    '--config', 'config/main.yaml',
    'replay', test_file
]

# Capture all output
result = subprocess.run(cmd, capture_output=True, text=True)

# Find the log files
import glob
log_files = sorted(glob.glob('/home/deano/projects/AIWhisperer/logs/aiwhisperer_*_batch_*.log'), 
                   key=lambda x: os.path.getmtime(x), reverse=True)

print("\n📋 Analyzing Debbie's flow from logs...\n")

# Extract key events
for log_file in log_files[:3]:  # Check the 3 most recent logs
    print(f"\n📄 Checking {log_file}:")
    
    with open(log_file, 'r') as f:
        content = f.read()
        
    # Find Alice's API call
    alice_calls = re.findall(r'agent_a.*\[OPENROUTER\].*', content)
    if alice_calls:
        print("\n1️⃣ ALICE'S API CALL:")
        for call in alice_calls[:2]:
            print(f"   {call}")
    
    # Find mail send
    mail_sends = re.findall(r'.*send_mail_with_switch.*result.*', content)
    if mail_sends:
        print("\n2️⃣ MAIL SENT:")
        for send in mail_sends[:1]:
            print(f"   {send}")
    
    # Find Debbie activation
    debbie_activations = re.findall(r'.*activated via agent switch.*', content)
    if debbie_activations:
        print("\n3️⃣ DEBBIE ACTIVATED:")
        for activation in debbie_activations[:1]:
            print(f"   {activation}")
    
    # Find Debbie's API call
    debbie_calls = re.findall(r'agent_d.*\[OPENROUTER\].*', content)
    if debbie_calls:
        print("\n4️⃣ DEBBIE'S API CALL:")
        for call in debbie_calls[:2]:
            print(f"   {call}")
    
    # Find check_mail execution
    check_mails = re.findall(r'.*check_mail.*called.*|.*MAILBOX.*check_mail.*', content)
    if check_mails:
        print("\n5️⃣ CHECK_MAIL EXECUTED:")
        for check in check_mails[:2]:
            print(f"   {check}")
    
    # Find Debbie's response
    debbie_responses = re.findall(r'.*agent_d.*RETURNING RESULT.*', content)
    if debbie_responses:
        print("\n6️⃣ DEBBIE'S RESPONSE:")
        for response in debbie_responses[:1]:
            print(f"   {response}")
    
    # Find continuation check
    continuation_checks = re.findall(r'.*continuation.*agent_d.*|.*agent_d.*continuation.*', content, re.IGNORECASE)
    if continuation_checks:
        print("\n7️⃣ CONTINUATION CHECK:")
        for check in continuation_checks[:2]:
            print(f"   {check}")

import os
print(f"\n\n🔍 To see full Debbie flow, run:")
print(f"   grep -E 'agent_d|check_mail|OPENROUTER.*d\\b|activated via' {log_files[0]} | less")