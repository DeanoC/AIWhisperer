"""
Tests for DebbieCommand debugging functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_whisperer.commands.debbie import DebbieCommand
from ai_whisperer.commands.errors import CommandError
from datetime import datetime, timedelta


class TestDebbieCommand:
    """Test cases for DebbieCommand"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.command = DebbieCommand()
        
        # Mock observer and monitor
        self.mock_observer = Mock()
        self.mock_monitor = Mock()
        
        # Set up mock monitor attributes
        self.mock_monitor._calculate_health_score.return_value = 85
        self.mock_monitor.metrics = Mock()
        self.mock_monitor.metrics.message_count = 10
        self.mock_monitor.metrics.error_count = 1
        self.mock_monitor.metrics.avg_response_time = 2.5
        self.mock_monitor.metrics.start_time = datetime.now() - timedelta(minutes=5)
        self.mock_monitor.metrics.detected_patterns = []
        self.mock_monitor.alerts = []
        
        # Set up mock observer
        self.mock_observer._enabled = True
        self.mock_observer.monitors = {'test-session': self.mock_monitor}
        self.mock_observer._pattern_check_interval = 5
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_status_command_specific_session(self, mock_get_observer):
        """Test /debbie status for specific session"""
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('status test-session')
        
        assert '🟢' in result  # Health score 85 should show green
        assert 'test-session' in result
        assert '85/100' in result
        assert 'Messages: 10' in result
        assert 'Errors: 1' in result
        assert '2.50s' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_status_command_global(self, mock_get_observer):
        """Test /debbie status for global monitoring status"""
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('status')
        
        assert 'Debbie Monitoring Status: Enabled' in result
        assert 'Active Sessions: 1' in result
        assert 'Check Interval: 5s' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_status_command_monitoring_disabled(self, mock_get_observer):
        """Test status when monitoring is disabled"""
        self.mock_observer._enabled = False
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('status')
        
        assert '❌ Debbie monitoring is not active' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_status_command_session_not_found(self, mock_get_observer):
        """Test status for non-existent session"""
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('status nonexistent-session')
        
        assert 'ℹ️ Session nonexist... is not currently monitored' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_status_command_detailed(self, mock_get_observer):
        """Test detailed status output"""
        mock_get_observer.return_value = self.mock_observer
        
        # Add some patterns and alerts
        from interactive_server.debbie_observer import PatternType
        self.mock_monitor.metrics.detected_patterns = [PatternType.STALL]
        
        mock_alert = Mock()
        mock_alert.severity = Mock()
        mock_alert.severity.value = 'WARNING'
        mock_alert.message = 'Test alert'
        self.mock_monitor.alerts = [mock_alert]
        
        result = self.command.run('status test-session --detailed')
        
        assert 'Detected Patterns: stall' in result
        assert 'Active Alerts: 1' in result
        assert 'WARNING: Test alert' in result
    
    @patch('ai_whisperer.tools.session_analysis_tool.SessionAnalysisTool')
    @patch('interactive_server.debbie_observer.get_observer')
    def test_analyze_command(self, mock_get_observer, mock_analysis_tool_class):
        """Test /debbie analyze command"""
        mock_get_observer.return_value = self.mock_observer
        
        # Mock analysis tool
        mock_analysis_tool = Mock()
        mock_analysis_tool_class.return_value = mock_analysis_tool
        mock_analysis_tool.execute.return_value = {
            'success': True,
            'analysis': {
                'health_score': 85,
                'total_events': 15,
                'error_rate': 10.0,
                'avg_response_time': 2.5,
                'errors': {
                    'tool_errors': {'count': 2}
                },
                'performance': {
                    'slowest_operations': [{'operation': 'file_read', 'duration': 3.2}]
                },
                'recommendations': ['Consider caching file reads', 'Optimize response time']
            }
        }
        
        result = self.command.run('analyze test-session 300')
        
        assert 'Deep Analysis for Session test-session' in result
        assert 'Health Score: 85/100' in result
        assert 'Total Events: 15' in result
        assert 'Error Rate: 10.0%' in result
        assert 'tool_errors: 2 occurrences' in result
        assert 'Slowest: file_read (3.20s)' in result
        assert 'Consider caching file reads' in result
        
        # Verify tool was called correctly
        mock_analysis_tool.execute.assert_called_once_with(
            session_id='test-session',
            time_range=300,
            focus='all'
        )
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_analyze_command_no_session(self, mock_get_observer):
        """Test analyze command without session ID"""
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('analyze')
        
        assert '❌ Session ID required for analysis' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_suggest_command_healthy_session(self, mock_get_observer):
        """Test suggestions for healthy session"""
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('suggest test-session')
        
        assert 'Suggestions for Session test-session' in result
        assert '✅ Session appears healthy' in result
        assert 'Run \'/debbie analyze\' for deeper insights' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_suggest_command_unhealthy_session(self, mock_get_observer):
        """Test suggestions for unhealthy session"""
        # Make session unhealthy
        self.mock_monitor._calculate_health_score.return_value = 45
        self.mock_monitor.metrics.avg_response_time = 15.0
        self.mock_monitor.metrics.error_count = 5
        self.mock_monitor.metrics.message_count = 10
        
        # Add problematic patterns
        from interactive_server.debbie_observer import PatternType
        self.mock_monitor.metrics.detected_patterns = [PatternType.STALL, PatternType.ERROR_CASCADE]
        
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('suggest test-session')
        
        assert 'Suggestions for Session test-session' in result
        assert '🔄 Consider restarting the session' in result
        assert '⏰ Agent may be stalled' in result
        assert '🚨 Multiple errors detected' in result
        assert '🐌 Slow response times' in result
        assert '❌ High error rate' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_report_command(self, mock_get_observer):
        """Test comprehensive session report"""
        mock_get_observer.return_value = self.mock_observer
        
        # Add some alerts
        mock_alert1 = Mock()
        mock_alert1.timestamp = datetime.now() - timedelta(minutes=2)
        mock_alert1.severity = Mock()
        mock_alert1.severity.value = 'WARNING'
        mock_alert1.message = 'Response time elevated'
        
        mock_alert2 = Mock()
        mock_alert2.timestamp = datetime.now() - timedelta(minutes=1)
        mock_alert2.severity = Mock()
        mock_alert2.severity.value = 'ERROR'
        mock_alert2.message = 'Tool execution failed'
        
        self.mock_monitor.alerts = [mock_alert1, mock_alert2]
        
        result = self.command.run('report test-session')
        
        assert 'Debbie Session Report' in result
        assert 'Session ID: test-session' in result
        assert 'Health Score: 85/100' in result
        assert 'Total Messages: 10' in result
        assert 'Error Count: 1' in result
        assert 'Total Alerts: 2' in result
        assert 'WARNING: 1 alerts' in result
        assert 'ERROR: 1 alerts' in result
        assert 'Response time elevated' in result
        assert 'Tool execution failed' in result
        assert 'Status: Excellent' in result  # Health score 85
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_report_command_poor_health(self, mock_get_observer):
        """Test report for session with poor health"""
        self.mock_monitor._calculate_health_score.return_value = 35
        mock_get_observer.return_value = self.mock_observer
        
        result = self.command.run('report test-session')
        
        assert 'Health Score: 35/100' in result
        assert 'Status: Poor - Significant issues detected' in result
        assert '• Consider session restart or intervention' in result
    
    def test_unknown_subcommand(self):
        """Test handling of unknown subcommands"""
        with pytest.raises(CommandError) as exc_info:
            self.command.run('unknown_command')
        
        assert 'Unknown subcommand: unknown_command' in str(exc_info.value)
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_observer_import_error(self, mock_get_observer):
        """Test handling when observer import fails"""
        mock_get_observer.side_effect = ImportError("Module not found")
        
        # ImportError is caught and handled, not raised as CommandError
        result = self.command.run('status')
        
        # Should return the monitoring not active message
        assert '❌ Debbie monitoring is not active' in result
    
    def test_parse_arguments(self):
        """Test argument parsing for various subcommands"""
        # Test with session ID
        parsed = self.command.parse_args('status session-123')
        assert parsed['args'] == ['status', 'session-123']
        
        # Test with options
        parsed = self.command.parse_args('status --detailed')
        assert parsed['args'] == ['status']
        assert parsed['options'].get('detailed', False)
        
        # Test analyze with time range
        parsed = self.command.parse_args('analyze session-123 600')
        assert parsed['args'] == ['analyze', 'session-123', '600']
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_context_session_id(self, mock_get_observer):
        """Test using session ID from context when not provided in args"""
        mock_get_observer.return_value = self.mock_observer
        
        context = {'session_id': 'test-session'}
        result = self.command.run('status', context=context)
        
        assert 'test-session' in result
        assert '85/100' in result
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_health_score_indicators(self, mock_get_observer):
        """Test health score emoji indicators"""
        mock_get_observer.return_value = self.mock_observer
        
        # Test excellent health (80+)
        self.mock_monitor._calculate_health_score.return_value = 90
        result = self.command.run('status test-session')
        assert '🟢' in result
        
        # Test good health (60-79)
        self.mock_monitor._calculate_health_score.return_value = 70
        result = self.command.run('status test-session')
        assert '🟡' in result
        
        # Test poor health (<60)
        self.mock_monitor._calculate_health_score.return_value = 45
        result = self.command.run('status test-session')
        assert '🔴' in result


class TestDebbieCommandIntegration:
    """Integration tests for DebbieCommand with real components"""
    
    @patch('interactive_server.debbie_observer.get_observer')
    def test_command_registry_registration(self, mock_get_observer):
        """Test that DebbieCommand is properly registered"""
        from ai_whisperer.commands.registry import CommandRegistry
        
        # Command should be registered
        command_cls = CommandRegistry.get('debbie')
        assert command_cls is not None
        assert command_cls == DebbieCommand
        
        # Should be able to instantiate and run
        command = command_cls()
        assert command.name == 'debbie'
        assert 'Debbie debugging and monitoring commands' in command.description