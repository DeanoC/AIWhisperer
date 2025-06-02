"""
Module: ai_whisperer/tools/session_analysis_tool.py
Purpose: AI tool implementation for session analysis

Session analysis tool for Debbie the Debugger.
Provides deep analysis of session patterns and performance.

Key Components:
- SessionAnalysisTool: Analyze session patterns and performance

Usage:
    tool = SessionAnalysisTool()
    result = await tool.execute(**parameters)

Dependencies:
- time
- collections

"""
from datetime import datetime
from typing import Any, Dict, List

import time
from collections import defaultdict

from ai_whisperer.tools.base_tool import AITool

class SessionAnalysisTool(AITool):
    """Analyze session patterns and performance"""
    
    @property
    def name(self) -> str:
        return "session_analysis"
    
    @property
    def description(self) -> str:
        return "Analyze session patterns, errors, and performance over a specified time range"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID to analyze. Use 'current' for current session."
                },
                "time_range_minutes": {
                    "type": "number",
                    "description": "Time range to analyze in minutes (default: 30)"
                },
                "focus_area": {
                    "type": "string",
                    "enum": ["errors", "performance", "patterns", "all"],
                    "description": "Specific area to focus the analysis on"
                }
            },
            "required": ["session_id"],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool"""
        return """Use this tool to perform deep analysis of session patterns and performance. It analyzes:
- Error patterns and clusters
- Performance metrics (response times, percentiles)
- Behavioral patterns (rapid messages, tool retries, agent switching)
- Generates actionable recommendations

Example: session_analysis(session_id="current", time_range_minutes=60, focus_area="errors")"""
    
    async def execute(
        self, 
        session_id: str, 
        time_range_minutes: int = 30,
        focus_area: str = "all"
    ) -> str:
        """Execute the session analysis"""
        if session_id == "current":
            session_id = "current-session-id"
        
        # Simulate gathering session data
        session_data = self._gather_session_data(session_id, time_range_minutes)
        
        # Perform analysis based on focus area
        analysis = {}
        if focus_area in ["errors", "all"]:
            analysis["errors"] = self._analyze_errors(session_data)
        if focus_area in ["performance", "all"]:
            analysis["performance"] = self._analyze_performance(session_data)
        if focus_area in ["patterns", "all"]:
            analysis["patterns"] = self._analyze_patterns(session_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)
        
        # Format report
        report = self._format_analysis_report(
            session_id, time_range_minutes, focus_area, analysis, recommendations
        )
        
        return report
    
    def _gather_session_data(self, session_id: str, time_range_minutes: int) -> Dict[str, Any]:
        """Gather session data for analysis"""
        # Simulated data - in real implementation would query actual logs
        current_time = time.time()
        start_time = current_time - (time_range_minutes * 60)
        
        # Simulate message history
        messages = []
        for i in range(25):
            timestamp = start_time + (i * 72)  # ~72 seconds apart
            messages.append({
                "timestamp": timestamp,
                "type": "user" if i % 3 == 0 else "assistant",
                "duration_ms": 1200 + (i * 50),
                "tool_calls": ["read_file"] if i % 5 == 0 else [],
                "error": "FileNotFoundError" if i == 10 else None,
                "agent": "alice" if i < 15 else "patricia"
            })
        
        return {
            "session_id": session_id,
            "start_time": start_time,
            "end_time": current_time,
            "messages": messages,
            "total_messages": len(messages),
            "agent_sessions": {
                "alice": {"messages": 15, "errors": 1, "avg_response_ms": 1400},
                "patricia": {"messages": 10, "errors": 0, "avg_response_ms": 1800}
            }
        }
    
    def _analyze_errors(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze error patterns"""
        errors = defaultdict(list)
        error_timeline = []
        
        for msg in session_data["messages"]:
            if msg["error"]:
                errors[msg["error"]].append(msg["timestamp"])
                error_timeline.append({
                    "time": msg["timestamp"],
                    "error": msg["error"],
                    "agent": msg["agent"]
                })
        
        # Cluster errors by frequency
        error_clusters = {}
        for error_type, occurrences in errors.items():
            error_clusters[error_type] = {
                "count": len(occurrences),
                "first_occurrence": min(occurrences) if occurrences else None,
                "last_occurrence": max(occurrences) if occurrences else None,
                "frequency": len(occurrences) / (session_data["total_messages"] or 1)
            }
        
        return {
            "total_errors": sum(len(v) for v in errors.values()),
            "unique_errors": len(errors),
            "error_clusters": error_clusters,
            "error_timeline": error_timeline,
            "error_rate": sum(len(v) for v in errors.values()) / (session_data["total_messages"] or 1)
        }
    
    def _analyze_performance(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        response_times = [msg["duration_ms"] for msg in session_data["messages"]]
        
        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        # Identify slow operations
        slow_operations = []
        for msg in session_data["messages"]:
            if msg["duration_ms"] > 3000:
                slow_operations.append({
                    "timestamp": msg["timestamp"],
                    "duration_ms": msg["duration_ms"],
                    "tool_calls": msg["tool_calls"],
                    "agent": msg["agent"]
                })
        
        return {
            "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time_ms": min(response_times) if response_times else 0,
            "max_response_time_ms": max(response_times) if response_times else 0,
            "p50_response_time_ms": p50,
            "p95_response_time_ms": p95,
            "p99_response_time_ms": p99,
            "slow_operations": slow_operations,
            "slow_operation_count": len(slow_operations),
            "performance_trend": "degrading" if p99 > p50 * 2 else "stable"
        }
    
    def _analyze_patterns(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze behavioral patterns"""
        patterns = []
        
        # Detect rapid message patterns
        rapid_messages = []
        for i in range(1, len(session_data["messages"])):
            time_diff = session_data["messages"][i]["timestamp"] - session_data["messages"][i-1]["timestamp"]
            if time_diff < 10 and session_data["messages"][i]["type"] == "user":
                rapid_messages.append(session_data["messages"][i]["timestamp"])
        
        if len(rapid_messages) >= 3:
            patterns.append({
                "type": "RAPID_USER_MESSAGES",
                "severity": "medium",
                "count": len(rapid_messages),
                "description": "User sending messages rapidly, possible frustration"
            })
        
        # Detect tool retry patterns
        tool_retries = defaultdict(int)
        last_tool = None
        for msg in session_data["messages"]:
            if msg["tool_calls"]:
                for tool in msg["tool_calls"]:
                    if tool == last_tool:
                        tool_retries[tool] += 1
                    last_tool = tool
        
        for tool, retry_count in tool_retries.items():
            if retry_count >= 2:
                patterns.append({
                    "type": "TOOL_RETRY_PATTERN",
                    "severity": "low",
                    "tool": tool,
                    "count": retry_count,
                    "description": f"Tool '{tool}' being retried multiple times"
                })
        
        # Detect agent switching patterns
        agent_switches = 0
        last_agent = None
        for msg in session_data["messages"]:
            if msg["agent"] != last_agent and last_agent is not None:
                agent_switches += 1
            last_agent = msg["agent"]
        
        if agent_switches > 3:
            patterns.append({
                "type": "FREQUENT_AGENT_SWITCHING",
                "severity": "medium",
                "count": agent_switches,
                "description": "Frequent agent switching may indicate task complexity"
            })
        
        return {
            "detected_patterns": patterns,
            "pattern_count": len(patterns),
            "severity_distribution": {
                "high": sum(1 for p in patterns if p.get("severity") == "high"),
                "medium": sum(1 for p in patterns if p.get("severity") == "medium"),
                "low": sum(1 for p in patterns if p.get("severity") == "low")
            }
        }
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Error-based recommendations
        if "errors" in analysis:
            if analysis["errors"]["error_rate"] > 0.1:
                recommendations.append("High error rate detected. Review error logs and add error handling.")
            
            for error_type, data in analysis["errors"]["error_clusters"].items():
                if data["count"] > 2:
                    recommendations.append(f"Recurring {error_type}. Implement specific handling for this error.")
        
        # Performance-based recommendations
        if "performance" in analysis:
            if analysis["performance"]["avg_response_time_ms"] > 3000:
                recommendations.append("Average response time is high. Consider optimizing tool operations.")
            
            if analysis["performance"]["slow_operation_count"] > 5:
                recommendations.append("Multiple slow operations detected. Profile and optimize bottlenecks.")
        
        # Pattern-based recommendations
        if "patterns" in analysis:
            for pattern in analysis["patterns"]["detected_patterns"]:
                if pattern["type"] == "RAPID_USER_MESSAGES":
                    recommendations.append("User frustration detected. Consider clearer prompts or guidance.")
                elif pattern["type"] == "TOOL_RETRY_PATTERN":
                    recommendations.append(f"Tool '{pattern['tool']}' failing repeatedly. Check tool configuration.")
                elif pattern["type"] == "FREQUENT_AGENT_SWITCHING":
                    recommendations.append("Consider using a single agent for related tasks to reduce context switching.")
        
        return recommendations
    
    def _format_analysis_report(
        self,
        session_id: str,
        time_range_minutes: int,
        focus_area: str,
        analysis: Dict[str, Any],
        recommendations: List[str]
    ) -> str:
        """Format the analysis report"""
        report = f"""Session Analysis Report
======================
Session ID: {session_id}
Time Range: Last {time_range_minutes} minutes
Focus Area: {focus_area.upper()}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
        
        # Error Analysis
        if "errors" in analysis:
            report += """Error Analysis
--------------
"""
            errors = analysis["errors"]
            report += f"• Total Errors: {errors['total_errors']}\n"
            report += f"• Unique Error Types: {errors['unique_errors']}\n"
            report += f"• Error Rate: {errors['error_rate']*100:.1f}%\n"
            
            if errors["error_clusters"]:
                report += "\nError Clusters:\n"
                for error_type, data in errors["error_clusters"].items():
                    report += f"  - {error_type}: {data['count']} occurrences ({data['frequency']*100:.1f}%)\n"
            
            report += "\n"
        
        # Performance Analysis
        if "performance" in analysis:
            report += """Performance Analysis
-------------------
"""
            perf = analysis["performance"]
            report += f"• Average Response Time: {perf['avg_response_time_ms']:.0f}ms\n"
            report += f"• P50 Response Time: {perf['p50_response_time_ms']:.0f}ms\n"
            report += f"• P95 Response Time: {perf['p95_response_time_ms']:.0f}ms\n"
            report += f"• P99 Response Time: {perf['p99_response_time_ms']:.0f}ms\n"
            report += f"• Performance Trend: {perf['performance_trend'].upper()}\n"
            
            if perf["slow_operations"]:
                report += f"\nSlow Operations ({perf['slow_operation_count']} found):\n"
                for op in perf["slow_operations"][:3]:  # Show top 3
                    report += f"  - {op['duration_ms']}ms"
                    if op['tool_calls']:
                        report += f" ({', '.join(op['tool_calls'])})"
                    report += "\n"
            
            report += "\n"
        
        # Pattern Analysis
        if "patterns" in analysis:
            report += """Pattern Analysis
---------------
"""
            patterns = analysis["patterns"]
            report += f"• Patterns Detected: {patterns['pattern_count']}\n"
            
            if patterns["detected_patterns"]:
                report += "\nDetected Patterns:\n"
                for pattern in patterns["detected_patterns"]:
                    report += f"  - {pattern['type']} ({pattern['severity']}): {pattern['description']}\n"
            else:
                report += "• No significant patterns detected\n"
            
            report += "\n"
        
        # Recommendations
        if recommendations:
            report += """Recommendations
--------------
"""
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
        else:
            report += """Recommendations
--------------
No specific recommendations at this time. Session appears healthy.
"""
        
        return report
