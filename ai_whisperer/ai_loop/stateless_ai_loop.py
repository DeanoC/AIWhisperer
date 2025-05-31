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
from ai_whisperer.ai_loop.tool_call_accumulator import ToolCallAccumulator

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

    def _get_validated_message_history(self, context_provider: ContextProvider) -> List[Dict[str, Any]]:
        """Retrieves and validates message history from the context provider."""
        messages = context_provider.retrieve_messages()
        logger.debug(f"🔍 RETRIEVED MESSAGES COUNT: {len(messages)}")
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                content = msg.get('content', '')
                content_preview = (content[:50] + '...' if len(content) > 50 else content) if isinstance(content, str) else (str(content)[:50] + '...')
                logger.debug(f"🔍 MESSAGE {i}: role={msg.get('role', 'unknown')} content={content_preview}")
            else:
                logger.debug(f"🔍 MESSAGE {i}: {type(msg)} {str(msg)[:50]}...")

        validated_messages = []
        for msg in messages:
            if isinstance(msg, str):
                logger.warning(f"Found string message in context, converting to dict: {msg[:100]}...")
                validated_messages.append({"role": "user", "content": msg})
            elif isinstance(msg, dict):
                validated_messages.append(msg)
            else:
                logger.error(f"Found unexpected message type in context: {type(msg)}")
                continue
        return validated_messages

    async def _execute_stream_with_retry(
        self,
        working_messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        on_stream_chunk: Optional[Callable[[str], Any]],
        timeout: Optional[float],
        generation_params: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Executes the AI stream with retry logic for empty responses."""

        async def run_stream_once():
            logger.debug(f"🚨 SENDING TO AI: {len(working_messages)} messages")
            for i, msg in enumerate(working_messages):
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                preview = content[:100] + '...' if len(content) > 100 else content
                logger.debug(f"🚨 MSG[{i}] role={role} content={preview}")

            params = {**self.config.__dict__, **generation_params}
            stream = self.ai_service.stream_chat_completion(
                messages=working_messages,
                tools=tools,
                **params
            )
            return await self._process_stream(stream, on_stream_chunk)

        retry_count = 0
        response_data = {}

        while retry_count < max_retries:
            if timeout:
                response_data = await asyncio.wait_for(run_stream_once(), timeout=timeout)
            else:
                response_data = await run_stream_once()

            is_empty_response = (
                not response_data.get('error') and
                not response_data.get('response') and
                not response_data.get('reasoning') and
                not response_data.get('tool_calls') and
                response_data.get('finish_reason') == 'stop'
            )

            if is_empty_response:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Empty response received, retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(1.0 * retry_count)  # Exponential backoff
                    continue
                else:
                    logger.error(f"Empty response persists after {max_retries} retries.")

            is_reasoning_only_response = (
                not response_data.get('error') and
                not response_data.get('response') and
                response_data.get('reasoning')
            )
            if is_reasoning_only_response: # Valid, don't retry
                logger.info(f"Got reasoning-only response: {len(response_data.get('reasoning', ''))} chars")
                if response_data.get('reasoning'): # Combine for backward compatibility
                    response_data['response'] = response_data['reasoning']

            break # Got a valid response or an error, or max retries reached

        return response_data

    async def process_with_context(
        self,
        message: str,
        context_provider: ContextProvider,
        on_stream_chunk: Optional[Callable[[str], Any]] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        timeout: Optional[float] = None, # Overall timeout for the operation
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
            timeout: Optional overall timeout for this operation, including retries.
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
            messages = self._get_validated_message_history(context_provider)
            
            # Note: first_role logging is already inside _get_validated_message_history
            # if messages and isinstance(messages[0], dict):
            #     first_role = messages[0].get('role', 'unknown')
            # else:
            #     first_role = 'N/A'
            # logger.debug(f"Processing with {len(messages)} messages, first message role: {first_role}")
            
            working_messages = messages + [{"role": "user", "content": message}]
            
            if tools is None:
                tools = get_tool_registry().get_all_tool_definitions()

            # The timeout for _execute_stream_with_retry is per attempt.
            # The overall timeout for process_with_context is handled by the outer try/except.
            # If a per-attempt timeout is also desired for the AI call itself,
            # it should be part of the 'timeout' argument passed to _execute_stream_with_retry's
            # own asyncio.wait_for, or handled by the AIService if it supports it.
            # For now, let's assume the 'timeout' here is for the whole process_with_context.

            async def main_operation():
                response_data = await self._execute_stream_with_retry(
                    working_messages=working_messages,
                    tools=tools,
                    on_stream_chunk=on_stream_chunk,
                    timeout=self.config.get("ai_call_timeout", 60.0), # Per-attempt timeout for AI call
                    generation_params=generation_params
                )
                result.update(response_data)
            
            if timeout: # Overall timeout for the entire process_with_context
                await asyncio.wait_for(main_operation(), timeout=timeout)
            else:
                await main_operation()

            # Use the result that was updated by main_operation()
            self._handle_atomic_message_storage(context_provider, message, result, store_messages)
                
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

    def _handle_atomic_message_storage(
        self,
        context_provider: ContextProvider,
        original_user_message: str,
        response_data: Dict[str, Any], # This should be the 'result' dict
        store_messages_flag: bool
    ):
        """Handles the atomic storage of user, assistant, and tool messages."""
        if not store_messages_flag:
            return

        has_valid_response = (
            not response_data.get('error') and
            (response_data.get('response') or
             response_data.get('reasoning') or
             response_data.get('tool_calls'))
        )

        if has_valid_response:
            logger.info(f"✅ ATOMIC: Storing user message and assistant response")
            user_msg_to_store = {"role": "user", "content": original_user_message}
            context_provider.store_message(user_msg_to_store)

            assistant_message = {"role": "assistant"}
            if response_data.get('response'):
                assistant_message['content'] = response_data['response']
            elif response_data.get('reasoning'):
                assistant_message['content'] = response_data['reasoning']

            if response_data.get('reasoning'): # Store reasoning separately if available
                assistant_message['reasoning'] = response_data['reasoning']

            if response_data.get('tool_calls'):
                assistant_message['tool_calls'] = response_data['tool_calls']

            context_provider.store_message(assistant_message)

            # If there were tool calls AND a response that is meant to be the textual result of those calls
            if response_data.get('tool_calls') and response_data.get('response') and response_data.get('finish_reason') != 'tool_calls':
                tool_results_text = response_data['response']
                for tool_call in response_data['tool_calls']:
                    tool_name = tool_call.get('function', {}).get('name', 'unknown')
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.get('id'),
                        "name": tool_name,
                        "content": tool_results_text
                    }
                    context_provider.store_message(tool_message)
                    logger.info(f"🔄 STORED TOOL RESULT for {tool_name} (ID: {tool_call.get('id')}) based on response text")
        else:
            logger.warning(f"❌ ATOMIC: Not storing messages due to empty/error response")
            if response_data.get('error'):
                logger.error(f"   Error: {response_data.get('error')}")
            else:
                # Consider what max_retries was for this call if logging empty response after retries
                logger.error(f"   Empty response or no tool calls after retries (if applicable)")

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
                # LOG EXACTLY WHAT MESSAGES WE'RE SENDING TO THE AI
                logger.error(f"🚨 SENDING TO AI: {len(messages)} messages")
                for i, msg in enumerate(messages):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    preview = content[:100] + '...' if len(content) > 100 else content
                    logger.error(f"🚨 MSG[{i}] role={role} content={preview}")
                
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

    async def _iterate_and_accumulate_stream(self, stream: AsyncIterator, on_stream_chunk: Optional[Callable[[str], Any]]):
        """Iterates through the AI stream, accumulates parts, and calls on_stream_chunk."""
        full_response_content = ""
        full_reasoning_content = ""
        tool_accumulator = ToolCallAccumulator()
        stream_finish_reason = None
        last_chunk_for_notification = None # To get final delta_content for notification

        async for chunk in stream:
            last_chunk_for_notification = chunk # Keep track of the last seen chunk
            if chunk.delta_content:
                full_response_content += chunk.delta_content
                if on_stream_chunk:
                    await on_stream_chunk(chunk.delta_content)

            if hasattr(chunk, 'delta_reasoning') and chunk.delta_reasoning:
                full_reasoning_content += chunk.delta_reasoning
                if on_stream_chunk: # Also stream reasoning for now
                    await on_stream_chunk(chunk.delta_reasoning)

            if chunk.delta_tool_call_part:
                if isinstance(chunk.delta_tool_call_part, list):
                    tool_accumulator.add_chunk(chunk.delta_tool_call_part)
                else:
                    logger.warning(f"Unexpected tool call format: {type(chunk.delta_tool_call_part)}")

            if chunk.finish_reason:
                stream_finish_reason = chunk.finish_reason

        return (
            full_response_content,
            full_reasoning_content,
            tool_accumulator,
            stream_finish_reason,
            last_chunk_for_notification # Return last_chunk itself
        )

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
        accumulated_full_response = ""
        accumulated_full_reasoning = ""
        final_tool_calls = None
        final_finish_reason = "unknown"
        
        try:
            if hasattr(stream, '__await__'):
                stream = await stream
            
            (iter_full_response,
             iter_full_reasoning,
             tool_accumulator,
             iter_finish_reason,
             last_chunk_for_notification) = await self._iterate_and_accumulate_stream(stream, on_stream_chunk)

            accumulated_full_response = iter_full_response
            accumulated_full_reasoning = iter_full_reasoning
            final_finish_reason = iter_finish_reason

            logger.info(f"🔄 STREAM FINISHED: finish_reason={final_finish_reason}, response_length={len(accumulated_full_response)}, reasoning_length={len(accumulated_full_reasoning)}")
            if len(accumulated_full_response) == 0 and len(accumulated_full_reasoning) == 0:
                logger.error(f"🚨 EMPTY RESPONSE AND REASONING! finish_reason={final_finish_reason}, last_chunk={last_chunk_for_notification}")
            elif len(accumulated_full_response) == 0 and len(accumulated_full_reasoning) > 0:
                logger.warning(f"⚠️ Empty response but got {len(accumulated_full_reasoning)} chars of reasoning")

            if on_stream_chunk:
                final_content = last_chunk_for_notification.delta_content if last_chunk_for_notification and last_chunk_for_notification.delta_content else ""
                logger.info(f"🔄 SENDING FINAL CHUNK: length={len(final_content)}")
                await on_stream_chunk(final_content)
            
            if final_finish_reason == "tool_calls":
                final_tool_calls = tool_accumulator.get_tool_calls()
                if final_tool_calls:
                    logger.info(f"Accumulated {len(final_tool_calls)} tool calls")
                    tool_strategy = self._determine_tool_strategy(final_tool_calls)
                    logger.info(f"🔧 TOOL STRATEGY: {tool_strategy}")

                    tool_results_text = await self._execute_tool_calls(final_tool_calls)
                    logger.info(f"🔧 TOOL EXECUTION COMPLETE: result_length={len(str(tool_results_text))}")
                    accumulated_full_response += tool_results_text

                    if on_stream_chunk and tool_results_text:
                        logger.info(f"🔄 STREAMING TOOL RESULTS: length={len(str(tool_results_text))}")
                        await on_stream_chunk(tool_results_text)
                        logger.info(f"🔄 TOOL RESULTS STREAMED")
            
            logger.info(f"🔄 RETURNING RESULT: response_length={len(accumulated_full_response)}, reasoning_length={len(accumulated_full_reasoning)}, tool_calls={len(final_tool_calls) if final_tool_calls else 0}")
            return {
                'response': accumulated_full_response,
                'reasoning': accumulated_full_reasoning if accumulated_full_reasoning else None,
                'finish_reason': final_finish_reason,
                'tool_calls': final_tool_calls,
                'error': None
            }
            
        except Exception as e:
            logger.exception("Error processing stream")
            return {
                'response': accumulated_full_response if accumulated_full_response else None,
                'reasoning': accumulated_full_reasoning if accumulated_full_reasoning else None,
                'finish_reason': 'error',
                'tool_calls': None,
                'error': e
            }

    async def _actually_execute_tool_with_variants(self, tool_instance: Any, tool_args: Dict[str, Any]) -> Any:
        """Handles the actual execution of a tool, trying different calling conventions."""
        if asyncio.iscoroutinefunction(tool_instance.execute):
            try:
                return await tool_instance.execute(arguments=tool_args)
            except TypeError:
                return await tool_instance.execute(**tool_args)
        else:
            try:
                return tool_instance.execute(arguments=tool_args)
            except TypeError:
                return tool_instance.execute(**tool_args)

    async def _execute_single_tool_and_format_result(self, tool_call: Dict[str, Any], tool_number: int, total_tools: int) -> str:
        """Executes a single tool call and returns its formatted result string."""
        tool_registry = get_tool_registry()
        tool_id = tool_call.get('id', 'unknown')
        function_info = tool_call.get('function', {})
        tool_name = function_info.get('name')
        tool_args_str = function_info.get('arguments', '{}')

        logger.info(f"🔧 EXECUTING TOOL {tool_number}/{total_tools}: {tool_name} (ID: {tool_id})")

        if not tool_name:
            logger.error(f"Tool call {tool_id} missing function name")
            return f"\n\n🔧 Tool Error: Missing function name for tool call {tool_id}"

        try:
            tool_args = json.loads(tool_args_str) if tool_args_str else {}
            logger.info(f"   Args: {tool_args}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse arguments for tool {tool_name}: {e}")
            return f"\n\n🔧 Tool Error: Invalid arguments for {tool_name}: {e}"

        tool_instance = tool_registry.get_tool_by_name(tool_name)
        if not tool_instance:
            logger.error(f"Tool {tool_name} not found in registry")
            return f"\n\n🔧 Tool Error: Tool '{tool_name}' not found"

        try:
            start_time = asyncio.get_event_loop().time()
            logger.info(f"   🔄 Starting execution...")

            tool_result = await self._actually_execute_tool_with_variants(tool_instance, tool_args)

            execution_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"   ✅ Tool {tool_name} completed in {execution_time:.3f}s")
            logger.info(f"Tool {tool_name} executed successfully")
            return f"\n\n🔧 **{tool_name}** executed:\n{str(tool_result)}"
        except Exception as e:
            logger.exception(f"Error executing tool call {tool_call}: {e}")
            return f"\n\n🔧 Tool Error: Failed to execute {tool_name}: {str(e)}"

    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> str:
        """
        Execute tool calls and return formatted results.
        
        Args:
            tool_calls: List of tool call dictionaries
            
        Returns:
            String containing formatted tool results
        """
        results = []
        for i, tool_call in enumerate(tool_calls):
            result_str = await self._execute_single_tool_and_format_result(tool_call, i + 1, len(tool_calls))
            results.append(result_str)
        return "".join(results)