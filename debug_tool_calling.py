#!/usr/bin/env python3
"""Debug tool calling issues in AIWhisperer"""
import asyncio
import json
import logging
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.services.ai.openrouter import OpenRouterAIService
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.core.config import load_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tool_format():
    """Test how tools are formatted and passed to the AI"""
    
    # Load config
    config = load_config("config/main.yaml")
    
    # Initialize tool registry
    tool_registry = get_tool_registry()
    
    # Register a simple tool
    list_dir_tool = ListDirectoryTool()
    tool_registry.register_tool(list_dir_tool)
    
    # Get tool definition
    tool_def = list_dir_tool.get_openrouter_tool_definition()
    print("Tool Definition:")
    print(json.dumps(tool_def, indent=2))
    
    # Get all tool definitions
    all_tools = tool_registry.get_all_tool_definitions()
    print(f"\nTotal tools available: {len(all_tools)}")
    
    # Test with a simple model
    openrouter_config = config.get("openrouter", {})
    ai_config = AIConfig(
        api_key=openrouter_config.get("api_key"),
        model_id="openai/gpt-3.5-turbo",  # Known working model
        temperature=0.7,
        max_tokens=1000
    )
    
    ai_service = OpenRouterAIService(ai_config)
    
    # Test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use the list_directory tool to list files in the current directory."},
        {"role": "user", "content": "Please list the files in the current directory."}
    ]
    
    # Test with just one tool
    single_tool = [tool_def]
    
    print("\nTesting with single tool...")
    print(f"Tool: {json.dumps(single_tool, indent=2)}")
    
    # Stream the response
    try:
        async for chunk in ai_service.stream_chat_completion(messages=messages, tools=single_tool):
            if chunk.delta_content:
                print(chunk.delta_content, end='', flush=True)
            if chunk.delta_tool_call_part:
                print(f"\nTool call: {chunk.delta_tool_call_part}")
            if chunk.finish_reason:
                print(f"\nFinish reason: {chunk.finish_reason}")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tool_format())