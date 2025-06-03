"""
Integration module for Debbie the Debugger.
Ties together monitoring, intervention, and interception systems.
"""

from typing import Any, Dict, Optional

import logging
from datetime import datetime

from ai_whisperer.extensions.conversation_replay.monitoring import DebbieMonitor, AnomalyAlert
from ai_whisperer.extensions.conversation_replay.intervention import InterventionOrchestrator, InterventionConfig
from ai_whisperer.extensions.conversation_replay.websocket_interceptor import WebSocketInterceptor
from ai_whisperer.extensions.monitoring.debbie_logger import DebbieLogger
from ai_whisperer.extensions.monitoring.log_aggregator import LogAggregator

logger = logging.getLogger(__name__)

class DebbieDebugger:
    """
    Main integration point for Debbie's debugging capabilities.
    Coordinates monitoring, intervention, and logging systems.
    """
    
    def __init__(self, session_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Debbie's debugging system.
        
        Args:
            session_manager: The session manager to monitor
            config: Configuration dictionary
        """
        self.session_manager = session_manager
        self.config = config or {}
        
        # Initialize components
        self.debbie_logger = DebbieLogger("debbie.main")
        self.log_aggregator = LogAggregator()
        
        # Create intervention config
        intervention_config = InterventionConfig(**self.config.get('intervention', {}))
        
        # Initialize systems
        self.monitor = DebbieMonitor(
            session_manager=session_manager,
            intervention_callback=self._handle_intervention_request
        )
        
        self.orchestrator = InterventionOrchestrator(
            session_manager=session_manager,
            config=intervention_config
        )
        
        self.interceptor = WebSocketInterceptor(
            monitor=self.monitor,
            log_aggregator=self.log_aggregator
        )
        
        # State
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Configure monitor
        if 'monitoring' in self.config:
            self.monitor.config.update(self.config['monitoring'])
    
    async def start(self):
        """Start Debbie's debugging system"""
        if self.is_running:
            return
        
        self.debbie_logger.info("Starting Debbie's debugging system")
        self.start_time = datetime.now()
        
        # Start components
        await self.orchestrator.start()
        
        self.is_running = True
        
        self.debbie_logger.info("Debbie is now monitoring and ready to help debug!")
    
    async def stop(self):
        """Stop Debbie's debugging system"""
        if not self.is_running:
            return
        
        self.debbie_logger.info("Stopping Debbie's debugging system")
        
        # Stop components
        await self.orchestrator.stop()
        await self.monitor.shutdown()
        
        self.is_running = False
        
        # Log final statistics
        stats = self.get_statistics()
        self.debbie_logger.info(
            "Debbie's debugging session complete",
            details=stats
        )
    
    async def _handle_intervention_request(self, alert: AnomalyAlert):
        """Handle intervention request from monitor"""
        self.debbie_logger.info(
            f"Intervention requested for {alert.alert_type}",
            session_id=alert.session_id,
            details={'alert': alert.to_dict()}
        )
        
        # Queue intervention
        await self.orchestrator.request_intervention(alert)
    
    def intercept_websocket(self, connection):
        """
        Wrap a WebSocket connection with interception.
        
        Args:
            connection: Original WebSocket connection
            
        Returns:
            Intercepting WebSocket wrapper
        """
        return self.interceptor.create_intercepting_connection(connection)
    
    async def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a session.
        
        Args:
            session_id: Session to analyze
            
        Returns:
            Analysis results
        """
        results = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': None,
            'logs': None,
            'interventions': None,
            'recommendations': []
        }
        
        # Get session metrics
        metrics = self.monitor.get_session_metrics(session_id)
        if metrics:
            results['metrics'] = metrics
        
        # Get recent logs
        logs = self.log_aggregator.get_logs(
            session_id=session_id,
            limit=100
        )
        results['logs'] = {
            'count': len(logs),
            'recent': logs[-10:] if logs else []
        }
        
        # Get intervention history
        intervention_history = self.orchestrator.executor.history.get_session_history(session_id)
        results['interventions'] = {
            'count': len(intervention_history),
            'success_rate': sum(1 for i in intervention_history if i.result.value == 'success') / len(intervention_history) if intervention_history else 0,
            'recent': [i.to_dict() for i in intervention_history[-5:]]
        }
        
        # Generate recommendations
        if metrics:
            if metrics.get('error_count', 0) > 5:
                results['recommendations'].append("High error rate detected. Review error logs for patterns.")
            
            if metrics.get('stall_count', 0) > 2:
                results['recommendations'].append("Multiple stalls detected. Consider updating agent continuation configuration.")
            
            if metrics.get('intervention_count', 0) > 5:
                results['recommendations'].append("Many interventions required. Session may need manual review.")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        return {
            'uptime_seconds': uptime,
            'is_running': self.is_running,
            'monitor_stats': {
                'monitored_sessions': len(self.monitor.monitored_sessions),
                'total_alerts': sum(m.stall_count + m.error_count for m in self.monitor.monitored_sessions.values())
            },
            'intervention_stats': self.orchestrator.get_stats(),
            'interceptor_stats': self.interceptor.get_statistics(),
            'log_stats': self.log_aggregator.get_statistics()
        }
    
    def get_debugging_report(self) -> str:
        """Generate a comprehensive debugging report"""
        stats = self.get_statistics()
        
        report = "# Debbie's Debugging Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"**Uptime:** {stats['uptime_seconds']:.1f} seconds\n\n"
        
        # Monitoring summary
        report += "## Monitoring Summary\n"
        monitor_stats = stats['monitor_stats']
        report += f"- Active Sessions: {monitor_stats['monitored_sessions']}\n"
        report += f"- Total Alerts: {monitor_stats['total_alerts']}\n\n"
        
        # Intervention summary
        report += "## Intervention Summary\n"
        intervention_stats = stats['intervention_stats']['executor_stats']
        report += f"- Total Interventions: {intervention_stats.get('total_interventions', 0)}\n"
        report += f"- Success Rate: {intervention_stats.get('overall_success_rate', 0):.1%}\n\n"
        
        # Strategy performance
        if 'strategy_stats' in intervention_stats:
            report += "### Strategy Performance\n"
            for strategy, stats in intervention_stats['strategy_stats'].items():
                if stats.get('total', 0) > 0:
                    report += f"- **{strategy}**: {stats.get('success_rate', 0):.1%} success ({stats['total']} attempts)\n"
            report += "\n"
        
        # WebSocket statistics
        report += "## WebSocket Analysis\n"
        ws_stats = stats['interceptor_stats']
        report += f"- Messages Intercepted: {ws_stats['message_count']}\n"
        report += f"- Messages/Second: {ws_stats['messages_per_second']:.2f}\n"
        report += f"- Active Sessions: {ws_stats['active_sessions']}\n\n"
        
        # Performance metrics
        if ws_stats['method_performance']:
            report += "### Method Performance\n"
            for method, perf in ws_stats['method_performance'].items():
                report += f"- **{method}**: avg {perf['avg_ms']:.0f}ms (calls: {perf['count']})\n"
            report += "\n"
        
        # Log statistics
        report += "## Log Statistics\n"
        log_stats = stats['log_stats']
        report += f"- Total Logs: {log_stats['total_logs']}\n"
        report += f"- Buffer Usage: {log_stats['buffer_usage']}\n"
        report += f"- Correlation Groups: {log_stats['correlation_groups']}\n\n"
        
        # Source distribution
        if log_stats['source_counts']:
            report += "### Log Sources\n"
            for source, count in log_stats['source_counts'].items():
                report += f"- {source}: {count}\n"
        
        return report

class DebbieFactory:
    """Factory for creating Debbie instances with different configurations"""
    
    @staticmethod
    def create_default(session_manager=None) -> DebbieDebugger:
        """Create Debbie with default configuration"""
        config = {
            'monitoring': {
                'check_interval_seconds': 5,
                'stall_threshold_seconds': 30,
                'auto_intervention': True,
                'max_interventions_per_session': 10
            },
            'intervention': {
                'auto_continue': True,
                'max_retries': 3,
                'retry_delay_seconds': 2.0
            }
        }
        return DebbieDebugger(session_manager, config)
    
    @staticmethod
    def create_aggressive(session_manager=None) -> DebbieDebugger:
        """Create Debbie with aggressive intervention settings"""
        config = {
            'monitoring': {
                'check_interval_seconds': 2,
                'stall_threshold_seconds': 15,
                'auto_intervention': True,
                'max_interventions_per_session': 20
            },
            'intervention': {
                'auto_continue': True,
                'max_retries': 5,
                'retry_delay_seconds': 1.0,
                'escalation_threshold': 5
            }
        }
        return DebbieDebugger(session_manager, config)
    
    @staticmethod
    def create_passive(session_manager=None) -> DebbieDebugger:
        """Create Debbie with passive monitoring only"""
        config = {
            'monitoring': {
                'check_interval_seconds': 10,
                'stall_threshold_seconds': 60,
                'auto_intervention': False,
                'max_interventions_per_session': 0
            },
            'intervention': {
                'auto_continue': False
            }
        }
        return DebbieDebugger(session_manager, config)

async def integrate_debbie_with_batch_client(batch_client, debbie: DebbieDebugger):
    """
    Integrate Debbie with an existing batch client.
    
    Args:
        batch_client: The batch client instance
        debbie: Debbie debugger instance
    """
    # Start Debbie
    await debbie.start()
    
    # Wrap WebSocket connection if it exists
    if hasattr(batch_client, 'ws_client') and batch_client.ws_client:
        if hasattr(batch_client.ws_client, 'connection'):
            # Replace connection with intercepting version
            batch_client.ws_client.connection = debbie.intercept_websocket(
                batch_client.ws_client.connection
            )
    
    # Add cleanup
    original_cleanup = None
    if hasattr(batch_client, 'cleanup'):
        original_cleanup = batch_client.cleanup
    
    async def enhanced_cleanup():
        """Enhanced cleanup that stops Debbie"""
        if original_cleanup:
            await original_cleanup()
        await debbie.stop()
    
    batch_client.cleanup = enhanced_cleanup
    
    return batch_client
