"""
Delegate bridge for converting AILoop delegate events to WebSocket notifications.

This module provides the DelegateBridge class which:
- Maps AILoop delegate events to WebSocket notification messages
- Routes notifications to the appropriate WebSocket connections
- Handles async notification sending with error recovery
- Provides proper event-to-message conversion
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .message_models import (
    AIMessageChunkNotification,
    SessionStatusNotification,
    ToolCallNotification,
    SessionStatus
)

logger = logging.getLogger(__name__)


class DelegateBridge:
    """
    Bridges AILoop delegate events to WebSocket notifications.
    
    This class registers as a delegate listener for AILoop events and converts
    them to appropriate WebSocket JSON-RPC notifications.
    """
    
    def __init__(self, session):
        """
        Initialize the delegate bridge for a session.
        
        Args:
            session: InteractiveSession instance to send notifications to
        """
        self.session = session
        self.is_active = True
        
        # Register event handlers with the session's delegate manager
        self._register_event_handlers()
    
    def _register_event_handlers(self) -> None:
        """
        Register all AILoop event handlers with the delegate manager.
        """
        try:
            delegate_manager = self.session.delegate_manager
            
            # Session lifecycle events
            delegate_manager.register_notification("ai_loop.session_started", self._handle_session_started)
            delegate_manager.register_notification("ai_loop.session_ended", self._handle_session_ended)
            
            # Message events
            delegate_manager.register_notification("ai_loop.message.user_processed", self._handle_user_message_processed)
            delegate_manager.register_notification("ai_loop.message.ai_chunk_received", self._handle_ai_chunk_received)
            
            # Tool call events
            delegate_manager.register_notification("ai_loop.tool_call.identified", self._handle_tool_call_identified)
            delegate_manager.register_notification("ai_loop.tool_call.result_processed", self._handle_tool_result_processed)
            
            # Status events
            delegate_manager.register_notification("ai_loop.status.paused", self._handle_session_paused)
            delegate_manager.register_notification("ai_loop.status.resumed", self._handle_session_resumed)
            
            # Error events
            delegate_manager.register_notification("ai_loop.error", self._handle_error)
            
            logger.debug(f"Registered delegate event handlers for session {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to register delegate event handlers: {e}")
            raise
    
    async def _handle_session_started(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.session_started event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Event data (typically None for session_started)
        """
        if not self.is_active:
            return
            
        try:
            notification = SessionStatusNotification(
                sessionId=self.session.session_id,
                status=SessionStatus.Active,
                reason="Session started"
            )
            
            await self.session.send_notification("SessionStatusNotification", notification)
            logger.debug(f"Sent session started notification for {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling session_started event: {e}")
    
    async def _handle_session_ended(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.session_ended event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Reason for session ending (string)
        """
        if not self.is_active:
            return
            
        try:
            # Map finish reasons to session status
            reason = str(event_data) if event_data else "unknown"
            
            if reason in ["stopped", "cancelled"]:
                status = SessionStatus.Stopped
            elif reason == "error":
                status = SessionStatus.Error
            else:
                status = SessionStatus.Stopped  # Default to stopped
            
            notification = SessionStatusNotification(
                sessionId=self.session.session_id,
                status=status,
                reason=f"Session ended: {reason}"
            )
            
            await self.session.send_notification("SessionStatusNotification", notification)
            logger.debug(f"Sent session ended notification for {self.session.session_id}: {reason}")
            
        except Exception as e:
            logger.error(f"Error handling session_ended event: {e}")
    
    async def _handle_user_message_processed(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.message.user_processed event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: The user message that was processed (string)
        """
        if not self.is_active:
            return
            
        # This event is primarily for internal tracking
        # No specific WebSocket notification is typically sent for user message processing
        logger.debug(f"User message processed in session {self.session.session_id}: {event_data}")
    
    async def _handle_ai_chunk_received(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.message.ai_chunk_received event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: The AI chunk content (string)
        """
        if not self.is_active:
            return

        try:
            # Support for final chunk notification (is_final_chunk kwarg)
            is_final = kwargs.get("is_final_chunk", False)
            chunk_content = str(event_data) if event_data else ""
            notification = AIMessageChunkNotification(
                sessionId=self.session.session_id,
                chunk=chunk_content,
                isFinal=is_final
            )
            await self.session.send_notification("AIMessageChunkNotification", notification)
            logger.debug(f"Sent AI chunk notification for {self.session.session_id}: {len(chunk_content)} chars, isFinal={is_final}, content='{chunk_content}'")
        except Exception as e:
            logger.error(f"Error handling ai_chunk_received event: {e}")
    
    async def _handle_tool_call_identified(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.tool_call.identified event.
        Args:
            sender: The AILoop instance that sent the event
            event_data: List of tool call dicts or tool names
        """
        if not self.is_active:
            return
        try:
            # Support both legacy (list of names) and new (list of tool call dicts) formats
            tool_calls = event_data if isinstance(event_data, list) else [event_data]
            for i, call in enumerate(tool_calls):
                if isinstance(call, dict) and "id" in call and "function" in call:
                    # New format: tool call dict from AI chunk
                    tool_call_id = call.get("id", f"tool-{self.session.session_id}-{i}")
                    tool_name = call["function"].get("name", str(call.get("type", "tool")))
                    # Arguments may be a JSON string or dict
                    arguments = call["function"].get("arguments", {})
                    import json
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except Exception:
                            pass
                else:
                    # Legacy: just a tool name
                    tool_call_id = f"tool-{self.session.session_id}-{i}"
                    tool_name = str(call)
                    arguments = {}
                notification = ToolCallNotification(
                    sessionId=self.session.session_id,
                    toolCallId=tool_call_id,
                    toolName=tool_name,
                    arguments=arguments
                )
                await self.session.send_notification("ToolCallNotification", notification)
            logger.debug(f"Sent tool call notifications for {self.session.session_id}: {tool_calls}")
        except Exception as e:
            logger.error(f"Error handling tool_call_identified event: {e}")
    
    async def _handle_tool_result_processed(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.tool_call.result_processed event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Tool result message (dict)
        """
        if not self.is_active:
            return
            
        # Tool result processing is typically internal
        # The result will be reflected in subsequent AI responses
        logger.debug(f"Tool result processed in session {self.session.session_id}: {event_data}")
    
    async def _handle_session_paused(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.status.paused event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Event data (typically None)
        """
        if not self.is_active:
            return
            
        try:
            notification = SessionStatusNotification(
                sessionId=self.session.session_id,
                status=SessionStatus.Paused,
                reason="Session paused"
            )
            
            await self.session.send_notification("SessionStatusNotification", notification)
            logger.debug(f"Sent session paused notification for {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling session_paused event: {e}")
    
    async def _handle_session_resumed(self, sender, event_data: Any, **kwargs) -> None:
        """
        Handle ai_loop.status.resumed event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Event data (typically None)
        """
        if not self.is_active:
            return
            
        try:
            notification = SessionStatusNotification(
                sessionId=self.session.session_id,
                status=SessionStatus.Active,
                reason="Session resumed"
            )
            
            await self.session.send_notification("SessionStatusNotification", notification)
            logger.debug(f"Sent session resumed notification for {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error handling session_resumed event: {e}")
    
    async def _handle_error(self, sender, event_data: Any, **kwargs) -> None:
        import logging
        logging.debug(f"[DelegateBridge._handle_error] Called with event_data: {event_data}")
        """
        Handle ai_loop.error event.
        
        Args:
            sender: The AILoop instance that sent the event
            event_data: Exception or error details
        """
        if not self.is_active:
            logging.debug("[DelegateBridge._handle_error] Not active, returning early.")
            return
            
        try:
            error_message = str(event_data) if event_data else "Unknown error"
            logging.debug(f"[DelegateBridge._handle_error] Preparing SessionStatusNotification: {error_message}")
            # Special handling for AI service timeout
            if error_message.strip().lower() in ["ai service timeout", "timeout"] or "timeout" in error_message.lower():
                notification = SessionStatusNotification(
                    sessionId=self.session.session_id,
                    status=SessionStatus.Error,
                    reason="timeout"
                )
            else:
                notification = SessionStatusNotification(
                    sessionId=self.session.session_id,
                    status=SessionStatus.Error,
                    reason=f"Error: {error_message}"
                )
            await self.session.send_notification("SessionStatusNotification", notification)
            logging.debug(f"[DelegateBridge._handle_error] Sent error notification for {self.session.session_id}: {error_message}")
            # Give the event loop a chance to flush the notification before shutdown/cleanup
            await asyncio.sleep(1.0)
        except Exception as e:
            logging.error(f"[DelegateBridge._handle_error] Error handling error event: {e}")
    
    async def cleanup(self) -> None:
        """
        Clean up the delegate bridge and unregister event handlers.
        """
        try:
            self.is_active = False
            
            # Unregister event handlers
            delegate_manager = self.session.delegate_manager
            
            # Session lifecycle events
            delegate_manager.unregister_notification("ai_loop.session_started", self._handle_session_started)
            delegate_manager.unregister_notification("ai_loop.session_ended", self._handle_session_ended)
            
            # Message events
            delegate_manager.unregister_notification("ai_loop.message.user_processed", self._handle_user_message_processed)
            delegate_manager.unregister_notification("ai_loop.message.ai_chunk_received", self._handle_ai_chunk_received)
            
            # Tool call events
            delegate_manager.unregister_notification("ai_loop.tool_call.identified", self._handle_tool_call_identified)
            delegate_manager.unregister_notification("ai_loop.tool_call.result_processed", self._handle_tool_result_processed)
            
            # Status events
            delegate_manager.unregister_notification("ai_loop.status.paused", self._handle_session_paused)
            delegate_manager.unregister_notification("ai_loop.status.resumed", self._handle_session_resumed)
            
            # Error events
            delegate_manager.unregister_notification("ai_loop.error", self._handle_error)
            
            logger.debug(f"Cleaned up delegate bridge for session {self.session.session_id}")
            
        except Exception as e:
            logger.error(f"Error during delegate bridge cleanup: {e}")
