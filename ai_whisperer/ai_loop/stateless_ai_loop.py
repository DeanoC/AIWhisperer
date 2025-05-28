"""
Stateless AILoop implementation that works without delegates.
This provides a cleaner interface for direct usage without the complexity
of delegate management and event notifications.
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Callable, AsyncIterator
from types import SimpleNamespace

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.ai_service import AIService
from ai_whisperer.context.provider import ContextProvider
from ai_whisperer.tools.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


class StatelessAILoop:
    """
    A stateless version of AILoop that processes messages directly without
    maintaining session state or using delegates.
    """
    
    def __init__(self, config: AIConfig, ai_service: AIService):
        """
        Initialize the stateless AI loop.
        
        Args:
            config: AI configuration settings
            ai_service: The AI service instance for chat completions
        """
        self.config = config
        self.ai_service = ai_service
    
    async def process_with_context(
        self,
        message: str,
        context_provider: ContextProvider,
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        store_messages: bool = True,
        **generation_params
    ) -> Dict[str, Any]:
        """
        Process a message using the provided context.
        
        Args:
            message: The user message to process
            context_provider: Context provider for message history
            on_stream_chunk: Optional callback for streaming chunks
            tools: Optional list of tool definitions to use
            timeout: Optional timeout in seconds
            store_messages: Whether to store messages in context (default: True)
            **generation_params: Additional AI generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict containing:
                - response: The AI response text
                - finish_reason: The reason the AI stopped
                - tool_calls: Any tool calls made by the AI
                - error: Any error that occurred
        """
        result = {
            'response': None,
            'finish_reason': None,
            'tool_calls': None,
            'error': None
        }
        
        try:
            # Store user message if requested
            if store_messages:
                user_message = {"role": "user", "content": message}
                context_provider.store_message(user_message)
            
            # Get message history
            messages = context_provider.retrieve_messages()
            
            # If no messages were stored, add the current message
            if not store_messages and not any(msg.get('content') == message for msg in messages):
                messages = messages + [{"role": "user", "content": message}]
            
            # Get tools if not provided
            if tools is None:
                tools = get_tool_registry().get_all_tool_definitions()
            
            # Create the streaming coroutine
            async def run_stream():
                # Merge config with generation params (generation params take precedence)
                params = {**self.config.__dict__, **generation_params}
                stream = self.ai_service.stream_chat_completion(
                    messages=messages,
                    tools=tools,
                    **params
                )
                return await self._process_stream(stream, on_stream_chunk)
            
            # Run with timeout if specified
            if timeout:
                response_data = await asyncio.wait_for(run_stream(), timeout=timeout)
            else:
                response_data = await run_stream()
            
            # Update result
            result.update(response_data)
            
            # Handle error from stream processing
            if response_data.get('error'):
                error_msg = f"Error processing message: {str(response_data['error'])}"
                if store_messages:
                    error_message = {"role": "assistant", "content": error_msg}
                    context_provider.store_message(error_message)
            # Store assistant message if requested and we have content
            elif store_messages and (response_data.get('response') or response_data.get('tool_calls')):
                assistant_message = {"role": "assistant"}
                if response_data.get('response'):
                    assistant_message['content'] = response_data['response']
                if response_data.get('tool_calls'):
                    assistant_message['tool_calls'] = response_data['tool_calls']
                context_provider.store_message(assistant_message)
                
        except asyncio.TimeoutError:
            error_msg = "AI service timeout: The AI did not respond in time."
            result['error'] = error_msg
            logger.error(error_msg)
            
            # Store error message in context
            if store_messages:
                error_message = {"role": "assistant", "content": error_msg}
                context_provider.store_message(error_message)
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            result['error'] = e
            logger.exception(error_msg)
            
            # Store error message in context
            if store_messages:
                error_message = {"role": "assistant", "content": error_msg}
                context_provider.store_message(error_message)
        
        return result
    
    async def process_messages(
        self,
        messages: List[Dict[str, Any]],
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        **generation_params
    ) -> Dict[str, Any]:
        """
        Process messages directly without using a context provider.
        
        Args:
            messages: List of message dictionaries
            on_stream_chunk: Optional callback for streaming chunks
            tools: Optional list of tool definitions
            timeout: Optional timeout in seconds
            **generation_params: Additional AI generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            Dict containing response data
        """
        result = {
            'response': None,
            'finish_reason': None,
            'tool_calls': None,
            'error': None
        }
        
        try:
            # Get tools if not provided
            if tools is None:
                tools = get_tool_registry().get_all_tool_definitions()
            
            # Create the streaming coroutine
            async def run_stream():
                # Merge config with generation params (generation params take precedence)
                params = {**self.config.__dict__, **generation_params}
                stream = self.ai_service.stream_chat_completion(
                    messages=messages,
                    tools=tools,
                    **params
                )
                return await self._process_stream(stream, on_stream_chunk)
            
            # Run with timeout if specified
            if timeout:
                response_data = await asyncio.wait_for(run_stream(), timeout=timeout)
            else:
                response_data = await run_stream()
            
            result.update(response_data)
            
        except asyncio.TimeoutError:
            error_msg = "AI service timeout: The AI did not respond in time."
            result['error'] = error_msg
            logger.error(error_msg)
            
        except Exception as e:
            error_msg = f"Error processing messages: {str(e)}"
            result['error'] = e
            logger.exception(error_msg)
        
        return result
    
    async def _process_stream(
        self,
        stream: AsyncIterator,
        on_stream_chunk: Optional[Callable[[str], Any]] = None
    ) -> Dict[str, Any]:
        """
        Process the AI response stream.
        
        Args:
            stream: The AI response stream
            on_stream_chunk: Optional callback for each chunk
            
        Returns:
            Dict with response data
        """
        full_response = ""
        accumulated_tool_calls = ""
        finish_reason = None
        last_chunk = None
        
        try:
            # Handle coroutine types (from mocks)
            if hasattr(stream, '__await__'):
                stream = await stream
            
            async for chunk in stream:
                last_chunk = chunk
                
                # Process content
                if chunk.delta_content:
                    full_response += chunk.delta_content
                    if on_stream_chunk:
                        await on_stream_chunk(chunk.delta_content)
                
                # Accumulate tool calls
                if chunk.delta_tool_call_part:
                    accumulated_tool_calls += chunk.delta_tool_call_part
                
                # Track finish reason
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
            
            # Send final chunk notification
            if on_stream_chunk:
                final_content = last_chunk.delta_content if last_chunk and last_chunk.delta_content else ""
                await on_stream_chunk(final_content)
            
            # Parse tool calls if present
            tool_calls = None
            if finish_reason == "tool_calls" and accumulated_tool_calls:
                try:
                    parsed_data = json.loads(accumulated_tool_calls)
                    if isinstance(parsed_data, dict) and "tool_calls" in parsed_data:
                        tool_calls = parsed_data["tool_calls"]
                    else:
                        tool_calls = parsed_data
                    if not isinstance(tool_calls, list):
                        tool_calls = [tool_calls]
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool calls: {e}")
            
            return {
                'response': full_response,
                'finish_reason': finish_reason,
                'tool_calls': tool_calls,
                'error': None
            }
            
        except Exception as e:
            logger.exception("Error processing stream")
            return {
                'response': full_response if full_response else None,
                'finish_reason': 'error',
                'tool_calls': None,
                'error': e
            }