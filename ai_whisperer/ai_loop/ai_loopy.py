import asyncio
import json
import logging
import enum
import types
from typing import AsyncIterator

from ai_whisperer.context_management import ContextManager
# Delegate system removed
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
    """
    The core AI Loop orchestrates the interaction between the AI service,
    context management, and tool execution. It manages the session state,
    processes user messages and tool results, and handles AI responses,
    including streaming and tool calls.

    The AILoop emits the following delegate notifications:

    - ai_loop.session_started: Emitted when a new AI session begins.
      event_data: None

    - ai_loop.session_ended: Emitted when an AI session concludes.
      event_data: A string indicating the reason for termination (e.g., "stopped", "error", "unknown").

    - ai_loop.message.user_processed: Emitted when a user message is processed by the loop.
      event_data: The user message string.

    - ai_loop.message.ai_chunk_received: Emitted for each chunk of content received during AI streaming.
      event_data: The string content of the AI chunk.

    - ai_loop.tool_call.identified: Emitted when the AI response includes tool calls.
      event_data: A list of tool names identified in the AI response.

    - ai_loop.tool_call.result_processed: Emitted when the result of a tool call is processed and added to context.
      event_data: The tool result message dictionary (e.g., {"role": "tool", "tool_call_id": "...", "name": "...", "content": "..."}).

    - ai_loop.status.paused: Emitted when the AI loop session is paused.
      event_data: None

    - ai_loop.status.resumed: Emitted when the AI loop session is resumed.
      event_data: None

    - ai_loop.error: Emitted when an unhandled exception occurs within the AI loop.
      event_data: The exception object.
    """
    def __init__(self, config: AIConfig, ai_service: AIService, context_manager: ContextManager, delegate_manager=None, get_agent_id=None):
        """
        Initializes the AILoop with necessary components and sets up control delegate registrations.

        Args:
            config: AI configuration settings.
            ai_service: The AI service instance for chat completions.
            context_manager: Manages the conversation history.
            delegate_manager: Manages delegate notifications and control events.
        """
        self.config = config
        self.ai_service = ai_service
        self.context_manager = context_manager
        self.delegate_manager = delegate_manager
        self.get_agent_id = get_agent_id  # Function or lambda to get current agent_id
        self.shutdown_event = asyncio.Event()
        self.pause_event = asyncio.Event()
        self.pause_event.set() # Start in unpaused state
        self._user_message_queue = asyncio.Queue()
        self._tool_result_queue = asyncio.Queue()
        self._session_task = None
        self._tool_registry = None # To be set during start_session if provided
        self._state = SessionState.NOT_STARTED
        
        # Subscribe to control delegates
        self.delegate_manager.register_control("ai_loop.control.start", self._handle_start_session)

    async def _handle_wait_for_input_state(self) -> SessionState:
        shutdown_requested = await self._process_input_queues()
        if shutdown_requested or self.shutdown_event.is_set():
            logger.debug("_handle_wait_for_input_state: Shutdown requested, transitioning to SHUTDOWN")
            return SessionState.SHUTDOWN
        else:
            logger.debug("_handle_wait_for_input_state: Input processed, transitioning to ASSEMBLE_AI_STREAM")
            return SessionState.ASSEMBLE_AI_STREAM

    async def _handle_assemble_ai_stream_state(self) -> tuple[SessionState, str]:
        # This method calls _handle_ai_stream_assembly and then determines the
        # next state and the finish_reason to be used by _run_session.
        # _handle_ai_stream_assembly itself will set self._state based on its internal logic.

        finish_reason = await self._handle_ai_stream_assembly()
        self._last_ai_finish_reason = finish_reason # Store for _run_session's finally block

        # Determine next_state based on the finish_reason from stream assembly
        if finish_reason == "tool_calls":
            next_state = SessionState.PROCESS_TOOL_RESULT
        elif finish_reason in ["error", "timeout_error", "stream_exception", "cancelled", "stopped"]:
            next_state = SessionState.SHUTDOWN
        else: # "stop" from AI, or other normal completion
            next_state = SessionState.WAIT_FOR_INPUT

        return next_state # Only return next_state, finish_reason is on self


    async def _handle_process_tool_result_state(self) -> SessionState:
        tool_result_item = await self._tool_result_queue.get()
        # _handle_queued_item returns True if item is None (shutdown signal)
        is_shutdown_signal = await self._handle_queued_item(tool_result_item, "tool_result_queue (from _run_session state handler)")

        if is_shutdown_signal or self.shutdown_event.is_set():
            logger.debug("_handle_process_tool_result_state: Shutdown signal or event, transitioning to SHUTDOWN")
            return SessionState.SHUTDOWN
        else:
            logger.debug("_handle_process_tool_result_state: Tool result processed, transitioning to ASSEMBLE_AI_STREAM")
            return SessionState.ASSEMBLE_AI_STREAM

    async def _handle_queued_item(self, item: any, item_origin: str) -> bool:
        """
        Handles a single item retrieved from a queue (user message or tool result).
        Returns True if the item is a shutdown signal (None), False otherwise.
        """
        if item is None:
            logger.debug(f"_handle_queued_item: Shutdown signal received from {item_origin}.")
            return True # Shutdown signal

        agent_id = self.get_agent_id() if self.get_agent_id else 'default'

        if item_origin == "user_message_queue":
            if not isinstance(item, str):
                error_msg = f"Invalid item type in {item_origin}: Expected str, got {type(item)}."
                logger.error(error_msg)
                await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                return False # Not a shutdown, but an error handled.
            logger.debug(f"_handle_queued_item: Got user_message: {item}")
            self.context_manager.add_message({"role": "user", "content": item}, agent_id=agent_id)
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=item)

        elif item_origin == "tool_result_queue":
            if not isinstance(item, dict):
                error_msg = f"Invalid item type in {item_origin}: Expected dict, got {type(item)}."
                logger.error(error_msg)
                await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                return False # Not a shutdown, but an error handled.
            logger.debug(f"_handle_queued_item: Got tool_result: {item}")
            self.context_manager.add_message(item, agent_id=agent_id)
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=item)

        return False # Item processed, not a shutdown signal

    async def _process_input_queues(self):
        """Checks and processes user messages and tool results from their respective queues.
        Returns True if a shutdown signal (None) is received from any queue.
        """
        # Try nowait first
        try:
            user_message = self._user_message_queue.get_nowait()
            if await self._handle_queued_item(user_message, "user_message_queue"):
                return True # Shutdown signal
            return False # Item processed
        except asyncio.QueueEmpty:
            pass

        try:
            tool_result = self._tool_result_queue.get_nowait()
            if await self._handle_queued_item(tool_result, "tool_result_queue"):
                return True # Shutdown signal
            return False # Item processed
        except asyncio.QueueEmpty:
            pass

        # If no immediate items, wait for the first available item
        logger.debug("_process_input_queues: Waiting for input from user_message_queue or tool_result_queue.")
        user_task = asyncio.create_task(self._user_message_queue.get())
        tool_task = asyncio.create_task(self._tool_result_queue.get())
        done, pending = await asyncio.wait([user_task, tool_task], return_when=asyncio.FIRST_COMPLETED)

        for task in pending:
            task.cancel()

        result_task = done.pop()
        if result_task is user_task:
            return await self._handle_queued_item(user_task.result(), "user_message_queue (await)")
        else: # result_task is tool_task
            return await self._handle_queued_item(tool_task.result(), "tool_result_queue (await)")

    async def _handle_ai_stream_assembly(self):
        """Handles the AI stream assembly and processes its outcome.
        Returns the finish_reason from the AI stream.
        """
        messages = self.context_manager.get_history()
        tools_for_model = get_tool_registry().get_all_tool_definitions()
        logger.debug(f"_handle_ai_stream_assembly: Calling ai_service.stream_chat_completion with messages={len(messages)} tools")

        current_finish_reason = "unknown"
        try:
            async def run_stream():
                ai_response_stream = self.ai_service.stream_chat_completion(
                    messages=messages,
                    tools=tools_for_model,
                    **self.config.__dict__
                )
                try:
                    # Pass self.get_agent_id to _assemble_ai_stream if needed, or handle agent_id differently
                    return await self._assemble_ai_stream(ai_response_stream)
                except asyncio.CancelledError:
                    logger.error("run_stream: CancelledError caught, closing ai_response_stream")
                    if hasattr(ai_response_stream, 'aclose'):
                        await ai_response_stream.aclose()
                    raise

            # TODO: Make timeout configurable via self.config
            current_finish_reason = await asyncio.wait_for(run_stream(), timeout=self.config.get("ai_call_timeout", 10.0))
            logger.debug(f"_handle_ai_stream_assembly: Finished _assemble_ai_stream with finish_reason={current_finish_reason}")
            return current_finish_reason
        except asyncio.TimeoutError:
            logger.error("_handle_ai_stream_assembly: AI service call timed out.")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data="AI service timeout")
            error_msg_content = "AI service timeout: The AI did not respond in time."
            error_msg = {"role": "assistant", "content": error_msg_content}
            agent_id = self.get_agent_id() if self.get_agent_id else 'default'
            self.context_manager.add_message(error_msg, agent_id=agent_id)
            return "timeout_error" # Indicate a specific type of error
        except Exception as e:
            logger.exception("_handle_ai_stream_assembly: Error calling ai_service.stream_chat_completion:")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
            error_msg_content = f"An error occurred while processing the AI response: {e}"
            error_msg = {"role": "assistant", "content": error_msg_content}
            agent_id = self.get_agent_id() if self.get_agent_id else 'default'
            self.context_manager.add_message(error_msg, agent_id=agent_id)
            return "stream_exception" # Indicate a specific type of error
        self.delegate_manager.register_control("ai_loop.control.stop", self._handle_stop_session)
        self.delegate_manager.register_control("ai_loop.control.pause", self._handle_pause_session)
        self.delegate_manager.register_control("ai_loop.control.resume", self._handle_resume_session)
        self.delegate_manager.register_control("ai_loop.control.send_user_message", self._handle_send_user_message)
        self.delegate_manager.register_control("ai_loop.control.provide_tool_result", self._handle_provide_tool_result)

    async def start_session(self, system_prompt: str):
        """
        Starts a new AI session. Clears previous history, adds the system prompt,
        and begins the main session loop task.

        Args:
            system_prompt: The initial system message for the AI.

        Returns:
            The asyncio Task for the running session. Returns the existing task if already running.
        """
        if self._session_task is not None and not self._session_task.done():
            logger.debug("AILoop session already running.")
            return self._session_task

        self.context_manager.clear_history()
        agent_id = self.get_agent_id() if self.get_agent_id else 'default'
        import logging
        logging.error(f"[AILoop.start_session] Adding system prompt to context for agent_id={agent_id}: {system_prompt}")
        self.context_manager.add_message({"role": "system", "content": system_prompt}, agent_id=agent_id)
        await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.session_started")

        self._session_task = asyncio.create_task(self._run_session())
        logger.debug(f"start_session: _session_task created: {self._session_task}")
        return self._session_task
    
    def is_waiting_for_input(self) -> bool:
        """
        Checks if the AI loop is currently in the WAIT_FOR_INPUT state.

        Returns:
            True if the state is WAIT_FOR_INPUT and the session task is running, False otherwise.
        """
        if self._session_task is None or self._session_task.done():
            return False
        return self._state == SessionState.WAIT_FOR_INPUT

    async def wait_for_idle(self, timeout: float = None):
        """
        Waits until the AI loop session is in the WAIT_FOR_INPUT state and both
        the user message and tool result queues are empty.

        Args:
            timeout: Optional timeout in seconds. If provided, raises asyncio.TimeoutError
                     if the loop does not become idle within the specified time.
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
        self._last_ai_finish_reason = "unknown"
        logger.debug("_run_session: Session started.")
        max_iterations = 1000
        iteration_count = 0
        
        if self._session_task is None:
            logger.error("AILoop session task is None at the start of _run_session.")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=RuntimeError("Session task is None."))
            return
        if self._state != SessionState.NOT_STARTED:
            logger.error(f"AILoop session state is {self._state}, expected NOT_STARTED.")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=RuntimeError(f"Invalid initial state: {self._state}"))
            return

        self._state = SessionState.WAIT_FOR_INPUT
        logger.debug(f"_run_session: Initial state set to {self._state}")

        state_handlers = {
            SessionState.WAIT_FOR_INPUT: self._handle_wait_for_input_state,
            SessionState.ASSEMBLE_AI_STREAM: self._handle_assemble_ai_stream_state,
            SessionState.PROCESS_TOOL_RESULT: self._handle_process_tool_result_state,
        }

        try:
            while iteration_count < max_iterations and self._state != SessionState.SHUTDOWN:
                iteration_count += 1
                logger.debug(f"_run_session: Iteration {iteration_count}, Current State: {self._state}")
                await self.pause_event.wait()

                handler = state_handlers.get(self._state)
                if not handler:
                    logger.error(f"No handler for state {self._state}. Shutting down.")
                    self._state = SessionState.SHUTDOWN
                    self._last_ai_finish_reason = "error_unknown_state"
                    break

                # _handle_assemble_ai_stream_state updates self._last_ai_finish_reason via _handle_ai_stream_assembly
                # and returns the next state. Other handlers just return the next state.
                self._state = await handler()

            if iteration_count >= max_iterations:
                logger.warning(f"_run_session: Exited loop due to max_iterations ({max_iterations}).")
                self._last_ai_finish_reason = "max_iterations_reached"

        except asyncio.CancelledError:
            logger.info("_run_session: Main loop cancelled.")
            self._last_ai_finish_reason = "cancelled"
            # No re-raise here, finally block will handle notifications
        except Exception as e:
            logger.exception("AILoop _run_session encountered an unhandled error:")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
            self._last_ai_finish_reason = "error"
        finally:
            logger.debug(f"_run_session: Loop finished. Final self._state: {self._state}, Shutdown event: {self.shutdown_event.is_set()}")

            final_session_end_reason = "unknown"
            if self.shutdown_event.is_set():
                final_session_end_reason = "stopped"
            elif self._last_ai_finish_reason == "cancelled":
                final_session_end_reason = "cancelled"
            elif self._last_ai_finish_reason == "error" or (isinstance(self._last_ai_finish_reason, str) and "error" in self._last_ai_finish_reason) :
                final_session_end_reason = "error"
            elif self._last_ai_finish_reason == "max_iterations_reached":
                final_session_end_reason = "max_iterations_reached"
            # Add other specific finish reasons if needed

            logger.info(f"AILoop session ended. Reason: {final_session_end_reason}. Last AI finish_reason: {self._last_ai_finish_reason}")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.session_ended", event_data=final_session_end_reason)
            self._session_task = None
            self._state = SessionState.NOT_STARTED

    import types

    async def _iterate_ai_stream(self, ai_response_stream: AsyncIterator):
        full_response_content = ""
        accumulated_tool_calls_part = ""
        finish_reason_from_stream = None
        last_chunk_delta_content = ""
        saw_any_chunk = False

        async for chunk in ai_response_stream:
            saw_any_chunk = True
            last_chunk_delta_content = chunk.delta_content if chunk.delta_content is not None else ""

            if self.shutdown_event.is_set():
                logger.debug("_iterate_ai_stream: Shutdown event set, stopping stream iteration.")
                finish_reason_from_stream = "stopped"
                break
            await self.pause_event.wait()

            logger.debug(f"_iterate_ai_stream: Received chunk: {chunk}")
            if chunk.delta_content:
                full_response_content += chunk.delta_content
                await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.ai_chunk_received", event_data=chunk.delta_content)

            if chunk.delta_tool_call_part:
                accumulated_tool_calls_part += chunk.delta_tool_call_part

            if chunk.finish_reason:
                finish_reason_from_stream = chunk.finish_reason
                logger.debug(f"_iterate_ai_stream: Received finish_reason: {finish_reason_from_stream}")

            await asyncio.sleep(0.05) # Yield control

        return full_response_content, accumulated_tool_calls_part, finish_reason_from_stream, last_chunk_delta_content, saw_any_chunk

    async def _send_final_chunk_notification(self, last_chunk_delta_content: str = ""):
        """Sends the final AI message chunk notification."""
        logger.debug(f"[DEBUG] Sending final chunk notification: event_data='{last_chunk_delta_content}', is_final_chunk=True")
        await self.delegate_manager.invoke_notification(
            sender=self,
            event_type="ai_loop.message.ai_chunk_received",
            event_data=last_chunk_delta_content,
            is_final_chunk=True
        )

    async def _execute_single_tool_call(self, tc: dict):
        """Executes a single tool call and queues its result."""
        name = tc.get("function", {}).get("name")
        args_str = tc.get("function", {}).get("arguments")
        tool_id = tc.get("id")

        if not (name and args_str and tool_id):
            logger.warning(f"Malformed tool call data received: {tc}")
            await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id or "unknown_id", "name": name or "unknown_name", "content": "Error: Malformed tool call data."})
            return

        tool_instance = get_tool_registry().get_tool_by_name(name)
        if not tool_instance:
            logger.error(f"_execute_single_tool_call: Tool {name} not found.")
            await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error: Tool {name} not found."})
            return

        try:
            tool_args_dict = json.loads(args_str)
            # TODO: Consider if tool_instance.execute should be async
            tool_result_content = tool_instance.execute(arguments=tool_args_dict)
            tool_result_msg = {"role": "tool", "tool_call_id": tool_id, "name": name, "content": str(tool_result_content)}
            await self._tool_result_queue.put(tool_result_msg)
        except json.JSONDecodeError as e_args:
            logger.error(f"_execute_single_tool_call: Failed to parse args for {name}: {e_args}. Args: {args_str}")
            await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error: Invalid arguments for tool {name}."})
        except Exception as e_exec:
            logger.error(f"_execute_single_tool_call: Error executing tool {name}: {e_exec}", exc_info=True)
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e_exec)
            await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error executing tool {name}: {str(e_exec)}"})

    async def _process_tool_calls_from_stream(self, accumulated_tool_calls_part: str, assistant_message_to_add: dict):
        """Parses and executes tool calls identified in the AI stream."""
        try:
            logger.debug(f"_process_tool_calls_from_stream: Attempting to parse: '{accumulated_tool_calls_part}'")
            parsed_tool_calls = json.loads(accumulated_tool_calls_part)

            if isinstance(parsed_tool_calls, dict) and "tool_calls" in parsed_tool_calls:
                tool_calls = parsed_tool_calls["tool_calls"]
            else:
                tool_calls = parsed_tool_calls

            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]

            assistant_message_to_add["tool_calls"] = tool_calls
            logger.debug(f"_process_tool_calls_from_stream: Found tool_calls: {tool_calls}")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.identified", event_data=tool_calls)

            for tc in tool_calls:
                await self._execute_single_tool_call(tc)

        except json.JSONDecodeError as e:
            logger.error(f"_process_tool_calls_from_stream: Failed to parse tool calls JSON: {e}")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
        except TypeError as e:
            logger.error(f"_process_tool_calls_from_stream: TypeError during tool call processing: {e}")
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)


    async def _assemble_ai_stream(self, ai_response_stream):
        """
        Assemble the AI stream, add messages to context, emit events, and return finish_reason.
        """
        final_finish_reason = "unknown" # More descriptive name for the variable returned by this func
        assistant_message_to_add = {"role": "assistant"}

        try:
            if isinstance(ai_response_stream, types.CoroutineType):
                ai_response_stream = await ai_response_stream

            (full_response_content,
             accumulated_tool_calls_part,
             stream_finish_reason,  # This is the finish_reason from iterating the stream
             last_chunk_delta_content,
             saw_any_chunk) = await self._iterate_ai_stream(ai_response_stream)

            final_finish_reason = stream_finish_reason # Default to what the stream reported

            await self._send_final_chunk_notification(last_chunk_delta_content if saw_any_chunk else "")

            logger.debug(f"_assemble_ai_stream: full_response_content after stream: '{full_response_content}'")
            if full_response_content:
                assistant_message_to_add["content"] = full_response_content

            if stream_finish_reason == "tool_calls" and not self.shutdown_event.is_set() and accumulated_tool_calls_part:
                await self._process_tool_calls_from_stream(accumulated_tool_calls_part, assistant_message_to_add)
                # If tool calls were processed, the loop should continue to get their results,
                # so the finish_reason for this step is effectively "tool_calls".
                final_finish_reason = "tool_calls"
            elif stream_finish_reason == "stopped": # stream was stopped by shutdown_event
                 logger.info("_assemble_ai_stream: Stream iteration was stopped by shutdown event.")
                 final_finish_reason = "stopped"


            if "content" in assistant_message_to_add or "tool_calls" in assistant_message_to_add:
                agent_id = self.get_agent_id() if self.get_agent_id else 'default'
                self.context_manager.add_message(assistant_message_to_add, agent_id=agent_id)
                logger.debug(f"_assemble_ai_stream: Added assistant message to context: {assistant_message_to_add}")

            logger.debug(f"_assemble_ai_stream: AI call finished with reason: {final_finish_reason}.")

        except TypeError as e: # This specifically catches if ai_response_stream is not an async iterable
            logger.error(f"_assemble_ai_stream: Expected ai_response_stream to be an async iterable, got error: {e}")
            # Notify about the TypeError related to the stream type
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
            # Add an error message to context
            error_msg = {"role": "assistant", "content": f"Error processing AI stream: Invalid stream format. Details: {e}"}
            agent_id = self.get_agent_id() if self.get_agent_id else 'default'
            self.context_manager.add_message(error_msg, agent_id=agent_id)
            logger.debug(f"_assemble_ai_stream: Added error message to context: {error_msg}")
            finish_reason = "stop" # Return "stop" to allow the loop to continue
            # Do NOT re-raise, handle it gracefully

        except asyncio.CancelledError:
             logger.debug("_assemble_ai_stream: CancelledError caught during stream processing.")
             finish_reason = "cancelled"
             raise # Re-raise the cancellation exception

        except Exception as e:
             logger.exception("_assemble_ai_stream encountered an error:")
             await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
             # Add a user-friendly error message to the context history
             error_msg = {"role": "assistant", "content": f"An error occurred while processing the AI response: {e}"}
             agent_id = self.get_agent_id() if self.get_agent_id else 'default'
             self.context_manager.add_message(error_msg, agent_id=agent_id)
             logger.debug(f"_assemble_ai_stream: Added error message to context: {error_msg}")
             finish_reason = "stop" # Return "stop" to allow the loop to continue
             # Do NOT re-raise, handle it gracefully

        return finish_reason

    async def stop_session(self):
        """
        Stops the current AI session. Sets the shutdown event, unblocks queues,
        and waits for the session task to complete.
        """
        logger.debug(f"stop_session: called. _session_task: {self._session_task}")
        self.shutdown_event.set()
        self.pause_event.set()
        # Put None on queues to unblock any pending gets and allow the loop to exit gracefully
        await self._user_message_queue.put(None)
        await self._tool_result_queue.put(None)

        if self._session_task:
            try:
                logger.debug(f"stop_session: waiting for _session_task: {self._session_task}")
                # Wait for the session task to finish, with a timeout
                await asyncio.wait_for(self._session_task, timeout=5.0)
                logger.debug("AILoop session task finished.")
            except asyncio.TimeoutError:
                logger.warning("AILoop session task did not finish within timeout, cancelling.")
                if self._session_task and not self._session_task.done():
                    self._session_task.cancel()
                    try:
                        await self._session_task
                    except asyncio.CancelledError:
                        logger.debug("AILoop session task cancelled successfully.")
                    except Exception as e:
                        logger.error(f"Error waiting for cancelled session task: {e}")
                else:
                    logger.debug("stop_session: _session_task was None or already done after timeout.")
            except Exception as e:
                 logger.error(f"Error waiting for session task to finish: {e}")
            finally:
                self._session_task = None # Ensure task is set to None regardless of outcome

    async def pause_session(self):
        """
        Pauses the AI loop session, preventing it from processing new messages or AI responses.
        Emits the 'ai_loop.status.paused' notification if the session was successfully paused.
        """
        if self.pause_event.is_set(): # Only proceed if the session is currently unpaused
            logger.debug("Pausing AILoop session...")
            self.pause_event.clear()
            # Invoke notification if the session was in a state where it could be paused
            # and the event was successfully cleared (meaning it was previously set)
            if self._state in [SessionState.WAIT_FOR_INPUT, SessionState.PROCESS_TOOL_RESULT, SessionState.ASSEMBLE_AI_STREAM]:
                 await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.status.paused")
            else:
                 logger.debug(f"Paused AILoop session in state: {self._state}, but no pause notification sent.")
        else:
            logger.debug("AILoop session is already paused.")

    async def resume_session(self):
        """
        Resumes a paused AI loop session, allowing it to continue processing.
        Emits the 'ai_loop.status.resumed' notification.
        """
        if not self.pause_event.is_set():
            logger.debug("Resuming AILoop session...")
            self.pause_event.set()
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.status.resumed")
        else:
            logger.debug("AILoop session is already running.")

    async def send_user_message(self, message: str):
        """
        Sends a user message to the AI loop for processing. The message is added
        to an internal queue and will be processed when the loop is in the
        WAIT_FOR_INPUT state.

        Args:
            message: The user message string.
        """
        if not isinstance(message, str):
            logger.error(f"Invalid input to send_user_message: Expected string, got {type(message)}")
            await self.delegate_manager.invoke_notification(
                sender=self,
                event_type="ai_loop.error",
                event_data=TypeError(f"Invalid input to send_user_message: Expected string, got {type(message)}")
            )
            return

        if self._session_task is None or self._session_task.done():
            logger.warning("send_user_message called but session is not running or has finished.")
            # Depending on desired behavior, you might start a new session here,
            # but for now, we'll just log and queue the message.
            # The message will be processed if/when the loop is started later.
        logger.debug(f"Received user message: {message}")
        await self._user_message_queue.put(message)
        # Yield control to allow background session task to process the message (helps in tests)
        await asyncio.sleep(0)

    async def _handle_start_session(self, **kwargs):
        # tool_registry = kwargs.get("tool_registry") # Not used here, handled by get_tool_registry()
        system_prompt = kwargs.get("initial_prompt") # Match the kwarg used in the test
        if not isinstance(system_prompt, str):
            logger.error(f"Control event 'ai_loop.control.start' received with invalid 'initial_prompt' type: {type(system_prompt)}. Expected string.")
            await self.delegate_manager.invoke_notification(
                sender=self,
                event_type="ai_loop.error",
                event_data=TypeError(f"Invalid 'initial_prompt' type for ai_loop.control.start: Expected string, got {type(system_prompt)}")
            )
            return
        await self.start_session(system_prompt=system_prompt)

    async def _handle_stop_session(self, **kwargs):
        await self.stop_session()

    async def _handle_pause_session(self, **kwargs):
        await self.pause_session()

    async def _handle_resume_session(self, **kwargs):
        await self.resume_session()

    async def _handle_send_user_message(self, **kwargs):
        message = kwargs.get("message")
        if not isinstance(message, str):
            logger.error(f"Control event 'ai_loop.control.send_user_message' received with invalid 'message' type: {type(message)}. Expected string.")
            await self.delegate_manager.invoke_notification(
                sender=self,
                event_type="ai_loop.error",
                event_data=TypeError(f"Invalid 'message' type for ai_loop.control.send_user_message: Expected string, got {type(message)}")
            )
            return
        await self.send_user_message(message)

    async def _handle_provide_tool_result(self, **kwargs):
        result = kwargs.get("result")
        # Validate that the result is a dictionary, which is the expected format for a tool message
        if not isinstance(result, dict):
            logger.error(f"Control event 'ai_loop.control.provide_tool_result' received with invalid 'result' type: {type(result)}. Expected dictionary.")
            await self.delegate_manager.invoke_notification(
                sender=self,
                event_type="ai_loop.error",
                event_data=TypeError(f"Invalid 'result' type for ai_loop.control.provide_tool_result: Expected dictionary, got {type(result)}")
            )
            return

        if result is not None: # Check for None explicitly after type check
            logger.debug(f"Received tool result via delegate: {result}")
            await self._tool_result_queue.put(result)

