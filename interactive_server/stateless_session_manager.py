"""
Stateless session manager for direct WebSocket communication.
This manager handles sessions without using the event notification system.
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import uuid

from interactive_server.streaming_session import StreamingSession
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService

logger = logging.getLogger(__name__)


class StatelessSessionManager:
    """
    Manages interactive sessions with direct WebSocket streaming.
    Each session is a StreamingSession that handles its own WebSocket communication.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the stateless session manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.sessions: Dict[str, StreamingSession] = {}
        self.sessions_file = Path("sessions.json")
        
        # Load persisted sessions (without restoring actual session objects)
        self.session_metadata = self._load_session_metadata()
        
    def _load_session_metadata(self) -> Dict[str, Any]:
        """Load session metadata from disk."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} persisted sessions")
                    return data
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
        return {}
    
    def _save_session_metadata(self):
        """Save session metadata to disk."""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.session_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    async def create_session(self, websocket) -> str:
        """
        Create a new streaming session.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        # Create AI config from application config
        openrouter_config = self.config.get('openrouter', {})
        ai_config = AIConfig(
            api_key=openrouter_config.get('api_key', ''),
            model_id=openrouter_config.get('model', 'openai/gpt-3.5-turbo'),
            temperature=openrouter_config.get('params', {}).get('temperature', 0.7),
            max_tokens=openrouter_config.get('params', {}).get('max_tokens', None),
            site_url=openrouter_config.get('site_url', 'http://AIWhisperer:8000'),
            app_name=openrouter_config.get('app_name', 'AIWhisperer'),
        )
        
        # Create AI service
        ai_service = OpenRouterAIService(ai_config)
        
        # Create streaming session
        session = StreamingSession(
            session_id=session_id,
            websocket=websocket,
            ai_config=ai_config,
            ai_service=ai_service
        )
        
        self.sessions[session_id] = session
        
        # Store metadata
        self.session_metadata[session_id] = {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'agents': {}
        }
        self._save_session_metadata()
        
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """
        Get an active session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            StreamingSession or None if not found
        """
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """
        Close and clean up a session.
        
        Args:
            session_id: Session ID
        """
        session = self.sessions.pop(session_id, None)
        if session:
            # Clean up any resources
            logger.info(f"Closed session: {session_id}")
    
    async def list_sessions(self) -> Dict[str, Any]:
        """
        List all sessions (active and persisted).
        
        Returns:
            Dict with session information
        """
        result = {
            'active': [],
            'persisted': []
        }
        
        # Active sessions
        for session_id, session in self.sessions.items():
            result['active'].append({
                'id': session_id,
                'agents': list(session.agents.keys()) if hasattr(session, 'agents') else []
            })
        
        # Persisted sessions (from metadata)
        for session_id, metadata in self.session_metadata.items():
            if session_id not in self.sessions:  # Only show inactive sessions
                result['persisted'].append({
                    'id': session_id,
                    'created_at': metadata.get('created_at'),
                    'agents': list(metadata.get('agents', {}).keys())
                })
        
        return result
    
    async def send_message(self, session_id: str, message: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to a session.
        
        Args:
            session_id: Session ID
            message: User message
            agent_id: Optional agent ID
            
        Returns:
            Response dict or error
        """
        session = await self.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        try:
            result = await session.send_message(message, agent_id)
            
            # Update metadata
            if agent_id and agent_id not in self.session_metadata[session_id]['agents']:
                self.session_metadata[session_id]['agents'][agent_id] = {
                    'created_at': datetime.now().isoformat()
                }
                self._save_session_metadata()
            
            return result
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {'error': str(e)}