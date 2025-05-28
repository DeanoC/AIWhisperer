"""
Temporary patch to add streaming support to InteractiveSession.
This adds WebSocket notifications for AI responses without requiring
a full refactor to StreamingSession.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from fastapi import WebSocket

from .message_models import AIMessageChunkNotification

logger = logging.getLogger(__name__)


async def send_user_message_with_streaming(
    session,
    message: str,
    websocket: Optional[WebSocket] = None
) -> Dict[str, Any]:
    """
    Enhanced send_user_message that streams AI responses to WebSocket.
    
    Args:
        session: The InteractiveSession instance
        message: User message to send
        websocket: Optional WebSocket connection for streaming
        
    Returns:
        Result dictionary
    """
    if not session.is_started or not session.active_agent:
        raise RuntimeError(f"Session {session.session_id} is not started or no active agent")
    
    try:
        agent = session.agents[session.active_agent]
        
        # If we have a websocket, wrap the agent's process_message to capture chunks
        if websocket and hasattr(agent, 'ai_loop') and agent.ai_loop:
            # Store original context manager
            original_context_manager = agent.ai_loop.context_manager
            
            # Temporarily add a hook to capture AI chunks
            chunks_received = []
            
            async def send_chunk_notification(chunk_content: str, is_final: bool = False):
                """Send AI chunk notification via WebSocket."""
                try:
                    notification = AIMessageChunkNotification(
                        sessionId=session.session_id,
                        chunk=chunk_content,
                        isFinal=is_final
                    )
                    
                    await websocket.send_json({
                        "jsonrpc": "2.0",
                        "method": "AIMessageChunkNotification",
                        "params": notification.model_dump()
                    })
                    
                    logger.debug(f"Sent AI chunk: {len(chunk_content)} chars, final={is_final}")
                except Exception as e:
                    logger.error(f"Error sending chunk notification: {e}")
            
            # Hook into the AI loop's delegate manager if available
            if hasattr(agent.ai_loop, 'delegate_manager') and agent.ai_loop.delegate_manager:
                # Register a temporary notification handler
                async def chunk_handler(sender, event_data, **kwargs):
                    is_final = kwargs.get('is_final_chunk', False)
                    chunk_content = str(event_data) if event_data else ""
                    chunks_received.append(chunk_content)
                    await send_chunk_notification(chunk_content, is_final)
                
                # Register the handler
                agent.ai_loop.delegate_manager.register_notification(
                    "ai_loop.message.ai_chunk_received", 
                    chunk_handler
                )
                
                try:
                    # Process the message
                    result = await agent.process_message(message)
                    
                    # If no chunks were received but we have a result, send it as a single chunk
                    if not chunks_received and isinstance(result, str):
                        await send_chunk_notification(result, is_final=False)
                        await send_chunk_notification("", is_final=True)
                    
                    return result
                    
                finally:
                    # Unregister the handler
                    agent.ai_loop.delegate_manager.unregister_notification(
                        "ai_loop.message.ai_chunk_received",
                        chunk_handler
                    )
            else:
                # No delegate manager, fall back to sending complete response
                result = await agent.process_message(message)
                if isinstance(result, str):
                    await send_chunk_notification(result, is_final=False)
                    await send_chunk_notification("", is_final=True)
                return result
        else:
            # No websocket, just process normally
            return await agent.process_message(message)
            
    except Exception as e:
        logger.error(f"Failed to send message to agent '{session.active_agent}' in session {session.session_id}: {e}")
        raise


def patch_session_manager(session_manager):
    """
    Monkey-patch the session manager to add streaming support.
    
    Args:
        session_manager: The InteractiveSessionManager instance
    """
    # Store websocket references
    session_manager._websockets = {}
    
    # Patch create_session to store websocket reference
    original_create_session = session_manager.create_session
    
    async def create_session_with_ws(websocket: Optional[WebSocket] = None) -> str:
        session_id = await original_create_session(websocket)
        if websocket:
            session_manager._websockets[session_id] = websocket
        return session_id
    
    session_manager.create_session = create_session_with_ws
    
    # Patch send_message to use streaming
    original_send_message = session_manager.send_message
    
    async def send_message_with_streaming(session_id: str, message: str) -> Dict[str, Any]:
        session = session_manager.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get websocket for this session
        websocket = session_manager._websockets.get(session_id)
        
        # Use our enhanced streaming version
        return await send_user_message_with_streaming(session, message, websocket)
    
    session_manager.send_message = send_message_with_streaming
    
    logger.info("Applied streaming patch to InteractiveSessionManager")