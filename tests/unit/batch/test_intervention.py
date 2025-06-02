"""
Unit tests for ai_whisperer.batch.intervention

Tests for the automated intervention system that implements recovery strategies
and intervention policies. This is a HIGH PRIORITY module with 10/10 complexity score.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import uuid

from ai_whisperer.extensions.batch.intervention import (
    InterventionStrategy, InterventionResult, InterventionConfig,
    InterventionRecord, InterventionHistory, InterventionExecutor,
    InterventionOrchestrator
)
from ai_whisperer.extensions.batch.monitoring import AnomalyAlert
from ai_whisperer.core.logging import LogLevel


class TestInterventionStrategy:
    """Test InterventionStrategy enum."""
    
    def test_strategy_values(self):
        """Test strategy enum values."""
        assert InterventionStrategy.PROMPT_INJECTION.value == "prompt_injection"
        assert InterventionStrategy.SESSION_RESTART.value == "session_restart"
        assert InterventionStrategy.STATE_RESET.value == "state_reset"
        assert InterventionStrategy.TOOL_RETRY.value == "tool_retry"
        assert InterventionStrategy.ESCALATE.value == "escalate"
        assert InterventionStrategy.PYTHON_SCRIPT.value == "python_script"
        assert InterventionStrategy.CUSTOM.value == "custom"


class TestInterventionResult:
    """Test InterventionResult enum."""
    
    def test_result_values(self):
        """Test result enum values."""
        assert InterventionResult.SUCCESS.value == "success"
        assert InterventionResult.PARTIAL_SUCCESS.value == "partial_success"
        assert InterventionResult.FAILURE.value == "failure"
        assert InterventionResult.SKIPPED.value == "skipped"
        assert InterventionResult.ESCALATED.value == "escalated"


class TestInterventionConfig:
    """Test InterventionConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = InterventionConfig()
        
        assert config.auto_continue is True
        assert config.max_retries == 3
        assert config.retry_delay_seconds == 2.0
        assert config.escalation_threshold == 3
        
        # Check prompt injection config
        assert 'timeout_seconds' in config.prompt_injection_config
        assert 'templates' in config.prompt_injection_config
        assert 'continuation' in config.prompt_injection_config['templates']
        
        # Check alert strategy map
        assert 'session_stall' in config.alert_strategy_map
        assert InterventionStrategy.PROMPT_INJECTION in config.alert_strategy_map['session_stall']
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = InterventionConfig(
            auto_continue=False,
            max_retries=5,
            escalation_threshold=5
        )
        
        assert config.auto_continue is False
        assert config.max_retries == 5
        assert config.escalation_threshold == 5


class TestInterventionRecord:
    """Test InterventionRecord dataclass."""
    
    def test_default_record(self):
        """Test default record values."""
        record = InterventionRecord()
        
        assert record.intervention_id != ""  # UUID generated
        assert record.session_id == ""
        assert record.alert is None
        assert record.strategy == InterventionStrategy.PROMPT_INJECTION
        assert isinstance(record.timestamp, datetime)
        assert record.result == InterventionResult.SKIPPED
        assert record.details == {}
        assert record.duration_ms is None
        assert record.error is None
    
    def test_custom_record(self):
        """Test custom record values."""
        alert = Mock(spec=AnomalyAlert)
        record = InterventionRecord(
            session_id="test-session",
            alert=alert,
            strategy=InterventionStrategy.STATE_RESET,
            result=InterventionResult.SUCCESS,
            duration_ms=123.4
        )
        
        assert record.session_id == "test-session"
        assert record.alert == alert
        assert record.strategy == InterventionStrategy.STATE_RESET
        assert record.result == InterventionResult.SUCCESS
        assert record.duration_ms == 123.4
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        alert = Mock(spec=AnomalyAlert)
        alert.to_dict.return_value = {"type": "test_alert"}
        
        record = InterventionRecord(
            session_id="test-session",
            alert=alert,
            strategy=InterventionStrategy.TOOL_RETRY,
            result=InterventionResult.FAILURE,
            details={"key": "value"},
            error="Test error"
        )
        
        data = record.to_dict()
        
        assert data['session_id'] == "test-session"
        assert data['strategy'] == "tool_retry"
        assert data['result'] == "failure"
        assert data['details'] == {"key": "value"}
        assert data['error'] == "Test error"
        assert data['alert'] == {"type": "test_alert"}
        assert 'timestamp' in data


class TestInterventionHistory:
    """Test InterventionHistory class."""
    
    def test_init(self):
        """Test history initialization."""
        history = InterventionHistory(max_history=100)
        
        assert history.max_history == 100
        assert history.records == []
        assert history.session_interventions == {}
        assert history.strategy_success_rates == {}
    
    def test_add_record(self):
        """Test adding intervention records."""
        history = InterventionHistory()
        
        record1 = InterventionRecord(
            session_id="session1",
            strategy=InterventionStrategy.PROMPT_INJECTION,
            result=InterventionResult.SUCCESS
        )
        
        history.add_record(record1)
        
        assert len(history.records) == 1
        assert "session1" in history.session_interventions
        assert len(history.session_interventions["session1"]) == 1
        assert InterventionStrategy.PROMPT_INJECTION in history.strategy_success_rates
    
    def test_max_history_limit(self):
        """Test that history respects max limit."""
        history = InterventionHistory(max_history=5)
        
        # Add more than max
        for i in range(10):
            record = InterventionRecord(
                session_id=f"session{i}",
                result=InterventionResult.SUCCESS
            )
            history.add_record(record)
        
        assert len(history.records) == 5
        # Should have the last 5 records
        assert history.records[0].session_id == "session5"
        assert history.records[-1].session_id == "session9"
    
    def test_update_success_rate(self):
        """Test success rate tracking."""
        history = InterventionHistory()
        
        # Add various results
        for result in [InterventionResult.SUCCESS, InterventionResult.SUCCESS,
                      InterventionResult.FAILURE, InterventionResult.PARTIAL_SUCCESS]:
            record = InterventionRecord(
                strategy=InterventionStrategy.PROMPT_INJECTION,
                result=result
            )
            history.add_record(record)
        
        stats = history.strategy_success_rates[InterventionStrategy.PROMPT_INJECTION]
        assert stats['total'] == 4
        assert stats['success'] == 2
        assert stats['failure'] == 1
        assert stats['partial'] == 1
    
    def test_get_session_history(self):
        """Test getting session-specific history."""
        history = InterventionHistory()
        
        # Add records for different sessions
        record1 = InterventionRecord(session_id="session1")
        record2 = InterventionRecord(session_id="session2")
        record3 = InterventionRecord(session_id="session1")
        
        history.add_record(record1)
        history.add_record(record2)
        history.add_record(record3)
        
        session1_history = history.get_session_history("session1")
        assert len(session1_history) == 2
        assert all(r.session_id == "session1" for r in session1_history)
        
        # Non-existent session
        assert history.get_session_history("unknown") == []
    
    def test_get_strategy_stats(self):
        """Test getting strategy statistics."""
        history = InterventionHistory()
        
        # Add records with different results
        for _ in range(3):
            history.add_record(InterventionRecord(
                strategy=InterventionStrategy.STATE_RESET,
                result=InterventionResult.SUCCESS
            ))
        
        history.add_record(InterventionRecord(
            strategy=InterventionStrategy.STATE_RESET,
            result=InterventionResult.FAILURE
        ))
        
        stats = history.get_strategy_stats(InterventionStrategy.STATE_RESET)
        assert stats['total'] == 4
        assert stats['success'] == 3
        assert stats['failure'] == 1
        assert stats['success_rate'] == 0.75  # 3/4
        
        # Non-existent strategy
        empty_stats = history.get_strategy_stats(InterventionStrategy.CUSTOM)
        assert empty_stats == {}
    
    def test_get_recent_interventions(self):
        """Test getting recent interventions."""
        history = InterventionHistory()
        
        # Add 20 records
        for i in range(20):
            history.add_record(InterventionRecord(session_id=f"session{i}"))
        
        recent = history.get_recent_interventions(limit=5)
        assert len(recent) == 5
        assert recent[0].session_id == "session15"
        assert recent[-1].session_id == "session19"


class TestInterventionExecutor:
    """Test InterventionExecutor class."""
    
    def test_init(self):
        """Test executor initialization."""
        session_manager = Mock()
        config = InterventionConfig()
        
        executor = InterventionExecutor(session_manager, config)
        
        assert executor.session_manager == session_manager
        assert executor.config == config
        assert executor.message_injector is not None
        assert executor.session_inspector is not None
        assert executor.python_executor is not None
        assert executor.history is not None
        assert executor.active_interventions == {}
        assert len(executor.strategy_handlers) == 6
    
    @pytest.mark.asyncio
    @patch('ai_whisperer.batch.intervention.DebbieLogger')
    async def test_intervene_success(self, mock_logger_class):
        """Test successful intervention."""
        mock_logger = Mock()
        mock_logger_class.return_value = mock_logger
        
        session_manager = Mock()
        executor = InterventionExecutor(session_manager)
        
        # Mock strategy handler
        async def mock_handler(alert, record):
            record.details['handled'] = True
            return True
        
        executor.strategy_handlers[InterventionStrategy.PROMPT_INJECTION] = mock_handler
        
        # Create alert
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "session_stall"
        alert.to_dict.return_value = {"type": "session_stall"}
        
        # Execute intervention
        record = await executor.intervene(alert)
        
        assert record.result == InterventionResult.SUCCESS
        assert record.session_id == "test-session"
        assert record.details['handled'] is True
        assert len(executor.history.records) == 1
    
    @pytest.mark.asyncio
    async def test_intervene_with_multiple_strategies(self):
        """Test intervention trying multiple strategies."""
        executor = InterventionExecutor()
        
        # Mock handlers - first fails, second succeeds
        async def failing_handler(alert, record):
            return False
        
        async def success_handler(alert, record):
            return True
        
        executor.strategy_handlers[InterventionStrategy.PROMPT_INJECTION] = failing_handler
        executor.strategy_handlers[InterventionStrategy.SESSION_RESTART] = success_handler
        
        # Override config to use both strategies
        executor.config.alert_strategy_map['test_alert'] = [
            InterventionStrategy.PROMPT_INJECTION,
            InterventionStrategy.SESSION_RESTART
        ]
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "test_alert"
        alert.to_dict.return_value = {}
        
        record = await executor.intervene(alert)
        
        assert record.result == InterventionResult.SUCCESS
        assert record.strategy == InterventionStrategy.SESSION_RESTART
    
    @pytest.mark.asyncio
    async def test_intervene_all_strategies_fail(self):
        """Test when all strategies fail."""
        executor = InterventionExecutor()
        
        # Mock handler that always fails
        async def failing_handler(alert, record):
            return False
        
        executor.strategy_handlers[InterventionStrategy.PROMPT_INJECTION] = failing_handler
        executor.strategy_handlers[InterventionStrategy.STATE_RESET] = failing_handler
        
        executor.config.alert_strategy_map['test_alert'] = [
            InterventionStrategy.PROMPT_INJECTION,
            InterventionStrategy.STATE_RESET
        ]
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "test_alert"
        alert.to_dict.return_value = {}
        
        record = await executor.intervene(alert)
        
        assert record.result == InterventionResult.ESCALATED
    
    @pytest.mark.asyncio
    async def test_intervene_with_exception(self):
        """Test intervention handling exceptions."""
        executor = InterventionExecutor()
        
        # Mock handler that raises exception
        async def error_handler(alert, record):
            raise RuntimeError("Test error")
        
        executor.strategy_handlers[InterventionStrategy.PROMPT_INJECTION] = error_handler
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "session_stall"
        alert.message = "Test alert message"  # Add message attribute
        alert.to_dict.return_value = {}
        
        record = await executor.intervene(alert)
        
        # Since session_stall has two strategies, it will try SESSION_RESTART after PROMPT_INJECTION fails
        # So the result will be ESCALATED if both fail
        assert record.result in [InterventionResult.FAILURE, InterventionResult.ESCALATED]
        # The error will be from the last strategy attempted
        assert record.error is not None
    
    def test_should_skip_strategy(self):
        """Test strategy skipping logic."""
        executor = InterventionExecutor()
        
        # Add some failed interventions
        for _ in range(2):
            record = InterventionRecord(
                session_id="session1",
                strategy=InterventionStrategy.PROMPT_INJECTION,
                result=InterventionResult.FAILURE
            )
            executor.history.add_record(record)
        
        # Should skip after 2 failures
        assert executor._should_skip_strategy("session1", InterventionStrategy.PROMPT_INJECTION) is True
        
        # Different strategy should not be skipped
        assert executor._should_skip_strategy("session1", InterventionStrategy.STATE_RESET) is False
        
        # Different session should not be skipped
        assert executor._should_skip_strategy("session2", InterventionStrategy.PROMPT_INJECTION) is False
    
    @pytest.mark.asyncio
    async def test_execute_prompt_injection(self):
        """Test prompt injection strategy execution."""
        executor = InterventionExecutor()
        
        # Mock tools
        executor.message_injector.execute = Mock(return_value={
            'success': True,
            'result': {'response_received': True}
        })
        
        executor.session_inspector.execute = Mock(return_value={
            'success': True,
            'analysis': {'stall_detected': False}
        })
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "session_stall"
        
        record = InterventionRecord(session_id="test-session")
        
        result = await executor._execute_prompt_injection(alert, record)
        
        assert result is True
        assert 'injection_result' in record.details
        executor.message_injector.execute.assert_called_once()
        executor.session_inspector.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_state_reset(self):
        """Test state reset strategy execution."""
        executor = InterventionExecutor()
        
        executor.message_injector.execute = Mock(return_value={'success': True})
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        
        record = InterventionRecord()
        
        result = await executor._execute_state_reset(alert, record)
        
        assert result is True
        assert 'reset_result' in record.details
    
    @pytest.mark.asyncio
    async def test_execute_python_script(self):
        """Test Python script strategy execution."""
        executor = InterventionExecutor()
        
        # Mock Python executor
        async def mock_execute(*args, **kwargs):
            return {
                'success': True,
                'result': {'output': 'Analysis complete'}
            }
        
        executor._execute_python_analysis = mock_execute
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "slow_response"
        
        record = InterventionRecord()
        
        result = await executor._execute_python_script(alert, record)
        
        assert result is True
        assert 'python_analysis' in record.details
    
    def test_get_intervention_stats(self):
        """Test getting intervention statistics."""
        executor = InterventionExecutor()
        
        # Add some records
        for i in range(5):
            record = InterventionRecord(
                strategy=InterventionStrategy.PROMPT_INJECTION,
                result=InterventionResult.SUCCESS if i < 3 else InterventionResult.FAILURE
            )
            executor.history.add_record(record)
        
        stats = executor.get_intervention_stats()
        
        assert stats['total_interventions'] == 5
        assert stats['active_interventions'] == 0
        assert 'prompt_injection' in stats['strategy_stats']
        assert stats['overall_success_rate'] == 0.6  # 3/5


class TestInterventionOrchestrator:
    """Test InterventionOrchestrator class."""
    
    def test_init(self):
        """Test orchestrator initialization."""
        session_manager = Mock()
        config = InterventionConfig()
        
        orchestrator = InterventionOrchestrator(session_manager, config)
        
        assert orchestrator.session_manager == session_manager
        assert orchestrator.config == config
        assert orchestrator.executor is not None
        assert orchestrator.intervention_queue is not None
        assert orchestrator.processing_task is None
        assert orchestrator.is_running is False
    
    @pytest.mark.asyncio
    async def test_start_stop(self):
        """Test starting and stopping orchestrator."""
        orchestrator = InterventionOrchestrator()
        
        # Start
        await orchestrator.start()
        assert orchestrator.is_running is True
        assert orchestrator.processing_task is not None
        
        # Stop
        await orchestrator.stop()
        assert orchestrator.is_running is False
    
    @pytest.mark.asyncio
    async def test_request_intervention_auto_disabled(self):
        """Test intervention request when auto-continue is disabled."""
        config = InterventionConfig(auto_continue=False)
        orchestrator = InterventionOrchestrator(config=config)
        
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        
        await orchestrator.request_intervention(alert)
        
        # Should not add to queue
        assert orchestrator.intervention_queue.qsize() == 0
    
    @pytest.mark.asyncio
    async def test_request_intervention_auto_enabled(self):
        """Test intervention request when auto-continue is enabled."""
        orchestrator = InterventionOrchestrator()
        
        alert = Mock(spec=AnomalyAlert)
        
        await orchestrator.request_intervention(alert)
        
        # Should add to queue
        assert orchestrator.intervention_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_process_interventions(self):
        """Test processing intervention queue."""
        orchestrator = InterventionOrchestrator()
        
        # Mock executor
        orchestrator.executor.intervene = AsyncMock(return_value=Mock())
        
        # Add alert to queue
        alert = Mock(spec=AnomalyAlert)
        await orchestrator.intervention_queue.put(alert)
        
        # Start processing
        await orchestrator.start()
        
        # Wait briefly for processing
        await asyncio.sleep(0.1)
        
        # Stop
        await orchestrator.stop()
        
        # Verify intervention was called
        orchestrator.executor.intervene.assert_called_once_with(alert)
    
    def test_get_stats(self):
        """Test getting orchestrator statistics."""
        orchestrator = InterventionOrchestrator()
        
        # Mock executor stats
        orchestrator.executor.get_intervention_stats = Mock(return_value={
            'total_interventions': 10
        })
        
        stats = orchestrator.get_stats()
        
        assert stats['queue_size'] == 0
        assert stats['is_running'] is False
        assert stats['executor_stats']['total_interventions'] == 10


class TestInterventionIntegration:
    """Integration tests for intervention system."""
    
    @pytest.mark.asyncio
    async def test_full_intervention_flow(self):
        """Test complete intervention flow from alert to resolution."""
        # Create orchestrator
        session_manager = Mock()
        orchestrator = InterventionOrchestrator(session_manager)
        
        # Mock the entire prompt injection handler to ensure success
        async def mock_prompt_injection(alert, record):
            record.details['injection_result'] = {'response_received': True}
            return True
        
        orchestrator.executor.strategy_handlers[InterventionStrategy.PROMPT_INJECTION] = mock_prompt_injection
        
        # Start orchestrator
        await orchestrator.start()
        
        # Create and queue alert
        alert = Mock(spec=AnomalyAlert)
        alert.session_id = "test-session"
        alert.alert_type = "session_stall"
        alert.message = "Session stalled"
        alert.to_dict.return_value = {}
        
        await orchestrator.request_intervention(alert)
        
        # Wait for processing
        await asyncio.sleep(0.3)  # Give it a bit more time
        
        # Stop orchestrator
        await orchestrator.stop()
        
        # Verify intervention was executed
        assert len(orchestrator.executor.history.records) == 1
        record = orchestrator.executor.history.records[0]
        assert record.result == InterventionResult.SUCCESS
        assert record.session_id == "test-session"
        assert record.duration_ms is not None
        assert record.duration_ms > 0
        assert 'injection_result' in record.details