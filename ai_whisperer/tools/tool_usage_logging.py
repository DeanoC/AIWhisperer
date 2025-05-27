import logging
from datetime import datetime, timezone
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.agents.registry import Agent

# Simple in-memory log for demonstration (replace with DB or file in production)
tool_usage_log = []

def log_tool_usage(agent: Agent, tool: AITool, params: dict, result: object):
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

def get_tool_usage_log():
    return tool_usage_log
