"""
Module: ai_whisperer/tools/recommend_external_agent_tool.py
Purpose: AI tool implementation for recommend external agent

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- RecommendExternalAgentTool: Tool for recommending external agents based on task characteristics.

Usage:
    tool = RecommendExternalAgentTool()
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
from ..extensions.agents.decomposed_task import DecomposedTask

logger = logging.getLogger(__name__)


class RecommendExternalAgentTool(AITool):
    """Tool for recommending external agents based on task characteristics."""
    
    def __init__(self):
        super().__init__()
        self._registry = AdapterRegistry()
    
    @property
    def name(self) -> str:
        return "recommend_external_agent"
    
    @property
    def description(self) -> str:
        return "Recommend the best external AI agent for a specific task"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "JSON representation of the task to get recommendations for"
                },
                "only_available": {
                    "type": "boolean",
                    "description": "Only recommend agents that are currently available (default: true)"
                }
            },
            "required": ["task"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["external_agents", "recommendation", "analysis"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to recommend the best external AI agent for a specific task.
The tool analyzes task characteristics and matches them with agent strengths.

Parameters:
- task: JSON representation of the task to get recommendations for (required)
- only_available: Only recommend agents that are currently available (optional, default: true)

Returns:
A JSON object containing:
- task_summary: Overview of the task characteristics
- recommendations: Ranked list of agents with scores and reasons
- best_choice: The top recommendation with confidence level
"""
    
    def execute(self, arguments: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Execute the recommend external agent tool."""
        task_json = arguments.get("task")
        only_available = arguments.get("only_available", True)
        
        if not task_json:
            return {
                "error": "task parameter is required",
                "recommendations": [],
                "analyzed": False
            }
        
        try:
            # Parse the task
            if isinstance(task_json, str):
                task_data = json.loads(task_json)
            else:
                task_data = task_json
            
            # Convert to DecomposedTask object for scoring
            task = DecomposedTask(
                task_id=task_data.get("id", task_data.get("task_id", "unknown")),
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                parent_task_name=task_data.get("parent_task_name", ""),
                context=task_data.get("context", {}),
                acceptance_criteria=task_data.get("acceptance_criteria", []),
                estimated_complexity=task_data.get("complexity", task_data.get("estimated_complexity", "moderate")),
                status=task_data.get("status", "pending"),
                external_agent_prompts=task_data.get("external_agent_prompts", {})
            )
            
            # Get recommendations
            all_recommendations = self._registry.recommend_adapters(task)
            
            # Build detailed recommendations
            detailed_recommendations = []
            
            for agent_name, score in all_recommendations:
                adapter = self._registry.get_adapter(agent_name)
                is_valid, validation_msg = adapter.validate_environment()
                
                # Skip unavailable agents if requested
                if only_available and not is_valid:
                    continue
                
                recommendation = {
                    "agent": agent_name,
                    "score": round(score, 3),
                    "available": is_valid,
                    "validation_message": validation_msg,
                    "reasons": []
                }
                
                # Add specific reasons for the score
                task_name_lower = task.parent_task_name.lower()
                context = task.context
                
                if agent_name == "claude_code":
                    if score >= 0.8:
                        recommendation["reasons"].append("Excellent for TDD and test-driven development")
                    if len(context.get("files_to_modify", [])) <= 2:
                        recommendation["reasons"].append("Well-suited for focused, single-file tasks")
                    if "test" in task_name_lower:
                        recommendation["reasons"].append("Strong testing capabilities")
                
                elif agent_name == "roocode":
                    if len(context.get("files_to_modify", [])) > 2:
                        recommendation["reasons"].append("Excels at multi-file edits")
                    if "refactor" in task_name_lower:
                        recommendation["reasons"].append("Powerful refactoring capabilities")
                    if task.estimated_complexity in ["complex", "very_complex"]:
                        recommendation["reasons"].append("Handles complex tasks well")
                
                elif agent_name == "github_copilot":
                    if task.estimated_complexity in ["complex", "very_complex"]:
                        recommendation["reasons"].append("Agent mode great for iterative refinement")
                    if "optimize" in task_name_lower or "performance" in task_name_lower:
                        recommendation["reasons"].append("Good at optimization tasks")
                    if "iterate" in task.description.lower():
                        recommendation["reasons"].append("Excels at iterative development")
                
                # Add general suitability
                if score >= 0.8:
                    recommendation["suitability"] = "Highly Recommended"
                elif score >= 0.6:
                    recommendation["suitability"] = "Recommended"
                elif score >= 0.4:
                    recommendation["suitability"] = "Suitable"
                else:
                    recommendation["suitability"] = "Not Recommended"
                
                detailed_recommendations.append(recommendation)
            
            # Build response
            response = {
                "task_summary": {
                    "title": task.title,
                    "complexity": task.estimated_complexity,
                    "files_to_modify": len(task.context.get("files_to_modify", [])),
                    "status": task.status
                },
                "recommendations": detailed_recommendations
            }
            
            # Add overall recommendation
            if detailed_recommendations:
                best_agent = detailed_recommendations[0]
                response["best_choice"] = {
                    "agent": best_agent["agent"],
                    "confidence": "high" if best_agent["score"] >= 0.8 else "medium",
                    "primary_reason": best_agent["reasons"][0] if best_agent["reasons"] else "Good general fit"
                }
            else:
                response["best_choice"] = {
                    "agent": None,
                    "confidence": "none",
                    "primary_reason": "No available agents found"
                }
            
            response["analyzed"] = True
            return response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task JSON: {e}")
            return {
                "error": f"Invalid JSON format - {str(e)}",
                "recommendations": [],
                "analyzed": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in recommend_external_agent: {e}", exc_info=True)
            return {
                "error": f"Unexpected error - {str(e)}",
                "recommendations": [],
                "analyzed": False
            }