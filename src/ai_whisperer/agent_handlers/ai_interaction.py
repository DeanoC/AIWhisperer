
# Handler dependencies
import json
import traceback
from pathlib import Path
from datetime import datetime, timezone
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType
from src.ai_whisperer.exceptions import TaskExecutionError, OpenRouterAPIError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError

def handle_ai_interaction(engine, task_definition, task_id):
    """
    Handle an AI interaction task.
    Implementation moved from ExecutionEngine._handle_ai_interaction.
    """
    # 'engine' is the ExecutionEngine instance
    self = engine
    if self.openrouter_api is None:
        error_message = (
            f"AI interaction task {task_id} cannot be executed because OpenRouter API failed to initialize."
        )
        logger = self.config.get('logger', None)
        if logger:
            logger.error(error_message)
        self.monitor.add_log_message(
            LogMessage(
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
    logger = self.config.get('logger', None)
    if logger:
        logger.debug(f"Task {task_id}: Merged AI config: {merged_ai_config}")

    try:
        instructions = task_definition.get("instructions", "")
        input_artifacts = task_definition.get("input_artifacts", [])
        artifact_contents = {}
        prompt_context = ""
        try:
            for artifact in input_artifacts:
                artifact_path = Path(artifact).resolve()
                if artifact_path.exists():
                    with open(artifact_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        artifact_contents[artifact] = content
                        prompt_context += f"Content of {artifact}:\n{content}\n\n"
            if prompt_context and logger:
                logger.info(f"Read input artifacts for task {task_id}: {list(artifact_contents.keys())}")
        except Exception as e:
            error_message = f"Failed to read input artifacts for task {task_id}: {e}"
            if logger:
                logger.error(error_message)
            self.monitor.add_log_message(
                LogMessage(
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
        if logger:
            logger.debug(f"Task {task_id}: agent_type_prompt value: '{agent_type_prompt}', type: {type(agent_type_prompt)}")
        if agent_type_prompt and instructions:
            selected_prompt = agent_type_prompt + "\n\n" + instructions
        elif agent_type_prompt:
            selected_prompt = agent_type_prompt
        elif instructions and self.config.get("global_runner_default_prompt_content"):
            global_default_prompt = self.config["global_runner_default_prompt_content"]
            selected_prompt = global_default_prompt + "\n\n" + instructions
        elif self.config.get("global_runner_default_prompt_content"):
            selected_prompt = self.config["global_runner_default_prompt_content"]
        else:
            error_message = (
                f"No suitable prompt found for AI interaction task {task_id} (agent type: {agent_type})."
            )
            if logger:
                logger.error(error_message)
            self.monitor.add_log_message(
                LogMessage(
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
        if logger:
            logger.info(f"Task {task_id}: Final constructed prompt: {prompt}")

        messages_history = self._collect_ai_history(task_id)
        if logger:
            logger.debug(f"Task {task_id}: Conversation history: {messages_history}")

        ai_response = self.openrouter_api.call_chat_completion(
            prompt_text=prompt,
            model=merged_ai_config.get("model"),
            params=merged_ai_config.get("params", {}),
            messages_history=messages_history,
        )

        if ai_response and ai_response.get("choices"):
            message = ai_response["choices"][0].get("message", {})
            if message.get("tool_calls"):
                if logger:
                    logger.info(f"Task {task_id}: Received tool calls.")
                self.monitor.add_log_message(
                    LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_tool_calls",
                        f"Task {task_id}: Received tool calls.",
                        subtask_id=task_id,
                    )
                )
                result = ai_response
            elif message.get("content") is not None:
                result = message["content"]
                if logger:
                    logger.info(f"Task {task_id}: Received content.")
                self.monitor.add_log_message(
                    LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_content",
                        f"Task {task_id}: Received content.",
                        subtask_id=task_id,
                    )
                )
            else:
                error_message = f"AI interaction task {task_id} received unexpected message format: {message}"
                if logger:
                    logger.error(error_message)
                self.monitor.add_log_message(
                    LogMessage(
                        LogLevel.ERROR,
                        ComponentType.EXECUTION_ENGINE,
                        "ai_task_unexpected_message_format",
                        error_message,
                        subtask_id=task_id,
                        details={"message": message},
                    )
                )
                raise TaskExecutionError(error_message)

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

            # Add usage_info if available in the AI response
            if "usage" in ai_response:
                 assistant_turn["usage_info"] = ai_response["usage"]

            self.state_manager.store_conversation_turn(task_id, assistant_turn)

            output_artifacts_spec = task_definition.get("output_artifacts", [])
            if output_artifacts_spec:
                output_artifact_path_str = output_artifacts_spec[0]
                output_artifact_path = Path(output_artifact_path_str).resolve()
                try:
                    output_artifact_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_artifact_path, "w", encoding="utf-8") as f:
                        if isinstance(result, str):
                            f.write(result)
                        elif isinstance(result, dict):
                            json.dump(result, f, indent=4)
                        else:
                            if logger:
                                logger.warning(
                                    f"Task {task_id}: Unexpected result type for output artifact: {type(result)}. Writing string representation."
                                )
                            f.write(str(result))
                    if logger:
                        logger.info(f"Task {task_id}: Wrote result to output artifact: {output_artifact_path_str}")
                    self.monitor.add_log_message(
                        LogMessage(
                            LogLevel.INFO,
                            ComponentType.EXECUTION_ENGINE,
                            "output_artifact_written",
                            f"Task {task_id}: Wrote result to output artifact: {output_artifact_path_str}",
                            subtask_id=task_id,
                            details={"artifact_path": output_artifact_path_str},
                        )
                    )
                except Exception as e:
                    error_message = (
                        f"Failed to write output artifact {output_artifact_path_str} for task {task_id}: {e}"
                    )
                    if logger:
                        logger.error(error_message)
                    self.monitor.add_log_message(
                        LogMessage(
                            LogLevel.ERROR,
                            ComponentType.EXECUTION_ENGINE,
                            "output_artifact_write_failed",
                            error_message,
                            subtask_id=task_id,
                            details={"artifact_path": output_artifact_path_str, "error": str(e)},
                        )
                    )
                    raise TaskExecutionError(error_message) from e
            return result
        else:
            error_message = f"AI interaction task {task_id} received empty or unexpected response: {ai_response}"
            if logger:
                logger.error(error_message)
            self.monitor.add_log_message(
                LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_task_empty_response",
                    error_message,
                    subtask_id=task_id,
                    details={"response": ai_response},
                )
            )
            raise TaskExecutionError(error_message)

    except (OpenRouterAPIError, OpenRouterAuthError, OpenRouterRateLimitError, OpenRouterConnectionError) as e:
        error_message = f"AI interaction task {task_id} failed due to AI service error: {e}"
        if logger:
            logger.error(error_message, exc_info=True)
        self.monitor.add_log_message(
            LogMessage(
                LogLevel.ERROR,
                ComponentType.EXECUTION_ENGINE,
                "ai_task_service_error",
                error_message,
                subtask_id=task_id,
                details={"error": str(e), "traceback": traceback.format_exc()},
            )
        )
        raise TaskExecutionError(error_message) from e
    except Exception as e:
        error_message = f"An unexpected error occurred during AI interaction task {task_id} execution: {e}"
        if logger:
            logger.exception(error_message)
        self.monitor.add_log_message(
            LogMessage(
                LogLevel.CRITICAL,
                ComponentType.EXECUTION_ENGINE,
                "ai_task_unexpected_error",
                error_message,
                subtask_id=task_id,
                details={"error": str(e), "traceback": traceback.format_exc()},
            )
        )
        raise TaskExecutionError(error_message) from e
