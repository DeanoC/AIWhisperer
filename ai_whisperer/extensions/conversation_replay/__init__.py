"""
ai_whisperer.extensions.conversation_replay - Conversation replay mode extension

This extension provides conversation replay capabilities:
- Text-based conversation automation  
- WebSocket-based server communication
- Line-by-line message replay
- Real-time agent interaction
"""

from .conversation_client import ConversationReplayClient
from .server_manager import ServerManager
from .conversation_processor import ConversationProcessor

__all__ = ['ConversationReplayClient', 'ServerManager', 'ConversationProcessor']
