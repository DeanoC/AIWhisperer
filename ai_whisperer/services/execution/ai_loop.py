"""
Module: ai_whisperer/ai_loop/stateless_ai_loop.py
Purpose: Implementation of StatelessAILoop class

Stateless AILoop implementation that works without delegates.
This provides a cleaner interface for direct usage without the complexity
of delegate management and event notifications.

Key Components:
- StatelessAILoop: 

Usage:
    statelessailoop = StatelessAILoop()
    result = statelessailoop.process_with_context()

Dependencies:
- logging
- asyncio
- types

Related:
- See docs/archive/debugging-session-2025-05-30-consolidated.md
- See docs/archive/refactor_tracking/REFACTOR_CODE_MAP_SUMMARY.md
- See docs/archive/consolidated_phase2/PR_DESCRIPTION.md

"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional, Callable, AsyncIterator
from ai_whisperer.services.execution.ai_config import AIConfig
from ai_whisperer.services.ai.base import AIService
from ai_whisperer.context.provider import ContextProvider
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.services.execution.tool_call_accumulator import ToolCallAccumulator

logger = logging.getLogger(__name__)

class StatelessAILoop:
    """
    A stateless version of AILoop that processes messages directly without
    maintaining session state or using delegates.
    """
    
    def __init__(self, config: AIConfig, ai_service: AIService, agent_context: Optional[Dict[str, Any]] = None):
        """
        Initialize the stateless AI loop.
        
        Args:
            config: AI configuration settings
            ai_service: The AI service instance for chat completions
            agent_context: Optional context about the current agent
        """
        self.config = config
        self.ai_service = ai_service
        self.agent_context = agent_context or {}
    
    async def process_with_context(
        self,
        message: str,
        context_provider: ContextProvider,
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        store_messages: bool = True,
        response_format: Optional[Dict[str, Any]] = None,
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
            response_format: Optional structured output format (JSON Schema)
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
            # ATOMIC MESSAGE HANDLING: Don't store user message yet
            # We'll only store it if we get a successful response
            
            # Get message history
            messages = context_provider.retrieve_messages()
            logger.debug(f"🔍 RETRIEVED MESSAGES COUNT: {len(messages)}")
            for i, msg in enumerate(messages):
                if isinstance(msg, dict):
                    content = msg.get('content', '')
                    if isinstance(content, str):
                        content_preview = content[:50] + '...' if len(content) > 50 else content
                    else:
                        content_preview = str(content)[:50] + '...'
                    logger.debug(f"🔍 MESSAGE {i}: role={msg.get('role', 'unknown')} content={content_preview}")
                else:
                    logger.debug(f"🔍 MESSAGE {i}: {type(msg)} {str(msg)[:50]}...")
            
            # Ensure all messages are dicts (defensive programming)
            validated_messages = []
            for msg in messages:
                if isinstance(msg, str):
                    logger.warning(f"Found string message in context, converting to dict: {msg[:100]}...")
                    validated_messages.append({"role": "user", "content": msg})
                elif isinstance(msg, dict):
                    validated_messages.append(msg)
                else:
                    logger.error(f"Found unexpected message type in context: {type(msg)}")
                    # Skip invalid messages
                    continue
            messages = validated_messages
            
            if messages and isinstance(messages[0], dict):
                first_role = messages[0].get('role', 'unknown')
            else:
                first_role = 'N/A'
            logger.debug(f"Processing with {len(messages)} messages, first message role: {first_role}")
            
            # Always add the current message to the messages we send to AI
            # (but don't store it in context yet - that's atomic)
            working_messages = messages + [{"role": "user", "content": message}]
            
            # Get tools if not provided
            if tools is None:
                tools = get_tool_registry().get_all_tool_definitions()
            
            # Create the streaming coroutine
            async def run_stream():
                # LOG EXACTLY WHAT MESSAGES WE'RE SENDING TO THE AI
                logger.debug(f"🚨 SENDING TO AI: {len(working_messages)} messages")
                for i, msg in enumerate(working_messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    preview = content[:100] + '...' if len(content) > 100 else content
                    logger.debug(f"🚨 MSG[{i}] role={role} content={preview}")
                
                # Merge config with generation params (generation params take precedence)
                params = {**self.config.__dict__, **generation_params}
                stream = self.ai_service.stream_chat_completion(
                    messages=working_messages,
                    tools=tools,
                    response_format=response_format,
                    **params
                )
                return await self._process_stream(stream, on_stream_chunk, response_format)
            
            # Run with timeout if specified, with retry logic for empty responses
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                if timeout:
                    response_data = await asyncio.wait_for(run_stream(), timeout=timeout)
                else:
                    response_data = await run_stream()
                
                # Check if we got an empty response (no error but no content or reasoning)
                if (not response_data.get('error') and 
                    not response_data.get('response') and 
                    not response_data.get('reasoning') and
                    not response_data.get('tool_calls') and
                    response_data.get('finish_reason') == 'stop'):
                    
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.warning(f"Empty response received (no content or reasoning), retrying ({retry_count}/{max_retries})...")
                        await asyncio.sleep(1.0 * retry_count)  # Exponential backoff
                        continue
                    else:
                        logger.error(f"Empty response persists after {max_retries} retries")
                
                # If we have reasoning but no content, that's valid - don't retry
                if (not response_data.get('error') and 
                    not response_data.get('response') and 
                    response_data.get('reasoning')):
                    logger.info(f"Got reasoning-only response: {len(response_data.get('reasoning', ''))} chars")
                    # Combine reasoning with response for backward compatibility
                    if response_data.get('reasoning'):
                        response_data['response'] = response_data['reasoning']
                
                # Got a valid response or an error, break out of retry loop
                break
            
            # Update result
            result.update(response_data)
            
            # ATOMIC MESSAGE HANDLING: Only store messages if we got a successful response
            if store_messages:
                # Check if we have a valid response (not empty and no error)
                has_valid_response = (
                    not response_data.get('error') and
                    (response_data.get('response') or 
                     response_data.get('reasoning') or 
                     response_data.get('tool_calls'))
                )
                
                if has_valid_response:
                    # SUCCESS: Store both user and assistant messages atomically
                    logger.info(f"✅ ATOMIC: Storing user message and assistant response")
                    
                    # Store user message
                    user_message = {"role": "user", "content": message}
                    context_provider.store_message(user_message)
                    
                    # Store assistant message
                    assistant_message = {"role": "assistant"}
                    
                    # Handle content and reasoning
                    if response_data.get('response'):
                        # Clean the response before storing to prevent JSON leakage
                        content = response_data['response']
                        if isinstance(content, str) and content.strip().startswith('{'):
                            # This might be structured JSON - check if it has analysis/commentary without final
                            if '"analysis"' in content and '"commentary"' in content and '"final"' not in content:
                                # This is partial JSON without user-facing content - don't store it
                                logger.warning("Suppressing partial JSON from being stored in context")
                                assistant_message['content'] = "[Processing...]"
                            else:
                                # Store as-is
                                assistant_message['content'] = content
                        else:
                            assistant_message['content'] = content
                    elif response_data.get('reasoning'):
                        # If we only have reasoning, use it as content for now
                        assistant_message['content'] = response_data['reasoning']
                    elif response_data.get('tool_calls'):
                        # If only tool calls, no content needed
                        pass
                    
                    # Store reasoning separately if available (for models that support it)
                    if response_data.get('reasoning'):
                        assistant_message['reasoning'] = response_data['reasoning']
                    
                    if response_data.get('tool_calls'):
                        assistant_message['tool_calls'] = response_data['tool_calls']
                        
                    context_provider.store_message(assistant_message)
                else:
                    # FAILURE: Don't store anything - maintain atomic consistency
                    logger.warning(f"❌ ATOMIC: Not storing messages due to empty/error response")
                    if response_data.get('error'):
                        logger.error(f"   Error: {response_data['error']}")
                    else:
                        logger.error(f"   Empty response after {max_retries} retries")
                
                # If there were tool calls, we need to store the tool results too
                if response_data.get('tool_calls') and response_data.get('tool_results'):
                    # Store each tool result as a separate message
                    tool_results = response_data['tool_results']
                    for i, tool_call in enumerate(response_data['tool_calls']):
                        if i < len(tool_results):
                            tool_result = tool_results[i]
                            tool_name = tool_call.get('function', {}).get('name', 'unknown')
                            
                            # Convert tool result to JSON string for the content field
                            try:
                                content = json.dumps(tool_result)
                            except (TypeError, ValueError):
                                content = str(tool_result)
                            
                            # Store tool result message in OpenRouter format
                            tool_message = {
                                "role": "tool",
                                "tool_call_id": tool_call.get('id'),
                                "name": tool_name,
                                "content": content  # JSON string of the tool result
                            }
                            context_provider.store_message(tool_message)
                            logger.info(f"🔄 STORED TOOL RESULT for {tool_name} (ID: {tool_call.get('id')})")
                
        except asyncio.TimeoutError:
            error_msg = "AI service timeout: The AI did not respond in time."
            result['error'] = error_msg
            logger.error(error_msg)
            
            # ATOMIC: Don't store anything on timeout
            if store_messages:
                logger.warning(f"❌ ATOMIC: Not storing messages due to timeout")
                
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            result['error'] = e
            logger.exception(error_msg)
            
            # ATOMIC: Don't store anything on error
            if store_messages:
                logger.warning(f"❌ ATOMIC: Not storing messages due to exception: {type(e).__name__}")
        
        return result
    
    async def process_messages(
        self,
        messages: List[Dict[str, Any]],
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
        response_format: Optional[Dict[str, Any]] = None,
        **generation_params
    ) -> Dict[str, Any]:
        """
        Process messages directly without using a context provider.
        
        Args:
            messages: List of message dictionaries
            on_stream_chunk: Optional callback for streaming chunks
            tools: Optional list of tool definitions
            timeout: Optional timeout in seconds
            response_format: Optional structured output format (JSON Schema)
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
                # LOG EXACTLY WHAT MESSAGES WE'RE SENDING TO THE AI
                logger.debug(f"🚨 SENDING TO AI: {len(messages)} messages")
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    preview = content[:100] + '...' if len(content) > 100 else content
                    logger.debug(f"🚨 MSG[{i}] role={role} content={preview}")
                
                # Merge config with generation params (generation params take precedence)
                params = {**self.config.__dict__, **generation_params}
                stream = self.ai_service.stream_chat_completion(
                    messages=messages,
                    tools=tools,
                    response_format=response_format,
                    **params
                )
                return await self._process_stream(stream, on_stream_chunk, response_format)
            
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
    
    def _determine_tool_strategy(self, tool_calls: List[Dict[str, Any]]) -> str:
        """Determine tool execution strategy based on model capabilities and tool count"""
        try:
            model_id = getattr(self.config, 'model_id', 'unknown')
            num_tools = len(tool_calls)
            
            # Use the model capabilities configuration
            from ai_whisperer.model_capabilities import get_model_capabilities
            capabilities = get_model_capabilities(model_id)
            
            supports_multi_tool = capabilities.get('multi_tool', False)
            supports_parallel = capabilities.get('parallel_tools', False)
            max_tools = capabilities.get('max_tools_per_turn', 1)
            
            if num_tools == 0:
                return f"NO_TOOLS ({model_id})"
            elif num_tools == 1:
                if supports_multi_tool:
                    return f"MULTI_TOOL_MODEL_SINGLE_CALL ({model_id})"
                else:
                    return f"SINGLE_TOOL_MODEL_SINGLE_CALL ({model_id})"
            else:  # num_tools > 1
                if supports_multi_tool and supports_parallel:
                    return f"MULTI_TOOL_MODEL_PARALLEL ({model_id}) - {num_tools} tools"
                elif supports_multi_tool and not supports_parallel:
                    return f"MULTI_TOOL_MODEL_SEQUENTIAL ({model_id}) - {num_tools} tools"
                else:
                    return f"SINGLE_TOOL_MODEL_ERROR ({model_id}) - {num_tools} tools requested but max is {max_tools}"
                
        except Exception as e:
            return f"STRATEGY_ERROR: {str(e)}"
    
    async def _process_stream(
        self,
        stream: AsyncIterator,
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process the AI response stream.
        
        Args:
            stream: The AI response stream
            on_stream_chunk: Optional callback for each chunk
            response_format: Optional response format used for structured output
            
        Returns:
            Dict with response data
        """
        full_response = ""
        full_reasoning = ""  # Accumulate reasoning tokens separately
        tool_accumulator = ToolCallAccumulator()
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
                
                # Process reasoning tokens
                if hasattr(chunk, 'delta_reasoning') and chunk.delta_reasoning:
                    full_reasoning += chunk.delta_reasoning
                    # For now, also stream reasoning as content to maintain compatibility
                    if on_stream_chunk:
                        await on_stream_chunk(chunk.delta_reasoning)
                
                # Accumulate tool calls
                if chunk.delta_tool_call_part:
                    if isinstance(chunk.delta_tool_call_part, list):
                        # Add tool call chunks to accumulator
                        tool_accumulator.add_chunk(chunk.delta_tool_call_part)
                    else:
                        # Log unexpected format
                        logger.warning(f"Unexpected tool call format: {type(chunk.delta_tool_call_part)}")
                
                # Track finish reason
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
            
            logger.info(f"🔄 STREAM FINISHED: finish_reason={finish_reason}, response_length={len(full_response)}, reasoning_length={len(full_reasoning)}")
            
            # DEBUG: Log if we got an empty response but have reasoning
            if len(full_response) == 0 and len(full_reasoning) == 0:
                logger.error(f"🚨 EMPTY RESPONSE AND REASONING! finish_reason={finish_reason}, last_chunk={last_chunk}")
            elif len(full_response) == 0 and len(full_reasoning) > 0:
                logger.warning(f"⚠️ Empty response but got {len(full_reasoning)} chars of reasoning")
            
            # Send final chunk notification
            if on_stream_chunk:
                final_content = last_chunk.delta_content if last_chunk and last_chunk.delta_content else ""
                logger.info(f"🔄 SENDING FINAL CHUNK: length={len(final_content)}")
                await on_stream_chunk(final_content)
            
            # Get tool calls if present
            tool_calls = None
            if finish_reason == "tool_calls":
                tool_calls = tool_accumulator.get_tool_calls()
                if tool_calls:
                    logger.info(f"Accumulated {len(tool_calls)} tool calls")
            
            # Execute tool calls if present
            tool_results_list = None
            if tool_calls:
                logger.info(f"🔧 EXECUTING TOOLS: Found {len(tool_calls)} tool calls")
                for i, tool_call in enumerate(tool_calls):
                    logger.info(f"   Tool {i+1}: {tool_call.get('function', {}).get('name', 'unknown')}")
                
                # Determine tool execution strategy
                tool_strategy = self._determine_tool_strategy(tool_calls)
                logger.info(f"🔧 TOOL STRATEGY: {tool_strategy}")
                
                tool_results_list = await self._execute_tool_calls(tool_calls)
                logger.info(f"🔧 TOOL EXECUTION COMPLETE: {len(tool_results_list)} results")
                
                # Don't append tool results to the response - they'll be handled separately
                # The AI will process them from the tool messages
                
            logger.info(f"🔄 RETURNING RESULT: response_length={len(full_response)}, reasoning_length={len(full_reasoning)}, tool_calls={len(tool_calls) if tool_calls else 0}")
            
            # Apply postprocessing if we have a JSON response that might be wrapped in markdown
            processed_response = full_response
            if full_response and self._should_apply_postprocessing(full_response):
                processed_response = self._postprocess_response(full_response)
                if processed_response != full_response:
                    logger.debug("Applied postprocessing to clean response")
            
            return {
                'response': processed_response,
                'reasoning': full_reasoning if full_reasoning else None,
                'finish_reason': finish_reason,
                'tool_calls': tool_calls,
                'tool_results': tool_results_list,  # Return the raw tool results
                'error': None,
                'used_structured_output': response_format is not None  # Track if structured output was used
            }
            
        except Exception as e:
            logger.exception("Error processing stream")
            return {
                'response': full_response if full_response else None,
                'reasoning': full_reasoning if full_reasoning else None,
                'finish_reason': 'error',
                'tool_calls': None,
                'error': e
            }
    
    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Any]:
        """
        Execute tool calls and return raw results.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            List of raw tool results (preserving their original structure)
        """
        tool_registry = get_tool_registry()
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                # Extract tool call information
                tool_id = tool_call.get('id', 'unknown')
                function_info = tool_call.get('function', {})
                tool_name = function_info.get('name')
                tool_args_str = function_info.get('arguments', '{}')
                
                logger.info(f"🔧 EXECUTING TOOL {i+1}/{len(tool_calls)}: {tool_name} (ID: {tool_id})")
                
                if not tool_name:
                    logger.error(f"Tool call {tool_id} missing function name")
                    results.append({"error": f"Missing function name for tool call {tool_id}"})
                    continue
                
                # Parse arguments
                try:
                    tool_args = json.loads(tool_args_str) if tool_args_str else {}
                    logger.info(f"   Args: {tool_args}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse arguments for tool {tool_name}: {e}")
                    results.append({"error": f"Invalid arguments for {tool_name}: {str(e)}"})
                    continue
                
                # Get tool instance
                tool_instance = tool_registry.get_tool_by_name(tool_name)
                if not tool_instance:
                    logger.error(f"Tool {tool_name} not found in registry")
                    results.append({"error": f"Tool '{tool_name}' not found"})
                    continue
                
                # Execute tool
                start_time = asyncio.get_event_loop().time()
                logger.info(f"   🔄 Starting execution...")
                
                # Add agent context to tool args if available
                if self.agent_context:
                    # Create a copy of tool_args to avoid modifying the original
                    enriched_args = tool_args.copy()
                    # Add agent context parameters
                    if 'agent_id' in self.agent_context:
                        enriched_args['_agent_id'] = self.agent_context['agent_id']
                    if 'agent_name' in self.agent_context:
                        enriched_args['_agent_name'] = self.agent_context['agent_name']
                        enriched_args['_from_agent'] = self.agent_context['agent_name']
                else:
                    enriched_args = tool_args
                
                # Check if execute method is async
                if asyncio.iscoroutinefunction(tool_instance.execute):
                    # Try different calling conventions
                    try:
                        # First try the newer 'arguments' pattern (RFC tools, read_file_tool)
                        tool_result = await tool_instance.execute(arguments=enriched_args)
                    except TypeError:
                        # Fallback to **kwargs pattern (base_tool, execute_command_tool, write_file_tool)
                        tool_result = await tool_instance.execute(**enriched_args)
                else:
                    # Try different calling conventions
                    try:
                        # First try the newer 'arguments' pattern (RFC tools, read_file_tool)
                        tool_result = tool_instance.execute(arguments=enriched_args)
                    except TypeError:
                        # Fallback to **kwargs pattern (base_tool, execute_command_tool, write_file_tool)
                        tool_result = tool_instance.execute(**enriched_args)
                
                execution_time = asyncio.get_event_loop().time() - start_time
                logger.info(f"   ✅ Tool {tool_name} completed in {execution_time:.3f}s")
                
                # Return the raw tool result - no formatting, no conversion
                # The AI will receive exactly what the tool returned
                results.append(tool_result)
                
                logger.info(f"Tool {tool_name} executed successfully")
                
            except Exception as e:
                logger.exception(f"Error executing tool call {tool_call}: {e}")
                tool_name = tool_call.get('function', {}).get('name', 'unknown')
                results.append({"error": f"Failed to execute {tool_name}: {str(e)}"})
        
        return results
    
    def _should_apply_postprocessing(self, response: str) -> bool:
        """
        Check if postprocessing should be applied to clean markdown wrappers.
        
        Args:
            response: The AI response string
            
        Returns:
            True if response appears to be JSON wrapped in markdown
        """
        if not response:
            return False
            
        # Check if response starts with markdown code block
        response_stripped = response.strip()
        return response_stripped.startswith('```json') or response_stripped.startswith('```')
    
    def _postprocess_response(self, response: str) -> str:
        """
        Apply postprocessing to clean markdown wrappers from JSON responses.
        
        Args:
            response: The AI response string
            
        Returns:
            Cleaned response with markdown wrappers removed
        """
        try:
            # Use the same regex pattern as clean_backtick_wrapper
            cleaned = re.sub(r"^```[a-zA-Z]*\n?(.*)\n?```$", r"\1", response.strip(), flags=re.DOTALL)
            
            # Validate it's valid JSON after cleaning
            try:
                json.loads(cleaned)
                logger.debug("Successfully cleaned markdown wrapper from JSON response")
                return cleaned
            except json.JSONDecodeError:
                # If it's not valid JSON after cleaning, return original
                logger.debug("Cleaned response is not valid JSON, returning original")
                return response
                
        except Exception as e:
            logger.error(f"Error in postprocessing response: {e}")
            return response
