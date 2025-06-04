"""
Prompt Metrics Tool - Measure prompt effectiveness for each agent
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

from ai_whisperer.tools.base_tool import AITool
from pathlib import Path


class PromptMetricsTool(AITool):
    """Tool for collecting and analyzing prompt effectiveness metrics."""
    
    @property
    def name(self) -> str:
        return "prompt_metrics"
    
    @property
    def description(self) -> str:
        return "Analyze agent responses to measure prompt compliance and effectiveness"
    
    @property
    def category(self) -> str:
        return "analysis"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'analyze_response', 'log_tool_usage', 'get_summary', 'compare_versions', 'get_tool_metrics'",
                    "enum": ["analyze_response", "log_tool_usage", "get_summary", "compare_versions", "get_tool_metrics"]
                },
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID (A, P, T, D, E)"
                },
                "response": {
                    "type": "string",
                    "description": "Agent response to analyze"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for tracking"
                },
                "prompt_version": {
                    "type": "string",
                    "description": "Prompt version identifier (e.g., 'current', 'revised')"
                },
                "tool_name": {
                    "type": "string",
                    "description": "Name of the tool being logged"
                },
                "tool_success": {
                    "type": "boolean",
                    "description": "Whether the tool execution succeeded"
                },
                "error_message": {
                    "type": "string",
                    "description": "Error message if tool failed"
                },
                "execution_time_ms": {
                    "type": "integer",
                    "description": "Tool execution time in milliseconds"
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }
    
    def __init__(self):
        super().__init__()
        # Use current working directory for metrics storage
        self.metrics_dir = Path.cwd() / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        self.metrics_file = self.metrics_dir / "prompt_metrics.json"
        self.tool_metrics_file = self.metrics_dir / "tool_metrics.json"
        self._load_metrics()
        self._load_tool_metrics()
    
    def get_ai_prompt_instructions(self) -> str:
        """Provide instructions for AI on how to use this tool."""
        return """Use the prompt_metrics tool to analyze agent responses and track tool usage:
        
        Actions:
        - analyze_response: Analyze an agent's response for channel compliance, conciseness, and autonomy
        - log_tool_usage: Record when a tool is used by an agent
        - get_summary: Get aggregated metrics for an agent or all agents
        - compare_versions: Compare metrics between prompt versions (current vs revised)
        - get_tool_metrics: Get tool usage statistics
        
        Example usage:
        prompt_metrics(action="analyze_response", agent_id="A", response="[FINAL]Hello[/FINAL]", session_id="test123", prompt_version="revised")
        """
    
    def _load_metrics(self):
        """Load existing metrics from file."""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                self.metrics = json.load(f)
        else:
            self.metrics = defaultdict(lambda: defaultdict(list))
    
    def _save_metrics(self):
        """Save metrics to file."""
        # Convert defaultdict to regular dict for JSON serialization
        metrics_dict = {k: dict(v) for k, v in self.metrics.items()}
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
    
    def _load_tool_metrics(self):
        """Load existing tool metrics from file."""
        if self.tool_metrics_file.exists():
            with open(self.tool_metrics_file, 'r') as f:
                self.tool_metrics = json.load(f)
        else:
            self.tool_metrics = defaultdict(lambda: defaultdict(lambda: {
                "total_uses": 0,
                "successes": 0,
                "failures": 0,
                "errors": [],
                "avg_execution_time": 0,
                "execution_times": []
            }))
    
    def _save_tool_metrics(self):
        """Save tool metrics to file."""
        # Convert nested defaultdicts to regular dicts
        tool_dict = {}
        for agent, tools in self.tool_metrics.items():
            tool_dict[agent] = {}
            for tool, data in tools.items():
                tool_dict[agent][tool] = dict(data)
        with open(self.tool_metrics_file, 'w') as f:
            json.dump(tool_dict, f, indent=2)
    
    def _analyze_channel_compliance(self, response: str) -> Dict:
        """Analyze if response uses proper channel structure."""
        return {
            "has_analysis": bool(re.search(r'\[ANALYSIS\].*?\[/ANALYSIS\]', response, re.DOTALL)),
            "has_commentary": bool(re.search(r'\[COMMENTARY\].*?\[/COMMENTARY\]', response, re.DOTALL)),
            "has_final": bool(re.search(r'\[FINAL\].*?\[/FINAL\]', response, re.DOTALL)),
            "channel_count": len(re.findall(r'\[(ANALYSIS|COMMENTARY|FINAL)\]', response))
        }
    
    def _analyze_conciseness(self, response: str) -> Dict:
        """Analyze response conciseness."""
        # Extract FINAL section content
        final_match = re.search(r'\[FINAL\](.*?)\[/FINAL\]', response, re.DOTALL)
        final_content = final_match.group(1).strip() if final_match else response
        
        # Count metrics
        word_count = len(final_content.split())
        line_count = len(final_content.strip().split('\n'))
        
        # Check for forbidden patterns
        has_preamble = bool(re.match(r'^(Great|Certainly|Okay|Sure|I\'ll help)', final_content))
        has_explanation = bool(re.search(r'(Let me|I will|I\'m going to)', final_content))
        
        return {
            "word_count": word_count,
            "line_count": line_count,
            "has_preamble": has_preamble,
            "has_explanation": has_explanation,
            "conciseness_score": max(0, 100 - (word_count - 20) * 2)  # Penalty for words over 20
        }
    
    def _analyze_autonomy(self, response: str) -> Dict:
        """Analyze autonomous behavior indicators."""
        # Look for permission-seeking patterns
        permission_patterns = [
            r'(Should I|Would you like me to|Do you want)',
            r'(May I|Can I|Is it okay)',
            r'(confirm|permission|proceed\?)'
        ]
        
        permission_count = sum(
            len(re.findall(pattern, response, re.IGNORECASE)) 
            for pattern in permission_patterns
        )
        
        # Look for tool usage
        tool_matches = re.findall(r'Tool: (\w+)', response)
        
        # Check for task completion markers
        has_completion = bool(re.search(r'(Task complete|Completed|Done)', response, re.IGNORECASE))
        
        return {
            "permission_seeking_count": permission_count,
            "tools_used": len(tool_matches),
            "unique_tools": len(set(tool_matches)),
            "declares_completion": has_completion,
            "autonomy_score": max(0, 100 - permission_count * 20)
        }
    
    def _analyze_response(self, agent_id: str, response: str, session_id: str, version: str) -> Dict:
        """Perform complete analysis of a response."""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "session_id": session_id,
            "version": version,
            "channel_compliance": self._analyze_channel_compliance(response),
            "conciseness": self._analyze_conciseness(response),
            "autonomy": self._analyze_autonomy(response),
            "response_length": len(response)
        }
        
        # Calculate overall score
        scores = []
        if analysis["channel_compliance"]["has_final"]:
            scores.append(analysis["channel_compliance"]["channel_count"] * 25)
        scores.append(analysis["conciseness"]["conciseness_score"])
        scores.append(analysis["autonomy"]["autonomy_score"])
        
        analysis["overall_score"] = sum(scores) / len(scores) if scores else 0
        
        return analysis
    
    def _get_summary(self, agent_id: Optional[str] = None) -> Dict:
        """Get summary statistics for an agent or all agents."""
        summary = {}
        
        agents = [agent_id] if agent_id else self.metrics.keys()
        
        for aid in agents:
            if aid not in self.metrics:
                continue
                
            agent_metrics = []
            for version_data in self.metrics[aid].values():
                agent_metrics.extend(version_data)
            
            if not agent_metrics:
                continue
            
            # Calculate averages
            summary[aid] = {
                "total_responses": len(agent_metrics),
                "avg_overall_score": sum(m["overall_score"] for m in agent_metrics) / len(agent_metrics),
                "avg_conciseness_score": sum(m["conciseness"]["conciseness_score"] for m in agent_metrics) / len(agent_metrics),
                "avg_autonomy_score": sum(m["autonomy"]["autonomy_score"] for m in agent_metrics) / len(agent_metrics),
                "channel_compliance_rate": sum(1 for m in agent_metrics if all([
                    m["channel_compliance"]["has_analysis"],
                    m["channel_compliance"]["has_commentary"], 
                    m["channel_compliance"]["has_final"]
                ])) / len(agent_metrics) * 100,
                "avg_word_count": sum(m["conciseness"]["word_count"] for m in agent_metrics) / len(agent_metrics),
                "permission_seeking_rate": sum(m["autonomy"]["permission_seeking_count"] > 0 for m in agent_metrics) / len(agent_metrics) * 100
            }
        
        return summary
    
    def _compare_versions(self, agent_id: str) -> Dict:
        """Compare metrics between different prompt versions."""
        if agent_id not in self.metrics:
            return {"error": f"No metrics found for agent {agent_id}"}
        
        comparison = {}
        for version, data in self.metrics[agent_id].items():
            if not data:
                continue
                
            comparison[version] = {
                "sample_size": len(data),
                "avg_overall_score": sum(m["overall_score"] for m in data) / len(data),
                "avg_conciseness": sum(m["conciseness"]["word_count"] for m in data) / len(data),
                "channel_compliance": sum(1 for m in data if m["channel_compliance"]["has_final"]) / len(data) * 100,
                "autonomy_score": sum(m["autonomy"]["autonomy_score"] for m in data) / len(data)
            }
        
        # Calculate improvements
        if "current" in comparison and "revised" in comparison:
            improvements = {
                "overall_score_change": comparison["revised"]["avg_overall_score"] - comparison["current"]["avg_overall_score"],
                "conciseness_improvement": comparison["current"]["avg_conciseness"] - comparison["revised"]["avg_conciseness"],
                "compliance_improvement": comparison["revised"]["channel_compliance"] - comparison["current"]["channel_compliance"],
                "autonomy_improvement": comparison["revised"]["autonomy_score"] - comparison["current"]["autonomy_score"]
            }
            comparison["improvements"] = improvements
        
        return comparison
    
    def _log_tool_usage(self, agent_id: str, tool_name: str, success: bool, 
                       error_message: Optional[str] = None, 
                       execution_time: Optional[int] = None) -> Dict:
        """Log a tool usage event."""
        if agent_id not in self.tool_metrics:
            self.tool_metrics[agent_id] = defaultdict(lambda: {
                "total_uses": 0,
                "successes": 0,
                "failures": 0,
                "errors": [],
                "avg_execution_time": 0,
                "execution_times": []
            })
        
        tool_data = self.tool_metrics[agent_id][tool_name]
        tool_data["total_uses"] += 1
        
        if success:
            tool_data["successes"] += 1
        else:
            tool_data["failures"] += 1
            if error_message:
                # Keep last 10 errors
                tool_data["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "message": error_message
                })
                tool_data["errors"] = tool_data["errors"][-10:]
        
        if execution_time is not None:
            tool_data["execution_times"].append(execution_time)
            # Keep last 100 execution times
            tool_data["execution_times"] = tool_data["execution_times"][-100:]
            tool_data["avg_execution_time"] = sum(tool_data["execution_times"]) / len(tool_data["execution_times"])
        
        # Calculate success rate
        tool_data["success_rate"] = (tool_data["successes"] / tool_data["total_uses"] * 100) if tool_data["total_uses"] > 0 else 0
        
        self._save_tool_metrics()
        
        return {
            "agent_id": agent_id,
            "tool_name": tool_name,
            "total_uses": tool_data["total_uses"],
            "success_rate": tool_data["success_rate"],
            "avg_execution_time": tool_data["avg_execution_time"]
        }
    
    def _get_tool_metrics(self, agent_id: Optional[str] = None) -> Dict:
        """Get tool usage metrics for an agent or all agents."""
        result = {}
        
        agents = [agent_id] if agent_id else list(self.tool_metrics.keys())
        
        for aid in agents:
            if aid not in self.tool_metrics:
                continue
            
            agent_tools = self.tool_metrics[aid]
            tool_summary = {}
            
            for tool_name, data in agent_tools.items():
                tool_summary[tool_name] = {
                    "total_uses": data["total_uses"],
                    "success_rate": data.get("success_rate", 0),
                    "failure_rate": (data["failures"] / data["total_uses"] * 100) if data["total_uses"] > 0 else 0,
                    "avg_execution_time_ms": data.get("avg_execution_time", 0),
                    "recent_errors": data.get("errors", [])[-3:]  # Last 3 errors
                }
            
            # Calculate agent-level statistics
            total_tools = len(agent_tools)
            total_uses = sum(t["total_uses"] for t in agent_tools.values())
            total_failures = sum(t["failures"] for t in agent_tools.values())
            
            result[aid] = {
                "tools_used": total_tools,
                "total_tool_calls": total_uses,
                "overall_success_rate": ((total_uses - total_failures) / total_uses * 100) if total_uses > 0 else 0,
                "most_used_tools": sorted(
                    [(name, data["total_uses"]) for name, data in agent_tools.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "most_error_prone": sorted(
                    [(name, data["failures"]) for name, data in agent_tools.items() if data["failures"] > 0],
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "tool_details": tool_summary
            }
        
        return result
    
    def execute(self, **kwargs) -> Dict:
        """Execute the prompt metrics tool."""
        action = kwargs.get("action")
        
        if action == "analyze_response":
            agent_id = kwargs.get("agent_id")
            response = kwargs.get("response")
            session_id = kwargs.get("session_id", "unknown")
            version = kwargs.get("prompt_version", "current")
            
            if not agent_id or not response:
                return {
                    "success": False,
                    "error": "Missing required parameters: agent_id and response"
                }
            
            # Perform analysis
            analysis = self._analyze_response(agent_id, response, session_id, version)
            
            # Store metrics
            if agent_id not in self.metrics:
                self.metrics[agent_id] = defaultdict(list)
            self.metrics[agent_id][version].append(analysis)
            self._save_metrics()
            
            return {
                "success": True,
                "data": analysis,
                "metadata": {
                    "agent_id": agent_id,
                    "version": version,
                    "overall_score": analysis["overall_score"]
                }
            }
        
        elif action == "get_summary":
            agent_id = kwargs.get("agent_id")
            summary = self._get_summary(agent_id)
            
            return {
                "success": True,
                "data": summary,
                "metadata": {"agents_analyzed": list(summary.keys())}
            }
        
        elif action == "compare_versions":
            agent_id = kwargs.get("agent_id")
            if not agent_id:
                return {
                    "success": False,
                    "error": "Missing required parameter: agent_id"
                }
            
            comparison = self._compare_versions(agent_id)
            
            return {
                "success": True,
                "data": comparison,
                "metadata": {"agent_id": agent_id}
            }
        
        elif action == "log_tool_usage":
            agent_id = kwargs.get("agent_id")
            tool_name = kwargs.get("tool_name")
            tool_success = kwargs.get("tool_success", True)
            error_message = kwargs.get("error_message")
            execution_time_ms = kwargs.get("execution_time_ms")
            
            if not agent_id or not tool_name:
                return {
                    "success": False,
                    "error": "Missing required parameters: agent_id and tool_name"
                }
            
            log_result = self._log_tool_usage(
                agent_id, tool_name, tool_success, 
                error_message, execution_time_ms
            )
            
            return {
                "success": True,
                "data": log_result,
                "metadata": {
                    "agent_id": agent_id,
                    "tool_name": tool_name,
                    "logged": True
                }
            }
        
        elif action == "get_tool_metrics":
            agent_id = kwargs.get("agent_id")
            metrics = self._get_tool_metrics(agent_id)
            
            return {
                "success": True,
                "data": metrics,
                "metadata": {
                    "agents_analyzed": list(metrics.keys()),
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}"
            }


# Usage example:
"""
# Analyze a response
prompt_metrics(
    action="analyze_response",
    agent_id="A",
    response="[ANALYSIS]Need to check file[/ANALYSIS][COMMENTARY]Tool: read_file...[/COMMENTARY][FINAL]File contains configuration.[/FINAL]",
    session_id="session123",
    prompt_version="revised"
)

# Log tool usage
prompt_metrics(
    action="log_tool_usage",
    agent_id="P",
    tool_name="create_rfc",
    tool_success=True,
    execution_time_ms=150
)

# Log tool failure
prompt_metrics(
    action="log_tool_usage",
    agent_id="A",
    tool_name="read_file",
    tool_success=False,
    error_message="File not found: config.yaml",
    execution_time_ms=25
)

# Get tool metrics
prompt_metrics(
    action="get_tool_metrics",
    agent_id="P"  # Or omit for all agents
)

# Get summary
prompt_metrics(
    action="get_summary",
    agent_id="A"
)

# Compare versions
prompt_metrics(
    action="compare_versions",
    agent_id="A"
)
"""