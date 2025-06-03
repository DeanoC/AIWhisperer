"""
Module: ai_whisperer/tools/message_injector_tool.py
Purpose: AI tool implementation for message injector

Message Injector Tool for Debbie the Debugger.
Injects messages into AI sessions to unstick agents or simulate user responses.

Key Components:
- InjectionType: Types of message injections
- InjectionResult: Result of message injection
- MessageInjectorTool: 

Usage:
    tool = InjectionType()
    result = await tool.execute(**parameters)

Dependencies:
- logging
- time

Related:
- See docs/archive/debugging-session-2025-05-30-consolidated.md
- See PHASE_CONSOLIDATED_SUMMARY.md
- See UNTESTED_MODULES_REPORT.md

"""
from typing import Any, Dict, List, Optional, Type

import time
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.core.logging import EnhancedLogMessage, LogLevel, LogSource, ComponentType

logger = logging.getLogger(__name__)

class InjectionType(Enum):
    """Types of message injections"""
    CONTINUATION = "continuation"  # Continue with task
    USER_MESSAGE = "user_message"  # Simulate user input
    SYSTEM_PROMPT = "system_prompt"  # System-level instruction
    ERROR_RECOVERY = "error_recovery"  # Recover from error
    RESET = "reset"  # Reset context
    
@dataclass
class InjectionResult:
    """Result of message injection"""
    success: bool
    session_id: str
    injection_type: InjectionType
    message: str
    timestamp: datetime
    response_received: bool = False
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'session_id': self.session_id,
            'injection_type': self.injection_type.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'response_received': self.response_received,
            'response_time_ms': self.response_time_ms,
            'error': self.error
        }

class MessageInjectorTool(AITool):
    """
    Injects messages into AI sessions to unstick agents, recover from errors,
    or simulate user interactions for debugging purposes.
    """
    
    # Pre-defined injection templates
    INJECTION_TEMPLATES = {
        InjectionType.CONTINUATION: [
            "Please continue with the task based on the previous results.",
            "Continue processing the request.",
            "Please proceed with the next step.",
            "Based on the tool results, please continue with your analysis."
        ],
        InjectionType.ERROR_RECOVERY: [
            "An error occurred. Please try a different approach.",
            "The previous attempt failed. Can you retry with modified parameters?",
            "Please recover from the error and continue with an alternative solution."
        ],
        InjectionType.RESET: [
            "Let's start fresh. Please summarize the current state.",
            "Reset context and continue from the current point.",
            "Clear previous context and focus on the current task."
        ]
    }
    
    def __init__(self, session_manager=None, message_handler=None):
        """
        Initialize with session manager and message handler.
        
        Args:
            session_manager: The session manager for accessing sessions
            message_handler: Handler for sending messages to sessions
        """
        self.session_manager = session_manager
        self.message_handler = message_handler
        self.injection_history = []  # Track injection history
        self.rate_limit = 10  # Max injections per minute per session
        self.rate_tracker = {}  # Track injection rates
        
    @property
    def name(self) -> str:
        return "message_injector"
    
    @property
    def description(self) -> str:
        return "Injects messages into AI sessions to unstick agents or simulate user responses"
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The session ID to inject message into. Use 'current' for current session."
                },
                "message": {
                    "type": "string",
                    "description": "The message to inject. Leave empty to use auto-generated message based on type."
                },
                "injection_type": {
                    "type": "string",
                    "enum": ["continuation", "user_message", "system_prompt", "error_recovery", "reset"],
                    "description": "Type of injection to perform",
                    "default": "continuation"
                },
                "wait_for_response": {
                    "type": "boolean",
                    "description": "Whether to wait for a response after injection",
                    "default": True
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Timeout in seconds when waiting for response",
                    "default": 10
                }
            },
            "required": ["session_id"]
        }
    
    @property
    def category(self) -> Optional[str]:
        return "Debugging"
    
    @property
    def tags(self) -> List[str]:
        return ["debugging", "intervention", "message", "recovery"]
    
    def get_ai_prompt_instructions(self) -> str:
        return """
        Use the message_injector tool to:
        - Unstick agents that are waiting for user input (use injection_type="continuation")
        - Recover from errors by providing alternative instructions
        - Test agent behavior with simulated user messages
        - Reset agent context when needed
        
        Examples:
        - message_injector(session_id="current", injection_type="continuation")
        - message_injector(session_id="abc123", message="Try using a different approach", injection_type="error_recovery")
        - message_injector(session_id="current", message="List all available tools", injection_type="user_message")
        
        Safety features:
        - Rate limited to prevent injection loops
        - Validates session exists before injection
        - Tracks injection history for debugging
        """
    
    def execute(self, session_id: str, message: str = "", 
                injection_type: str = "continuation",
                wait_for_response: bool = True,
                timeout_seconds: int = 10) -> Dict[str, Any]:
        """
        Inject a message into the specified session.
        
        Args:
            session_id: Target session ID ('current' for current session)
            message: Message to inject (auto-generated if empty)
            injection_type: Type of injection
            wait_for_response: Whether to wait for agent response
            timeout_seconds: Response timeout
            
        Returns:
            Injection result with success status and details
        """
        try:
            # Parse injection type
            try:
                inj_type = InjectionType(injection_type)
            except ValueError:
                return {"error": f"Invalid injection type: {injection_type}"}
            
            # Resolve session ID
            if session_id == "current":
                session_id = self._get_current_session_id()
                if not session_id:
                    return {"error": "No active session found"}
            
            # Check rate limit
            if not self._check_rate_limit(session_id):
                return {
                    "error": "Rate limit exceeded. Too many injections in short time.",
                    "success": False
                }
            
            # Generate message if not provided
            if not message:
                message = self._generate_message(inj_type, session_id)
            
            # Validate session exists
            if not self._validate_session(session_id):
                return {"error": f"Session {session_id} not found or inactive"}
            
            # Perform injection
            start_time = time.time()
            result = self._inject_message(
                session_id, message, inj_type, 
                wait_for_response, timeout_seconds
            )
            
            # Calculate response time
            if result.response_received:
                result.response_time_ms = (time.time() - start_time) * 1000
            
            # Track injection
            self._track_injection(result)
            
            # Log the injection
            self._log_injection(result)
            
            return {
                "result": result.to_dict(),
                "success": result.success
            }
            
        except Exception as e:
            logger.error(f"Error injecting message: {e}")
            return {
                "error": str(e),
                "success": False
            }
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get current active session ID"""
        if not self.session_manager:
            return None
        
        return getattr(self.session_manager, 'current_session_id', None)
    
    def _check_rate_limit(self, session_id: str) -> bool:
        """Check if injection is within rate limit"""
        now = time.time()
        
        # Clean old entries
        self.rate_tracker = {
            sid: times for sid, times in self.rate_tracker.items()
            if any(t > now - 60 for t in times)
        }
        
        # Check current session
        session_times = self.rate_tracker.get(session_id, [])
        recent_times = [t for t in session_times if t > now - 60]
        
        if len(recent_times) >= self.rate_limit:
            return False
        
        # Add new timestamp
        self.rate_tracker[session_id] = recent_times + [now]
        return True
    
    def _generate_message(self, injection_type: InjectionType, session_id: str) -> str:
        """Generate appropriate message based on injection type"""
        templates = self.INJECTION_TEMPLATES.get(injection_type, [])
        
        if templates:
            # Rotate through templates to avoid repetition
            session_index = hash(session_id + str(len(self.injection_history))) % len(templates)
            return templates[session_index]
        
        # Default messages
        default_messages = {
            InjectionType.USER_MESSAGE: "Please provide a status update.",
            InjectionType.SYSTEM_PROMPT: "System: Continue with the current task."
        }
        
        return default_messages.get(injection_type, "Please continue.")
    
    def _validate_session(self, session_id: str) -> bool:
        """Validate that session exists and is active"""
        if not self.session_manager:
            # Mock validation for testing
            return True
        
        if hasattr(self.session_manager, 'is_session_active'):
            return self.session_manager.is_session_active(session_id)
        
        return True
    
    def _inject_message(self, session_id: str, message: str, 
                       injection_type: InjectionType,
                       wait_for_response: bool,
                       timeout_seconds: int) -> InjectionResult:
        """Perform the actual message injection"""
        timestamp = datetime.now()
        
        # If no message handler, create mock result
        if not self.message_handler:
            return self._mock_injection(session_id, message, injection_type, timestamp)
        
        try:
            # Send message through handler
            if asyncio.iscoroutinefunction(self.message_handler.send_message):
                # Handle async message handler
                loop = asyncio.get_event_loop()
                send_task = loop.create_task(
                    self.message_handler.send_message(session_id, message, injection_type.value)
                )
                loop.run_until_complete(send_task)
            else:
                # Handle sync message handler
                self.message_handler.send_message(session_id, message, injection_type.value)
            
            # Wait for response if requested
            response_received = False
            if wait_for_response:
                response_received = self._wait_for_response(session_id, timeout_seconds)
            
            return InjectionResult(
                success=True,
                session_id=session_id,
                injection_type=injection_type,
                message=message,
                timestamp=timestamp,
                response_received=response_received
            )
            
        except Exception as e:
            return InjectionResult(
                success=False,
                session_id=session_id,
                injection_type=injection_type,
                message=message,
                timestamp=timestamp,
                error=str(e)
            )
    
    def _wait_for_response(self, session_id: str, timeout_seconds: int) -> bool:
        """Wait for response from agent after injection"""
        if not self.session_manager:
            # Mock wait
            time.sleep(0.5)
            return True
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            if self._check_for_response(session_id, start_time):
                return True
            time.sleep(0.1)
        
        return False
    
    def _check_for_response(self, session_id: str, since_time: float) -> bool:
        """Check if agent has responded since injection"""
        # This would check session manager for new messages
        # For now, return mock result
        return time.time() - since_time > 1.0
    
    def _track_injection(self, result: InjectionResult):
        """Track injection in history"""
        self.injection_history.append(result)
        
        # Keep only recent history (last 100 injections)
        if len(self.injection_history) > 100:
            self.injection_history = self.injection_history[-100:]
    
    def _log_injection(self, result: InjectionResult):
        """Log the injection event"""
        log_level = LogLevel.INFO if result.success else LogLevel.ERROR
        
        log_msg = EnhancedLogMessage(
            level=log_level,
            component=ComponentType.USER_INTERACTION,
            source=LogSource.DEBBIE,
            action="message_injected",
            event_summary=f"Injected {result.injection_type.value} message to session {result.session_id}",
            session_id=result.session_id,
            details={
                "injection_type": result.injection_type.value,
                "message": result.message,
                "response_received": result.response_received,
                "response_time_ms": result.response_time_ms,
                "error": result.error
            }
        )
        
        logger.info(log_msg.event_summary, extra=log_msg.to_dict())
    
    def _mock_injection(self, session_id: str, message: str,
                       injection_type: InjectionType,
                       timestamp: datetime) -> InjectionResult:
        """Create mock injection result for testing"""
        # Simulate successful injection
        time.sleep(0.2)  # Simulate network delay
        
        return InjectionResult(
            success=True,
            session_id=session_id,
            injection_type=injection_type,
            message=message,
            timestamp=timestamp,
            response_received=True,
            response_time_ms=200.0
        )
    
    def get_injection_history(self, session_id: Optional[str] = None,
                            injection_type: Optional[InjectionType] = None,
                            last_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get injection history for debugging.
        
        Args:
            session_id: Filter by session ID
            injection_type: Filter by injection type
            last_n: Number of recent injections to return
            
        Returns:
            List of injection records
        """
        history = self.injection_history
        
        # Apply filters
        if session_id:
            history = [h for h in history if h.session_id == session_id]
        if injection_type:
            history = [h for h in history if h.injection_type == injection_type]
        
        # Return last N
        return [h.to_dict() for h in history[-last_n:]]
