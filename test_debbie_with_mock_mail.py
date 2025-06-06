#!/usr/bin/env python3
"""Test Debbie with mocked check_mail to see if she executes tool requests"""

import sys
import os

# Temporarily replace check_mail in the registry
original_file = "/home/deano/projects/AIWhisperer/ai_whisperer/tools/check_mail_tool.py"
backup_file = "/home/deano/projects/AIWhisperer/ai_whisperer/tools/check_mail_tool.py.backup"
mock_file = "/home/deano/projects/AIWhisperer/mock_check_mail_tool.py"

print("=== Setting up mock check_mail tool ===")

# Backup original
if os.path.exists(original_file):
    with open(original_file, 'r') as f:
        original_content = f.read()
    with open(backup_file, 'w') as f:
        f.write(original_content)
    print(f"✓ Backed up original check_mail_tool.py")

# Copy mock
with open(mock_file, 'r') as f:
    mock_content = f.read()
with open(original_file, 'w') as f:
    f.write(mock_content)
print(f"✓ Installed mock check_mail_tool.py")

try:
    # Run the test
    print("\n=== Running test with Debbie ===")
    os.system("AIWHISPERER_DEFAULT_AGENT=d python -m ai_whisperer.interfaces.cli.main --config config/main.yaml replay test_debbie_check_separate.txt")
    
finally:
    # Restore original
    print("\n=== Restoring original check_mail tool ===")
    if os.path.exists(backup_file):
        with open(backup_file, 'r') as f:
            original_content = f.read()
        with open(original_file, 'w') as f:
            f.write(original_content)
        os.remove(backup_file)
        print(f"✓ Restored original check_mail_tool.py")