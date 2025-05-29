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
from ai_whisperer.context.context_manager import AgentContextManager
from ai_whisperer.path_management import PathManager
from .message_models import AIMessageChunkNotification

logger = logging.getLogger(__name__)


class StatelessInteractiveSession:
    """
    Interactive session using StatelessAgent architecture.
    Supports direct streaming without delegates.
    """
    
    def __init__(self, session_id: str, websocket: WebSocket, config: dict, agent_registry=None, prompt_system=None, project_path: Optional[str] = None):
        """
        Initialize a stateless interactive session.
        
        Args:
            session_id: Unique identifier for this session
            websocket: WebSocket connection for this session
            config: Configuration dictionary for AI service
            agent_registry: Optional AgentRegistry instance
            prompt_system: Optional PromptSystem instance
            project_path: Optional path to the project workspace
        """
        self.session_id = session_id
        self.websocket = websocket
        self.config = config
        self.agent_registry = agent_registry
        self.prompt_system = prompt_system
        self.project_path = project_path
        
        # Agent management
        self.agents: Dict[str, StatelessAgent] = {}
        self.active_agent: Optional[str] = None
        self.introduced_agents: set = set()  # Track which agents have introduced themselves
        
        # Continuation tracking
        self._continuation_depth = 0  # Track continuation depth to prevent loops
        self._max_continuation_depth = 3  # Maximum continuation depth
        
        # Session state
        self.is_started = False
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Initialize context tracking
        path_manager = PathManager()
        if project_path:
            path_manager.initialize(config_values={'workspace_path': project_path})
        self.context_manager = AgentContextManager(session_id, path_manager)
        
        # Register tools for interactive sessions
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools needed for interactive sessions."""
        from ai_whisperer.tools.tool_registry import get_tool_registry
        
        tool_registry = get_tool_registry()
        
        # Register basic file operation tools
        from ai_whisperer.tools.read_file_tool import ReadFileTool
        from ai_whisperer.tools.write_file_tool import WriteFileTool
        from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
        from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
        from ai_whisperer.tools.search_files_tool import SearchFilesTool
        from ai_whisperer.tools.get_file_content_tool import GetFileContentTool
        
        tool_registry.register_tool(ReadFileTool())
        tool_registry.register_tool(WriteFileTool())
        tool_registry.register_tool(ExecuteCommandTool())
        tool_registry.register_tool(ListDirectoryTool())
        tool_registry.register_tool(SearchFilesTool())
        tool_registry.register_tool(GetFileContentTool())
        
        # Register advanced analysis tools
        from ai_whisperer.tools.find_pattern_tool import FindPatternTool
        from ai_whisperer.tools.workspace_stats_tool import WorkspaceStatsTool
        
        # These tools need PathManager instance
        path_manager = PathManager()
        tool_registry.register_tool(FindPatternTool(path_manager))
        tool_registry.register_tool(WorkspaceStatsTool(path_manager))
        
        # Register RFC management tools
        from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
        from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
        from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
        from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
        from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
        
        tool_registry.register_tool(CreateRFCTool())
        tool_registry.register_tool(ReadRFCTool())
        tool_registry.register_tool(ListRFCsTool())
        tool_registry.register_tool(UpdateRFCTool())
        tool_registry.register_tool(MoveRFCTool())
        
        # Register codebase analysis tools
        from ai_whisperer.tools.analyze_languages_tool import AnalyzeLanguagesTool
        from ai_whisperer.tools.find_similar_code_tool import FindSimilarCodeTool
        from ai_whisperer.tools.get_project_structure_tool import GetProjectStructureTool
        
        tool_registry.register_tool(AnalyzeLanguagesTool())
        tool_registry.register_tool(FindSimilarCodeTool())
        tool_registry.register_tool(GetProjectStructureTool())
        
        # Register web research tools
        from ai_whisperer.tools.web_search_tool import WebSearchTool
        from ai_whisperer.tools.fetch_url_tool import FetchURLTool
        
        tool_registry.register_tool(WebSearchTool())
        tool_registry.register_tool(FetchURLTool())
        
        logger.info("Registered all tools for interactive session")
    
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
            return await self._create_agent_internal(agent_id, system_prompt, config)
    
    async def _create_agent_internal(self, agent_id: str, system_prompt: str, config: Optional[AgentConfig] = None, agent_registry_info=None) -> StatelessAgent:
        """Internal method to create agent - assumes lock is already held"""
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
        logger.info(f"Created AgentContext for {agent_id} with system prompt length: {len(system_prompt)}")
        
        # Create stateless AI loop for this agent
        ai_loop = self._create_stateless_ai_loop(agent_id)
        
        # Create stateless agent with registry info for tool filtering
        agent = StatelessAgent(config, context, ai_loop, agent_registry_info)
        logger.info(f"Created StatelessAgent for {agent_id}")
        
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
        Uses Alice (agent 'a') as the default if available.
        """
        if self.is_started:
            raise RuntimeError(f"Session {self.session_id} is already started")
        
        try:
            self.is_started = True
            
            # Try to use Alice as default agent
            if self.agent_registry and self.agent_registry.get_agent("A"):
                try:
                    # Switch to Alice - this will create the agent from registry
                    await self.switch_agent("a")
                    logger.info(f"Started session {self.session_id} with Alice agent")
                    return self.session_id
                except Exception as e:
                    logger.error(f"Failed to create Alice agent: {e}, falling back to default")
                    # Fall through to create default agent
            
            # Fallback to generic default agent
            system_prompt = system_prompt or "You are a helpful AI assistant."
            await self.create_agent("default", system_prompt)
            logger.info(f"Started session {self.session_id} with default agent")
            
            # Have the default agent introduce itself
            await self._agent_introduction()
            
            return self.session_id
            
        except Exception as e:
            logger.error(f"Failed to start session {self.session_id}: {e}")
            import traceback
            traceback.print_exc()
            self.is_started = False
            await self.cleanup()
            raise RuntimeError(f"Failed to start session: {e}")
    
    async def switch_agent(self, agent_id: str) -> None:
        """
        Switch the active agent for this session.
        Creates the agent from registry if it doesn't exist.
        """
        logger.info(f"switch_agent called with agent_id: {agent_id}")
        
        async with self._lock:
            logger.info(f"Acquired lock for switch_agent")
            
            # If agent doesn't exist in session, try to create it from registry
            if agent_id not in self.agents and self.agent_registry:
                logger.info(f"Agent {agent_id} not in session, checking registry")
                agent_info = self.agent_registry.get_agent(agent_id.upper())
                if not agent_info:
                    raise ValueError(f"Agent '{agent_id}' not found in registry")
                
                logger.info(f"Found agent info: {agent_info.name}")
                
                # Load the agent's prompt from the prompt system
                system_prompt = f"You are {agent_info.name}, {agent_info.description}"  # Better fallback
                if self.prompt_system and agent_info.prompt_file:
                    logger.info(f"Attempting to load prompt file: {agent_info.prompt_file}")
                    try:
                        # Remove .prompt.md extension if present for prompt system
                        prompt_name = agent_info.prompt_file
                        if prompt_name.endswith('.prompt.md'):
                            prompt_name = prompt_name[:-10]  # Remove '.prompt.md'
                        elif prompt_name.endswith('.md'):
                            prompt_name = prompt_name[:-3]  # Remove '.md'
                        
                        logger.info(f"Trying to load prompt: agents/{prompt_name}")
                        try:
                            prompt = self.prompt_system.get_formatted_prompt("agents", prompt_name)
                            system_prompt = prompt
                            logger.info(f"Successfully loaded prompt for {agent_id}")
                        except Exception as e1:
                            logger.warning(f"Failed to load prompt: {e1}")
                            # Keep the fallback prompt
                            logger.info(f"Using fallback prompt for {agent_info.name}")
                    except Exception as e:
                        logger.error(f"Failed to load prompt for agent {agent_id}: {e}")
                        logger.error(f"Using fallback prompt for {agent_info.name}")
                
                # Create the agent with the loaded prompt and registry info
                logger.info(f"About to create agent with prompt: {system_prompt[:200]}...")
                await self._create_agent_internal(agent_id, system_prompt, agent_registry_info=agent_info)
                logger.info(f"Created agent '{agent_id}' from registry with system prompt")
            
            # Verify agent exists now
            if agent_id not in self.agents:
                logger.error(f"Agent '{agent_id}' not found in session after creation attempt")
                raise ValueError(f"Agent '{agent_id}' not found in session")
            
            old_agent = self.active_agent
            self.active_agent = agent_id
            logger.info(f"Set active agent to: {agent_id}")
            
            # Notify client
            logger.info(f"Sending agent.switched notification")
            await self.send_notification("agent.switched", {
                "from": old_agent,
                "to": agent_id
            })
            
            logger.info(f"Switched active agent from '{old_agent}' to '{agent_id}' in session {self.session_id}")
            
            # Have the agent introduce itself if not already introduced
            if self.active_agent and self.active_agent not in self.introduced_agents:
                await self._agent_introduction()
                self.introduced_agents.add(self.active_agent)
    
    async def send_user_message(self, message: str, is_continuation: bool = False):
        """
        Route a user message to the active agent with streaming support.
        
        Processes @ file references and adds them to the agent's context.
        
        Args:
            message: The user message to send
            is_continuation: Whether this is a continuation message (internal use)
        """
        if not self.is_started or not self.active_agent:
            raise RuntimeError(f"Session {self.session_id} is not started or no active agent")
        
        try:
            if self.active_agent not in self.agents:
                logger.error(f"Active agent '{self.active_agent}' not found in agents dict")
                raise RuntimeError(f"Active agent '{self.active_agent}' not found")
                
            agent = self.agents[self.active_agent]
            
            # Process @ references in the message
            context_items = self.context_manager.process_message_references(
                self.active_agent, 
                message
            )
            
            # If we added context items, notify the client
            if context_items:
                await self.send_notification("context.updated", {
                    "agent_id": self.active_agent,
                    "items_added": len(context_items),
                    "context_summary": self.context_manager.get_context_summary(self.active_agent)
                })
                
                # Add file contents to the message for the agent
                # This ensures the agent sees the actual content, not just the reference
                enriched_message = message
                for item in context_items:
                    file_ref = f"@{item.path}"
                    if item.line_range:
                        file_ref += f":{item.line_range[0]}-{item.line_range[1]}"
                    
                    # Replace the reference with the actual content
                    content_block = f"\n\n[Content of {file_ref}]:\n```\n{item.content}\n```\n"
                    enriched_message = enriched_message.replace(file_ref, content_block)
                
                message = enriched_message
            
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
            
            # Defensive: ensure result is a dict
            if not isinstance(result, dict):
                logger.error(f"Unexpected result type from agent.process_message: {type(result)}")
                result = {
                    'response': str(result) if result else None,
                    'finish_reason': 'error',
                    'error': f'Unexpected result type: {type(result)}'
                }
            
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
            
            # Debug logging to understand the result type
            logger.debug(f"Result type: {type(result)}, value: {result}")
            
            # Ensure result is a dict for continuation logic
            if not isinstance(result, dict):
                logger.warning(f"Unexpected result type from agent.process_message: {type(result)}")
                # Convert to dict format if needed
                result = {'response': str(result) if result else None}
            
            # Reset continuation depth if this is not a continuation and we got a non-tool response
            if not is_continuation and (not result.get('tool_calls') or result.get('error')):
                self._continuation_depth = 0
                logger.debug("Reset continuation depth to 0")
            
            # Check if continuation is needed (like old delegate system)
            try:
                should_continue = await self._should_continue_after_tools(result, message)
            except Exception as e:
                logger.error(f"Error in _should_continue_after_tools: {e}", exc_info=True)
                should_continue = False
            
            if should_continue:
                # Extract tool names for context-aware continuation
                tool_calls = result.get('tool_calls', [])
                tool_names = [tc.get('function', {}).get('name', '') for tc in tool_calls]
                # Check continuation depth to prevent infinite loops
                if self._continuation_depth >= self._max_continuation_depth:
                    logger.warning(f"Hit max continuation depth ({self._max_continuation_depth}), stopping continuation")
                    # Reset for next interaction
                    self._continuation_depth = 0
                else:
                    # Increment continuation depth
                    self._continuation_depth += 1
                    logger.info(f"Auto-continuing after tool execution for agent {self.active_agent} (depth: {self._continuation_depth})")
                    
                    # Give a brief pause to let UI update
                    await asyncio.sleep(0.5)
                    
                    # Get continuation message from agent or use default
                    if self.active_agent and self.active_agent in self.agents:
                        agent = self.agents[self.active_agent]
                        if hasattr(agent, 'get_continuation_message'):
                            continuation_msg = agent.get_continuation_message(tool_names, message)
                        else:
                            continuation_msg = "Please continue with the next step."
                    else:
                        continuation_msg = "Please continue with the next step."
                    
                    logger.info(f"Sending continuation message: {continuation_msg}")
                    continuation_result = await self.send_user_message(continuation_msg, is_continuation=True)
                    
                    # Ensure continuation_result is also a dict
                    if not isinstance(continuation_result, dict):
                        logger.warning(f"Unexpected continuation result type: {type(continuation_result)}")
                        continuation_result = {'response': str(continuation_result) if continuation_result else None}
                    
                    # Merge results for the original caller
                    if isinstance(result, dict) and isinstance(continuation_result, dict):
                        # Append continuation response
                        if result.get('response') and continuation_result.get('response'):
                            result['response'] += "\n\n" + continuation_result['response']
                        # Merge tool calls
                        if continuation_result.get('tool_calls'):
                            if result.get('tool_calls'):
                                result['tool_calls'].extend(continuation_result['tool_calls'])
                            else:
                                result['tool_calls'] = continuation_result['tool_calls']
            
            # Reset continuation depth if we're done with continuations
            if not is_continuation and self._continuation_depth > 0:
                logger.debug(f"Resetting continuation depth from {self._continuation_depth} to 0")
                self._continuation_depth = 0
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message to agent '{self.active_agent}' in session {self.session_id}: {e}", exc_info=True)
            # Reset continuation depth on error
            if self._continuation_depth > 0:
                logger.debug("Resetting continuation depth due to error")
                self._continuation_depth = 0
            raise
    
    async def _agent_introduction(self):
        """
        Have the active agent introduce itself to the user.
        This helps verify the system prompt is working correctly.
        """
        if not self.active_agent or self.active_agent not in self.agents:
            return
        
        # Skip if agent has already introduced itself
        if self.active_agent in self.introduced_agents:
            return
        
        try:
            # Send a simple introduction request
            introduction_prompt = "Please introduce yourself briefly, mentioning your name and what you help with."
            
            # Create streaming callback for introduction
            async def send_intro_chunk(chunk: str):
                """Send introduction chunk to the client"""
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
                except Exception as e:
                    logger.error(f"Error sending introduction chunk: {e}")
            
            # Get the agent to introduce itself without storing in context
            agent = self.agents[self.active_agent]
            
            # Process introduction without storing messages
            await agent.process_message(
                introduction_prompt, 
                on_stream_chunk=send_intro_chunk,
                store_messages=False  # Don't store introduction in context
            )
            
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
            
            logger.info(f"Agent '{self.active_agent}' introduced itself")
            
        except Exception as e:
            logger.error(f"Failed to get agent introduction: {e}")
            # Don't raise - introduction is nice to have but not critical
    
    async def get_state(self) -> Dict[str, Any]:
        """
        Get the current state of the session for persistence.
        """
        state = {
            "session_id": self.session_id,
            "is_started": self.is_started,
            "active_agent": self.active_agent,
            "introduced_agents": list(self.introduced_agents),
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
        self.introduced_agents = set(state.get("introduced_agents", []))
        
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
    
    async def _should_continue_after_tools(self, result: Any, original_message: str) -> bool:
        """
        Determine if we should automatically continue after tool execution.
        This mimics the old delegate system's behavior.
        
        Args:
            result: The result from agent.process_message
            original_message: The original user message
            
        Returns:
            True if continuation is needed, False otherwise
        """
        # Only continue if we have a dict result with tool calls
        if not isinstance(result, dict) or not result.get('tool_calls'):
            return False
        
        # Check if model supports multi-tool
        from ai_whisperer.model_capabilities import supports_multi_tool
        
        # Get model name from active agent or config
        model_name = None
        if self.active_agent and self.active_agent in self.agents:
            agent = self.agents[self.active_agent]
            model_name = agent.config.model_name
        
        if not model_name:
            # Fallback to config
            model_name = self.config.get('openrouter', {}).get('model', 'google/gemini-2.5-flash-preview')
        
        model_supports_multi_tool = supports_multi_tool(model_name)
        logger.debug(f"Model {model_name} multi-tool support: {model_supports_multi_tool}")
        
        if model_supports_multi_tool:
            # Multi-tool models handle everything in one go
            return False
        
        # Single-tool model continuation logic
        tool_calls = result.get('tool_calls', [])
        if not tool_calls:
            return False
        
        # Get the tool that was called
        tool_names = [tc.get('function', {}).get('name', '') for tc in tool_calls]
        
        # Check if agent has custom continuation logic
        if self.active_agent and self.active_agent in self.agents:
            agent = self.agents[self.active_agent]
            if hasattr(agent, 'should_continue_after_tools'):
                return agent.should_continue_after_tools(result, original_message)
        
        continuation_phrases = [
            'let me', 'now i', "i'll", 'next', 'then i',
            'following that', 'after that'
        ]
        
        # If the AI's response suggests it plans to do more
        if any(phrase in response_text for phrase in continuation_phrases):
            # But it only did one tool call, it probably needs continuation
            if len(tool_calls) == 1:
                return True
        
        return False
    
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
    
    async def get_agent_context(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get context items for an agent.
        
        Args:
            agent_id: Agent ID, uses active agent if not provided
            
        Returns:
            Dictionary with context items and summary
        """
        if agent_id is None:
            agent_id = self.active_agent
        
        if not agent_id:
            return {"items": [], "summary": {}}
        
        items = self.context_manager.get_agent_context(agent_id)
        summary = self.context_manager.get_context_summary(agent_id)
        
        return {
            "agent_id": agent_id,
            "items": [item.to_dict() for item in items],
            "summary": summary
        }
    
    async def refresh_context(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Refresh stale context items for an agent.
        
        Args:
            agent_id: Agent ID, uses active agent if not provided
            
        Returns:
            Dictionary with refreshed items
        """
        if agent_id is None:
            agent_id = self.active_agent
        
        if not agent_id:
            return {"refreshed": 0, "items": []}
        
        refreshed_items = self.context_manager.refresh_stale_items(agent_id)
        
        # Notify client if items were refreshed
        if refreshed_items:
            await self.send_notification("context.refreshed", {
                "agent_id": agent_id,
                "refreshed_count": len(refreshed_items),
                "context_summary": self.context_manager.get_context_summary(agent_id)
            })
        
        return {
            "agent_id": agent_id,
            "refreshed": len(refreshed_items),
            "items": [item.to_dict() for item in refreshed_items]
        }


class StatelessSessionManager:
    """
    Manages multiple stateless interactive sessions for WebSocket connections.
    """
    
    def __init__(self, config: dict, agent_registry=None, prompt_system=None):
        """
        Initialize the session manager.
        
        Args:
            config: Global configuration dictionary
            agent_registry: Optional AgentRegistry instance
            prompt_system: Optional PromptSystem instance
        """
        self.config = config
        self.agent_registry = agent_registry
        self.prompt_system = prompt_system
        self.sessions: Dict[str, StatelessInteractiveSession] = {}
        self.websocket_sessions: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()
        
        # Register tools with the tool registry
        self._register_tools()
        
        # Load persisted sessions
        self._load_sessions()
    
    def _register_tools(self):
        """Register tools with the ToolRegistry (copied from plan_runner.py)"""
        from ai_whisperer.tools.tool_registry import get_tool_registry
        from ai_whisperer.tools.read_file_tool import ReadFileTool
        from ai_whisperer.tools.write_file_tool import WriteFileTool
        from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
        from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
        from ai_whisperer.tools.search_files_tool import SearchFilesTool
        from ai_whisperer.tools.get_file_content_tool import GetFileContentTool
        from ai_whisperer.path_management import PathManager
        
        tool_registry = get_tool_registry()
        
        # Register file operation tools
        tool_registry.register_tool(ReadFileTool())
        tool_registry.register_tool(WriteFileTool())
        tool_registry.register_tool(ExecuteCommandTool())
        
        # Register workspace browsing tools
        tool_registry.register_tool(ListDirectoryTool())
        tool_registry.register_tool(SearchFilesTool())
        tool_registry.register_tool(GetFileContentTool())
        
        # Register advanced analysis tools
        from ai_whisperer.tools.find_pattern_tool import FindPatternTool
        from ai_whisperer.tools.workspace_stats_tool import WorkspaceStatsTool
        
        # These tools need PathManager instance
        path_manager = PathManager()
        tool_registry.register_tool(FindPatternTool(path_manager))
        tool_registry.register_tool(WorkspaceStatsTool(path_manager))
        
        # Register RFC management tools
        from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
        from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
        from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
        from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
        from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
        
        tool_registry.register_tool(CreateRFCTool())
        tool_registry.register_tool(ReadRFCTool())
        tool_registry.register_tool(ListRFCsTool())
        tool_registry.register_tool(UpdateRFCTool())
        tool_registry.register_tool(MoveRFCTool())
        
        # Register codebase analysis tools
        from ai_whisperer.tools.analyze_languages_tool import AnalyzeLanguagesTool
        from ai_whisperer.tools.find_similar_code_tool import FindSimilarCodeTool
        from ai_whisperer.tools.get_project_structure_tool import GetProjectStructureTool
        
        tool_registry.register_tool(AnalyzeLanguagesTool())
        tool_registry.register_tool(FindSimilarCodeTool())
        tool_registry.register_tool(GetProjectStructureTool())
        
        # Register web research tools
        from ai_whisperer.tools.web_search_tool import WebSearchTool
        from ai_whisperer.tools.fetch_url_tool import FetchURLTool
        
        tool_registry.register_tool(WebSearchTool())
        tool_registry.register_tool(FetchURLTool())
        
        logger.info(f"Registered {len(tool_registry.get_all_tools())} tools with ToolRegistry")
        
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
    
    async def create_session(self, websocket: WebSocket, project_path: Optional[str] = None) -> str:
        """
        Create a new session for a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            project_path: Optional path to the project workspace
            
        Returns:
            The session ID
        """
        async with self._lock:
            session_id = str(uuid.uuid4())
            session = StatelessInteractiveSession(
                session_id, 
                websocket, 
                self.config, 
                self.agent_registry, 
                self.prompt_system,
                project_path=project_path
            )
            
            self.sessions[session_id] = session
            self.websocket_sessions[websocket] = session_id
            
            logger.info(f"Created session {session_id} for WebSocket connection with project: {project_path}")
            
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