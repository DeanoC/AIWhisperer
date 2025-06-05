"""Monitoring and metrics for MCP server."""

import time
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    method: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    success: Optional[bool] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    transport: Optional[str] = None
    connection_id: Optional[str] = None
    

@dataclass
class TransportMetrics:
    """Metrics for a transport."""
    active_connections: int = 0
    total_connections: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    

@dataclass
class ToolMetrics:
    """Metrics for tool usage."""
    name: str
    invocations: int = 0
    successes: int = 0
    failures: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    last_error: Optional[str] = None
    

class MCPMonitor:
    """Monitor for MCP server metrics and logging."""
    
    def __init__(
        self,
        server_name: str = "aiwhisperer-mcp",
        enable_metrics: bool = True,
        enable_audit_log: bool = True,
        metrics_retention_minutes: int = 60,
        slow_request_threshold_ms: float = 5000,
        max_recent_errors: int = 100,
        audit_log_file: Optional[str] = None
    ):
        self.server_name = server_name
        self.enable_metrics = enable_metrics
        self.enable_audit_log = enable_audit_log
        self.metrics_retention_minutes = metrics_retention_minutes
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.max_recent_errors = max_recent_errors
        
        # Metrics storage
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.active_requests = 0
        
        # Per-method metrics
        self.method_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "errors": 0,
            "total_ms": 0.0,
            "min_ms": float('inf'),
            "max_ms": 0.0
        })
        
        # Transport metrics
        self.transport_metrics: Dict[str, TransportMetrics] = {}
        
        # Tool metrics
        self.tool_metrics: Dict[str, ToolMetrics] = {}
        
        # Recent requests for debugging
        self.recent_requests: deque = deque(maxlen=1000)
        self.recent_errors: deque = deque(maxlen=max_recent_errors)
        self.slow_requests: deque = deque(maxlen=100)
        
        # Audit log
        self.audit_logger = logging.getLogger(f"{self.server_name}.audit")
        if enable_audit_log and audit_log_file:
            # Set up file handler for audit log
            audit_handler = logging.FileHandler(audit_log_file)
            audit_handler.setFormatter(logging.Formatter('%(message)s'))
            self.audit_logger.addHandler(audit_handler)
            self.audit_logger.setLevel(logging.INFO)
            self.audit_logger.propagate = False  # Don't propagate to root logger
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the monitor."""
        if self.enable_metrics:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info(f"MCP monitor started for {self.server_name}")
            
    async def stop(self):
        """Stop the monitor."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        # Log final metrics
        self.log_summary()
        
    @asynccontextmanager
    async def track_request(
        self,
        method: str,
        params: Dict[str, Any],
        transport: Optional[str] = None,
        connection_id: Optional[str] = None
    ):
        """Context manager to track request metrics."""
        request_id = f"{method}_{time.time()}"
        metrics = RequestMetrics(
            method=method,
            start_time=time.time(),
            transport=transport,
            connection_id=connection_id
        )
        
        with self._lock:
            self.request_count += 1
            self.active_requests += 1
            
        # Audit log
        if self.enable_audit_log:
            self.audit_logger.info(json.dumps({
                "event": "request_start",
                "request_id": request_id,
                "method": method,
                "params": self._sanitize_params(params),
                "transport": transport,
                "connection_id": connection_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }))
            
        try:
            yield metrics
            
            # Success
            metrics.success = True
            metrics.end_time = time.time()
            metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
            
            # Update metrics
            self._update_metrics(metrics)
            
            # Audit log success
            if self.enable_audit_log:
                self.audit_logger.info(json.dumps({
                    "event": "request_complete",
                    "request_id": request_id,
                    "method": method,
                    "duration_ms": metrics.duration_ms,
                    "success": True,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                
        except Exception as e:
            # Failure
            metrics.success = False
            metrics.end_time = time.time()
            metrics.duration_ms = (metrics.end_time - metrics.start_time) * 1000
            
            # Extract error details
            if hasattr(e, 'code'):
                metrics.error_code = e.code
            metrics.error_message = str(e)
            
            # Update metrics
            self._update_metrics(metrics)
            
            with self._lock:
                self.error_count += 1
                
            # Audit log error
            if self.enable_audit_log:
                self.audit_logger.error(json.dumps({
                    "event": "request_error",
                    "request_id": request_id,
                    "method": method,
                    "duration_ms": metrics.duration_ms,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                
            raise
            
        finally:
            with self._lock:
                self.active_requests -= 1
                
    def track_tool_execution(
        self,
        tool_name: str,
        start_time: float,
        success: bool,
        error: Optional[str] = None
    ):
        """Track tool execution metrics."""
        duration_ms = (time.time() - start_time) * 1000
        
        with self._lock:
            if tool_name not in self.tool_metrics:
                self.tool_metrics[tool_name] = ToolMetrics(name=tool_name)
                
            metrics = self.tool_metrics[tool_name]
            metrics.invocations += 1
            
            if success:
                metrics.successes += 1
            else:
                metrics.failures += 1
                metrics.last_error = error
                
            metrics.total_duration_ms += duration_ms
            metrics.avg_duration_ms = metrics.total_duration_ms / metrics.invocations
            
    def update_transport_metrics(
        self,
        transport: str,
        event: str,
        value: int = 1
    ):
        """Update transport-specific metrics."""
        with self._lock:
            if transport not in self.transport_metrics:
                self.transport_metrics[transport] = TransportMetrics()
                
            metrics = self.transport_metrics[transport]
            
            if event == "connection_opened":
                metrics.active_connections += 1
                metrics.total_connections += 1
            elif event == "connection_closed":
                metrics.active_connections = max(0, metrics.active_connections - 1)
            elif event == "message_sent":
                metrics.messages_sent += value
            elif event == "message_received":
                metrics.messages_received += value
            elif event == "bytes_sent":
                metrics.bytes_sent += value
            elif event == "bytes_received":
                metrics.bytes_received += value
            elif event == "error":
                metrics.errors += 1
                
    def _update_metrics(self, request: RequestMetrics):
        """Update internal metrics."""
        with self._lock:
            # Update method metrics
            method_stats = self.method_metrics[request.method]
            method_stats["count"] += 1
            
            if request.success:
                method_stats["total_ms"] += request.duration_ms
                method_stats["min_ms"] = min(method_stats["min_ms"], request.duration_ms)
                method_stats["max_ms"] = max(method_stats["max_ms"], request.duration_ms)
            else:
                method_stats["errors"] += 1
                
            # Track recent requests
            self.recent_requests.append(asdict(request))
            
            # Track errors
            if not request.success:
                self.recent_errors.append({
                    **asdict(request),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
            # Track slow requests
            if request.duration_ms > self.slow_request_threshold_ms:
                self.slow_requests.append({
                    **asdict(request),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                logger.warning(
                    f"Slow request detected: {request.method} took {request.duration_ms:.2f}ms"
                )
                
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for logging (remove sensitive data)."""
        # Create a copy to avoid modifying original
        sanitized = params.copy()
        
        # Remove potentially sensitive fields
        sensitive_fields = ["password", "token", "secret", "key", "auth"]
        
        for field in sensitive_fields:
            for key in list(sanitized.keys()):
                if field in key.lower():
                    sanitized[key] = "[REDACTED]"
                
        return sanitized
        
    async def _cleanup_loop(self):
        """Periodically clean up old metrics."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                cutoff_time = time.time() - (self.metrics_retention_minutes * 60)
                
                with self._lock:
                    # Clean up old requests
                    while self.recent_requests and self.recent_requests[0]["start_time"] < cutoff_time:
                        self.recent_requests.popleft()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        uptime_seconds = time.time() - self.start_time
        
        with self._lock:
            # Calculate aggregates
            total_duration_ms = sum(
                m["total_ms"] for m in self.method_metrics.values()
            )
            
            avg_duration_ms = (
                total_duration_ms / self.request_count
                if self.request_count > 0 else 0
            )
            
            return {
                "server": {
                    "name": self.server_name,
                    "uptime_seconds": uptime_seconds,
                    "uptime_human": str(timedelta(seconds=int(uptime_seconds)))
                },
                "requests": {
                    "total": self.request_count,
                    "active": self.active_requests,
                    "errors": self.error_count,
                    "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
                    "avg_duration_ms": avg_duration_ms
                },
                "methods": dict(self.method_metrics),
                "transports": {
                    name: asdict(metrics)
                    for name, metrics in self.transport_metrics.items()
                },
                "tools": {
                    name: asdict(metrics)
                    for name, metrics in self.tool_metrics.items()
                },
                "recent_errors": list(self.recent_errors)[-10:],  # Last 10 errors
                "slow_requests": list(self.slow_requests)[-10:]  # Last 10 slow requests
            }
            
    def get_health(self) -> Dict[str, Any]:
        """Get health check information."""
        metrics = self.get_metrics()
        
        # Determine health status
        error_rate = metrics["requests"]["error_rate"]
        active_requests = metrics["requests"]["active"]
        
        if error_rate > 0.5:  # >50% errors
            status = "unhealthy"
        elif error_rate > 0.1:  # >10% errors
            status = "degraded"
        else:
            status = "healthy"
            
        return {
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": metrics["server"]["uptime_human"],
            "metrics": {
                "requests_total": metrics["requests"]["total"],
                "requests_active": active_requests,
                "error_rate": f"{error_rate:.2%}",
                "avg_latency_ms": f"{metrics['requests']['avg_duration_ms']:.2f}"
            },
            "transports": {
                name: {
                    "active_connections": t["active_connections"],
                    "total_connections": t["total_connections"]
                }
                for name, t in metrics["transports"].items()
            }
        }
        
    def log_summary(self):
        """Log a summary of metrics."""
        metrics = self.get_metrics()
        
        logger.info(
            f"MCP Server Metrics Summary:\n"
            f"  Uptime: {metrics['server']['uptime_human']}\n"
            f"  Total Requests: {metrics['requests']['total']}\n"
            f"  Error Rate: {metrics['requests']['error_rate']:.2%}\n"
            f"  Avg Latency: {metrics['requests']['avg_duration_ms']:.2f}ms"
        )
        
        # Log per-method stats
        for method, stats in metrics["methods"].items():
            if stats["count"] > 0:
                avg_ms = stats["total_ms"] / stats["count"]
                logger.info(
                    f"  {method}: {stats['count']} calls, "
                    f"{stats['errors']} errors, "
                    f"avg {avg_ms:.2f}ms"
                )