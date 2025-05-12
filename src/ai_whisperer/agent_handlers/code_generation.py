# src/ai_whisperer/agent_handlers/code_generation.py
from src.ai_whisperer.execution_engine import ExecutionEngine
from src.ai_whisperer.exceptions import TaskExecutionError
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType
from src.ai_whisperer.tools.tool_registry import ToolRegistry # Assuming ToolRegistry is accessible
from pathlib import Path
import json
import traceback
from datetime import datetime, timezone

# Potentially import build_ascii_directory_tree if needed
from src.ai_whisperer.utils import build_ascii_directory_tree

def handle_code_generation(engine: ExecutionEngine, task_definition: dict, task_id: str):
    """
    Handles the execution of a 'code_generation' task.

    Orchestrates AI interaction, tool execution (including file I/O and tests),
    and state management for code generation subtasks.
    """
    logger = engine.config.get('logger', None) # Get logger from engine config
    if logger:
        logger.info(f"Starting code_generation handler for task: {task_id}")
    engine.monitor.add_log_message(
        LogMessage(
            LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "code_gen_start",
            f"Starting code generation handler for task {task_id}.", subtask_id=task_id
        )
    )

    # --- Main Handler Logic (detailed in sections below) ---
    try:
        # 1. Context Gathering
        prompt_context = _gather_context(engine, task_definition, task_id, logger)

        # 2. Prompt Construction
        initial_prompt = _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger)

        # 3. AI Interaction & Tool Execution Loop
        final_ai_result, conversation_history = _run_ai_interaction_loop(engine, task_definition, task_id, initial_prompt, logger)
        if logger:
             logger.info(f"Task {task_id}: AI interaction loop finished.")


        # 4. Test Execution / Validation
        validation_passed, validation_details = _execute_validation(engine, task_definition, task_id, logger)
        if logger:
             logger.info(f"Task {task_id}: Validation executed. Passed: {validation_passed}")

        print(f"DEBUG: Task {task_id}: Validation passed: {validation_passed}") # Debug print

        # 5. Final Result Processing & State Update
        if validation_passed:
            final_task_result = {
                "message": "Code generation completed and validation passed.",
                "ai_result": final_ai_result, # Could be final AI message or last tool outputs
                "validation_details": validation_details
            }
            if logger:
                logger.info(f"Task {task_id} completed successfully.")
            engine.monitor.add_log_message(
                LogMessage(
                    LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "code_gen_success",
                    f"Code generation task {task_id} completed and validated successfully.", subtask_id=task_id,
                    details=validation_details
                )
            )
            # StateManager update happens in the main engine loop upon successful return
            return final_task_result # Return structured result
        else:
            print(f"DEBUG: Task {task_id}: Validation failed. Raising TaskExecutionError.") # Debug print
            error_message = f"Code generation task {task_id} failed validation."
            if logger:
                logger.error(f"{error_message} Details: {validation_details}")
            engine.monitor.add_log_message(
                LogMessage(
                    LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_validation_failed",
                    error_message, subtask_id=task_id, details=validation_details
                )
            )
            raise TaskExecutionError(error_message, details=validation_details)

    except TaskExecutionError as e:
        # TaskExecutionError is already logged within the function that raised it.
        # Re-raise for the main engine loop to catch and set task state to failed.
        # No need to log again here or wrap in another TaskExecutionError.
        raise e
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error in handle_code_generation for task {task_id}: {e}"
        if logger:
            logger.error(error_message, exc_info=True)
        engine.monitor.add_log_message(
            LogMessage(
                LogLevel.CRITICAL, ComponentType.EXECUTION_ENGINE, "code_gen_unexpected_error",
                error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()}
            )
        )
        # Raise as TaskExecutionError for consistent handling in the main engine loop
        raise TaskExecutionError(error_message) from e

# --- Helper Functions (Private to the handler module) ---

def _gather_context(engine, task_definition, task_id, logger) -> str:
    """Gathers context from input_artifacts."""
    context = []
    artifacts = task_definition.get('input_artifacts', [])
    if logger:
        logger.debug(f"Task {task_id}: Gathering context from artifacts: {artifacts}")

    for artifact_path_str in artifacts:
        artifact_path = Path(artifact_path_str)
        try:
            if artifact_path.is_file():
                content = artifact_path.read_text()
                context.append(f"--- File: {artifact_path_str} ---\n{content}\n--- End File: {artifact_path_str} ---\n")
                if logger:
                    logger.debug(f"Task {task_id}: Read file: {artifact_path_str}")
            elif artifact_path.is_dir():
                tree = build_ascii_directory_tree(artifact_path)
                context.append(f"--- Directory Tree: {artifact_path_str} ---\n{tree}\n--- End Directory Tree: {artifact_path_str} ---\n")
                if logger:
                    logger.debug(f"Task {task_id}: Generated directory tree for: {artifact_path_str}")
            else:
                if logger:
                    logger.warning(f"Task {task_id}: Artifact not found or not a file/directory: {artifact_path_str}")
                context.append(f"--- Artifact Not Found: {artifact_path_str} ---\nContent not available.\n--- End Artifact Not Found: {artifact_path_str} ---\n")
        except FileNotFoundError:
            if logger:
                logger.warning(f"Task {task_id}: File not found for artifact: {artifact_path_str}")
            context.append(f"--- File Not Found: {artifact_path_str} ---\nContent not available.\n--- End File Not Found: {artifact_path_str} ---\n")
        except IOError as e:
            if logger:
                logger.warning(f"Task {task_id}: Error reading artifact {artifact_path_str}: {e}")
            context.append(f"--- Error Reading Artifact: {artifact_path_str} ---\nError: {e}\n--- End Error Reading Artifact: {artifact_path_str} ---\n")
        except Exception as e:
            if logger:
                logger.error(f"Task {task_id}: Unexpected error processing artifact {artifact_path_str}: {e}", exc_info=True)
            context.append(f"--- Unexpected Error Processing Artifact: {artifact_path_str} ---\nError: {e}\n--- End Unexpected Error Processing Artifact: {artifact_path_str} ---\n")

    return "\n".join(context)

def _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger) -> str:
    """Constructs the initial prompt for the AI agent."""
    # Get the base system prompt from the default prompt file
    try:
        base_prompt_path = Path("prompts/code_generation_default.md")
        base_prompt = base_prompt_path.read_text()
        if logger:
            logger.debug(f"Task {task_id}: Read base prompt from {base_prompt_path}")
    except FileNotFoundError:
        base_prompt = "You are an expert software engineer AI agent."
        if logger:
            logger.warning(f"Task {task_id}: Base prompt file not found. Using default: {base_prompt_path}")
    except IOError as e:
        base_prompt = "You are an expert software engineer AI agent."
        if logger:
            logger.warning(f"Task {task_id}: Error reading base prompt file {base_prompt_path}: {e}. Using default.")

    prompt_parts = [
        base_prompt,
        "\n\n--- Task Description ---",
        task_definition.get('description', 'No description provided.'),
        "\n\n--- Instructions ---",
        "\n".join(task_definition.get('instructions', ['No instructions provided.'])),
        "\n\n--- Context ---",
        prompt_context if prompt_context else "No input artifacts provided or context gathered.",
        "\n\n--- Constraints ---",
        "\n".join(task_definition.get('constraints', ['No constraints provided.'])),
        "\n\n--- Raw Task JSON ---",
        task_definition.get('raw_text', json.dumps(task_definition, indent=2)) # Use raw_text if available, otherwise dump the dict
    ]

    initial_prompt = "\n".join(prompt_parts)

    if logger:
        logger.debug(f"Task {task_id}: Constructed initial prompt.")

    return initial_prompt

def _run_ai_interaction_loop(engine, task_definition, task_id, initial_prompt, logger) -> tuple[dict, list]:
    """Manages the AI interaction loop, including tool execution."""
    conversation_history = [] # Start with an empty history, add initial prompt before first call
    final_result = None
    tool_registry = ToolRegistry() # Get the tool registry instance
    consecutive_tool_calls = 0 # Counter for consecutive tool-only responses
    MAX_CONSECUTIVE_TOOL_CALLS = 5 # Threshold to detect potential infinite loops

    # Add the initial user prompt to the state manager and conversation history
    user_prompt_entry = {"role": "user", "content": initial_prompt}
    engine.state_manager.store_conversation_turn(task_id, user_prompt_entry)
    conversation_history.append(user_prompt_entry)


    if logger:
        logger.debug(f"Task {task_id}: Entering AI interaction loop.")

    # First AI call with prompt_text
    try:
        if logger:
            logger.debug(f"Task {task_id}: Calling AI with initial prompt_text.")

        params = {
            'temperature': engine.config.get('ai_temperature', 0.1) # Use temperature from config
        }
        ai_response = engine.openrouter_api.call_chat_completion(
            prompt_text=initial_prompt, # Pass initial prompt as prompt_text
            model=engine.config.get('ai_model', 'google/gemini-2.5-flash-preview'), # Use model from config
            params=params,
            messages_history=conversation_history # Include history for context
        )

        if logger:
            logger.debug(f"Task {task_id}: Initial AI call completed.")

        # Store the assistant's response in the state manager and conversation history
        engine.state_manager.store_conversation_turn(task_id, ai_response)
        conversation_history.append(ai_response)

    except Exception as e:
        error_message = f"Task {task_id}: Error during initial AI call: {e}"
        if logger:
            logger.error(error_message, exc_info=True)
        engine.monitor.add_log_message(
            LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_initial_ai_call_error", error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()})
        )
        raise TaskExecutionError(error_message) from e


    # Subsequent AI interaction loop
    while True:
        if logger:
            logger.debug(f"Task {task_id}: Start of subsequent AI interaction loop iteration.")

        # Process the AI response from the previous turn
        message = ai_response.get('choices', [{}])[0].get('message', {})
        tool_calls = message.get('tool_calls')
        content = message.get('content')

        if tool_calls is not None and isinstance(tool_calls, list) and len(tool_calls) > 0:
            # AI wants to use tools
            consecutive_tool_calls += 1
            if consecutive_tool_calls > MAX_CONSECUTIVE_TOOL_CALLS:
                error_message = f"Task {task_id}: Exceeded maximum consecutive tool calls ({MAX_CONSECUTIVE_TOOL_CALLS}). Potential infinite loop detected."
                if logger:
                    logger.error(error_message)
                engine.monitor.add_log_message(
                    LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_infinite_loop", error_message, subtask_id=task_id)
                )
                raise TaskExecutionError(error_message)

            if logger:
                logger.debug(f"Task {task_id}: AI requested tool calls: {tool_calls}")

            tool_outputs = []
            for tool_call in tool_calls:
                tool_name = tool_call.get('function', {}).get('name')
                tool_arguments_str = tool_call.get('function', {}).get('arguments', '{}')
                tool_call_id = tool_call.get('id')

                if not tool_name or not tool_call_id:
                    if logger:
                        logger.error(f"Task {task_id}: Invalid tool call received: {tool_call}")
                    tool_outputs.append({
                        "tool_call_id": tool_call_id or "unknown",
                        "output": f"Error: Invalid tool call format."
                    })
                    continue

                try:
                    tool_arguments = json.loads(tool_arguments_str)
                    if logger:
                        logger.debug(f"Task {task_id}: Executing tool: {tool_name} with args: {tool_arguments}")

                    tool_instance = tool_registry.get_tool(tool_name)
                    tool_output_data = tool_instance.execute(**tool_arguments)

                    # Format tool output for the next AI turn
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": json.dumps(tool_output_data) if isinstance(tool_output_data, (dict, list)) else str(tool_output_data)
                    })
                    if logger:
                        logger.debug(f"Task {task_id}: Tool {tool_name} executed successfully.")

                except json.JSONDecodeError as e:
                    print(f"DEBUG: Task {task_id}: Caught JSONDecodeError for tool {tool_name}. Arguments: {tool_arguments_str}") # Debug print
                    error_message = f"Task {task_id}: Failed to parse tool arguments JSON for tool '{tool_name}': {e}. Arguments: {tool_arguments_str}"
                    if logger:
                        logger.error(error_message)
                    engine.monitor.add_log_message(
                        LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "tool_call_invalid_arguments",
                            error_message, subtask_id=task_id, details={"tool_name": tool_name, "arguments": tool_arguments_str, "error": str(e)}
                        )
                    )
                    # Raise TaskExecutionError on JSON decoding failure
                    raise TaskExecutionError(error_message) from e
                except tool_registry.ToolNotFound:
                    error_message = f"Task {task_id}: Tool not found: {tool_name}"
                    if logger:
                        logger.error(error_message)
                    engine.monitor.add_log_message(
                        LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "tool_not_found",
                            error_message, subtask_id=task_id, details={"tool_name": tool_name}
                        )
                    )
                    # Decide whether to fail the task or just skip this tool call
                    # For now, we'll log and skip this specific tool call
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": f"Error: Tool '{tool_name}' not found."
                    })
                    continue
                except Exception as e:
                    error_message = f"Task {task_id}: Error executing tool '{tool_name}': {e}"
                    if logger:
                        logger.error(error_message, exc_info=True)
                    engine.monitor.add_log_message(
                        LogMessage(
                            LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "tool_execution_error",
                            error_message, subtask_id=task_id, details={"tool_name": tool_name, "error": str(e), "traceback": traceback.format_exc()}
                        )
                    )
                    # Decide whether to fail the task or just skip this tool call
                    # For now, we'll log and skip this specific tool call
                    tool_outputs.append({
                        "tool_call_id": tool_call_id,
                        "output": f"Error executing tool {tool_name}: {e}"
                    })
                    continue
                
            # Add tool outputs to conversation history and state manager
            for output in tool_outputs:
                 tool_output_entry = {"role": "tool", "tool_call_id": output["tool_call_id"], "content": output["output"]}
                 conversation_history.append(tool_output_entry)
                 engine.state_manager.store_conversation_turn(task_id, tool_output_entry)

            # Call AI again with updated history
            try:
                if logger:
                    logger.debug(f"Task {task_id}: Calling AI with updated conversation history.")

                params = {
                    'temperature': engine.config.get('ai_temperature', 0.1) # Use temperature from config
                }
                ai_response = engine.openrouter_api.call_chat_completion(
                    messages_history=conversation_history,
                    model=engine.config.get('ai_model', 'google/gemini-2.5-flash-preview'), # Use model from config
                    params=params
                )

                if logger:
                    logger.debug(f"Task {task_id}: AI call with updated history completed.")

                # Store the assistant's response in the state manager and conversation history
                engine.state_manager.store_conversation_turn(task_id, ai_response)
                conversation_history.append(ai_response)

            except Exception as e:
                error_message = f"Task {task_id}: Error during AI call with updated history: {e}"
                if logger:
                    logger.error(error_message, exc_info=True)
                engine.monitor.add_log_message(
                    LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_subsequent_ai_call_error", error_message, subtask_id=task_id, details={"error": str(e), "traceback": traceback.format_exc()})
                )
                raise TaskExecutionError(error_message) from e


        elif content is not None:
            # AI provided content, conversation is likely finished
            consecutive_tool_calls = 0 # Reset counter on receiving content
            final_result = ai_response
            if logger:
                logger.debug(f"Task {task_id}: AI provided final content.")
            break # Exit the loop

        else:
            # Unexpected response format
            error_message = f"Task {task_id}: Unexpected AI response format in subsequent turn: {ai_response}"
            if logger:
                logger.error(error_message)
            engine.monitor.add_log_message(
                LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_ai_response_error_subsequent", error_message, subtask_id=task_id)
            )
            raise TaskExecutionError(error_message)

    return final_result, conversation_history

def _execute_validation(engine, task_definition, task_id, logger) -> tuple[bool, dict]:
    """Executes validation criteria, typically shell commands."""
    validation_criteria = task_definition.get('validation_criteria')
    validation_details = {"commands_executed": [], "overall_status": "skipped"}
    overall_passed = True

    if isinstance(validation_criteria, list) and all(isinstance(cmd, str) for cmd in validation_criteria):
        validation_details["overall_status"] = "pending"
        if logger:
            logger.debug(f"Task {task_id}: Executing validation commands: {validation_criteria}")

        try:
            tool_registry = ToolRegistry()
            execute_command_tool = tool_registry.get_tool('execute_command')

            if execute_command_tool is None:
                error_message = f"Task {task_id}: Execute command tool not found for validation."
                if logger:
                    logger.error(error_message)
                validation_details["overall_status"] = "failed"
                validation_details["commands_executed"].append({"command": "N/A", "exit_code": 1, "stdout": "", "stderr": error_message})

            for command in validation_criteria:
                try:
                    if logger:
                        logger.info(f"Task {task_id}: Running validation command: {command}")
                    # Assuming execute_command tool returns a dict with exit_code, stdout, stderr
                    command_result = execute_command_tool.execute(command=command)
                    exit_code = command_result.get('exit_code', 1) # Default to 1 if not provided
                    stdout = command_result.get('stdout', '')
                    stderr = command_result.get('stderr', '')

                    validation_details["commands_executed"].append({
                        "command": command,
                        "exit_code": exit_code,
                        "stdout": stdout,
                        "stderr": stderr
                    })

                    if exit_code != 0:
                        overall_passed = False
                        if logger:
                            logger.error(f"Task {task_id}: Validation command failed: {command} with exit code {exit_code}")
                        # Continue executing other commands to gather all results

                except Exception as e:
                    overall_passed = False
                    error_message = f"Task {task_id}: Error executing validation command '{command}': {e}"
                    if logger:
                        logger.error(error_message, exc_info=True)
                    validation_details["commands_executed"].append({
                        "command": command,
                        "exit_code": 1, # Indicate failure
                        "stdout": "",
                        "stderr": error_message
                    })
                    # Continue executing other commands

            validation_details["overall_status"] = "passed" if overall_passed else "failed"
            if logger:
                logger.info(f"Task {task_id}: Validation finished. Overall status: {validation_details['overall_status']}")

        # Remove the incorrect exception catch
        except Exception as e:
            overall_passed = False
            error_message = f"Task {task_id}: Unexpected error during validation execution: {e}"
            if logger:
                logger.error(error_message, exc_info=True)
            validation_details["overall_status"] = "failed"
            validation_details["commands_executed"].append({"command": "N/A", "exit_code": 1, "stdout": "", "stderr": error_message})
         
    else:
        if logger:
            logger.warning(f"Task {task_id}: No executable validation criteria found or format is incorrect.")
        validation_details["overall_status"] = "skipped"
        overall_passed = True # Treat skipped validation as passed for now

    return overall_passed, validation_details
