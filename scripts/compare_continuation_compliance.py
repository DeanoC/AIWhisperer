#!/usr/bin/env python3
"""
Compare continuation protocol compliance between models.

This creates separate config files and tests each model.
"""
import subprocess
import re
import json
import sys
from pathlib import Path
import time


def create_model_config(model_name: str, config_path: str):
    """Create a config file for a specific model."""
    config_content = f"""openrouter:
  model: {model_name}
  params:
    temperature: 0.7
    max_tokens: 8000
  site_url: http://AIWhisperer:8000
  app_name: AIWhisperer
prompts: {{}}
workspace_ignore_patterns:
- .git
- .venv
- __pycache__
- .idea
- .vscode
- project_dev/done"""
    
    Path(config_path).write_text(config_content)


def test_model(model_name: str, config_path: str, prompt: str) -> dict:
    """Test a specific model for continuation compliance."""
    # Create test conversation file
    test_file = Path(f"test_{model_name.replace('/', '_')}.txt")
    test_file.write_text(prompt)
    
    try:
        # Run conversation replay
        result = subprocess.run(
            ["python", "-m", "ai_whisperer.interfaces.cli.main",
             "--config", config_path,
             "replay", str(test_file),
             "--timeout", "10"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        # Find [FINAL] response
        final_pos = output.rfind("[FINAL]")
        if final_pos == -1:
            return {
                "model": model_name,
                "has_response": False,
                "has_continuation": False,
                "error": "No [FINAL] response found"
            }
        
        # Extract response (up to 2000 chars after [FINAL])
        response = output[final_pos:final_pos+2000]
        
        # Look for continuation signal
        json_pattern = r'\{"continuation":\s*\{[^}]+\}\}'
        match = re.search(json_pattern, response)
        
        result_data = {
            "model": model_name,
            "has_response": True,
            "has_continuation": match is not None,
            "response_snippet": response[:300] + "..." if len(response) > 300 else response
        }
        
        if match:
            try:
                cont_data = json.loads(match.group(0))
                result_data["continuation"] = cont_data["continuation"]
            except:
                result_data["continuation"] = "Failed to parse"
        
        return result_data
        
    finally:
        test_file.unlink(missing_ok=True)


def main():
    print("=== Model Continuation Protocol Compliance Comparison ===")
    print("=" * 70)
    
    # Models to test
    models = [
        ("google/gemini-2.5-flash-preview-05-20:thinking", "Gemini 2.5 Flash"),
        ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet"),
        ("openai/gpt-4o", "GPT-4o"),
    ]
    
    # Test prompt
    prompt = "Who are you? Please introduce yourself briefly."
    
    results = []
    
    for model_id, display_name in models:
        print(f"\nTesting {display_name}...")
        
        # Create config for this model
        config_path = f"config/test_{model_id.replace('/', '_')}.yaml"
        create_model_config(model_id, config_path)
        
        try:
            # Test the model
            result = test_model(model_id, config_path, prompt)
            result["display_name"] = display_name
            results.append(result)
            
            # Display result
            if result["has_continuation"]:
                print(f"✅ {display_name}: COMPLIANT")
                if "continuation" in result:
                    print(f"   Status: {result['continuation'].get('status', 'N/A')}")
                    print(f"   Reason: {result['continuation'].get('reason', 'N/A')[:50]}...")
            else:
                print(f"❌ {display_name}: NOT COMPLIANT")
                if "error" in result:
                    print(f"   Error: {result['error']}")
            
        finally:
            # Clean up config
            Path(config_path).unlink(missing_ok=True)
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"{'Model':<30} {'Compliant':<15} {'Details'}")
    print("-" * 70)
    
    for result in results:
        status = "✅ Yes" if result["has_continuation"] else "❌ No"
        details = ""
        if result["has_continuation"] and "continuation" in result:
            details = f"Status: {result['continuation'].get('status', 'N/A')}"
        elif "error" in result:
            details = result["error"]
        else:
            details = "No continuation signal"
        
        print(f"{result['display_name']:<30} {status:<15} {details}")
    
    # Show example response snippets
    print("\n" + "=" * 70)
    print("RESPONSE EXAMPLES")
    print("=" * 70)
    
    for result in results:
        if result["has_response"]:
            print(f"\n{result['display_name']}:")
            print("-" * 40)
            print(result["response_snippet"])
            if not result["has_continuation"]:
                print("⚠️  Note: No continuation signal in response")


if __name__ == "__main__":
    main()