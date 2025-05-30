"""
Unit tests for Debbie Observer functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from interactive_server.debbie_observer import (
    DebbieObserver,
    InteractiveMonitor,
    PatternDetector,
    PatternType,
    AlertSeverity,
    Alert,
    SessionMetrics,
    get_observer
)


class TestPatternDetector:
    """Test pattern detection logic"""
    
    def test_detect_stall(self):
        """Test stall detection"""
        detector = PatternDetector()
        metrics = SessionMetrics(session_id="test-123")
        
        # No stall initially
        patterns = detector.detect_patterns(metrics)
        assert PatternType.STALL not in patterns
        
        # Simulate stall
        metrics.last_activity = datetime.now() - timedelta(seconds=35)
        metrics.response_times = [1.0, 2.0]  # Has responses
        patterns = detector.detect_patterns(metrics)
        assert PatternType.STALL in patterns
    
    def test_detect_rapid_retry(self):
        """Test rapid retry detection"""
        detector = PatternDetector()
        metrics = SessionMetrics(session_id="test-123")
        
        # Add similar messages rapidly - need at least 5 messages to check
        now = datetime.now()
        metrics.message_history = [
            {'timestamp': now - timedelta(seconds=8), 'content': 'list files', 'type': 'user'},
            {'timestamp': now - timedelta(seconds=6), 'content': 'list files', 'type': 'user'},
            {'timestamp': now - timedelta(seconds=4), 'content': 'list files', 'type': 'user'},
            {'timestamp': now - timedelta(seconds=2), 'content': 'list files', 'type': 'user'},
            {'timestamp': now - timedelta(seconds=1), 'content': 'list files', 'type': 'user'},
        ]
        
        patterns = detector.detect_patterns(metrics)
        assert PatternType.RAPID_RETRY in patterns
    
    def test_detect_error_cascade(self):
        """Test error cascade detection"""
        detector = PatternDetector()
        metrics = SessionMetrics(session_id="test-123")
        
        # Add multiple errors
        now = datetime.now()
        for i in range(6):
            metrics.error_history.append({
                'timestamp': now - timedelta(seconds=i * 5),
                'error': f'Error {i}'
            })
        
        patterns = detector.detect_patterns(metrics)
        assert PatternType.ERROR_CASCADE in patterns
    
    def test_detect_permission_issues(self):
        """Test permission issue detection"""
        detector = PatternDetector()
        metrics = SessionMetrics(session_id="test-123")
        
        # Add permission errors with timestamps
        metrics.error_history = [
            {'error': 'Permission denied accessing file', 'timestamp': datetime.now()},
            {'error': 'Access forbidden to directory', 'timestamp': datetime.now()},
        ]
        
        patterns = detector.detect_patterns(metrics)
        assert PatternType.PERMISSION_ISSUE in patterns


class TestInteractiveMonitor:
    """Test interactive session monitoring"""
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = InteractiveMonitor("test-session-123")
        assert monitor.session_id == "test-session-123"
        assert monitor.metrics.session_id == "test-session-123"
        assert monitor.metrics.message_count == 0
        assert monitor.alerts == []
    
    def test_on_message_tracking(self):
        """Test message tracking"""
        monitor = InteractiveMonitor("test-session")
        
        # Track message start
        monitor.on_message_start("Hello AI")
        assert monitor.metrics.message_count == 1
        assert len(monitor.metrics.message_history) == 1
        assert monitor._message_start is not None
        
        # Track message complete
        monitor.on_message_complete({'response': 'Hello!'})
        assert len(monitor.metrics.response_times) == 1
        assert monitor._message_start is None
    
    def test_on_tool_tracking(self):
        """Test tool execution tracking"""
        monitor = InteractiveMonitor("test-session")
        
        # Track tool start
        monitor.on_tool_start("read_file")
        assert monitor.metrics.tool_execution_count == 1
        assert monitor._active_tool_name == "read_file"
        
        # Track tool complete
        monitor.on_tool_complete("read_file", {'content': 'data'})
        assert monitor._active_tool_name is None
    
    def test_error_tracking(self):
        """Test error tracking"""
        monitor = InteractiveMonitor("test-session")
        
        # Track error
        error = ValueError("Test error")
        monitor.on_error(error)
        assert monitor.metrics.error_count == 1
        assert len(monitor.metrics.error_history) == 1
        assert monitor.metrics.error_history[0]['error'] == "Test error"
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        monitor = InteractiveMonitor("test-session")
        
        # Perfect health
        monitor.metrics.message_count = 10
        monitor.metrics.error_count = 0
        assert monitor._calculate_health_score() == 100.0
        
        # With errors
        monitor.metrics.error_count = 5
        health_score = monitor._calculate_health_score()
        assert health_score < 100.0
        assert health_score >= 0.0
    
    def test_alert_generation(self):
        """Test alert generation for patterns"""
        monitor = InteractiveMonitor("test-session")
        
        # Simulate stall
        monitor.metrics.last_activity = datetime.now() - timedelta(seconds=35)
        monitor.metrics.response_times = [1.0]
        
        alerts = monitor.check_patterns()
        assert len(alerts) > 0
        assert alerts[0].pattern == PatternType.STALL
        assert alerts[0].severity == AlertSeverity.WARNING


class TestDebbieObserver:
    """Test main Debbie observer"""
    
    def test_observer_singleton(self):
        """Test observer singleton pattern"""
        observer1 = get_observer()
        observer2 = get_observer()
        assert observer1 is observer2
    
    def test_observe_session(self):
        """Test session observation"""
        observer = DebbieObserver()
        
        # Start observing
        monitor = observer.observe_session("test-123")
        assert "test-123" in observer.monitors
        assert isinstance(monitor, InteractiveMonitor)
        
        # Same session returns same monitor
        monitor2 = observer.observe_session("test-123")
        assert monitor is monitor2
    
    def test_stop_observing(self):
        """Test stopping observation"""
        observer = DebbieObserver()
        
        # Start and stop
        observer.observe_session("test-123")
        assert "test-123" in observer.monitors
        
        observer.stop_observing("test-123")
        assert "test-123" not in observer.monitors
    
    @pytest.mark.asyncio
    async def test_enable_disable(self):
        """Test enable/disable functionality"""
        observer = DebbieObserver()
        
        # Initially enabled
        assert observer._enabled
        
        # Disable
        observer.disable()
        assert not observer._enabled
        
        # Enable
        observer.enable()
        assert observer._enabled
        
        # Cleanup
        observer.disable()
    
    def test_message_hooks(self):
        """Test message processing hooks"""
        observer = DebbieObserver()
        monitor = observer.observe_session("test-123")
        
        # Test hooks
        observer.on_message_start("test-123", "Hello")
        assert monitor.metrics.message_count == 1
        
        observer.on_message_complete("test-123", {'response': 'Hi'})
        assert len(monitor.metrics.response_times) == 1
    
    def test_disabled_hooks(self):
        """Test hooks when disabled"""
        observer = DebbieObserver()
        observer.observe_session("test-123")
        observer.disable()
        
        # Hooks should not affect monitors when disabled
        observer.on_message_start("test-123", "Hello")
        monitor = observer.monitors.get("test-123")
        assert monitor.metrics.message_count == 0
    
    @pytest.mark.asyncio
    async def test_alert_callbacks(self):
        """Test alert callback mechanism"""
        observer = DebbieObserver()
        
        # Add callback
        alerts_received = []
        async def alert_callback(session_id, alert):
            alerts_received.append((session_id, alert))
        
        observer.add_alert_callback(alert_callback)
        
        # Generate alert
        alert = Alert(
            severity=AlertSeverity.WARNING,
            pattern=PatternType.STALL,
            message="Test alert"
        )
        
        await observer._handle_alert("test-123", alert)
        
        # Verify callback was called
        assert len(alerts_received) == 1
        assert alerts_received[0][0] == "test-123"
        assert alerts_received[0][1] == alert
    
    def test_session_health(self):
        """Test session health reporting"""
        observer = DebbieObserver()
        monitor = observer.observe_session("test-123")
        
        # Add some activity
        monitor.on_message_start("Hello")
        monitor.on_message_complete({'response': 'Hi'})
        
        # Get health
        health = observer.get_session_health("test-123")
        assert health is not None
        assert health['session_id'] == "test-123"
        assert health['message_count'] == 1
        assert 'health_score' in health
        
        # Non-existent session
        health = observer.get_session_health("non-existent")
        assert health is None


class TestDebbieObserverIntegration:
    """Test observer integration with session manager"""
    
    @pytest.mark.asyncio
    async def test_pattern_check_loop(self):
        """Test background pattern checking"""
        observer = DebbieObserver()
        observer._pattern_check_interval = 0.1  # Fast checking for test
        
        # Mock monitor with patterns
        monitor = Mock(spec=InteractiveMonitor)
        monitor.check_patterns.return_value = [
            Alert(AlertSeverity.WARNING, PatternType.STALL, "Test stall")
        ]
        observer.monitors["test-123"] = monitor
        
        # Track alerts
        alerts_handled = []
        observer.add_alert_callback(lambda sid, alert: alerts_handled.append(alert))
        
        # Enable and wait
        observer.enable()
        await asyncio.sleep(0.2)
        
        # Should have checked patterns
        assert monitor.check_patterns.called
        assert len(alerts_handled) > 0
        
        # Cleanup
        observer.disable()
    
    def test_get_all_sessions_health(self):
        """Test getting health for all sessions"""
        observer = DebbieObserver()
        
        # Add multiple sessions
        monitor1 = observer.observe_session("session-1")
        monitor2 = observer.observe_session("session-2")
        
        # Add activity
        monitor1.on_message_start("Hello")
        # For session-2, add a message first so error_rate can be calculated
        monitor2.on_message_start("Test message")
        monitor2.on_error(ValueError("Test error"))
        
        # Get all health
        all_health = observer.get_all_sessions_health()
        assert len(all_health) == 2
        assert "session-1" in all_health
        assert "session-2" in all_health
        assert all_health["session-1"]['message_count'] == 1
        assert all_health["session-2"]['error_rate'] > 0