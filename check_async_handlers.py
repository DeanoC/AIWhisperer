#!/usr/bin/env python3
"""Check if async handlers are loaded in the server."""

import sys
sys.path.insert(0, '/home/deano/projects/AIWhisperer')

from interactive_server.main import HANDLERS, async_agent_endpoints

print("=== Checking Async Handlers ===\n")

print(f"async_agent_endpoints object: {async_agent_endpoints}")
print(f"Type: {type(async_agent_endpoints) if async_agent_endpoints else 'None'}\n")

print("Available handlers:")
for key in sorted(HANDLERS.keys()):
    if key.startswith("async."):
        print(f"  ✅ {key}")
        
async_methods = [k for k in HANDLERS.keys() if k.startswith("async.")]
print(f"\nTotal async methods: {len(async_methods)}")

if len(async_methods) == 0:
    print("\n❌ No async handlers found!")
    print("\nAll available handlers:")
    for key in sorted(HANDLERS.keys()):
        print(f"  - {key}")