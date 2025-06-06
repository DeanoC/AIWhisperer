#!/usr/bin/env python3
"""Test script to debug Debbie's mail processing with OpenRouter logging enabled."""

import os
import subprocess
import sys
import time

# Enable OpenRouter debug logging
os.environ['AIWHISPERER_DEBUG_OPENROUTER'] = '1'

# Create test conversation file
test_file = 'test_mail_with_logging.txt'
with open(test_file, 'w') as f:
    f.write("Use send_mail_with_switch to send a message to agent 'd' with subject 'Debug Test' and body 'What is 5 * 5?'")

print("🔍 Running test with OpenRouter debug logging enabled...")
print("📝 This will show all API calls to OpenRouter\n")

# Run the conversation replay
cmd = [
    sys.executable, '-m', 'ai_whisperer.interfaces.cli.main',
    '--config', 'config/main.yaml',
    'replay', test_file
]

# Run with environment variable set
env = os.environ.copy()
env['AIWHISPERER_DEBUG_OPENROUTER'] = '1'

result = subprocess.run(cmd, env=env, capture_output=False, text=True)

print(f"\n✅ Test completed with exit code: {result.returncode}")
print("\n📋 Check the debug log file for OpenRouter API details:")
print(f"   grep -n 'Streaming payload\\|RETURNING RESULT' logs/aiwhisperer_debug_batch_*.log | tail -50")