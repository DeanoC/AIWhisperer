"""
Automated intervention system for Debbie the Debugger.
Implements recovery strategies and intervention policies.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import uuid

from ..logging_custom import EnhancedLogMessage, LogLevel, LogSource, ComponentType
from ..logging.debbie_logger import DebbieLogger
from ..tools.message_injector_tool import MessageInjectorTool, InjectionType
from ..tools.session_inspector_tool import SessionInspectorTool
from ..tools.python_executor_tool import PythonExecutorTool
from .monitoring import AnomalyAlert

logger = logging.getLogger(__name__)


class InterventionStrategy(Enum):
    """Types of intervention strategies"""
    PROMPT_INJECTION = "prompt_injection"
    SESSION_RESTART = "session_restart"
    STATE_RESET = "state_reset"
    TOOL_RETRY = "tool_retry"
    ESCALATE = "escalate"
    PYTHON_SCRIPT = "python_script"
    CUSTOM = "custom"


class InterventionResult(Enum):
    """Result of an intervention attempt"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    SKIPPED = "skipped"
    ESCALATED = "escalated"


@dataclass
class InterventionConfig:
    """Configuration for intervention behavior"""
    auto_continue: bool = True
    max_retries: int = 3
    retry_delay_seconds: float = 2.0
    escalation_threshold: int = 3  # Failed interventions before escalation
    
    # Strategy-specific configs
    prompt_injection_config: Dict[str, Any] = field(default_factory=lambda: {
        'timeout_seconds': 10,
        'wait_for_response': True,
        'templates': {
            'continuation': [
                "Please continue with the task based on the previous results.",
                "Continue processing. If you're waiting for input, use the available information to proceed.",
                "The tool execution is complete. Please analyze the results and continue."
            ],
            'error_recovery': [
                "An error occurred. Please try a different approach.",
                "The previous attempt failed. Can you find an alternative solution?",
                "Let's recover from this error. What other options do we have?"
            ]
        }
    })
    
    session_restart_config: Dict[str, Any] = field(default_factory=lambda: {
        'preserve_context': True,
        'max_restart_attempts': 2
    })
    
    python_script_config: Dict[str, Any] = field(default_factory=lambda: {
        'timeout': 30,
        'scripts': {
            'analyze_stall': 'find_stalls',
            'check_performance': 'analyze_performance',
            'diagnose_errors': 'error_analysis'
        }
    })
    
    # Alert type to strategy mapping
    alert_strategy_map: Dict[str, List[InterventionStrategy]] = field(default_factory=lambda: {
        'session_stall': [InterventionStrategy.PROMPT_INJECTION, InterventionStrategy.SESSION_RESTART],
        'tool_loop': [InterventionStrategy.STATE_RESET, InterventionStrategy.ESCALATE],
        'high_error_rate': [InterventionStrategy.TOOL_RETRY, InterventionStrategy.PYTHON_SCRIPT],
        'slow_response': [InterventionStrategy.PYTHON_SCRIPT, InterventionStrategy.ESCALATE],
        'memory_spike': [InterventionStrategy.STATE_RESET, InterventionStrategy.SESSION_RESTART]
    })


@dataclass
class InterventionRecord:
    """Record of an intervention attempt"""
    intervention_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    alert: Optional[AnomalyAlert] = None
    strategy: InterventionStrategy = InterventionStrategy.PROMPT_INJECTION
    timestamp: datetime = field(default_factory=datetime.now)
    result: InterventionResult = InterventionResult.SKIPPED
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['strategy'] = self.strategy.value
        data['result'] = self.result.value
        if self.alert:
            data['alert'] = self.alert.to_dict()
        return data


class InterventionHistory:
    """Tracks intervention history and patterns"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.records: List[InterventionRecord] = []
        self.session_interventions: Dict[str, List[InterventionRecord]] = {}
        self.strategy_success_rates: Dict[InterventionStrategy, Dict[str, int]] = {}
        
    def add_record(self, record: InterventionRecord):
        """Add intervention record"""
        self.records.append(record)
        
        # Maintain size limit
        if len(self.records) > self.max_history:
            self.records = self.records[-self.max_history:]
        
        # Track by session
        if record.session_id not in self.session_interventions:
            self.session_interventions[record.session_id] = []
        self.session_interventions[record.session_id].append(record)
        
        # Update success rates
        self._update_success_rate(record)
    
    def _update_success_rate(self, record: InterventionRecord):
        """Update strategy success rate statistics"""
        if record.strategy not in self.strategy_success_rates:
            self.strategy_success_rates[record.strategy] = {
                'total': 0,
                'success': 0,
                'partial': 0,
                'failure': 0
            }
        
        stats = self.strategy_success_rates[record.strategy]
        stats['total'] += 1
        
        if record.result == InterventionResult.SUCCESS:
            stats['success'] += 1
        elif record.result == InterventionResult.PARTIAL_SUCCESS:
            stats['partial'] += 1
        elif record.result == InterventionResult.FAILURE:
            stats['failure'] += 1
    
    def get_session_history(self, session_id: str) -> List[InterventionRecord]:
        """Get intervention history for a session"""
        return self.session_interventions.get(session_id, [])
    
    def get_strategy_stats(self, strategy: InterventionStrategy) -> Dict[str, Any]:
        """Get success statistics for a strategy"""
        stats = self.strategy_success_rates.get(strategy, {})
        if stats and stats.get('total', 0) > 0:
            success_rate = (stats.get('success', 0) + 0.5 * stats.get('partial', 0)) / stats['total']
            stats['success_rate'] = success_rate
        return stats
    
    def get_recent_interventions(self, limit: int = 10) -> List[InterventionRecord]:
        """Get recent intervention records"""
        return self.records[-limit:]


class InterventionExecutor:
    """Executes intervention strategies"""
    
    def __init__(self, session_manager=None, config: Optional[InterventionConfig] = None):
        """
        Initialize executor.
        
        Args:
            session_manager: Session manager for interventions
            config: Intervention configuration
        """
        self.session_manager = session_manager
        self.config = config or InterventionConfig()
        
        # Tools
        self.message_injector = MessageInjectorTool(session_manager)
        self.session_inspector = SessionInspectorTool(session_manager)
        self.python_executor = PythonExecutorTool()
        
        # State
        self.debbie_logger = DebbieLogger("debbie.intervention")
        self.history = InterventionHistory()
        self.active_interventions: Dict[str, InterventionRecord] = {}
        
        # Strategy handlers
        self.strategy_handlers = {
            InterventionStrategy.PROMPT_INJECTION: self._execute_prompt_injection,
            InterventionStrategy.SESSION_RESTART: self._execute_session_restart,
            InterventionStrategy.STATE_RESET: self._execute_state_reset,
            InterventionStrategy.TOOL_RETRY: self._execute_tool_retry,
            InterventionStrategy.ESCALATE: self._execute_escalation,
            InterventionStrategy.PYTHON_SCRIPT: self._execute_python_script,
        }
    
    async def intervene(self, alert: AnomalyAlert) -> InterventionRecord:
        """
        Execute intervention based on alert.
        
        Args:
            alert: The anomaly alert triggering intervention
            
        Returns:
            Record of the intervention attempt
        """
        # Create intervention record
        record = InterventionRecord(
            session_id=alert.session_id,
            alert=alert
        )
        
        try:
            # Log intervention start
            self.debbie_logger.info(
                f"Starting intervention for {alert.alert_type}",
                session_id=alert.session_id,
                details={'alert': alert.to_dict()}
            )
            
            # Get strategies for this alert type
            strategies = self.config.alert_strategy_map.get(
                alert.alert_type,
                [InterventionStrategy.PROMPT_INJECTION]  # Default
            )
            
            # Try strategies in order
            for strategy in strategies:
                record.strategy = strategy
                record.timestamp = datetime.now()
                
                # Check if we should skip based on history
                if self._should_skip_strategy(alert.session_id, strategy):
                    self.debbie_logger.info(
                        f"Skipping {strategy.value} due to recent failures",
                        session_id=alert.session_id
                    )
                    continue
                
                # Execute strategy
                start_time = time.time()
                success = await self._execute_strategy(strategy, alert, record)
                record.duration_ms = (time.time() - start_time) * 1000
                
                if success:
                    record.result = InterventionResult.SUCCESS
                    break
                else:
                    record.result = InterventionResult.FAILURE
                    
                    # Add retry delay
                    if strategy != strategies[-1]:  # Not the last strategy
                        await asyncio.sleep(self.config.retry_delay_seconds)
            
            # If all strategies failed, mark as escalated
            if record.result == InterventionResult.FAILURE and len(strategies) > 1:
                record.result = InterventionResult.ESCALATED
            
        except Exception as e:
            logger.error(f"Error during intervention: {e}")
            record.result = InterventionResult.FAILURE
            record.error = str(e)
        
        finally:
            # Record intervention
            self.history.add_record(record)
            
            # Log result
            self.debbie_logger.info(
                f"Intervention completed: {record.result.value}",
                session_id=alert.session_id,
                details=record.to_dict()
            )
        
        return record
    
    def _should_skip_strategy(self, session_id: str, strategy: InterventionStrategy) -> bool:
        """Check if we should skip a strategy based on recent failures"""
        recent_records = self.history.get_session_history(session_id)[-5:]
        
        # Count recent failures for this strategy
        recent_failures = sum(
            1 for r in recent_records
            if r.strategy == strategy and r.result == InterventionResult.FAILURE
        )
        
        # Skip if too many recent failures
        return recent_failures >= 2
    
    async def _execute_strategy(self, strategy: InterventionStrategy, 
                               alert: AnomalyAlert,
                               record: InterventionRecord) -> bool:
        """Execute a specific intervention strategy"""
        handler = self.strategy_handlers.get(strategy)
        
        if not handler:
            logger.error(f"No handler for strategy: {strategy}")
            return False
        
        try:
            return await handler(alert, record)
        except Exception as e:
            logger.error(f"Error executing {strategy}: {e}")
            record.error = str(e)
            return False
    
    async def _execute_prompt_injection(self, alert: AnomalyAlert, 
                                      record: InterventionRecord) -> bool:
        """Execute prompt injection strategy"""
        config = self.config.prompt_injection_config
        
        # Determine injection type based on alert
        injection_type = InjectionType.CONTINUATION
        if 'error' in alert.alert_type:
            injection_type = InjectionType.ERROR_RECOVERY
        
        # Get appropriate template
        templates = config['templates'].get(injection_type.value, [])
        if templates:
            # Rotate through templates
            template_index = len(self.history.get_session_history(alert.session_id)) % len(templates)
            message = templates[template_index]
        else:
            message = ""
        
        # Inject message
        result = self.message_injector.execute(
            session_id=alert.session_id,
            message=message,
            injection_type=injection_type.value,
            wait_for_response=config['wait_for_response'],
            timeout_seconds=config['timeout_seconds']
        )
        
        # Check result
        if result.get('success') and result.get('result', {}).get('response_received'):
            record.details['injection_result'] = result['result']
            
            # Verify recovery
            await asyncio.sleep(2)  # Brief wait
            inspection = self.session_inspector.execute(
                session_id=alert.session_id,
                time_window_minutes=1
            )
            
            if inspection.get('success'):
                analysis = inspection.get('analysis', {})
                if not analysis.get('stall_detected'):
                    self.debbie_logger.comment(
                        level=LogLevel.INFO,
                        comment="Prompt injection successful - agent resumed activity",
                        context={'session_id': alert.session_id}
                    )
                    return True
        
        return False
    
    async def _execute_session_restart(self, alert: AnomalyAlert, 
                                     record: InterventionRecord) -> bool:
        """Execute session restart strategy"""
        config = self.config.session_restart_config
        
        # This would interact with session manager to restart
        # For now, log the intention
        self.debbie_logger.warning(
            "Session restart requested",
            session_id=alert.session_id,
            details={
                'preserve_context': config['preserve_context'],
                'reason': alert.message
            }
        )
        
        # In a real implementation, this would:
        # 1. Save current context/state
        # 2. Gracefully end current session
        # 3. Start new session with saved context
        # 4. Verify new session is healthy
        
        record.details['restart_requested'] = True
        record.details['preserve_context'] = config['preserve_context']
        
        # For now, return partial success
        record.result = InterventionResult.PARTIAL_SUCCESS
        return False
    
    async def _execute_state_reset(self, alert: AnomalyAlert, 
                                 record: InterventionRecord) -> bool:
        """Execute state reset strategy"""
        # Reset specific problematic state while preserving context
        self.debbie_logger.info(
            "Executing state reset",
            session_id=alert.session_id
        )
        
        # Inject a reset message
        result = self.message_injector.execute(
            session_id=alert.session_id,
            injection_type="reset",
            message="Let's reset and approach this differently. Please summarize the current state and continue."
        )
        
        record.details['reset_result'] = result
        return result.get('success', False)
    
    async def _execute_tool_retry(self, alert: AnomalyAlert, 
                                 record: InterventionRecord) -> bool:
        """Execute tool retry strategy"""
        # This would analyze the failed tool execution and retry with modifications
        self.debbie_logger.info(
            "Attempting tool retry with modifications",
            session_id=alert.session_id
        )
        
        # Analyze recent errors
        python_result = await self._execute_python_analysis(
            alert.session_id,
            'error_analysis'
        )
        
        if python_result and python_result.get('success'):
            # Based on analysis, inject retry suggestion
            result = self.message_injector.execute(
                session_id=alert.session_id,
                message="The previous tool execution failed. Try again with different parameters or use an alternative approach.",
                injection_type="error_recovery"
            )
            
            record.details['retry_suggested'] = True
            return result.get('success', False)
        
        return False
    
    async def _execute_escalation(self, alert: AnomalyAlert, 
                                record: InterventionRecord) -> bool:
        """Execute escalation strategy"""
        self.debbie_logger.critical(
            f"Escalating intervention for {alert.alert_type}",
            session_id=alert.session_id,
            details={
                'alert': alert.to_dict(),
                'previous_attempts': len(self.history.get_session_history(alert.session_id))
            }
        )
        
        # In a real system, this might:
        # - Notify human operators
        # - Trigger more aggressive recovery
        # - Log to external monitoring system
        
        record.details['escalated'] = True
        record.details['escalation_reason'] = "Multiple intervention failures"
        
        return False  # Escalation doesn't resolve the issue directly
    
    async def _execute_python_script(self, alert: AnomalyAlert, 
                                   record: InterventionRecord) -> bool:
        """Execute Python script for analysis and intervention"""
        config = self.config.python_script_config
        
        # Select appropriate script based on alert type
        script_map = {
            'session_stall': 'analyze_stall',
            'slow_response': 'check_performance',
            'high_error_rate': 'diagnose_errors'
        }
        
        script_name = script_map.get(alert.alert_type, 'analyze_performance')
        template = config['scripts'].get(script_name)
        
        if template:
            result = await self._execute_python_analysis(
                alert.session_id,
                template
            )
            
            if result and result.get('success'):
                record.details['python_analysis'] = result.get('result', {})
                
                # Log insights from analysis
                output = result.get('result', {}).get('output', '')
                if output:
                    self.debbie_logger.comment(
                        level=LogLevel.INFO,
                        comment=f"Python analysis completed:\n{output[:500]}",
                        context={'session_id': alert.session_id}
                    )
                
                return True
        
        return False
    
    async def _execute_python_analysis(self, session_id: str, 
                                     template: str) -> Optional[Dict[str, Any]]:
        """Execute Python analysis script"""
        try:
            result = self.python_executor.execute(
                use_template=template,
                context={
                    'session_id': session_id,
                    'include_logs': True,
                    'include_state': True
                },
                timeout=self.config.python_script_config['timeout']
            )
            return result
        except Exception as e:
            logger.error(f"Error executing Python analysis: {e}")
            return None
    
    def get_intervention_stats(self) -> Dict[str, Any]:
        """Get intervention statistics"""
        stats = {
            'total_interventions': len(self.history.records),
            'active_interventions': len(self.active_interventions),
            'strategy_stats': {}
        }
        
        # Get stats for each strategy
        for strategy in InterventionStrategy:
            strategy_stats = self.history.get_strategy_stats(strategy)
            if strategy_stats:
                stats['strategy_stats'][strategy.value] = strategy_stats
        
        # Calculate overall success rate
        total = len(self.history.records)
        if total > 0:
            success_count = sum(
                1 for r in self.history.records
                if r.result in [InterventionResult.SUCCESS, InterventionResult.PARTIAL_SUCCESS]
            )
            stats['overall_success_rate'] = success_count / total
        
        return stats


class InterventionOrchestrator:
    """Orchestrates monitoring and intervention systems"""
    
    def __init__(self, session_manager=None, config: Optional[InterventionConfig] = None):
        """
        Initialize orchestrator.
        
        Args:
            session_manager: Session manager
            config: Intervention configuration
        """
        self.session_manager = session_manager
        self.config = config or InterventionConfig()
        
        # Components
        self.executor = InterventionExecutor(session_manager, config)
        self.debbie_logger = DebbieLogger("debbie.orchestrator")
        
        # State
        self.intervention_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.is_running = False
    
    async def start(self):
        """Start the orchestrator"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._process_interventions())
        
        self.debbie_logger.info("Intervention orchestrator started")
    
    async def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        self.debbie_logger.info("Intervention orchestrator stopped")
    
    async def request_intervention(self, alert: AnomalyAlert):
        """Request an intervention for an alert"""
        if not self.config.auto_continue:
            self.debbie_logger.info(
                "Auto-intervention disabled, skipping",
                session_id=alert.session_id
            )
            return
        
        # Add to queue
        await self.intervention_queue.put(alert)
    
    async def _process_interventions(self):
        """Process intervention queue"""
        while self.is_running:
            try:
                # Wait for alert with timeout
                alert = await asyncio.wait_for(
                    self.intervention_queue.get(),
                    timeout=1.0
                )
                
                # Execute intervention
                await self.executor.intervene(alert)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing intervention: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            'queue_size': self.intervention_queue.qsize(),
            'is_running': self.is_running,
            'executor_stats': self.executor.get_intervention_stats()
        }