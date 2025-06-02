"""
Module: ai_whisperer/tools/session_health_tool.py
Purpose: AI tool implementation for session health

Session health monitoring tool for Debbie the Debugger.
Provides real-time health metrics for AI sessions.

Key Components:
- SessionHealthTool: Check the health status of AI sessions

Usage:
    tool = SessionHealthTool()
    result = await tool.execute(**parameters)

Dependencies:
- time

"""
from typing import Any, Dict
from datetime import timedelta

import time
from ai_whisperer.tools.base_tool import AITool

class SessionHealthTool(AITool):
    """Check the health status of AI sessions"""
    
    @property
    def name(self) -> str:
        return "session_health"
    
    @property
    def description(self) -> str:
        return "Check the health status of an AI session, including metrics like error rate, response time, and activity patterns"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID to check health for. Use 'current' for the current session."
                }
            },
            "required": ["session_id"],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool"""
        return """Use this tool to check the health status of AI sessions. It provides:
- Overall health score (0-100)
- Key metrics like error rate, response time, memory usage
- Detection of problematic patterns
- Recommendations for improving session health

Example: session_health(session_id="current") to check the current session."""
    
    async def execute(self, session_id: str) -> str:
        """Execute the session health check"""
        # In a real implementation, this would query actual session metrics
        # For now, we'll simulate realistic health data
        
        if session_id == "current":
            # Get current session from context (would be injected in real implementation)
            session_id = "current-session-id"
        
        # Simulate gathering health metrics
        metrics = self._gather_health_metrics(session_id)
        
        # Calculate health score
        health_score = self._calculate_health_score(metrics)
        
        # Format response
        response = self._format_health_report(session_id, health_score, metrics)
        
        return response
    
    def _gather_health_metrics(self, session_id: str) -> Dict[str, Any]:
        """Gather health metrics for a session"""
        # Simulated metrics - in real implementation would query actual data
        current_time = time.time()
        
        return {
            "session_id": session_id,
            "uptime_seconds": 1234,
            "message_count": 42,
            "error_count": 2,
            "warning_count": 5,
            "avg_response_time_ms": 1250,
            "last_activity": current_time - 30,  # 30 seconds ago
            "memory_usage_mb": 156.3,
            "active_tools": ["read_file", "list_directory", "search_files"],
            "patterns_detected": [
                {"type": "SLOW_RESPONSE", "count": 3, "last_occurrence": current_time - 120},
                {"type": "TOOL_RETRY", "count": 1, "last_occurrence": current_time - 300}
            ],
            "agent_switches": 2,
            "current_agent": "alice"
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> int:
        """Calculate overall health score (0-100)"""
        score = 100
        
        # Deduct for errors
        error_rate = metrics["error_count"] / max(metrics["message_count"], 1)
        if error_rate > 0.1:
            score -= 30
        elif error_rate > 0.05:
            score -= 15
        elif error_rate > 0:
            score -= 5
        
        # Deduct for slow responses
        if metrics["avg_response_time_ms"] > 5000:
            score -= 20
        elif metrics["avg_response_time_ms"] > 3000:
            score -= 10
        elif metrics["avg_response_time_ms"] > 2000:
            score -= 5
        
        # Deduct for detected patterns
        for pattern in metrics["patterns_detected"]:
            if pattern["type"] == "STALL":
                score -= 15
            elif pattern["type"] == "ERROR_CASCADE":
                score -= 20
            elif pattern["type"] in ["SLOW_RESPONSE", "TOOL_RETRY"]:
                score -= 5
        
        # Ensure score stays in valid range
        return max(0, min(100, score))
    
    def _format_health_report(self, session_id: str, health_score: int, metrics: Dict[str, Any]) -> str:
        """Format the health report as a readable string"""
        # Determine health status
        if health_score >= 90:
            status = "🟢 Healthy"
        elif health_score >= 70:
            status = "🟡 Fair"
        elif health_score >= 50:
            status = "🟠 Degraded"
        else:
            status = "🔴 Critical"
        
        # Format uptime
        uptime = timedelta(seconds=metrics["uptime_seconds"])
        uptime_str = f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m"
        
        # Build report
        report = f"""Session Health Report
====================
Session ID: {session_id}
Status: {status}
Health Score: {health_score}/100

Metrics:
--------
• Uptime: {uptime_str}
• Messages: {metrics['message_count']}
• Errors: {metrics['error_count']} ({metrics['error_count'] / max(metrics['message_count'], 1) * 100:.1f}%)
• Warnings: {metrics['warning_count']}
• Avg Response Time: {metrics['avg_response_time_ms']}ms
• Memory Usage: {metrics['memory_usage_mb']:.1f}MB
• Current Agent: {metrics['current_agent']}
• Agent Switches: {metrics['agent_switches']}

Active Tools:
------------
{', '.join(metrics['active_tools'])}

Detected Patterns:
-----------------"""
        
        if metrics["patterns_detected"]:
            for pattern in metrics["patterns_detected"]:
                time_ago = int(time.time() - pattern["last_occurrence"])
                report += f"\n• {pattern['type']}: {pattern['count']} occurrences (last: {time_ago}s ago)"
        else:
            report += "\n• None detected"
        
        # Add recommendations if health is degraded
        if health_score < 70:
            report += "\n\nRecommendations:\n---------------"
            if metrics["error_count"] > 5:
                report += "\n• High error rate detected. Check logs for root cause."
            if metrics["avg_response_time_ms"] > 3000:
                report += "\n• Slow response times. Consider checking system resources."
            if any(p["type"] == "STALL" for p in metrics["patterns_detected"]):
                report += "\n• Stall patterns detected. Agent may need manual intervention."
        
        return report
