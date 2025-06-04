"""
Channel integration for AIWhisperer sessions.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .types import ChannelType, ChannelMessage
from .router import ChannelRouter
from .storage import ChannelStorage

logger = logging.getLogger(__name__)


class ChannelIntegration:
    """Integrates channel system with AIWhisperer sessions."""
    
    def __init__(self):
        """Initialize channel integration."""
        self._storage = ChannelStorage()
        self._routers: Dict[str, ChannelRouter] = {}
        self._visibility_preferences: Dict[str, Dict[str, bool]] = {}
        
        # Default visibility settings
        self._default_visibility = {
            "show_commentary": True,
            "show_analysis": False
        }
    
    def get_router(self, session_id: str, agent_id: Optional[str] = None) -> ChannelRouter:
        """Get or create a router for a session (session-wide, not per-agent)."""
        # Use session-wide router instead of per-agent to get consistent sequence numbers
        key = session_id  # Remove agent_id from key to share router across agents
        
        if key not in self._routers:
            self._routers[key] = ChannelRouter(
                session_id=session_id,
                agent_id=None  # Session-wide router
            )
            logger.debug(f"Created new session-wide router for {key}")
        else:
            logger.debug(f"Reusing session-wide router for {key}, current sequence: {self._routers[key]._sequence_counter}")
        
        # Update agent_id for this specific call (for metadata)
        router = self._routers[key]
        router.agent_id = agent_id  # Set current agent for this message
        
        return router
    
    def process_ai_response(
        self, 
        session_id: str, 
        content: str,
        agent_id: Optional[str] = None,
        is_partial: bool = False,
        is_structured: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process an AI response and return channel messages.
        
        Returns:
            List of channel message dictionaries ready for WebSocket
        """
        router = self.get_router(session_id, agent_id)
        messages = router.route_response(content, is_partial, is_structured)
        
        # Store messages
        for message in messages:
            self._storage.add_message(session_id, message)
        
        # Convert to WebSocket format
        websocket_messages = []
        visibility = self.get_visibility_preferences(session_id)
        
        for message in messages:
            # Apply visibility rules
            if message.channel == ChannelType.ANALYSIS and not visibility["show_analysis"]:
                logger.debug(f"Hiding analysis message for session {session_id}")
                continue
            elif message.channel == ChannelType.COMMENTARY and not visibility["show_commentary"]:
                logger.debug(f"Hiding commentary message for session {session_id}")
                continue
            
            websocket_messages.append(self._to_websocket_format(message))
        
        return websocket_messages
    
    def reset_streaming(self, session_id: str, agent_id: Optional[str] = None):
        """Reset streaming for a new conversation."""
        router = self.get_router(session_id, agent_id)
        router.reset_streaming()
    
    def _to_websocket_format(self, message: ChannelMessage) -> Dict[str, Any]:
        """Convert ChannelMessage to WebSocket notification format."""
        return {
            "type": "channel_message",
            "channel": message.channel.value,
            "content": message.content,
            "metadata": {
                "sequence": message.metadata.sequence,
                "timestamp": message.metadata.timestamp.isoformat(),
                "agentId": message.metadata.agent_id,
                "sessionId": message.metadata.session_id,
                "toolCalls": message.metadata.tool_calls,
                "continuationDepth": message.metadata.continuation_depth,
                "isPartial": message.metadata.is_partial,
                **message.metadata.custom
            }
        }
    
    def get_channel_history(
        self,
        session_id: str,
        channels: Optional[List[str]] = None,
        limit: Optional[int] = None,
        since_sequence: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get channel message history."""
        # Convert string channels to ChannelType
        channel_types = None
        if channels:
            channel_types = []
            for ch in channels:
                channel_type = ChannelType.from_string(ch)
                if channel_type:
                    channel_types.append(channel_type)
        
        # Get messages from storage
        messages = []
        if channel_types:
            for channel_type in channel_types:
                channel_messages = self._storage.get_messages(
                    session_id, 
                    channel_type,
                    limit=limit,
                    since_sequence=since_sequence
                )
                messages.extend(channel_messages)
        else:
            messages = self._storage.get_messages(
                session_id,
                limit=limit,
                since_sequence=since_sequence
            )
        
        # Sort by sequence
        messages.sort(key=lambda m: m.metadata.sequence)
        
        # Apply limit after combining all channels
        if limit:
            messages = messages[-limit:]
        
        # Convert to WebSocket format
        return {
            "messages": [self._to_websocket_format(m) for m in messages],
            "totalCount": len(messages)
        }
    
    def set_visibility_preferences(
        self, 
        session_id: str, 
        show_commentary: bool,
        show_analysis: bool = False
    ) -> None:
        """Set channel visibility preferences for a session."""
        self._visibility_preferences[session_id] = {
            "show_commentary": show_commentary,
            "show_analysis": show_analysis
        }
        logger.info(
            f"Updated visibility for {session_id}: "
            f"commentary={show_commentary}, analysis={show_analysis}"
        )
    
    def get_visibility_preferences(self, session_id: str) -> Dict[str, bool]:
        """Get channel visibility preferences for a session."""
        return self._visibility_preferences.get(
            session_id, 
            self._default_visibility.copy()
        )
    
    def clear_session(self, session_id: str) -> None:
        """Clear all data for a session."""
        # Clear storage
        self._storage.clear_session(session_id)
        
        # Clear routers
        keys_to_remove = [k for k in self._routers if k.startswith(f"{session_id}:")]
        for key in keys_to_remove:
            del self._routers[key]
        
        # Clear preferences
        self._visibility_preferences.pop(session_id, None)
        
        logger.info(f"Cleared all channel data for session {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a session."""
        stats = self._storage.get_session_stats(session_id)
        stats["visibility"] = self.get_visibility_preferences(session_id)
        return stats
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions."""
        cleaned = self._storage.cleanup_old_sessions(max_age_hours)
        
        # Also clean up routers and preferences for cleaned sessions
        active_sessions = self._storage.get_active_sessions()
        
        # Clean routers
        router_keys_to_remove = []
        for key in self._routers:
            session_id = key.split(":")[0]
            if session_id not in active_sessions:
                router_keys_to_remove.append(key)
        
        for key in router_keys_to_remove:
            del self._routers[key]
        
        # Clean preferences
        pref_keys_to_remove = []
        for session_id in self._visibility_preferences:
            if session_id not in active_sessions:
                pref_keys_to_remove.append(session_id)
        
        for session_id in pref_keys_to_remove:
            del self._visibility_preferences[session_id]
        
        logger.info(f"Cleaned up {cleaned} sessions and related data")
        return cleaned


# Global instance for easy access
_channel_integration: Optional[ChannelIntegration] = None


def get_channel_integration() -> ChannelIntegration:
    """Get the global channel integration instance."""
    global _channel_integration
    if _channel_integration is None:
        _channel_integration = ChannelIntegration()
    return _channel_integration