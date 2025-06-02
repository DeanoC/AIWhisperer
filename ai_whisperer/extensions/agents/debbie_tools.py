"""
Module: ai_whisperer/agents/debbie_tools.py
Purpose: AI agent implementation for specialized task handling

Tool registration for Debbie the Debugger.
Registers Debbie's specialized debugging tools when she's the active agent.

Key Components:
- get_debbie_tools(): Get all of Debbie's debugging tools
- register_debbie_tools(): Register Debbie's tools with the tool registry
- unregister_debbie_tools(): Unregister Debbie's tools from the tool registry

Usage:
    tool = Tool()
    result = await tool.execute(**parameters)

Dependencies:
- logging

Related:
- See UNTESTED_MODULES_REPORT.md
- See TEST_CONSOLIDATED_SUMMARY.md

"""

import logging
from typing import List

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.session_health_tool import SessionHealthTool
from ai_whisperer.tools.session_analysis_tool import SessionAnalysisTool
from ai_whisperer.tools.monitoring_control_tool import MonitoringControlTool
from ai_whisperer.tools.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


def get_debbie_tools() -> List[AITool]:
    """Get all of Debbie's debugging tools"""
    return [
        SessionHealthTool(),
        SessionAnalysisTool(),
        MonitoringControlTool()
    ]


def register_debbie_tools() -> None:
    """Register Debbie's tools with the tool registry"""
    tool_registry = get_tool_registry()
    
    for tool in get_debbie_tools():
        logger.info(f"Registering Debbie tool: {tool.name}")
        tool_registry.register_tool(tool)


def unregister_debbie_tools() -> None:
    """Unregister Debbie's tools from the tool registry"""
    tool_registry = get_tool_registry()
    
    for tool in get_debbie_tools():
        logger.info(f"Unregistering Debbie tool: {tool.name}")
        tool_registry.unregister_tool(tool.name)