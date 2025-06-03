"""
Module: ai_whisperer/tools/analyze_dependencies_tool.py
Purpose: AI tool implementation for analyze dependencies

This module implements an AI-usable tool that extends the AITool
base class. It provides structured input/output handling and
integrates with the OpenRouter API for AI model interactions.

Key Components:
- AnalyzeDependenciesTool: Tool for analyzing and resolving task dependencies.

Usage:
    tool = AnalyzeDependenciesTool()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- base_tool
- agents.agent_e_exceptions

Related:
- See UNTESTED_MODULES_REPORT.md

"""

from typing import Any, Dict, List

import json
import logging
from ai_whisperer.tools.base_tool import AITool
from ..extensions.agents.task_decomposer import TaskDecomposer
from ..extensions.agents.agent_e_exceptions import DependencyCycleError

logger = logging.getLogger(__name__)

class AnalyzeDependenciesTool(AITool):
    """Tool for analyzing and resolving task dependencies."""
    
    def __init__(self):
        super().__init__()
        self._decomposer = TaskDecomposer()
    
    @property
    def name(self) -> str:
        return "analyze_dependencies"
    
    @property
    def description(self) -> str:
        return "Analyze task dependencies and create an optimal execution order"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "string",
                    "description": "JSON array of tasks with id and dependencies fields"
                }
            },
            "required": ["tasks"]
        }
    
    @property
    def tags(self) -> List[str]:
        return ["planning", "task_management", "analysis", "dependencies"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
Use this tool to analyze task dependencies and create an optimal execution order.
The tool performs topological sorting to determine which tasks can run in parallel
and which must wait for dependencies.

Parameters:
- tasks: JSON array of tasks with 'id' and 'dependencies' fields (required)

Returns:
A JSON object containing:
- total_tasks: Number of tasks analyzed
- execution_phases: Number of sequential phases needed
- max_parallel_tasks: Maximum tasks that can run in parallel
- execution_order: Ordered list of task IDs
- phases: Detailed breakdown of tasks by phase
- recommendations: Suggestions for optimization
"""
    
    def execute(self, arguments: Dict[str, Any], **kwargs) -> str:
        """Execute the analyze dependencies tool."""
        tasks_json = arguments.get("tasks")
        
        if not tasks_json:
            return "Error: tasks parameter is required"
        
        try:
            # Parse the tasks
            if isinstance(tasks_json, str):
                tasks_data = json.loads(tasks_json)
            else:
                tasks_data = tasks_json
            
            # Build dependency graph
            dependency_graph = {}
            task_map = {}
            
            for task in tasks_data:
                task_id = task.get("id", task.get("task_id"))
                dependencies = task.get("dependencies", [])
                
                if not task_id:
                    return "Error: Each task must have an 'id' or 'task_id' field"
                
                dependency_graph[task_id] = dependencies
                task_map[task_id] = task
            
            # Resolve dependencies using topological sort
            try:
                execution_order = self._decomposer._topological_sort(dependency_graph)
            except DependencyCycleError as e:
                return f"Error: Circular dependency detected - {str(e)}"
            
            # Build execution phases
            phases = []
            phase_map = {}
            
            # Group tasks by their dependency depth
            for task_id in execution_order:
                # Find the maximum phase of dependencies
                max_dep_phase = -1
                for dep_id in dependency_graph.get(task_id, []):
                    if dep_id in phase_map:
                        max_dep_phase = max(max_dep_phase, phase_map[dep_id])
                
                # This task goes in the next phase
                task_phase = max_dep_phase + 1
                phase_map[task_id] = task_phase
                
                # Ensure we have enough phases
                while len(phases) <= task_phase:
                    phases.append([])
                
                phases[task_phase].append({
                    "id": task_id,
                    "title": task_map[task_id].get("title", ""),
                    "dependencies": dependency_graph[task_id]
                })
            
            # Analyze dependency patterns
            analysis = {
                "total_tasks": len(tasks_data),
                "execution_phases": len(phases),
                "max_parallel_tasks": max(len(phase) for phase in phases) if phases else 0,
                "has_circular_dependencies": False,
                "execution_order": execution_order,
                "phases": []
            }
            
            # Format phases for output
            for i, phase_tasks in enumerate(phases):
                phase_info = {
                    "phase": i + 1,
                    "task_count": len(phase_tasks),
                    "can_run_parallel": True,
                    "tasks": phase_tasks
                }
                analysis["phases"].append(phase_info)
            
            # Add recommendations
            recommendations = []
            if analysis["max_parallel_tasks"] > 5:
                recommendations.append("Consider breaking down complex tasks to reduce parallel execution burden")
            if analysis["execution_phases"] > 10:
                recommendations.append("Deep dependency chain detected - consider consolidating related tasks")
            if any(len(task.get("dependencies", [])) > 3 for task in tasks_data):
                recommendations.append("Some tasks have many dependencies - ensure they're all necessary")
            
            analysis["recommendations"] = recommendations
            
            return json.dumps(analysis, indent=2)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tasks JSON: {e}")
            return f"Error: Invalid JSON format - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in analyze_dependencies: {e}", exc_info=True)
            return f"Error: Unexpected error - {str(e)}"
