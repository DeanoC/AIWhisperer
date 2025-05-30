"""
Monitoring control tool for Debbie the Debugger.
Controls monitoring settings and alerts.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime

from ai_whisperer.tools.base_tool import AITool


class MonitoringControlTool(AITool):
    """Control monitoring settings for AI sessions"""
    
    @property
    def name(self) -> str:
        return "monitoring_control"
    
    @property
    def description(self) -> str:
        return "Control monitoring settings - enable/disable monitoring, adjust thresholds, clear alerts"
    
    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["enable", "disable", "status", "set_threshold", "clear_alerts"],
                    "description": "The monitoring control action to perform"
                },
                "session_id": {
                    "type": ["string", "null"],
                    "description": "Session ID to control. Use 'current' for current session, null for global"
                },
                "threshold_type": {
                    "type": ["string", "null"],
                    "enum": ["error_rate", "response_time", "stall_detection", None],
                    "description": "Type of threshold to set (required for set_threshold action)"
                },
                "threshold_value": {
                    "type": ["number", "null"],
                    "description": "New threshold value (required for set_threshold action)"
                }
            },
            "required": ["action"],
            "additionalProperties": False
        }
    
    def get_ai_prompt_instructions(self) -> str:
        """Get instructions for AI on how to use this tool"""
        return """Use this tool to control session monitoring settings. Actions:
- enable/disable: Turn monitoring on/off (globally or per session)
- status: Check current monitoring status and alerts
- set_threshold: Adjust monitoring thresholds (error_rate, response_time, stall_detection)
- clear_alerts: Clear existing alerts

Examples:
- monitoring_control(action="status") - Check global status
- monitoring_control(action="enable", session_id="current") - Enable for current session
- monitoring_control(action="set_threshold", threshold_type="error_rate", threshold_value=0.05)"""
    
    async def execute(
        self,
        action: str,
        session_id: Optional[str] = None,
        threshold_type: Optional[str] = None,
        threshold_value: Optional[float] = None
    ) -> str:
        """Execute the monitoring control action"""
        # Handle current session
        if session_id == "current":
            session_id = "current-session-id"
        
        # Simulate monitoring state (in real implementation would be persistent)
        monitoring_state = self._get_monitoring_state()
        
        # Execute action
        if action == "enable":
            result = self._enable_monitoring(monitoring_state, session_id)
        elif action == "disable":
            result = self._disable_monitoring(monitoring_state, session_id)
        elif action == "status":
            result = self._get_monitoring_status(monitoring_state, session_id)
        elif action == "set_threshold":
            result = self._set_threshold(monitoring_state, threshold_type, threshold_value)
        elif action == "clear_alerts":
            result = self._clear_alerts(monitoring_state, session_id)
        else:
            result = f"Unknown action: {action}"
        
        return result
    
    def _get_monitoring_state(self) -> Dict[str, Any]:
        """Get current monitoring state (simulated)"""
        return {
            "global": {
                "enabled": True,
                "thresholds": {
                    "error_rate": 0.1,  # 10%
                    "response_time": 5000,  # 5 seconds
                    "stall_detection": 30  # 30 seconds
                },
                "alerts": [
                    {
                        "id": "alert-001",
                        "type": "STALL_DETECTED",
                        "session_id": "session-123",
                        "timestamp": datetime.now().isoformat(),
                        "severity": "high"
                    }
                ]
            },
            "sessions": {
                "session-123": {
                    "enabled": True,
                    "custom_thresholds": {},
                    "alerts": 1
                },
                "current-session-id": {
                    "enabled": True,
                    "custom_thresholds": {},
                    "alerts": 0
                }
            }
        }
    
    def _enable_monitoring(self, state: Dict[str, Any], session_id: Optional[str]) -> str:
        """Enable monitoring"""
        if session_id:
            # Enable for specific session
            session_name = f"Session {session_id}"
            if session_id in state["sessions"]:
                if state["sessions"][session_id]["enabled"]:
                    return f"Monitoring already enabled for {session_name}"
                else:
                    # Simulate enabling
                    return f"""Monitoring Enabled
==================
Target: {session_name}
Status: ✅ Active
Thresholds: Using global settings
Alert Count: {state['sessions'].get(session_id, {}).get('alerts', 0)}

Monitoring will track:
• Error rates and patterns
• Response time metrics
• Stall detection
• Tool execution failures"""
            else:
                return f"""Monitoring Enabled
==================
Target: {session_name}
Status: ✅ Active (New Session)
Thresholds: Using global settings

Session will be monitored for all standard patterns."""
        else:
            # Enable globally
            if state["global"]["enabled"]:
                return "Global monitoring is already enabled"
            else:
                return """Global Monitoring Enabled
========================
Status: ✅ Active
Sessions Affected: All current and future sessions

Current Thresholds:
• Error Rate: {:.0%}
• Response Time: {}ms
• Stall Detection: {}s""".format(
                    state["global"]["thresholds"]["error_rate"],
                    state["global"]["thresholds"]["response_time"],
                    state["global"]["thresholds"]["stall_detection"]
                )
    
    def _disable_monitoring(self, state: Dict[str, Any], session_id: Optional[str]) -> str:
        """Disable monitoring"""
        if session_id:
            session_name = f"Session {session_id}"
            return f"""Monitoring Disabled
===================
Target: {session_name}
Status: ⏸️ Paused
Active Alerts: {state['sessions'].get(session_id, {}).get('alerts', 0)}

Note: Existing alerts remain but no new issues will be detected."""
        else:
            active_sessions = sum(1 for s in state["sessions"].values() if s["enabled"])
            return f"""Global Monitoring Disabled
=========================
Status: ⏸️ Paused
Sessions Affected: {active_sessions}
Pending Alerts: {len(state['global']['alerts'])}

Warning: No new issues will be detected until monitoring is re-enabled."""
    
    def _get_monitoring_status(self, state: Dict[str, Any], session_id: Optional[str]) -> str:
        """Get monitoring status"""
        if session_id:
            # Status for specific session
            session_data = state["sessions"].get(session_id, {"enabled": False, "alerts": 0})
            status = "✅ Active" if session_data["enabled"] else "⏸️ Paused"
            
            return f"""Monitoring Status - Session {session_id}
====================================
Status: {status}
Active Alerts: {session_data['alerts']}
Custom Thresholds: {len(session_data.get('custom_thresholds', {}))}

Using Thresholds:
• Error Rate: {state['global']['thresholds']['error_rate']:.0%}
• Response Time: {state['global']['thresholds']['response_time']}ms
• Stall Detection: {state['global']['thresholds']['stall_detection']}s"""
        else:
            # Global status
            total_sessions = len(state["sessions"])
            active_sessions = sum(1 for s in state["sessions"].values() if s["enabled"])
            total_alerts = len(state["global"]["alerts"])
            
            status = "✅ Active" if state["global"]["enabled"] else "⏸️ Paused"
            
            report = f"""Global Monitoring Status
=======================
Status: {status}
Active Sessions: {active_sessions}/{total_sessions}
Total Alerts: {total_alerts}

Current Thresholds:
------------------
• Error Rate: {state['global']['thresholds']['error_rate']:.0%}
• Response Time: {state['global']['thresholds']['response_time']}ms
• Stall Detection: {state['global']['thresholds']['stall_detection']}s"""
            
            if total_alerts > 0:
                report += "\n\nRecent Alerts:\n-------------"
                for alert in state["global"]["alerts"][:3]:  # Show top 3
                    report += f"\n• [{alert['severity'].upper()}] {alert['type']} in {alert['session_id']}"
            
            return report
    
    def _set_threshold(self, state: Dict[str, Any], threshold_type: Optional[str], threshold_value: Optional[float]) -> str:
        """Set monitoring threshold"""
        if not threshold_type or threshold_value is None:
            return "Error: Both threshold_type and threshold_value are required for set_threshold action"
        
        if threshold_type not in ["error_rate", "response_time", "stall_detection"]:
            return f"Error: Invalid threshold_type '{threshold_type}'"
        
        # Validate threshold values
        if threshold_type == "error_rate" and not (0 <= threshold_value <= 1):
            return "Error: error_rate must be between 0 and 1"
        elif threshold_type == "response_time" and threshold_value <= 0:
            return "Error: response_time must be positive"
        elif threshold_type == "stall_detection" and threshold_value <= 0:
            return "Error: stall_detection must be positive"
        
        old_value = state["global"]["thresholds"][threshold_type]
        
        # Format based on type
        if threshold_type == "error_rate":
            old_formatted = f"{old_value:.0%}"
            new_formatted = f"{threshold_value:.0%}"
        elif threshold_type == "response_time":
            old_formatted = f"{old_value}ms"
            new_formatted = f"{threshold_value}ms"
        else:  # stall_detection
            old_formatted = f"{old_value}s"
            new_formatted = f"{threshold_value}s"
        
        return f"""Threshold Updated
================
Type: {threshold_type.replace('_', ' ').title()}
Previous: {old_formatted}
New: {new_formatted}
Status: ✅ Applied

This change affects all sessions using global thresholds."""
    
    def _clear_alerts(self, state: Dict[str, Any], session_id: Optional[str]) -> str:
        """Clear monitoring alerts"""
        if session_id:
            # Clear for specific session
            session_alerts = state["sessions"].get(session_id, {}).get("alerts", 0)
            if session_alerts == 0:
                return f"No alerts to clear for session {session_id}"
            
            return f"""Alerts Cleared
=============
Session: {session_id}
Cleared: {session_alerts} alert(s)
Status: ✅ Complete

The session monitoring continues with a clean slate."""
        else:
            # Clear all alerts
            total_alerts = len(state["global"]["alerts"])
            if total_alerts == 0:
                return "No alerts to clear"
            
            # Group alerts by type
            alert_types = {}
            for alert in state["global"]["alerts"]:
                alert_types[alert["type"]] = alert_types.get(alert["type"], 0) + 1
            
            report = f"""All Alerts Cleared
==================
Total Cleared: {total_alerts}
Status: ✅ Complete

Cleared Alert Types:"""
            
            for alert_type, count in alert_types.items():
                report += f"\n• {alert_type}: {count}"
            
            report += "\n\nMonitoring continues with all alerts reset."
            
            return report