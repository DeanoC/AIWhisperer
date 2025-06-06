"""
WebSocket endpoints for async agent management.

Provides API for creating, managing, and monitoring async agent sessions.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import WebSocket

from ai_whisperer.services.agents.async_session_manager import AsyncAgentSessionManager, AgentState
# from .message_models import ErrorCode  # Not available yet

logger = logging.getLogger(__name__)


class AsyncAgentEndpoints:
    """Handles async agent management via WebSocket."""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.async_managers: Dict[str, AsyncAgentSessionManager] = {}
        
    def register_handlers(self, router):
        """Register async agent handlers with the router."""
        # Async agent management
        router.register_handler("async.createAgent", self.create_async_agent)
        router.register_handler("async.startAgent", self.start_agent)
        router.register_handler("async.stopAgent", self.stop_agent)
        router.register_handler("async.sleepAgent", self.sleep_agent)
        router.register_handler("async.wakeAgent", self.wake_agent)
        router.register_handler("async.sendTask", self.send_task_to_agent)
        router.register_handler("async.getAgentStates", self.get_agent_states)
        router.register_handler("async.broadcastEvent", self.broadcast_event)
        
        logger.info("Registered async agent endpoints")
        
    async def _get_or_create_manager(self, session_id: str, websocket=None) -> AsyncAgentSessionManager:
        """Get or create async manager for a session."""
        if session_id not in self.async_managers:
            # Get config from session
            session = self.session_manager.get_session(session_id)
            if not session:
                raise ValueError(f"No session found: {session_id}")
                
            config = session.config if hasattr(session, 'config') else {}
            
            # Use new refactored manager if feature flag is set
            if config.get("use_refactored_async_agents", True):
                from ai_whisperer.services.agents.async_session_manager_v2 import AsyncAgentSessionManager
            else:
                from ai_whisperer.services.agents.async_session_manager import AsyncAgentSessionManager
            
            # Create notification callback
            async def notification_callback(method: str, params: Dict[str, Any]):
                """Send WebSocket notifications."""
                # Get the current WebSocket for this session
                ws = websocket
                if ws:
                    try:
                        await ws.send_json({
                            "jsonrpc": "2.0",
                            "method": method,
                            "params": {
                                **params,
                                "sessionId": session_id
                            }
                        })
                    except Exception as e:
                        logger.error(f"Failed to send notification: {e}")
            
            # Create manager with callback
            manager = AsyncAgentSessionManager(config, notification_callback)
            await manager.start()
            self.async_managers[session_id] = manager
            
        return self.async_managers[session_id]
        
    async def create_async_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Create a new async agent session."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            auto_start = params.get("autoStart", True)
            
            if not session_id or not agent_id:
                return {
                    "error": "INVALID_PARAMS",
                    "message": "sessionId and agentId are required"
                }
                
            # Get or create manager
            manager = await self._get_or_create_manager(session_id, websocket)
            
            # Create agent session
            agent_session = await manager.create_agent_session(agent_id, auto_start)
            
            return {
                "success": True,
                "agentId": agent_id,
                "state": agent_session.state.value,
                "autoStarted": auto_start
            }
            
        except Exception as e:
            logger.error(f"Error creating async agent: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def start_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Start an agent's background processor."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            
            manager = await self._get_or_create_manager(session_id)
            
            if agent_id not in manager.sessions:
                return {
                    "error": "INVALID_PARAMS",
                    "message": f"Agent {agent_id} not found"
                }
                
            session = manager.sessions[agent_id]
            if not session.background_task:
                # Start processor
                import asyncio
                task = asyncio.create_task(manager._agent_processor(session))
                session.background_task = task
                manager._background_tasks.add(task)
                
            return {
                "success": True,
                "agentId": agent_id,
                "state": session.state.value
            }
            
        except Exception as e:
            logger.error(f"Error starting agent: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def stop_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Stop an agent."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            
            manager = await self._get_or_create_manager(session_id)
            
            if agent_id not in manager.sessions:
                return {
                    "error": "INVALID_PARAMS",
                    "message": f"Agent {agent_id} not found"
                }
                
            session = manager.sessions[agent_id]
            session.state = AgentState.STOPPED
            
            if session.background_task:
                session.background_task.cancel()
                
            return {
                "success": True,
                "agentId": agent_id,
                "state": "stopped"
            }
            
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def sleep_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Put an agent to sleep."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            duration = params.get("durationSeconds")
            wake_events = params.get("wakeEvents", [])
            
            manager = await self._get_or_create_manager(session_id)
            
            await manager.sleep_agent(
                agent_id,
                duration_seconds=duration,
                wake_events=set(wake_events) if wake_events else None
            )
            
            return {
                "success": True,
                "agentId": agent_id,
                "state": "sleeping",
                "duration": duration,
                "wakeEvents": wake_events
            }
            
        except Exception as e:
            logger.error(f"Error sleeping agent: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def wake_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Wake a sleeping agent."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            reason = params.get("reason", "manual wake")
            
            manager = await self._get_or_create_manager(session_id)
            
            await manager.wake_agent(agent_id, reason)
            
            return {
                "success": True,
                "agentId": agent_id,
                "state": "idle",
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error waking agent: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def send_task_to_agent(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Send a task directly to an agent."""
        try:
            session_id = params.get("sessionId")
            agent_id = params.get("agentId")
            prompt = params.get("prompt")
            
            if not prompt:
                return {
                    "error": "INVALID_PARAMS",
                    "message": "prompt is required"
                }
                
            manager = await self._get_or_create_manager(session_id)
            
            # Send task
            await manager.send_task_to_agent(agent_id, prompt)
            
            return {
                "success": True,
                "agentId": agent_id,
                "taskQueued": True
            }
            
        except Exception as e:
            logger.error(f"Error sending task: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def get_agent_states(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Get states of all agents in a session."""
        try:
            session_id = params.get("sessionId")
            
            manager = await self._get_or_create_manager(session_id)
            
            states = manager.get_agent_states()
            
            return {
                "success": True,
                "agents": states
            }
            
        except Exception as e:
            logger.error(f"Error getting agent states: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def broadcast_event(self, params: Dict[str, Any], websocket=None) -> Dict[str, Any]:
        """Broadcast an event to agents."""
        try:
            session_id = params.get("sessionId")
            event = params.get("event")
            data = params.get("data", {})
            
            if not event:
                return {
                    "error": "INVALID_PARAMS",
                    "message": "event is required"
                }
                
            manager = await self._get_or_create_manager(session_id)
            
            await manager.broadcast_event(event, data)
            
            return {
                "success": True,
                "event": event,
                "broadcast": True
            }
            
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            return {
                "error": "INTERNAL_ERROR",
                "message": str(e)
            }
            
    async def cleanup_session(self, session_id: str):
        """Clean up async agents for a session."""
        if session_id in self.async_managers:
            manager = self.async_managers[session_id]
            await manager.stop()
            del self.async_managers[session_id]
            logger.info(f"Cleaned up async agents for session {session_id}")