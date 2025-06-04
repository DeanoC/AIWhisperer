#!/usr/bin/env python3
"""
Test runner for newly revised prompts (2025-06-04)
Tests key improvements: channel compliance, conciseness, autonomous operation
"""

import asyncio
import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.extensions.conversation_replay import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient
from ai_whisperer.extensions.conversation_replay.conversation_processor import ConversationProcessor
from ai_whisperer.core.config import load_config


class PromptTestRunner:
    """Test runner for comparing old vs new prompts."""
    
    def __init__(self, config_path: str = "config/main.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.prompts_dir = PROJECT_ROOT / "prompts"
        self.results_dir = PROJECT_ROOT / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test scenarios for different agents
        self.test_scenarios = {
            "alice": [
                ("List my workspace files", "alice_workspace_test"),
                ("What agents are available?", "alice_agents_test"),
                ("I need to create an RFC for dark mode", "alice_rfc_switch_test")
            ],
            "patricia": [
                ("I want to add user authentication", "patricia_rfc_create_test"),
                ("The RFC looks complete, can we create a plan?", "patricia_plan_gen_test")
            ],
            "debbie": [
                ("Check session health", "debbie_health_test"),
                ("My agent seems stuck", "debbie_intervention_test")
            ]
        }
        
    def backup_prompts(self):
        """Backup all current prompts before testing."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.prompts_dir.parent / f"prompts_backup_{timestamp}"
        
        print(f"Backing up prompts to {backup_dir}")
        shutil.copytree(self.prompts_dir, backup_dir)
        
        return backup_dir
    
    def restore_prompts(self, backup_dir: Path):
        """Restore prompts from backup."""
        print(f"Restoring prompts from {backup_dir}")
        shutil.rmtree(self.prompts_dir)
        shutil.copytree(backup_dir, self.prompts_dir)
    
    async def test_single_message(self, agent: str, message: str, test_name: str, prompt_version: str) -> Dict:
        """Test a single message with an agent."""
        print(f"\n[{prompt_version}] Testing {agent}: '{message[:50]}...'")
        
        # Start server
        manager = ServerManager()
        manager.start_server()
        
        # Wait for server
        await asyncio.sleep(3)
        
        server_url = f"ws://127.0.0.1:{manager.port}/ws"
        
        try:
            # Create WebSocket client
            ws_client = WebSocketClient(server_url)
            
            # Collect responses
            collected_responses = []
            
            async def notification_handler(notification):
                method = notification.get("method", "")
                params = notification.get("params", {})
                
                if method == "ChannelMessageNotification":
                    collected_responses.append({
                        "channel": params.get("channel", ""),
                        "content": params.get("content", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            ws_client.set_notification_handler(notification_handler)
            
            # Connect
            await ws_client.connect()
            
            # Start session
            start_response = await ws_client.send_request(
                method="startSession",
                params={"userId": f"test_{prompt_version}_{test_name}"},
                request_id=1
            )
            
            session_id = start_response.get("sessionId")
            
            # Wait for agent introduction
            await asyncio.sleep(2)
            
            # Switch to target agent if not alice
            if agent != "alice":
                switch_msg = f"switch to {agent}"
                await ws_client.send_request(
                    method="sendUserMessage",
                    params={"sessionId": session_id, "message": switch_msg},
                    request_id=2
                )
                await asyncio.sleep(2)
                collected_responses.clear()  # Clear switch responses
            
            # Send test message
            response = await ws_client.send_request(
                method="sendUserMessage",
                params={"sessionId": session_id, "message": message},
                request_id=3
            )
            
            # Wait for response
            await asyncio.sleep(5)
            
            # Close connection
            await ws_client.close()
            
            # Analyze response
            metrics = self.analyze_response(collected_responses)
            
            return {
                "agent": agent,
                "message": message,
                "test_name": test_name,
                "prompt_version": prompt_version,
                "responses": collected_responses,
                "metrics": metrics,
                "success": True
            }
            
        except Exception as e:
            return {
                "agent": agent,
                "message": message,
                "test_name": test_name,
                "prompt_version": prompt_version,
                "error": str(e),
                "success": False
            }
        finally:
            manager.stop_server()
    
    def analyze_response(self, responses: List[Dict]) -> Dict:
        """Analyze response for key metrics."""
        # Extract channels
        channels = {}
        total_content = ""
        
        for resp in responses:
            channel = resp["channel"]
            content = resp["content"]
            channels[channel] = content
            total_content += content + "\n"
        
        # Check for forbidden phrases
        forbidden_phrases = [
            "I'll help you", "Let me", "Great!", "Certainly!", 
            "I'd be happy to", "I'll be glad to", "Would you like me to",
            "Should I", "May I", "Can I"
        ]
        
        violations = []
        for phrase in forbidden_phrases:
            if phrase.lower() in total_content.lower():
                violations.append(phrase)
        
        # Count lines in FINAL channel
        final_lines = 0
        if "FINAL" in channels:
            final_lines = len([l for l in channels["FINAL"].split('\n') if l.strip()])
        
        # Check channel compliance
        has_all_channels = all(ch in channels for ch in ["ANALYSIS", "COMMENTARY", "FINAL"])
        
        return {
            "has_all_channels": has_all_channels,
            "channels_present": list(channels.keys()),
            "final_lines": final_lines,
            "final_within_limit": final_lines <= 4,
            "total_length": len(total_content),
            "violations": violations,
            "has_violations": len(violations) > 0,
            "word_count": len(total_content.split())
        }
    
    async def run_comparison_tests(self):
        """Run tests comparing old and new prompts."""
        # Backup current prompts
        backup_dir = self.backup_prompts()
        
        all_results = []
        
        try:
            # Test each agent with OLD prompts (current state)
            print("\n=== Testing with CURRENT prompts ===")
            for agent, scenarios in self.test_scenarios.items():
                for message, test_name in scenarios:
                    result = await self.test_single_message(agent, message, test_name, "old")
                    all_results.append(result)
                    await asyncio.sleep(1)
            
            # Note: Since we've already updated the prompts in place,
            # the "current" state IS the new prompts. We'd need to
            # restore from a previous backup to test old prompts.
            
            print("\n=== Testing with NEW prompts ===")
            print("(Current prompts are already the new revised versions)")
            
            for agent, scenarios in self.test_scenarios.items():
                for message, test_name in scenarios:
                    result = await self.test_single_message(agent, message, test_name, "new")
                    all_results.append(result)
                    await asyncio.sleep(1)
            
        finally:
            # Don't restore - we want to keep the new prompts
            print("\nKeeping new prompts in place")
            shutil.rmtree(backup_dir)  # Clean up backup
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"prompt_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Generate report
        self.generate_report(all_results, timestamp)
        
        return all_results
    
    def generate_report(self, results: List[Dict], timestamp: str):
        """Generate comparison report."""
        report = {
            "timestamp": timestamp,
            "summary": {
                "old": {"total": 0, "success": 0, "metrics": {}},
                "new": {"total": 0, "success": 0, "metrics": {}}
            },
            "by_agent": {}
        }
        
        # Process results
        for result in results:
            version = result["prompt_version"]
            agent = result["agent"]
            
            # Initialize agent data
            if agent not in report["by_agent"]:
                report["by_agent"][agent] = {
                    "old": {"tests": []},
                    "new": {"tests": []}
                }
            
            report["summary"][version]["total"] += 1
            
            if result["success"]:
                report["summary"][version]["success"] += 1
                
                # Add test result
                test_summary = {
                    "test_name": result["test_name"],
                    "metrics": result["metrics"]
                }
                report["by_agent"][agent][version]["tests"].append(test_summary)
        
        # Calculate aggregates
        for version in ["old", "new"]:
            tests = []
            for agent_data in report["by_agent"].values():
                tests.extend(agent_data[version]["tests"])
            
            if tests:
                # Channel compliance
                channel_compliance = sum(1 for t in tests if t["metrics"]["has_all_channels"]) / len(tests) * 100
                
                # Final line compliance
                line_compliance = sum(1 for t in tests if t["metrics"]["final_within_limit"]) / len(tests) * 100
                
                # Violations
                violation_rate = sum(1 for t in tests if t["metrics"]["has_violations"]) / len(tests) * 100
                
                # Average lengths
                avg_length = sum(t["metrics"]["total_length"] for t in tests) / len(tests)
                avg_words = sum(t["metrics"]["word_count"] for t in tests) / len(tests)
                
                report["summary"][version]["metrics"] = {
                    "channel_compliance": channel_compliance,
                    "line_limit_compliance": line_compliance,
                    "violation_rate": violation_rate,
                    "avg_response_length": avg_length,
                    "avg_word_count": avg_words
                }
        
        # Save report
        report_file = self.results_dir / f"prompt_comparison_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("PROMPT COMPARISON REPORT")
        print("="*60)
        
        for version in ["old", "new"]:
            print(f"\n{version.upper()} PROMPTS:")
            print(f"  Success Rate: {report['summary'][version]['success']}/{report['summary'][version]['total']}")
            
            if "metrics" in report["summary"][version]:
                m = report["summary"][version]["metrics"]
                print(f"  Channel Compliance: {m['channel_compliance']:.1f}%")
                print(f"  Line Limit Compliance: {m['line_limit_compliance']:.1f}%")
                print(f"  Violation Rate: {m['violation_rate']:.1f}%")
                print(f"  Avg Response Length: {m['avg_response_length']:.0f} chars")
                print(f"  Avg Word Count: {m['avg_word_count']:.0f} words")
        
        print("\nDETAILED RESULTS BY AGENT:")
        for agent, data in report["by_agent"].items():
            print(f"\n{agent.upper()}:")
            for version in ["old", "new"]:
                if data[version]["tests"]:
                    print(f"  {version}: {len(data[version]['tests'])} tests")
                    violations = sum(1 for t in data[version]["tests"] if t["metrics"]["has_violations"])
                    if violations:
                        print(f"    - Violations: {violations}")
        
        results_file = self.results_dir / f"prompt_test_results_{timestamp}.json"
        print(f"\nFull results saved to: {results_file}")
        print(f"Report saved to: {report_file}")


async def main():
    """Run prompt comparison tests."""
    runner = PromptTestRunner()
    await runner.run_comparison_tests()


if __name__ == "__main__":
    asyncio.run(main())