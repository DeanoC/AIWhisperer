"""
Stateless Session Manager using the refactored agent architecture.
This replaces the legacy delegate-based system with direct streaming support.
"""

import asyncio
import logging
import uuid
import json
import re
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime

from fastapi import WebSocket
from ai_whisperer.services.agents.stateless import StatelessAgent
from ai_whisperer.services.agents.config import AgentConfig
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.services.execution.ai_loop import StatelessAILoop
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.ai.openrouter import OpenRouterAIService
from ai_whisperer.services.agents.ai_loop_manager import AILoopManager
from ai_whisperer.services.execution.context import ContextManager
from ai_whisperer.context.context_manager import AgentContextManager
from ai_whisperer.utils.path import PathManager
from .message_models import AIMessageChunkNotification, ContinuationProgressNotification
from .debbie_observer import get_observer
from .agent_switch_handler import AgentSwitchHandler

logger = logging.getLogger(__name__)


class StatelessInteractiveSession:
    """
    Interactive session using StatelessAgent architecture.
    Supports direct streaming without delegates.
    """
    
    def __init__(self, session_id: str, websocket: WebSocket, config: dict, agent_registry=None, prompt_system=None, project_path: Optional[str] = None, observer=None):
        """
        Initialize a stateless interactive session.
        
        Args:
            session_id: Unique identifier for this session
            websocket: WebSocket connection for this session
            config: Configuration dictionary for AI service
            agent_registry: Optional AgentRegistry instance
            prompt_system: Optional PromptSystem instance
            project_path: Optional path to the project workspace
            observer: Optional Debbie observer for monitoring
        """
        self.session_id = session_id
        self.websocket = websocket
        self.config = config
        self.observer = observer
        self.agent_registry = agent_registry
        self.prompt_system = prompt_system
        self.project_path = project_path
        
        # Agent management
        self.agents: Dict[str, StatelessAgent] = {}
        self.active_agent: Optional[str] = None
        self.introduced_agents: set = set()  # Track which agents have introduced themselves
        
        # AI Loop management - each agent gets its own AI loop
        self.ai_loop_manager = AILoopManager(default_config=config)
        
        # Continuation tracking
        self._continuation_depth = 0  # Track continuation depth to prevent loops
        self._max_continuation_depth = 3  # Default maximum continuation depth
        self._agent_max_depths = {}  # Store per-agent max depths
        
        # Session state
        self.is_started = False
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Initialize agent switch handler
        self.agent_switch_handler = AgentSwitchHandler(self)
        
        # Initialize context tracking
        path_manager = PathManager()
        if project_path:
            path_manager.initialize(config_values={'workspace_path': project_path})
        self.context_manager = AgentContextManager(session_id, path_manager)
        
        # Initialize Debbie observer for this session if provided
        if self.observer:
            try:
                self.observer.observe_session(session_id)
                logger.info(f"Debbie observer initialized for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Debbie observer for session {session_id}: {e}")
        else:
            logger.debug(f"No observer provided for session {session_id}")
        
        # Register tools for interactive sessions
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools needed for interactive sessions."""
        from ai_whisperer.tools.tool_registration import register_all_tools
        
        # Get PathManager instance for tools that need it
        path_manager = PathManager()
        if self.project_path:
            path_manager.initialize(config_values={'workspace_path': self.project_path})
        
        # Register all tools
        register_all_tools(path_manager)
        
        # Also register mailbox tools explicitly in case they're not in register_all_tools
        from ai_whisperer.tools.tool_registry import get_tool_registry
        from ai_whisperer.tools.send_mail_tool import SendMailTool
        from ai_whisperer.tools.check_mail_tool import CheckMailTool
        from ai_whisperer.tools.reply_mail_tool import ReplyMailTool
        from ai_whisperer.tools.switch_agent_tool import SwitchAgentTool
        
        tool_registry = get_tool_registry()
        tool_registry.register_tool(SendMailTool())
        tool_registry.register_tool(CheckMailTool())
        tool_registry.register_tool(ReplyMailTool())
        tool_registry.register_tool(SwitchAgentTool())
        
        logger.info("Registered all tools for interactive session including mailbox and agent switching tools")
    
    
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
        
        # Get or create AI loop for this agent through the manager
        ai_loop = self.ai_loop_manager.get_or_create_ai_loop(
            agent_id=agent_id,
            agent_config=config,
            fallback_config=self.config
        )
        
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
                prompt_source = "fallback"  # Track where the prompt came from
                
                if self.prompt_system and agent_info.prompt_file:
                    logger.info(f"Attempting to load prompt file: {agent_info.prompt_file}")
                    try:
                        # Try with prompt system first to get proper tool instructions
                        prompt_name = agent_info.prompt_file
                        if prompt_name.endswith('.prompt.md'):
                            prompt_name = prompt_name[:-10]  # Remove '.prompt.md'
                        elif prompt_name.endswith('.md'):
                            prompt_name = prompt_name[:-3]  # Remove '.md'
                        
                        logger.info(f"Trying to load prompt via PromptSystem with tools: agents/{prompt_name}")
                        try:
                            # Enable continuation feature for all agents
                            self.prompt_system.enable_feature('continuation_protocol')
                            
                            # Include tools for debugging agents like Debbie
                            include_tools = agent_id.lower() in ['d', 'debbie'] or 'debug' in agent_info.name.lower()
                            prompt = self.prompt_system.get_formatted_prompt("agents", prompt_name, include_tools=include_tools)
                            system_prompt = prompt
                            prompt_source = f"prompt_system:agents/{prompt_name}" + (" (with_tools)" if include_tools else "")
                            logger.info(f"✅ Successfully loaded prompt via PromptSystem for {agent_id} (tools included: {include_tools})")
                        except Exception as e1:
                            logger.warning(f"⚠️ PromptSystem failed: {e1}, trying direct file read")
                            # Try direct file read as fallback
                            from pathlib import Path
                            prompt_file = Path("prompts") / "agents" / agent_info.prompt_file
                            if prompt_file.exists():
                                with open(prompt_file, 'r', encoding='utf-8') as f:
                                    base_prompt = f.read()
                                
                                # Add tool instructions manually for debugging agents
                                if agent_id.lower() in ['d', 'debbie'] or 'debug' in agent_info.name.lower():
                                    try:
                                        from ai_whisperer.tools.tool_registry import get_tool_registry
                                        tool_registry = get_tool_registry()
                                        tool_instructions = tool_registry.get_all_ai_prompt_instructions()
                                        if tool_instructions:
                                            system_prompt = base_prompt + "\n\n## AVAILABLE TOOLS\n" + tool_instructions
                                            prompt_source = f"direct_file:{prompt_file} (with_tools)"
                                            logger.info(f"✅ Added tool instructions to direct file prompt for {agent_id}")
                                        else:
                                            system_prompt = base_prompt
                                            prompt_source = f"direct_file:{prompt_file} (no_tools)"
                                            logger.warning(f"⚠️ No tool instructions available for {agent_id}")
                                    except Exception as e2:
                                        logger.warning(f"⚠️ Failed to add tool instructions: {e2}")
                                        system_prompt = base_prompt
                                        prompt_source = f"direct_file:{prompt_file} (tools_failed)"
                                else:
                                    system_prompt = base_prompt
                                    prompt_source = f"direct_file:{prompt_file}"
                                
                                logger.info(f"✅ Successfully loaded prompt via direct file read for {agent_id}: {prompt_file}")
                            else:
                                logger.warning(f"❌ Prompt file not found: {prompt_file}")
                                logger.warning(f"❌ FALLBACK ACTIVATED: Using basic fallback prompt for {agent_info.name}")
                                prompt_source = "basic_fallback"
                                # Keep the fallback prompt
                    except Exception as e:
                        logger.error(f"❌ Failed to load prompt for agent {agent_id}: {e}")
                        logger.error(f"❌ FALLBACK ACTIVATED: Using basic fallback prompt for {agent_info.name}")
                        prompt_source = "error_fallback"
                else:
                    logger.warning(f"⚠️ No prompt system or prompt file configured for {agent_id}, using basic fallback")
                    prompt_source = "no_config_fallback"
                
                # Create agent config with AI settings if available
                agent_config = None
                if agent_info.ai_config:
                    # Create AgentConfig with agent-specific AI settings
                    openrouter_config = self.config.get("openrouter", {})
                    agent_config = AgentConfig(
                        name=agent_info.name,
                        description=agent_info.description,
                        system_prompt=system_prompt,
                        model_name=agent_info.ai_config.get("model", openrouter_config.get("model", "openai/gpt-3.5-turbo")),
                        provider=agent_info.ai_config.get("provider", "openrouter"),
                        api_settings={
                            "api_key": openrouter_config.get("api_key"),
                            **agent_info.ai_config.get("api_settings", {})
                        },
                        generation_params={
                            **openrouter_config.get("params", {}),
                            **agent_info.ai_config.get("generation_params", {})
                        },
                        tool_permissions=[],
                        tool_limits={},
                        context_settings=agent_info.ai_config.get("context_settings", {"max_context_messages": 50})
                    )
                    logger.info(f"Created agent config with custom AI settings: model={agent_config.model_name}")
                
                # Create the agent with the loaded prompt and registry info
                logger.info(f"📝 Agent {agent_id} ({agent_info.name}) prompt loaded from: {prompt_source}")
                logger.info(f"About to create agent with prompt: {system_prompt[:200]}...")
                await self._create_agent_internal(agent_id, system_prompt, config=agent_config, agent_registry_info=agent_info)
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
            
            # Notify observer about agent switch
            if old_agent and self.observer:
                self.observer.on_agent_switch(self.session_id, old_agent, agent_id)
            
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
        logger.debug(f"[send_user_message] Processing message for session {self.session_id}")
        
        if not self.is_started or not self.active_agent:
            raise RuntimeError(f"Session {self.session_id} is not started or no active agent")
        
        try:
            if self.active_agent not in self.agents:
                logger.error(f"Active agent '{self.active_agent}' not found in agents dict")
                raise RuntimeError(f"Active agent '{self.active_agent}' not found")
                
            agent = self.agents[self.active_agent]
            
            # Reset continuation tracking for new conversations
            if not is_continuation:
                self._continuation_depth = 0
                if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                    agent.continuation_strategy.reset()
                    logger.debug("Reset continuation strategy for new conversation")
            
            # Check for commands before processing
            if message.strip().startswith('/'):
                command_result = await self._handle_command(message.strip())
                if command_result:
                    # Command was handled, return early
                    return
            
            # Notify observer that message processing is starting
            if self.observer:
                self.observer.on_message_start(self.session_id, message)
            
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
            
            # Optimize message for model-specific behavior
            model_name = agent.config.model_name if hasattr(agent.config, 'model_name') else \
                        self.config.get('openrouter', {}).get('model', '')
            
            if model_name:
                from ai_whisperer.extensions.agents.prompt_optimizer import optimize_user_message
                optimized_message = optimize_user_message(message, model_name, self.active_agent)
                if optimized_message != message:
                    logger.debug(f"Optimized user message for {model_name}")
                    message = optimized_message
                
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
                    # Check if WebSocket is still connected
                    if self.websocket is None:
                        logger.warning(f"WebSocket disconnected for session {self.session_id}, skipping chunk")
                        return
                        
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
                    # If we get a RuntimeError about closed connection, clear the WebSocket
                    if "closed" in str(e).lower():
                        self.websocket = None
            
            # Check if we should use structured output for plan generation
            kwargs = {}
            if self._should_use_structured_output_for_plan(agent, message):
                kwargs['response_format'] = self._get_plan_generation_schema()
                logger.info("Enabling structured output for plan generation")
            
            # Process message with streaming
            logger.debug(f"[send_user_message] Calling agent.process_message")
            result = await agent.process_message(message, on_stream_chunk=send_chunk, **kwargs)
            logger.debug(f"[send_user_message] Agent processing completed")
            
            # Defensive: ensure result is a dict
            if not isinstance(result, dict):
                logger.error(f"Unexpected result type from agent.process_message: {type(result)}")
                result = {
                    'response': str(result) if result else None,
                    'finish_reason': 'error',
                    'error': f'Unexpected result type: {type(result)}'
                }
            
            # Send final notification if WebSocket is still connected
            if self.websocket is not None:
                try:
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
                except Exception as e:
                    logger.error(f"Error sending final notification: {e}")
                    if "closed" in str(e).lower():
                        self.websocket = None
            
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
                
                # Also reset continuation strategy if present
                if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                    agent.continuation_strategy.reset()
                    logger.debug("Reset continuation strategy")
            
            # Note: Assistant message is already stored by the AI loop, no need to store again
            
            # Check if agent switching is needed based on tool results
            if result.get('tool_calls') and hasattr(self, 'agent_switch_handler'):
                switch_occurred, additional_response = await self.agent_switch_handler.handle_tool_results(
                    result.get('tool_calls', []),
                    result.get('response', '')
                )
                
                if switch_occurred and additional_response:
                    # Append the additional response from agent switching
                    if result.get('response'):
                        result['response'] += additional_response
                    else:
                        result['response'] = additional_response
                    logger.info("Agent switch completed, appended response")
            
            # Check if continuation is needed (like old delegate system)
            try:
                logger.info(f"🔄 CHECKING CONTINUATION: result has {len(result.get('tool_calls', []))} tool calls")
                should_continue = await self._should_continue_after_tools(result, message)
                logger.info(f"🔄 CONTINUATION DECISION: {should_continue}")
            except Exception as e:
                logger.error(f"Error in _should_continue_after_tools: {e}", exc_info=True)
                should_continue = False
            
            if should_continue:
                # Extract tool names for context-aware continuation
                tool_calls = result.get('tool_calls', [])
                tool_names = [tc.get('function', {}).get('name', '') for tc in tool_calls]
                # Get max depth for this agent
                agent_max_depth = self._max_continuation_depth  # Default
                if self.active_agent and self.active_agent in self.agents:
                    agent = self.agents[self.active_agent]
                    if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                        # Use agent's configured max iterations
                        agent_max_depth = agent.continuation_strategy.max_iterations
                
                # Check continuation depth to prevent infinite loops
                if self._continuation_depth >= agent_max_depth:
                    logger.warning(f"Hit max continuation depth ({agent_max_depth}) for agent {self.active_agent}, stopping continuation")
                    # Reset for next interaction
                    self._continuation_depth = 0
                else:
                    # Increment continuation depth
                    self._continuation_depth += 1
                    logger.info(f"Auto-continuing after tool execution for agent {self.active_agent} (depth: {self._continuation_depth})")
                    
                    # Give a brief pause to let UI update
                    await asyncio.sleep(0.5)
                    
                    # Get continuation message from agent
                    continuation_msg = "Please continue with the next step."
                    if self.active_agent and self.active_agent in self.agents:
                        agent = self.agents[self.active_agent]
                        
                        # Check if agent has continuation strategy for progress tracking
                        if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                            # Get progress information
                            progress = agent.continuation_strategy.get_progress(agent.context._context)
                            
                            # Send progress notification using the new method
                            await self._send_progress_notification(progress, tool_names)
                            
                            # Use continuation strategy's message
                            continuation_msg = agent.continuation_strategy.get_continuation_message(tool_names, message)
                        elif hasattr(agent, 'get_continuation_message'):
                            # Fallback to old method
                            continuation_msg = agent.get_continuation_message(tool_names, message)
                    
                    logger.info(f"🔄 SENDING CONTINUATION MESSAGE: {continuation_msg}")
                    logger.debug(f"🔄 BEFORE CONTINUATION - Agent context has {len(self.agents[self.active_agent].context._messages)} messages")
                    continuation_result = await self.send_user_message(continuation_msg, is_continuation=True)
                    logger.debug(f"🔄 AFTER CONTINUATION - Agent context has {len(self.agents[self.active_agent].context._messages)} messages")
                    
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
            
            # Notify observer that message processing completed
            if self.observer:
                self.observer.on_message_complete(self.session_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to send message to agent '{self.active_agent}' in session {self.session_id}: {e}", exc_info=True)
            
            # Notify observer about the error
            if self.observer:
                self.observer.on_error(self.session_id, e)
            
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
            
            # Send final notification if WebSocket is still connected
            if self.websocket is not None:
                try:
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
                except Exception as e:
                    logger.error(f"Error sending final notification: {e}")
                    if "closed" in str(e).lower():
                        self.websocket = None
            
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
    
    async def save_session(self, filepath: Optional[str] = None) -> str:
        """
        Save the current session state to a file.
        
        Args:
            filepath: Optional custom filepath. If not provided, saves to .WHISPER/sessions/
            
        Returns:
            Path where the session was saved
        """
        from pathlib import Path
        import json
        
        # Get session state
        state = await self.get_state()
        
        # Add save metadata
        state["saved_at"] = datetime.now().isoformat()
        state["version"] = "1.0"
        
        # Determine filepath
        if not filepath:
            sessions_dir = Path(".WHISPER/sessions")
            sessions_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = sessions_dir / f"{self.session_id}_{timestamp}.json"
        else:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"Saved session {self.session_id} to {filepath}")
        
        # Send notification to client
        await self.send_notification("session.saved", {
            "session_id": self.session_id,
            "filepath": str(filepath),
            "saved_at": state["saved_at"]
        })
        
        return str(filepath)
    
    async def load_session(self, filepath: str) -> None:
        """
        Load a session state from a file.
        
        Args:
            filepath: Path to the session file
        """
        from pathlib import Path
        import json
        
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")
        
        # Load state from file
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        # Restore the state
        await self.restore_state(state)
        
        logger.info(f"Loaded session from {filepath}")
        
        # Send notification to client
        await self.send_notification("session.loaded", {
            "session_id": self.session_id,
            "filepath": str(filepath),
            "saved_at": state.get("saved_at", "unknown"),
            "active_agent": self.active_agent,
            "agent_count": len(self.agents)
        })
    
    async def _send_progress_notification(self, progress: dict, tool_names: list = None) -> None:
        """
        Send a progress notification via WebSocket.
        
        Args:
            progress: Progress information from continuation strategy
            tool_names: List of tool names being executed
        """
        try:
            # Get agent-specific max depth
            agent_max_depth = self._max_continuation_depth
            if self.active_agent and self.active_agent in self.agents:
                agent = self.agents[self.active_agent]
                if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                    agent_max_depth = agent.continuation_strategy.max_iterations
            
            notification_data = {
                "sessionId": self.session_id,
                "agent_id": self.active_agent,
                "iteration": self._continuation_depth,
                "max_iterations": agent_max_depth,
                "progress": progress
            }
            
            if tool_names:
                notification_data["current_tools"] = tool_names
                
            # Add timestamp
            from datetime import datetime
            notification_data["timestamp"] = datetime.now().isoformat()
            
            await self.send_notification("continuation.progress", notification_data)
            logger.debug(f"Sent continuation progress notification: iteration {self._continuation_depth}/{self._max_continuation_depth}")
            
        except Exception as e:
            logger.error(f"Failed to send progress notification: {e}")
            # Don't fail the continuation on notification error
    
    async def _should_continue_after_tools(self, result: Any, original_message: str) -> bool:
        """
        Determine if we should automatically continue after tool execution.
        Uses the agent's ContinuationStrategy if available.
        
        Args:
            result: The result from agent.process_message
            original_message: The original user message
            
        Returns:
            True if continuation is needed, False otherwise
        """
        # Get model name from active agent or config
        model_name = None
        if self.active_agent and self.active_agent in self.agents:
            agent = self.agents[self.active_agent]
            model_name = agent.config.model_name
        
        if not model_name:
            # Fallback to config
            model_name = self.config.get('openrouter', {}).get('model', 'google/gemini-2.5-flash-preview')
        
        # Apply model-specific optimizations first
        if isinstance(result, dict):
            result = self._apply_model_optimization(result, model_name)
        
        # Check if agent has continuation strategy FIRST
        # This allows agents to explicitly signal continuation even on single-tool models
        if self.active_agent and self.active_agent in self.agents:
            agent = self.agents[self.active_agent]
            if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                # Use the new ContinuationStrategy
                should_continue = agent.continuation_strategy.should_continue(result, original_message)
                logger.info(f"🔄 CONTINUATION STRATEGY DECISION: {should_continue}")
                return should_continue
        
        # Fallback: Only continue if we have a dict result with tool calls
        if not isinstance(result, dict) or not result.get('tool_calls'):
            return False
        
        # Check if model supports multi-tool
        from ai_whisperer.model_capabilities import supports_multi_tool
        
        model_supports_multi_tool = supports_multi_tool(model_name)
        logger.info(f"🔄 MODEL CAPABILITY CHECK: {model_name} multi-tool support: {model_supports_multi_tool}")
        
        if not model_supports_multi_tool:
            # Single-tool models should NOT continue after using their one tool (unless using continuation strategy)
            logger.info(f"🔄 SINGLE-TOOL MODEL: {model_name} - no continuation after tool use (no continuation strategy)")
            return False
        
        # Single-tool model continuation logic
        tool_calls = result.get('tool_calls', [])
        if not tool_calls:
            return False
        
        # Get the tool that was called
        tool_names = [tc.get('function', {}).get('name', '') for tc in tool_calls]
        
        # Check if agent has custom continuation logic (old method)
        if self.active_agent and self.active_agent in self.agents:
            agent = self.agents[self.active_agent]
            if hasattr(agent, 'should_continue_after_tools'):
                return agent.should_continue_after_tools(result, original_message)
        
        # Get the AI's response text from the result
        response_text = result.get('response', '').lower() if result.get('response') else ''
        
        continuation_phrases = [
            'let me', 'now i', "i'll", 'next', 'then i',
            'following that', 'after that'
        ]
        
        # If the AI's response suggests it plans to do more
        if response_text and any(phrase in response_text for phrase in continuation_phrases):
            # But it only did one tool call, it probably needs continuation
            if len(tool_calls) == 1:
                return True
        
        return False
    
    def _apply_model_optimization(self, response: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """Apply model-specific optimizations to improve continuation behavior"""
        from ai_whisperer.model_capabilities import get_model_capabilities
        
        capabilities = get_model_capabilities(model_name)
        
        # For single-tool models, enhance continuation signals
        if not capabilities.get("multi_tool"):
            response_text = response.get('response', '')
            if response_text and 'tool_calls' in response:
                # Add explicit continuation hints to response
                enhanced_patterns = [
                    "I'll continue with the next step",
                    "Now proceeding to the next operation",
                    "Moving on to step"
                ]
                
                # Check if response already has continuation patterns
                has_pattern = any(pattern.lower() in response_text.lower() 
                                for pattern in enhanced_patterns)
                
                if not has_pattern and len(response.get('tool_calls', [])) == 1:
                    # Enhance response with continuation hint
                    logger.debug(f"Enhancing single-tool model response for better continuation")
                    response['_continuation_optimized'] = True
        
        # For multi-tool models, check if batching was suboptimal
        elif capabilities.get("multi_tool") and response.get('tool_calls'):
            tool_count = len(response.get('tool_calls', []))
            if tool_count == 1:
                # Log for monitoring - might indicate prompt could be optimized
                logger.debug(f"Multi-tool model {model_name} used only 1 tool - consider prompt optimization")
                response['_batching_opportunity'] = True
        
        return response
    
    def _get_optimal_continuation_config(self, agent_type: str, model_name: str) -> Dict[str, Any]:
        """Get optimized continuation configuration for agent/model combination"""
        from ai_whisperer.model_capabilities import get_model_capabilities
        
        # Start with agent's base config
        base_config = {}
        if agent_type and agent_type in self.agents:
            agent = self.agents[agent_type]
            if hasattr(agent, 'continuation_strategy') and agent.continuation_strategy:
                base_config = {
                    'max_iterations': agent.continuation_strategy.max_iterations,
                    'timeout': agent.continuation_strategy.timeout,
                    'require_explicit_signal': agent.continuation_strategy.require_explicit_signal
                }
        
        # Apply model-specific adjustments
        capabilities = get_model_capabilities(model_name)
        
        if capabilities.get("multi_tool"):
            # Multi-tool models need fewer iterations
            base_config['max_iterations'] = min(base_config.get('max_iterations', 5), 5)
            # Can use explicit signals effectively
            base_config['require_explicit_signal'] = True
        else:
            # Single-tool models need more iterations
            base_config['max_iterations'] = base_config.get('max_iterations', 10)
            # Increase timeout for sequential operations
            base_config['timeout'] = int(base_config.get('timeout', 300) * 1.5)
            # Don't require explicit signals
            base_config['require_explicit_signal'] = False
            
        logger.debug(f"Optimized continuation config for {agent_type}/{model_name}: {base_config}")
        return base_config
    
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
        
        # Clean up AI loops
        self.ai_loop_manager.cleanup()
        
        # Stop observing this session
        if self.observer:
            self.observer.stop_observing(self.session_id)
            logger.info(f"Stopped Debbie observer for session {self.session_id}")
        else:
            logger.debug(f"No observer to stop for session {self.session_id}")
        
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
    
    async def clear_agent_context(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear all context items for an agent.
        
        Args:
            agent_id: Agent ID, uses active agent if not provided
            
        Returns:
            Dictionary with clear operation results
        """
        if agent_id is None:
            agent_id = self.active_agent
        
        if not agent_id:
            return {"cleared": False, "error": "No active agent"}
        
        # Get current context size before clearing
        current_context = self.context_manager.get_agent_context(agent_id)
        items_count = len(current_context)
        
        # Clear the context
        self.context_manager.clear_agent_context(agent_id)
        
        # Also clear the agent's internal context if it has one
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            if hasattr(agent, 'context') and hasattr(agent.context, 'clear'):
                agent.context.clear()
        
        # Notify client
        await self.send_notification("context.cleared", {
            "agent_id": agent_id,
            "items_cleared": items_count
        })
        
        logger.info(f"Cleared {items_count} context items for agent {agent_id}")
        
        return {
            "agent_id": agent_id,
            "cleared": True,
            "items_cleared": items_count
        }
    
    async def _handle_command(self, message: str) -> bool:
        """Handle slash commands.
        
        Args:
            message: The message starting with /
            
        Returns:
            True if command was handled, False otherwise
        """
        parts = message.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "/clear":
            # Handle /clear command
            target_agent = None
            if args:
                # Check if agent name was specified
                if args in self.agents:
                    target_agent = args
                elif args == "all":
                    # Clear all agents
                    total_cleared = 0
                    for agent_id in list(self.agents.keys()):
                        result = await self.clear_agent_context(agent_id)
                        total_cleared += result.get("items_cleared", 0)
                    
                    # Send response to user
                    await self._send_system_message(
                        f"Cleared context for all agents ({total_cleared} items total)"
                    )
                    return True
                else:
                    await self._send_system_message(
                        f"Unknown agent: {args}. Available agents: {', '.join(self.agents.keys())}"
                    )
                    return True
            
            # Clear specific agent or current agent
            result = await self.clear_agent_context(target_agent)
            
            if result.get("cleared"):
                agent_name = target_agent or self.active_agent
                await self._send_system_message(
                    f"Cleared {result['items_cleared']} context items for agent {agent_name}"
                )
            else:
                await self._send_system_message(
                    f"Failed to clear context: {result.get('error', 'Unknown error')}"
                )
            
            return True
        
        elif command == "/save":
            # Handle /save command
            try:
                filepath = await self.save_session(args if args else None)
                await self._send_system_message(f"Session saved to: {filepath}")
            except Exception as e:
                await self._send_system_message(f"Failed to save session: {e}")
            return True
        
        elif command == "/load":
            # Handle /load command
            if not args:
                await self._send_system_message("Please specify a file to load: /load <filepath>")
                return True
            
            try:
                await self.load_session(args)
                await self._send_system_message(
                    f"Session loaded successfully. Active agent: {self.active_agent}, "
                    f"Total agents: {len(self.agents)}"
                )
            except FileNotFoundError:
                await self._send_system_message(f"Session file not found: {args}")
            except Exception as e:
                await self._send_system_message(f"Failed to load session: {e}")
            return True
        
        elif command == "/debug":
            # Handle /debug command for testing
            if not args:
                # Show debug status
                if self.prompt_system:
                    debug_options = self.prompt_system.get_debug_options()
                    if debug_options:
                        await self._send_system_message(
                            f"Debug mode active with options: {', '.join(sorted(debug_options))}"
                        )
                    else:
                        await self._send_system_message("Debug mode is not active")
                else:
                    await self._send_system_message("Prompt system not available")
                return True
            
            # Parse debug options
            options = args.split()
            if options[0] == "off":
                # Disable all debug options
                if self.prompt_system:
                    self.prompt_system.set_debug_mode()  # All False by default
                    
                    # Regenerate the active agent's system prompt without debug options
                    if self.active_agent in self.agents:
                        agent = self.agents[self.active_agent]
                        if hasattr(agent, 'config') and hasattr(agent, 'ai_loop'):
                            try:
                                system_prompt = self.prompt_system.get_formatted_prompt(
                                    'agents',
                                    self.active_agent,
                                    include_tools=True,
                                    include_shared=True
                                )
                                # Update the agent's AI loop with new system prompt
                                agent.ai_loop.config.system_prompt = system_prompt
                                logger.info(f"Updated {self.active_agent} agent prompt without debug options")
                            except Exception as e:
                                logger.warning(f"Failed to update agent prompt: {e}")
                    
                    await self._send_system_message("Debug mode disabled")
                else:
                    await self._send_system_message("Prompt system not available")
            elif options[0] == "on":
                # Enable specific debug options
                debug_flags = {
                    'single_tool': False,
                    'verbose_progress': False,
                    'force_sequential': False,
                    'explicit_continuation': False
                }
                
                # Parse remaining options
                for opt in options[1:]:
                    if opt in debug_flags:
                        debug_flags[opt] = True
                    else:
                        await self._send_system_message(
                            f"Unknown debug option: {opt}. "
                            f"Available: {', '.join(debug_flags.keys())}"
                        )
                        return True
                
                if self.prompt_system:
                    self.prompt_system.set_debug_mode(**debug_flags)
                    enabled_opts = [k for k, v in debug_flags.items() if v]
                    
                    # Regenerate the active agent's system prompt with debug options
                    if self.active_agent in self.agents:
                        agent = self.agents[self.active_agent]
                        if hasattr(agent, 'config') and hasattr(agent, 'ai_loop'):
                            # Get the updated prompt with debug options
                            try:
                                system_prompt = self.prompt_system.get_formatted_prompt(
                                    'agents',
                                    self.active_agent,
                                    include_tools=True,
                                    include_shared=True
                                )
                                # Update the agent's AI loop with new system prompt
                                agent.ai_loop.config.system_prompt = system_prompt
                                logger.info(f"Updated {self.active_agent} agent prompt with debug options")
                            except Exception as e:
                                logger.warning(f"Failed to update agent prompt: {e}")
                    
                    if enabled_opts:
                        await self._send_system_message(
                            f"Debug mode enabled with options: {', '.join(enabled_opts)}"
                        )
                    else:
                        await self._send_system_message(
                            "Debug mode enabled with default options. "
                            "Use: /debug on single_tool verbose_progress"
                        )
                else:
                    await self._send_system_message("Prompt system not available")
            else:
                await self._send_system_message(
                    "Usage:\n"
                    "• /debug - Show current debug status\n"
                    "• /debug off - Disable debug mode\n"
                    "• /debug on [options] - Enable debug mode with options\n"
                    "  Options: single_tool, verbose_progress, force_sequential, explicit_continuation"
                )
            return True
            
        elif command == "/help":
            # Show available commands
            help_text = """Available commands:
• /clear - Clear context for current agent
• /clear <agent> - Clear context for specific agent
• /clear all - Clear context for all agents
• /save - Save current session
• /save <filepath> - Save session to specific file
• /load <filepath> - Load session from file
• /debug - Show debug status or configure debug options
• /help - Show this help message"""
            
            await self._send_system_message(help_text)
            return True
        
        # Unknown command
        return False
    
    async def _send_system_message(self, message: str):
        """Send a system message to the client.
        
        Args:
            message: The system message to send
        """
        # Send as a notification that looks like an agent message
        await self.send_notification("agent.message", {
            "agent_id": "system",
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "type": "system"
        })


    def _should_use_structured_output_for_plan(self, agent: Any, message: str) -> bool:
        """
        Determine if we should enable structured output for plan generation.
        
        Args:
            agent: The active agent
            message: The user message
            
        Returns:
            True if we should use structured output
        """
        # Check if this is Patricia agent
        if not hasattr(agent, 'config') or agent.config.name != 'patricia':
            return False
            
        # Check if the model supports structured output
        from ai_whisperer.model_capabilities import supports_structured_output
        if not supports_structured_output(agent.config.model_name):
            return False
            
        # Check if the message is likely asking for plan generation
        plan_indicators = [
            "generate a structured json plan",
            "generate a plan",
            "create a plan",
            "convert.*to.*plan",
            "plan structure required",
            "structured output enabled"
        ]
        
        message_lower = message.lower()
        return any(indicator in message_lower or re.search(indicator, message_lower) for indicator in plan_indicators)
    
    def _get_plan_generation_schema(self) -> Dict[str, Any]:
        """
        Get the plan generation schema for structured output.
        
        Returns:
            The response_format dict for plan generation
        """
        import json
        from pathlib import Path
        
        # Load the plan generation schema
        from ai_whisperer.core.config import get_schema_path
        schema_path = get_schema_path("plan_generation_schema")
        try:
            with open(schema_path) as f:
                plan_schema = json.load(f)
            
            # Remove the $schema field if present
            if "$schema" in plan_schema:
                del plan_schema["$schema"]
            
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "rfc_plan_generation",
                    "strict": False,  # Use False for complex schemas
                    "schema": plan_schema
                }
            }
        except Exception as e:
            logger.error(f"Failed to load plan generation schema: {e}")
            return None


class StatelessSessionManager:
    """
    Manages multiple stateless interactive sessions for WebSocket connections.
    """
    
    def __init__(self, config: dict, agent_registry=None, prompt_system=None, observer=None):
        """
        Initialize the session manager.
        
        Args:
            config: Global configuration dictionary
            agent_registry: Optional AgentRegistry instance
            prompt_system: Optional PromptSystem instance
            observer: Optional Debbie observer for monitoring
        """
        self.config = config
        self.agent_registry = agent_registry
        self.prompt_system = prompt_system
        self.observer = observer
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
        from ai_whisperer.utils.path import PathManager
        
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
        
        # Mailbox tools are already registered in __init__ method
        # Skip duplicate registration here
        
        # Register RFC management tools
        from ai_whisperer.tools.create_rfc_tool import CreateRFCTool
        from ai_whisperer.tools.read_rfc_tool import ReadRFCTool
        from ai_whisperer.tools.list_rfcs_tool import ListRFCsTool
        from ai_whisperer.tools.update_rfc_tool import UpdateRFCTool
        from ai_whisperer.tools.move_rfc_tool import MoveRFCTool
        from ai_whisperer.tools.delete_rfc_tool import DeleteRFCTool
        
        tool_registry.register_tool(CreateRFCTool())
        tool_registry.register_tool(ReadRFCTool())
        tool_registry.register_tool(ListRFCsTool())
        tool_registry.register_tool(UpdateRFCTool())
        tool_registry.register_tool(MoveRFCTool())
        tool_registry.register_tool(DeleteRFCTool())
        
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
        
        # Register plan management tools
        from ai_whisperer.tools.prepare_plan_from_rfc_tool import PreparePlanFromRFCTool
        from ai_whisperer.tools.save_generated_plan_tool import SaveGeneratedPlanTool
        from ai_whisperer.tools.list_plans_tool import ListPlansTool
        from ai_whisperer.tools.read_plan_tool import ReadPlanTool
        from ai_whisperer.tools.update_plan_from_rfc_tool import UpdatePlanFromRFCTool
        from ai_whisperer.tools.move_plan_tool import MovePlanTool
        from ai_whisperer.tools.delete_plan_tool import DeletePlanTool
        
        tool_registry.register_tool(PreparePlanFromRFCTool())
        tool_registry.register_tool(SaveGeneratedPlanTool())
        tool_registry.register_tool(ListPlansTool())
        tool_registry.register_tool(ReadPlanTool())
        tool_registry.register_tool(UpdatePlanFromRFCTool())
        tool_registry.register_tool(MovePlanTool())
        tool_registry.register_tool(DeletePlanTool())
        
        # Register Debbie's debugging and monitoring tools
        try:
            from ai_whisperer.tools.session_health_tool import SessionHealthTool
            from ai_whisperer.tools.session_analysis_tool import SessionAnalysisTool
            from ai_whisperer.tools.monitoring_control_tool import MonitoringControlTool
            from ai_whisperer.tools.session_inspector_tool import SessionInspectorTool
            from ai_whisperer.tools.message_injector_tool import MessageInjectorTool
            from ai_whisperer.tools.workspace_validator_tool import WorkspaceValidatorTool
            from ai_whisperer.tools.python_executor_tool import PythonExecutorTool
            from ai_whisperer.tools.script_parser_tool import ScriptParserTool
            from ai_whisperer.tools.batch_command_tool import BatchCommandTool
            from ai_whisperer.tools.ai_loop_inspector_tool import AILoopInspectorTool
            
            tool_registry.register_tool(SessionHealthTool())
            tool_registry.register_tool(SessionAnalysisTool())
            tool_registry.register_tool(MonitoringControlTool())
            tool_registry.register_tool(SessionInspectorTool())
            tool_registry.register_tool(MessageInjectorTool())
            tool_registry.register_tool(WorkspaceValidatorTool())
            tool_registry.register_tool(PythonExecutorTool())
            tool_registry.register_tool(ScriptParserTool())
            tool_registry.register_tool(BatchCommandTool(tool_registry))
            tool_registry.register_tool(AILoopInspectorTool())
            
            logger.info("Successfully registered Debbie's debugging and batch processing tools")
        except ImportError as e:
            logger.warning(f"Some debugging/batch tools not available: {e}")
        except Exception as e:
            logger.error(f"Failed to register debugging/batch tools: {e}")
        
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
                project_path=project_path,
                observer=self.observer
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