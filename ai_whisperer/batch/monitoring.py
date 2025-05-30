"""
Real-time monitoring system for Debbie the Debugger.
Monitors AI sessions for anomalies, stalls, and performance issues.
"""

import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
from collections import deque, defaultdict

from ..logging_custom import EnhancedLogMessage, LogLevel, LogSource, ComponentType
from ..logging.debbie_logger import DebbieLogger
from ..logging.log_aggregator import LogAggregator
from ..tools.session_inspector_tool import SessionInspectorTool
from ..tools.message_injector_tool import MessageInjectorTool

logger = logging.getLogger(__name__)


class MonitoringEvent(Enum):
    """Types of monitoring events"""
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TOOL_EXECUTION_START = "tool_execution_start"
    TOOL_EXECUTION_END = "tool_execution_end"
    AGENT_STALL_DETECTED = "agent_stall_detected"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_DETECTED = "error_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    INTERVENTION_TRIGGERED = "intervention_triggered"


@dataclass
class MonitoringMetrics:
    """Performance and health metrics for a session"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    message_count: int = 0
    tool_execution_count: int = 0
    error_count: int = 0
    intervention_count: int = 0
    avg_response_time_ms: float = 0.0
    response_times: List[float] = field(default_factory=list)
    memory_usage_mb: List[float] = field(default_factory=list)
    active_tools: Set[str] = field(default_factory=set)
    stall_count: int = 0
    
    def update_response_time(self, response_time_ms: float):
        """Update response time metrics"""
        self.response_times.append(response_time_ms)
        # Keep last 100 response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]
        self.avg_response_time_ms = statistics.mean(self.response_times)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        data['active_tools'] = list(self.active_tools)
        data['duration_seconds'] = (datetime.now() - self.start_time).total_seconds()
        return data


@dataclass
class AnomalyAlert:
    """Alert for detected anomaly"""
    alert_type: str
    severity: str  # "low", "medium", "high", "critical"
    session_id: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    requires_intervention: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'alert_type': self.alert_type,
            'severity': self.severity,
            'session_id': self.session_id,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'requires_intervention': self.requires_intervention
        }


class AnomalyDetector:
    """Detects anomalies in session behavior"""
    
    def __init__(self):
        self.baseline_metrics = {}
        self.anomaly_thresholds = {
            'response_time_multiplier': 2.0,  # 2x slower than baseline
            'error_rate_threshold': 0.2,      # 20% error rate
            'stall_duration_seconds': 30,     # 30s without activity
            'memory_spike_multiplier': 1.5,   # 50% above baseline
            'tool_loop_threshold': 5,         # Same tool 5+ times
        }
        
    def analyze(self, metrics: MonitoringMetrics, 
                recent_events: List[Dict[str, Any]]) -> List[AnomalyAlert]:
        """Analyze metrics and events for anomalies"""
        alerts = []
        
        # Check response time anomaly
        if metrics.avg_response_time_ms > 0:
            baseline = self.baseline_metrics.get(
                f"{metrics.session_id}_response_time", 
                metrics.avg_response_time_ms
            )
            if metrics.avg_response_time_ms > baseline * self.anomaly_thresholds['response_time_multiplier']:
                alerts.append(AnomalyAlert(
                    alert_type="slow_response",
                    severity="medium",
                    session_id=metrics.session_id,
                    message=f"Response time degraded to {metrics.avg_response_time_ms:.0f}ms (baseline: {baseline:.0f}ms)",
                    details={
                        'current_avg': metrics.avg_response_time_ms,
                        'baseline': baseline,
                        'degradation_factor': metrics.avg_response_time_ms / baseline
                    }
                ))
        
        # Check error rate
        if metrics.message_count > 0:
            error_rate = metrics.error_count / metrics.message_count
            if error_rate > self.anomaly_thresholds['error_rate_threshold']:
                alerts.append(AnomalyAlert(
                    alert_type="high_error_rate",
                    severity="high",
                    session_id=metrics.session_id,
                    message=f"High error rate: {error_rate:.1%} ({metrics.error_count} errors)",
                    details={
                        'error_count': metrics.error_count,
                        'message_count': metrics.message_count,
                        'error_rate': error_rate
                    },
                    requires_intervention=True
                ))
        
        # Check for stalls
        time_since_activity = (datetime.now() - metrics.last_activity).total_seconds()
        if time_since_activity > self.anomaly_thresholds['stall_duration_seconds']:
            alerts.append(AnomalyAlert(
                alert_type="session_stall",
                severity="high",
                session_id=metrics.session_id,
                message=f"Session stalled for {time_since_activity:.0f} seconds",
                details={
                    'stall_duration': time_since_activity,
                    'last_activity': metrics.last_activity.isoformat()
                },
                requires_intervention=True
            ))
        
        # Check for tool loops
        tool_usage = self._analyze_tool_usage(recent_events)
        for tool, count in tool_usage.items():
            if count >= self.anomaly_thresholds['tool_loop_threshold']:
                alerts.append(AnomalyAlert(
                    alert_type="tool_loop",
                    severity="critical",
                    session_id=metrics.session_id,
                    message=f"Possible tool loop: '{tool}' executed {count} times",
                    details={
                        'tool_name': tool,
                        'execution_count': count
                    },
                    requires_intervention=True
                ))
        
        # Check memory usage
        if metrics.memory_usage_mb:
            current_memory = metrics.memory_usage_mb[-1]
            baseline_memory = statistics.mean(metrics.memory_usage_mb[:5]) if len(metrics.memory_usage_mb) > 5 else current_memory
            
            if current_memory > baseline_memory * self.anomaly_thresholds['memory_spike_multiplier']:
                alerts.append(AnomalyAlert(
                    alert_type="memory_spike",
                    severity="medium",
                    session_id=metrics.session_id,
                    message=f"Memory usage spike: {current_memory:.1f}MB",
                    details={
                        'current_memory_mb': current_memory,
                        'baseline_memory_mb': baseline_memory,
                        'spike_factor': current_memory / baseline_memory
                    }
                ))
        
        return alerts
    
    def _analyze_tool_usage(self, recent_events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze tool usage patterns"""
        tool_counts = defaultdict(int)
        
        # Look at last 50 events
        for event in recent_events[-50:]:
            if event.get('action') == 'tool_execution_start':
                tool_name = event.get('details', {}).get('tool_name')
                if tool_name:
                    tool_counts[tool_name] += 1
        
        return dict(tool_counts)
    
    def update_baseline(self, session_id: str, metric_name: str, value: float):
        """Update baseline metrics for comparison"""
        key = f"{session_id}_{metric_name}"
        if key not in self.baseline_metrics:
            self.baseline_metrics[key] = value
        else:
            # Exponential moving average
            alpha = 0.1
            self.baseline_metrics[key] = (alpha * value + 
                                         (1 - alpha) * self.baseline_metrics[key])


class DebbieMonitor:
    """Main monitoring system for Debbie"""
    
    def __init__(self, session_manager=None, intervention_callback: Optional[Callable] = None):
        """
        Initialize monitor.
        
        Args:
            session_manager: The session manager to monitor
            intervention_callback: Callback for triggering interventions
        """
        self.session_manager = session_manager
        self.intervention_callback = intervention_callback
        
        # Components
        self.anomaly_detector = AnomalyDetector()
        self.metrics_collector = MetricsCollector()
        self.debbie_logger = DebbieLogger("debbie.monitor")
        self.log_aggregator = LogAggregator()
        
        # Tools
        self.session_inspector = SessionInspectorTool(session_manager)
        self.message_injector = MessageInjectorTool(session_manager)
        
        # State
        self.monitored_sessions: Dict[str, MonitoringMetrics] = {}
        self.event_handlers: Dict[MonitoringEvent, List[Callable]] = defaultdict(list)
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.is_monitoring = True
        
        # Configuration
        self.config = {
            'check_interval_seconds': 5,
            'stall_threshold_seconds': 30,
            'auto_intervention': True,
            'max_interventions_per_session': 10,
        }
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default event handlers"""
        self.register_handler(MonitoringEvent.SESSION_START, self._handle_session_start)
        self.register_handler(MonitoringEvent.SESSION_END, self._handle_session_end)
        self.register_handler(MonitoringEvent.MESSAGE_SENT, self._handle_message_sent)
        self.register_handler(MonitoringEvent.TOOL_EXECUTION_START, self._handle_tool_start)
        self.register_handler(MonitoringEvent.TOOL_EXECUTION_END, self._handle_tool_end)
        self.register_handler(MonitoringEvent.ERROR_DETECTED, self._handle_error)
        self.register_handler(MonitoringEvent.AGENT_STALL_DETECTED, self._handle_stall)
    
    def register_handler(self, event_type: MonitoringEvent, handler: Callable):
        """Register an event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def start_monitoring(self, session_id: str):
        """Start monitoring a session"""
        if session_id in self.monitored_sessions:
            return  # Already monitoring
        
        # Initialize metrics
        self.monitored_sessions[session_id] = MonitoringMetrics(session_id=session_id)
        
        # Start monitoring task
        task = asyncio.create_task(self._monitor_session(session_id))
        self.monitoring_tasks[session_id] = task
        
        # Emit event
        await self._emit_event(MonitoringEvent.SESSION_START, {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        })
        
        self.debbie_logger.info(f"Started monitoring session: {session_id}")
    
    async def stop_monitoring(self, session_id: str):
        """Stop monitoring a session"""
        if session_id not in self.monitored_sessions:
            return
        
        # Cancel monitoring task
        if session_id in self.monitoring_tasks:
            self.monitoring_tasks[session_id].cancel()
            del self.monitoring_tasks[session_id]
        
        # Emit event
        await self._emit_event(MonitoringEvent.SESSION_END, {
            'session_id': session_id,
            'metrics': self.monitored_sessions[session_id].to_dict()
        })
        
        # Clean up
        del self.monitored_sessions[session_id]
        
        self.debbie_logger.info(f"Stopped monitoring session: {session_id}")
    
    async def _monitor_session(self, session_id: str):
        """Main monitoring loop for a session"""
        while self.is_monitoring and session_id in self.monitored_sessions:
            try:
                # Get session metrics
                metrics = self.monitored_sessions[session_id]
                
                # Inspect session
                inspection_result = await self._inspect_session(session_id)
                
                # Get recent events
                recent_events = self.log_aggregator.get_logs(
                    session_id=session_id,
                    limit=100
                )
                
                # Check for anomalies
                alerts = self.anomaly_detector.analyze(metrics, recent_events)
                
                # Process alerts
                for alert in alerts:
                    await self._process_alert(alert)
                
                # Update metrics
                self._update_metrics_from_inspection(metrics, inspection_result)
                
                # Wait before next check
                await asyncio.sleep(self.config['check_interval_seconds'])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring session {session_id}: {e}")
                await asyncio.sleep(self.config['check_interval_seconds'])
    
    async def _inspect_session(self, session_id: str) -> Dict[str, Any]:
        """Inspect session state"""
        try:
            result = self.session_inspector.execute(
                session_id=session_id,
                include_message_history=True,
                time_window_minutes=5
            )
            return result
        except Exception as e:
            logger.error(f"Error inspecting session: {e}")
            return {}
    
    def _update_metrics_from_inspection(self, metrics: MonitoringMetrics, 
                                      inspection: Dict[str, Any]):
        """Update metrics based on inspection results"""
        if not inspection or not inspection.get('success'):
            return
        
        analysis = inspection.get('analysis', {})
        
        # Update activity time
        last_activity_str = analysis.get('last_activity')
        if last_activity_str:
            try:
                metrics.last_activity = datetime.fromisoformat(last_activity_str)
            except:
                pass
        
        # Update counts
        metrics.message_count = analysis.get('message_count', metrics.message_count)
        metrics.error_count = analysis.get('error_count', metrics.error_count)
        
        # Check for stalls
        if analysis.get('stall_detected'):
            metrics.stall_count += 1
    
    async def _process_alert(self, alert: AnomalyAlert):
        """Process an anomaly alert"""
        # Log the alert
        self.debbie_logger.warning(
            f"Anomaly detected: {alert.message}",
            session_id=alert.session_id,
            details=alert.details
        )
        
        # Add to log aggregator
        self.log_aggregator.add_log({
            'source': LogSource.DEBBIE.value,
            'level': LogLevel.WARNING.value,
            'component': ComponentType.MONITOR.value,
            'action': 'anomaly_detected',
            'event_summary': alert.message,
            'session_id': alert.session_id,
            'details': alert.to_dict()
        })
        
        # Emit event
        await self._emit_event(MonitoringEvent.ANOMALY_DETECTED, alert.to_dict())
        
        # Trigger intervention if needed
        if alert.requires_intervention and self.config['auto_intervention']:
            await self._trigger_intervention(alert)
    
    async def _trigger_intervention(self, alert: AnomalyAlert):
        """Trigger intervention based on alert"""
        session_id = alert.session_id
        metrics = self.monitored_sessions.get(session_id)
        
        if not metrics:
            return
        
        # Check intervention limit
        if metrics.intervention_count >= self.config['max_interventions_per_session']:
            self.debbie_logger.warning(
                f"Intervention limit reached for session {session_id}",
                session_id=session_id
            )
            return
        
        # Emit intervention event
        await self._emit_event(MonitoringEvent.INTERVENTION_TRIGGERED, {
            'session_id': session_id,
            'alert': alert.to_dict(),
            'intervention_count': metrics.intervention_count + 1
        })
        
        # Call intervention callback
        if self.intervention_callback:
            try:
                await self.intervention_callback(alert)
                metrics.intervention_count += 1
            except Exception as e:
                logger.error(f"Error triggering intervention: {e}")
    
    async def _emit_event(self, event_type: MonitoringEvent, data: Dict[str, Any]):
        """Emit monitoring event to handlers"""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    # Default event handlers
    async def _handle_session_start(self, data: Dict[str, Any]):
        """Handle session start event"""
        session_id = data['session_id']
        self.debbie_logger.info(f"Session started: {session_id}", session_id=session_id)
    
    async def _handle_session_end(self, data: Dict[str, Any]):
        """Handle session end event"""
        session_id = data['session_id']
        metrics = data.get('metrics', {})
        self.debbie_logger.info(
            f"Session ended: {session_id}",
            session_id=session_id,
            details=metrics
        )
    
    async def _handle_message_sent(self, data: Dict[str, Any]):
        """Handle message sent event"""
        session_id = data.get('session_id')
        if session_id in self.monitored_sessions:
            self.monitored_sessions[session_id].message_count += 1
            self.monitored_sessions[session_id].last_activity = datetime.now()
    
    async def _handle_tool_start(self, data: Dict[str, Any]):
        """Handle tool execution start"""
        session_id = data.get('session_id')
        tool_name = data.get('tool_name')
        
        if session_id in self.monitored_sessions:
            metrics = self.monitored_sessions[session_id]
            metrics.tool_execution_count += 1
            metrics.active_tools.add(tool_name)
            metrics.last_activity = datetime.now()
    
    async def _handle_tool_end(self, data: Dict[str, Any]):
        """Handle tool execution end"""
        session_id = data.get('session_id')
        tool_name = data.get('tool_name')
        duration_ms = data.get('duration_ms')
        
        if session_id in self.monitored_sessions:
            metrics = self.monitored_sessions[session_id]
            metrics.active_tools.discard(tool_name)
            
            if duration_ms:
                metrics.update_response_time(duration_ms)
    
    async def _handle_error(self, data: Dict[str, Any]):
        """Handle error event"""
        session_id = data.get('session_id')
        if session_id in self.monitored_sessions:
            self.monitored_sessions[session_id].error_count += 1
    
    async def _handle_stall(self, data: Dict[str, Any]):
        """Handle stall detection"""
        session_id = data.get('session_id')
        stall_duration = data.get('duration_seconds', 0)
        
        self.debbie_logger.comment(
            level=LogLevel.WARNING,
            comment=f"Stall detected in session {session_id}",
            context={
                'session_id': session_id,
                'duration': stall_duration,
                'action': 'investigating'
            }
        )
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current metrics for a session"""
        metrics = self.monitored_sessions.get(session_id)
        return metrics.to_dict() if metrics else None
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all monitored sessions"""
        return {
            session_id: metrics.to_dict()
            for session_id, metrics in self.monitored_sessions.items()
        }
    
    async def shutdown(self):
        """Shutdown monitoring system"""
        self.is_monitoring = False
        
        # Cancel all monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.monitoring_tasks:
            await asyncio.gather(*self.monitoring_tasks.values(), return_exceptions=True)
        
        self.monitoring_tasks.clear()
        self.monitored_sessions.clear()
        
        self.debbie_logger.info("Monitoring system shut down")


class MetricsCollector:
    """Collects and aggregates performance metrics"""
    
    def __init__(self):
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
    def record_metric(self, session_id: str, metric_name: str, value: float, 
                     timestamp: Optional[datetime] = None):
        """Record a metric value"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.metrics_history[f"{session_id}:{metric_name}"].append({
            'value': value,
            'timestamp': timestamp
        })
    
    def get_metric_stats(self, session_id: str, metric_name: str, 
                        time_window_minutes: int = 10) -> Dict[str, float]:
        """Get statistics for a metric"""
        key = f"{session_id}:{metric_name}"
        if key not in self.metrics_history:
            return {}
        
        # Filter by time window
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_values = [
            entry['value'] for entry in self.metrics_history[key]
            if entry['timestamp'] > cutoff_time
        ]
        
        if not recent_values:
            return {}
        
        return {
            'mean': statistics.mean(recent_values),
            'median': statistics.median(recent_values),
            'min': min(recent_values),
            'max': max(recent_values),
            'count': len(recent_values),
            'std_dev': statistics.stdev(recent_values) if len(recent_values) > 1 else 0
        }