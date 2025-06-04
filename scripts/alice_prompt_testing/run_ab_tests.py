#!/usr/bin/env python3
"""
A/B Testing Runner for Alice Prompt Improvements

This script runs conversation replay tests with both current and revised prompts,
collecting metrics for comparison.
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import shutil
import tempfile

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.extensions.conversation_replay import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor
from ai_whisperer.core.config import load_config


class AliceABTestRunner:
    """Runs A/B tests for Alice prompt variations."""
    
    def __init__(self, config_path: str = "config/main.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.test_dir = Path(__file__).parent
        self.prompts_dir = PROJECT_ROOT / "prompts" / "agents"
        self.results_dir = self.test_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test scenarios
        self.test_scenarios = [
            "test_workspace_status.txt",
            "test_agent_listing.txt", 
            "test_mailbox_question.txt",
            "test_high_level_code.txt",
            "test_low_level_code.txt"
        ]
        
    async def run_single_test(self, test_file: str, prompt_version: str, session_id: str) -> Dict:
        """Run a single test scenario with specified prompt version."""
        print(f"Running test: {test_file} with {prompt_version} prompt...")
        
        # Start server
        manager = ServerManager()
        manager.start_server()  # This will use config from environment
        
        # Wait for server to be ready
        await asyncio.sleep(3)
        
        server_url = f"ws://127.0.0.1:{manager.port}/ws"
        
        collected_responses = []
        
        try:
            # Create WebSocket client
            ws_client = WebSocketClient(server_url)
            
            # Set up notification handler to capture all channel messages
            async def notification_handler(notification):
                method = notification.get("method", "")
                params = notification.get("params", {})
                
                if method == "ChannelMessageNotification":
                    content = params.get("content", "")
                    channel = params.get("channel", "")
                    collected_responses.append({
                        "channel": channel,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    })
            
            ws_client.set_notification_handler(notification_handler)
            
            # Connect to server
            await ws_client.connect()
            
            # Start session
            start_response = await ws_client.send_request(
                method="startSession",
                params={"userId": f"ab_test_{prompt_version}", "sessionParams": {"language": "en"}},
                request_id=1
            )
            
            # Extract session ID
            ws_session_id = start_response.get("sessionId")
            if not ws_session_id:
                raise Exception("Failed to get session ID")
            
            # Wait for introduction
            await asyncio.sleep(2)
            
            # Load conversation
            conversation_path = self.test_dir / test_file
            processor = ConversationProcessor(str(conversation_path))
            processor.load_conversation()
            
            results = []
            request_id = 2
            
            # Send messages one by one
            while True:
                msg = processor.get_next_message()
                if msg is None:
                    break
                
                # Clear collected responses for this message
                collected_responses.clear()
                
                # Send message via JSON-RPC
                response = await ws_client.send_request(
                    method="sendUserMessage",
                    params={"sessionId": ws_session_id, "message": msg},
                    request_id=request_id
                )
                request_id += 1
                
                # Wait for Alice to respond
                await asyncio.sleep(3)
                
                # Combine all collected responses
                full_response = "\n".join([
                    f"[{r['channel']}]\n{r['content']}" 
                    for r in collected_responses
                ])
                
                results.append({
                    "message": msg,
                    "response": full_response,
                    "channel_responses": list(collected_responses)
                })
                
                # Brief pause between messages
                await asyncio.sleep(0.5)
            
            # Close connection
            await ws_client.close()
            
            # Analyze responses with prompt metrics tool
            metrics = []
            for i, result in enumerate(results):
                # Call prompt metrics tool to analyze response
                metric_result = await self._analyze_response(
                    agent_id="A",
                    response=result.get("response", ""),
                    channel_responses=result.get("channel_responses", []),
                    session_id=session_id,
                    prompt_version=prompt_version
                )
                metrics.append(metric_result)
            
            return {
                "test_file": test_file,
                "prompt_version": prompt_version,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "results": results,
                "metrics": metrics,
                "success": True
            }
            
        except Exception as e:
            return {
                "test_file": test_file,
                "prompt_version": prompt_version,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }
        finally:
            manager.stop_server()
    
    async def _analyze_response(self, agent_id: str, response: str, channel_responses: List[Dict], 
                               session_id: str, prompt_version: str) -> Dict:
        """Analyze response using prompt metrics tool."""
        # Enhanced analysis based on channel structure
        analysis_channel = None
        commentary_channel = None
        final_channel = None
        
        for ch_resp in channel_responses:
            if ch_resp["channel"] == "ANALYSIS":
                analysis_channel = ch_resp["content"]
            elif ch_resp["channel"] == "COMMENTARY":
                commentary_channel = ch_resp["content"]
            elif ch_resp["channel"] == "FINAL":
                final_channel = ch_resp["content"]
        
        # Check for preambles
        preambles = ["I'll help you", "Let me", "I can help", "I'll be happy to", "I'd be glad to"]
        has_preamble = any(preamble.lower() in response.lower() for preamble in preambles)
        
        # Check for permission-seeking
        permission_phrases = ["Would you like me to", "Should I", "May I", "Can I", "Do you want me to"]
        seeks_permission = any(phrase.lower() in response.lower() for phrase in permission_phrases)
        
        return {
            "agent_id": agent_id,
            "session_id": session_id,
            "prompt_version": prompt_version,
            "response_length": len(response),
            "has_channels": bool(analysis_channel or commentary_channel or final_channel),
            "has_analysis": bool(analysis_channel),
            "has_commentary": bool(commentary_channel), 
            "has_final": bool(final_channel),
            "final_length": len(final_channel) if final_channel else 0,
            "has_preamble": has_preamble,
            "seeks_permission": seeks_permission,
            "word_count": len(response.split()),
            "channel_count": len(channel_responses)
        }
    
    def swap_prompts(self, use_revised: bool):
        """Swap between current and revised Alice prompts."""
        current_prompt = self.prompts_dir / "alice_assistant.prompt.md"
        backup_prompt = self.prompts_dir / "alice_assistant.prompt.md.backup"
        revised_prompt = self.prompts_dir / "alice_assistant_revised.prompt.md"
        
        if use_revised:
            # Backup current if not already done
            if not backup_prompt.exists():
                shutil.copy(current_prompt, backup_prompt)
            
            # Use revised prompt if it exists
            if revised_prompt.exists():
                shutil.copy(revised_prompt, current_prompt)
                print(f"Switched to revised prompt")
            else:
                print(f"Warning: Revised prompt not found at {revised_prompt}")
        else:
            # Restore original
            if backup_prompt.exists():
                shutil.copy(backup_prompt, current_prompt)
                print(f"Restored original prompt")
    
    async def run_all_tests(self, iterations: int = 3):
        """Run all test scenarios with both prompt versions."""
        all_results = []
        
        for iteration in range(iterations):
            print(f"\n=== Iteration {iteration + 1}/{iterations} ===")
            
            # Run with current prompt
            print("\nTesting with CURRENT prompt...")
            self.swap_prompts(use_revised=False)
            
            for test_file in self.test_scenarios:
                session_id = f"current_{iteration}_{test_file.replace('.txt', '')}"
                result = await self.run_single_test(test_file, "current", session_id)
                all_results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(2)
            
            # Run with revised prompt
            print("\nTesting with REVISED prompt...")
            self.swap_prompts(use_revised=True)
            
            for test_file in self.test_scenarios:
                session_id = f"revised_{iteration}_{test_file.replace('.txt', '')}"
                result = await self.run_single_test(test_file, "revised", session_id)
                all_results.append(result)
                
                # Brief pause between tests
                await asyncio.sleep(2)
        
        # Restore original prompt
        self.swap_prompts(use_revised=False)
        
        # Save all results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"ab_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        
        # Generate summary
        self.generate_summary(all_results, timestamp)
        
        return all_results
    
    def generate_summary(self, results: List[Dict], timestamp: str):
        """Generate a summary report of the A/B test results."""
        summary = {
            "timestamp": timestamp,
            "total_tests": len(results),
            "by_version": {
                "current": {"total": 0, "success": 0, "failures": [], "metrics": {}},
                "revised": {"total": 0, "success": 0, "failures": [], "metrics": {}}
            },
            "by_scenario": {}
        }
        
        # Initialize metric accumulators
        metric_fields = ["has_channels", "has_preamble", "seeks_permission", "response_length", "final_length"]
        for version in ["current", "revised"]:
            for field in metric_fields:
                summary["by_version"][version]["metrics"][field] = []
        
        # Process results
        for result in results:
            version = result["prompt_version"]
            scenario = result["test_file"]
            
            summary["by_version"][version]["total"] += 1
            if result["success"]:
                summary["by_version"][version]["success"] += 1
                
                # Aggregate metrics
                if "metrics" in result:
                    for metric in result["metrics"]:
                        for field in metric_fields:
                            if field in metric:
                                summary["by_version"][version]["metrics"][field].append(metric[field])
            else:
                summary["by_version"][version]["failures"].append({
                    "test": scenario,
                    "error": result.get("error", "Unknown error")
                })
            
            # Track by scenario
            if scenario not in summary["by_scenario"]:
                summary["by_scenario"][scenario] = {
                    "current": {"runs": 0, "success": 0},
                    "revised": {"runs": 0, "success": 0}
                }
            
            summary["by_scenario"][scenario][version]["runs"] += 1
            if result["success"]:
                summary["by_scenario"][scenario][version]["success"] += 1
        
        # Calculate success rates and metric averages
        for version in ["current", "revised"]:
            total = summary["by_version"][version]["total"]
            success = summary["by_version"][version]["success"]
            summary["by_version"][version]["success_rate"] = (success / total * 100) if total > 0 else 0
            
            # Calculate metric averages
            metrics = summary["by_version"][version]["metrics"]
            summary["by_version"][version]["avg_metrics"] = {}
            for field, values in metrics.items():
                if values:
                    if field in ["has_channels", "has_preamble", "seeks_permission"]:
                        # Boolean fields - calculate percentage
                        summary["by_version"][version]["avg_metrics"][field] = sum(values) / len(values) * 100
                    else:
                        # Numeric fields - calculate average
                        summary["by_version"][version]["avg_metrics"][field] = sum(values) / len(values)
        
        # Save summary
        summary_file = self.results_dir / f"ab_test_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n=== A/B Test Summary ===")
        print(f"Total tests run: {summary['total_tests']}")
        print("\nBy Version:")
        for version, data in summary["by_version"].items():
            print(f"  {version.upper()}:")
            print(f"    - Success rate: {data['success_rate']:.1f}%")
            print(f"    - Successful: {data['success']}/{data['total']}")
            if data['failures']:
                print(f"    - Failures: {len(data['failures'])}")
            
            if "avg_metrics" in data and data["avg_metrics"]:
                print("    - Average Metrics:")
                avg = data["avg_metrics"]
                if "has_channels" in avg:
                    print(f"      • Uses channels: {avg['has_channels']:.1f}%")
                if "has_preamble" in avg:
                    print(f"      • Has preambles: {avg['has_preamble']:.1f}%")
                if "seeks_permission" in avg:
                    print(f"      • Seeks permission: {avg['seeks_permission']:.1f}%")
                if "response_length" in avg:
                    print(f"      • Response length: {avg['response_length']:.0f} chars")
                if "final_length" in avg:
                    print(f"      • Final section length: {avg['final_length']:.0f} chars")
        
        print("\nBy Scenario:")
        for scenario, data in summary["by_scenario"].items():
            print(f"  {scenario}:")
            for version in ["current", "revised"]:
                success_rate = (data[version]["success"] / data[version]["runs"] * 100) if data[version]["runs"] > 0 else 0
                print(f"    - {version}: {success_rate:.1f}% success ({data[version]['success']}/{data[version]['runs']})")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run A/B tests for Alice prompt improvements")
    parser.add_argument("--config", default="config/main.yaml", help="Config file path")
    parser.add_argument("--iterations", type=int, default=3, help="Number of test iterations")
    parser.add_argument("--single", help="Run a single test file")
    parser.add_argument("--version", choices=["current", "revised"], help="Test specific version only")
    
    args = parser.parse_args()
    
    runner = AliceABTestRunner(args.config)
    
    if args.single:
        # Run single test
        session_id = f"single_{args.version or 'current'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if args.version == "revised":
            runner.swap_prompts(use_revised=True)
        
        result = await runner.run_single_test(args.single, args.version or "current", session_id)
        print(json.dumps(result, indent=2))
        
        # Restore prompt
        runner.swap_prompts(use_revised=False)
    else:
        # Run full A/B test
        await runner.run_all_tests(iterations=args.iterations)


if __name__ == "__main__":
    asyncio.run(main())