#!/usr/bin/env python3
"""
Test if a model supports structured output by trying to use it.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_whisperer.core.config import load_config
from ai_whisperer.services.ai.openrouter import OpenRouterAIService


async def test_structured_output(model_name: str = None):
    """Test if a model supports structured output."""
    # Load config
    config = load_config("config/main.yaml")
    
    # Use provided model or get from config
    if not model_name:
        model_name = config.get("openrouter", {}).get("model", "openai/gpt-3.5-turbo")
    
    print(f"Testing structured output for model: {model_name}")
    
    # Create AI service with AIConfig
    from ai_whisperer.services.execution.ai_config import AIConfig
    
    openrouter_config = config.get("openrouter", {})
    ai_config = AIConfig(
        api_key=openrouter_config.get("api_key"),
        model_id=model_name,
        temperature=openrouter_config.get("params", {}).get("temperature", 0.7),
        max_tokens=openrouter_config.get("params", {}).get("max_tokens", 8000),
        site_url=openrouter_config.get("site_url", "http://AIWhisperer:8000"),
        app_name=openrouter_config.get("app_name", "AIWhisperer")
    )
    
    ai_service = OpenRouterAIService(ai_config)
    
    # Simple test schema
    test_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "hobbies": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["name", "age", "hobbies"]
    }
    
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "person_info",
            "strict": True,
            "schema": test_schema
        }
    }
    
    # Test message - be explicit about JSON
    messages = [
        {"role": "system", "content": "You must respond with valid JSON only. No other text."},
        {"role": "user", "content": "Generate a JSON object with name (string), age (integer), and hobbies (array of strings) for a fictional person named Alice who is 25 years old and likes reading and hiking."}
    ]
    
    try:
        print("Attempting structured output...")
        
        # Try with structured output
        response_text = ""
        async for chunk in ai_service.stream_chat_completion(
            messages=messages,
            response_format=response_format
        ):
            if chunk.delta_content:
                response_text += chunk.delta_content
        
        print(f"\n✅ SUCCESS! Model supports structured output.")
        print(f"Response: {response_text}")
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response_text)
            print(f"Parsed JSON: {json.dumps(parsed, indent=2)}")
        except json.JSONDecodeError:
            print("Warning: Response is not valid JSON")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {type(e).__name__}: {e}")
        
        # Try without structured output as fallback
        print("\nTrying without structured output...")
        try:
            response_text = ""
            async for chunk in ai_service.stream_chat_completion(messages=messages):
                if chunk.delta_content:
                    response_text += chunk.delta_content
            
            print(f"Fallback response: {response_text[:200]}...")
            return False
            
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
            return False


async def main():
    """Test multiple models."""
    models_to_test = [
        "google/gemini-2.5-flash-preview-05-20:thinking",  # Current Gemini
        "anthropic/claude-3.5-sonnet",  # Claude
        "openai/gpt-4o",  # GPT-4o  
    ]
    
    if len(sys.argv) > 1:
        # Test specific model from command line
        models_to_test = [sys.argv[1]]
    
    results = {}
    for model in models_to_test:
        print("\n" + "="*60)
        result = await test_structured_output(model)
        results[model] = result
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY - Structured Output Support:")
    print("="*60)
    for model, supported in results.items():
        status = "✅ YES" if supported else "❌ NO"
        print(f"{model:<50} {status}")


if __name__ == "__main__":
    asyncio.run(main())