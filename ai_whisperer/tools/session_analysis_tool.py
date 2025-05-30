"""
Session Analysis Tool - Allows Debbie to analyze session activity and provide insights
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import Counter

from .base_tool import AITool
from interactive_server.debbie_observer import get_observer, PatternType, AlertSeverity


class SessionAnalysisTool(AITool):
    """
    Tool for analyzing session activity and providing debugging insights.
    This tool is primarily for Debbie to help diagnose issues.
    """
    
    def __init__(self):
        """Initialize the session analysis tool"""
        super().__init__()
        self._name = "session_analysis"
        self._description = "Analyze recent session activity and provide debugging insights"
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
                    "description": "Session ID to analyze (optional, defaults to current session)"
                },
                "time_range": {
                    "type": "integer",
                    "description": "Time range in seconds to analyze (default: 300 = last 5 minutes)",
                    "default": 300
                },
                "focus": {
                    "type": "string",
                    "description": "Focus area: 'errors', 'performance', 'patterns', 'all'",
                    "enum": ["errors", "performance", "patterns", "all"],
                    "default": "all"
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
        return ["monitoring", "debugging", "analysis", "insights"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Instructions for AI on how to use this tool"""
        return """
Use this tool to analyze recent session activity and get debugging insights.
The tool provides deep analysis of:
- Error patterns and root causes
- Performance bottlenecks
- User behavior patterns
- Recommended actions

Parameters:
- session_id: Optional session ID (defaults to current session)
- time_range: Seconds to look back (default: 300 = 5 minutes)
- focus: Analysis focus area ('errors', 'performance', 'patterns', 'all')

Example usage:
{
    "session_id": "current",
    "time_range": 600,
    "focus": "errors"
}

The analysis includes:
- Timeline of significant events
- Pattern detection results
- Common error analysis
- Performance metrics
- Actionable recommendations
"""
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the session analysis"""
        session_id = kwargs.get('session_id', 'current')
        time_range = kwargs.get('time_range', 300)
        focus = kwargs.get('focus', 'all')
        
        # Handle current session
        if session_id == 'current':
            all_health = self.observer.get_all_sessions_health()
            if not all_health:
                return {
                    'success': False,
                    'error': 'No active sessions found'
                }
            # Analyze most recent session
            session_id = list(all_health.keys())[-1]
        
        # Get monitor for session
        monitor = self.observer.monitors.get(session_id)
        if not monitor:
            return {
                'success': False,
                'error': f'Session {session_id} not found or not being monitored'
            }
        
        # Perform analysis based on focus
        analysis = {
            'success': True,
            'session_id': session_id,
            'time_range_seconds': time_range,
            'analysis_time': datetime.now().isoformat()
        }
        
        if focus in ['all', 'errors']:
            analysis['error_analysis'] = self._analyze_errors(monitor, time_range)
        
        if focus in ['all', 'performance']:
            analysis['performance_analysis'] = self._analyze_performance(monitor, time_range)
        
        if focus in ['all', 'patterns']:
            analysis['pattern_analysis'] = self._analyze_patterns(monitor)
        
        # Always include recommendations
        analysis['recommendations'] = self._generate_recommendations(monitor, analysis)
        
        # Add session summary
        analysis['summary'] = self._generate_summary(monitor, analysis)
        
        return analysis
    
    def _analyze_errors(self, monitor, time_range: int) -> Dict[str, Any]:
        """Analyze error patterns"""
        cutoff_time = datetime.now() - timedelta(seconds=time_range)
        recent_errors = [
            e for e in monitor.metrics.error_history
            if e['timestamp'] > cutoff_time
        ]
        
        if not recent_errors:
            return {
                'error_count': 0,
                'message': 'No errors in the specified time range'
            }
        
        # Categorize errors
        error_types = Counter(e.get('type', 'Unknown') for e in recent_errors)
        
        # Find common error messages
        error_messages = [e['error'] for e in recent_errors]
        common_patterns = self._find_common_patterns(error_messages)
        
        # Timeline of errors
        error_timeline = []
        for i, error in enumerate(recent_errors[-5:]):  # Last 5 errors
            error_timeline.append({
                'time_ago': self._format_time_ago(error['timestamp']),
                'type': error.get('type', 'Unknown'),
                'summary': self._summarize_error(error['error'])
            })
        
        return {
            'error_count': len(recent_errors),
            'error_rate_per_minute': len(recent_errors) / (time_range / 60),
            'error_types': dict(error_types),
            'common_patterns': common_patterns,
            'recent_errors': error_timeline,
            'clustering': self._cluster_errors(recent_errors)
        }
    
    def _analyze_performance(self, monitor, time_range: int) -> Dict[str, Any]:
        """Analyze performance metrics"""
        metrics = monitor.metrics
        
        if not metrics.response_times:
            return {
                'message': 'No performance data available'
            }
        
        # Calculate percentiles
        sorted_times = sorted(metrics.response_times)
        n = len(sorted_times)
        
        perf_data = {
            'avg_response_time': sum(sorted_times) / n,
            'median_response_time': sorted_times[n // 2],
            'p95_response_time': sorted_times[int(n * 0.95)] if n > 20 else sorted_times[-1],
            'slowest_response': max(sorted_times),
            'fastest_response': min(sorted_times)
        }
        
        # Identify slow operations
        slow_threshold = perf_data['avg_response_time'] * 2
        slow_operations = sum(1 for t in sorted_times if t > slow_threshold)
        perf_data['slow_operations_count'] = slow_operations
        perf_data['slow_operations_percentage'] = (slow_operations / n) * 100
        
        # Tool timeout analysis
        if metrics.tool_timeouts > 0:
            perf_data['tool_timeouts'] = {
                'count': metrics.tool_timeouts,
                'impact': 'High' if metrics.tool_timeouts > 3 else 'Medium'
            }
        
        # Response time trend
        if len(sorted_times) > 10:
            recent = sorted_times[-10:]
            older = sorted_times[-20:-10] if len(sorted_times) > 20 else sorted_times[:10]
            trend = 'improving' if sum(recent)/len(recent) < sum(older)/len(older) else 'degrading'
            perf_data['trend'] = trend
        
        return perf_data
    
    def _analyze_patterns(self, monitor) -> Dict[str, Any]:
        """Analyze detected patterns"""
        patterns = monitor.metrics.detected_patterns
        alerts = monitor.alerts
        
        if not patterns and not alerts:
            return {
                'message': 'No patterns detected',
                'health': 'Good'
            }
        
        # Count pattern occurrences
        pattern_counts = Counter(patterns)
        
        # Get pattern details
        pattern_details = {}
        for pattern in set(patterns):
            pattern_details[pattern.value] = {
                'count': pattern_counts[pattern],
                'severity': self._get_pattern_severity(pattern),
                'description': self._get_pattern_description(pattern),
                'impact': self._get_pattern_impact(pattern)
            }
        
        # Recent alerts
        recent_alerts = []
        for alert in alerts[-5:]:  # Last 5 alerts
            recent_alerts.append({
                'pattern': alert.pattern.value,
                'severity': alert.severity.value,
                'message': alert.message,
                'time_ago': self._format_time_ago(alert.timestamp),
                'suggestions': alert.suggestions[:2]  # First 2 suggestions
            })
        
        return {
            'total_patterns_detected': len(patterns),
            'unique_patterns': len(set(patterns)),
            'pattern_details': pattern_details,
            'recent_alerts': recent_alerts,
            'most_common_pattern': pattern_counts.most_common(1)[0] if pattern_counts else None
        }
    
    def _generate_recommendations(self, monitor, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check error analysis
        if 'error_analysis' in analysis and analysis['error_analysis'].get('error_count', 0) > 0:
            error_data = analysis['error_analysis']
            
            # Permission errors
            if 'Permission' in str(error_data.get('error_types', {})):
                recommendations.append({
                    'priority': 'high',
                    'category': 'permissions',
                    'action': 'Check file and directory permissions',
                    'details': 'Permission errors detected. Verify write access to output directories.'
                })
            
            # High error rate
            if error_data.get('error_rate_per_minute', 0) > 1:
                recommendations.append({
                    'priority': 'high',
                    'category': 'stability',
                    'action': 'Investigate error cascade',
                    'details': f"High error rate: {error_data['error_rate_per_minute']:.1f} errors/minute"
                })
        
        # Check performance
        if 'performance_analysis' in analysis:
            perf_data = analysis['performance_analysis']
            
            # Slow responses
            if perf_data.get('avg_response_time', 0) > 5:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'performance',
                    'action': 'Optimize slow operations',
                    'details': f"Average response time is {perf_data['avg_response_time']:.1f}s"
                })
            
            # Tool timeouts
            if perf_data.get('tool_timeouts', {}).get('count', 0) > 0:
                recommendations.append({
                    'priority': 'high',
                    'category': 'performance',
                    'action': 'Investigate tool timeouts',
                    'details': f"{perf_data['tool_timeouts']['count']} tool operations timed out"
                })
        
        # Check patterns
        if 'pattern_analysis' in analysis:
            pattern_data = analysis['pattern_analysis']
            
            # Stall pattern
            if 'stall' in pattern_data.get('pattern_details', {}):
                recommendations.append({
                    'priority': 'high',
                    'category': 'responsiveness',
                    'action': 'Check for agent stalls',
                    'details': 'Agent stalls detected. Consider restarting or checking system resources.'
                })
            
            # Frustration pattern
            if 'frustration' in pattern_data.get('pattern_details', {}):
                recommendations.append({
                    'priority': 'medium',
                    'category': 'user_experience',
                    'action': 'Improve response clarity',
                    'details': 'User frustration detected. Consider providing clearer error messages.'
                })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _generate_summary(self, monitor, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary"""
        health = self.observer.get_session_health(monitor.session_id)
        
        parts = []
        
        # Health status
        if health:
            status = self._get_status_from_score(health['health_score'])
            parts.append(f"Session health: {status} ({health['health_score']:.0f}/100)")
        
        # Error summary
        if 'error_analysis' in analysis:
            error_count = analysis['error_analysis'].get('error_count', 0)
            if error_count > 0:
                parts.append(f"{error_count} errors detected")
        
        # Performance summary
        if 'performance_analysis' in analysis:
            avg_time = analysis['performance_analysis'].get('avg_response_time', 0)
            if avg_time > 0:
                parts.append(f"Avg response: {avg_time:.1f}s")
        
        # Pattern summary
        if 'pattern_analysis' in analysis:
            pattern_count = analysis['pattern_analysis'].get('total_patterns_detected', 0)
            if pattern_count > 0:
                parts.append(f"{pattern_count} patterns detected")
        
        # Recommendation count
        rec_count = len(analysis.get('recommendations', []))
        if rec_count > 0:
            parts.append(f"{rec_count} recommendations available")
        
        return ". ".join(parts) if parts else "Session appears healthy with no significant issues."
    
    # Helper methods
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
    
    def _summarize_error(self, error_msg: str) -> str:
        """Create a short summary of an error message"""
        # Truncate long errors
        if len(error_msg) > 100:
            return error_msg[:97] + "..."
        return error_msg
    
    def _find_common_patterns(self, messages: List[str]) -> List[str]:
        """Find common patterns in error messages"""
        if not messages:
            return []
        
        # Simple pattern detection - look for common words
        words = []
        for msg in messages:
            words.extend(msg.lower().split())
        
        word_counts = Counter(words)
        # Filter out common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'from', 'in', 'on', 'at'}
        significant_words = [(w, c) for w, c in word_counts.items() 
                            if w not in stop_words and len(w) > 3 and c > 1]
        
        # Return top patterns
        patterns = []
        for word, count in sorted(significant_words, key=lambda x: x[1], reverse=True)[:3]:
            if count > len(messages) * 0.3:  # Word appears in >30% of messages
                patterns.append(f"'{word}' (appears {count} times)")
        
        return patterns
    
    def _cluster_errors(self, errors: List[Dict]) -> Dict[str, List[Dict]]:
        """Cluster similar errors together"""
        clusters = {}
        
        for error in errors:
            error_text = error['error'].lower()
            
            # Simple clustering by keywords
            if 'permission' in error_text or 'denied' in error_text:
                key = 'permission_errors'
            elif 'timeout' in error_text or 'timed out' in error_text:
                key = 'timeout_errors'
            elif 'not found' in error_text or 'missing' in error_text:
                key = 'not_found_errors'
            elif 'connection' in error_text or 'network' in error_text:
                key = 'connection_errors'
            else:
                key = 'other_errors'
            
            if key not in clusters:
                clusters[key] = []
            clusters[key].append({
                'time': self._format_time_ago(error['timestamp']),
                'message': self._summarize_error(error['error'])
            })
        
        return clusters
    
    def _get_pattern_severity(self, pattern: PatternType) -> str:
        """Get severity level for a pattern"""
        severity_map = {
            PatternType.STALL: 'high',
            PatternType.ERROR_CASCADE: 'high',
            PatternType.PERMISSION_ISSUE: 'high',
            PatternType.TOOL_TIMEOUT: 'medium',
            PatternType.FRUSTRATION: 'medium',
            PatternType.RAPID_RETRY: 'low',
            PatternType.ABANDONMENT: 'medium',
            PatternType.CONNECTION_ISSUE: 'high'
        }
        return severity_map.get(pattern, 'medium')
    
    def _get_pattern_description(self, pattern: PatternType) -> str:
        """Get description for a pattern"""
        descriptions = {
            PatternType.STALL: 'Agent is not responding within expected time',
            PatternType.RAPID_RETRY: 'User is retrying the same command multiple times',
            PatternType.ERROR_CASCADE: 'Multiple errors occurring in quick succession',
            PatternType.TOOL_TIMEOUT: 'Tool execution is taking longer than expected',
            PatternType.FRUSTRATION: 'User showing signs of frustration (rapid messages)',
            PatternType.ABANDONMENT: 'User may be about to leave the session',
            PatternType.PERMISSION_ISSUE: 'File or directory permission problems',
            PatternType.CONNECTION_ISSUE: 'WebSocket connection instability'
        }
        return descriptions.get(pattern, 'Unknown pattern')
    
    def _get_pattern_impact(self, pattern: PatternType) -> str:
        """Get impact description for a pattern"""
        impacts = {
            PatternType.STALL: 'Blocks user progress completely',
            PatternType.RAPID_RETRY: 'Indicates unclear error messages or confusion',
            PatternType.ERROR_CASCADE: 'System may be in unstable state',
            PatternType.TOOL_TIMEOUT: 'Significantly slows down operations',
            PatternType.FRUSTRATION: 'Poor user experience, may lead to abandonment',
            PatternType.ABANDONMENT: 'User likely to stop using the system',
            PatternType.PERMISSION_ISSUE: 'Prevents file operations from completing',
            PatternType.CONNECTION_ISSUE: 'May cause message loss or delays'
        }
        return impacts.get(pattern, 'May affect user experience')