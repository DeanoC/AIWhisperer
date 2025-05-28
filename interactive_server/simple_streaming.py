"""
Simple streaming implementation that directly sends WebSocket notifications.
This bypasses the delegate system entirely.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import WebSocket

from .message_models import AIMessageChunkNotification

logger = logging.getLogger(__name__)


class SimpleStreamingWrapper:
    """Wraps session.send_user_message to add streaming notifications."""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.websocket_map: Dict[str, WebSocket] = {}
    
    def register_websocket(self, session_id: str, websocket: WebSocket):
        """Register a websocket for a session."""
        self.websocket_map[session_id] = websocket
        logger.info(f"[SimpleStreaming] Registered websocket for session {session_id}")
    
    def unregister_websocket(self, session_id: str):
        """Unregister a websocket for a session."""
        if session_id in self.websocket_map:
            del self.websocket_map[session_id]
            logger.info(f"[SimpleStreaming] Unregistered websocket for session {session_id}")
    
    async def send_notification(self, session_id: str, notification: dict):
        """Send a notification to the websocket for a session."""
        websocket = self.websocket_map.get(session_id)
        if websocket:
            try:
                await websocket.send_json(notification)
                logger.debug(f"[SimpleStreaming] Sent notification to session {session_id}")
            except Exception as e:
                logger.error(f"[SimpleStreaming] Error sending notification: {e}")
        else:
            logger.warning(f"[SimpleStreaming] No websocket found for session {session_id}")
    
    async def wrap_send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Wrap the session's send_user_message to capture and stream the response.
        """
        logger.info(f"[SimpleStreaming] Wrapping send_message for session {session_id}")
        
        session = self.session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Check if we have the original send_user_message method
        if not hasattr(session, 'send_user_message'):
            logger.error(f"[SimpleStreaming] Session {session_id} has no send_user_message method")
            raise RuntimeError("Session has no send_user_message method")
        
        # Store the original AI loop's context messages before sending
        agent = session.agents.get(session.active_agent) if session.active_agent else None
        if not agent:
            logger.error(f"[SimpleStreaming] No active agent in session {session_id}")
            raise RuntimeError("No active agent")
        
        initial_message_count = len(agent.context.retrieve_messages())
        
        # Send the message
        result = await session.send_user_message(message)
        
        # After sending, check if there's a new assistant message
        messages = agent.context.retrieve_messages()
        if len(messages) > initial_message_count:
            # Find the new assistant message(s)
            new_messages = messages[initial_message_count:]
            for msg in new_messages:
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    if content:
                        # Send the content as chunks
                        logger.info(f"[SimpleStreaming] Found assistant response: {len(content)} chars")
                        
                        # Send as a single chunk for now
                        chunk_notification = AIMessageChunkNotification(
                            sessionId=session_id,
                            chunk=content,
                            isFinal=False
                        )
                        
                        await self.send_notification(session_id, {
                            "jsonrpc": "2.0",
                            "method": "AIMessageChunkNotification",
                            "params": chunk_notification.model_dump()
                        })
                        
                        # Send final chunk
                        final_notification = AIMessageChunkNotification(
                            sessionId=session_id,
                            chunk="",
                            isFinal=True
                        )
                        
                        await self.send_notification(session_id, {
                            "jsonrpc": "2.0",
                            "method": "AIMessageChunkNotification",
                            "params": final_notification.model_dump()
                        })
        
        return result


def install_simple_streaming(session_manager):
    """Install the simple streaming wrapper on the session manager."""
    logger.info("[SimpleStreaming] Installing simple streaming wrapper")
    logger.info(f"[SimpleStreaming] Session manager type: {type(session_manager)}")
    logger.info(f"[SimpleStreaming] Has send_message: {hasattr(session_manager, 'send_message')}")
    
    # Create wrapper instance
    wrapper = SimpleStreamingWrapper(session_manager)
    
    # Store wrapper on session manager
    session_manager._streaming_wrapper = wrapper
    
    # Override create_session to register websockets
    original_create_session = session_manager.create_session
    
    async def create_session_with_ws_tracking(websocket: Optional[WebSocket] = None) -> str:
        session_id = await original_create_session(websocket)
        if websocket:
            wrapper.register_websocket(session_id, websocket)
        return session_id
    
    session_manager.create_session = create_session_with_ws_tracking
    
    # Override send_message to use wrapper
    original_send_message = session_manager.send_message
    
    async def send_message_with_streaming(session_id: str, message: str) -> Dict[str, Any]:
        return await wrapper.wrap_send_message(session_id, message)
    
    session_manager.send_message = send_message_with_streaming
    
    # Override cleanup_session to unregister websockets
    original_cleanup_session = session_manager.cleanup_session
    
    async def cleanup_session_with_ws_cleanup(session_id: str) -> None:
        wrapper.unregister_websocket(session_id)
        await original_cleanup_session(session_id)
    
    session_manager.cleanup_session = cleanup_session_with_ws_cleanup
    
    logger.info("[SimpleStreaming] Simple streaming wrapper installed")