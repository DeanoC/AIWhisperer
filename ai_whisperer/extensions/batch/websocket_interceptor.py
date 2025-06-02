"""
WebSocket message interceptor for Debbie the Debugger.
Provides non-invasive monitoring of WebSocket communications.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import json
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from ai_whisperer.core.logging import EnhancedLogMessage, LogLevel, LogSource, ComponentType
from ai_whisperer.extensions.monitoring.debbie_logger import DebbieLogger
from ai_whisperer.extensions.monitoring.log_aggregator import LogAggregator
from ai_whisperer.extensions.batch.monitoring import MonitoringEvent, DebbieMonitor

logger = logging.getLogger(__name__)

class MessageDirection(Enum):
    """Direction of WebSocket messages"""
    INCOMING = "incoming"  # Server to client
    OUTGOING = "outgoing"  # Client to server

class MessageType(Enum):
    """Types of JSON-RPC messages"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class InterceptedMessage:
    """Represents an intercepted WebSocket message"""
    message_id: str
    direction: MessageDirection
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    method: Optional[str] = None
    correlation_id: Optional[str] = None  # For matching requests/responses
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'message_id': self.message_id,
            'direction': self.direction.value,
            'message_type': self.message_type.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id,
            'method': self.method,
            'correlation_id': self.correlation_id
        }

class MessageInterceptor:
    """Base class for message interception"""
    
    def __init__(self):
        self.handlers: List[Callable] = []
        self.filters: List[Callable] = []
        
    def add_handler(self, handler: Callable):
        """Add a message handler"""
        self.handlers.append(handler)
        
    def add_filter(self, filter_func: Callable) -> None:
        """Add a message filter"""
        self.filters.append(filter_func)
        
    async def intercept(self, message: InterceptedMessage):
        """Process intercepted message through handlers"""
        # Apply filters
        for filter_func in self.filters:
            if not filter_func(message):
                return  # Message filtered out
        
        # Process through handlers
        for handler in self.handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(f"Error in message handler: {e}")

class WebSocketInterceptor:
    """
    Intercepts WebSocket messages for monitoring and debugging.
    Acts as a transparent proxy between client and server.
    """
    
    def __init__(self, monitor: Optional[DebbieMonitor] = None,
                 log_aggregator: Optional[LogAggregator] = None):
        """
        Initialize interceptor.
        
        Args:
            monitor: Debbie's monitoring system
            log_aggregator: Log aggregation system
        """
        self.monitor = monitor
        self.log_aggregator = log_aggregator or LogAggregator()
        self.debbie_logger = DebbieLogger("debbie.websocket")
        
        # Interceptors
        self.request_interceptor = MessageInterceptor()
        self.response_interceptor = MessageInterceptor()
        self.notification_interceptor = MessageInterceptor()
        
        # State tracking
        self.pending_requests: Dict[Union[str, int], InterceptedMessage] = {}
        self.session_mapping: Dict[str, str] = {}  # connection_id -> session_id
        self.message_count = 0
        self.start_time = datetime.now()
        
        # Performance tracking
        self.response_times: Dict[str, List[float]] = {}
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers"""
        # Request handlers
        self.request_interceptor.add_handler(self._handle_request)
        
        # Response handlers
        self.response_interceptor.add_handler(self._handle_response)
        
        # Notification handlers
        self.notification_interceptor.add_handler(self._handle_notification)
    
    async def intercept_message(self, raw_message: str, 
                              direction: MessageDirection,
                              connection_id: Optional[str] = None) -> str:
        """
        Intercept and process a WebSocket message.
        
        Args:
            raw_message: Raw message string
            direction: Message direction
            connection_id: Optional connection identifier
            
        Returns:
            The original message (unchanged)
        """
        try:
            # Parse message
            data = json.loads(raw_message)
            
            # Determine message type
            message_type = self._determine_message_type(data)
            
            # Create intercepted message
            message = InterceptedMessage(
                message_id=f"msg_{self.message_count}",
                direction=direction,
                message_type=message_type,
                content=data,
                session_id=self.session_mapping.get(connection_id)
            )
            
            self.message_count += 1
            
            # Extract method if present
            if 'method' in data:
                message.method = data['method']
            elif 'id' in data and data['id'] in self.pending_requests:
                # This is a response to a request
                original_request = self.pending_requests[data['id']]
                message.method = original_request.method
                message.correlation_id = original_request.message_id
            
            # Process based on type
            if message_type == MessageType.REQUEST:
                await self.request_interceptor.intercept(message)
            elif message_type == MessageType.RESPONSE:
                await self.response_interceptor.intercept(message)
            elif message_type == MessageType.NOTIFICATION:
                await self.notification_interceptor.intercept(message)
            
            # Log to aggregator
            self._log_message(message)
            
            # Update session mapping if needed
            self._update_session_mapping(message, connection_id)
            
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON message intercepted: {raw_message[:100]}")
        except Exception as e:
            logger.error(f"Error intercepting message: {e}")
        
        # Always return original message unchanged
        return raw_message
    
    def _determine_message_type(self, data: Dict[str, Any]) -> MessageType:
        """Determine the type of JSON-RPC message"""
        if 'method' in data and 'id' in data:
            return MessageType.REQUEST
        elif 'method' in data and 'id' not in data:
            return MessageType.NOTIFICATION
        elif 'result' in data or 'error' in data:
            return MessageType.RESPONSE
        elif 'error' in data:
            return MessageType.ERROR
        else:
            return MessageType.UNKNOWN
    
    async def _handle_request(self, message: InterceptedMessage):
        """Handle intercepted request"""
        # Track pending request
        request_id = message.content.get('id')
        if request_id is not None:
            self.pending_requests[request_id] = message
        
        # Extract session info
        params = message.content.get('params', {})
        
        # Handle specific methods
        method = message.method
        if method == 'startSession':
            await self._handle_session_start(message, params)
        elif method == 'sendUserMessage':
            await self._handle_user_message(message, params)
        elif method == 'stopSession':
            await self._handle_session_stop(message, params)
        
        # Emit monitoring event
        if self.monitor and message.session_id:
            await self.monitor._emit_event(MonitoringEvent.MESSAGE_SENT, {
                'session_id': message.session_id,
                'method': method,
                'timestamp': message.timestamp.isoformat()
            })
    
    async def _handle_response(self, message: InterceptedMessage):
        """Handle intercepted response"""
        # Match with request
        response_id = message.content.get('id')
        if response_id in self.pending_requests:
            request = self.pending_requests.pop(response_id)
            
            # Calculate response time
            response_time = (message.timestamp - request.timestamp).total_seconds() * 1000
            
            # Track performance
            if request.method:
                if request.method not in self.response_times:
                    self.response_times[request.method] = []
                self.response_times[request.method].append(response_time)
            
            # Log performance
            if response_time > 1000:  # Slow response
                self.debbie_logger.warning(
                    f"Slow response for {request.method}: {response_time:.0f}ms",
                    session_id=message.session_id,
                    details={
                        'method': request.method,
                        'response_time_ms': response_time
                    }
                )
        
        # Check for errors
        if 'error' in message.content:
            await self._handle_error_response(message)
    
    async def _handle_notification(self, message: InterceptedMessage):
        """Handle intercepted notification"""
        # Notifications don't have IDs and don't expect responses
        method = message.method
        
        # Handle specific notifications
        if method == 'toolExecutionStarted':
            await self._handle_tool_start_notification(message)
        elif method == 'toolExecutionCompleted':
            await self._handle_tool_end_notification(message)
        elif method == 'agentMessage':
            await self._handle_agent_message(message)
    
    async def _handle_session_start(self, message: InterceptedMessage, params: Dict[str, Any]):
        """Handle session start request"""
        user_id = params.get('userId')
        self.debbie_logger.info(
            f"Session start requested by {user_id}",
            details={'params': params}
        )
    
    async def _handle_user_message(self, message: InterceptedMessage, params: Dict[str, Any]):
        """Handle user message"""
        session_id = params.get('sessionId')
        user_message = params.get('message', '')
        
        if session_id:
            message.session_id = session_id
            
            # Update monitor
            if self.monitor:
                await self.monitor._emit_event(MonitoringEvent.MESSAGE_SENT, {
                    'session_id': session_id,
                    'message': user_message[:100],  # Truncate for logging
                    'timestamp': message.timestamp.isoformat()
                })
    
    async def _handle_session_stop(self, message: InterceptedMessage, params: Dict[str, Any]):
        """Handle session stop request"""
        session_id = params.get('sessionId')
        if session_id:
            self.debbie_logger.info(
                f"Session stop requested: {session_id}",
                session_id=session_id
            )
            
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop_monitoring(session_id)
    
    async def _handle_error_response(self, message: InterceptedMessage):
        """Handle error response"""
        error = message.content.get('error', {})
        self.debbie_logger.error(
            f"Error response: {error.get('message', 'Unknown error')}",
            session_id=message.session_id,
            details={'error': error}
        )
        
        # Emit error event
        if self.monitor and message.session_id:
            await self.monitor._emit_event(MonitoringEvent.ERROR_DETECTED, {
                'session_id': message.session_id,
                'error': error,
                'timestamp': message.timestamp.isoformat()
            })
    
    async def _handle_tool_start_notification(self, message: InterceptedMessage):
        """Handle tool execution start notification"""
        params = message.content.get('params', {})
        tool_name = params.get('toolName')
        session_id = params.get('sessionId')
        
        if self.monitor and session_id:
            await self.monitor._emit_event(MonitoringEvent.TOOL_EXECUTION_START, {
                'session_id': session_id,
                'tool_name': tool_name,
                'timestamp': message.timestamp.isoformat()
            })
    
    async def _handle_tool_end_notification(self, message: InterceptedMessage):
        """Handle tool execution end notification"""
        params = message.content.get('params', {})
        tool_name = params.get('toolName')
        session_id = params.get('sessionId')
        duration_ms = params.get('durationMs')
        
        if self.monitor and session_id:
            await self.monitor._emit_event(MonitoringEvent.TOOL_EXECUTION_END, {
                'session_id': session_id,
                'tool_name': tool_name,
                'duration_ms': duration_ms,
                'timestamp': message.timestamp.isoformat()
            })
    
    async def _handle_agent_message(self, message: InterceptedMessage):
        """Handle agent message notification"""
        params = message.content.get('params', {})
        session_id = params.get('sessionId')
        
        if self.monitor and session_id:
            await self.monitor._emit_event(MonitoringEvent.MESSAGE_RECEIVED, {
                'session_id': session_id,
                'timestamp': message.timestamp.isoformat()
            })
    
    def _update_session_mapping(self, message: InterceptedMessage, connection_id: Optional[str]):
        """Update connection to session mapping"""
        if not connection_id:
            return
        
        # Check for session ID in various places
        session_id = None
        
        if message.session_id:
            session_id = message.session_id
        elif 'params' in message.content:
            session_id = message.content['params'].get('sessionId')
        elif 'result' in message.content:
            session_id = message.content['result'].get('sessionId')
        
        if session_id:
            self.session_mapping[connection_id] = session_id
            
            # Start monitoring if not already
            if self.monitor and session_id not in self.monitor.monitored_sessions:
                asyncio.create_task(self.monitor.start_monitoring(session_id))
    
    def _log_message(self, message: InterceptedMessage):
        """Log intercepted message"""
        log_entry = EnhancedLogMessage(
            level=LogLevel.DEBUG,
            component=ComponentType.MONITOR,
            source=LogSource.WEBSOCKET,
            action="message_intercepted",
            event_summary=f"{message.direction.value} {message.message_type.value}: {message.method or 'unknown'}",
            session_id=message.session_id,
            correlation_id=message.correlation_id,
            details=message.to_dict()
        )
        
        self.log_aggregator.add_log(log_entry)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get interceptor statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        stats = {
            'message_count': self.message_count,
            'pending_requests': len(self.pending_requests),
            'active_sessions': len(set(self.session_mapping.values())),
            'uptime_seconds': uptime,
            'messages_per_second': self.message_count / uptime if uptime > 0 else 0,
            'method_performance': {}
        }
        
        # Calculate average response times
        for method, times in self.response_times.items():
            if times:
                stats['method_performance'][method] = {
                    'avg_ms': sum(times) / len(times),
                    'max_ms': max(times),
                    'min_ms': min(times),
                    'count': len(times)
                }
        
        return stats
    
    def create_intercepting_connection(self, original_connection: Any) -> 'InterceptingWebSocket':
        """
        Create an intercepting wrapper around a WebSocket connection.
        
        Args:
            original_connection: The original WebSocket connection
            
        Returns:
            Wrapped connection with interception
        """
        return InterceptingWebSocket(original_connection, self)

class InterceptingWebSocket:
    """
    WebSocket wrapper that intercepts messages.
    Mimics the WebSocket client interface.
    """
    
    def __init__(self, connection: Any, interceptor: WebSocketInterceptor):
        self._connection = connection
        self._interceptor = interceptor
        self._connection_id = f"conn_{id(self)}"
    
    async def send(self, data: Union[str, bytes]):
        """Send data through the connection with interception"""
        if isinstance(data, str):
            # Intercept outgoing message
            intercepted = await self._interceptor.intercept_message(
                data,
                MessageDirection.OUTGOING,
                self._connection_id
            )
            await self._connection.send(intercepted)
        else:
            # Binary data - pass through
            await self._connection.send(data)
    
    async def recv(self) -> Union[str, bytes]:
        """Receive data from the connection with interception"""
        data = await self._connection.recv()
        
        if isinstance(data, str):
            # Intercept incoming message
            intercepted = await self._interceptor.intercept_message(
                data,
                MessageDirection.INCOMING,
                self._connection_id
            )
            return intercepted
        else:
            # Binary data - pass through
            return data
    
    async def close(self):
        """Close the connection"""
        await self._connection.close()
    
    async def ping(self):
        """Send ping"""
        await self._connection.ping()
    
    async def pong(self):
        """Send pong"""
        await self._connection.pong()
    
    @property
    def closed(self):
        """Check if connection is closed"""
        return self._connection.closed
    
    def __getattr__(self, name):
        """Proxy other attributes to the original connection"""
        return getattr(self._connection, name)
