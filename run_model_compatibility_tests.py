#!/usr/bin/env python3
"""
Run continuation compatibility tests across multiple models.
This script allows easy testing of new models and regression testing.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_whisperer.core.config import load_config
from ai_whisperer.model_override import ModelOverride
from ai_whisperer.extensions.batch.client import BatchClient
from tests.integration.test_model_continuation_compatibility import (
    ModelCompatibilityTester,
    CONTINUATION_TEST_SCENARIOS,
    TEST_MODELS
)


def print_banner(text: str):
    """Print a formatted banner"""
    width = 70
    print("\n" + "=" * width)
    print(f"{text:^{width}}")
    print("=" * width)


async def test_single_model(model_name: str, base_config_path: str = "config.yaml"):
    """Test a single model with all scenarios"""
    print_banner(f"Testing {model_name}")
    
    # Load base config
    try:
        base_config = load_config(base_config_path)
    except Exception as e:
        print(f"⚠️  Warning: Could not load config from {base_config_path}: {e}")
        base_config = {
            "openrouter": {
                "api_key": os.environ.get("OPENROUTER_API_KEY", ""),
                "params": {"temperature": 0.7}
            }
        }
    
    # Apply model override
    override = ModelOverride(base_config)
    config = override.apply_override(model_name)
    
    # Save temporary config
    temp_config_path = Path(f"temp_config_{model_name.replace('/', '_')}.yaml")
    override.save_override_config(temp_config_path)
    
    # Run tests
    tester = ModelCompatibilityTester(str(temp_config_path))
    results = await tester.run_all_tests(CONTINUATION_TEST_SCENARIOS)
    
    # Clean up temp config
    temp_config_path.unlink(missing_ok=True)
    
    return results


async def test_multiple_models(model_names: List[str], save_report: bool = True):
    """Test multiple models and generate comparison report"""
    print_banner("Multi-Model Continuation Test Suite")
    
    all_results = {
        "test_run": datetime.now().isoformat(),
        "models": {},
        "summary": {}
    }
    
    for model_name in model_names:
        try:
            results = await test_single_model(model_name)
            all_results["models"][model_name] = results
        except Exception as e:
            print(f"\n❌ Error testing {model_name}: {e}")
            all_results["models"][model_name] = {
                "error": str(e),
                "success": False
            }
    
    # Generate summary
    all_results["summary"] = generate_summary(all_results["models"])
    
    # Save results
    if save_report:
        save_test_results(all_results)
    
    # Print summary
    print_summary(all_results["summary"])
    
    return all_results


def generate_summary(model_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary statistics from model results"""
    summary = {
        "total_models": len(model_results),
        "successful_models": 0,
        "model_scores": {},
        "best_single_tool_model": None,
        "best_multi_tool_model": None
    }
    
    for model_name, results in model_results.items():
        if isinstance(results, dict) and "results" in results:
            # Calculate success rate
            total_tests = 0
            successful_tests = 0
            
            for model_data in results["results"]:
                for scenario in model_data.get("scenario_results", []):
                    total_tests += 1
                    if scenario.get("success", False):
                        successful_tests += 1
            
            success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
            summary["model_scores"][model_name] = {
                "success_rate": success_rate,
                "total_tests": total_tests,
                "successful_tests": successful_tests
            }
            
            if success_rate > 0:
                summary["successful_models"] += 1
            
            # Track best models by type
            model_info = TEST_MODELS.get(model_name, {})
            if model_info.get("continuation_style") == "single_tool":
                if not summary["best_single_tool_model"] or \
                   success_rate > summary["model_scores"].get(summary["best_single_tool_model"], {}).get("success_rate", 0):
                    summary["best_single_tool_model"] = model_name
            else:
                if not summary["best_multi_tool_model"] or \
                   success_rate > summary["model_scores"].get(summary["best_multi_tool_model"], {}).get("success_rate", 0):
                    summary["best_multi_tool_model"] = model_name
    
    return summary


def print_summary(summary: Dict[str, Any]):
    """Print test summary"""
    print_banner("Test Summary")
    
    print(f"\nModels Tested: {summary['total_models']}")
    print(f"Successful Models: {summary['successful_models']}")
    
    if summary["best_single_tool_model"]:
        print(f"\nBest Single-Tool Model: {summary['best_single_tool_model']}")
        score = summary["model_scores"][summary["best_single_tool_model"]]
        print(f"  Success Rate: {score['success_rate']:.1f}%")
    
    if summary["best_multi_tool_model"]:
        print(f"\nBest Multi-Tool Model: {summary['best_multi_tool_model']}")
        score = summary["model_scores"][summary["best_multi_tool_model"]]
        print(f"  Success Rate: {score['success_rate']:.1f}%")
    
    print("\n📊 Model Scores:")
    for model_name, score in summary["model_scores"].items():
        status = "✅" if score["success_rate"] >= 70 else "⚠️" if score["success_rate"] >= 40 else "❌"
        print(f"{status} {model_name:40} {score['success_rate']:5.1f}% ({score['successful_tests']}/{score['total_tests']})")


def save_test_results(results: Dict[str, Any]):
    """Save test results to files"""
    # Create results directory
    results_dir = Path("test_results")
    results_dir.mkdir(exist_ok=True)
    
    # Save JSON results
    json_path = results_dir / f"model_compatibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Results saved to: {json_path}")
    
    # Generate markdown report
    md_path = results_dir / f"model_compatibility_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(md_path, 'w') as f:
        f.write(generate_markdown_report(results))
    print(f"📄 Report saved to: {md_path}")


def generate_markdown_report(results: Dict[str, Any]) -> str:
    """Generate a markdown report from results"""
    lines = []
    lines.append("# Model Continuation Compatibility Report")
    lines.append(f"\nGenerated: {results['test_run']}")
    
    summary = results.get("summary", {})
    lines.append(f"\n## Summary")
    lines.append(f"- Models Tested: {summary.get('total_models', 0)}")
    lines.append(f"- Successful Models: {summary.get('successful_models', 0)}")
    
    if summary.get("best_single_tool_model"):
        lines.append(f"- Best Single-Tool Model: **{summary['best_single_tool_model']}**")
    if summary.get("best_multi_tool_model"):
        lines.append(f"- Best Multi-Tool Model: **{summary['best_multi_tool_model']}**")
    
    lines.append("\n## Detailed Results\n")
    
    for model_name, score in summary.get("model_scores", {}).items():
        lines.append(f"### {model_name}")
        lines.append(f"- Success Rate: {score['success_rate']:.1f}%")
        lines.append(f"- Tests Passed: {score['successful_tests']}/{score['total_tests']}")
        
        # Add model capabilities
        model_info = TEST_MODELS.get(model_name, {})
        if model_info:
            lines.append(f"- Continuation Style: {model_info.get('continuation_style', 'unknown')}")
            lines.append(f"- Multi-Tool Support: {model_info.get('supports_multi_tool', False)}")
        
        lines.append("")
    
    return "\n".join(lines)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test continuation compatibility across models")
    parser.add_argument("--models", nargs="+", help="Specific models to test")
    parser.add_argument("--all", action="store_true", help="Test all known models")
    parser.add_argument("--single", help="Test a single model")
    parser.add_argument("--config", default="config.yaml", help="Base config file path")
    parser.add_argument("--no-save", action="store_true", help="Don't save results")
    
    args = parser.parse_args()
    
    # Determine which models to test
    models_to_test = []
    
    if args.all:
        models_to_test = list(TEST_MODELS.keys())
    elif args.single:
        models_to_test = [args.single]
    elif args.models:
        models_to_test = args.models
    else:
        # Default: test a representative set
        models_to_test = [
            "openai/gpt-4o-mini",
            "anthropic/claude-3-5-haiku-latest", 
            "google/gemini-1.5-flash"
        ]
    
    print(f"🧪 Testing models: {', '.join(models_to_test)}")
    
    # Run tests
    try:
        results = asyncio.run(test_multiple_models(
            models_to_test,
            save_report=not args.no_save
        ))
        
        # Exit with error if any model failed completely
        if results["summary"]["successful_models"] == 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()