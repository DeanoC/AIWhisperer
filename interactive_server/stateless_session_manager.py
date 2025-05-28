"""
Stateless Session Manager using the refactored agent architecture.
This replaces the legacy delegate-based system with direct streaming support.
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from fastapi import WebSocket
from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.agents.factory import AgentFactory
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.context_management import ContextManager
from .message_models import AIMessageChunkNotification

logger = logging.getLogger(__name__)


class StatelessInteractiveSession:
    """
    Interactive session using StatelessAgent architecture.
    Supports direct streaming without delegates.
    """
    
    def __init__(self, session_id: str, websocket: WebSocket, config: dict):
        """
        Initialize a stateless interactive session.
        
        Args:
            session_id: Unique identifier for this session
            websocket: WebSocket connection for this session
            config: Configuration dictionary for AI service
        """
        self.session_id = session_id
        self.websocket = websocket
        self.config = config
        
        # Agent management
        self.agents: Dict[str, StatelessAgent] = {}
        self.active_agent: Optional[str] = None
        
        # Session state
        self.is_started = False
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    def _create_stateless_ai_loop(self, agent_id: str = None) -> StatelessAILoop:
        """Create a StatelessAILoop instance for an agent"""
        # Extract AI configuration
        openrouter_config = self.config.get("openrouter", {})
        ai_config = AIConfig(
            api_key=openrouter_config.get("api_key"),
            model_id=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
            temperature=openrouter_config.get("params", {}).get("temperature", 0.7),
            max_tokens=openrouter_config.get("params", {}).get("max_tokens", 1000)
        )
        
        # Create AI service
        ai_service = OpenRouterAIService(config=ai_config)
        
        # Create StatelessAILoop
        return StatelessAILoop(
            config=ai_config,
            ai_service=ai_service
        )
    
    async def create_agent(self, agent_id: str, system_prompt: str, config: Optional[AgentConfig] = None) -> StatelessAgent:
        """
        Create a new stateless agent.
        
        Args:
            agent_id: Unique identifier for the agent
            system_prompt: System prompt for the agent
            config: Optional AgentConfig, will create default if not provided
            
        Returns:
            The created StatelessAgent instance
        """
        async with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent '{agent_id}' already exists in session")
            
            # Create agent config if not provided
            if config is None:
                openrouter_config = self.config.get("openrouter", {})
                config = AgentConfig(
                    name=agent_id,
                    description=f"Agent {agent_id}",
                    system_prompt=system_prompt,
                    model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
                    provider="openrouter",
                    api_settings={"api_key": openrouter_config.get("api_key")},
                    generation_params=openrouter_config.get("params", {}),
                    tool_permissions=[],
                    tool_limits={},
                    context_settings={"max_context_messages": 50}
                )
            
            # Create agent context
            context = AgentContext(agent_id=agent_id, system_prompt=system_prompt)
            
            # Create stateless AI loop for this agent
            ai_loop = self._create_stateless_ai_loop(agent_id)
            
            # Create stateless agent
            agent = StatelessAgent(config, context, ai_loop)
            
            # Store agent
            self.agents[agent_id] = agent
            
            # Set as active if first agent
            if self.active_agent is None:
                self.active_agent = agent_id
                # Mark session as started when first agent is created
                self.is_started = True
            
            # Notify client
            await self.send_notification("agent.created", {
                "agent_id": agent_id,
                "active": self.active_agent == agent_id
            })
            
            return agent
    
    async def start_ai_session(self, system_prompt: str = None) -> str:
        """
        Start the AI session by creating a default agent.
        """
        if self.is_started:
            raise RuntimeError(f"Session {self.session_id} is already started")
        
        try:
            # Create default agent
            system_prompt = system_prompt or "You are a helpful AI assistant."
            await self.create_agent("default", system_prompt)
            
            self.is_started = True
            logger.info(f"Started session {self.session_id} with default agent")
            
            return self.session_id
            
        except Exception as e:
            logger.error(f"Failed to start session {self.session_id}: {e}")
            await self.cleanup()
            raise RuntimeError(f"Failed to start session: {e}")
    
    async def switch_agent(self, agent_id: str) -> None:
        """
        Switch the active agent for this session.
        """
        async with self._lock:
            if agent_id not in self.agents:
                raise ValueError(f"Agent '{agent_id}' not found in session")
            
            old_agent = self.active_agent
            self.active_agent = agent_id
            
            # Notify client
            await self.send_notification("agent.switched", {
                "from": old_agent,
                "to": agent_id
            })
            
            logger.info(f"Switched active agent from '{old_agent}' to '{agent_id}' in session {self.session_id}")
    
    async def send_user_message(self, message: str):
        """
        Route a user message to the active agent with streaming support.
        """
        if not self.is_started or not self.active_agent:
            raise RuntimeError(f"Session {self.session_id} is not started or no active agent")
        
        try:
            agent = self.agents[self.active_agent]
            
            # Create streaming callback
            async def send_chunk(chunk: str):
                """Send a chunk of AI response to the client"""
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
                    logger.debug(f"Sent chunk: {len(chunk)} chars")
                except Exception as e:
                    logger.error(f"Error sending chunk: {e}")
            
            # Process message with streaming
            result = await agent.process_message(message, on_stream_chunk=send_chunk)
            
            # Send final notification
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
            logger.error(f"Failed to send message to agent '{self.active_agent}' in session {self.session_id}: {e}")
            raise
    
    async def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the session for persistence.
        """
        state = {
            "session_id": self.session_id,
            "is_started": self.is_started,
            "active_agent": self.active_agent,
            "agents": {}
        }
        
        # Save each agent's state
        for agent_id, agent in self.agents.items():
            agent_state = {
                "config": {
                    "name": agent.config.name,
                    "description": agent.config.description,
                    "system_prompt": agent.config.system_prompt,
                    "model_name": agent.config.model_name,
                    "provider": agent.config.provider,
                    "api_settings": agent.config.api_settings,
                    "generation_params": agent.config.generation_params,
                    "tool_permissions": agent.config.tool_permissions,
                    "tool_limits": agent.config.tool_limits,
                    "context_settings": agent.config.context_settings
                },
                "context": {
                    "messages": agent.context.retrieve_messages(),
                    "metadata": agent.context._metadata if hasattr(agent.context, '_metadata') else {}
                }
            }
            state["agents"][agent_id] = agent_state
        
        return state
    
    async def restore_state(self, state: Dict[str, Any]) -> None:
        """
        Restore session state from a saved state dictionary.
        """
        self.is_started = state.get("is_started", False)
        
        # Restore agents
        for agent_id, agent_state in state.get("agents", {}).items():
            # Reconstruct AgentConfig
            config_data = agent_state["config"]
            config = AgentConfig(**config_data)
            
            # Create agent with config
            agent = await self.create_agent(
                agent_id, 
                config.system_prompt,
                config
            )
            
            # Restore context
            context_data = agent_state.get("context", {})
            for message in context_data.get("messages", []):
                agent.context.store_message(message)
            
            # Restore metadata if supported
            if hasattr(agent.context, '_metadata'):
                agent.context._metadata = context_data.get("metadata", {})
        
        # Restore active agent
        if state.get("active_agent") and state["active_agent"] in self.agents:
            self.active_agent = state["active_agent"]
    
    async def stop_ai_session(self) -> None:
        """
        Stop the AI session gracefully.
        """
        self.is_started = False
        logger.info(f"Stopped session {self.session_id}")
    
    async def cleanup(self) -> None:
        """
        Clean up all resources associated with this session.
        """
        logger.info(f"Cleaning up session {self.session_id}")
        
        # Stop AI session
        await self.stop_ai_session()
        
        # Clear agents
        self.agents.clear()
        self.active_agent = None
        
        logger.info(f"Session {self.session_id} cleaned up")
    
    async def send_notification(self, method: str, params: Any = None) -> None:
        """
        Send a JSON-RPC notification to the client.
        """
        if self.websocket:
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params
            }
            try:
                await self.websocket.send_json(notification)
            except Exception as e:
                logger.error(f"Failed to send notification to client: {e}")


class StatelessSessionManager:
    """
    Manages multiple stateless interactive sessions for WebSocket connections.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the session manager.
        
        Args:
            config: Global configuration dictionary
        """
        self.config = config
        self.sessions: Dict[str, StatelessInteractiveSession] = {}
        self.websocket_sessions: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()
        
        # Load persisted sessions
        self._load_sessions()
        
    def _load_sessions(self):
        """Load persisted session IDs from file"""
        try:
            session_file = Path("sessions.json")
            if session_file.exists():
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('sessions', []))} persisted sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def _save_sessions(self):
        """Save current session IDs to file"""
        try:
            data = {
                "sessions": list(self.sessions.keys()),
                "timestamp": datetime.now().isoformat()
            }
            with open("sessions.json", 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.sessions)} sessions to sessions.json")
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    async def create_session(self, websocket: WebSocket) -> str:
        """
        Create a new session for a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            The session ID
        """
        async with self._lock:
            session_id = str(uuid.uuid4())
            session = StatelessInteractiveSession(session_id, websocket, self.config)
            
            self.sessions[session_id] = session
            self.websocket_sessions[websocket] = session_id
            
            logger.info(f"Created session {session_id} for WebSocket connection")
            
            # Save sessions
            self._save_sessions()
            
            return session_id
    
    async def start_session(self, session_id: str, system_prompt: str = None) -> str:
        """
        Start an AI session.
        
        Args:
            session_id: The session ID
            system_prompt: Optional system prompt
            
        Returns:
            The session ID
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return await session.start_ai_session(system_prompt)
    
    async def send_message(self, session_id: str, message: str):
        """
        Send a message to a session.
        
        Args:
            session_id: The session ID
            message: The message to send
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return await session.send_user_message(message)
    
    async def stop_session(self, session_id: str) -> None:
        """
        Stop an AI session without cleaning up resources.
        
        Args:
            session_id: The session ID
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        await session.stop_ai_session()
    
    def get_session(self, session_id: str) -> Optional[StatelessInteractiveSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def get_session_by_websocket(self, websocket: WebSocket) -> Optional[StatelessInteractiveSession]:
        """Get a session by WebSocket connection"""
        session_id = self.websocket_sessions.get(websocket)
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    async def cleanup_session(self, session_id: str) -> None:
        """
        Clean up a session and remove it from tracking.
        
        Args:
            session_id: The session ID to clean up
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if session:
                try:
                    await session.cleanup()
                except Exception as e:
                    logger.error(f"Error during session cleanup for {session_id}: {e}")
                    # Continue with cleanup even if session cleanup fails
                
                del self.sessions[session_id]
                
                # Remove WebSocket mapping
                ws_to_remove = None
                for ws, sid in self.websocket_sessions.items():
                    if sid == session_id:
                        ws_to_remove = ws
                        break
                if ws_to_remove:
                    del self.websocket_sessions[ws_to_remove]
                
                logger.info(f"Cleaned up session {session_id}")
                
                # Save sessions
                self._save_sessions()
    
    async def cleanup_websocket(self, websocket: WebSocket) -> None:
        """
        Clean up session associated with a WebSocket.
        
        Args:
            websocket: The WebSocket connection
        """
        session_id = self.websocket_sessions.get(websocket)
        if session_id:
            await self.cleanup_session(session_id)
    
    async def cleanup_all(self) -> None:
        """Clean up all sessions"""
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            await self.cleanup_session(session_id)
    
    def get_active_sessions_count(self) -> int:
        """Get the count of active sessions"""
        return len(self.sessions)
    
    async def cleanup_all_sessions(self) -> None:
        """Alias for cleanup_all() for backward compatibility"""
        await self.cleanup_all()