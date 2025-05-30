"""
Session Inspector Tool for Debbie the Debugger.
Analyzes active session state, message history, and detects common issues like stalls.
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .base_tool import AITool
from ..logging_custom import EnhancedLogMessage, LogLevel, LogSource, ComponentType

logger = logging.getLogger(__name__)


@dataclass
class SessionAnalysis:
    """Results of session analysis"""
    session_id: str
    status: str  # active, stalled, error, completed
    duration_seconds: float
    message_count: int
    last_activity: datetime
    stall_detected: bool
    stall_duration: Optional[float] = None
    stall_reason: Optional[str] = None
    tool_usage_summary: Dict[str, int] = None
    error_count: int = 0
    warnings: List[str] = None
    recommendations: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_activity'] = self.last_activity.isoformat()
        return data


class SessionInspectorTool(AITool):
    """
    Inspects and analyzes active AI sessions to detect issues like stalls,
    errors, and performance problems.
    """
    
    def __init__(self, session_manager=None, log_aggregator=None):
        """
        Initialize with optional session manager and log aggregator.
        
        Args:
            session_manager: The session manager instance to inspect sessions
            log_aggregator: The log aggregator for analyzing session logs
        """
        self.session_manager = session_manager
        self.log_aggregator = log_aggregator
        self.stall_threshold = 30  # seconds before considering a session stalled
        
    @property
    def name(self) -> str:
        return "session_inspector"
    
    @property
    def description(self) -> str:
        return "Analyzes active AI sessions to detect stalls, errors, and performance issues"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID to inspect. Use 'current' for the current session."
                },
                "include_message_history": {
                    "type": "boolean",
                    "description": "Whether to include detailed message history in the analysis",
                    "default": False
                },
                "time_window_minutes": {
                    "type": "integer",
                    "description": "Time window in minutes to analyze (default: last 10 minutes)",
                    "default": 10
                }
            },
            "required": ["session_id"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Debugging"
    
    @property
    def tags(self) -> List[str]:
        return ["debugging", "monitoring", "session", "analysis"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the session_inspector tool to analyze AI sessions when:
        - An agent appears to be stuck or not responding
        - You need to understand what's happening in a session
        - Performance issues are suspected
        - Errors or warnings need investigation
        
        The tool will detect:
        - Stalled sessions (no activity for >30 seconds)
        - Tool execution patterns
        - Error frequencies
        - Performance metrics
        
        Example usage:
        - session_inspector(session_id="current") - Inspect the current session
        - session_inspector(session_id="abc123", include_message_history=true) - Get detailed history
        """
    
    def execute(self, session_id: str, include_message_history: bool = False, 
                time_window_minutes: int = 10) -> Dict[str, Any]:
        """
        Inspect and analyze the specified session.
        
        Args:
            session_id: The session to inspect ('current' for current session)
            include_message_history: Whether to include message details
            time_window_minutes: How far back to analyze
            
        Returns:
            Analysis results including stall detection and recommendations
        """
        try:
            # Resolve session ID
            if session_id == "current" and self.session_manager:
                session_id = self._get_current_session_id()
                
            if not session_id:
                return {"error": "No active session found"}
            
            # Get session data
            session_data = self._get_session_data(session_id)
            if not session_data:
                return {"error": f"Session {session_id} not found"}
            
            # Analyze session
            analysis = self._analyze_session(
                session_data, 
                time_window_minutes,
                include_message_history
            )
            
            # Log the analysis
            self._log_analysis(analysis)
            
            # Format response
            response = {
                "analysis": analysis.to_dict(),
                "success": True
            }
            
            if include_message_history and session_data.get('messages'):
                response['message_history'] = self._format_message_history(
                    session_data['messages']
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error inspecting session: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get the current active session ID"""
        if not self.session_manager:
            return None
        
        # This would interact with the actual session manager
        # For now, return a placeholder
        return self.session_manager.get_current_session_id() if hasattr(
            self.session_manager, 'get_current_session_id'
        ) else None
    
    def _get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data from session manager"""
        if not self.session_manager:
            # Mock data for testing
            return self._get_mock_session_data(session_id)
        
        return self.session_manager.get_session_data(session_id) if hasattr(
            self.session_manager, 'get_session_data'
        ) else None
    
    def _analyze_session(self, session_data: Dict[str, Any], 
                        time_window_minutes: int,
                        include_details: bool) -> SessionAnalysis:
        """Perform comprehensive session analysis"""
        now = datetime.now()
        start_time = now - timedelta(minutes=time_window_minutes)
        
        # Extract basic info
        session_id = session_data.get('id', 'unknown')
        messages = session_data.get('messages', [])
        session_start = session_data.get('start_time', now)
        
        # Filter messages by time window
        recent_messages = [
            msg for msg in messages 
            if self._parse_timestamp(msg.get('timestamp', '')) >= start_time
        ]
        
        # Analyze activity
        last_activity = self._get_last_activity(recent_messages)
        time_since_activity = (now - last_activity).total_seconds() if last_activity else 0
        
        # Detect stalls
        stall_detected = time_since_activity > self.stall_threshold
        stall_reason = None
        if stall_detected:
            stall_reason = self._determine_stall_reason(recent_messages)
        
        # Analyze tool usage
        tool_usage = self._analyze_tool_usage(recent_messages)
        
        # Count errors
        error_count = self._count_errors(recent_messages)
        
        # Generate warnings and recommendations
        warnings = self._generate_warnings(
            stall_detected, time_since_activity, error_count, tool_usage
        )
        recommendations = self._generate_recommendations(
            stall_detected, stall_reason, error_count, tool_usage
        )
        
        return SessionAnalysis(
            session_id=session_id,
            status=self._determine_status(stall_detected, error_count),
            duration_seconds=(now - session_start).total_seconds(),
            message_count=len(recent_messages),
            last_activity=last_activity or now,
            stall_detected=stall_detected,
            stall_duration=time_since_activity if stall_detected else None,
            stall_reason=stall_reason,
            tool_usage_summary=tool_usage,
            error_count=error_count,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _determine_stall_reason(self, messages: List[Dict]) -> Optional[str]:
        """Determine why a session stalled"""
        if not messages:
            return "No recent activity"
        
        last_message = messages[-1]
        
        # Check for common stall patterns
        if last_message.get('type') == 'tool_execution':
            return "Waiting for user input after tool execution (continuation required)"
        elif last_message.get('type') == 'error':
            return f"Stalled after error: {last_message.get('error', 'Unknown error')}"
        elif 'waiting' in last_message.get('content', '').lower():
            return "Agent indicated it's waiting for something"
        else:
            return "Unknown stall reason"
    
    def _analyze_tool_usage(self, messages: List[Dict]) -> Dict[str, int]:
        """Analyze tool usage patterns"""
        tool_usage = {}
        for msg in messages:
            if msg.get('type') == 'tool_execution':
                tool_name = msg.get('tool_name', 'unknown')
                tool_usage[tool_name] = tool_usage.get(tool_name, 0) + 1
        return tool_usage
    
    def _count_errors(self, messages: List[Dict]) -> int:
        """Count error messages"""
        return sum(1 for msg in messages if msg.get('type') == 'error')
    
    def _generate_warnings(self, stall_detected: bool, time_since_activity: float,
                          error_count: int, tool_usage: Dict[str, int]) -> List[str]:
        """Generate warning messages based on analysis"""
        warnings = []
        
        if stall_detected:
            warnings.append(f"Session stalled for {time_since_activity:.1f} seconds")
        
        if error_count > 0:
            warnings.append(f"Found {error_count} errors in recent activity")
        
        # Check for tool loops
        for tool, count in tool_usage.items():
            if count > 5:
                warnings.append(f"Tool '{tool}' executed {count} times - possible loop")
        
        return warnings
    
    def _generate_recommendations(self, stall_detected: bool, stall_reason: Optional[str],
                                 error_count: int, tool_usage: Dict[str, int]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if stall_detected and stall_reason:
            if "continuation required" in stall_reason:
                recommendations.append("Inject continuation prompt to unstick the agent")
            elif "error" in stall_reason:
                recommendations.append("Review error and consider retry with different parameters")
            else:
                recommendations.append("Consider restarting the session or injecting a prompt")
        
        if error_count > 2:
            recommendations.append("Investigate recurring errors - may need configuration fix")
        
        # Tool-specific recommendations
        if any(count > 5 for count in tool_usage.values()):
            recommendations.append("Possible tool execution loop - review agent logic")
        
        return recommendations
    
    def _determine_status(self, stall_detected: bool, error_count: int) -> str:
        """Determine overall session status"""
        if stall_detected:
            return "stalled"
        elif error_count > 0:
            return "error"
        else:
            return "active"
    
    def _get_last_activity(self, messages: List[Dict]) -> Optional[datetime]:
        """Get timestamp of last activity"""
        if not messages:
            return None
        
        for msg in reversed(messages):
            timestamp = self._parse_timestamp(msg.get('timestamp', ''))
            if timestamp:
                return timestamp
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        try:
            # Handle ISO format
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None
    
    def _format_message_history(self, messages: List[Dict]) -> List[Dict]:
        """Format message history for output"""
        formatted = []
        for msg in messages[-10:]:  # Last 10 messages
            formatted.append({
                'timestamp': msg.get('timestamp'),
                'type': msg.get('type'),
                'content': msg.get('content', '')[:200],  # Truncate long content
                'tool': msg.get('tool_name') if msg.get('type') == 'tool_execution' else None
            })
        return formatted
    
    def _log_analysis(self, analysis: SessionAnalysis):
        """Log the analysis results"""
        log_msg = EnhancedLogMessage(
            level=LogLevel.INFO,
            component=ComponentType.MONITOR,
            source=LogSource.DEBBIE,
            action="session_inspected",
            event_summary=f"Session {analysis.session_id} analysis: {analysis.status}",
            session_id=analysis.session_id,
            details={
                "stall_detected": analysis.stall_detected,
                "stall_duration": analysis.stall_duration,
                "error_count": analysis.error_count,
                "warnings": analysis.warnings,
                "recommendations": analysis.recommendations
            }
        )
        logger.info(log_msg.event_summary, extra=log_msg.to_dict())
    
    def _get_mock_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get mock session data for testing"""
        now = datetime.now()
        return {
            'id': session_id,
            'start_time': now - timedelta(minutes=5),
            'messages': [
                {
                    'timestamp': (now - timedelta(minutes=3)).isoformat(),
                    'type': 'user_message',
                    'content': 'List the RFCs'
                },
                {
                    'timestamp': (now - timedelta(minutes=2, seconds=50)).isoformat(),
                    'type': 'tool_execution',
                    'tool_name': 'list_rfcs',
                    'content': 'Executing list_rfcs tool...'
                },
                {
                    'timestamp': (now - timedelta(minutes=2, seconds=45)).isoformat(),
                    'type': 'tool_result',
                    'content': 'Found 3 RFCs in the system'
                }
                # No activity for last 2+ minutes - stall!
            ]
        }