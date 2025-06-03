"""
Channel Storage for managing channel message history.
"""

import logging
from typing import Dict, List, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from .types import ChannelType, ChannelMessage

logger = logging.getLogger(__name__)


class ChannelStorage:
    """Stores and manages channel messages for sessions."""
    
    def __init__(self, max_messages_per_channel: int = 1000):
        """
        Initialize channel storage.
        
        Args:
            max_messages_per_channel: Maximum messages to keep per channel
        """
        self.max_messages = max_messages_per_channel
        
        # Storage structure: {session_id: {channel_type: [messages]}}
        self._storage: Dict[str, Dict[ChannelType, List[ChannelMessage]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # Track active sessions
        self._active_sessions: Set[str] = set()
        
        # Session metadata
        self._session_metadata: Dict[str, Dict] = {}
    
    def add_message(self, session_id: str, message: ChannelMessage) -> None:
        """Add a message to channel storage."""
        channel_messages = self._storage[session_id][message.channel]
        channel_messages.append(message)
        
        # Enforce size limit
        if len(channel_messages) > self.max_messages:
            # Remove oldest messages
            channel_messages[:] = channel_messages[-self.max_messages:]
        
        self._active_sessions.add(session_id)
        logger.debug(f"Added {message.channel.value} message to session {session_id}")
    
    def get_messages(
        self, 
        session_id: str, 
        channel: Optional[ChannelType] = None,
        limit: Optional[int] = None,
        since_sequence: Optional[int] = None
    ) -> List[ChannelMessage]:
        """
        Get messages from storage.
        
        Args:
            session_id: Session to get messages for
            channel: Specific channel to filter by (None for all)
            limit: Maximum number of messages to return
            since_sequence: Only return messages after this sequence number
            
        Returns:
            List of channel messages
        """
        if session_id not in self._storage:
            return []
        
        messages = []
        
        if channel:
            # Get messages from specific channel
            channel_messages = self._storage[session_id].get(channel, [])
            messages.extend(channel_messages)
        else:
            # Get messages from all channels
            for channel_type in ChannelType:
                channel_messages = self._storage[session_id].get(channel_type, [])
                messages.extend(channel_messages)
        
        # Filter by sequence number if specified
        if since_sequence is not None:
            messages = [m for m in messages if m.metadata.sequence > since_sequence]
        
        # Sort by sequence
        messages.sort(key=lambda m: m.metadata.sequence)
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_channel_messages(
        self, 
        session_id: str, 
        channel: ChannelType,
        limit: Optional[int] = None
    ) -> List[ChannelMessage]:
        """Get messages from a specific channel."""
        return self.get_messages(session_id, channel, limit)
    
    def get_user_visible_messages(
        self, 
        session_id: str,
        include_commentary: bool = True,
        limit: Optional[int] = None
    ) -> List[ChannelMessage]:
        """Get messages that should be visible to users."""
        messages = []
        
        # Always include final channel
        messages.extend(self.get_channel_messages(session_id, ChannelType.FINAL))
        
        # Optionally include commentary
        if include_commentary:
            messages.extend(self.get_channel_messages(session_id, ChannelType.COMMENTARY))
        
        # Sort by sequence
        messages.sort(key=lambda m: m.metadata.sequence)
        
        # Apply limit
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def clear_session(self, session_id: str) -> None:
        """Clear all messages for a session."""
        if session_id in self._storage:
            del self._storage[session_id]
        self._active_sessions.discard(session_id)
        if session_id in self._session_metadata:
            del self._session_metadata[session_id]
        logger.info(f"Cleared storage for session {session_id}")
    
    def clear_channel(self, session_id: str, channel: ChannelType) -> None:
        """Clear messages for a specific channel in a session."""
        if session_id in self._storage and channel in self._storage[session_id]:
            self._storage[session_id][channel].clear()
            logger.info(f"Cleared {channel.value} channel for session {session_id}")
    
    def get_session_stats(self, session_id: str) -> Dict[str, int]:
        """Get statistics for a session."""
        if session_id not in self._storage:
            return {}
        
        stats = {}
        for channel in ChannelType:
            messages = self._storage[session_id].get(channel, [])
            stats[f"{channel.value}_count"] = len(messages)
        
        return stats
    
    def get_active_sessions(self) -> Set[str]:
        """Get set of active session IDs."""
        return self._active_sessions.copy()
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up sessions older than specified hours.
        
        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        sessions_to_clean = []
        
        for session_id in self._active_sessions:
            # Get latest message time
            latest_time = None
            for channel in ChannelType:
                messages = self._storage[session_id].get(channel, [])
                if messages:
                    channel_latest = messages[-1].metadata.timestamp
                    if latest_time is None or channel_latest > latest_time:
                        latest_time = channel_latest
            
            # Clean up if session is old
            if latest_time and latest_time < cutoff_time:
                sessions_to_clean.append(session_id)
        
        # Clean up identified sessions
        for session_id in sessions_to_clean:
            self.clear_session(session_id)
        
        logger.info(f"Cleaned up {len(sessions_to_clean)} old sessions")
        return len(sessions_to_clean)
    
    def set_session_metadata(self, session_id: str, metadata: Dict) -> None:
        """Set metadata for a session."""
        self._session_metadata[session_id] = metadata
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """Get metadata for a session."""
        return self._session_metadata.get(session_id)