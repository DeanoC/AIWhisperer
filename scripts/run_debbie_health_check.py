#!/usr/bin/env python3
"""
Example script showing how to use AIWhisperer's batch mode to run Debbie's system health check.

This demonstrates:
1. Starting a batch server
2. Running a batch script that switches to Debbie
3. Executing the system health check
4. Processing the results

Usage:
    python scripts/run_debbie_health_check.py
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_whisperer.extensions.conversation_replay.client import BatchClient
from ai_whisperer.extensions.conversation_replay.server_manager import ServerManager


async def run_health_check():
    """Run Debbie's system health check using batch mode."""
    
    # Initialize server manager
    server_manager = ServerManager()
    
    # Find an available port
    port = server_manager.find_available_port()
    print(f"Starting batch server on port {port}...")
    
    # Start the server
    server_url = await server_manager.start_server(port)
    
    try:
        # Create batch client
        client = BatchClient(server_url)
        
        # Wait for server to be ready
        print("Waiting for server to be ready...")
        await client.wait_for_ready()
        
        # Run the health check script
        script_path = project_root / "scripts" / "debbie_health_check.json"
        
        print(f"\nRunning health check script: {script_path}")
        print("=" * 60)
        
        # Execute the script
        result = await client.run_script(str(script_path))
        
        # Process results
        if result.get('success'):
            print("\n✅ Health check completed successfully!")
            
            # Extract the health check report from the results
            steps = result.get('results', [])
            for step in steps:
                if step.get('step_id') == 'health_check':
                    output = step.get('output', '')
                    print("\nHealth Check Report:")
                    print("-" * 60)
                    print(output)
                    break
        else:
            print("\n❌ Health check failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Show any partial results
            if result.get('results'):
                print("\nPartial results:")
                for i, step_result in enumerate(result['results']):
                    print(f"\nStep {i+1}: {step_result.get('status', 'unknown')}")
                    if step_result.get('error'):
                        print(f"  Error: {step_result['error']}")
                    if step_result.get('output'):
                        print(f"  Output: {step_result['output'][:200]}...")
        
        # Save full results
        results_file = project_root / "scripts" / "health_check_results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\nFull results saved to: {results_file}")
        
    finally:
        # Always stop the server
        print("\nStopping server...")
        await server_manager.stop_server()
        print("Server stopped.")


def main():
    """Main entry point."""
    print("AIWhisperer Batch Mode Example: System Health Check with Debbie")
    print("=" * 60)
    
    try:
        # Run the async function
        asyncio.run(run_health_check())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()