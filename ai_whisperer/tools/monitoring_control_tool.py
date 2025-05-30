"""
Monitoring Control Tool - Allows Debbie to control monitoring settings
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from .base_tool import AITool
from interactive_server.debbie_observer import get_observer, PatternType


class MonitoringControlTool(AITool):
    """
    Tool for controlling monitoring settings and alert thresholds.
    This allows Debbie to adjust monitoring behavior.
    """
    
    def __init__(self):
        """Initialize the monitoring control tool"""
        super().__init__()
        self._name = "monitoring_control"
        self._description = "Control monitoring settings and alert thresholds"
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
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["enable", "disable", "status", "set_threshold", "clear_alerts"],
                    "default": "status"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for session-specific actions (optional)"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern type for threshold setting",
                    "enum": ["stall", "rapid_retry", "error_cascade", "tool_timeout", "frustration"]
                },
                "threshold": {
                    "type": "number",
                    "description": "New threshold value"
                }
            },
            "required": ["action"]
        }
    
    @property
    def category(self) -> str:
        """Tool category"""
        return "Monitoring"
    
    @property
    def tags(self) -> list:
        """Tool tags"""
        return ["monitoring", "control", "settings", "alerts"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on how to use this tool"""
        return """
Use this tool to control monitoring settings and manage alerts.

Actions:
- enable: Enable monitoring (globally or for a session)
- disable: Disable monitoring (globally or for a session)
- status: Get current monitoring status
- set_threshold: Adjust pattern detection thresholds
- clear_alerts: Clear alerts for a session

Parameters:
- action: Required action to perform
- session_id: Optional, for session-specific actions
- pattern: Pattern type when setting thresholds
- threshold: New threshold value

Example usage:
{
    "action": "set_threshold",
    "pattern": "stall",
    "threshold": 45
}

{
    "action": "clear_alerts",
    "session_id": "session-123"
}

Default thresholds:
- stall: 30 seconds
- rapid_retry: 3 attempts in 10 seconds
- error_cascade: 5 errors in 60 seconds
- tool_timeout: 30 seconds
- frustration: 5 messages in 30 seconds
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the monitoring control action"""
        action = kwargs.get('action', 'status')
        session_id = kwargs.get('session_id')
        
        if action == 'enable':
            return self._enable_monitoring(session_id)
        elif action == 'disable':
            return self._disable_monitoring(session_id)
        elif action == 'status':
            return self._get_status(session_id)
        elif action == 'set_threshold':
            return self._set_threshold(kwargs.get('pattern'), kwargs.get('threshold'))
        elif action == 'clear_alerts':
            return self._clear_alerts(session_id)
        else:
            return {
                'success': False,
                'error': f'Unknown action: {action}'
            }
    
    def _enable_monitoring(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Enable monitoring"""
        if session_id:
            # Enable for specific session
            if session_id not in self.observer.monitors:
                monitor = self.observer.observe_session(session_id)
                return {
                    'success': True,
                    'message': f'Monitoring enabled for session {session_id}',
                    'session_health': monitor.get_health_status()
                }
            else:
                return {
                    'success': True,
                    'message': f'Monitoring already enabled for session {session_id}'
                }
        else:
            # Enable globally
            self.observer.enable()
            return {
                'success': True,
                'message': 'Global monitoring enabled',
                'active_sessions': len(self.observer.monitors)
            }
    
    def _disable_monitoring(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Disable monitoring"""
        if session_id:
            # Disable for specific session
            if session_id in self.observer.monitors:
                self.observer.stop_observing(session_id)
                return {
                    'success': True,
                    'message': f'Monitoring disabled for session {session_id}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Session {session_id} is not being monitored'
                }
        else:
            # Disable globally
            self.observer.disable()
            return {
                'success': True,
                'message': 'Global monitoring disabled'
            }
    
    def _get_status(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Get monitoring status"""
        status = {
            'success': True,
            'global_enabled': self.observer._enabled,
            'active_sessions': len(self.observer.monitors),
            'pattern_check_interval': self.observer._pattern_check_interval
        }
        
        if session_id:
            # Get session-specific status
            monitor = self.observer.monitors.get(session_id)
            if monitor:
                status['session_status'] = {
                    'monitored': True,
                    'health_score': monitor._calculate_health_score(),
                    'message_count': monitor.metrics.message_count,
                    'error_count': monitor.metrics.error_count,
                    'detected_patterns': [p.value for p in monitor.metrics.detected_patterns],
                    'alert_count': len(monitor.alerts)
                }
            else:
                status['session_status'] = {
                    'monitored': False
                }
        else:
            # Get all sessions status
            status['sessions'] = {}
            for sid, monitor in self.observer.monitors.items():
                status['sessions'][sid] = {
                    'health_score': monitor._calculate_health_score(),
                    'uptime': (datetime.now() - monitor.metrics.start_time).total_seconds(),
                    'patterns': len(monitor.metrics.detected_patterns),
                    'alerts': len(monitor.alerts)
                }
        
        # Current thresholds
        from interactive_server.debbie_observer import PatternDetector
        status['thresholds'] = {}
        for pattern_type, config in PatternDetector.PATTERNS.items():
            if 'threshold' in config:
                status['thresholds'][pattern_type.value] = {
                    'value': config['threshold'],
                    'unit': 'seconds' if 'window' not in config else 'occurrences',
                    'description': config['description']
                }
        
        return status
    
    def _set_threshold(self, pattern: Optional[str], threshold: Optional[float]) -> Dict[str, Any]:
        """Set pattern detection threshold"""
        if not pattern or threshold is None:
            return {
                'success': False,
                'error': 'Both pattern and threshold parameters are required'
            }
        
        # Map string to PatternType
        pattern_map = {
            'stall': PatternType.STALL,
            'rapid_retry': PatternType.RAPID_RETRY,
            'error_cascade': PatternType.ERROR_CASCADE,
            'tool_timeout': PatternType.TOOL_TIMEOUT,
            'frustration': PatternType.FRUSTRATION
        }
        
        pattern_type = pattern_map.get(pattern)
        if not pattern_type:
            return {
                'success': False,
                'error': f'Unknown pattern type: {pattern}'
            }
        
        # Update threshold in PatternDetector
        from interactive_server.debbie_observer import PatternDetector
        if pattern_type in PatternDetector.PATTERNS:
            old_threshold = PatternDetector.PATTERNS[pattern_type].get('threshold', 'N/A')
            PatternDetector.PATTERNS[pattern_type]['threshold'] = threshold
            
            return {
                'success': True,
                'message': f'Threshold updated for {pattern}',
                'pattern': pattern,
                'old_threshold': old_threshold,
                'new_threshold': threshold,
                'unit': 'seconds' if pattern in ['stall', 'tool_timeout'] else 'occurrences'
            }
        else:
            return {
                'success': False,
                'error': f'Pattern {pattern} does not have a configurable threshold'
            }
    
    def _clear_alerts(self, session_id: Optional[str]) -> Dict[str, Any]:
        """Clear alerts for a session"""
        if not session_id:
            # Clear all alerts
            cleared_count = 0
            for monitor in self.observer.monitors.values():
                cleared_count += len(monitor.alerts)
                monitor.alerts.clear()
                monitor.metrics.detected_patterns.clear()
            
            return {
                'success': True,
                'message': f'Cleared {cleared_count} alerts from all sessions',
                'sessions_affected': len(self.observer.monitors)
            }
        else:
            # Clear specific session alerts
            monitor = self.observer.monitors.get(session_id)
            if not monitor:
                return {
                    'success': False,
                    'error': f'Session {session_id} not found'
                }
            
            alert_count = len(monitor.alerts)
            pattern_count = len(monitor.metrics.detected_patterns)
            
            monitor.alerts.clear()
            monitor.metrics.detected_patterns.clear()
            
            return {
                'success': True,
                'message': f'Cleared alerts for session {session_id}',
                'alerts_cleared': alert_count,
                'patterns_cleared': pattern_count
            }