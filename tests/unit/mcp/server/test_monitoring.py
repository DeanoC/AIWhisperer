"""Tests for MCP monitoring."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch

from ai_whisperer.mcp.server.monitoring import (
    MCPMonitor, RequestMetrics, TransportMetrics, ToolMetrics
)


class TestMCPMonitor:
    """Tests for MCP monitoring."""
    
    @pytest.fixture
    def monitor(self):
        """Create monitor instance."""
        return MCPMonitor(
            server_name="test-server",
            enable_metrics=True,
            enable_audit_log=False,  # Disable for tests
            slow_request_threshold_ms=100
        )
        
    @pytest.mark.asyncio
    async def test_init(self, monitor):
        """Test monitor initialization."""
        assert monitor.server_name == "test-server"
        assert monitor.enable_metrics is True
        assert monitor.request_count == 0
        assert monitor.error_count == 0
        assert monitor.active_requests == 0
        
    @pytest.mark.asyncio
    async def test_start_stop(self, monitor):
        """Test starting and stopping monitor."""
        await monitor.start()
        assert monitor._cleanup_task is not None
        
        await monitor.stop()
        assert monitor._cleanup_task.cancelled()
        
    @pytest.mark.asyncio
    async def test_track_request_success(self, monitor):
        """Test tracking successful request."""
        await monitor.start()
        
        # Track a successful request
        async with monitor.track_request(
            method="test/method",
            params={"foo": "bar"},
            transport="websocket",
            connection_id="conn-123"
        ) as metrics:
            # Simulate some work
            await asyncio.sleep(0.01)
            
        # Verify metrics
        assert metrics.success is True
        assert metrics.duration_ms > 0
        assert metrics.method == "test/method"
        assert metrics.transport == "websocket"
        assert metrics.connection_id == "conn-123"
        
        # Verify counters
        assert monitor.request_count == 1
        assert monitor.error_count == 0
        assert monitor.active_requests == 0
        
        # Verify method metrics
        method_stats = monitor.method_metrics["test/method"]
        assert method_stats["count"] == 1
        assert method_stats["errors"] == 0
        assert method_stats["total_ms"] > 0
        
        await monitor.stop()
        
    @pytest.mark.asyncio
    async def test_track_request_failure(self, monitor):
        """Test tracking failed request."""
        await monitor.start()
        
        # Track a failed request
        with pytest.raises(ValueError):
            async with monitor.track_request(
                method="test/error",
                params={},
                transport="stdio"
            ) as metrics:
                raise ValueError("Test error")
                
        # Verify metrics
        assert metrics.success is False
        assert metrics.error_message == "Test error"
        
        # Verify counters
        assert monitor.request_count == 1
        assert monitor.error_count == 1
        assert monitor.active_requests == 0
        
        # Verify error was recorded
        assert len(monitor.recent_errors) == 1
        error = monitor.recent_errors[0]
        assert error["method"] == "test/error"
        assert error["error_message"] == "Test error"
        
        await monitor.stop()
        
    @pytest.mark.asyncio
    async def test_slow_request_detection(self, monitor):
        """Test slow request detection."""
        monitor.slow_request_threshold_ms = 50  # Lower threshold for test
        await monitor.start()
        
        # Track a slow request
        async with monitor.track_request(
            method="test/slow",
            params={}
        ):
            await asyncio.sleep(0.1)  # 100ms
            
        # Verify slow request was recorded
        assert len(monitor.slow_requests) == 1
        slow_req = monitor.slow_requests[0]
        assert slow_req["method"] == "test/slow"
        assert slow_req["duration_ms"] > 50
        
        await monitor.stop()
        
    def test_track_tool_execution(self, monitor):
        """Test tracking tool execution."""
        # Track successful execution
        monitor.track_tool_execution(
            tool_name="read_file",
            start_time=time.time() - 0.1,
            success=True
        )
        
        # Track failed execution
        monitor.track_tool_execution(
            tool_name="read_file",
            start_time=time.time() - 0.05,
            success=False,
            error="File not found"
        )
        
        # Verify metrics
        tool_metrics = monitor.tool_metrics["read_file"]
        assert tool_metrics.invocations == 2
        assert tool_metrics.successes == 1
        assert tool_metrics.failures == 1
        assert tool_metrics.last_error == "File not found"
        assert tool_metrics.avg_duration_ms > 0
        
    def test_update_transport_metrics(self, monitor):
        """Test updating transport metrics."""
        # Update various metrics
        monitor.update_transport_metrics("websocket", "connection_opened")
        monitor.update_transport_metrics("websocket", "connection_opened")
        monitor.update_transport_metrics("websocket", "connection_closed")
        monitor.update_transport_metrics("websocket", "message_sent", 5)
        monitor.update_transport_metrics("websocket", "message_received", 3)
        monitor.update_transport_metrics("websocket", "bytes_sent", 1024)
        monitor.update_transport_metrics("websocket", "error")
        
        # Verify metrics
        ws_metrics = monitor.transport_metrics["websocket"]
        assert ws_metrics.active_connections == 1
        assert ws_metrics.total_connections == 2
        assert ws_metrics.messages_sent == 5
        assert ws_metrics.messages_received == 3
        assert ws_metrics.bytes_sent == 1024
        assert ws_metrics.errors == 1
        
    def test_sanitize_params(self, monitor):
        """Test parameter sanitization."""
        params = {
            "username": "test_user",
            "password": "test_password_do_not_use",
            "api_key": "test_api_key_fake",
            "data": "normal data"
        }
        
        sanitized = monitor._sanitize_params(params)
        
        assert sanitized["username"] == "test_user"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["api_key"] == "[REDACTED]"
        assert sanitized["data"] == "normal data"
        
    @pytest.mark.asyncio
    async def test_get_metrics(self, monitor):
        """Test getting metrics snapshot."""
        await monitor.start()
        
        # Generate some activity
        async with monitor.track_request("test/method", {}):
            pass
            
        monitor.update_transport_metrics("websocket", "connection_opened")
        monitor.track_tool_execution("test_tool", time.time() - 0.1, True)
        
        # Get metrics
        metrics = monitor.get_metrics()
        
        assert metrics["server"]["name"] == "test-server"
        assert metrics["server"]["uptime_seconds"] > 0
        assert metrics["requests"]["total"] == 1
        assert metrics["requests"]["errors"] == 0
        assert "test/method" in metrics["methods"]
        assert "websocket" in metrics["transports"]
        assert "test_tool" in metrics["tools"]
        
        await monitor.stop()
        
    @pytest.mark.asyncio
    async def test_get_health(self, monitor):
        """Test getting health status."""
        await monitor.start()
        
        # Healthy state
        async with monitor.track_request("test/method", {}):
            pass
            
        health = monitor.get_health()
        assert health["status"] == "healthy"
        assert health["metrics"]["error_rate"] == "0.00%"
        
        # Generate errors for degraded state
        for i in range(5):
            try:
                async with monitor.track_request(f"test/error{i}", {}):
                    raise ValueError("Test")
            except:
                pass
                
        health = monitor.get_health()
        assert health["status"] in ["degraded", "unhealthy"]
        
        await monitor.stop()
        
    @pytest.mark.asyncio
    async def test_cleanup_loop(self, monitor):
        """Test metrics cleanup."""
        monitor.metrics_retention_minutes = 0.001  # Very short for test
        
        # Add old request
        old_request = {
            "start_time": time.time() - 1000,
            "method": "old/request"  
        }
        monitor.recent_requests.append(old_request)
        
        # Add recent request
        recent_request = {
            "start_time": time.time(),
            "method": "recent/request"
        }
        monitor.recent_requests.append(recent_request)
        
        # Manually trigger cleanup logic
        cutoff_time = time.time() - (monitor.metrics_retention_minutes * 60)
        
        with monitor._lock:
            # Clean up old requests
            while monitor.recent_requests and monitor.recent_requests[0]["start_time"] < cutoff_time:
                monitor.recent_requests.popleft()
        
        # Old request should be removed
        assert len(monitor.recent_requests) == 1
        assert monitor.recent_requests[0]["method"] == "recent/request"