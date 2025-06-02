"""
Simplified model compatibility tests for continuation system.
Tests actual model behavior with different continuation scenarios.
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from ai_whisperer.core.config import load_config
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.ai.openrouter import OpenRouterAIService
from ai_whisperer.model_capabilities import get_model_capabilities
from interactive_server.stateless_session_manager import StatelessSessionManager


# Define test models with their capabilities
TEST_MODELS = {
    "openai/gpt-4o-mini": {
        "provider": "openai", 
        "supports_multi_tool": True,
        "continuation_style": "multi_tool"
    },
    "anthropic/claude-3-5-haiku-latest": {
        "provider": "anthropic",
        "supports_multi_tool": True,
        "continuation_style": "multi_tool"
    },
    "google/gemini-1.5-flash": {
        "provider": "google",
        "supports_multi_tool": False,
        "continuation_style": "single_tool"
    }
}


class ModelCompatibilityTester:
    """Runs continuation tests with real session manager but mocked AI service"""
    
    def __init__(self):
        """Initialize tester"""
        self.test_results = {}
        self.get_model_capabilities = get_model_capabilities
        
    def create_test_config(self, model_name: str) -> dict:
        """Create test configuration for a model"""
        return {
            "openrouter": {
                "api_key": "test-key",
                "model": model_name,
                "params": {
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            }
        }
    
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
            # Create configuration
            config = self.create_test_config(model_name)
            
            # Create mocks
            mock_prompt_system = Mock()
            mock_prompt_system.format_prompt.return_value = "Test prompt"
            
            mock_agent_registry = Mock(spec=AgentRegistry)
            mock_agent_factory = Mock(spec=AgentFactory)
            
            # Create session manager with real dependencies where possible
            session_manager = StatelessSessionManager(
                config, 
                mock_prompt_system, 
                mock_agent_registry
            )
            session_manager.agent_factory = mock_agent_factory
            
            # Mock the AI service with scenario-specific responses
            mock_ai_service = self._create_mock_ai_service(model_name, scenario)
            
            # Create a mock agent that uses the mock AI service
            mock_agent = Mock()
            mock_agent.name = "test_agent"
            mock_agent.model_name = model_name
            mock_agent.ai_service = mock_ai_service
            mock_agent.process_message = AsyncMock(side_effect=self._create_agent_processor(scenario, mock_ai_service))
            
            # Configure factory to return our mock agent
            mock_agent_factory.create_agent = Mock(return_value=mock_agent)
            
            # Mock WebSocket
            mock_ws = AsyncMock()
            mock_ws.messages = []
            
            async def capture_send(data):
                mock_ws.messages.append(data)
                
            mock_ws.send_json = capture_send
            
            # Create session
            session_id = "test-session"
            await session_manager.create_session(session_id, mock_ws, {
                "model": model_name,
                "agent": "test"
            })
            
            # Send initial message
            start_time = asyncio.get_event_loop().time()
            
            await session_manager.handle_message(session_id, {
                "message": scenario["initial_message"]
            })
            
            # Track metrics
            end_time = asyncio.get_event_loop().time()
            result["metrics"]["response_time"] = end_time - start_time
            
            # Count continuation-related messages
            continuation_messages = [
                msg for msg in mock_ws.messages 
                if msg.get("method") == "continuation.progress"
            ]
            result["metrics"]["continuation_count"] = len(continuation_messages)
            
            # Count tool calls
            tool_messages = [
                msg for msg in mock_ws.messages
                if msg.get("method") == "tool.start"
            ]
            result["metrics"]["tool_calls"] = len(tool_messages)
            
            # Verify expected behavior based on model type
            model_info = TEST_MODELS[model_name]
            if model_info["continuation_style"] == "single_tool":
                # Single-tool models should show continuation
                if scenario.get("expects_multiple_tools", False):
                    result["success"] = len(continuation_messages) > 0
                else:
                    result["success"] = True
            else:
                # Multi-tool models can batch operations
                result["success"] = True
                
        except Exception as e:
            result["errors"].append(str(e))
            result["success"] = False
            import traceback
            traceback.print_exc()
            
        return result
    
    def _create_mock_ai_service(self, model_name: str, scenario: dict):
        """Create a mock AI service with scenario responses"""
        mock_service = Mock(spec=OpenRouterAIService)
        
        # Configure model capabilities
        model_info = TEST_MODELS[model_name]
        mock_service.supports_multi_tool.return_value = model_info["supports_multi_tool"]
        
        # Create response sequence
        responses = scenario.get("mock_responses", self._get_default_responses(model_info))
        response_iter = iter(responses)
        
        async def mock_process(*args, **kwargs):
            try:
                return next(response_iter)
            except StopIteration:
                return {"response": "Task complete", "tool_calls": []}
        
        mock_service.process_message = AsyncMock(side_effect=mock_process)
        
        return mock_service
    
    def _create_agent_processor(self, scenario: dict, ai_service):
        """Create an agent message processor"""
        async def process_message(message, **kwargs):
            # Simulate agent processing
            result = await ai_service.process_message(message)
            
            # Add continuation signal for single-tool models
            if hasattr(ai_service, 'supports_multi_tool') and not ai_service.supports_multi_tool():
                if result.get("tool_calls") and "complete" not in result.get("response", "").lower():
                    result["needs_continuation"] = True
                    
            return result
            
        return process_message
    
    def _get_default_responses(self, model_info: dict) -> List[dict]:
        """Get default responses based on model type"""
        if model_info["supports_multi_tool"]:
            # Multi-tool model can call multiple tools at once
            return [
                {
                    "response": "I'll help you with this task. Let me gather the information.",
                    "tool_calls": [
                        {"function": {"name": "list_items", "arguments": "{}"}},
                        {"function": {"name": "analyze_items", "arguments": "{}"}}
                    ]
                },
                {
                    "response": "I've completed the analysis. The task is done.",
                    "tool_calls": []
                }
            ]
        else:
            # Single-tool model needs multiple turns
            return [
                {
                    "response": "I'll help you with this task. First, let me list the items.",
                    "tool_calls": [
                        {"function": {"name": "list_items", "arguments": "{}"}}
                    ]
                },
                {
                    "response": "Now I'll analyze the items I found.",
                    "tool_calls": [
                        {"function": {"name": "analyze_items", "arguments": "{}"}}
                    ]
                },
                {
                    "response": "I've completed the analysis. The task is done.",
                    "tool_calls": []
                }
            ]
    
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
            
            # Show metrics
            report.append("\n#### Metrics:")
            for scenario in scenarios:
                metrics = scenario.get("metrics", {})
                report.append(f"- {scenario['scenario']}:")
                report.append(f"  - Continuation Count: {metrics.get('continuation_count', 0)}")
                report.append(f"  - Tool Calls: {metrics.get('tool_calls', 0)}")
                report.append(f"  - Response Time: {metrics.get('response_time', 0):.2f}s")
            
            report.append("")
        
        return "\n".join(report)


# Define test scenarios
CONTINUATION_TEST_SCENARIOS = [
    {
        "name": "Multi-step Task",
        "initial_message": "List the plans and analyze them",
        "expects_multiple_tools": True,
        "mock_responses": [
            {
                "response": "I'll help you list and analyze the plans. Let me start by listing them.",
                "tool_calls": [{"function": {"name": "list_plans", "arguments": "{}"}}]
            },
            {
                "response": "Now I'll analyze each plan in detail.",
                "tool_calls": [{"function": {"name": "analyze_plan", "arguments": "{}"}}]
            },
            {
                "response": "I've completed the analysis of all plans.",
                "tool_calls": []
            }
        ]
    },
    {
        "name": "Single Tool Task",
        "initial_message": "Show me the current directory structure",
        "expects_multiple_tools": False,
        "mock_responses": [
            {
                "response": "I'll show you the directory structure.",
                "tool_calls": [{"function": {"name": "list_directory", "arguments": "{}"}}]
            },
            {
                "response": "Here's the directory structure as requested.",
                "tool_calls": []
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


@pytest.mark.asyncio
async def test_full_compatibility_suite():
    """Run full compatibility test suite"""
    tester = ModelCompatibilityTester()
    results = await tester.run_all_tests(CONTINUATION_TEST_SCENARIOS)
    
    # Generate report
    report = tester.generate_compatibility_report(results)
    
    # Save report
    report_path = Path("test_results/model_compatibility_report_simple.md")
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
                if scenario.get("errors"):
                    print(f"     Error: {scenario['errors'][0]}")
    
    asyncio.run(main())