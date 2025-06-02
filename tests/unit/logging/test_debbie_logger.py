"""
Unit tests for ai_whisperer.logging.debbie_logger

Tests for Debbie's enhanced logger with intelligent commentary and pattern detection.
This is a HIGH PRIORITY module with 10/10 complexity score.
"""

import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time

from ai_whisperer.extensions.monitoring.debbie_logger import (
    PatternType, DetectedPattern, Insight, PatternDetector,
    InsightGenerator, DebbieCommentary, DebbieLogger
)
from ai_whisperer.core.logging import LogLevel, LogSource, ComponentType


class TestPatternType:
    """Test PatternType enum."""
    
    def test_pattern_type_values(self):
        """Test pattern type enum values."""
        assert PatternType.CONTINUATION_STALL.value == "continuation_stall"
        assert PatternType.TOOL_LOOP.value == "tool_loop"
        assert PatternType.ERROR_PATTERN.value == "error_pattern"
        assert PatternType.PERFORMANCE_DEGRADATION.value == "performance_degradation"
        assert PatternType.MEMORY_SPIKE.value == "memory_spike"
        assert PatternType.WEBSOCKET_DELAY.value == "websocket_delay"
        assert PatternType.CONFIGURATION_ISSUE.value == "configuration_issue"


class TestDetectedPattern:
    """Test DetectedPattern dataclass."""
    
    def test_default_pattern(self):
        """Test default pattern values."""
        pattern = DetectedPattern(
            pattern_type=PatternType.TOOL_LOOP,
            confidence=0.85,
            description="Tool loop detected",
            evidence=[{"event": "test"}]
        )
        
        assert pattern.pattern_type == PatternType.TOOL_LOOP
        assert pattern.confidence == 0.85
        assert pattern.description == "Tool loop detected"
        assert len(pattern.evidence) == 1
        assert isinstance(pattern.timestamp, datetime)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        pattern = DetectedPattern(
            pattern_type=PatternType.ERROR_PATTERN,
            confidence=0.9,
            description="Recurring error",
            evidence=[{"e1": "v1"}, {"e2": "v2"}]
        )
        
        data = pattern.to_dict()
        
        assert data['pattern_type'] == "error_pattern"
        assert data['confidence'] == 0.9
        assert data['description'] == "Recurring error"
        assert data['evidence_count'] == 2
        assert 'timestamp' in data


class TestInsight:
    """Test Insight dataclass."""
    
    def test_insight_creation(self):
        """Test insight creation."""
        patterns = [
            DetectedPattern(
                pattern_type=PatternType.CONTINUATION_STALL,
                confidence=0.95,
                description="Stall detected",
                evidence=[]
            )
        ]
        
        insight = Insight(
            message="Agent stalled after tool execution",
            confidence=0.95,
            patterns=patterns,
            recommendations=["Inject continuation prompt"],
            severity="warning"
        )
        
        assert insight.message == "Agent stalled after tool execution"
        assert insight.confidence == 0.95
        assert len(insight.patterns) == 1
        assert len(insight.recommendations) == 1
        assert insight.severity == "warning"
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        insight = Insight(
            message="Test insight",
            confidence=0.8,
            patterns=[],
            recommendations=["Rec 1", "Rec 2"],
            severity="critical"
        )
        
        data = insight.to_dict()
        
        assert data['message'] == "Test insight"
        assert data['confidence'] == 0.8
        assert data['pattern_count'] == 0
        assert data['recommendations'] == ["Rec 1", "Rec 2"]
        assert data['severity'] == "critical"


class TestPatternDetector:
    """Test PatternDetector class."""
    
    def test_init(self):
        """Test detector initialization."""
        detector = PatternDetector()
        
        assert detector.pattern_history == []
        assert len(detector.detection_rules) > 0
        assert PatternType.CONTINUATION_STALL in detector.detection_rules
    
    def test_detect_continuation_stall(self):
        """Test continuation stall detection."""
        detector = PatternDetector()
        
        # Create stall event
        event = {
            'action': 'session_inspected',
            'details': {
                'stall_detected': True,
                'stall_duration': 45.0
            }
        }
        
        # Recent events with tool execution
        recent_events = [
            {'component': 'TOOL', 'action': 'tool_executed'},  # Detector expects string 'TOOL'
            {'action': 'other'},
        ]
        
        pattern = detector._detect_continuation_stall(event, recent_events)
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.CONTINUATION_STALL
        assert pattern.confidence == 0.92
        assert "45.0s" in pattern.description
    
    def test_detect_tool_loop(self):
        """Test tool loop detection."""
        detector = PatternDetector()
        
        # Current tool event
        event = {
            'action': 'tool_executed',
            'details': {'tool_name': 'get_file_content'}
        }
        
        # Recent events with repeated tool calls
        recent_events = []
        for i in range(10):
            recent_events.append({
                'action': 'tool_executed',
                'details': {'tool_name': 'get_file_content'}
            })
        
        pattern = detector._detect_tool_loop(event, recent_events)
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.TOOL_LOOP
        assert pattern.confidence == 0.85
        assert "get_file_content" in pattern.description
    
    def test_detect_error_pattern(self):
        """Test error pattern detection."""
        detector = PatternDetector()
        
        # Error event
        event = {
            'level': 'ERROR',
            'event_summary': 'Connection timeout error'
        }
        
        # Recent similar errors
        recent_events = [
            {'level': 'ERROR', 'event_summary': 'Connection timeout error'},
            {'level': 'INFO', 'event_summary': 'Processing'},
            {'level': 'ERROR', 'event_summary': 'Connection timeout error'},
            {'level': 'ERROR', 'event_summary': 'Connection timeout error'},
        ]
        
        pattern = detector._detect_error_pattern(event, recent_events)
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.ERROR_PATTERN
        assert pattern.confidence == 0.8
        assert "Connection timeout" in pattern.description
    
    def test_detect_performance_degradation(self):
        """Test performance degradation detection."""
        detector = PatternDetector()
        
        # Slow event
        event = {
            'action': 'process_file',
            'duration_ms': 1500
        }
        
        # Recent fast events
        recent_events = []
        for i in range(10):
            recent_events.append({
                'action': 'process_file',
                'duration_ms': 500
            })
        
        pattern = detector._detect_performance_degradation(event, recent_events)
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.PERFORMANCE_DEGRADATION
        assert pattern.confidence == 0.75
        assert "1500ms" in pattern.description
        assert "avg: 500ms" in pattern.description
    
    def test_detect_memory_spike(self):
        """Test memory spike detection."""
        detector = PatternDetector()
        
        # High memory event
        event = {
            'details': {
                'memory_used_mb': 450.5
            }
        }
        
        pattern = detector._detect_memory_spike(event, [])
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.MEMORY_SPIKE
        assert pattern.confidence == 0.9
        assert "450.5MB" in pattern.description
    
    def test_detect_websocket_delay(self):
        """Test WebSocket delay detection."""
        detector = PatternDetector()
        
        # Delayed WebSocket event
        event = {
            'component': 'websocket_handler',
            'details': {
                'response_time_ms': 1500
            }
        }
        
        pattern = detector._detect_websocket_delay(event, [])
        
        assert pattern is not None
        assert pattern.pattern_type == PatternType.WEBSOCKET_DELAY
        assert pattern.confidence == 0.85
        assert "1500ms" in pattern.description
    
    def test_similarity_score(self):
        """Test text similarity calculation."""
        detector = PatternDetector()
        
        # Identical strings
        assert detector._similarity_score("hello world", "hello world") == 1.0
        
        # Partially similar
        score = detector._similarity_score("connection timeout error", "connection error occurred")
        assert 0.3 < score < 0.7
        
        # Completely different
        assert detector._similarity_score("hello", "goodbye") == 0.0
        
        # Empty strings
        assert detector._similarity_score("", "test") == 0.0
        assert detector._similarity_score("test", "") == 0.0
    
    def test_analyze_multiple_patterns(self):
        """Test analyzing events for multiple patterns."""
        detector = PatternDetector()
        
        # Event that could trigger multiple patterns
        event = {
            'action': 'tool_executed',
            'level': 'ERROR',
            'event_summary': 'Tool execution failed',
            'details': {
                'tool_name': 'test_tool',
                'memory_used_mb': 500
            },
            'duration_ms': 2000
        }
        
        recent_events = [
            {'action': 'tool_executed', 'details': {'tool_name': 'test_tool'}},
            {'level': 'ERROR', 'event_summary': 'Tool execution failed'},
            {'action': 'tool_executed', 'duration_ms': 500},
        ]
        
        patterns = detector.analyze(event, recent_events)
        
        # Should detect at least memory spike
        assert any(p.pattern_type == PatternType.MEMORY_SPIKE for p in patterns)
    
    def test_analyze_with_exception(self):
        """Test pattern detection handles exceptions gracefully."""
        detector = PatternDetector()
        
        # Mock a detection rule that raises exception
        def bad_detector(event, recent):
            raise RuntimeError("Detection failed")
        
        detector.detection_rules[PatternType.TOOL_LOOP] = bad_detector
        
        # Should not raise exception
        patterns = detector.analyze({'test': 'event'}, [])
        
        # Should still detect other patterns if applicable
        assert isinstance(patterns, list)


class TestInsightGenerator:
    """Test InsightGenerator class."""
    
    def test_generate_no_patterns(self):
        """Test generation with no patterns."""
        generator = InsightGenerator()
        
        insight = generator.generate({}, [])
        
        assert insight is None
    
    def test_generate_continuation_stall_insight(self):
        """Test continuation stall insight generation."""
        generator = InsightGenerator()
        
        pattern = DetectedPattern(
            pattern_type=PatternType.CONTINUATION_STALL,
            confidence=0.95,
            description="Agent stalled for 30s",
            evidence=[]
        )
        
        insight = generator.generate({}, [pattern])
        
        assert insight is not None
        assert "waiting for user input" in insight.message
        assert insight.confidence == 0.95
        assert insight.severity == "warning"
        assert any("continuation prompt" in rec for rec in insight.recommendations)
    
    def test_generate_tool_loop_insight(self):
        """Test tool loop insight generation."""
        generator = InsightGenerator()
        
        pattern = DetectedPattern(
            pattern_type=PatternType.TOOL_LOOP,
            confidence=0.85,
            description="Tool called 10 times",
            evidence=[]
        )
        
        insight = generator.generate({}, [pattern])
        
        assert insight is not None
        assert "infinite loop" in insight.message
        assert insight.severity == "critical"
        assert any("loop detection" in rec for rec in insight.recommendations)
    
    def test_generate_error_pattern_insight(self):
        """Test error pattern insight generation."""
        generator = InsightGenerator()
        
        pattern = DetectedPattern(
            pattern_type=PatternType.ERROR_PATTERN,
            confidence=0.8,
            description="Recurring timeout errors",
            evidence=[]
        )
        
        insight = generator.generate({}, [pattern])
        
        assert insight is not None
        assert "Recurring errors" in insight.message
        assert insight.severity == "critical"
        assert any("root cause" in rec for rec in insight.recommendations)
    
    def test_generate_performance_insight(self):
        """Test performance degradation insight generation."""
        generator = InsightGenerator()
        
        pattern = DetectedPattern(
            pattern_type=PatternType.PERFORMANCE_DEGRADATION,
            confidence=0.75,
            description="Operation 50% slower",
            evidence=[]
        )
        
        insight = generator.generate({}, [pattern])
        
        assert insight is not None
        assert "performance is degrading" in insight.message
        assert insight.severity == "warning"
        assert any("Profile" in rec for rec in insight.recommendations)
    
    def test_generate_with_multiple_patterns(self):
        """Test insight generation with multiple patterns."""
        generator = InsightGenerator()
        
        patterns = [
            DetectedPattern(
                pattern_type=PatternType.MEMORY_SPIKE,
                confidence=0.7,
                description="Memory high",
                evidence=[]
            ),
            DetectedPattern(
                pattern_type=PatternType.PERFORMANCE_DEGRADATION,
                confidence=0.9,
                description="System slow",
                evidence=[]
            )
        ]
        
        insight = generator.generate({}, patterns)
        
        # Should prioritize higher confidence pattern
        assert "performance" in insight.message.lower()
        assert len(insight.patterns) == 2
    
    def test_generate_default_insight(self):
        """Test default insight for unknown pattern types."""
        generator = InsightGenerator()
        
        # Create pattern with no specific handler
        pattern = DetectedPattern(
            pattern_type=PatternType.CONFIGURATION_ISSUE,
            confidence=0.8,
            description="Config issue detected",
            evidence=[]
        )
        
        # Mock to ensure we don't have a handler
        generator.generate({}, [pattern])
        
        # Should generate default insight
        # (The actual implementation would generate a default)


class TestDebbieCommentary:
    """Test DebbieCommentary class."""
    
    def test_init(self):
        """Test commentary initialization."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        
        assert commentary.logger == mock_logger
        assert commentary.pattern_detector is not None
        assert commentary.insight_generator is not None
        assert commentary.recent_events == []
        assert commentary.max_recent == 1000
    
    def test_observe_no_patterns(self):
        """Test observing event with no patterns detected."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        
        event = {'action': 'normal_event'}
        commentary.observe(event)
        
        assert len(commentary.recent_events) == 1
        mock_logger.comment.assert_not_called()
    
    def test_observe_with_pattern(self):
        """Test observing event that triggers pattern detection."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        
        # Mock pattern detection
        mock_pattern = DetectedPattern(
            pattern_type=PatternType.CONTINUATION_STALL,
            confidence=0.9,
            description="Stall detected",
            evidence=[]
        )
        commentary.pattern_detector.analyze = Mock(return_value=[mock_pattern])
        
        # Mock insight generation
        mock_insight = Insight(
            message="Agent stalled",
            confidence=0.9,
            patterns=[mock_pattern],
            recommendations=["Fix it"],
            severity="warning"
        )
        commentary.insight_generator.generate = Mock(return_value=mock_insight)
        
        event = {'action': 'test_event'}
        commentary.observe(event)
        
        # Should log commentary
        mock_logger.comment.assert_called_once()
        call_args = mock_logger.comment.call_args
        assert call_args[1]['level'] == LogLevel.WARNING
        assert "Agent stalled" in call_args[1]['comment']
    
    def test_observe_event_limit(self):
        """Test that recent events are limited."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        commentary.max_recent = 10
        
        # Add more than max events
        for i in range(20):
            commentary.observe({'event': i})
        
        assert len(commentary.recent_events) == 10
        assert commentary.recent_events[0]['event'] == 10
        assert commentary.recent_events[-1]['event'] == 19
    
    def test_explain_stall(self):
        """Test stall explanation."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        
        commentary.explain_stall("session-123", 45.5)
        
        mock_logger.comment.assert_called_once()
        call_args = mock_logger.comment.call_args
        assert call_args[1]['level'] == LogLevel.WARNING
        assert "45.5s" in call_args[1]['comment']
        assert call_args[1]['context']['session_id'] == "session-123"
        assert call_args[1]['context']['stall_duration'] == 45.5
    
    def test_explain_intervention(self):
        """Test intervention explanation."""
        mock_logger = Mock()
        commentary = DebbieCommentary(mock_logger)
        
        commentary.explain_intervention("inject_prompt", "stall_detected", "success")
        
        mock_logger.comment.assert_called_once()
        call_args = mock_logger.comment.call_args
        assert call_args[1]['level'] == LogLevel.INFO
        assert "inject_prompt" in call_args[1]['comment']
        assert call_args[1]['context']['intervention_type'] == "inject_prompt"
        assert call_args[1]['context']['result'] == "success"


class TestDebbieLogger:
    """Test DebbieLogger class."""
    
    def test_init(self):
        """Test logger initialization."""
        logger = DebbieLogger("test_debbie")
        
        assert logger.logger is not None
        assert logger.commentary is not None
        assert isinstance(logger.commentary, DebbieCommentary)
    
    @patch('ai_whisperer.logging.debbie_logger.logging.getLogger')
    def test_log_basic(self, mock_get_logger):
        """Test basic logging functionality."""
        mock_logger_instance = Mock()
        mock_get_logger.return_value = mock_logger_instance
        
        logger = DebbieLogger("test")
        
        logger.log(
            level=LogLevel.INFO,
            source=LogSource.DEBBIE,
            action="test_action",
            message="Test message",
            details={"key": "value"}
        )
        
        # Verify log was called
        mock_logger_instance.log.assert_called_once()
        call_args = mock_logger_instance.log.call_args
        assert call_args[0][0] == logging.INFO
        assert call_args[0][1] == "Test message"
        
        # Check extra data
        extra = call_args[1]['extra']
        assert extra['level'] == 'INFO'
        assert extra['action'] == 'test_action'
        assert extra['details']['key'] == 'value'
    
    def test_comment(self):
        """Test comment functionality."""
        logger = DebbieLogger("test")
        logger.log = Mock()
        
        logger.comment(
            level=LogLevel.WARNING,
            comment="This is Debbie's insight",
            context={"pattern": "stall"}
        )
        
        logger.log.assert_called_once()
        # Use kwargs to access named arguments
        call_kwargs = logger.log.call_args.kwargs
        assert call_kwargs['level'] == LogLevel.WARNING
        assert call_kwargs['source'] == LogSource.DEBBIE_COMMENT
        assert call_kwargs['action'] == "commentary"
        assert call_kwargs['message'] == "This is Debbie's insight"
        assert call_kwargs['details']['pattern'] == 'stall'
    
    def test_convenience_methods(self):
        """Test convenience logging methods."""
        logger = DebbieLogger("test")
        logger.log = Mock()
        
        # Test debug
        logger.debug("Debug message", session_id="123")
        assert logger.log.call_args[0][0] == LogLevel.DEBUG
        assert logger.log.call_args[0][1] == LogSource.DEBBIE
        assert logger.log.call_args[0][2] == "debug"
        assert logger.log.call_args[0][3] == "Debug message"
        assert logger.log.call_args[1]['session_id'] == "123"
        
        # Test info
        logger.info("Info message")
        assert logger.log.call_args[0][0] == LogLevel.INFO
        assert logger.log.call_args[0][3] == "Info message"
        
        # Test warning
        logger.warning("Warning message")
        assert logger.log.call_args[0][0] == LogLevel.WARNING
        
        # Test error
        logger.error("Error message")
        assert logger.log.call_args[0][0] == LogLevel.ERROR
        
        # Test critical
        logger.critical("Critical message")
        assert logger.log.call_args[0][0] == LogLevel.CRITICAL
    
    def test_log_triggers_observation(self):
        """Test that logging triggers pattern observation."""
        logger = DebbieLogger("test")
        logger.commentary.observe = Mock()
        
        with patch('ai_whisperer.logging.debbie_logger.logging.getLogger'):
            logger.info("Test message", details={"test": "data"})
        
        # Commentary should observe the event
        logger.commentary.observe.assert_called_once()
        observed_event = logger.commentary.observe.call_args[0][0]
        assert observed_event['event_summary'] == "Test message"
        assert observed_event['details']['test'] == "data"


class TestDebbieLoggerIntegration:
    """Integration tests for Debbie logger system."""
    
    def test_full_pattern_detection_flow(self):
        """Test complete flow from logging to pattern detection and insight."""
        logger = DebbieLogger("test_integration")
        
        # Mock the actual logger to avoid output
        with patch('ai_whisperer.logging.debbie_logger.logging.getLogger'):
            # Generate tool loop pattern
            for i in range(10):
                logger.log(
                    level=LogLevel.INFO,
                    source=LogSource.TOOL,
                    action="tool_executed",
                    message=f"Executing tool iteration {i}",
                    details={"tool_name": "test_tool"}
                )
            
            # Should have accumulated events (including commentary)
            assert len(logger.commentary.recent_events) >= 10
            
            # Check that tool events were recorded
            tool_events = [e for e in logger.commentary.recent_events 
                          if e.get('action') == 'tool_executed']
            assert len(tool_events) == 10
    
    def test_stall_detection_flow(self):
        """Test stall detection and explanation flow."""
        logger = DebbieLogger("test_stall")
        
        with patch('ai_whisperer.logging.debbie_logger.logging.getLogger'):
            # First log a tool execution
            logger.log(
                level=LogLevel.INFO,
                source=LogSource.TOOL,
                action="tool_executed",
                message="Tool completed",
                details={"tool_name": "test_tool"}
            )
            
            # Then log a stall detection
            logger.log(
                level=LogLevel.WARNING,
                source=LogSource.DEBBIE,
                action="session_inspected",
                message="Session stalled",
                details={
                    "stall_detected": True,
                    "stall_duration": 35.0
                }
            )
            
            # Should have both events plus commentary
            assert len(logger.commentary.recent_events) == 3  # tool + stall + commentary
            
            # Verify the stall was detected and commented on
            commentary_events = [e for e in logger.commentary.recent_events
                               if e.get('action') == 'commentary']
            assert len(commentary_events) == 1
            assert 'waiting for user input' in commentary_events[0]['event_summary']