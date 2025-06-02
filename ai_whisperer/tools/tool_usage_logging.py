"""
Module: ai_whisperer/tools/tool_usage_logging.py
Purpose: Utility functions for tool usage logging

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- log_tool_usage(): Function implementation
- get_tool_usage_log(): Function implementation

Usage:
    tool = Tool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.services.agents.registry import Agent

# Simple in-memory log for demonstration (replace with DB or file in production)
tool_usage_log: List[Dict[str, Any]] = []

def log_tool_usage(agent: Agent, tool: AITool, params: Dict[str, Any], result: Any) -> Dict[str, Any]:
    """
    Log tool usage by an agent.
    
    Args:
        agent: The agent using the tool
        tool: The tool being used
        params: Parameters passed to the tool
        result: Result returned by the tool
        
    Returns:
        The log entry that was created
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": agent.agent_id,
        "agent_name": agent.name,
        "tool_name": tool.name,
        "params": params,
        "result": result,
    }
    tool_usage_log.append(entry)
    logging.info(f"Tool usage: {entry}")
    return entry

def get_tool_usage_log() -> List[Dict[str, Any]]:
    """
    Get the complete tool usage log.
    
    Returns:
        List of tool usage log entries
    """
    return tool_usage_log
