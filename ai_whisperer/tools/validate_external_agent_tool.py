"""
Module: ai_whisperer/tools/validate_external_agent_tool.py
Purpose: AI tool implementation for validate external agent

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- ValidateExternalAgentTool: Tool for validating external agent environments.

Usage:
    tool = ValidateExternalAgentTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool
- agents.external_adapters

Related:
- See UNTESTED_MODULES_REPORT.md

"""

import json
import logging
from typing import Dict, Any, List

from ai_whisperer.tools.base_tool import AITool
from ..extensions.agents.external_adapters import AdapterRegistry

logger = logging.getLogger(__name__)


class ValidateExternalAgentTool(AITool):
    """Tool for validating external agent environments."""
    
    def __init__(self):
        super().__init__()
        self._registry = AdapterRegistry()
    
    @property
    def name(self) -> str:
        return "validate_external_agent"
    
    @property
    def description(self) -> str:
        return "Validate that external AI agents are available and properly configured"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "agents": {
                    "type": "string",
                    "description": "Comma-separated list of agents to validate (or 'all' for all agents)"
                }
            },
            "required": []
        }
    
    @property
    def tags(self) -> List[str]:
        return ["external_agents", "validation", "environment"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to validate that external AI agents are available and properly configured.
The tool checks if the agents are installed and accessible in the current environment.

Parameters:
- agents: Comma-separated list of agents to validate, or 'all' for all agents (optional, default: 'all')

Returns:
A JSON object containing:
- summary: Overview of validation results
- validations: Detailed validation for each agent
- recommendation: Suggested actions based on results
- installation_links: Links to install missing agents (if any)
"""
    
    def execute(self, arguments: Dict[str, Any], **kwargs) -> str:
        """Execute the validate external agent tool."""
        agents_param = arguments.get("agents", "all")
        
        try:
            # Determine which agents to validate
            if agents_param.lower() == "all":
                agents_to_check = self._registry.list_adapters()
            else:
                agents_to_check = [a.strip().lower() for a in agents_param.split(",")]
            
            # Validate each agent
            validation_results = []
            summary = {
                "total_checked": 0,
                "available": 0,
                "unavailable": 0
            }
            
            for agent_name in agents_to_check:
                adapter = self._registry.get_adapter(agent_name)
                
                if not adapter:
                    validation_results.append({
                        "agent": agent_name,
                        "status": "unknown",
                        "valid": False,
                        "message": f"Unknown agent '{agent_name}'"
                    })
                    summary["unavailable"] += 1
                else:
                    is_valid, message = adapter.validate_environment()
                    validation_results.append({
                        "agent": agent_name,
                        "status": "available" if is_valid else "unavailable",
                        "valid": is_valid,
                        "message": message
                    })
                    
                    if is_valid:
                        summary["available"] += 1
                    else:
                        summary["unavailable"] += 1
                
                summary["total_checked"] += 1
            
            # Build response
            response = {
                "summary": summary,
                "validations": validation_results
            }
            
            # Add recommendations
            if summary["available"] == 0:
                response["recommendation"] = "No external agents are available. Please install at least one."
                response["installation_links"] = {
                    "claude_code": "https://claude.ai/code",
                    "roocode": "Install from VS Code marketplace",
                    "github_copilot": "https://github.com/features/copilot"
                }
            elif summary["available"] < summary["total_checked"]:
                available_agents = [v["agent"] for v in validation_results if v["valid"]]
                response["recommendation"] = f"Some agents unavailable. Available agents: {', '.join(available_agents)}"
            else:
                response["recommendation"] = "All checked agents are available and ready to use"
            
            return json.dumps(response, indent=2)
            
        except Exception as e:
            logger.error(f"Unexpected error in validate_external_agent: {e}", exc_info=True)
            return f"Error: Unexpected error - {str(e)}"