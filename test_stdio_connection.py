#!/usr/bin/env python3
"""Test stdio connection for MCP"""
import sys
import json
import logging

# Log to stderr to avoid interfering with stdio
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(message)s',
    stream=sys.stderr
)

def main():
    logging.info("Test stdio server starting")
    
    # Simple echo server
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            msg = json.loads(line.strip())
            logging.info(f"Received: {msg}")
            
            # Echo back with result
            response = {
                "jsonrpc": "2.0",
                "id": msg.get("id"),
                "result": {"echo": msg}
            }
            
            sys.stdout.write(json.dumps(response) + '\n')
            sys.stdout.flush()
            
        except Exception as e:
            logging.error(f"Error: {e}")
            
if __name__ == "__main__":
    main()