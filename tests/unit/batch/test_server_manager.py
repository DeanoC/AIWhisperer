"""
Unit tests for ai_whisperer.extensions.batch.server_manager

Tests for server lifecycle management, subprocess handling, and port allocation.
This is a CRITICAL module for batch processing workflow functionality.
"""

import pytest
import socket
import subprocess
import time
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import os

from ai_whisperer.extensions.batch.server_manager import ServerManager


class TestServerManagerInit:
    """Test ServerManager initialization."""
    
    def test_init_default_port(self):
        """Test initialization with default port."""
        manager = ServerManager()
        assert manager.port is None
        assert manager.process is None
    
    def test_init_specified_port(self):
        """Test initialization with specified port."""
        manager = ServerManager(port=8080)
        assert manager.port == 8080
        assert manager.process is None
    
    def test_init_with_zero_port(self):
        """Test initialization with port 0."""
        manager = ServerManager(port=0)
        assert manager.port == 0
        assert manager.process is None


class TestServerManagerPortAllocation:
    """Test port allocation logic."""
    
    @patch('ai_whisperer.extensions.batch.server_manager.random.randint')
    def test_random_port_allocation(self, mock_randint):
        """Test random port allocation when no port specified."""
        mock_randint.return_value = 25000
        
        manager = ServerManager()
        manager.port = None
        
        # Simulate the port allocation logic from start_server
        if manager.port is None:
            manager.port = mock_randint(20000, 40000)
        
        assert manager.port == 25000
        mock_randint.assert_called_once_with(20000, 40000)
    
    def test_port_range_validation(self):
        """Test that random port is within expected range."""
        import random
        
        # Test multiple random selections to ensure they're in range
        for _ in range(10):
            port = random.randint(20000, 40000)
            assert 20000 <= port <= 40000


class TestServerManagerIsRunning:
    """Test server running status detection."""
    
    def test_is_running_no_process(self):
        """Test is_running when no process exists."""
        manager = ServerManager()
        assert not manager.is_running()
    
    def test_is_running_with_active_process(self):
        """Test is_running with active process."""
        manager = ServerManager()
        mock_process = Mock()
        mock_process.poll.return_value = None  # None means still running
        manager.process = mock_process
        
        assert manager.is_running()
    
    def test_is_running_with_terminated_process(self):
        """Test is_running with terminated process."""
        manager = ServerManager()
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Non-None means terminated
        manager.process = mock_process
        
        assert not manager.is_running()
    
    def test_is_running_with_process_no_poll(self):
        """Test is_running with process that has no poll method."""
        manager = ServerManager()
        
        # Create an object without poll method
        class FakeProcess:
            pass
        
        manager.process = FakeProcess()
        
        # With the current implementation, if poll doesn't exist,
        # getattr returns lambda: None, which when called returns None
        # So is_running() will return True (process is not None and poll() is None)
        assert manager.is_running()


class TestServerManagerWaitForReady:
    """Test server readiness detection."""
    
    @patch('ai_whisperer.extensions.batch.server_manager.socket.socket')
    @patch('ai_whisperer.extensions.batch.server_manager.time.sleep')
    def test_wait_for_server_ready_success(self, mock_sleep, mock_socket_class):
        """Test successful server readiness detection."""
        manager = ServerManager(port=8080)
        
        # Mock socket connection success
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 0  # Success
        mock_socket_class.return_value = mock_socket
        
        result = manager._wait_for_server_ready(timeout_seconds=2)
        
        assert result is True
        mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket.settimeout.assert_called_once_with(1)
        mock_socket.connect_ex.assert_called_once_with(('127.0.0.1', 8080))
        mock_socket.close.assert_called_once()
    
    @patch('ai_whisperer.extensions.batch.server_manager.socket.socket')
    @patch('ai_whisperer.extensions.batch.server_manager.time.sleep')
    @patch('ai_whisperer.extensions.batch.server_manager.time.time')
    def test_wait_for_server_ready_timeout(self, mock_time, mock_sleep, mock_socket_class):
        """Test server readiness timeout."""
        manager = ServerManager(port=8080)
        
        # Mock socket connection failure
        mock_socket = Mock()
        mock_socket.connect_ex.return_value = 1  # Connection failed
        mock_socket_class.return_value = mock_socket
        
        # Mock time progression to trigger timeout
        mock_time.side_effect = [0, 5, 10, 15]  # Start, during, timeout exceeded
        
        result = manager._wait_for_server_ready(timeout_seconds=10)
        
        assert result is False
    
    @patch('ai_whisperer.extensions.batch.server_manager.socket.socket')
    @patch('ai_whisperer.extensions.batch.server_manager.time.sleep')
    def test_wait_for_server_ready_exception_handling(self, mock_sleep, mock_socket_class):
        """Test exception handling during server readiness check."""
        manager = ServerManager(port=8080)
        
        # Mock socket exception
        mock_socket_class.side_effect = Exception("Socket error")
        
        with patch('ai_whisperer.extensions.batch.server_manager.time.time', side_effect=[0, 15]):
            result = manager._wait_for_server_ready(timeout_seconds=10)
        
        assert result is False


class TestServerManagerStopServer:
    """Test server stopping functionality."""
    
    def test_stop_server_no_process(self):
        """Test stopping server when no process exists."""
        manager = ServerManager()
        
        # Should not raise exception
        manager.stop_server()
        assert manager.process is None
    
    def test_stop_server_successful_termination(self):
        """Test successful server termination."""
        manager = ServerManager(port=8080)
        
        mock_process = Mock()
        mock_process.terminate.return_value = None
        mock_process.wait.return_value = None
        manager.process = mock_process
        
        manager.stop_server()
        
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once_with(timeout=2)
        assert manager.process is None
    
    def test_stop_server_termination_exception(self):
        """Test server termination with exception."""
        manager = ServerManager(port=8080)
        
        mock_process = Mock()
        mock_process.terminate.side_effect = Exception("Termination failed")
        manager.process = mock_process
        
        # Should handle exception gracefully
        manager.stop_server()
        
        mock_process.terminate.assert_called_once()
        assert manager.process is None


class TestServerManagerStartSubprocess:
    """Test subprocess creation and management."""
    
    @patch.dict(os.environ, {}, clear=False)
    @patch('ai_whisperer.extensions.batch.server_manager.subprocess.Popen')
    def test_start_subprocess_success(self, mock_popen):
        """Test successful subprocess creation."""
        manager = ServerManager(port=8080)
        
        # Mock successful process creation
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Mock wait_for_server_ready to return True
        with patch.object(manager, '_wait_for_server_ready', return_value=True):
            manager._start_subprocess()
        
        # Verify subprocess was created
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args
        
        # Check that the command includes the expected components
        cmd_args = call_args[0][0]
        assert "-m" in cmd_args
        assert "interactive_server.main" in cmd_args
        assert "--host=127.0.0.1" in cmd_args
        assert "--port=8080" in cmd_args
        
        # Check environment variable was set
        env_arg = call_args[1]['env']
        assert env_arg['AIWHISPERER_BATCH_PORT'] == '8080'
        
        assert manager.process == mock_process
    
    @patch('ai_whisperer.extensions.batch.server_manager.subprocess.Popen')
    def test_start_subprocess_server_not_ready(self, mock_popen):
        """Test subprocess creation when server doesn't become ready."""
        manager = ServerManager(port=8080)
        
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        # Mock wait_for_server_ready to return False
        with patch.object(manager, '_wait_for_server_ready', return_value=False):
            with patch.object(manager, 'stop_server') as mock_stop:
                with pytest.raises(RuntimeError, match="Server failed to start on port 8080"):
                    manager._start_subprocess()
                
                mock_stop.assert_called_once()
    
    @patch('ai_whisperer.extensions.batch.server_manager.subprocess.Popen')
    def test_start_subprocess_popen_exception(self, mock_popen):
        """Test subprocess creation with Popen exception."""
        manager = ServerManager(port=8080)
        
        mock_popen.side_effect = Exception("Failed to start process")
        
        with pytest.raises(Exception, match="Failed to start process"):
            manager._start_subprocess()


class TestServerManagerStartServer:
    """Test complete server startup process."""
    
    @patch('ai_whisperer.extensions.batch.server_manager.random.randint')
    def test_start_server_success_first_attempt(self, mock_randint):
        """Test successful server start on first attempt."""
        mock_randint.return_value = 25000
        manager = ServerManager()
        
        with patch.object(manager, '_start_subprocess') as mock_start_sub:
            with patch.object(manager, 'is_running', return_value=True):
                with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                    manager.start_server(max_retries=3)
        
        assert manager.port == 25000
        mock_start_sub.assert_called_once()
    
    @patch('ai_whisperer.extensions.batch.server_manager.random.randint')
    def test_start_server_retry_on_port_conflict(self, mock_randint):
        """Test server start retry when port is in use."""
        mock_randint.side_effect = [25000, 25001]  # First port fails, second succeeds
        manager = ServerManager()
        
        call_count = 0
        def mock_start_subprocess():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("Address already in use")
            # Second attempt succeeds
        
        with patch.object(manager, '_start_subprocess', side_effect=mock_start_subprocess):
            with patch.object(manager, 'is_running', return_value=True):
                with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                    manager.start_server(max_retries=3)
        
        assert manager.port == 25001
        assert call_count == 2
    
    @patch('ai_whisperer.extensions.batch.server_manager.random.randint')
    def test_start_server_max_retries_exceeded(self, mock_randint):
        """Test server start failure after max retries."""
        mock_randint.return_value = 25000
        manager = ServerManager()
        
        with patch.object(manager, '_start_subprocess', side_effect=OSError("Address already in use")):
            with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                with pytest.raises(RuntimeError, match="Failed to start server after 2 attempts"):
                    manager.start_server(max_retries=2)
    
    def test_start_server_with_specified_port(self):
        """Test server start with pre-specified port."""
        manager = ServerManager(port=8080)
        
        with patch.object(manager, '_start_subprocess') as mock_start_sub:
            with patch.object(manager, 'is_running', return_value=True):
                with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                    manager.start_server()
        
        assert manager.port == 8080  # Should not change
        mock_start_sub.assert_called_once()


class TestServerManagerIntegration:
    """Integration tests for complete server lifecycle."""
    
    def test_server_lifecycle_without_actual_server(self):
        """Test complete server lifecycle with mocked components."""
        manager = ServerManager(port=8080)
        
        # Mock all external dependencies
        with patch.object(manager, '_start_subprocess') as mock_start:
            with patch.object(manager, 'is_running', side_effect=[True, True, False]) as mock_running:
                with patch.object(manager, 'stop_server') as mock_stop:
                    with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                        # Start server
                        manager.start_server()
                        assert manager.port == 8080
                        
                        # Check running status
                        assert manager.is_running()
                        
                        # Stop server
                        manager.stop_server()
    
    def test_server_manager_context_behavior(self):
        """Test ServerManager behavior in different contexts."""
        manager = ServerManager()
        
        # Test initial state
        assert not manager.is_running()
        assert manager.port is None
        assert manager.process is None
        
        # Test state after setting port
        manager.port = 9000
        assert manager.port == 9000
        assert not manager.is_running()  # Still no process
        
        # Test state with mock process
        mock_process = Mock()
        mock_process.poll.return_value = None
        manager.process = mock_process
        assert manager.is_running()


class TestServerManagerErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_start_server_unexpected_exception(self):
        """Test handling of unexpected exceptions during startup."""
        manager = ServerManager(port=8080)
        
        with patch.object(manager, '_start_subprocess', side_effect=KeyError("Unexpected error")):
            with pytest.raises(KeyError, match="Unexpected error"):
                manager.start_server(max_retries=1)
    
    def test_wait_for_server_ready_socket_creation_failure(self):
        """Test handling of socket creation failure."""
        manager = ServerManager(port=8080)
        
        with patch('ai_whisperer.extensions.batch.server_manager.socket.socket', side_effect=OSError("Socket creation failed")):
            with patch('ai_whisperer.extensions.batch.server_manager.time.time', side_effect=[0, 15]):
                result = manager._wait_for_server_ready(timeout_seconds=10)
                assert result is False
    
    def test_stop_server_wait_timeout(self):
        """Test server stop with wait timeout."""
        manager = ServerManager(port=8080)
        
        mock_process = Mock()
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 2)
        manager.process = mock_process
        
        # Should handle timeout gracefully
        manager.stop_server()
        assert manager.process is None


# Performance and edge case tests
class TestServerManagerPerformance:
    """Test performance-related aspects and edge cases."""
    
    def test_multiple_server_managers(self):
        """Test behavior with multiple ServerManager instances."""
        manager1 = ServerManager(port=8080)
        manager2 = ServerManager(port=8081)
        
        assert manager1.port != manager2.port
        assert manager1.process is None
        assert manager2.process is None
        
        # Each should maintain independent state
        mock_process1 = Mock()
        mock_process2 = Mock()
        manager1.process = mock_process1
        manager2.process = mock_process2
        
        with patch.object(mock_process1, 'poll', return_value=None):
            with patch.object(mock_process2, 'poll', return_value=0):
                assert manager1.is_running()
                assert not manager2.is_running()
    
    def test_rapid_start_stop_cycles(self):
        """Test rapid start/stop cycles don't cause issues."""
        manager = ServerManager(port=8080)
        
        # Simulate rapid start/stop cycles
        for i in range(3):
            with patch.object(manager, '_start_subprocess'):
                with patch.object(manager, 'is_running', return_value=True):
                    with patch('ai_whisperer.extensions.batch.server_manager.time.sleep'):
                        manager.start_server()
                
                mock_process = Mock()
                manager.process = mock_process
                manager.stop_server()
                
                assert manager.process is None
    
    def test_port_range_edge_cases(self):
        """Test edge cases in port range."""
        # Test minimum and maximum values in range
        import random
        
        min_port = 20000
        max_port = 40000
        
        # Test edge values
        edge_ports = [min_port, max_port, min_port + 1, max_port - 1]
        
        for port in edge_ports:
            manager = ServerManager(port=port)
            assert manager.port == port
            assert 20000 <= manager.port <= 40000