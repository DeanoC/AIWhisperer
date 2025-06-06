#!/usr/bin/env python3
"""Analyze why Debbie isn't making tool calls"""

import re

logs = [
    ("/home/deano/projects/AIWhisperer/logs/agents/agent_d_d_20250605_192921.log", "Gemini - Error"),
    ("/home/deano/projects/AIWhisperer/logs/agents/agent_d_d_20250605_195051.log", "Gemini - Success"), 
    ("/home/deano/projects/AIWhisperer/logs/agents/agent_d_debbie__debugger_20250605_200012.log", "Claude - No Tool Call")
]

for log_path, label in logs:
    print(f"\n=== {label} ===")
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Find what message Debbie received
    mail_received = re.findall(r'Debbie.*?activated.*?|check.*?mail.*?|Please use the list_directory', content, re.IGNORECASE)
    if mail_received:
        print(f"Context: {mail_received[0][:100]}...")
    
    # Check if she actually found mail
    mail_check = re.findall(r'Found \d+ unread messages|Message \d+:.*?body=|Inbox contains', content)
    if mail_check:
        print(f"Mail check result: {mail_check[0][:100]}...")
        
    # Check tool calls
    tool_calls = re.findall(r'=== TOOL CALL ===\n(.*?)\n', content)
    if tool_calls:
        print(f"Tool calls made: {tool_calls}")
    else:
        print("No tool calls made")
        
    # Check analysis field for intent
    analysis_match = re.search(r'"analysis":\s*"([^"]*)"', content)
    if analysis_match:
        print(f"Analysis: {analysis_match.group(1)[:150]}...")