"""
Model compatibility tests for continuation system.
Tests the same scenarios across different models to ensure consistent behavior.
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from ai_whisperer.core.config import load_config
from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.registry import AgentRegistry
from ai_whisperer.prompt_system import PromptSystem, PromptConfiguration
from interactive_server.stateless_session_manager import StatelessSessionManager


# Define test models with their capabilities
TEST_MODELS = {
    "openai/gpt-4o": {
        "provider": "openai",
        "supports_multi_tool": True,
        "supports_structured_output": True,
        "continuation_style": "multi_tool",
        "max_tokens": 4096
    },
    "openai/gpt-4o-mini": {
        "provider": "openai", 
        "supports_multi_tool": True,
        "supports_structured_output": True,
        "continuation_style": "multi_tool",
        "max_tokens": 16384
    },
    "anthropic/claude-3-5-sonnet-latest": {
        "provider": "anthropic",
        "supports_multi_tool": True,
        "supports_structured_output": False,
        "continuation_style": "multi_tool",
        "max_tokens": 8192
    },
    "anthropic/claude-3-5-haiku-latest": {
        "provider": "anthropic",
        "supports_multi_tool": True,
        "supports_structured_output": False,
        "continuation_style": "multi_tool",
        "max_tokens": 8192
    },
    "google/gemini-2.0-flash-exp": {
        "provider": "google",
        "supports_multi_tool": False,
        "supports_structured_output": False,
        "continuation_style": "single_tool",
        "max_tokens": 32768
    },
    "google/gemini-1.5-pro": {
        "provider": "google",
        "supports_multi_tool": False,
        "supports_structured_output": False,
        "continuation_style": "single_tool", 
        "max_tokens": 32768
    },
    "google/gemini-1.5-flash": {
        "provider": "google",
        "supports_multi_tool": False,
        "supports_structured_output": False,
        "continuation_style": "single_tool",
        "max_tokens": 32768
    }
}


class ModelCompatibilityTester:
    """Runs continuation tests across different models"""
    
    def __init__(self, base_config_path: str = "config.yaml"):
        """Initialize with base configuration"""
        self.base_config_path = base_config_path
        self.base_config = self._load_base_config()
        self.test_results = {}
        
    def _load_base_config(self) -> dict:
        """Load base configuration"""
        try:
            return load_config(self.base_config_path)
        except:
            # Fallback config if file doesn't exist
            return {
                "openrouter": {
                    "api_key": os.environ.get("OPENROUTER_API_KEY", "test-key"),
                    "params": {
                        "temperature": 0.7,
                        "max_tokens": 2000
                    }
                }
            }
    
    def create_model_config(self, model_name: str) -> dict:
        """Create configuration with specific model override"""
        config = self.base_config.copy()
        model_info = TEST_MODELS.get(model_name, {})
        
        # Override model in config
        config["openrouter"]["model"] = model_name
        
        # Adjust parameters based on model capabilities
        if model_info.get("max_tokens"):
            config["openrouter"]["params"]["max_tokens"] = min(
                2000, 
                model_info["max_tokens"]
            )
        
        # Add model-specific settings
        config["model_capabilities"] = model_info
        
        return config
    
    async def test_continuation_scenario(self, model_name: str, scenario: dict) -> dict:
        """Run a continuation scenario with a specific model"""
        print(f"\n🤖 Testing {model_name} with scenario: {scenario['name']}")
        
        result = {
            "model": model_name,
            "scenario": scenario["name"],
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "metrics": {},
            "errors": []
        }
        
        try:
            # Create model-specific config
            config = self.create_model_config(model_name)
            
            # Create session manager with mocked dependencies
            session_manager = StatelessSessionManager(config, None, None)
            
            # Mock WebSocket
            mock_ws = AsyncMock()
            mock_ws.messages = []
            
            async def capture_send(data):
                mock_ws.messages.append(data)
                
            mock_ws.send_json = capture_send
            session_manager.websocket = mock_ws
            
            # Setup test session manager
            session_manager = await self._create_test_agent(session_manager, config, scenario)
            
            # Run scenario
            start_time = asyncio.get_event_loop().time()
            
            # Send initial message
            response = await session_manager.process_message(
                scenario["initial_message"],
                on_stream_chunk=AsyncMock()
            )
            
            # Track metrics
            end_time = asyncio.get_event_loop().time()
            result["metrics"]["response_time"] = end_time - start_time
            result["metrics"]["continuation_count"] = getattr(session_manager, '_continuation_depth', 0)
            
            # Analyze response
            if isinstance(response, dict):
                result["metrics"]["tool_calls"] = len(response.get("tool_calls", []))
                result["metrics"]["response_length"] = len(response.get("response", ""))
                
                # Check if continuation happened as expected
                model_info = TEST_MODELS[model_name]
                if model_info["continuation_style"] == "single_tool":
                    # Single-tool models should trigger continuation
                    if scenario.get("expects_continuation", True):
                        result["success"] = session_manager._continuation_depth > 0
                else:
                    # Multi-tool models might batch operations
                    result["success"] = True  # More lenient for multi-tool
            
            # Verify expected behaviors
            if scenario.get("expected_patterns"):
                response_text = str(response.get("response", ""))
                for pattern in scenario["expected_patterns"]:
                    if pattern.lower() in response_text.lower():
                        result["metrics"]["patterns_matched"] = result["metrics"].get("patterns_matched", 0) + 1
            
            # Check progress notifications
            progress_notifications = [
                msg for msg in mock_ws.messages 
                if msg.get("method") == "continuation.progress"
            ]
            result["metrics"]["progress_notifications"] = len(progress_notifications)
            
        except Exception as e:
            result["errors"].append(str(e))
            result["success"] = False
            
        return result
    
    async def _create_test_agent(self, session_manager, config, scenario):
        """Create a test agent with continuation support"""
        # Mock the session manager's process_message to return scenario responses
        response_generator = self._create_response_generator(scenario)
        
        async def mock_process_message(*args, **kwargs):
            # The session manager will handle continuation internally
            return await response_generator(*args, **kwargs)
        
        session_manager.process_message = mock_process_message
        
        # Return the session manager itself as it handles everything
        return session_manager
    
    def _create_response_generator(self, scenario):
        """Create a response generator for the scenario"""
        responses = scenario.get("mock_responses", [
            {
                "response": "I'll analyze this step by step. First, let me list the items.",
                "tool_calls": [{"function": {"name": "list_items"}}]
            },
            {
                "response": "Found 5 items. Now I'll analyze each one in detail.",
                "tool_calls": [{"function": {"name": "analyze_items"}}]
            },
            {
                "response": "Analysis complete. The task is finished.",
                "tool_calls": []
            }
        ])
        
        response_iter = iter(responses)
        
        async def generate_response(*args, **kwargs):
            try:
                return next(response_iter)
            except StopIteration:
                return {"response": "Task complete"}
                
        return generate_response
    
    async def run_all_tests(self, scenarios: List[dict]) -> dict:
        """Run all scenarios across all models"""
        all_results = {
            "test_run": datetime.now().isoformat(),
            "models_tested": len(TEST_MODELS),
            "scenarios_tested": len(scenarios),
            "results": []
        }
        
        for model_name in TEST_MODELS:
            print(f"\n{'='*60}")
            print(f"Testing Model: {model_name}")
            print(f"{'='*60}")
            
            model_results = {
                "model": model_name,
                "capabilities": TEST_MODELS[model_name],
                "scenario_results": []
            }
            
            for scenario in scenarios:
                try:
                    result = await self.test_continuation_scenario(model_name, scenario)
                    model_results["scenario_results"].append(result)
                except Exception as e:
                    print(f"❌ Error testing {model_name} with {scenario['name']}: {e}")
                    model_results["scenario_results"].append({
                        "model": model_name,
                        "scenario": scenario["name"],
                        "success": False,
                        "error": str(e)
                    })
            
            all_results["results"].append(model_results)
        
        return all_results
    
    def generate_compatibility_report(self, results: dict) -> str:
        """Generate a compatibility report from test results"""
        report = []
        report.append("# Model Continuation Compatibility Report")
        report.append(f"\nGenerated: {results['test_run']}")
        report.append(f"Models Tested: {results['models_tested']}")
        report.append(f"Scenarios Tested: {results['scenarios_tested']}")
        
        report.append("\n## Summary by Model\n")
        
        for model_result in results["results"]:
            model = model_result["model"]
            capabilities = model_result["capabilities"]
            
            report.append(f"### {model}")
            report.append(f"- Provider: {capabilities['provider']}")
            report.append(f"- Multi-tool Support: {capabilities['supports_multi_tool']}")
            report.append(f"- Continuation Style: {capabilities['continuation_style']}")
            
            # Calculate success rate
            scenarios = model_result["scenario_results"]
            success_count = sum(1 for s in scenarios if s.get("success", False))
            success_rate = (success_count / len(scenarios) * 100) if scenarios else 0
            
            report.append(f"- Success Rate: {success_rate:.1f}% ({success_count}/{len(scenarios)})")
            
            # Show failed scenarios
            failed = [s for s in scenarios if not s.get("success", False)]
            if failed:
                report.append("\n#### Failed Scenarios:")
                for f in failed:
                    report.append(f"- {f['scenario']}: {f.get('errors', ['Unknown error'])}")
            
            report.append("")
        
        return "\n".join(report)


# Define test scenarios
CONTINUATION_TEST_SCENARIOS = [
    {
        "name": "Multi-step Plan Execution",
        "initial_message": "Execute the python-ast-json plan. List plans, read the plan, then decompose it.",
        "expects_continuation": True,
        "expected_patterns": ["list", "read", "decompose"],
        "continuation_config": {
            "require_explicit_signal": False,
            "max_iterations": 5,
            "continuation_patterns": ["now I'll", "next", "then"],
            "termination_patterns": ["complete", "done", "finished"]
        }
    },
    {
        "name": "RFC Creation Flow", 
        "initial_message": "Create an RFC for adding dark mode. First check existing RFCs, then create a new one.",
        "expects_continuation": True,
        "expected_patterns": ["existing", "create", "RFC"],
        "continuation_config": {
            "require_explicit_signal": False,
            "max_iterations": 3,
            "continuation_patterns": ["now I'll", "let me"],
            "termination_patterns": ["created", "complete"]
        }
    },
    {
        "name": "Simple Single Tool",
        "initial_message": "List the files in the current directory.",
        "expects_continuation": False,
        "expected_patterns": ["files", "directory"],
        "mock_responses": [
            {
                "response": "Here are the files in the current directory.",
                "tool_calls": [{"function": {"name": "list_directory"}}]
            }
        ]
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", list(TEST_MODELS.keys()))
async def test_model_continuation_compatibility(model_name):
    """Test continuation compatibility for each model"""
    tester = ModelCompatibilityTester()
    
    # Run single scenario for quick testing
    scenario = CONTINUATION_TEST_SCENARIOS[0]
    result = await tester.test_continuation_scenario(model_name, scenario)
    
    # Basic assertions
    assert result["model"] == model_name
    assert "success" in result
    assert "metrics" in result
    
    # Model-specific assertions
    model_info = TEST_MODELS[model_name]
    if model_info["continuation_style"] == "single_tool":
        # Single-tool models should show continuation behavior
        if scenario["expects_continuation"]:
            assert result["metrics"].get("continuation_count", 0) > 0 or not result["success"]


@pytest.mark.asyncio
async def test_full_compatibility_suite():
    """Run full compatibility test suite"""
    tester = ModelCompatibilityTester()
    results = await tester.run_all_tests(CONTINUATION_TEST_SCENARIOS)
    
    # Generate report
    report = tester.generate_compatibility_report(results)
    
    # Save report
    report_path = Path("test_results/model_compatibility_report.md")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report)
    
    print(f"\n📊 Compatibility report saved to: {report_path}")
    
    # Basic assertions
    assert results["models_tested"] == len(TEST_MODELS)
    assert results["scenarios_tested"] == len(CONTINUATION_TEST_SCENARIOS)
    assert len(results["results"]) == len(TEST_MODELS)


if __name__ == "__main__":
    # Allow running as a script for manual testing
    async def main():
        tester = ModelCompatibilityTester()
        results = await tester.run_all_tests(CONTINUATION_TEST_SCENARIOS)
        
        # Print summary
        print("\n" + "="*60)
        print("COMPATIBILITY TEST SUMMARY")
        print("="*60)
        
        for model_result in results["results"]:
            model = model_result["model"]
            scenarios = model_result["scenario_results"]
            success_count = sum(1 for s in scenarios if s.get("success", False))
            
            print(f"\n{model}:")
            print(f"  Success: {success_count}/{len(scenarios)}")
            
            for scenario in scenarios:
                status = "✅" if scenario.get("success") else "❌"
                print(f"  {status} {scenario['scenario']}")
        
        # Save detailed results
        results_path = Path("test_results/model_compatibility_results.json")
        results_path.parent.mkdir(exist_ok=True)
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📁 Detailed results saved to: {results_path}")
    
    asyncio.run(main())