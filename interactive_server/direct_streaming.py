"""
Direct streaming implementation that hooks into agent processing.
This completely bypasses the deprecated delegate system.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from fastapi import WebSocket

from .message_models import AIMessageChunkNotification

logger = logging.getLogger(__name__)


class DirectStreamingSession:
    """Enhanced session that streams AI responses directly."""
    
    def __init__(self, original_session, websocket: Optional[WebSocket] = None):
        self.original_session = original_session
        self.websocket = websocket
        self.session_id = original_session.session_id
        
        # Copy all attributes from original session
        for attr in dir(original_session):
            if not attr.startswith('_') and not hasattr(self, attr):
                setattr(self, attr, getattr(original_session, attr))
    
    async def send_user_message(self, message: str) -> Dict[str, Any]:
        """
        Override send_user_message to add streaming support.
        """
        logger.info(f"[DirectStreaming] Processing message for session {self.session_id}")
        
        if not self.websocket:
            logger.warning(f"[DirectStreaming] No websocket for session {self.session_id}")
            # Fall back to original method
            return await self.original_session.send_user_message(message)
        
        # Create chunk sender
        async def send_chunk(chunk: str):
            try:
                notification = AIMessageChunkNotification(
                    sessionId=self.session_id,
                    chunk=chunk,
                    isFinal=False
                )
                await self.websocket.send_json({
                    "jsonrpc": "2.0",
                    "method": "AIMessageChunkNotification",
                    "params": notification.model_dump()
                })
                logger.debug(f"[DirectStreaming] Sent chunk: {len(chunk)} chars")
            except Exception as e:
                logger.error(f"[DirectStreaming] Error sending chunk: {e}")
        
        # Get the active agent
        if not self.original_session.active_agent:
            raise RuntimeError("No active agent")
        
        agent = self.original_session.agents[self.original_session.active_agent]
        
        # Check if agent supports streaming (StatelessAgent)
        if hasattr(agent, 'process_message') and 'on_stream_chunk' in agent.process_message.__code__.co_varnames:
            logger.info(f"[DirectStreaming] Using streaming-capable agent")
            try:
                # Process with streaming
                result = await agent.process_message(message, on_stream_chunk=send_chunk)
                
                # Send final chunk
                final_notification = AIMessageChunkNotification(
                    sessionId=self.session_id,
                    chunk="",
                    isFinal=True
                )
                await self.websocket.send_json({
                    "jsonrpc": "2.0",
                    "method": "AIMessageChunkNotification",
                    "params": final_notification.model_dump()
                })
                
                return result
            except Exception as e:
                logger.error(f"[DirectStreaming] Error in streaming: {e}", exc_info=True)
                # Fall back to non-streaming
        
        # Fallback: Use original method and send response as single chunk
        logger.info(f"[DirectStreaming] Using non-streaming fallback")
        
        # Store message count before
        agent_context = agent.context if hasattr(agent, 'context') else None
        initial_count = 0
        if agent_context:
            initial_count = len(agent_context.retrieve_messages())
            logger.info(f"[DirectStreaming] Initial message count: {initial_count}")
        
        # Process message
        result = await self.original_session.send_user_message(message)
        logger.info(f"[DirectStreaming] Message processed, result type: {type(result)}")
        
        # Check for new assistant message
        if agent_context:
            messages = agent_context.retrieve_messages()
            logger.info(f"[DirectStreaming] New message count: {len(messages)}")
            if len(messages) > initial_count:
                logger.info(f"[DirectStreaming] Found {len(messages) - initial_count} new messages")
                for msg in messages[initial_count:]:
                    logger.info(f"[DirectStreaming] New message role: {msg.get('role')}, content length: {len(msg.get('content', ''))}")
                    if msg.get('role') == 'assistant':
                        content = msg.get('content', '')
                        if content:
                            logger.info(f"[DirectStreaming] Sending assistant message as chunk: {len(content)} chars")
                            # Send as chunks
                            await send_chunk(content)
                            
                            # Send final
                            final_notification = AIMessageChunkNotification(
                                sessionId=self.session_id,
                                chunk="",
                                isFinal=True
                            )
                            await self.websocket.send_json({
                                "jsonrpc": "2.0",
                                "method": "AIMessageChunkNotification",
                                "params": final_notification.model_dump()
                            })
                            logger.info(f"[DirectStreaming] Sent final chunk notification")
            else:
                logger.warning(f"[DirectStreaming] No new messages found after processing")
        else:
            logger.warning(f"[DirectStreaming] No agent context available")
        
        return result


def install_direct_streaming(session_manager):
    """Install direct streaming by wrapping sessions."""
    logger.info("[DirectStreaming] Installing direct streaming")
    
    # Track websockets
    session_manager._websockets = {}
    
    # Wrap get_session to return streaming-enhanced sessions
    original_get_session = session_manager.get_session
    
    def get_streaming_session(session_id: str):
        session = original_get_session(session_id)
        logger.info(f"[DirectStreaming] get_session called for {session_id}, found: {session is not None}, has websocket: {session_id in session_manager._websockets}")
        if session and session_id in session_manager._websockets:
            # Return wrapped session with streaming
            wrapped = DirectStreamingSession(session, session_manager._websockets[session_id])
            logger.info(f"[DirectStreaming] Returning wrapped session for {session_id}")
            return wrapped
        return session
    
    session_manager.get_session = get_streaming_session
    
    # Also wrap get_session_by_websocket
    if hasattr(session_manager, 'get_session_by_websocket'):
        original_get_by_ws = session_manager.get_session_by_websocket
        
        def get_session_by_websocket_wrapped(websocket):
            session_id = None
            # Find session_id for this websocket
            for sid, ws in session_manager._websockets.items():
                if ws == websocket:
                    session_id = sid
                    break
            
            if session_id:
                return get_streaming_session(session_id)
            
            # Fallback to original
            return original_get_by_ws(websocket)
        
        session_manager.get_session_by_websocket = get_session_by_websocket_wrapped
    
    # Wrap create_session to track websockets
    original_create_session = session_manager.create_session
    
    async def create_session_with_tracking(websocket: Optional[WebSocket] = None) -> str:
        session_id = await original_create_session(websocket)
        if websocket:
            session_manager._websockets[session_id] = websocket
            logger.info(f"[DirectStreaming] Tracking websocket for session {session_id}")
        return session_id
    
    session_manager.create_session = create_session_with_tracking
    
    # Wrap cleanup to remove websocket tracking
    original_cleanup = session_manager.cleanup_session
    
    async def cleanup_with_tracking(session_id: str):
        if session_id in session_manager._websockets:
            del session_manager._websockets[session_id]
            logger.info(f"[DirectStreaming] Removed websocket for session {session_id}")
        await original_cleanup(session_id)
    
    session_manager.cleanup_session = cleanup_with_tracking
    
    logger.info("[DirectStreaming] Direct streaming installed")