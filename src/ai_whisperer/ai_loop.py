# src/ai_whisperer/ai_loop.py

import json
import traceback
from unittest.mock import MagicMock # Assuming MagicMock might be used for testing within the loop itself, though ideally tests mock the loop. Keep for now.
import asyncio # Import asyncio

from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, get_logger, log_event # Import log_event
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.context_management import ContextManager

import threading # Import threading for shutdown_event type hint
from ai_whisperer.delegate_manager import DelegateManager # Import DelegateManager

logger = get_logger(__name__)

def run_ai_loop(engine: ExecutionEngine, task_definition: dict, task_id: str, initial_prompt: str, logger, context_manager: ContextManager, delegate_manager: DelegateManager) -> dict:
    """
    Manages the iterative AI interaction loop for a task, including sending prompts,
    processing AI responses, executing tool calls, and managing conversation history
    using the provided ContextManager.

    This function encapsulates the core logic for interacting with the AI service
    to drive the execution of a task based on the conversation flow and tool usage.

    Args:
        engine: The execution engine instance, providing access to AI service,
                tool registry, configuration, and monitoring.
        task_definition: The dictionary defining the current task being executed.
        task_id: The unique identifier for the current task.
        initial_prompt: The initial prompt string to send to the AI.
        logger: The logger instance for logging messages within the loop.
        context_manager: The ContextManager instance specifically for this task,
                         used to manage the conversation history.

    Returns:
        A dictionary representing the final response received from the AI
        when the loop terminates (e.g., when the AI provides content or signals stop).

    Raises:
        TaskExecutionError: If a critical error occurs during the AI interaction,
                            such as failure to call the AI service, invalid tool calls,
                            tool execution errors, or exceeding consecutive tool call limits.
    """
    final_result = None
    from ai_whisperer.tools.tool_registry import get_tool_registry
    tool_registry = get_tool_registry() # Get the tool registry singleton instance
    consecutive_tool_calls = 0 # Counter for consecutive tool-only responses
    MAX_CONSECUTIVE_TOOL_CALLS = 5 # Threshold to detect potential infinite loops

    _ai_loop_pause_event = threading.Event() # Add AI loop pause event
    _ai_loop_paused = False # Add AI loop paused state flag


    # Prepare system prompt for OpenRouter, including tool usage instructions. Do NOT add user message to context before first call.
    context_manager.clear_history()  # Ensure history is clean for this task
    # Gather tool usage instructions
    tool_usage_instructions = []
    for tool in tool_registry.get_all_tools():
        if hasattr(tool, 'get_ai_prompt_instructions'):
            instr = tool.get_ai_prompt_instructions()
            if instr:
                tool_usage_instructions.append(instr.strip())
    tool_usage_block = "\n\n".join(tool_usage_instructions)
    system_prompt = (
        "You are an expert AI coding agent. You must use the OpenRouter tool call protocol for all tool use. "
        "When you need to use a tool, respond with a tool call in the 'tool_calls' field, not as plain text. "
        "Do not output tool calls as plain text in the 'content' field. Only output final answers or explanations in 'content' when the task is complete. "
        "If you need to write a file, use the 'write_to_file' tool.\n\n"
        "--- TOOL USAGE INSTRUCTIONS ---\n" + tool_usage_block
    )
    user_prompt_entry = {"role": "user", "content": initial_prompt}
    # For OpenAI-compatible APIs, build messages array with system and user messages
    first_call_messages = [
        {"role": "system", "content": system_prompt},
        user_prompt_entry
    ]

    logger.debug(f"Task {task_id}: Entering AI interaction loop.")
    delegate_manager.invoke_notification(engine, "ai_loop_started", {"task_id": task_id})

    # First AI call: send system and user messages as the messages_history array
    try:
        logger.debug(f"Task {task_id}: Calling AI with system and user messages in messages_history.")
        log_event(
            log_message=LogMessage(
                LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_calling_ai_initial",
                f"Calling AI for task {task_id} with system and user messages in messages_history", subtask_id=task_id, details={"prompt_text": initial_prompt}
            )
            )
        delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "initial_ai_call_preparation", "task_id": task_id}) # Add processing step notification

        params = {
            'temperature': engine.config.get('ai_temperature', 0.1) # Use temperature from config
        }
        # Prepare tools for debug print
        if hasattr(engine, 'openrouter_api') and hasattr(engine.openrouter_api, 'tools'):
            tools_debug = engine.openrouter_api.tools
        else:
            tools_debug = tool_registry.get_all_tool_definitions()
        # Use model from config, supporting both 'openrouter' and 'ai_model' keys
        model = (
            engine.config.get('openrouter', {}).get('model')
            or engine.config.get('ai_model')
            or engine.config.get('model')
            or 'google/gemini-2.5-flash-preview'
        )

        # Defensive: ensure the result is a dict with 'message' key
        prompt_result = engine.openrouter_api.call_chat_completion(
            prompt_text=initial_prompt,
            messages_history=None,  # Use None so the API wrapper builds from prompt_text and system_prompt
            model=model,
            params={**params, 'tool_choice': 'auto'},
            tools=tools_debug,
        )
        if not (isinstance(prompt_result, dict) and "message" in prompt_result):
            error_message = f"Task {task_id}: AI response is not a valid dict with 'message' key: {prompt_result}"
            logger.error(error_message)
            log_event(
                log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_invalid_ai_response_initial", error_message, subtask_id=task_id, details={"ai_response": str(prompt_result)})
            )
            raise TaskExecutionError(error_message)
        ai_response = prompt_result

        logger.debug(f"Task {task_id}: Initial AI call completed.")
        if delegate_manager: # Add check for delegate_manager
            delegate_manager.invoke_notification(engine, "ai_response_received", {"response_data": ai_response}) # Invoke ai_response_received delegate
            delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "initial_ai_response_processing", "task_id": task_id}) # Add processing step notification

        # After the call, add the user message and the AI response to the context manager
        context_manager.add_message(user_prompt_entry)
        context_manager.add_message(ai_response["message"])

    except Exception as e:
        error_message = f"Task {task_id}: Error during initial AI call: {e}"
        logger.error(error_message, exc_info=True)
        log_event(
            log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_initial_ai_call_error", error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()})
        )
        if delegate_manager: # Add check for delegate_manager
            delegate_manager.invoke_notification(engine, "ai_loop_error_occurred", {"error_type": type(e).__name__, "error_message": error_message}) # Invoke ai_loop_error_occurred delegate
        raise TaskExecutionError(error_message) from e


    # Subsequent AI interaction loop
    while True:
        logger.debug(f"Task {task_id}: Start of subsequent AI interaction loop iteration.")

        # Check for pause request
        if delegate_manager and delegate_manager.invoke_control(engine, "ai_loop_request_pause"): # Add check for delegate_manager
            # TODO: Implement actual pause logic (e.g., wait on a threading.Event)
            logger.info(f"AI loop paused for task {task_id}")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_loop_paused",
                    f"AI loop paused for task {task_id}.",
                    subtask_id=task_id,
                )
            )
            while _ai_loop_paused and not engine.shutdown_event.is_set():
                _ai_loop_pause_event.wait(timeout=0.1) # Wait with a timeout to allow checking shutdown_event
            if engine.shutdown_event.is_set():
                logger.info("Shutdown requested while AI loop paused. Stopping AI loop.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_loop_shutdown_while_paused",
                        "Shutdown requested while AI loop paused. Stopping AI loop.",
                        subtask_id=task_id,
                    )
                )
                break # Exit the AI loop for graceful shutdown

       # Check for stop request
        if delegate_manager and delegate_manager.invoke_control(engine, "ai_loop_request_stop"): # Add check for delegate_manager
            logger.info(f"AI loop received stop request for task {task_id}. Initiating graceful shutdown.")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_loop_stop_requested",
                    f"AI loop received stop request for task {task_id}. Initiating graceful shutdown.",
                    subtask_id=task_id,
                )
            )
            # In a real implementation, this might involve more cleanup
            break # Exit the loop for graceful shutdown

        # Extract tool_calls and content from OpenAI-style response structure
        tool_calls = None
        content = None
        finish_reason = None
        ai_message = ai_response["message"] if isinstance(ai_response, dict) and "message" in ai_response else ai_response
        if isinstance(ai_message, dict) and "tool_calls" in ai_message:
            tool_calls = ai_message.get("tool_calls")
            content = ai_message.get("content")
            finish_reason = ai_message.get("finish_reason")
        else:
            # fallback for legacy/flat responses (should not occur in normal operation)
            tool_calls = ai_message.get("tool_calls") if isinstance(ai_message, dict) else None
            content = ai_message.get("content") if isinstance(ai_message, dict) else None
            finish_reason = ai_message.get("finish_reason") if isinstance(ai_message, dict) else None

        logger.debug(f"Task {task_id}: Processing AI response in loop. tool_calls type: {type(tool_calls)}, content type: {type(content)}, content: '{content}'")
        log_event(
            log_message=LogMessage(
                LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_processing_ai_response",
                f"Task {task_id}: Processing AI response in loop", subtask_id=task_id,
                details={"tool_calls_type": str(type(tool_calls)), "content_type": str(type(content)), "content_preview": str(content)[:100]}
            )
        )

        if tool_calls is not None and isinstance(tool_calls, list) and len(tool_calls) > 0:
            # AI wants to use tools
            consecutive_tool_calls += 1
            if consecutive_tool_calls > MAX_CONSECUTIVE_TOOL_CALLS:
                error_message = f"Task {task_id}: Exceeded maximum consecutive tool calls ({MAX_CONSECUTIVE_TOOL_CALLS}). Potential infinite loop detected."
                logger.error(error_message)
                log_event(
                    log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_infinite_loop", f"{error_message}", subtask_id=task_id, details={"message": error_message})
                )
                raise TaskExecutionError(error_message)

            delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "tool_call_execution", "task_id": task_id, "tool_calls_count": len(tool_calls)}) # Add processing step notification

            logger.debug(f"Task {task_id}: AI requested tool calls: {tool_calls}")

            tool_outputs = []
            for tool_call in tool_calls:
                tool_name = tool_call.get('function', {}).get('name')
                tool_arguments_str = tool_call.get('function', {}).get('arguments', '{}')
                tool_call_id = tool_call.get('id')

                if not tool_name or not tool_call_id:
                    logger.error(f"Task {task_id}: Invalid tool call received: {tool_call}")
                    log_event(
                        log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_invalid_tool_call", f"Task {task_id}: Invalid tool call received: {tool_call}", subtask_id=task_id, details={"tool_call": tool_call})
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call_id or "unknown",
                        "output": f"Error: Invalid tool call format."
                    })
                    continue

                try:
                    tool_arguments = json.loads(tool_arguments_str)
                    logger.debug(f"Task {task_id}: Executing tool: {tool_name} with args: {tool_arguments}")
                    log_event(
                        log_message=LogMessage(LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_executing_tool", f"Task {task_id}: Executing tool: {tool_name}", subtask_id=task_id, details={"tool_name": tool_name, "arguments": tool_arguments})
                    )

                    tool_instance = tool_registry.get_tool_by_name(tool_name)
                    if tool_instance is None:
                        error_message = f"Task {task_id}: Tool not found: {tool_name}"
                        logger.error(error_message)
                        log_event(
                            log_message=LogMessage(
                                LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_tool_not_found",
                                error_message, subtask_id=task_id, details={"tool_name": tool_name}
                            )
                        )
                        tool_outputs.append({
                            "tool_call_id": tool_call_id,
                            "output": f"Error: Tool '{tool_name}' not found."
                        })
                        continue

                    tool_output_data = tool_instance.execute(**tool_arguments)    
    
                    # Format tool output for the next AI turn
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": json.dumps(tool_output_data) if isinstance(tool_output_data, (dict, list)) else str(tool_output_data)
                    })
                    logger.debug(f"Task {task_id}: Tool {tool_name} executed successfully.")
                    output_preview = ""
                    if tool_outputs: # Check if the list is not empty
                        try:
                            # Safely access the output and get a preview
                            output_data = tool_outputs[-1].get('output')
                            if output_data is not None:
                                output_preview = str(output_data)[:100]
                        except Exception as preview_e:
                            logger.warning(f"Task {task_id}: Failed to get output preview for tool {tool_name}: {preview_e}")
                            output_preview = "Error getting preview"

                    log_event(
                        log_message=LogMessage(LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_tool_executed", f"Task {task_id}: Tool {tool_name} executed successfully.", subtask_id=task_id, details={"tool_name": tool_name, "output_preview": output_preview})
                    )


                except json.JSONDecodeError as e:
                    error_message = f"Task {task_id}: Failed to parse tool arguments JSON for tool '{tool_name}': {e}. Arguments: {tool_arguments_str}"
                    logger.error(error_message)
                    log_event(
                        log_message=LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_tool_call_invalid_arguments",
                            error_message, subtask_id=task_id, details={"tool_name": tool_name, "arguments": tool_arguments_str, "error": str(e)}
                        )
                    )
                    # Raise TaskExecutionError on JSON decoding failure
                    raise TaskExecutionError(error_message) from e

                except Exception as e:
                    error_message = f"Task {task_id}: Error executing tool '{tool_name}': {e}"
                    logger.error(error_message, exc_info=True)
                    log_event(
                        log_message=LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_tool_execution_error",
                            error_message, subtask_id=task_id, details={"tool_name": tool_name, "error": str(e), "traceback": traceback.format_exc()}
                        )
                    )
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": f"Error executing tool {tool_name}: {e}"
                    })
                    continue

            # Add tool outputs to conversation history using context manager
            for output in tool_outputs:
                 tool_output_entry = {"role": "tool", "tool_call_id": output["tool_call_id"], "content": output["output"]}
                 context_manager.add_message(tool_output_entry)

            if delegate_manager: # Add check for delegate_manager
                delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "tool_output_processing", "task_id": task_id, "tool_outputs_count": len(tool_outputs)}) # Add processing step notification

            # Call AI again with updated history from context manager
            try:
                logger.debug(f"Task {task_id}: Calling AI with updated conversation history from ContextManager.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_calling_ai_subsequent",
                        f"Calling AI for task {task_id} with updated history", subtask_id=task_id, details={"history_length": len(context_manager.get_history())}
                    )
                )
                if delegate_manager: # Add check for delegate_manager
                    delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "subsequent_ai_call_preparation", "task_id": task_id}) # Add processing step notification


                params = {
                    'temperature': engine.config.get('ai_temperature', 0.1),
                    'tool_choice': 'auto'  # Explicitly request tool call protocol
                }
                # Use model from config, supporting both 'openrouter' and 'ai_model' keys
                model = (
                    engine.config.get('openrouter', {}).get('model')
                    or engine.config.get('ai_model')
                    or engine.config.get('model')
                    or 'google/gemini-2.5-flash-preview'
                )
                delegate_manager.invoke_notification(engine, "ai_request_prepared", {"request_payload": {"prompt_text": "", "model": model, "params": params, "messages_history": context_manager.get_history()}})

                ai_response = engine.openrouter_api.call_chat_completion(
                    prompt_text ="",
                    messages_history=context_manager.get_history(), # Use history from ContextManager
                    model=model, # Use model from config
                    params=params,
                    tools=tools_debug,
                )
                if(ai_response is None):
                    raise TaskExecutionError("AI response is None. Check the AI model and parameters.")
                if not isinstance(ai_response, dict):
                    error_message = f"Task {task_id}: AI response is not a dict, which is unexpected."
                    logger.error(error_message)
                    log_event(
                        log_message=LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_invalid_ai_response",
                            error_message, subtask_id=task_id, details={"ai_response": ai_response}
                        )
                    )
                    raise TaskExecutionError(error_message)

                logger.debug(f"Task {task_id}: AI call with updated history completed.")
                if delegate_manager: # Add check for delegate_manager
                    delegate_manager.invoke_notification(engine, "ai_response_received", {"response_data": ai_response}) # Invoke ai_response_received delegate
                log_event(
                    log_message=LogMessage(
                        LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_ai_call_completed",
                        f"Task {task_id}: AI call with updated history completed.", subtask_id=task_id, details={"ai_response_preview": str(ai_response)[:100]}
                    )
                )
                if delegate_manager: # Add check for delegate_manager
                    delegate_manager.invoke_notification(engine, "ai_processing_step", {"step_name": "subsequent_ai_response_processing", "task_id": task_id}) # Add processing step notification


                # Store the assistant's response in the context manager
                context_manager.add_message(ai_response["message"])

            except Exception as e:
                error_message = f"Task {task_id}: Error during AI call with updated history: {e}"
                logger.error(error_message, exc_info=True)
                log_event(
                    log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_subsequent_ai_call_error", error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()})
                    )
                if delegate_manager: # Add check for delegate_manager
                    delegate_manager.invoke_notification(engine, "ai_loop_error_occurred", {"error_type": type(e).__name__, "error_message": error_message}) # Invoke ai_loop_error_occurred delegate
                raise TaskExecutionError(error_message) from e

        # Check if AI provided content or if the finish reason is 'stop'
        elif (content is not None and (tool_calls is None or len(tool_calls) == 0)) or (finish_reason == 'stop'):
            # AI provided content or signaled completion
            # Fallback: Try to detect and execute a tool call in plain text content
            import re
            tool_call_pattern = re.compile(r"^(\w+)\((.*)\)$", re.DOTALL)
            match = tool_call_pattern.match(content.strip()) if isinstance(content, str) else None
            if match:
                tool_name = match.group(1)
                args_str = match.group(2)
                # Try to parse arguments as Python kwargs (very basic, not secure for arbitrary code)
                import ast
                try:
                    # Convert args string to a dict by wrapping in dict() and using ast.literal_eval
                    # e.g., path='foo', content='bar' -> {'path': 'foo', 'content': 'bar'}
                    args_dict = ast.literal_eval(f"dict({args_str})")
                except Exception as e:
                    logger.warning(f"Task {task_id}: Failed to parse tool call arguments from content fallback: {e}")
                    args_dict = None
                tool_instance = tool_registry.get_tool_by_name(tool_name) if args_dict else None
                if tool_instance and args_dict:
                    logger.warning(f"Task {task_id}: Fallback: Executing tool '{tool_name}' from plain text content.")
                    try:
                        tool_output_data = tool_instance.execute(**args_dict)
                        # Add tool output to conversation history
                        tool_output_entry = {"role": "tool", "tool_call_id": f"fallback_{tool_name}", "content": json.dumps(tool_output_data) if isinstance(tool_output_data, (dict, list)) else str(tool_output_data)}
                        context_manager.add_message(tool_output_entry)
                        # Optionally, set final_result to tool_output_data or continue loop
                        final_result = tool_output_entry
                        logger.info(f"Task {task_id}: Fallback tool execution complete for '{tool_name}'.")
                        break
                    except Exception as e:
                        logger.error(f"Task {task_id}: Error in fallback tool execution for '{tool_name}': {e}", exc_info=True)
                        final_result = ai_response
                        break
                else:
                    logger.warning(f"Task {task_id}: Fallback: No valid tool call detected in content or tool not found.")
                    consecutive_tool_calls = 0 # Reset counter on receiving content or stop signal
                    final_result = ai_response
                    logger.debug(f"Task {task_id}: AI provided final content or signaled stop.")
                    log_event(
                        log_message=LogMessage(LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_completion_signal", f"Task {task_id}: AI provided final content or signaled stop.", subtask_id=task_id)
                    )
                    break # Exit the loop
            else:
                consecutive_tool_calls = 0 # Reset counter on receiving content or stop signal
                final_result = ai_response
                logger.debug(f"Task {task_id}: AI provided final content or signaled stop.")
                log_event(
                    log_message=LogMessage(LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_loop_completion_signal", f"Task {task_id}: AI provided final content or signaled stop.", subtask_id=task_id)
                )
                break # Exit the loop

        else:
            # Unexpected response format (neither tool calls, non-empty content, nor stop signal)
            error_message = f"Task {task_id}: Unexpected AI response format or finish reason in subsequent turn: {ai_response}"
            logger.error(error_message)
            log_event(
                log_message=LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "ai_loop_ai_response_error_subsequent", error_message, subtask_id=task_id)
            )
            raise TaskExecutionError(error_message)

    delegate_manager.invoke_notification(engine, "ai_loop_stopped", {"task_id": task_id})
    return final_result