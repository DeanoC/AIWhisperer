import asyncio
import json
import logging
import enum
from typing import AsyncIterator

from ai_whisperer.context_management import ContextManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.ai_service.ai_service import AIService
from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.tools.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)

class SessionState(enum.Enum):
    WAIT_FOR_INPUT = 1
    PROCESS_TOOL_RESULT = 2
    ASSEMBLE_AI_STREAM = 3
    SHUTDOWN = 4
    NOT_STARTED = 5

class AILoop:
    def __init__(self, config: AIConfig, ai_service: AIService, context_manager: ContextManager, delegate_manager: DelegateManager):
        self.config = config
        self.ai_service = ai_service
        self.context_manager = context_manager
        self.delegate_manager = delegate_manager
        self.shutdown_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        self.pause_event.set() # Start in unpaused state
        self._user_message_queue = asyncio.Queue()
        self._tool_result_queue = asyncio.Queue()
        self._user_input_event = asyncio.Event() # Event to signal new user input or tool result
        self._session_task = None
        self._tool_registry = None # To be set during start_session if provided
        self._state = SessionState.NOT_STARTED
        
        # Subscribe to control delegates
        self.delegate_manager.register_control("ai_loop.control.start", self._handle_start_session)
        self.delegate_manager.register_control("ai_loop.control.stop", self._handle_stop_session)
        self.delegate_manager.register_control("ai_loop.control.pause", self._handle_pause_session)
        self.delegate_manager.register_control("ai_loop.control.resume", self._handle_resume_session)
        self.delegate_manager.register_control("ai_loop.control.send_user_message", self._handle_send_user_message)
        self.delegate_manager.register_control("ai_loop.control.provide_tool_result", self._handle_provide_tool_result)

    async def start_session(self, system_prompt: str):
        if self._session_task is not None and not self._session_task.done():
            logger.debug("AILoop session already running.")
            return self._session_task

        self.context_manager.clear_history()
        self.context_manager.add_message({"role": "system", "content": system_prompt})
        self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.session_started")

        self._session_task = asyncio.create_task(self._run_session())
        logger.debug(f"start_session: _session_task created: {self._session_task}")
        return self._session_task
    
    def is_waiting_for_input(self) -> bool:
        if self._session_task is None or self._session_task.done():
            return False
        return self._state == SessionState.WAIT_FOR_INPUT

    async def wait_for_idle(self, timeout: float = None):
        """
        Wait until the session state is WAIT_FOR_INPUT and both queues are empty.
        Optionally specify a timeout in seconds.
        """
        async def is_idle():
            return (
                self._state == SessionState.WAIT_FOR_INPUT and
                self._user_message_queue.empty() and
                self._tool_result_queue.empty()
            )

        async def wait_loop():
            while not await is_idle():
                await asyncio.sleep(0.05)

        if timeout is not None:
            await asyncio.wait_for(wait_loop(), timeout=timeout)
        else:
            await wait_loop()
            
    async def _run_session(self):
        finish_reason = "unknown" # Track the finish reason of the last AI call
        logger.debug("_run_session: Session started.")
        max_iterations = 1000 # Set a high limit to prevent infinite loops during debugging
        iteration_count = 0
        
        if(self._session_task is None):
            raise ValueError("AILoop session hasn't started or hasn't been reset")
        if(self._state != SessionState.NOT_STARTED):
            raise ValueError("AILoop session already started or in progress.")
        
        self._state = SessionState.WAIT_FOR_INPUT

        try:
            while iteration_count < max_iterations: # Use a counter to prevent infinite loops
                iteration_count += 1
                logger.debug(f"_run_session: Iteration {iteration_count}, State: {self._state}")

                await self.pause_event.wait()

                if self._state == SessionState.WAIT_FOR_INPUT:
                    # Check queues for user or tool input
                    processed_queue_item = False
                    try:
                        user_message = self._user_message_queue.get_nowait()
                        self.context_manager.add_message({"role": "user", "content": user_message})
                        self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
                        processed_queue_item = True
                    except asyncio.QueueEmpty:
                        pass

                    if not processed_queue_item:
                        try:
                            tool_result = self._tool_result_queue.get_nowait()
                            if tool_result is None:
                                processed_queue_item = True
                            else:
                                self.context_manager.add_message({"role": "tool", "content": tool_result})
                                self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                                processed_queue_item = True
                        except asyncio.QueueEmpty:
                            pass

                    if not processed_queue_item:
                        user_task = asyncio.create_task(self._user_message_queue.get())
                        tool_task = asyncio.create_task(self._tool_result_queue.get())
                        done, pending = await asyncio.wait(
                            [user_task, tool_task],
                            return_when=asyncio.FIRST_COMPLETED
                        )
                        for task in pending:
                            task.cancel()
                        result_task = done.pop()
                        if result_task is user_task:
                            user_message = user_task.result()
                            self.context_manager.add_message({"role": "user", "content": user_message})
                            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
                        else:
                            tool_result = tool_task.result()
                            if tool_result is None:
                                pass
                            else:
                                self.context_manager.add_message({"role": "tool", "content": tool_result})
                                self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                    # After processing input, move to AI stream state if not shutting down
                    if not self.shutdown_event.is_set():
                        self._state = SessionState.ASSEMBLE_AI_STREAM
                    else:
                        self._state = SessionState.SHUTDOWN

                elif self._state == SessionState.ASSEMBLE_AI_STREAM:
                    # Prepare AI call arguments
                    messages = self.context_manager.get_history()
                    tools_for_model = get_tool_registry().get_all_tool_definitions()

                    ai_response_stream = self.ai_service.stream_chat_completion(
                        messages=messages,
                        tools=tools_for_model,
                        **self.config.__dict__
                    )
                    finish_reason = await self._assemble_ai_stream(ai_response_stream)
                    if finish_reason == "tool_calls":
                        self._state = SessionState.PROCESS_TOOL_RESULT
                    elif finish_reason == "error":
                        self._state = SessionState.SHUTDOWN
                    else:
                        self._state = SessionState.WAIT_FOR_INPUT

                elif self._state == SessionState.PROCESS_TOOL_RESULT:
                    # Wait for tool result to be provided
                    tool_result = await self._tool_result_queue.get()
                    if tool_result is None:
                        self._state = SessionState.SHUTDOWN
                    else:
                        self.context_manager.add_message({"role": "tool", "content": tool_result})
                        self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                        self._state = SessionState.ASSEMBLE_AI_STREAM

                elif self._state == SessionState.SHUTDOWN:
                    logger.debug("_run_session: Shutdown requested or finished. Stopping loop.")
                    break
            else:
                logger.debug(f"_run_session: Exited loop after reaching max_iterations={max_iterations}.")
        except asyncio.CancelledError:
            logger.debug("_run_session: CancelledError caught, coroutine was cancelled externally.")
            finish_reason = "cancelled"
            raise  # Re-raise so cancellation propagates
        except Exception as e:
            logger.exception("AILoop encountered an error:")
            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
            finish_reason = "error"
        finally:
            logger.debug(f"_run_session: Loop finished. Checking shutdown_event.")
            # Determine the final finish reason based on shutdown state and last AI interaction
            if self.shutdown_event.is_set():
                final_finish_reason = "stopped"
            elif finish_reason == "error":
                 final_finish_reason = "error"
            else:
                 final_finish_reason = "unknown"

            logger.debug(f"AILoop session ended with reason: {final_finish_reason}")
            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.session_ended", event_data=final_finish_reason)
            self._session_task = None

    async def _assemble_ai_stream(self, ai_response_stream):
        """
        Assemble the AI stream, add messages to context, emit events, and return finish_reason.
        """
        full_response_content = ""
        accumulated_tool_calls_part = ""
        tool_calls = []
        finish_reason = None

        if isinstance(ai_response_stream, AsyncIterator):
            logger.debug("_run_session: Processing AI stream.")
            async for chunk in ai_response_stream:
                logger.debug(f"_run_session: Received chunk: {chunk}")
                if chunk.delta_content:
                    full_response_content += chunk.delta_content
                    self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.ai_chunk_received", event_data=chunk.delta_content)

                if chunk.delta_tool_call_part:
                    accumulated_tool_calls_part += chunk.delta_tool_call_part

                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                    logger.debug(f"_run_session: Received finish_reason: {finish_reason}")

            # After streaming, process the full response and identified tool calls
            logger.debug(f"_run_session: full_response_content after stream: '{full_response_content}'")
            if full_response_content:
                self.context_manager.add_message({"role": "assistant", "content": full_response_content})
                logger.debug("_run_session: Assistant message added to context.")

            if finish_reason == "tool_calls":
                # Attempt to parse accumulated tool call parts into ToolCall objects
                try:
                    logger.debug(f"_run_session: Attempting to parse accumulated_tool_calls_part: '{accumulated_tool_calls_part}'")
                    parsed_response_object = json.loads(accumulated_tool_calls_part)
                    logger.debug(f"_run_session: Parsed response object: {parsed_response_object}")
                    if "tool_calls" in parsed_response_object and isinstance(parsed_response_object["tool_calls"], list):
                        logger.debug(f"_run_session: Found 'tool_calls' list in parsed object: {parsed_response_object['tool_calls']}")
                        for tc in parsed_response_object["tool_calls"]:
                            name = tc["function"]["name"]
                            args = tc["function"]["arguments"]
                            tool_calls.append(name)
                            self._tool_result_queue.put_nowait(get_tool_registry().get_tool_by_name(name).execute(args))

                        logger.debug(f"_run_session: Identified tool calls from stream: {tool_calls}")
                    else:
                        logger.warning("_run_session: Parsed tool calls JSON does not contain a 'tool_calls' list.")
                except json.JSONDecodeError as e:
                    logger.error(f"_run_session: Failed to parse tool calls JSON: {e}")
                    pass
                except TypeError as e:
                    logger.error(f"_run_session: TypeError during ToolCall instantiation: {e}")
                    pass

                if tool_calls:
                    self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.identified", event_data=tool_calls)
                    # The loop will continue to the next iteration and wait for the tool result via _tool_result_queue.get()
                else:
                    logger.debug("_run_session: Finish reason is 'tool_calls' but no tool calls were parsed.")


            # If finish_reason is "stop" or "error", the loop should now break if queues are empty
            # If finish_reason is not "stop", "error", or "tool_calls", the loop continues.
            logger.debug(f"_run_session: AI call finished with reason: {finish_reason}. Checking queues for pending messages.")

        else: # Non-streaming response (shouldn't happen with stream=True in this implementation)
            raise ValueError("Expected ai_response_stream to be an AsyncIterator, got a non-streaming response.")

        return finish_reason

    async def stop_session(self):
        logger.debug(f"stop_session: called. _session_task: {self._session_task}")
        self.shutdown_event.set()
        self.pause_event.set()
        await self._user_message_queue.put(None) # Unblock pending get
        await self._tool_result_queue.put(None) # Unblock pending get

        if self._session_task:
            try:
                logger.debug(f"stop_session: waiting for _session_task: {self._session_task}")
                self._user_input_event.set()
                await asyncio.wait_for(self._session_task, timeout=5.0)
                logger.debug("AILoop session task finished.")
            except asyncio.TimeoutError:
                logger.debug("AILoop session task did not finish within timeout, cancelling.")
                if self._session_task:
                    self._session_task.cancel()
                    try:
                        await self._session_task
                    except asyncio.CancelledError:
                        logger.debug("AILoop session task cancelled.")
                else:
                    logger.debug("stop_session: _session_task was None after timeout.")
            self._session_task = None

    async def pause_session(self):
        if self.pause_event.is_set():
            logger.debug("Pausing AILoop session...")
            self.pause_event.clear()
            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.status.paused")
        else:
            logger.debug("AILoop session is already paused.")

    async def resume_session(self):
        if not self.pause_event.is_set():
            logger.debug("Resuming AILoop session...")
            self.pause_event.set()
            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.status.resumed")
        else:
            logger.debug("AILoop session is already running.")

    async def send_user_message(self, message: str):
        logger.debug(f"Received user message: {message}")
        await self._user_message_queue.put(message)
        self._user_input_event.set() # Signal that new user input is available

    async def _handle_start_session(self, **kwargs):
        tool_registry = kwargs.get("tool_registry")
        await self.start_session(tool_registry)

    async def _handle_stop_session(self, **kwargs):
        await self.stop_session()

    async def _handle_pause_session(self, **kwargs):
        await self.pause_session()

    async def _handle_resume_session(self, **kwargs):
        await self.resume_session()

    async def _handle_send_user_message(self, **kwargs):
        message = kwargs.get("message")
        if message:
            await self.send_user_message(message)
            self._user_input_event.set()

    async def _handle_provide_tool_result(self, **kwargs):
        result = kwargs.get("result")
        if result is not None:
            logger.debug(f"Received tool result via delegate: {result}")
            await self._tool_result_queue.put(result)
            self._user_input_event.set()

        # Try processing user message queue first
        processed_queue_item = False

        # Try user message queue first
        try:
            user_message = self._user_message_queue.get_nowait()
            self.context_manager.add_message({"role": "user", "content": user_message})
            self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
            processed_queue_item = True
            logger.debug("_run_session: Processed user message from queue.")
        except asyncio.QueueEmpty:
            pass

        # Try tool result queue if user message not processed
        if not processed_queue_item:
            try:
                tool_result = self._tool_result_queue.get_nowait()
                if tool_result is None:
                    processed_queue_item = True
                    logger.debug("_run_session: Received None from tool result queue, likely shutting down.")
                else:
                    self.context_manager.add_message({"role": "tool", "content": tool_result})
                    self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                    processed_queue_item = True
                    logger.debug("_run_session: Processed tool result from queue.")
            except asyncio.QueueEmpty:
                pass

        # If nothing was processed, wait for either queue
        if not processed_queue_item:
            logger.debug("_run_session: Both queues empty, waiting for input.")
            user_task = asyncio.create_task(self._user_message_queue.get())
            tool_task = asyncio.create_task(self._tool_result_queue.get())
            done, pending = await asyncio.wait(
                [user_task, tool_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
            result_task = done.pop()
            if result_task is user_task:
                user_message = user_task.result()
                self.context_manager.add_message({"role": "user", "content": user_message})
                self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
                logger.debug("_run_session: Processed user message from awaited queue.")
            else:
                tool_result = tool_task.result()
                if tool_result is None:
                    logger.debug("_run_session: Received None from awaited tool result queue, likely shutting down.")
                else:
                    self.context_manager.add_message({"role": "tool", "content": tool_result})
                    self.delegate_manager.invoke_notification(sender=self,event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                    logger.debug("_run_session: Processed tool result from awaited queue.")
