#!/usr/bin/env python3
"""
Test continuation protocol with structured output.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_whisperer.core.config import load_config
from ai_whisperer.services.ai.openrouter import OpenRouterAIService
from ai_whisperer.services.execution.ai_config import AIConfig


async def test_continuation_structured():
    """Test continuation with structured output."""
    # Load config
    config = load_config("config/main.yaml")
    model_name = config.get("openrouter", {}).get("model")
    
    print(f"Testing structured continuation for: {model_name}")
    
    # Create AI service
    openrouter_config = config.get("openrouter", {})
    ai_config = AIConfig(
        api_key=openrouter_config.get("api_key"),
        model_id=model_name,
        temperature=openrouter_config.get("params", {}).get("temperature", 0.7),
        max_tokens=openrouter_config.get("params", {}).get("max_tokens", 8000)
    )
    
    ai_service = OpenRouterAIService(ai_config)
    
    # Load continuation schema
    with open("config/schemas/continuation_schema.json", "r") as f:
        schema = json.load(f)
        if "$schema" in schema:
            del schema["$schema"]
    
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "continuation_protocol",
            "strict": True,
            "schema": schema
        }
    }
    
    # Test with Debbie's introduction
    messages = [
        {
            "role": "system", 
            "content": """You are Debbie, the debugging specialist. Follow channel format:

[ANALYSIS]
Your analysis.

[COMMENTARY]
Tool usage/observations.

[FINAL]
Direct response to user."""
        },
        {"role": "user", "content": "Who are you?"}
    ]
    
    try:
        print("\nTesting with structured output...")
        response_text = ""
        
        async for chunk in ai_service.stream_chat_completion(
            messages=messages,
            response_format=response_format
        ):
            if chunk.delta_content:
                response_text += chunk.delta_content
        
        print(f"\nRaw response:\n{response_text}")
        
        # Try to parse
        try:
            parsed = json.loads(response_text)
            print(f"\n✅ Valid JSON response!")
            print(f"Response field: {parsed.get('response', 'N/A')[:200]}...")
            print(f"Continuation: {parsed.get('continuation', {})}")
            
            # Check if response includes channel format
            if "[ANALYSIS]" in parsed.get("response", ""):
                print("✅ Response includes channel format")
            else:
                print("⚠️  Response missing channel format")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ Invalid JSON: {e}")
            
            # Check for markdown wrapped JSON
            if "```json" in response_text:
                print("⚠️  JSON is wrapped in markdown code blocks")
                
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_continuation_structured())