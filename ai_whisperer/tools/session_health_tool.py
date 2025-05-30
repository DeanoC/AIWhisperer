"""
Session Health Tool - Allows Debbie to check session health status
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

from .base_tool import AITool
from interactive_server.debbie_observer import get_observer


class SessionHealthTool(AITool):
    """
    Tool for checking session health and monitoring status.
    This tool is primarily for Debbie to analyze session health.
    """
    
    def __init__(self):
        """Initialize the session health tool"""
        super().__init__()
        self._name = "session_health"
        self._description = "Check health status of current or specified session"
        self.observer = get_observer()
    
    @property
    def name(self) -> str:
        """Tool identifier"""
        return self._name
    
    @property
    def description(self) -> str:
        """Tool description"""
        return self._description
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """JSON schema for tool parameters"""
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to check (optional, defaults to current session)"
                },
                "detailed": {
                    "type": "boolean",
                    "description": "Include detailed metrics",
                    "default": False
                }
            },
            "required": []
        }
    
    @property
    def category(self) -> str:
        """Tool category"""
        return "Monitoring"
    
    @property
    def tags(self) -> list:
        """Tool tags"""
        return ["monitoring", "debugging", "session", "health"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on how to use this tool"""
        return """
Use this tool to check the health status of interactive sessions.
The tool provides:
- Overall health score (0-100)
- Message count and error rate
- Average response time
- Recent detected patterns
- Session uptime

Parameters:
- session_id: Optional session ID (defaults to current session)
- detailed: Whether to include detailed metrics

Example usage:
{
    "session_id": "current",
    "detailed": true
}

The health score is calculated based on:
- Error rate (high errors reduce score)
- Response time (slow responses reduce score)
- Detected patterns (issues reduce score)

Patterns that may be detected:
- STALL: Agent not responding (>30s)
- RAPID_RETRY: User retrying same command
- ERROR_CASCADE: Multiple errors in succession
- FRUSTRATION: Rapid message sending
- PERMISSION_ISSUE: Permission-related errors
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the health check"""
        session_id = kwargs.get('session_id', 'current')
        detailed = kwargs.get('detailed', False)
        
        # Get current session ID from context if not specified
        if session_id == 'current':
            # This would normally come from the agent context
            # For now, we'll return all sessions if current is requested
            all_health = self.observer.get_all_sessions_health()
            if not all_health:
                return {
                    'success': False,
                    'error': 'No active sessions found'
                }
            
            # Return health for all active sessions
            result = {
                'success': True,
                'active_sessions': len(all_health),
                'sessions': []
            }
            
            for sid, health in all_health.items():
                session_data = self._format_health_data(health, detailed)
                result['sessions'].append(session_data)
            
            return result
        
        # Get health for specific session
        health = self.observer.get_session_health(session_id)
        if not health:
            return {
                'success': False,
                'error': f'Session {session_id} not found or not being monitored'
            }
        
        return {
            'success': True,
            **self._format_health_data(health, detailed)
        }
    
    def _format_health_data(self, health: Dict[str, Any], detailed: bool) -> Dict[str, Any]:
        """Format health data for output"""
        # Basic health info
        data = {
            'session_id': health['session_id'],
            'health_score': round(health['health_score'], 1),
            'status': self._get_status_from_score(health['health_score']),
            'uptime_seconds': round(health['uptime'], 1),
            'uptime_human': self._format_duration(health['uptime']),
            'message_count': health['message_count'],
            'error_rate': round(health['error_rate'] * 100, 1),  # Convert to percentage
            'avg_response_time': round(health['avg_response_time'], 2)
        }
        
        # Add recent patterns if any
        if health['recent_patterns']:
            data['recent_patterns'] = health['recent_patterns']
            data['pattern_descriptions'] = self._get_pattern_descriptions(health['recent_patterns'])
        
        # Add detailed metrics if requested
        if detailed:
            monitor = self.observer.monitors.get(health['session_id'])
            if monitor:
                metrics = monitor.metrics
                data['detailed_metrics'] = {
                    'error_count': metrics.error_count,
                    'tool_execution_count': metrics.tool_execution_count,
                    'agent_switches': metrics.agent_switches,
                    'tool_timeouts': metrics.tool_timeouts,
                    'response_times': {
                        'min': min(metrics.response_times) if metrics.response_times else 0,
                        'max': max(metrics.response_times) if metrics.response_times else 0,
                        'median': self._median(metrics.response_times) if metrics.response_times else 0
                    }
                }
                
                # Add recent errors if any
                if metrics.error_history:
                    data['recent_errors'] = [
                        {
                            'error': err['error'],
                            'type': err.get('type', 'Unknown'),
                            'time_ago': self._format_time_ago(err['timestamp'])
                        }
                        for err in metrics.error_history[-3:]  # Last 3 errors
                    ]
        
        return data
    
    def _get_status_from_score(self, score: float) -> str:
        """Get status description from health score"""
        if score >= 90:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 50:
            return "Fair"
        elif score >= 30:
            return "Poor"
        else:
            return "Critical"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format how long ago something happened"""
        delta = datetime.now() - timestamp
        seconds = delta.total_seconds()
        
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        else:
            return f"{int(seconds / 3600)}h ago"
    
    def _median(self, values: list) -> float:
        """Calculate median of a list"""
        if not values:
            return 0
        sorted_values = sorted(values)
        n = len(sorted_values)
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def _get_pattern_descriptions(self, patterns: list) -> Dict[str, str]:
        """Get human-readable descriptions for patterns"""
        descriptions = {
            'stall': 'Agent is taking too long to respond',
            'rapid_retry': 'User is retrying the same command multiple times',
            'error_cascade': 'Multiple errors occurring in succession',
            'tool_timeout': 'Tool execution is taking too long',
            'frustration': 'User appears frustrated (rapid messages)',
            'abandonment': 'User may be about to abandon the session',
            'permission_issue': 'Permission-related errors detected',
            'connection_issue': 'WebSocket connection problems detected'
        }
        
        return {p: descriptions.get(p, p) for p in patterns}