"""
Debbie debugging commands for interactive session monitoring and analysis.
"""

from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry
from ai_whisperer.interfaces.cli.commands.errors import CommandError
from typing import Any, Dict, Optional
from datetime import datetime

class DebbieCommand(Command):
    """
    Debbie debugging command with subcommands for session monitoring.
    
    Usage:
        /debbie status [session_id] - Show current session health
        /debbie analyze [session_id] [time_range] - Deep analysis of recent activity  
        /debbie suggest [session_id] - Get recommendations for current session
        /debbie report [session_id] - Generate comprehensive session report
    """
    name = 'debbie'
    description = 'Debbie debugging and monitoring commands'

    def run(self, args: str, context: Dict[str, Any] = None) -> Any:
        """Execute debbie subcommand"""
        parsed = self.parse_args(args)
        subcommand = parsed['args'][0] if parsed['args'] else 'status'
        
        # Get session ID from args or context
        session_id = None
        if len(parsed['args']) > 1:
            session_id = parsed['args'][1]
        elif context and 'session_id' in context:
            session_id = context['session_id']
        
        try:
            if subcommand == 'status':
                return self._status_command(session_id, parsed['options'])
            elif subcommand == 'analyze':
                time_range = int(parsed['args'][2]) if len(parsed['args']) > 2 else 300  # 5 minutes default
                return self._analyze_command(session_id, time_range, parsed['options'])
            elif subcommand == 'suggest':
                return self._suggest_command(session_id, parsed['options'])
            elif subcommand == 'report':
                return self._report_command(session_id, parsed['options'])
            else:
                raise CommandError(f"Unknown subcommand: {subcommand}")
        except Exception as e:
            raise CommandError(f"Debbie command failed: {str(e)}")

    def _get_observer(self):
        """Get the Debbie observer instance"""
        try:
            from interactive_server.debbie_observer import get_observer
            observer = get_observer()
            if not observer._enabled:
                return None  # Observer exists but is disabled
            return observer
        except ImportError:
            return None  # Observer not available

    def _status_command(self, session_id: Optional[str], options: Dict[str, Any]) -> str:
        """Get current session health status"""
        observer = self._get_observer()
        
        if not observer:
            return """❌ Debbie monitoring is not active

To enable monitoring, restart the server with:
  python -m interactive_server.main --debbie-monitor

Available monitoring levels:
  --monitor-level passive  (observe only)
  --monitor-level active   (can intervene)

For now, I'm available for general debugging assistance!"""
        
        # Get detailed status
        detailed = options.get('detailed', False) or options.get('d', False)
        
        if session_id:
            # Status for specific session
            monitor = observer.monitors.get(session_id)
            if not monitor:
                # Session not being monitored, but provide helpful info
                return f"""ℹ️ Session {session_id[:8]}... is not currently monitored

📊 Global Monitoring Status: {'Enabled' if observer._enabled else 'Disabled'}
📈 Active Monitored Sessions: {len(observer.monitors)}

To monitor this session, restart the server with:
  python -m interactive_server.main --debbie-monitor

Or use `/debbie status` without arguments for global information."""
            
            health_score = monitor._calculate_health_score()
            status_emoji = "🟢" if health_score >= 80 else "🟡" if health_score >= 60 else "🔴"
            
            result = f"""{status_emoji} Session {session_id} Health: {health_score}/100

📊 Metrics:
  • Messages: {monitor.metrics.message_count}
  • Errors: {monitor.metrics.error_count}
  • Avg Response Time: {monitor.metrics.avg_response_time:.2f}s
  • Uptime: {(datetime.now() - monitor.metrics.start_time).total_seconds():.0f}s"""

            if detailed:
                patterns = [p.value for p in monitor.metrics.detected_patterns]
                alerts = len(monitor.alerts)
                result += f"""
  • Detected Patterns: {', '.join(patterns) if patterns else 'None'}
  • Active Alerts: {alerts}"""
                
                if monitor.alerts:
                    result += f"\n\n🚨 Recent Alerts:"
                    for alert in monitor.alerts[-3:]:  # Show last 3 alerts
                        result += f"\n  • {alert.severity.value}: {alert.message}"
            
            return result
        else:
            # Global status
            active_sessions = len(observer.monitors)
            
            result = f"""🤖 Debbie Monitoring Status: {'Enabled' if observer._enabled else 'Disabled'}

📈 Global Stats:
  • Active Sessions: {active_sessions}
  • Check Interval: {observer._pattern_check_interval}s

💡 Available Commands:
  • `/debbie status` - Show this global status
  • `/debbie suggest` - General debugging suggestions
  • `/debbie analyze <session_id>` - Deep session analysis (requires monitoring)
  • `/debbie report <session_id>` - Comprehensive report (requires monitoring)"""
            
            if detailed and active_sessions > 0:
                result += f"\n\n📋 Session Summary:"
                for sid, monitor in observer.monitors.items():
                    health = monitor._calculate_health_score()
                    emoji = "🟢" if health >= 80 else "🟡" if health >= 60 else "🔴"
                    result += f"\n  {emoji} {sid[:8]}... Health: {health}/100"
            elif active_sessions == 0:
                result += f"\n\n💡 To enable session monitoring:\n  python -m interactive_server.main --debbie-monitor"
            
            return result

    def _analyze_command(self, session_id: Optional[str], time_range: int, options: Dict[str, Any]) -> str:
        """Deep analysis of recent session activity"""
        observer = self._get_observer()
        
        if not observer:
            return "❌ Session analysis requires active monitoring. Use `/debbie status` for setup instructions."
        
        if not session_id:
            return "❌ Session ID required for analysis"
        
        monitor = observer.monitors.get(session_id)
        if not monitor:
            return f"❌ Session {session_id} not found or not monitored"
        
        # Use session analysis tool for detailed analysis
        try:
            from ai_whisperer.tools.session_analysis_tool import SessionAnalysisTool
            analysis_tool = SessionAnalysisTool()
            
            # Execute analysis
            result = analysis_tool.execute(
                session_id=session_id,
                time_range=time_range,
                focus=options.get('focus', 'all')
            )
            
            if not result.get('success'):
                return f"❌ Analysis failed: {result.get('error', 'Unknown error')}"
            
            analysis = result.get('analysis', {})
            
            # Format analysis results
            output = f"""🔍 Deep Analysis for Session {session_id} (last {time_range}s)

📊 Summary:
  • Health Score: {analysis.get('health_score', 'N/A')}/100
  • Total Events: {analysis.get('total_events', 0)}
  • Error Rate: {analysis.get('error_rate', 0):.1f}%
  • Avg Response Time: {analysis.get('avg_response_time', 0):.2f}s"""
            
            # Error analysis
            errors = analysis.get('errors', {})
            if errors:
                output += f"\n\n🚨 Error Analysis:"
                for category, details in errors.items():
                    output += f"\n  • {category}: {details.get('count', 0)} occurrences"
            
            # Performance analysis
            performance = analysis.get('performance', {})
            if performance:
                output += f"\n\n⚡ Performance:"
                slowest = performance.get('slowest_operations', [])
                if slowest:
                    output += f"\n  • Slowest: {slowest[0].get('operation', 'N/A')} ({slowest[0].get('duration', 0):.2f}s)"
            
            # Recommendations
            recommendations = analysis.get('recommendations', [])
            if recommendations:
                output += f"\n\n💡 Recommendations:"
                for rec in recommendations[:3]:  # Show top 3
                    output += f"\n  • {rec}"
            
            return output
            
        except Exception as e:
            return f"❌ Analysis failed: {str(e)}"

    def _suggest_command(self, session_id: Optional[str], options: Dict[str, Any]) -> str:
        """Get recommendations for current session"""
        observer = self._get_observer()
        
        if not observer:
            return """💡 General Debugging Suggestions:

1. 🔍 Check server logs for error messages
2. 🔄 Try refreshing the browser if UI is unresponsive  
3. 🔌 Verify WebSocket connection to backend
4. 🐛 Look for JavaScript console errors
5. 📊 Monitor memory usage and performance
6. 🚀 Restart server if issues persist

For session-specific suggestions, enable monitoring with:
  python -m interactive_server.main --debbie-monitor"""
        
        if not session_id:
            # No session ID provided, show general suggestions
            return """💡 General Debugging Suggestions:

1. 🔍 Check server logs for error messages
2. 🔄 Try refreshing the browser if UI is unresponsive  
3. 🔌 Verify WebSocket connection to backend
4. 🐛 Look for JavaScript console errors (F12)
5. 📊 Monitor memory usage and performance
6. 🚀 Restart server if issues persist
7. 🔑 Check API keys and configuration files
8. 🌐 Verify network connectivity

💡 For session-specific suggestions, use:
  `/debbie suggest <session_id>`

📊 For monitoring status, use:
  `/debbie status`"""
        
        monitor = observer.monitors.get(session_id)
        if not monitor:
            return f"❌ Session {session_id} not found or not monitored"
        
        # Generate context-aware suggestions
        health_score = monitor._calculate_health_score()
        patterns = monitor.metrics.detected_patterns
        alerts = monitor.alerts
        
        suggestions = []
        
        # Health-based suggestions
        if health_score < 60:
            suggestions.append("🔄 Consider restarting the session - health score is low")
        elif health_score < 80:
            suggestions.append("⚠️ Monitor session closely - some issues detected")
        
        # Pattern-based suggestions
        from interactive_server.debbie_observer import PatternType
        if PatternType.STALL in patterns:
            suggestions.append("⏰ Agent may be stalled - try sending a continuation prompt")
        if PatternType.RAPID_RETRY in patterns:
            suggestions.append("🔄 User is retrying commands - check for underlying issues")
        if PatternType.ERROR_CASCADE in patterns:
            suggestions.append("🚨 Multiple errors detected - investigate root cause")
        if PatternType.FRUSTRATION in patterns:
            suggestions.append("😤 User frustration detected - consider offering assistance")
        
        # Performance suggestions
        if monitor.metrics.avg_response_time > 10:
            suggestions.append("🐌 Slow response times - check system resources")
        
        # Error rate suggestions
        error_rate = (monitor.metrics.error_count / max(monitor.metrics.message_count, 1)) * 100
        if error_rate > 20:
            suggestions.append("❌ High error rate - review recent tool executions")
        
        # Default suggestions if none specific
        if not suggestions:
            suggestions.append("✅ Session appears healthy - continue normal operation")
            suggestions.append("📊 Run '/debbie analyze' for deeper insights")
        
        result = f"💡 Suggestions for Session {session_id}:\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            result += f"{i}. {suggestion}\n"
        
        return result.strip()

    def _report_command(self, session_id: Optional[str], options: Dict[str, Any]) -> str:
        """Generate comprehensive session report"""
        observer = self._get_observer()
        
        if not observer:
            return "❌ Session reports require active monitoring. Use `/debbie status` for setup instructions."
        
        if not session_id:
            return "❌ Session ID required for report generation"
        
        monitor = observer.monitors.get(session_id)
        if not monitor:
            return f"❌ Session {session_id} not found or not monitored"
        
        # Generate comprehensive report
        uptime = (datetime.now() - monitor.metrics.start_time).total_seconds()
        health_score = monitor._calculate_health_score()
        
        report = f"""📋 Debbie Session Report
Session ID: {session_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════

📊 SESSION OVERVIEW
  Health Score: {health_score}/100
  Session Uptime: {uptime:.0f} seconds ({uptime/60:.1f} minutes)
  
📈 ACTIVITY METRICS
  Total Messages: {monitor.metrics.message_count}
  Error Count: {monitor.metrics.error_count}
  Error Rate: {(monitor.metrics.error_count / max(monitor.metrics.message_count, 1)) * 100:.1f}%
  Average Response Time: {monitor.metrics.avg_response_time:.2f}s

🔍 PATTERN DETECTION
  Detected Patterns: {len(monitor.metrics.detected_patterns)}"""
        
        if monitor.metrics.detected_patterns:
            for pattern in monitor.metrics.detected_patterns:
                report += f"\n    • {pattern.value}"
        else:
            report += "\n    • No problematic patterns detected"
        
        report += f"\n\n🚨 ALERTS SUMMARY\n  Total Alerts: {len(monitor.alerts)}"
        
        if monitor.alerts:
            # Group alerts by severity
            from collections import defaultdict
            alerts_by_severity = defaultdict(list)
            for alert in monitor.alerts:
                alerts_by_severity[alert.severity.value].append(alert)
            
            for severity, alerts in alerts_by_severity.items():
                report += f"\n    • {severity}: {len(alerts)} alerts"
        
        # Recent activity (last 5 alerts)
        if monitor.alerts:
            report += f"\n\n📅 RECENT ALERTS (Last 5):"
            for alert in monitor.alerts[-5:]:
                timestamp = alert.timestamp.strftime('%H:%M:%S')
                report += f"\n  [{timestamp}] {alert.severity.value}: {alert.message}"
        
        # Health assessment
        report += f"\n\n🏥 HEALTH ASSESSMENT"
        if health_score >= 80:
            report += f"\n  Status: Excellent - Session is performing well"
        elif health_score >= 60:
            report += f"\n  Status: Good - Minor issues may be present"
        else:
            report += f"\n  Status: Poor - Significant issues detected"
        
        # Recommendations section
        report += f"\n\n💡 RECOMMENDATIONS"
        if health_score < 70:
            report += f"\n  • Consider session restart or intervention"
        if monitor.metrics.avg_response_time > 5:
            report += f"\n  • Investigate performance bottlenecks"
        if len(monitor.alerts) > 10:
            report += f"\n  • Review alert patterns for recurring issues"
        
        report += f"\n\n═══════════════════════════════════════\nEnd of Report"
        
        return report

# Register the command
CommandRegistry.register(DebbieCommand)
