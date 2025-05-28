"""
Session manager for handling multiple AILoop instances in the interactive server.

This module provides the InteractiveSessionManager class which manages:
- Creation and destruction of AILoop instances per WebSocket connection
- Session lifecycle management
- Resource cleanup on disconnect
- WebSocket-to-session mapping
"""

import asyncio
import logging
import uuid
from typing import Dict, Optional
from fastapi import WebSocket

from ai_whisperer.interactive_ai import InteractiveAI
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.context_management import ContextManager
from .delegate_bridge import DelegateBridge

logger = logging.getLogger(__name__)


class InteractiveSession:
    """
    Represents a single interactive AI session bound to a WebSocket connection.
    """
    
    def __init__(self, session_id: str, websocket: WebSocket, config: dict):
        """
        Initialize an interactive session using Agent architecture.
        
        Args:
            session_id: Unique identifier for this session
            websocket: WebSocket connection for this session
            config: Configuration dictionary for AI service
        """
        self.session_id = session_id
        self.websocket = websocket
        self.config = config

        # Manage agents for this session
        self.agents = {}
        self.active_agent = None

        self.is_started = False
        self.delegate_bridge: Optional[DelegateBridge] = None
        
    def switch_agent(self, agent_id: str):
        """
        Switch the active agent for this session.
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent '{agent_id}' not found in session {self.session_id}")
        self.active_agent = self.agents[agent_id]

    async def start_ai_session(self, system_prompt: str = None) -> str:
        """
        Start the agent-based AI session for this connection.
        """
        if self.is_started:
            raise RuntimeError(f"Session {self.session_id} is already started")
        try:
            # Create the default agent using AgentFactory
            from ai_whisperer.agents.factory import AgentFactory
            agent_config = self.config.get("agent", {"preset_name": "default"})
            agent = AgentFactory.create_agent(agent_config)
            self.agents["default"] = agent
            self.active_agent = agent

            self.is_started = True
            return self.session_id
        except Exception as e:
            import logging
            logging.error(f"Failed to start agent session {self.session_id}: {e}")
            await self.cleanup()
            raise RuntimeError(f"Failed to start agent session: {e}")
    
    async def send_user_message(self, message: str):
        """
        Route a user message to the active agent.
        """
        if not self.is_started or not self.active_agent:
            raise RuntimeError(f"Session {self.session_id} is not started")
        try:
            return await self.active_agent.process_message(message)
        except Exception as e:
            import logging
            logging.error(f"Failed to send message to agent in session {self.session_id}: {e}")
            raise
    
    async def stop_ai_session(self) -> None:
        """
        Stop the AI session gracefully.
        """
        self.is_started = False
    
    async def send_notification(self, method: str, notification_data) -> None:
        """
        Send a JSON-RPC notification to the WebSocket client.
        Adds detailed debug logging about websocket state and errors.
        """
        import logging
        try:
            import json
            # Serialize notification data
            if hasattr(notification_data, 'model_dump'):
                params = notification_data.model_dump()
            elif isinstance(notification_data, dict):
                params = notification_data
            else:
                params = {"data": str(notification_data)}
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params
            }
            logging.debug(f"[send_notification] About to send notification {method} to session {self.session_id}. WebSocket: {self.websocket}")
            logging.debug(f"[send_notification] Notification payload: {notification}")
            try:
                await self.websocket.send_text(json.dumps(notification))
                logging.debug(f"[send_notification] Sent notification {method} to session {self.session_id}")
            except Exception as send_exc:
                logging.error(f"[send_notification] Exception during websocket.send_text: {send_exc}")
                raise
        except Exception as e:
            logging.error(f"[send_notification] Failed to send notification {method} to session {self.session_id}: {e}")
    
    async def cleanup(self) -> None:
        """
        Clean up session resources.
        """
        try:
            await self.stop_ai_session()
            self.agents.clear()
            self.active_agent = None
        except Exception as e:
            import logging
            logging.error(f"Error during cleanup of session {self.session_id}: {e}")


class InteractiveSessionManager:
    """
    Manages multiple InteractiveSession instances for WebSocket connections.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the session manager.

        Args:
            config: Application configuration dictionary
        """
        self.config = config
        self.sessions: Dict[str, InteractiveSession] = {}
        self.websocket_sessions: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()
        self._persistence_path = self.config.get("session_persistence_path", "sessions.json")
        
    async def create_session(self, websocket: WebSocket, session_params: dict = None) -> str:
        """
        Create a new interactive session for a WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_params: Optional session parameters

        Returns:
            Session ID

        Raises:
            RuntimeError: If session creation fails
        """
        session_id = str(uuid.uuid4())

        async with self._lock:
            try:
                session = InteractiveSession(session_id, websocket, self.config)
                self.sessions[session_id] = session
                self.websocket_sessions[websocket] = session_id
                logger.info(f"Created session {session_id} for WebSocket connection")
                await self.save_sessions()
                return session_id
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise RuntimeError(f"Failed to create session: {e}")
    
    async def start_session(self, session_id: str, system_prompt: str = None) -> str:
        """
        Start an AI session.
        
        Args:
            session_id: Session identifier
            system_prompt: Optional system prompt
            
        Returns:
            Session ID if successful
            
        Raises:
            ValueError: If session not found
            RuntimeError: If session start fails
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        return await session.start_ai_session(system_prompt)
    
    async def send_message(self, session_id: str, message: str) -> None:
        """
        Send a message to a session.
        
        Args:
            session_id: Session identifier
            message: Message to send
            
        Raises:
            ValueError: If session not found
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
            
        await session.send_user_message(message)
    
    async def stop_session(self, session_id: str) -> None:
        """
        Stop a session gracefully.
        
        Args:
            session_id: Session identifier
        """
        session = self.sessions.get(session_id)
        if session:
            await session.stop_ai_session()
    
    async def cleanup_session(self, session_id: str) -> None:
        """
        Clean up and remove a session.

        Args:
            session_id: Session identifier
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                try:
                    # Remove from websocket mapping
                    if session.websocket in self.websocket_sessions:
                        del self.websocket_sessions[session.websocket]

                    # Clean up session resources
                    await session.cleanup()

                    # Remove from sessions
                    del self.sessions[session_id]

                    logger.info(f"Cleaned up session {session_id}")
                    await self.save_sessions()
                except Exception as e:
                    logger.error(f"Error cleaning up session {session_id}: {e}")
    
    async def cleanup_websocket(self, websocket: WebSocket) -> None:
        """
        Clean up session associated with a WebSocket connection.
        
        Args:
            websocket: WebSocket connection that disconnected
        """
        session_id = self.websocket_sessions.get(websocket)
        if session_id:
            await self.cleanup_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[InteractiveSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            InteractiveSession instance or None if not found
        """
        return self.sessions.get(session_id)
    
    def get_session_by_websocket(self, websocket: WebSocket) -> Optional[InteractiveSession]:
        """
        Get a session by WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            InteractiveSession instance or None if not found
        """
        session_id = self.websocket_sessions.get(websocket)
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    def get_active_sessions_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self.sessions)
    
    async def cleanup_all_sessions(self) -> None:
        """
        Clean up all active sessions.
        """
        async with self._lock:
            session_ids = list(self.sessions.keys())
            for session_id in session_ids:
                await self.cleanup_session(session_id)
            logger.info("Cleaned up all sessions")
            await self.save_sessions()

# --- Persistence Methods ---

    async def save_sessions(self):
        """
        Persist session metadata (not websocket or live agent state).
        """
        import json
        try:
            # Only save session IDs and minimal info (not websocket or agent objects)
            data = [{"session_id": sid} for sid in self.sessions.keys()]
            with open(self._persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            logger.info(f"Saved {len(data)} sessions to {self._persistence_path}")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    async def load_sessions(self):
        """
        Load session metadata from disk (restores session IDs, not live objects).
        """
        import json
        try:
            with open(self._persistence_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only restore session IDs for now (websockets must reconnect)
            for entry in data:
                sid = entry.get("session_id")
                if sid and sid not in self.sessions:
                    # Placeholder: cannot restore websocket or agent state
                    self.sessions[sid] = None
            logger.info(f"Loaded {len(data)} sessions from {self._persistence_path}")
        except FileNotFoundError:
            logger.info("No persisted sessions found to load.")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
