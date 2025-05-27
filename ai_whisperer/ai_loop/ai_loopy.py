import asyncio
import json
import logging
import enum
import types
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
    def __init__(self, config: AIConfig, ai_service: AIService, context_manager: ContextManager, delegate_manager: DelegateManager):
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
        self.context_manager.add_message({"role": "system", "content": system_prompt})
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
        finish_reason = "unknown" # Track the finish reason of the last AI call
        logger.debug("_run_session: Session started.")
        print("[AILoop _run_session] Session started.")
        max_iterations = 1000 # Set a high limit to prevent infinite loops during debugging
        iteration_count = 0
        
        # Initial state validation - these should ideally not happen if start_session is called correctly,
        # but adding graceful handling instead of crashing.
        if self._session_task is None:
            error_msg = "AILoop session task is None at the start of _run_session."
            logger.error(error_msg)
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=RuntimeError(error_msg))
            return # Exit the session task
        if self._state != SessionState.NOT_STARTED:
            error_msg = f"AILoop session state is {self._state}, expected NOT_STARTED at the start of _run_session."
            logger.error(error_msg)
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=RuntimeError(error_msg))
            return # Exit the session task

        self._state = SessionState.WAIT_FOR_INPUT
        logger.debug(f"_run_session: State set to WAIT_FOR_INPUT")

        try:
            while iteration_count < max_iterations: # Use a counter to prevent infinite loops
                iteration_count += 1
                logger.debug(f"_run_session: Iteration {iteration_count}, State: {self._state}")
                print(f"[AILoop _run_session] Iteration {iteration_count}, State: {self._state}")

                await self.pause_event.wait()

                logger.debug(f"_run_session: Top of loop, state={self._state}, shutdown_event={self.shutdown_event.is_set()}, user_queue_empty={self._user_message_queue.empty()}, tool_queue_empty={self._tool_result_queue.empty()}")

                if self._state == SessionState.WAIT_FOR_INPUT:
                    # Check queues for user or tool input
                    processed_queue_item = False
                    try:
                        user_message = self._user_message_queue.get_nowait()
                        if user_message is not None: # Handle potential None from stop_session
                            if not isinstance(user_message, str):
                                error_msg = f"Invalid item type received from user_message_queue: Expected str, got {type(user_message)}. Discarding."
                                logger.error(error_msg)
                                await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                            else:
                                logger.debug(f"_run_session: Got user_message from queue: {user_message}")
                                self.context_manager.add_message({"role": "user", "content": user_message}) # type: ignore
                                await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
                                processed_queue_item = True
                        else:
                             processed_queue_item = True # Treat None as processed for shutdown
                    except asyncio.QueueEmpty:
                        logger.debug("_run_session: No user_message in queue.")
                        pass

                    if not processed_queue_item:
                        try:
                            tool_result = self._tool_result_queue.get_nowait()
                            if tool_result is not None: # Handle potential None from stop_session
                                if not isinstance(tool_result, dict):
                                    error_msg = f"Invalid item type received from tool_result_queue: Expected dict, got {type(tool_result)}. Discarding."
                                    logger.error(error_msg)
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                                else:
                                    logger.debug(f"_run_session: Got tool_result from queue: {tool_result}")
                                    self.context_manager.add_message(tool_result) # type: ignore
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                                    processed_queue_item = True
                            else:
                                processed_queue_item = True # Treat None as processed for shutdown
                        except asyncio.QueueEmpty:
                            logger.debug("_run_session: No tool_result in queue.")
                            pass

                    if not processed_queue_item:
                        logger.debug("_run_session: Waiting for input from user_message_queue or tool_result_queue.")
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
                            if user_message is not None: # Handle potential None from stop_session
                                if not isinstance(user_message, str):
                                    error_msg = f"Invalid item type received from awaited user_message_queue: Expected str, got {type(user_message)}. Discarding."
                                    logger.error(error_msg)
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                                else:
                                    logger.debug(f"_run_session: Got user_message from awaited queue: {user_message}")
                                    self.context_manager.add_message({"role": "user", "content": user_message}) # type: ignore
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.user_processed", event_data=user_message)
                            # If None, it's a shutdown signal, handled by the main loop condition
                        else: # result_task is tool_task
                            tool_result = tool_task.result()
                            if tool_result is not None: # Handle potential None from stop_session
                                if not isinstance(tool_result, dict):
                                    error_msg = f"Invalid item type received from awaited tool_result_queue: Expected dict, got {type(tool_result)}. Discarding."
                                    logger.error(error_msg)
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=TypeError(error_msg))
                                else:
                                    logger.debug(f"_run_session: Got tool_result from awaited queue: {tool_result}")
                                    self.context_manager.add_message(tool_result) # type: ignore
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
                            # If None, it's a shutdown signal, handled by the main loop condition
                    # After processing input, move to AI stream state if not shutting down
                    logger.debug(f"_run_session: After input processing, shutdown_event={self.shutdown_event.is_set()}")
                    if not self.shutdown_event.is_set():
                        logger.debug("_run_session: Transitioning to ASSEMBLE_AI_STREAM")
                        self._state = SessionState.ASSEMBLE_AI_STREAM
                    else:
                        logger.debug("_run_session: Transitioning to SHUTDOWN")
                        self._state = SessionState.SHUTDOWN

                elif self._state == SessionState.ASSEMBLE_AI_STREAM:
                    # Prepare AI call arguments
                    messages = self.context_manager.get_history()
                    tools_for_model = get_tool_registry().get_all_tool_definitions()

                    logger.debug(f"_run_session: Calling ai_service.stream_chat_completion with messages={messages} tools={tools_for_model}")
                    try:
                        # Set a timeout for the entire AI service streaming process (e.g., 10 seconds)

                        async def run_stream():
                            ai_response_stream = self.ai_service.stream_chat_completion(
                                messages=messages,
                                tools=tools_for_model,
                                **self.config.__dict__
                            )
                            try:
                                return await self._assemble_ai_stream(ai_response_stream)
                            except asyncio.CancelledError:
                                logger.error("run_stream: CancelledError caught, closing ai_response_stream")
                                if hasattr(ai_response_stream, 'aclose'):
                                    await ai_response_stream.aclose()
                                raise

                        logger.error("_run_session: About to call asyncio.wait_for(run_stream(), timeout=10.0)")
                        finish_reason = await asyncio.wait_for(run_stream(), timeout=10.0)
                        logger.error(f"_run_session: Finished asyncio.wait_for, finish_reason={{finish_reason}}")
                        logger.debug(f"_run_session: Finished _assemble_ai_stream with finish_reason={{finish_reason}}")
                        if finish_reason == "tool_calls":
                            self._state = SessionState.PROCESS_TOOL_RESULT
                        elif finish_reason == "error":
                            self._state = SessionState.SHUTDOWN # Error during stream processing leads to shutdown
                        else:
                            self._state = SessionState.WAIT_FOR_INPUT
                    except asyncio.TimeoutError:
                        logger.error("_run_session: AI service call timed out.")
                        logger.error("_run_session: About to invoke error notification for timeout.")
                        await self.delegate_manager.invoke_notification(
                            sender=self,
                            event_type="ai_loop.error",
                            event_data="AI service timeout"
                        )
                        logger.error("_run_session: Finished invoke_notification for timeout.")
                        # Add a user-friendly error message to the context history
                        error_msg = {"role": "assistant", "content": "AI service timeout: The AI did not respond in time."}
                        self.context_manager.add_message(error_msg)
                        logger.debug(f"_run_session: Added timeout error message to context: {{error_msg}}")
                        self._state = SessionState.WAIT_FOR_INPUT
                    except Exception as e:
                        logger.exception("_run_session: Error calling ai_service.stream_chat_completion:")
                        await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
                        # Add a user-friendly error message to the context history
                        error_msg = {"role": "assistant", "content": f"An error occurred while processing the AI response: {e}"}
                        self.context_manager.add_message(error_msg)
                        logger.debug(f"_run_session: Added error message to context: {{error_msg}}")
                        self._state = SessionState.WAIT_FOR_INPUT # Return to waiting for input after AI service error
 
                elif self._state == SessionState.PROCESS_TOOL_RESULT:
                    # Wait for tool result to be provided
                    tool_result = await self._tool_result_queue.get()
                    if tool_result is None:
                        self._state = SessionState.SHUTDOWN
                    else:
                        self.context_manager.add_message(tool_result) # type: ignore
                        await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.result_processed", event_data=tool_result)
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
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
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
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.session_ended", event_data=final_finish_reason)
            self._session_task = None

    import types
    async def _assemble_ai_stream(self, ai_response_stream):
        """
        Assemble the AI stream, add messages to context, emit events, and return finish_reason.
        """
        full_response_content = ""
        accumulated_tool_calls_part = ""
        finish_reason = None
        assistant_message_to_add = {"role": "assistant"} # Initialize the message to be added

        try:

            # If ai_response_stream is a coroutine (from AsyncMock), await it to get the async generator
            if isinstance(ai_response_stream, types.CoroutineType):
                ai_response_stream = await ai_response_stream
            logger.debug("_run_session: Processing AI stream.")
            last_nonempty_chunk = None
            async for chunk in ai_response_stream:
                # Check for shutdown or pause requests frequently
                if self.shutdown_event.is_set():
                    logger.debug("_assemble_ai_stream: Shutdown event set, stopping stream processing.")
                    finish_reason = "stopped" # Indicate that streaming was stopped externally
                    break # Exit the streaming loop
                await self.pause_event.wait() # Wait if paused

                logger.debug(f"_run_session: Received chunk: {chunk}")
                if chunk.delta_content:
                    full_response_content += chunk.delta_content
                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.message.ai_chunk_received", event_data=chunk.delta_content)
                    if str(chunk.delta_content).strip():
                        last_nonempty_chunk = chunk.delta_content
                await asyncio.sleep(0.05) # Yield control to allow other tasks to run

                if chunk.delta_tool_call_part:
                    accumulated_tool_calls_part += chunk.delta_tool_call_part

                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                    logger.debug(f"_run_session: Received finish_reason: {finish_reason}")

            # After streaming, send a final chunk notification to indicate the end of the stream
            if last_nonempty_chunk is not None:
                await self.delegate_manager.invoke_notification(
                    sender=self,
                    event_type="ai_loop.message.ai_chunk_received",
                    event_data=last_nonempty_chunk,
                    is_final_chunk=True
                )

            # After streaming, process the full response and identified tool calls
            logger.debug(f"_run_session: full_response_content after stream: '{full_response_content}'")
            if full_response_content:
                assistant_message_to_add["content"] = full_response_content
                logger.debug("_run_session: Assistant message content added to assistant_message_to_add.")

            # Only process tool calls if the stream finished naturally with "tool_calls"
            # If shutdown was requested during streaming, we don't process tool calls from incomplete data.
            if finish_reason == "tool_calls" and not self.shutdown_event.is_set():
                # Attempt to parse accumulated tool call parts into ToolCall objects
                try:
                    logger.debug(f"_run_session: Attempting to parse accumulated_tool_calls_part: '{accumulated_tool_calls_part}'")
                    parsed_tool_calls = json.loads(accumulated_tool_calls_part) # This should be a list or dict
                    # If it's a list, treat as tool_calls; if dict with 'tool_calls', extract
                    if isinstance(parsed_tool_calls, dict) and "tool_calls" in parsed_tool_calls:
                        tool_calls = parsed_tool_calls["tool_calls"]
                    else:
                        tool_calls = parsed_tool_calls
                    if not isinstance(tool_calls, list):
                        tool_calls = [tool_calls]
                    assistant_message_to_add["tool_calls"] = tool_calls
                    logger.debug(f"_run_session: Found tool_calls: {tool_calls}")
                    # Notify delegate with full tool call dicts (for websocket notification)
                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.tool_call.identified", event_data=tool_calls)
                    # Continue with tool execution as before
                    for tc in tool_calls:
                        name = tc.get("function", {}).get("name")
                        args_str = tc.get("function", {}).get("arguments")
                        tool_id = tc.get("id")
                        if name and args_str and tool_id:
                            tool_instance = get_tool_registry().get_tool_by_name(name)
                            if tool_instance:
                                try:
                                    tool_args_dict = json.loads(args_str) # Parse arguments string into dict
                                    tool_result_content = tool_instance.execute(arguments=tool_args_dict)
                                    tool_result_msg = {"role": "tool", "tool_call_id": tool_id, "name": name, "content": str(tool_result_content)}
                                    await self._tool_result_queue.put(tool_result_msg)
                                except json.JSONDecodeError as e_args:
                                    logger.error(f"_run_session: Failed to parse arguments for tool {name}: {e_args}. Arguments: {args_str}")
                                    await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error: Invalid arguments for tool {name}."})
                                except Exception as e_exec:
                                    logger.error(f"_run_session: Error executing tool {name}: {e_exec}", exc_info=True)
                                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e_exec)
                                    await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error executing tool {name}: {str(e_exec)}"})
                            else:
                                logger.error(f"_run_session: Tool {name} not found in registry.")
                                await self._tool_result_queue.put({"role": "tool", "tool_call_id": tool_id, "name": name, "content": f"Error: Tool {name} not found."})
                        else:
                            logger.warning(f"Malformed tool call data received: {tc}")
                except json.JSONDecodeError as e:
                    logger.error(f"_run_session: Failed to parse tool calls JSON: {e}")
                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
                except TypeError as e:
                    logger.error(f"_run_session: TypeError during ToolCall instantiation or processing: {e}")
                    await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)

            # Add the assembled assistant message to context if it has content or tool_calls
            if "content" in assistant_message_to_add or "tool_calls" in assistant_message_to_add:
                self.context_manager.add_message(assistant_message_to_add)
                logger.debug(f"_run_session: Added assistant message to context: {assistant_message_to_add}")

            # If finish_reason is "stop" or "error", the loop should now break if queues are empty
            # If finish_reason is not "stop", "error", or "tool_calls", the loop continues.
            logger.debug(f"_run_session: AI call finished with reason: {finish_reason}. Checking queues for pending messages.")

        except TypeError as e:
            logger.error(f"_assemble_ai_stream: Expected ai_response_stream to be an async iterable, got error: {e}")
            # Notify about the TypeError related to the stream type
            await self.delegate_manager.invoke_notification(sender=self, event_type="ai_loop.error", event_data=e)
            # Add an error message to context
            error_msg = {"role": "assistant", "content": f"Error processing AI stream: Invalid stream format. Details: {e}"}
            self.context_manager.add_message(error_msg)
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
             self.context_manager.add_message(error_msg)
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

