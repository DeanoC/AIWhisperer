"""
Direct streaming session implementation that bypasses delegates.
This provides a cleaner, more direct approach to WebSocket streaming
without the complexity of the delegate pattern.
"""
import asyncio
import logging
import uuid
from typing import Dict, Optional, Any, Callable
from datetime import datetime

from fastapi import WebSocket
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.agents.stateless_agent import StatelessAgent
from ai_whisperer.agents.config import AgentConfig

from .message_models import (
    AIMessageChunkNotification,
    SessionStatusNotification,
    ToolCallNotification,
    SessionStatus
)

logger = logging.getLogger(__name__)


class StreamingSession:
    """
    A session that uses direct streaming without delegates.
    Each session manages its own agents and streams AI responses
    directly to the WebSocket.
    """
    
    def __init__(self, session_id: str, websocket: WebSocket, config: Optional[dict] = None):
        """
        Initialize a streaming session.
        
        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection
            config: Optional configuration dictionary
        """
        self.session_id = session_id
        self.websocket = websocket
        self.config = config or {}
        
        # Agent management
        self.agents: Dict[str, StatelessAgent] = {}
        self.active_agent: Optional[str] = None
        
        # Session state
        self.is_active = True
        self._lock = asyncio.Lock()
        
        # Create stateless AI loop for streaming
        self._ai_loop: Optional[StatelessAILoop] = None
        self._initialize_ai_loop()
    
    def _initialize_ai_loop(self):
        """Initialize the stateless AI loop."""
        try:
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
            
            # Create stateless AI loop
            self._ai_loop = StatelessAILoop(
                config=ai_config,
                ai_service=ai_service
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize AI loop: {e}")
            self._ai_loop = None
    
    async def create_agent(self, agent_id: str, system_prompt: str, config: Optional[AgentConfig] = None) -> StatelessAgent:
        """
        Create a new agent in this session.
        
        Args:
            agent_id: Unique identifier for the agent
            system_prompt: System prompt for the agent
            config: Optional agent configuration
            
        Returns:
            The created agent
        """
        async with self._lock:
            if agent_id in self.agents:
                raise ValueError(f"Agent {agent_id} already exists")
            
            # Create agent context
            context = AgentContext(agent_id=agent_id)
            context.store_message({"role": "system", "content": system_prompt})
            
            # Create agent config if not provided
            if config is None:
                # Extract model info from session config
                openrouter_config = self.config.get("openrouter", {})
                
                config = AgentConfig(
                    name=agent_id,
                    description=f"Agent {agent_id}",
                    system_prompt=system_prompt,
                    model_name=openrouter_config.get("model", "openai/gpt-3.5-turbo"),
                    provider="openrouter",
                    api_settings={
                        "api_key": openrouter_config.get("api_key", "")
                    },
                    generation_params={
                        "temperature": openrouter_config.get("params", {}).get("temperature", 0.7),
                        "max_tokens": openrouter_config.get("params", {}).get("max_tokens", 1000)
                    }
                )
            
            # Create stateless agent with direct AI loop reference
            agent = StatelessAgent(
                config=config,
                context=context,
                ai_loop=self._ai_loop  # Direct reference, no delegates
            )
            
            self.agents[agent_id] = agent
            
            # Set as active if first agent
            if self.active_agent is None:
                self.active_agent = agent_id
            
            logger.info(f"Created agent {agent_id} in session {self.session_id}")
            return agent
    
    async def send_message(self, message: str, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a message to an agent and stream the response.
        
        Args:
            message: The user message
            agent_id: Optional agent ID (uses active agent if not specified)
            
        Returns:
            Result dictionary with response data
        """
        async with self._lock:
            # Get the target agent
            target_agent_id = agent_id or self.active_agent
            if not target_agent_id or target_agent_id not in self.agents:
                return {"success": False, "error": "No active agent"}
            
            agent = self.agents[target_agent_id]
            
            # Stream the response
            try:
                # Create streaming callback
                async def on_chunk(chunk: str):
                    await self._send_token_notification(chunk)
                
                # Process with agent
                result = await agent.process_message(
                    message=message,
                    on_stream_chunk=on_chunk
                )
                
                # Send final chunk
                await self._send_token_notification("", is_final=True)
                
                # Handle different result types
                if isinstance(result, dict):
                    # Handle errors
                    if result.get('error'):
                        await self._send_error_notification(str(result['error']))
                    
                    # Handle tool calls if present
                    if result.get('tool_calls'):
                        await self._send_tool_notifications(result['tool_calls'])
                    
                    return {
                        "success": True,
                        "response": result.get('response'),
                        "tool_calls": result.get('tool_calls'),
                        "finish_reason": result.get('finish_reason', 'stop')
                    }
                else:
                    # Simple string response
                    return {
                        "success": True,
                        "response": result,
                        "tool_calls": None,
                        "finish_reason": 'stop'
                    }
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self._send_error_notification(str(e))
                return {"success": False, "error": str(e)}
    
    async def _send_notification(self, method: str, params: Any):
        """
        Send a JSON-RPC notification to the WebSocket.
        
        Args:
            method: The notification method name
            params: The notification parameters
        """
        try:
            notification = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params.model_dump() if hasattr(params, 'model_dump') else params
            }
            await self.websocket.send_json(notification)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    async def _send_token_notification(self, token: str, is_final: bool = False):
        """
        Send a token/chunk notification.
        
        Args:
            token: The token/chunk content
            is_final: Whether this is the final chunk
        """
        notification = AIMessageChunkNotification(
            sessionId=self.session_id,
            chunk=token,
            isFinal=is_final
        )
        await self._send_notification("AIMessageChunkNotification", notification)
    
    async def _send_tool_notifications(self, tool_calls: list):
        """
        Send tool call notifications.
        
        Args:
            tool_calls: List of tool call dictionaries
        """
        import json
        
        for tool_call in tool_calls:
            # Parse arguments if they're a string
            arguments = tool_call.get("function", {}).get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {"raw": arguments}
            
            notification = ToolCallNotification(
                sessionId=self.session_id,
                toolCallId=tool_call.get("id", f"tool-{uuid.uuid4()}"),
                toolName=tool_call.get("function", {}).get("name", "unknown"),
                arguments=arguments
            )
            await self._send_notification("ToolCallNotification", notification)
    
    async def _send_error_notification(self, error: str):
        """
        Send an error notification.
        
        Args:
            error: Error message
        """
        notification = SessionStatusNotification(
            sessionId=self.session_id,
            status=SessionStatus.Error,
            reason=error
        )
        await self._send_notification("SessionStatusNotification", notification)
    
    async def _process_ai_stream(self, stream):
        """
        Process an AI response stream.
        
        Args:
            stream: The AI response stream
            
        Returns:
            Result dictionary
        """
        try:
            result = {
                'response': '',
                'tool_calls': None,
                'finish_reason': 'stop',
                'error': None
            }
            
            async for chunk in stream:
                if chunk.get('content'):
                    result['response'] += chunk['content']
                    await self._send_token_notification(chunk['content'])
                
                if chunk.get('tool_calls'):
                    result['tool_calls'] = chunk['tool_calls']
                    # Send tool call notifications
                    await self._send_tool_notifications(chunk['tool_calls'])
                
                if chunk.get('finish_reason'):
                    result['finish_reason'] = chunk['finish_reason']
                
                if chunk.get('is_final'):
                    await self._send_token_notification("", is_final=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in stream processing: {e}")
            # Send error notification
            await self._send_error_notification(str(e))
            return {
                'response': result.get('response', ''),
                'tool_calls': None,
                'finish_reason': 'error',
                'error': e
            }
    
    async def _stream_response(self, message: str, on_chunk: Optional[Callable] = None):
        """
        Stream a response for a message.
        
        Args:
            message: The message to process
            on_chunk: Optional callback for chunks
        """
        # Mock implementation for testing
        chunks = ["This ", "is ", "a ", "test ", "response."]
        for chunk in chunks:
            if on_chunk:
                await on_chunk(chunk)
            await asyncio.sleep(0.01)  # Simulate streaming delay
    
    async def cleanup(self):
        """Clean up the session."""
        self.is_active = False
        logger.info(f"Cleaned up streaming session {self.session_id}")