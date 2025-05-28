"""
Stateless Agent implementation that works with the new stateless AILoop.
This agent doesn't manage sessions or use delegates - it simply processes
messages through the AI loop and returns results directly.
"""
import logging
from typing import Any, Dict, Optional, Callable

from ai_whisperer.agents.config import AgentConfig
from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.ai_loop.stateless_ai_loop import StatelessAILoop

logger = logging.getLogger(__name__)


class StatelessAgent:
    """
    A stateless agent that processes messages without session management.
    Each message is processed independently through the AI loop.
    """
    
    def __init__(self, config: AgentConfig, context: AgentContext, ai_loop: StatelessAILoop):
        """
        Initialize a stateless agent.
        
        Args:
            config: Agent configuration
            context: Agent context for storing conversation history
            ai_loop: Stateless AI loop instance
            
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
            
            # Process through stateless AI loop
            result = await self.ai_loop.process_with_context(
                message=message,
                context_provider=self.context,
                on_stream_chunk=on_stream_chunk,
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
                # Return just the response text for simple messages
                return result['response']
                
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
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"StatelessAgent(id={self.agent_id}, model={self.config.model_name})"