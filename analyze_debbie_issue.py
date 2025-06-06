#!/usr/bin/env python3
"""Analyze Debbie's response truncation issue"""

import re
import json

# Check the failed response
failed_log = "/home/deano/projects/AIWhisperer/logs/agents/agent_d_d_20250605_192921.log"
success_log = "/home/deano/projects/AIWhisperer/logs/agents/agent_d_d_20250605_195051.log"

def analyze_log(log_path, label):
    print(f"\n=== Analyzing {label}: {log_path} ===")
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Find AI response section
    ai_response_match = re.search(r'<<< AI RESPONSE <<<\n(.*?)(?=\n\d{4}-\d{2}-\d{2})', content, re.DOTALL)
    if ai_response_match:
        response = ai_response_match.group(1)
        print(f"Response length: {len(response)} chars")
        
        # Check if JSON is complete
        try:
            # Extract JSON from response
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
                print("✓ Valid JSON response")
                print(f"  - analysis: {len(parsed.get('analysis', ''))} chars")
                print(f"  - commentary: {len(parsed.get('commentary', ''))} chars") 
                print(f"  - final: {len(parsed.get('final', ''))} chars")
            else:
                print("✗ No JSON found in response")
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}")
            print(f"Response snippet: {response[:200]}...")
            
        # Check finish reason
        finish_match = re.search(r'finish_reason: (\w+)', content[content.find('<<< AI RESPONSE <<<'):])
        if finish_match:
            print(f"Finish reason: {finish_match.group(1)}")
    else:
        print("No AI response found")
    
    # Check for any errors or timeouts
    error_patterns = [
        r'OpenRouter API error',
        r'Streaming error',
        r'timeout',
        r'JSONDecodeError',
        r'truncated'
    ]
    
    for pattern in error_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            print(f"Found {pattern}: {len(matches)} occurrences")

# Analyze both logs
analyze_log(failed_log, "FAILED RUN")
analyze_log(success_log, "SUCCESS RUN")

# Check for any streaming issues in the server logs
print("\n=== Checking for streaming issues ===")
server_logs = [
    "/home/deano/projects/AIWhisperer/logs/aiwhisperer_server_batch_20250605_192921_port26231.log",
    "/home/deano/projects/AIWhisperer/logs/aiwhisperer_server_batch_20250605_195050_port28130.log"
]

for log_path in server_logs:
    try:
        with open(log_path, 'r') as f:
            content = f.read()
            
        # Look for streaming updates
        streaming_updates = re.findall(r'StreamingUpdate.*?"content":\s*"([^"]*)"', content)
        if streaming_updates:
            print(f"\n{log_path}:")
            print(f"  Found {len(streaming_updates)} streaming updates")
            for i, update in enumerate(streaming_updates[:3]):
                print(f"  Update {i+1}: {update[:100]}...")
    except FileNotFoundError:
        print(f"  {log_path} not found")