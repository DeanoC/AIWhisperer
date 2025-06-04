#!/usr/bin/env python3
"""
Model Capability Tester for OpenRouter Models

This script tests various model capabilities and quirks by running actual tests
against the OpenRouter API. It outputs a JSON file with detected capabilities.

Usage:
    python test_model_capabilities.py                    # Test top models from rankings
    python test_model_capabilities.py --model MODEL_ID  # Test specific model
    python test_model_capabilities.py --all             # Test ALL models (warning: expensive!)
    python test_model_capabilities.py --list            # List available models
"""

import os
import json
import argparse
import requests
import time
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenRouter API settings
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS_API_URL = "https://openrouter.ai/api/v1/models"
API_KEY = os.getenv('OPENROUTER_API_KEY')

# Top models from OpenRouter rankings (as of 2024)
# These are commonly used models that we should test by default
TOP_MODELS = [
    "openai/gpt-4",
    "openai/gpt-4-turbo",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-opus",
    "anthropic/claude-3-sonnet",
    "anthropic/claude-3-5-sonnet",
    "anthropic/claude-3-5-sonnet-latest",
    "anthropic/claude-3-haiku",
    "google/gemini-pro",
    "google/gemini-1.5-pro",
    "google/gemini-1.5-flash",
    "google/gemini-2.0-flash-exp",
    "google/gemini-2.5-flash-preview",
    "meta-llama/llama-3-70b-instruct",
    "mistralai/mixtral-8x7b-instruct",
    "mistralai/mistral-7b-instruct",
]

class ModelCapabilityTester:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://AIWhisperer:8000",
            "X-Title": "AIWhisperer Model Tester"
        }
        self.results = {}
        
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetch list of available models from OpenRouter"""
        try:
            response = requests.get(MODELS_API_URL, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []
    
    def test_model(self, model_id: str) -> Dict[str, Any]:
        """Run comprehensive tests on a single model"""
        print(f"\n{'='*60}")
        print(f"Testing model: {model_id}")
        print(f"{'='*60}")
        
        capabilities = {
            "model_id": model_id,
            "tested_at": datetime.now().isoformat(),
            "multi_tool": False,
            "parallel_tools": False,
            "max_tools_per_turn": 0,
            "structured_output": False,
            "quirks": {},
            "test_results": {}
        }
        
        # Test 1: Basic functionality
        print("Test 1: Basic functionality...")
        basic_result = self._test_basic_functionality(model_id)
        capabilities["test_results"]["basic"] = basic_result
        if not basic_result["success"]:
            print(f"  ❌ Model failed basic test: {basic_result.get('error', 'Unknown error')}")
            return capabilities
        print("  ✅ Basic functionality works")
        
        # Test 2: Single tool calling
        print("Test 2: Single tool calling...")
        single_tool_result = self._test_single_tool(model_id)
        capabilities["test_results"]["single_tool"] = single_tool_result
        if single_tool_result["success"]:
            capabilities["max_tools_per_turn"] = 1
            print("  ✅ Single tool calling works")
        else:
            print(f"  ❌ Single tool calling failed: {single_tool_result.get('error', 'Unknown error')}")
        
        # Test 3: Multiple tool calling
        if single_tool_result["success"]:
            print("Test 3: Multiple tool calling...")
            multi_tool_result = self._test_multi_tool(model_id)
            capabilities["test_results"]["multi_tool"] = multi_tool_result
            if multi_tool_result["success"]:
                capabilities["multi_tool"] = True
                capabilities["parallel_tools"] = True
                capabilities["max_tools_per_turn"] = multi_tool_result.get("tools_called", 2)
                print(f"  ✅ Multiple tool calling works ({capabilities['max_tools_per_turn']} tools)")
            else:
                print("  ❌ Multiple tool calling not supported")
        
        # Test 4: Structured output (JSON)
        print("Test 4: Structured output...")
        structured_result = self._test_structured_output(model_id)
        capabilities["test_results"]["structured_output"] = structured_result
        if structured_result["success"]:
            capabilities["structured_output"] = True
            print("  ✅ Structured output works")
        else:
            print(f"  ❌ Structured output failed: {structured_result.get('error', 'Unknown error')}")
        
        # Test 5: Tools with structured output (quirk test)
        if single_tool_result["success"] and structured_result["success"]:
            print("Test 5: Tools + Structured output (quirk test)...")
            quirk_result = self._test_tools_with_structured_output(model_id)
            capabilities["test_results"]["tools_with_structured"] = quirk_result
            if not quirk_result["success"]:
                capabilities["quirks"]["no_tools_with_structured_output"] = True
                print(f"  ⚠️  Quirk detected: {quirk_result.get('error', 'Cannot use tools with structured output')}")
            else:
                print("  ✅ Tools work with structured output")
        
        # Test 6: Structured output hidden quirk (for Anthropic models)
        if "anthropic/claude" in model_id and not structured_result["success"]:
            print("Test 6: Checking for hidden structured output support...")
            hidden_structured_result = self._test_hidden_structured_output(model_id)
            capabilities["test_results"]["hidden_structured_output"] = hidden_structured_result
            if hidden_structured_result["success"]:
                capabilities["structured_output"] = True
                capabilities["quirks"]["structured_output_hidden"] = True
                print("  ⚠️  Quirk detected: Model supports structured output but reports it doesn't")
            else:
                print("  ❌ No hidden structured output support")
        
        # Test 7: Reasoning tokens (for models that support it)
        if "thinking" in model_id or "reasoning" in model_id:
            print("Test 7: Reasoning tokens...")
            reasoning_result = self._test_reasoning_tokens(model_id)
            capabilities["test_results"]["reasoning"] = reasoning_result
            if reasoning_result["success"]:
                capabilities["supports_reasoning"] = True
                print("  ✅ Reasoning tokens supported")
        
        return capabilities
    
    def _make_request(self, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Make a request to OpenRouter API and return success status and response"""
        try:
            response = requests.post(API_URL, headers=self.headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    return True, data
                else:
                    return False, {"error": "No choices in response", "raw": data}
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {})
                    if isinstance(error_msg, dict):
                        # Extract nested error message
                        if "metadata" in error_msg and "raw" in error_msg["metadata"]:
                            try:
                                raw_error = json.loads(error_msg["metadata"]["raw"])
                                error_text = raw_error.get("error", {}).get("message", str(error_msg))
                            except:
                                error_text = error_msg.get("message", str(error_msg))
                        else:
                            error_text = error_msg.get("message", str(error_msg))
                    else:
                        error_text = str(error_msg)
                    return False, {"error": error_text, "status_code": response.status_code}
                except:
                    return False, {"error": response.text, "status_code": response.status_code}
                    
        except Exception as e:
            return False, {"error": str(e)}
    
    def _test_basic_functionality(self, model_id: str) -> Dict[str, Any]:
        """Test if model can respond to basic prompts"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Say 'Hello World' and nothing else."}
            ],
            "temperature": 0,
            "max_tokens": 50
        }
        
        success, response = self._make_request(payload)
        if success:
            content = response['choices'][0]['message']['content']
            return {"success": True, "response": content}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def _test_single_tool(self, model_id: str) -> Dict[str, Any]:
        """Test single tool calling"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "What's the weather in New York? Use the get_weather tool."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "The city name"}
                            },
                            "required": ["location"]
                        }
                    }
                }
            ],
            "temperature": 0,
            "max_tokens": 200
        }
        
        success, response = self._make_request(payload)
        if success:
            message = response['choices'][0]['message']
            if 'tool_calls' in message and message['tool_calls']:
                return {"success": True, "tools_called": len(message['tool_calls'])}
            else:
                return {"success": False, "error": "No tool calls in response"}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def _test_multi_tool(self, model_id: str) -> Dict[str, Any]:
        """Test multiple tool calling in one response"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Get the weather in both New York and London. Use the get_weather tool for each city."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get the weather for a location",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "location": {"type": "string", "description": "The city name"}
                            },
                            "required": ["location"]
                        }
                    }
                }
            ],
            "temperature": 0,
            "max_tokens": 300
        }
        
        success, response = self._make_request(payload)
        if success:
            message = response['choices'][0]['message']
            if 'tool_calls' in message and len(message['tool_calls']) > 1:
                return {"success": True, "tools_called": len(message['tool_calls'])}
            else:
                return {"success": False, "error": "Model called only one tool or no tools"}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def _test_structured_output(self, model_id: str) -> Dict[str, Any]:
        """Test structured JSON output"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Return a JSON object with 'name' and 'age' fields. Use 'Alice' and 30."}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "person",
                    "strict": False,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "age": {"type": "integer"}
                        },
                        "required": ["name", "age"]
                    }
                }
            },
            "temperature": 0,
            "max_tokens": 100
        }
        
        success, response = self._make_request(payload)
        if success:
            content = response['choices'][0]['message']['content']
            try:
                parsed = json.loads(content)
                if "name" in parsed and "age" in parsed:
                    return {"success": True, "response": parsed}
                else:
                    return {"success": False, "error": "Response doesn't match schema"}
            except json.JSONDecodeError:
                return {"success": False, "error": "Response is not valid JSON"}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def _test_tools_with_structured_output(self, model_id: str) -> Dict[str, Any]:
        """Test if model can use tools and structured output together"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Just respond with a greeting in the required JSON format. Don't use any tools."}
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "dummy_tool",
                        "description": "A dummy tool that's available but shouldn't be used",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "param": {"type": "string"}
                            }
                        }
                    }
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "greeting",
                    "strict": False,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "greeting": {"type": "string"}
                        },
                        "required": ["greeting"]
                    }
                }
            },
            "temperature": 0,
            "max_tokens": 100
        }
        
        success, response = self._make_request(payload)
        if success:
            return {"success": True}
        else:
            # Extract specific error message if it's about mime type
            error_msg = response.get("error", "")
            if "mime type" in str(error_msg).lower() or "application/json" in str(error_msg):
                return {"success": False, "error": "Function calling with JSON response format unsupported"}
            return {"success": False, "error": error_msg}
    
    def _test_hidden_structured_output(self, model_id: str) -> Dict[str, Any]:
        """Test if Anthropic models actually support structured output despite reporting otherwise"""
        # Try a different approach - use JSON mode instead of json_schema
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You must respond with valid JSON only."},
                {"role": "user", "content": "Return a JSON object with 'name' set to 'Alice' and 'age' set to 30."}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
            "max_tokens": 100
        }
        
        success, response = self._make_request(payload)
        if success:
            content = response['choices'][0]['message']['content']
            try:
                parsed = json.loads(content)
                if "name" in parsed and "age" in parsed:
                    # Also try with json_schema format but different parameters
                    schema_payload = {
                        "model": model_id,
                        "messages": [
                            {"role": "user", "content": "Return JSON with name='Bob' and age=25"}
                        ],
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "person_info",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "age": {"type": "integer"}
                                    },
                                    "required": ["name", "age"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "temperature": 0,
                        "max_tokens": 100
                    }
                    
                    schema_success, schema_response = self._make_request(schema_payload)
                    if schema_success:
                        return {"success": True, "method": "json_schema"}
                    else:
                        return {"success": True, "method": "json_object"}
                else:
                    return {"success": False, "error": "Response doesn't match expected structure"}
            except json.JSONDecodeError:
                return {"success": False, "error": "Response is not valid JSON"}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def _test_reasoning_tokens(self, model_id: str) -> Dict[str, Any]:
        """Test reasoning token support"""
        payload = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": "Think step by step: What is 15 * 17?"}
            ],
            "reasoning": {"max_reasoning_tokens": 100},
            "temperature": 0,
            "max_tokens": 50
        }
        
        success, response = self._make_request(payload)
        if success:
            # Check if response includes reasoning tokens
            usage = response.get("usage", {})
            if "reasoning_tokens" in usage:
                return {"success": True, "reasoning_tokens": usage["reasoning_tokens"]}
            return {"success": True, "reasoning_tokens": 0}
        else:
            return {"success": False, "error": response.get("error", "Unknown error")}
    
    def test_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """Test multiple models and compile results"""
        all_results = {}
        
        for i, model_id in enumerate(model_ids, 1):
            print(f"\n[{i}/{len(model_ids)}] Testing {model_id}")
            
            # Rate limiting - be nice to the API
            if i > 1:
                time.sleep(2)  # 2 second delay between models
            
            try:
                result = self.test_model(model_id)
                all_results[model_id] = result
                
                # Save intermediate results in case of crash
                self._save_results(all_results, "model_capabilities_partial.json")
                
            except Exception as e:
                print(f"  ❌ Error testing {model_id}: {e}")
                all_results[model_id] = {
                    "model_id": model_id,
                    "error": str(e),
                    "tested_at": datetime.now().isoformat()
                }
        
        return all_results
    
    def _save_results(self, results: Dict[str, Any], filename: str):
        """Save results to JSON file"""
        output = {
            "generated_at": datetime.now().isoformat(),
            "generator": "AIWhisperer Model Capability Tester",
            "models": results
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: {filename}")
    
    def generate_capability_dict(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a model_capabilities.py compatible dictionary from test results"""
        capabilities = {}
        
        for model_id, result in results.items():
            if "error" in result:
                continue
                
            cap = {
                "multi_tool": result.get("multi_tool", False),
                "parallel_tools": result.get("parallel_tools", False),
                "max_tools_per_turn": result.get("max_tools_per_turn", 1),
                "structured_output": result.get("structured_output", False),
                "quirks": result.get("quirks", {})
            }
            
            capabilities[model_id] = cap
        
        return capabilities


def main():
    parser = argparse.ArgumentParser(description="Test model capabilities on OpenRouter")
    parser.add_argument("--model", help="Test a specific model")
    parser.add_argument("--all", action="store_true", help="Test ALL available models (expensive!)")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--output", default="model_capabilities_tested.json", help="Output filename")
    
    args = parser.parse_args()
    
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not found in environment")
        print("Please set your OpenRouter API key in .env file or environment")
        sys.exit(1)
    
    tester = ModelCapabilityTester(API_KEY)
    
    if args.list:
        print("Fetching available models...")
        models = tester.get_available_models()
        print(f"\nFound {len(models)} models:")
        for model in sorted(models, key=lambda x: x.get("id", "")):
            model_id = model.get("id", "unknown")
            pricing = model.get("pricing", {})
            prompt_price_raw = pricing.get("prompt", "0")
            try:
                prompt_price = float(prompt_price_raw) * 1_000_000  # Convert to per million
                print(f"  {model_id:<50} ${prompt_price:.2f}/1M tokens")
            except (ValueError, TypeError):
                print(f"  {model_id:<50} $?.??/1M tokens")
        return
    
    # Determine which models to test
    if args.model:
        models_to_test = [args.model]
        print(f"Testing single model: {args.model}")
    elif args.all:
        print("Fetching all available models...")
        all_models = tester.get_available_models()
        models_to_test = [m.get("id") for m in all_models if m.get("id")]
        print(f"WARNING: Testing {len(models_to_test)} models. This will be expensive!")
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            return
    else:
        models_to_test = TOP_MODELS
        print(f"Testing {len(models_to_test)} top models from OpenRouter rankings")
    
    # Run tests
    print("\nStarting capability tests...")
    results = tester.test_models(models_to_test)
    
    # Save full results
    tester._save_results(results, args.output)
    
    # Generate and save capability dictionary
    cap_dict = tester.generate_capability_dict(results)
    cap_output = {
        "generated_at": datetime.now().isoformat(),
        "model_capabilities": cap_dict
    }
    
    cap_filename = args.output.replace(".json", "_capabilities.json")
    with open(cap_filename, 'w') as f:
        json.dump(cap_output, f, indent=2)
    
    print(f"Capability dictionary saved to: {cap_filename}")
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in results.values() if "error" not in r)
    print(f"Successfully tested: {success_count}/{len(results)} models")
    
    multi_tool_models = [m for m, r in results.items() if r.get("multi_tool", False)]
    structured_models = [m for m, r in results.items() if r.get("structured_output", False)]
    quirky_models = [m for m, r in results.items() if r.get("quirks", {})]
    
    print(f"\nMulti-tool capable: {len(multi_tool_models)} models")
    print(f"Structured output capable: {len(structured_models)} models")
    print(f"Models with quirks: {len(quirky_models)} models")
    
    if quirky_models:
        print("\nQuirks detected:")
        for model in quirky_models:
            quirks = results[model].get("quirks", {})
            for quirk, value in quirks.items():
                if value:
                    print(f"  {model}: {quirk}")


if __name__ == "__main__":
    main()