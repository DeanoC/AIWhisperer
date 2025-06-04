#!/usr/bin/env python3
"""
Evaluation Script using Debbie to analyze Alice's responses

This script uses Debbie (the debugger agent) to evaluate the quality
of Alice's responses from the A/B tests.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai_whisperer.extensions.conversation_replay import ServerManager
from ai_whisperer.extensions.conversation_replay.websocket_client import WebSocketClient
from ai_whisperer.core.config import load_config


class DebbieEvaluator:
    """Uses Debbie to evaluate Alice's responses."""
    
    def __init__(self, config_path: str = "config/main.yaml"):
        self.config_path = config_path
        self.config = load_config(config_path)
        self.results_dir = Path(__file__).parent / "results"
        self.evaluations_dir = self.results_dir / "evaluations"
        self.evaluations_dir.mkdir(exist_ok=True)
        
    def create_evaluation_prompt(self, test_scenario: str, response: str, version: str) -> str:
        """Create a prompt for Debbie to evaluate Alice's response."""
        return f"""# Evaluation Request for Alice's Response

**Test Scenario**: {test_scenario}
**Prompt Version**: {version}

**Alice's Response**:
{response}

Please evaluate this response based on the following criteria:

1. **Channel Compliance** (0-10):
   - Does it use [ANALYSIS], [COMMENTARY], and [FINAL] channels correctly?
   - Is the channel structure clear and properly formatted?

2. **Conciseness** (0-10):
   - Is the response appropriately concise?
   - Does it avoid unnecessary preambles like "I'll help you..." or "Let me..."?
   - Is the FINAL section focused and to the point?

3. **Autonomy** (0-10):
   - Does Alice take initiative to use tools without asking permission?
   - Does she complete the task fully without stopping prematurely?
   - Does she avoid phrases like "Would you like me to..." or "Should I..."?

4. **Task Completion** (0-10):
   - Did Alice fully address the user's request?
   - Were appropriate tools used?
   - Is the answer complete and helpful?

5. **Tool Usage** (0-10):
   - Were tools used appropriately for the task?
   - Did Alice use tools proactively rather than just describing what could be done?
   - Was the tool selection optimal?

Please provide:
- A score for each criterion (0-10)
- An overall score (0-10)
- Key strengths of the response
- Areas for improvement
- Specific examples of good or problematic patterns

Format your evaluation as JSON in a code block."""

    async def evaluate_results(self, results_file: str):
        """Evaluate A/B test results using Debbie."""
        # Load test results
        with open(results_file, 'r') as f:
            test_results = json.load(f)
        
        evaluations = []
        
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
            
            # Set up notification handler to capture Debbie's responses
            async def notification_handler(notification):
                method = notification.get("method", "")
                params = notification.get("params", {})
                
                if method == "ChannelMessageNotification":
                    content = params.get("content", "")
                    channel = params.get("channel", "")
                    collected_responses.append({
                        "channel": channel,
                        "content": content
                    })
            
            ws_client.set_notification_handler(notification_handler)
            
            await ws_client.connect()
            
            # Start session
            start_response = await ws_client.send_request(
                method="startSession",
                params={"userId": "debbie_evaluator", "sessionParams": {"language": "en"}},
                request_id=1
            )
            
            session_id = start_response.get("sessionId")
            if not session_id:
                raise Exception("Failed to get session ID")
            
            # Wait for introduction
            await asyncio.sleep(2)
            
            # Switch to Debbie
            collected_responses.clear()
            switch_response = await ws_client.send_request(
                method="sendUserMessage",
                params={"sessionId": session_id, "message": "Switch to agent D (Debbie)"},
                request_id=2
            )
            
            # Wait for switch confirmation
            await asyncio.sleep(2)
            
            request_id = 3
            
            # Evaluate each result
            for test_result in test_results:
                if not test_result.get("success"):
                    continue
                
                print(f"Evaluating {test_result['test_file']} ({test_result['prompt_version']})...")
                
                # Get the response from the test
                responses = test_result.get("results", [])
                if responses:
                    # Combine all responses for this test
                    full_response = "\n".join([r.get("response", "") for r in responses])
                    
                    # Create evaluation prompt
                    eval_prompt = self.create_evaluation_prompt(
                        test_result["test_file"],
                        full_response,
                        test_result["prompt_version"]
                    )
                    
                    # Clear collected responses
                    collected_responses.clear()
                    
                    # Send to Debbie for evaluation
                    eval_response = await ws_client.send_request(
                        method="sendUserMessage",
                        params={"sessionId": session_id, "message": eval_prompt},
                        request_id=request_id
                    )
                    request_id += 1
                    
                    # Wait for Debbie to respond
                    await asyncio.sleep(5)
                    
                    # Combine all collected responses
                    debbie_full_response = "\n".join([
                        f"[{r['channel']}]\n{r['content']}" 
                        for r in collected_responses
                    ])
                    
                    # Extract JSON evaluation from response
                    evaluation = self._extract_json_evaluation(debbie_full_response)
                    
                    evaluations.append({
                        "test_file": test_result["test_file"],
                        "prompt_version": test_result["prompt_version"],
                        "session_id": test_result["session_id"],
                        "evaluation": evaluation,
                        "raw_evaluation": debbie_full_response,
                        "channel_responses": list(collected_responses)
                    })
                    
                    # Brief pause between evaluations
                    await asyncio.sleep(3)
            
            # Close connection
            await ws_client.close()
            
        finally:
            manager.stop_server()
        
        # Save evaluations
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        eval_file = self.evaluations_dir / f"debbie_evaluations_{timestamp}.json"
        
        with open(eval_file, 'w') as f:
            json.dump(evaluations, f, indent=2)
        
        print(f"\nEvaluations saved to: {eval_file}")
        
        # Generate evaluation summary
        self.generate_evaluation_summary(evaluations, timestamp)
        
        return evaluations
    
    def _extract_json_evaluation(self, response: str) -> Dict:
        """Extract JSON evaluation from Debbie's response."""
        import re
        
        # Look for JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code blocks
        try:
            # Look for JSON-like structure
            json_start = response.find('{')
            if json_start != -1:
                # Find matching closing brace
                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(response)):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break
                
                if json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)
        except:
            pass
        
        # Fallback: create basic structure
        return {
            "channel_compliance": 0,
            "conciseness": 0,
            "autonomy": 0,
            "task_completion": 0,
            "tool_usage": 0,
            "overall_score": 0,
            "strengths": [],
            "improvements": [],
            "notes": "Failed to parse evaluation"
        }
    
    def generate_evaluation_summary(self, evaluations: List[Dict], timestamp: str):
        """Generate summary of Debbie's evaluations."""
        summary = {
            "timestamp": timestamp,
            "total_evaluations": len(evaluations),
            "by_version": {
                "current": {
                    "count": 0,
                    "avg_scores": {},
                    "total_overall": 0
                },
                "revised": {
                    "count": 0,
                    "avg_scores": {},
                    "total_overall": 0
                }
            },
            "by_scenario": {},
            "improvements": {
                "channel_compliance": 0,
                "conciseness": 0,
                "autonomy": 0,
                "task_completion": 0,
                "tool_usage": 0,
                "overall": 0
            }
        }
        
        # Criteria to track
        criteria = ["channel_compliance", "conciseness", "autonomy", "task_completion", "tool_usage", "overall_score"]
        
        # Initialize averages
        for version in ["current", "revised"]:
            for criterion in criteria:
                summary["by_version"][version]["avg_scores"][criterion] = 0
        
        # Process evaluations
        for eval_data in evaluations:
            version = eval_data["prompt_version"]
            scenario = eval_data["test_file"]
            evaluation = eval_data["evaluation"]
            
            # Count by version
            summary["by_version"][version]["count"] += 1
            
            # Add scores
            for criterion in criteria:
                if criterion in evaluation:
                    score = evaluation[criterion]
                    # Handle both numeric and string scores
                    if isinstance(score, str):
                        try:
                            score = float(score)
                        except:
                            score = 0
                    summary["by_version"][version]["avg_scores"][criterion] += score
            
            # Track by scenario
            if scenario not in summary["by_scenario"]:
                summary["by_scenario"][scenario] = {
                    "current": {},
                    "revised": {}
                }
            
            summary["by_scenario"][scenario][version] = {
                criterion: evaluation.get(criterion, 0) for criterion in criteria
            }
        
        # Calculate averages
        for version in ["current", "revised"]:
            count = summary["by_version"][version]["count"]
            if count > 0:
                for criterion in criteria:
                    summary["by_version"][version]["avg_scores"][criterion] /= count
        
        # Calculate improvements
        if summary["by_version"]["current"]["count"] > 0 and summary["by_version"]["revised"]["count"] > 0:
            for criterion in criteria:
                current_avg = summary["by_version"]["current"]["avg_scores"][criterion]
                revised_avg = summary["by_version"]["revised"]["avg_scores"][criterion]
                improvement = revised_avg - current_avg
                summary["improvements"][criterion.replace("_score", "")] = improvement
        
        # Save summary
        summary_file = self.evaluations_dir / f"evaluation_summary_{timestamp}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print("\n=== Debbie's Evaluation Summary ===")
        print(f"Total evaluations: {summary['total_evaluations']}")
        
        print("\nAverage Scores by Version:")
        for version in ["current", "revised"]:
            print(f"\n{version.upper()} Prompt:")
            data = summary["by_version"][version]
            if data["count"] > 0:
                for criterion, score in data["avg_scores"].items():
                    print(f"  - {criterion.replace('_', ' ').title()}: {score:.1f}/10")
        
        print("\nImprovements (Revised vs Current):")
        for criterion, improvement in summary["improvements"].items():
            sign = "+" if improvement > 0 else ""
            color = "\033[92m" if improvement > 0 else "\033[91m" if improvement < 0 else "\033[0m"
            reset = "\033[0m"
            print(f"  - {criterion.replace('_', ' ').title()}: {color}{sign}{improvement:.1f}{reset}")
        
        print("\nScores by Scenario:")
        for scenario, data in summary["by_scenario"].items():
            print(f"\n{scenario}:")
            if "current" in data and data["current"]:
                current_overall = data["current"].get("overall_score", 0)
                revised_overall = data["revised"].get("overall_score", 0) if "revised" in data else 0
                improvement = revised_overall - current_overall
                sign = "+" if improvement > 0 else ""
                color = "\033[92m" if improvement > 0 else "\033[91m" if improvement < 0 else "\033[0m"
                reset = "\033[0m"
                print(f"  Current: {current_overall:.1f}/10, Revised: {revised_overall:.1f}/10 ({color}{sign}{improvement:.1f}{reset})")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Evaluate Alice's responses using Debbie")
    parser.add_argument("results_file", help="Path to A/B test results JSON file")
    parser.add_argument("--config", default="config/main.yaml", help="Config file path")
    
    args = parser.parse_args()
    
    evaluator = DebbieEvaluator(args.config)
    await evaluator.evaluate_results(args.results_file)


if __name__ == "__main__":
    asyncio.run(main())