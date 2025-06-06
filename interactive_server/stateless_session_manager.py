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
from ai_whisperer.channels.integration import get_channel_integration
from ai_whisperer.core.agent_logger import get_agent_logger

logger = logging.getLogger(__name__)


def clean_malformed_json(response: str) -> str:
    """
    Clean up malformed JSON responses that may contain multiple JSON objects concatenated.
    
    Args:
        response: The potentially malformed JSON response
        
    Returns:
        A cleaned up JSON string or the original response if not JSON
    """
    if not response.strip().startswith('{'):
        return response
    
    # Try to find the first complete JSON object
    brace_count = 0
    first_json_end = -1
    
    for i, char in enumerate(response):
        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                first_json_end = i
                break
    
    if first_json_end > 0:
        # Extract just the first JSON object
        first_json = response[:first_json_end + 1]
        try:
            # Validate it's proper JSON
            json.loads(first_json)
            return first_json
        except json.JSONDecodeError:
            pass
    
    # If we can't extract clean JSON, return original
    return response


def normalize_response_to_json(response: str, is_structured: bool = False) -> Dict[str, Any]:
    """
    Normalize any AI response to a consistent JSON structure.
    
    Args:
        response: The AI response (could be JSON or plain text)
        is_structured: Whether the response is already structured JSON
        
    Returns:
        Dictionary with analysis/commentary/final structure
    """
    # Clean up potentially malformed JSON first
    if isinstance(response, str) and response.strip().startswith('{'):
        response = clean_malformed_json(response)
    
    # If already valid JSON with expected structure, return as-is
    if is_structured or (isinstance(response, str) and response.strip().startswith('{')):
        try:
            data = json.loads(response)
            if isinstance(data, dict) and all(key in data for key in ['analysis', 'commentary', 'final']):
                return data
        except json.JSONDecodeError:
            pass
    
    # Check for marker-based format
    if '[FINAL]' in response or '[ANALYSIS]' in response or '[COMMENTARY]' in response:
        analysis = ""
        commentary = ""
        final = ""
        
        # Extract sections using regex
        analysis_match = re.search(r'\[ANALYSIS\](.*?)(?=\[COMMENTARY\]|\[FINAL\]|$)', response, re.DOTALL)
        if analysis_match:
            analysis = analysis_match.group(1).strip()
            
        commentary_match = re.search(r'\[COMMENTARY\](.*?)(?=\[FINAL\]|$)', response, re.DOTALL)
        if commentary_match:
            commentary = commentary_match.group(1).strip()
            
        final_match = re.search(r'\[FINAL\](.*?)(?=$)', response, re.DOTALL)
        if final_match:
            final = final_match.group(1).strip()
        else:
            # If no FINAL marker but has other markers, remaining content is final
            # Remove all marked sections to get remaining content
            remaining = response
            if analysis_match:
                remaining = remaining.replace(analysis_match.group(0), '')
            if commentary_match:
                remaining = remaining.replace(commentary_match.group(0), '')
            remaining = remaining.strip()
            if remaining:
                final = remaining
                
        return {
            "analysis": analysis,
            "commentary": commentary,
            "final": final
        }
    
    # Plain text response - everything goes to 'final'
    return {
        "analysis": "",
        "commentary": "",
        "final": response
    }


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
        
        # Initialize channel integration
        self.channel_integration = get_channel_integration()
        
        # Initialize agent logger
        self.agent_logger = get_agent_logger()
        
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
        
        # Also register mailbox and async agent tools explicitly 
        from ai_whisperer.tools.tool_registry import get_tool_registry
        from ai_whisperer.tools.send_mail_tool import SendMailTool
        from ai_whisperer.tools.send_mail_with_switch_tool import SendMailWithSwitchTool
        from ai_whisperer.tools.check_mail_tool import CheckMailTool
        from ai_whisperer.tools.reply_mail_tool import ReplyMailTool
        from ai_whisperer.tools.switch_agent_tool import SwitchAgentTool
        from ai_whisperer.tools.agent_sleep_tool import AgentSleepTool
        from ai_whisperer.tools.agent_wake_tool import AgentWakeTool
        
        tool_registry = get_tool_registry()
        tool_registry.register_tool(SendMailTool())
        tool_registry.register_tool(SendMailWithSwitchTool())
        tool_registry.register_tool(CheckMailTool())
        tool_registry.register_tool(ReplyMailTool())
        tool_registry.register_tool(SwitchAgentTool())
        tool_registry.register_tool(AgentSleepTool())
        tool_registry.register_tool(AgentWakeTool())
        
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
        
        # Initialize agent logger for this agent
        agent_name = config.name if config else f"Agent {agent_id}"
        self.agent_logger.get_agent_logger(agent_id, agent_name)
        self.agent_logger.log_agent_action(agent_id, "Agent Created", {
            "model": config.model_name if config else "unknown",
            "session_id": self.session_id,
            "agent_name": agent_name
        })
        
        # Log the system prompt for debugging
        self.agent_logger.log_system_prompt(agent_id, system_prompt)
        
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
        Uses Alice (agent 'a') as the default if available, unless overridden by AIWHISPERER_DEFAULT_AGENT env var.
        """
        if self.is_started:
            raise RuntimeError(f"Session {self.session_id} is already started")
        
        try:
            self.is_started = True
            
            # Check for default agent override in environment
            import os
            default_agent_id = os.environ.get('AIWHISPERER_DEFAULT_AGENT', 'a').lower()
            default_agent_name = {
                'a': 'Alice',
                'd': 'Debbie', 
                'p': 'Patricia',
                't': 'Tessa',
                'e': 'Eamonn'
            }.get(default_agent_id, 'Unknown')
            
            # Try to use specified default agent
            if self.agent_registry and self.agent_registry.get_agent(default_agent_id.upper()):
                try:
                    # Switch to default agent - this will create the agent from registry
                    await self.switch_agent(default_agent_id)
                    logger.info(f"Started session {self.session_id} with {default_agent_name} agent (id: {default_agent_id})")
                    return self.session_id
                except Exception as e:
                    logger.error(f"Failed to create {default_agent_name} agent: {e}, falling back to generic default")
                    # Fall through to create default agent
            
            # Fallback to generic default agent
            system_prompt = system_prompt or "You are a helpful AI assistant."
            await self.create_agent("default", system_prompt)
            logger.info(f"Started session {self.session_id} with default agent")
            
            # Introduction will be handled by switch_agent or first message
            
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
                            
                            # Enable mailbox debug mode for Debbie
                            if agent_id.lower() in ['d', 'debbie']:
                                logger.info(f"Enabling force_mailbox_tool debug mode for Debbie")
                                # First enable the debug_options feature
                                self.prompt_system.enable_feature('debug_options')
                                # Then enable the specific debug option
                                self.prompt_system.enable_debug_option('force_mailbox_tool')
                            
                            # Get model name for capability checking
                            model_name = None
                            if agent_info.ai_config and agent_info.ai_config.get("model"):
                                model_name = agent_info.ai_config.get("model")
                            else:
                                model_name = self.config.get("openrouter", {}).get("model")
                            
                            # Include tools for debugging agents like Debbie
                            include_tools = agent_id.lower() in ['d', 'debbie'] or 'debug' in agent_info.name.lower()
                            
                            # Get formatted prompt with model name for structured output support
                            prompt = self.prompt_system.get_formatted_prompt(
                                "agents", 
                                prompt_name, 
                                include_tools=include_tools,
                                model_name=model_name
                            )
                            system_prompt = prompt
                            prompt_source = f"prompt_system:agents/{prompt_name}" + (" (with_tools)" if include_tools else "")
                            logger.info(f"✅ Successfully loaded prompt via PromptSystem for {agent_id} (tools included: {include_tools})")
                            
                            # Clear debug options after loading prompt to avoid affecting other agents
                            if agent_id.lower() in ['d', 'debbie']:
                                self.prompt_system.disable_debug_option('force_mailbox_tool')
                                # Also disable the debug_options feature if no other debug options are active
                                if not self.prompt_system.get_debug_options():
                                    self.prompt_system.disable_feature('debug_options')
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
            
            # Log the agent switch
            if old_agent:
                self.agent_logger.log_agent_switch(old_agent, agent_id, "Agent switch requested")
            
            # Notify observer about agent switch
            if old_agent and self.observer:
                self.observer.on_agent_switch(self.session_id, old_agent, agent_id)
            
            logger.info(f"Switched active agent from '{old_agent}' to '{agent_id}' in session {self.session_id}")
            
            # Have the agent introduce itself if not already introduced
            if self.active_agent and self.active_agent not in self.introduced_agents:
                await self._agent_introduction()
    
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
            
            if model_name and not is_continuation:
                from ai_whisperer.extensions.agents.prompt_optimizer import optimize_user_message
                optimized_message = optimize_user_message(message, model_name, self.active_agent, is_continuation)
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
            
            # Note: Don't reset streaming sequences - let router handle sequence numbering naturally
            
            # Create streaming callback - parse structured JSON before sending
            chunk_buffer = []  # Buffer for accumulating chunks
            is_json_format = False  # Track if we detect JSON format
            last_display_content = ""  # Track last sent content to avoid duplicates
            detected_structured = False  # Track if we've detected structured output format
            
            async def send_chunk(chunk: str):
                """Send a chunk of AI response to the client"""
                nonlocal is_json_format, last_display_content, detected_structured
                try:
                    # Check if WebSocket is still connected
                    if self.websocket is None:
                        logger.warning(f"WebSocket disconnected for session {self.session_id}, skipping chunk")
                        return
                    
                    # Accumulate chunks
                    chunk_buffer.append(chunk)
                    accumulated_content = ''.join(chunk_buffer)
                    
                    # Try to detect format from accumulated content
                    if not is_json_format and accumulated_content.strip():
                        is_json_format = accumulated_content.strip().startswith('{')
                    
                    # Check if this response contains tool calls - if so, don't stream (backend-only operation)
                    contains_tool_calls = (
                        '"tool_calls"' in accumulated_content or 
                        '"function_calls"' in accumulated_content
                    )
                    
                    if contains_tool_calls:
                        # Tool calls are backend-only - don't stream to frontend
                        logger.debug("Suppressing streaming for tool call response")
                        return
                    
                    # Parse structured content if it looks like JSON
                    if is_json_format or detected_structured:
                        content_stripped = accumulated_content.strip()
                        
                        # Check if this looks like our structured format
                        if not detected_structured and ('"analysis"' in content_stripped or '"commentary"' in content_stripped or '"final"' in content_stripped):
                            detected_structured = True
                            logger.debug("Detected structured output format")
                        
                        if detected_structured:
                            # CRITICAL: If we have analysis/commentary but NO final field, this is likely
                            # a response that's building up to tool calls. Don't stream it.
                            if '"final"' not in content_stripped:
                                logger.debug("Suppressing structured content without final field (likely tool call preparation)")
                                return
                            
                            try:
                                # For partial responses, try to fix incomplete JSON
                                open_braces = content_stripped.count('{')
                                close_braces = content_stripped.count('}')
                                if open_braces > close_braces:
                                    test_content = content_stripped + '}' * (open_braces - close_braces)
                                else:
                                    test_content = content_stripped
                                
                                # Try to parse
                                data = json.loads(test_content)
                                
                                # Check if it has our expected structure
                                if 'analysis' in data or 'commentary' in data or 'final' in data:
                                    # This is structured output - extract only the final content
                                    display_content = data.get('final', '')
                                    
                                    # Only send if we have new content to display
                                    if display_content and display_content != last_display_content:
                                        await self.websocket.send_json({
                                            "jsonrpc": "2.0",
                                            "method": "StreamingUpdate",
                                            "params": {
                                                "type": "streaming_chunk",
                                                "content": display_content,  # Send only the 'final' field
                                                "sessionId": self.session_id,
                                                "agentId": self.active_agent,
                                                "isPartial": True,
                                                "format": "text",  # Always text for display
                                                "isStructured": True,  # Flag that this came from structured output
                                                "metadata": {
                                                    "analysis": data.get('analysis', ''),
                                                    "commentary": data.get('commentary', '')
                                                }
                                            }
                                        })
                                        last_display_content = display_content
                                    return
                            except json.JSONDecodeError:
                                # For incomplete JSON during streaming, try to extract partial final field
                                import re
                                final_match = re.search(r'"final"\s*:\s*"([^"]*)', content_stripped)
                                if final_match:
                                    display_content = final_match.group(1)
                                    # Unescape JSON string
                                    display_content = display_content.replace('\\n', '\n').replace('\\"', '"')
                                    if display_content and display_content != last_display_content:
                                        await self.websocket.send_json({
                                            "jsonrpc": "2.0",
                                            "method": "StreamingUpdate",
                                            "params": {
                                                "type": "streaming_chunk",
                                                "content": display_content,
                                                "sessionId": self.session_id,
                                                "agentId": self.active_agent,
                                                "isPartial": True,
                                                "format": "text",
                                                "isStructured": True
                                            }
                                        })
                                        last_display_content = display_content
                                    return
                                else:
                                    # If we can't extract final yet, don't send anything
                                    return
                    
                    # IMPORTANT: If we detected JSON format but haven't processed it above,
                    # don't send raw JSON chunks to avoid exposing internal structure
                    if is_json_format:
                        logger.debug("Suppressing raw JSON chunk to prevent wrapper exposure")
                        return
                    
                    # For non-structured content, send as-is
                    await self.websocket.send_json({
                        "jsonrpc": "2.0",
                        "method": "StreamingUpdate",
                        "params": {
                            "type": "streaming_chunk",
                            "content": accumulated_content,  # Send full accumulated content
                            "sessionId": self.session_id,
                            "agentId": self.active_agent,
                            "isPartial": True,
                            "format": "text",
                            "rawContent": True
                        }
                    })
                    
                    # Reduce debug spam - only log significant chunks
                    if len(accumulated_content) % 100 == 0:  # Log every 100 chars
                        logger.debug(f"Sent streaming chunk: {len(chunk)} chars, total: {len(accumulated_content)}")
                except Exception as e:
                    logger.error(f"Error sending chunk: {e}")
                    # If we get a RuntimeError about closed connection, clear the WebSocket
                    if "closed" in str(e).lower():
                        self.websocket = None
            
            # Check if we should use structured output
            kwargs = {}
            
            # First check for plan generation
            if self._should_use_structured_output_for_plan(agent, message):
                kwargs['response_format'] = self._get_plan_generation_schema()
                logger.info("Enabling structured output for plan generation")
            # Check if we should use structured channel output
            elif self._should_use_structured_channel_output(agent):
                kwargs['response_format'] = self._get_channel_response_schema()
                logger.info("Enabling structured output for channel responses")
            # Otherwise, check if we should use structured continuation output
            elif self._should_use_structured_continuation(agent):
                # Check if model has quirks about tools with structured output
                agent_tools = agent._get_agent_tools() if hasattr(agent, '_get_agent_tools') else []
                model_name = agent.config.model_name if hasattr(agent, 'config') else ''
                
                if agent_tools and model_name:
                    from ai_whisperer.model_capabilities import has_quirk
                    if has_quirk(model_name, "no_tools_with_structured_output"):
                        logger.info(f"Skipping structured output for {model_name} with tools (model quirk: no_tools_with_structured_output)")
                    else:
                        kwargs['response_format'] = self._get_continuation_schema()
                        logger.info("Enabling structured output for continuation protocol")
                else:
                    kwargs['response_format'] = self._get_continuation_schema()
                    logger.info("Enabling structured output for continuation protocol")
            
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
            
            # Mark if structured output was used so frontend knows to parse JSON
            if result.get('used_structured_output'):
                result['_structured_output'] = True
            
            # Process final message through channel integration to get proper final sequences
            if result.get('response') or result.get('used_structured_output'):
                final_content = result.get('response', '')
                
                # CRITICAL: Check if this is partial JSON that shouldn't be displayed
                if isinstance(final_content, str) and final_content.strip():
                    content_stripped = final_content.strip()
                    # Check for partial JSON patterns that indicate tool preparation
                    if (content_stripped.startswith('{') and 
                        '"analysis"' in content_stripped and 
                        '"commentary"' in content_stripped and
                        '"final"' not in content_stripped):
                        # This is partial JSON without a final field - likely tool preparation
                        logger.info("Detected partial JSON without final field - suppressing channel output")
                        # Skip channel processing entirely for this response
                        final_content = ''
                
                # Try to parse JSON response whether or not structured output was formally used
                # Models might return JSON based on prompt instructions even without response_format
                normalized_response = None
                if isinstance(final_content, str) and final_content.strip().startswith('{'):
                    try:
                        parsed_response = json.loads(final_content)
                        if isinstance(parsed_response, dict):
                            # Check if it's a channel response
                            if all(key in parsed_response for key in ['analysis', 'commentary', 'final']):
                                # This is already a structured channel response
                                normalized_response = parsed_response
                                logger.info("Response is already in structured channel format")
                            elif 'response' in parsed_response:
                                # This is a continuation response - normalize it
                                normalized_response = normalize_response_to_json(parsed_response['response'])
                                # Also extract continuation info if present
                                if 'continuation' in parsed_response:
                                    result['continuation'] = parsed_response['continuation']
                                # Check for tool_calls in the JSON response
                                if 'tool_calls' in parsed_response and parsed_response['tool_calls']:
                                    result['tool_calls'] = parsed_response['tool_calls']
                                    result['finish_reason'] = 'tool_calls'
                                    logger.info(f"Extracted {len(parsed_response['tool_calls'])} tool calls from structured response")
                                logger.debug("Normalized continuation response to JSON format")
                    except json.JSONDecodeError:
                        logger.debug("Response looks like JSON but failed to parse, will normalize as text")
                
                # If not already normalized, normalize the response
                if normalized_response is None:
                    normalized_response = normalize_response_to_json(final_content)
                    logger.debug("Normalized text response to JSON format")
                
                # Send response through channel integration
                # For structured responses, only send the final content to avoid JSON exposure
                if isinstance(normalized_response, dict):
                    # Extract display content - use final field if available, otherwise empty
                    display_content = normalized_response.get('final', '')
                    
                    # If there's no final field but there are tool calls coming, suppress the display
                    if not display_content and result.get('tool_calls'):
                        logger.debug("Suppressing channel message for tool call preparation (no final field)")
                        final_channel_messages = []  # Don't send anything to channels
                    else:
                        # Process through channel integration as plain text
                        final_channel_messages = self.channel_integration.process_ai_response(
                            self.session_id,
                            display_content,
                            agent_id=self.active_agent,
                            is_partial=False,
                            is_structured=False  # Plain text content
                        )
                        
                        # Enhance metadata with structured response data
                        for msg in final_channel_messages:
                            if msg.get('channel') == 'final' and 'metadata' in msg:
                                msg['metadata']['structuredResponse'] = normalized_response
                                msg['metadata']['analysis'] = normalized_response.get('analysis', '')
                                msg['metadata']['commentary'] = normalized_response.get('commentary', '')
                else:
                    # For plain text responses, send as-is
                    final_channel_messages = self.channel_integration.process_ai_response(
                        self.session_id,
                        str(normalized_response) if not isinstance(normalized_response, str) else normalized_response,
                        agent_id=self.active_agent,
                        is_partial=False,
                        is_structured=False
                    )
                
                # Send final channel messages with proper sequence numbers
                for channel_msg in final_channel_messages:
                    if self.websocket is not None:
                        try:
                            # Add response format info to the channel message
                            if channel_msg.get('channel') == 'final':
                                channel_msg['metadata']['responseFormat'] = 'json'
                                channel_msg['metadata']['fullResponse'] = normalized_response
                            
                            await self.websocket.send_json({
                                "jsonrpc": "2.0",
                                "method": "ChannelMessageNotification",
                                "params": channel_msg
                            })
                        except Exception as e:
                            logger.error(f"Error sending final channel message: {e}")
                            if "closed" in str(e).lower():
                                self.websocket = None
            
            # Final notifications now handled by channel system
            
            # Debug logging to understand the result type
            logger.debug(f"Result type: {type(result)}, value: {result}")
            
            # Ensure result is a dict for continuation logic
            if not isinstance(result, dict):
                logger.warning(f"Unexpected result type from agent.process_message: {type(result)}")
                # Convert to dict format if needed
                result = {'response': str(result) if result else None}
            
            # Log AI response to agent's log
            if result.get('response'):
                self.agent_logger.log_agent_message(self.active_agent, "ai_response", result['response'], {
                    "finish_reason": result.get('finish_reason'),
                    "tool_calls": len(result.get('tool_calls', [])) if result.get('tool_calls') else 0,
                    "used_structured_output": result.get('used_structured_output', False)
                })
            
            # Log tool calls if any
            if result.get('tool_calls'):
                for tool_call in result['tool_calls']:
                    tool_name = tool_call.get('function', {}).get('name', 'unknown')
                    tool_args = tool_call.get('function', {}).get('arguments', '{}')
                    self.agent_logger.log_agent_message(self.active_agent, "tool_call", 
                                                      f"{tool_name}({tool_args})", 
                                                      {"tool_id": tool_call.get('id')})
            
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
            
            # If the AI called tools, we need another round to get the final response
            # This follows the standard OpenAI/Claude tool calling pattern
            if result.get('finish_reason') == 'tool_calls' and result.get('tool_calls'):
                logger.info(f"🔧 TOOL CALLS COMPLETED: {len(result['tool_calls'])} tools were executed")
                logger.info("🔧 Making another AI call to process tool results...")
                
                # The tool results are already stored as tool messages by the AI loop
                # We need another AI call but without adding a new user message
                # This follows the standard OpenAI/Claude pattern
                
                # Store the AI's response that included the tool calls
                # This is important for the conversation history
                if 'response' in result:
                    # Temporarily store just the assistant message
                    # The tool results are already stored
                    pass
                
                # Now call the AI to process the tool results
                # We use process_messages to avoid adding a user message
                messages = agent.context.retrieve_messages()
                tool_response_result = await agent.ai_loop.process_messages(
                    messages=messages,
                    on_stream_chunk=send_chunk,
                    tools=agent._get_agent_tools(),
                    **kwargs
                )
                
                # Parse structured output if needed
                if tool_response_result.get('used_structured_output') and isinstance(tool_response_result.get('response'), str):
                    try:
                        parsed_response = json.loads(tool_response_result['response'])
                        if isinstance(parsed_response, dict) and 'response' in parsed_response:
                            # Extract the actual response content
                            tool_response_result['response'] = parsed_response['response']
                            # Also extract continuation info if present
                            if 'continuation' in parsed_response:
                                tool_response_result['continuation'] = parsed_response['continuation']
                            logger.debug("Parsed structured output response from tool processing")
                    except json.JSONDecodeError:
                        logger.debug("Tool response is not JSON, using raw content")
                
                # Normalize the tool response through channel integration
                if tool_response_result.get('response'):
                    normalized_tool_response = normalize_response_to_json(tool_response_result['response'])
                    tool_channel_messages = self.channel_integration.process_ai_response(
                        self.session_id,
                        json.dumps(normalized_tool_response),
                        agent_id=self.active_agent,
                        is_partial=False,
                        is_structured=True
                    )
                    
                    # Send tool response channel messages
                    for channel_msg in tool_channel_messages:
                        if self.websocket is not None:
                            try:
                                # Add response format info
                                if channel_msg.get('channel') == 'final':
                                    channel_msg['metadata']['responseFormat'] = 'json'
                                    channel_msg['metadata']['fullResponse'] = normalized_tool_response
                                
                                await self.websocket.send_json({
                                    "jsonrpc": "2.0",
                                    "method": "ChannelMessageNotification",
                                    "params": channel_msg
                                })
                            except Exception as e:
                                logger.error(f"Error sending tool response channel message: {e}")
                                if "closed" in str(e).lower():
                                    self.websocket = None
                
                # Store the final AI response
                if tool_response_result.get('response') and not tool_response_result.get('error'):
                    final_assistant_msg = {
                        "role": "assistant",
                        "content": tool_response_result['response']
                    }
                    agent.context.store_message(final_assistant_msg)
                    logger.info("🔧 Stored final AI response after tool processing")
                
                # Ensure tool_response_result is a dict
                if not isinstance(tool_response_result, dict):
                    logger.warning(f"Unexpected tool response type: {type(tool_response_result)}")
                    tool_response_result = {'response': str(tool_response_result) if tool_response_result else None}
                
                # Combine the results - keep the tool calls from first result, response from second
                combined_result = {
                    'response': tool_response_result.get('response'),
                    'tool_calls': result.get('tool_calls'),  # Keep original tool calls
                    'finish_reason': tool_response_result.get('finish_reason', 'stop'),
                    'error': tool_response_result.get('error'),
                    'continuation': tool_response_result.get('continuation'),  # Preserve continuation info
                    'used_structured_output': tool_response_result.get('used_structured_output', False)
                }
                result = combined_result
                logger.info("🔧 Tool results processed and final response generated")
            
            # Check if the AI wants to continue (using general continuation protocol)
            # This is separate from tool handling - it's about multi-step tasks
            if self.active_agent and self.active_agent in self.agents and not is_continuation:
                agent = self.agents[self.active_agent]
                
                # Extract continuation state from response
                continuation_state = None
                if result.get('continuation'):
                    continuation_state = result.get('continuation')
                elif result.get('response') and isinstance(result['response'], str):
                    # Try to extract from response if it's still in JSON format
                    try:
                        parsed = json.loads(result['response'])
                        if isinstance(parsed, dict) and 'continuation' in parsed:
                            continuation_state = parsed['continuation']
                    except:
                        # Try to extract continuation from partial JSON using regex
                        continuation_match = re.search(r'"continuation"\s*:\s*\{[^}]*"status"\s*:\s*"(CONTINUE|TERMINATE)"[^}]*\}', result['response'])
                        if continuation_match:
                            status = continuation_match.group(1)
                            continuation_state = {'status': status}
                            logger.debug(f"Extracted continuation status from partial JSON: {status}")
                
                # Special handling for error responses that might need continuation
                if result.get('finish_reason') == 'error' and not continuation_state:
                    # Check if the response indicates the AI was trying to do something
                    response_text = result.get('response', '')
                    if response_text and any(indicator in response_text for indicator in ['[COMMENTARY]', 'I will', "I'll", 'need to', 'going to']):
                        logger.info("🔄 Error response appears to be attempting an action, assuming CONTINUE")
                        continuation_state = {'status': 'CONTINUE', 'reason': 'Error response indicates ongoing task'}
                
                # Check if we should continue
                should_continue = False
                if continuation_state and isinstance(continuation_state, dict):
                    should_continue = continuation_state.get('status') == 'CONTINUE'
                    logger.info(f"🔄 Continuation state: {continuation_state}")
                
                if should_continue:
                    logger.info("🔄 AI signaled CONTINUE - executing continuation")
                    self._continuation_depth += 1
                    
                    # Check depth limit
                    if self._continuation_depth > self._max_continuation_depth:
                        logger.warning(f"Max continuation depth {self._max_continuation_depth} reached, stopping")
                    else:
                        # Create continuation message
                        continuation_msg = "Please continue with the next step."
                        if continuation_state.get('reason'):
                            continuation_msg = f"Continue: {continuation_state['reason']}"
                        
                        # Recursively call send_user_message to continue
                        logger.info(f"🔄 Sending continuation message: {continuation_msg}")
                        continuation_result = await self.send_user_message(continuation_msg, is_continuation=True)
                        
                        # Merge continuation result with original result
                        if continuation_result and isinstance(continuation_result, dict):
                            # Append continuation response to original
                            if result.get('response') and continuation_result.get('response'):
                                result['response'] += "\n\n" + continuation_result['response']
                            # Use continuation's finish reason
                            if continuation_result.get('finish_reason'):
                                result['finish_reason'] = continuation_result['finish_reason']
                            # Merge tool calls if any
                            if continuation_result.get('tool_calls'):
                                if result.get('tool_calls'):
                                    result['tool_calls'].extend(continuation_result['tool_calls'])
                                else:
                                    result['tool_calls'] = continuation_result['tool_calls']
            
            # Reset continuation depth if we're done with continuations
            if not is_continuation:
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
            # Send a simple introduction request using the full streaming pipeline
            introduction_prompt = "Please introduce yourself briefly, mentioning your name and what you help with."
            
            # TEMPORARILY DISABLED: Introduction is a UI feature, not needed for core functionality
            # TODO: Re-enable when UI properly handles agent introductions
            logger.info(f"Skipping agent introduction for '{self.active_agent}' (temporarily disabled)")
            return
            
            # Use the normal send_user_message pipeline but mark as internal
            # logger.info(f"Requesting introduction from agent '{self.active_agent}'")
            # await self.send_user_message(introduction_prompt, is_continuation=False)
            
            # Mark as introduced
            self.introduced_agents.add(self.active_agent)
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
        # json is already imported at module level
        
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
        # json is already imported at module level
        
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
        
        # Clear channel data for this session
        if hasattr(self, 'channel_integration'):
            self.channel_integration.clear_session(self.session_id)
            logger.info(f"Cleared channel data for session {self.session_id}")
        
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
        # json is already imported at module level
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
    
    def _should_use_structured_channel_output(self, agent: Any) -> bool:
        """
        Determine if we should use structured output for channel responses.
        
        Args:
            agent: The active agent
            
        Returns:
            True if we should use structured channel output
        """
        # Check if the model supports structured output
        from ai_whisperer.model_capabilities import supports_structured_output, has_quirk
        if not hasattr(agent, 'config') or not agent.config.model_name:
            return False
            
        model_name = agent.config.model_name
        
        if not supports_structured_output(model_name):
            return False
            
        # Check if model has the no_tools_with_structured_output quirk
        # If it does, we can't use structured output when tools are available
        if has_quirk(model_name, "no_tools_with_structured_output"):
            # Check if this agent has tools
            agent_tools = agent._get_agent_tools() if hasattr(agent, '_get_agent_tools') else []
            if agent_tools:
                logger.info(f"Skipping structured channel output for {model_name} (quirk: no_tools_with_structured_output with {len(agent_tools)} tools)")
                return False
            
        # Check if channel system is enabled in prompt system
        if self.prompt_system and 'channel_system' in self.prompt_system.get_enabled_features():
            logger.info(f"Enabling structured channel output for {model_name}")
            return True
            
        return False
    
    def _should_use_structured_continuation(self, agent: Any) -> bool:
        """
        Determine if we should use structured output for continuation protocol.
        
        Args:
            agent: The active agent
            
        Returns:
            True if we should use structured continuation output
        """
        # Check if the model supports structured output
        from ai_whisperer.model_capabilities import supports_structured_output
        if not hasattr(agent, 'config') or not agent.config.model_name:
            return False
            
        if not supports_structured_output(agent.config.model_name):
            return False
            
        # For now, enable for all agents with compatible models
        # We can make this configurable per agent later
        return True
    
    def _get_channel_response_schema(self) -> Dict[str, Any]:
        """
        Get the channel response schema for structured output.
        
        Returns:
            The response_format dict for channel responses
        """
        # Load the channel response schema
        from ai_whisperer.core.config import get_schema_path
        try:
            schema_path = get_schema_path("channel_response_schema")
            with open(schema_path) as f:
                schema = json.load(f)
            
            # Remove the $schema field if present
            if "$schema" in schema:
                del schema["$schema"]
            
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "channel_response",
                    "strict": False,
                    "schema": schema
                }
            }
        except Exception as e:
            logger.error(f"Failed to load channel response schema: {e}")
            return None
    
    def _get_continuation_schema(self) -> Dict[str, Any]:
        """
        Get the continuation protocol schema for structured output.
        
        Returns:
            The response_format dict for continuation protocol
        """
        # json is already imported at module level
        from pathlib import Path
        
        # Load the continuation schema
        schema_path = Path("config/schemas/continuation_schema.json")
        
        try:
            with open(schema_path, 'r') as f:
                continuation_schema = json.load(f)
            
            # Remove the $schema field if present
            if "$schema" in continuation_schema:
                del continuation_schema["$schema"]
            
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "continuation_protocol",
                    "strict": False,  # Use false for better compatibility
                    "schema": continuation_schema
                }
            }
        except Exception as e:
            logger.error(f"Failed to load continuation schema: {e}")
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