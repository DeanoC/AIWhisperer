import threading # Import threading for shutdown_event type hint

# Handler dependencies
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import MagicMock
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import log_event
from src.ai_whisperer.exceptions import TaskExecutionError, OpenRouterAPIError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError
from src.ai_whisperer.utils import build_ascii_directory_tree # Ensure this is imported

# Assuming logger is defined at the module level in the original file
import logging
logger = logging.getLogger(__name__)


def handle_ai_interaction(
    engine, 
    task_definition, 
    task_id
) -> dict:
    """
    Handle an AI interaction task.

    Returns:
        dict: The result of the AI interaction, always as a dictionary.
    """
    # 'engine' is the ExecutionEngine instance
    self = engine

    if self.openrouter_api is None:
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
        selected_prompt = None
        agent_type_prompt = self.config.get("runner_agent_type_prompts_content", {}).get(agent_type)
        if agent_type_prompt is not None:
            agent_type_prompt = agent_type_prompt.strip()
        # Use the module-level logger
        logger.debug(f"Task {task_id}: agent_type_prompt value: '{agent_type_prompt}', type: {type(agent_type_prompt)}")
        if agent_type_prompt and instructions:
            selected_prompt = agent_type_prompt + "\n\n" + instructions
        elif agent_type_prompt:
            selected_prompt = agent_type_prompt
        elif instructions and self.config.get("global_runner_default_prompt_content"):
            global_default_prompt = self.config["global_runner_default_prompt_content"]
            selected_prompt = global_default_prompt + "\n\n" + "\n\n".join(instructions)
        elif self.config.get("global_runner_default_prompt_content"):
            selected_prompt = self.config["global_runner_default_prompt_content"]
        else:
            error_message = (
                f"No suitable prompt found for AI interaction task {task_id} (agent type: {agent_type})."
            )
            # Use the module-level logger
            logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "no_prompt_found",
                    error_message,
                    subtask_id=task_id,
                )
            )
            raise TaskExecutionError(error_message)

        if prompt_context and selected_prompt:
            selected_prompt += "\n\n" + "## PROMPT CONTEXT " + prompt_context.strip()
        prompt = selected_prompt
        raw_subtask_text = task_definition.get("raw_text", "")
        if raw_subtask_text:
            prompt += "\n\n" + "## RAW SUBTASK TEXT\n" + raw_subtask_text
        # Use the module-level logger
        logger.info(f"Task {task_id}: Final constructed prompt: {prompt}")

        messages_history = self._collect_ai_history(task_id)
        # Use the module-level logger
        logger.debug(f"Task {task_id}: Conversation history: {messages_history}")

        # Use streaming API call to allow for interruption
        stream_generator = self.openrouter_api.stream_chat_completion(
            prompt_text=prompt,
            model=merged_ai_config.get("model"),
            params=merged_ai_config.get("params", {}),
            messages_history=messages_history,
        )

        full_response_content = ""
        tool_calls = []
        usage_info = None # To capture usage info from the last chunk


        try: # Try block for processing the stream
            print(f'DEBUG: stream_generator type: {type(stream_generator)}, is_mock: {isinstance(stream_generator, MagicMock)}')
            for chunk in stream_generator:
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

                # Process the chunk
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                if "content" in delta:
                    full_response_content += delta["content"]
                    # Optionally update monitor with streamed content
                    # self.monitor.update_ai_response(task_id, full_response_content)

                if "tool_calls" in delta:
                    # Accumulate tool calls. This might require more sophisticated handling
                    # if tool calls are split across chunks. For simplicity, assuming
                    # tool_calls delta contains the full list or appendable parts.
                    # A robust implementation would reconstruct tool calls from deltas.
                    # For now, we'll just store the last received tool_calls delta.
                    # This needs refinement for real-world tool call streaming.
                    if delta["tool_calls"] is not None: # Ensure it's not null
                         tool_calls.extend(delta["tool_calls"])

                # Capture usage info from the last chunk (often present in the final chunk)
                if "usage" in chunk:
                     usage_info = chunk["usage"]


            # After the stream finishes, process the full response
            if tool_calls:
                result = {"tool_calls": tool_calls}
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
            elif full_response_content:
                result = full_response_content
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
            else:
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

            if isinstance(result, str):
                assistant_turn["content"] = result
            elif isinstance(result, dict) and result.get("tool_calls"):
                assistant_turn["tool_calls"] = result["tool_calls"]

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
                        if isinstance(result, str):
                            f.write(result)
                        elif isinstance(result, dict):
                            json.dump(result, f, indent=4)
                        else:
                            # Use the module-level logger
                            logger.warning(
                                f"Task {task_id}: Unexpected result type for output artifact: {type(result)}. Writing string representation."
                            )
                            f.write(str(result))
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
            assert isinstance(result, dict), (
                f"Unexpected result type for task {task_id}: {type(result)}. Expected dict."
            )
            return result # Return the processed result

        except (OpenRouterAPIError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError) as e:
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
