import threading # Import threading for shutdown_event type hint

# Handler dependencies
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import log_event
from ai_whisperer.exceptions import TaskExecutionError, OpenRouterAIServiceError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError
from ai_whisperer.utils import build_ascii_directory_tree # Ensure this is imported
from ai_whisperer import PromptSystem # Import PromptSystem

# Assuming logger is defined at the module level in the original file
import logging
logger = logging.getLogger(__name__)


async def handle_ai_interaction( # Make async
        engine: ExecutionEngine,
        task_definition: dict,
        prompt_system: PromptSystem # Accept PromptSystem instance
) -> dict:
    """
    Handle an AI interaction task.

    Returns:
        dict: The result of the AI interaction, always as a dictionary.
    """
    # 'engine' is the ExecutionEngine instance
    self = engine
    task_id = task_definition.get("task_id")

    if self.aiservice is None:
        error_message = (
            f"AI interaction task {task_id} cannot be executed because OpenRouter API failed to initialize."
        )
        # Use the module-level logger
        logger.error(error_message)
        log_event(
            log_message=LogMessage(
                LogLevel.ERROR,
                ComponentType.EXECUTION_ENGINE,
                "ai_task_api_not_initialized",
                error_message,
                subtask_id=task_id,
            )
        )
        raise TaskExecutionError(error_message)

    task_ai_config = {}
    merged_ai_config = {
        **self.config.get("openrouter", {}),
        **task_ai_config,
    }
    # Use the module-level logger
    logger.debug(f"Task {task_id}: Merged AI config: {merged_ai_config}")

    try: # Outer try block to catch general exceptions during task execution
        instructions = task_definition.get("instructions", "")
        input_artifacts = task_definition.get("input_artifacts", [])
        artifact_contents = {}
        prompt_context = ""

        try: # Inner try block for artifact reading
            for artifact in input_artifacts:
                artifact_path = Path(artifact).resolve()
                if artifact_path.exists():
                    if artifact_path.is_file():
                        with open(artifact_path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            artifact_contents[artifact] = content
                            prompt_context += f"Content of {artifact}:\n{content}\n\n"
                    elif artifact_path.is_dir():
                        # If it's a directory, list its contents using the tree function
                        try:
                            tree_output = build_ascii_directory_tree(str(artifact_path))
                            artifact_contents[artifact] = tree_output # Store tree output as content
                            prompt_context += f"Directory structure of {artifact}:\n{tree_output}\n\n"
                            # Use the module-level logger
                            logger.info(f"Task {task_id}: Listed directory contents for {artifact}")
                        except Exception as tree_e:
                            error_message = f"Failed to list directory contents for {artifact} in task {task_id}: {tree_e}"
                            # Use the module-level logger
                            logger.error(error_message)
                            # Optionally add error to prompt context or logs
                            prompt_context += f"Error listing directory {artifact}: {tree_e}\n\n"
            if prompt_context: # Check prompt_context before logging
                # Use the module-level logger
                logger.info(f"Read input artifacts for task {task_id}: {list(artifact_contents.keys())}")
        except Exception as e: # Catch exceptions during artifact reading
            error_message = f"Failed to read input artifacts for task {task_id}: {e}"
            # Use the module-level logger
            logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "artifacts_read_failed",
                    error_message,
                    subtask_id=task_id,
                )
            )
            raise TaskExecutionError(error_message) from e



        agent_type = task_definition.get("type")
        instructions = task_definition.get("instructions", "")
        raw_subtask_text = task_definition.get("raw_text", "") # Get raw subtask text

        logger.info(f"Task {task_id}: Constructing prompt for agent type: {agent_type}")

        try:
            # Use PromptSystem to get the formatted prompt
            # Assuming agent_type maps directly to prompt name in 'agents' category
            prompt = prompt_system.get_formatted_prompt(
                "agents",
                agent_type,
                include_tools=True, # Include tool instructions
                instructions=instructions,
                prompt_context=prompt_context,
                raw_subtask_text=raw_subtask_text
            )
            logger.info(f"Task {task_id}: Final constructed prompt (length: {len(prompt)} chars)")
            log_event(
                log_message=LogMessage(
                    LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "ai_task_final_prompt",
                    f"Final prompt for task {task_id} (length: {len(prompt)} chars)", subtask_id=task_id
                )
            )

        except prompt_system.PromptNotFoundError as e:
             error_message = f"Prompt not found for agent type '{agent_type}' for task {task_id}: {e}"
             logger.error(error_message)
             log_event(
                 log_message=LogMessage(
                     LogLevel.ERROR,
                     ComponentType.EXECUTION_ENGINE,
                     "ai_task_prompt_not_found",
                     error_message,
                     subtask_id=task_id,
                     details={"agent_type": agent_type, "error": str(e)},
                 )
             )
             raise TaskExecutionError(error_message) from e
        except Exception as e:
             error_message = f"An unexpected error occurred while constructing prompt for task {task_id}: {e}"
             logger.exception(error_message)
             log_event(
                 log_message=LogMessage(
                     LogLevel.CRITICAL,
                     ComponentType.EXECUTION_ENGINE,
                     "ai_task_prompt_construction_error",
                     error_message,
                     subtask_id=task_id,
                     details={"agent_type": agent_type, "error": str(e), "traceback": traceback.format_exc()},
                 )
             )
             raise TaskExecutionError(error_message) from e


        messages_history = self._collect_ai_history(task_id)
        # Use the module-level logger
        logger.debug(f"Task {task_id}: Conversation history: {messages_history}")

        # Use streaming API call to allow for interruption
        stream_generator = self.aiservice.stream_chat_completion( # This is an async generator
            prompt_text=prompt,
            model=merged_ai_config.get("model"),
            params=merged_ai_config.get("params", {}),
            messages_history=messages_history,
        )

        full_response_content = ""
        tool_calls = []
        usage_info = None # To capture usage info from the last chunk


        try: # Try block for processing the stream
            async for chunk in stream_generator: # Use async for
                # Check for shutdown signal during streaming
                if self.shutdown_event.is_set():
                    # Use the module-level logger
                    logger.info(f"Task {task_id}: Shutdown signal received during AI streaming. Stopping.")
                    log_event(
                        log_message=LogMessage(
                            LogLevel.INFO,
                            ComponentType.EXECUTION_ENGINE,
                            "ai_task_streaming_interrupted",
                            f"Task {task_id}: AI streaming interrupted by shutdown signal.",
                            subtask_id=task_id,
                        )
                    )
                    # Raise an exception to stop processing this task
                    raise TaskExecutionError(f"Task {task_id} interrupted by shutdown signal during AI streaming.")

                # Process the chunk (assuming AIStreamChunk structure from ai_service.py)
                if chunk.delta_content:
                    full_response_content += chunk.delta_content
                
                # For simplicity, assuming tool_calls are sent in full in one chunk or accumulated correctly
                # A more robust implementation would handle partial tool_call deltas.
                # This part needs to align with how OpenRouterAIService yields tool call information.
                # For now, let's assume if a chunk has tool_calls, it's the complete list for that turn.
                # The AIStreamChunk does not directly have a 'tool_calls' attribute in its definition.
                # This logic needs to be consistent with what AIService.stream_chat_completion yields.
                # If tool calls are part of delta_tool_call_part, that needs to be accumulated and parsed.
                # For now, this part is simplified and might need adjustment based on actual stream format for tools.
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls: # Placeholder for actual tool call streaming logic
                    tool_calls.extend(chunk.tool_calls)
                
                if hasattr(chunk, 'usage') and chunk.usage: # Placeholder for usage info
                    usage_info = chunk.usage


            # After the stream finishes, process the full response

            # Always return a dict for consistency
            result_dict = {}
            if tool_calls:
                result_dict["tool_calls"] = tool_calls
                # Use the module-level logger
                logger.info(f"Task {task_id}: Received tool calls from stream.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_tool_calls_stream",
                        f"Task {task_id}: Received tool calls from stream.",
                        subtask_id=task_id,
                    )
                )
            if full_response_content:
                result_dict["content"] = full_response_content
                # Use the module-level logger
                logger.info(f"Task {task_id}: Received content from stream.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_content_stream",
                        f"Task {task_id}: Received content from stream.",
                        subtask_id=task_id,
                    )
                )
            if not result_dict:
                error_message = f"AI interaction task {task_id} received empty or unexpected streamed response."
                # Use the module-level logger
                logger.error(error_message)
                log_event(
                    log_message=LogMessage(
                        LogLevel.ERROR,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_empty_stream_response",
                        error_message,
                        subtask_id=task_id,
                    )
                )
                raise TaskExecutionError(error_message)

            # Store the conversation turn in the state manager for history
            user_turn = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self.state_manager.store_conversation_turn(task_id, user_turn)

            assistant_turn = {
                "role": "assistant",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if "content" in result_dict:
                assistant_turn["content"] = result_dict["content"]
            if "tool_calls" in result_dict:
                assistant_turn["tool_calls"] = result_dict["tool_calls"]

            # Add usage_info if captured
            if usage_info:
                 assistant_turn["usage_info"] = usage_info

            self.state_manager.store_conversation_turn(task_id, assistant_turn)

            # Handle output artifacts (write the final result)
            output_artifacts_spec = task_definition.get("output_artifacts", [])
            if output_artifacts_spec:
                output_artifact_path_str = output_artifacts_spec[0]
                output_artifact_path = Path(output_artifact_path_str).resolve()
                try: # Try block for writing output artifact
                    output_artifact_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_artifact_path, "w", encoding="utf-8") as f:
                        if "content" in result_dict:
                            f.write(result_dict["content"])
                        elif "tool_calls" in result_dict:
                            json.dump(result_dict["tool_calls"], f, indent=4)
                        else:
                            # Use the module-level logger
                            logger.warning(
                                f"Task {task_id}: Unexpected result type for output artifact: {type(result_dict)}. Writing string representation."
                            )
                            f.write(str(result_dict))
                    # Use the module-level logger
                    logger.info(f"Task {task_id}: Wrote result to output artifact: {output_artifact_path_str}")
                    log_event(
                        log_message=LogMessage(
                            LogLevel.INFO,
                            ComponentType.EXECUTION_ENGINE,
                            "output_artifact_written",
                            f"Task {task_id}: Wrote result to output artifact: {output_artifact_path_str}",
                            subtask_id=task_id,
                            details={"artifact_path": output_artifact_path_str},
                        )
                    )
                except Exception as e: # Catch exceptions during output artifact writing
                    error_message = (
                        f"Failed to write output artifact {output_artifact_path_str} for task {task_id}: {e}"
                    )
                    # Use the module-level logger
                    logger.error(error_message)
                    log_event(
                        log_message=LogMessage(
                            LogLevel.ERROR,
                            ComponentType.EXECUTION_ENGINE,
                            "output_artifact_write_failed",
                            error_message,
                            subtask_id=task_id,
                            details={"artifact_path": output_artifact_path_str, "error": str(e)},
                        )
                    )
                    raise TaskExecutionError(error_message) from e
            return result_dict # Always return a dict

        except (OpenRouterAIServiceError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError) as e:
            error_message = f"AI interaction task {task_id} failed due to AI service error: {e}"
            # Use the module-level logger
            logger.error(error_message, exc_info=True)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_task_service_error",
                    error_message,
                    subtask_id=task_id,
                    details={"error": str(e), "traceback": traceback.format_exc()},
                )
            )
            raise TaskExecutionError(error_message) from e
    except TaskExecutionError:
            # Re-raise TaskExecutionError if it was raised internally (e.g., by shutdown)
            raise
    except Exception as e: # Catch any other unexpected errors during processing
        error_message = f"An unexpected error occurred during AI interaction task {task_id} execution: {e}"
        # Use the module-level logger
        logger.exception(error_message)
        log_event(
            log_message=LogMessage(
                LogLevel.CRITICAL,
                ComponentType.EXECUTION_ENGINE,
                "ai_task_unexpected_error",
                error_message,
                subtask_id=task_id,
                details={"error": str(e), "traceback": traceback.format_exc()},
            )
        )
        raise TaskExecutionError(error_message) from e
