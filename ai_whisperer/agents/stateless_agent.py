"""
Stateless Agent implementation that works with the new stateless AILoop.
This agent doesn't manage sessions or use delegates - it simply processes
messages through the AI loop and returns results directly.
"""
import logging
from typing import Any, Dict, Optional, Callable, List

from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop
from ai_whisperer.agents.continuation_strategy import ContinuationStrategy

logger = logging.getLogger(__name__)


class StatelessAgent:
    """
    A stateless agent that processes messages without session management.
    Each message is processed independently through the AI loop.
    """
    
    def __init__(self, config: AgentConfig, context: AgentContext, ai_loop: StatelessAILoop, agent_registry_info=None):
        """
        Initialize a stateless agent.
        
        Args:
            config: Agent configuration
            context: Agent context for storing conversation history
            ai_loop: Stateless AI loop instance
            agent_registry_info: Optional agent info from AgentRegistry for tool filtering
            
        Raises:
            ValueError: If any required parameter is None
        """
        if config is None:
            raise ValueError("AgentConfig must not be None")
        if context is None:
            raise ValueError("AgentContext must not be None")
        if ai_loop is None:
            raise ValueError("AILoop instance must not be None")
            
        self.config = config
        self.context = context
        self.ai_loop = ai_loop
        self.agent_registry_info = agent_registry_info
        
        # Initialize continuation strategy if configured
        self.continuation_strategy = None
        if agent_registry_info and hasattr(agent_registry_info, 'continuation_config') and agent_registry_info.continuation_config:
            self.continuation_strategy = ContinuationStrategy(agent_registry_info.continuation_config)
            logger.info(f"Initialized continuation strategy for agent: {config.name}")
        
        logger.info(f"Created stateless agent: {config.name}")
    
    async def process_message(
        self,
        message: str,
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        **kwargs
    ) -> Any:
        """
        Process a message through the AI loop.
        
        Args:
            message: The message to process
            on_stream_chunk: Optional callback for streaming chunks
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The AI response - either a string or a dict with response/tool_calls
        """
        try:
            # Extract generation parameters from kwargs
            generation_params = {}
            
            # Override config defaults with provided parameters
            if 'temperature' in kwargs:
                generation_params['temperature'] = kwargs['temperature']
            elif 'temperature' in self.config.generation_params:
                generation_params['temperature'] = self.config.generation_params['temperature']
                
            if 'max_tokens' in kwargs:
                generation_params['max_tokens'] = kwargs['max_tokens']
            elif 'max_tokens' in self.config.generation_params:
                generation_params['max_tokens'] = self.config.generation_params['max_tokens']
            
            # Extract store_messages parameter if provided
            store_messages = kwargs.get('store_messages', True)
            
            # Extract response_format if provided
            response_format = kwargs.get('response_format', None)
            
            # Get filtered tools for this agent
            tools = self._get_agent_tools()
            
            # Process through stateless AI loop with agent-specific tools
            result = await self.ai_loop.process_with_context(
                message=message,
                context_provider=self.context,
                on_stream_chunk=on_stream_chunk,
                tools=tools,  # Pass filtered tools
                store_messages=store_messages,
                response_format=response_format,
                **generation_params
            )
            
            # Handle the result
            if result.get('error'):
                # Return error information
                return {
                    'response': result.get('response'),
                    'error': result['error'],
                    'finish_reason': result.get('finish_reason', 'error')
                }
            elif result.get('tool_calls'):
                # Return full result for tool calls
                return {
                    'response': result['response'],
                    'tool_calls': result['tool_calls'],
                    'finish_reason': result['finish_reason']
                }
            else:
                # Return full result for consistency
                return {
                    'response': result['response'],
                    'finish_reason': result.get('finish_reason', 'stop')
                }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Return error information
            return {
                'response': None,
                'error': e,
                'finish_reason': 'error'
            }
    
    def get_context_messages(self) -> list:
        """
        Get the current conversation history.
        
        Returns:
            List of message dictionaries
        """
        return self.context.retrieve_messages()
    
    def clear_context(self):
        """Clear the conversation history."""
        # Clear by retrieving and not storing
        messages = self.context.retrieve_messages()
        
        # Keep only system message if present
        system_messages = [msg for msg in messages if msg.get('role') == 'system']
        
        # Re-initialize context with system message
        if hasattr(self.context, 'clear'):
            self.context.clear()
            for msg in system_messages:
                self.context.store_message(msg)
        else:
            logger.warning("Context does not support clear operation")
    
    @property
    def agent_id(self) -> str:
        """Get the agent ID."""
        return self.config.name
    
    @property
    def system_prompt(self) -> str:
        """Get the system prompt."""
        return self.config.system_prompt
    
    def _get_agent_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get filtered tools for this agent based on registry configuration.
        
        Returns:
            List of tool definitions for this agent, or None to use all tools
        """
        if not self.agent_registry_info:
            # No registry info, use all tools (fallback behavior)
            logger.debug(f"Agent {self.config.name}: No registry info, using all tools")
            return None
        
        try:
            from ai_whisperer.tools.tool_registry import get_tool_registry
            
            tool_registry = get_tool_registry()
            
            # Get filtered tools based on agent configuration
            filtered_tools = tool_registry.get_tools_for_agent(
                tool_sets=getattr(self.agent_registry_info, 'tool_sets', None),
                tags=getattr(self.agent_registry_info, 'tool_tags', None),
                allow_tools=getattr(self.agent_registry_info, 'allow_tools', None),
                deny_tools=getattr(self.agent_registry_info, 'deny_tools', None)
            )
            
            # Convert tools to OpenRouter tool definitions
            tool_definitions = [tool.get_openrouter_tool_definition() for tool in filtered_tools]
            
            logger.info(f"Agent {self.config.name}: Using {len(tool_definitions)} filtered tools")
            return tool_definitions
            
        except Exception as e:
            logger.error(f"Failed to get filtered tools for agent {self.config.name}: {e}")
            # Fallback to all tools on error
            return None
    
    def should_continue_after_tools(self, result: Dict[str, Any], original_message: str) -> bool:
        """
        Determine if continuation is needed after tool execution.
        
        Args:
            result: The result from process_message with tool_calls
            original_message: The original user message
            
        Returns:
            True if continuation is needed, False otherwise
        """
        if not self.continuation_strategy:
            return False
        return self.continuation_strategy.should_continue(result, original_message)
    
    def get_continuation_message(self, tool_names: List[str], original_message: str) -> str:
        """
        Get the appropriate continuation message based on context.
        
        Args:
            tool_names: List of tool names that were just executed
            original_message: The original user message
            
        Returns:
            The continuation message to send
        """
        if not self.continuation_strategy:
            return "Please continue with the next step."
        return self.continuation_strategy.get_continuation_message(tool_names, original_message)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"StatelessAgent(id={self.agent_id}, model={self.config.model_name})"