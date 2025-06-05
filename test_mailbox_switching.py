#!/usr/bin/env python3
"""
Test script for synchronous mailbox switching between agents.
Tests the send_mail_with_switch tool and agent switching functionality.
"""

import asyncio
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_mailbox_switching():
    """Test synchronous mail switching between agents."""
    
    print("\n" + "="*60)
    print("Testing Synchronous Mailbox Switching")
    print("="*60 + "\n")
    
    # Test conversation script
    conversation = [
        "/switch-agent a",
        "Who are you?",
        "Use send_mail_with_switch to send to Debbie with subject 'System Health Check' and body 'Please check the system health.'",
        "/inspect-agent d",  # Check Debbie's state after switch
        "/switch-agent a",   # Go back to Alice to see if she got a response
        "What was Debbie's response?",
        "/exit"
    ]
    
    # Write conversation to file
    test_file = f"test_mailbox_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(test_file, 'w') as f:
        for line in conversation:
            f.write(line + '\n')
    
    print(f"Created test conversation file: {test_file}")
    print("\nTest conversation:")
    for line in conversation:
        print(f"  {line}")
    
    print("\nRunning conversation replay...")
    print("-" * 40)
    
    # Run the conversation using replay mode
    import subprocess
    cmd = [
        "python", "-m", "ai_whisperer.interfaces.cli.main",
        "--config", "config/main.yaml",
        "replay", test_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        print("\nOutput:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        
        # Check the agent logs
        print("\n" + "="*60)
        print("Checking Agent Logs")
        print("="*60 + "\n")
        
        import os
        from pathlib import Path
        
        logs_dir = Path("logs/agents")
        if logs_dir.exists():
            # Find the most recent log files
            log_files = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
            
            # Show last few entries from Alice and Debbie logs
            for log_file in log_files[:4]:  # Check last 4 log files
                if "agent_a" in str(log_file) or "agent_d" in str(log_file):
                    print(f"\n--- {log_file.name} (last 20 lines) ---")
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        for line in lines[-20:]:
                            print(line.rstrip())
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("\nERROR: Test timed out after 60 seconds")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

async def check_latest_logs():
    """Check the latest agent logs for tool calls and system prompts."""
    print("\n" + "="*60)
    print("Analyzing Latest Agent Logs")
    print("="*60 + "\n")
    
    from pathlib import Path
    import os
    
    logs_dir = Path("logs/agents")
    if not logs_dir.exists():
        print("No agent logs found")
        return
    
    # Find the most recent session logs
    log_files = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
    
    # Group by session timestamp
    sessions = {}
    for log_file in log_files:
        # Extract session timestamp from filename
        parts = log_file.stem.split('_')
        if len(parts) >= 3:
            session_time = '_'.join(parts[-2:])  # Get last two parts as timestamp
            if session_time not in sessions:
                sessions[session_time] = []
            sessions[session_time].append(log_file)
    
    # Analyze the most recent session
    if sessions:
        latest_session = list(sessions.keys())[0]
        print(f"Latest session: {latest_session}")
        print(f"Log files: {len(sessions[latest_session])}")
        
        for log_file in sessions[latest_session]:
            agent_name = log_file.stem.split('_')[1]  # Get agent ID
            print(f"\n--- Agent {agent_name.upper()} ---")
            
            with open(log_file, 'r') as f:
                content = f.read()
                
                # Check for system prompt
                if "=== SYSTEM PROMPT ===" in content:
                    print("✓ System prompt logged")
                    # Check if mailbox debug mode is active
                    if "Force Mailbox Tool Usage" in content:
                        print("✓ Mailbox debug mode ACTIVE")
                    else:
                        print("✗ Mailbox debug mode NOT active")
                
                # Count tool calls
                tool_calls = content.count("=== TOOL CALL ===")
                print(f"Tool calls made: {tool_calls}")
                
                # Check for specific tools
                if "check_mail(" in content:
                    print("✓ check_mail tool called")
                if "send_mail_with_switch(" in content:
                    print("✓ send_mail_with_switch tool called")
                
                # Check for agent switches
                switches_to = content.count("*** SWITCHING TO AGENT")
                switches_from = content.count("*** SWITCHED FROM AGENT")
                print(f"Agent switches: {switches_to} outgoing, {switches_from} incoming")

if __name__ == "__main__":
    success = asyncio.run(test_mailbox_switching())
    asyncio.run(check_latest_logs())
    
    print("\n" + "="*60)
    print(f"Test {'PASSED' if success else 'FAILED'}")
    print("="*60)