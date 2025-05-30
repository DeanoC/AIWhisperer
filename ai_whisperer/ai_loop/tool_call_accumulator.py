"""
Tool call accumulator for properly handling streaming tool calls.
"""
import json
from typing import Dict, List, Any, Optional


class ToolCallAccumulator:
    """Accumulates streaming tool call chunks into complete tool calls"""
    
    def __init__(self):
        self.tool_calls: Dict[int, Dict[str, Any]] = {}
        
    def add_chunk(self, delta_tool_calls: List[Dict[str, Any]]) -> None:
        """Add a chunk of tool call data"""
        if not delta_tool_calls:
            return
            
        for tc in delta_tool_calls:
            index = tc.get("index", 0)
            
            if index not in self.tool_calls:
                # First chunk for this tool call
                self.tool_calls[index] = {
                    "id": tc.get("id"),
                    "type": tc.get("type", "function"),
                    "function": {
                        "name": tc.get("function", {}).get("name"),
                        "arguments": ""
                    }
                }
            
            # Accumulate arguments
            if "function" in tc and "arguments" in tc["function"]:
                self.tool_calls[index]["function"]["arguments"] += tc["function"]["arguments"]
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Get the accumulated tool calls"""
        result = []
        for tc in self.tool_calls.values():
            if tc.get("id") and tc.get("function", {}).get("name"):
                result.append(tc)
        return result