# src/ai_whisperer/agent_handlers/code_generation.py
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, get_logger, log_event # Import log_event
from ai_whisperer.tools.tool_registry import ToolRegistry # Assuming ToolRegistry is accessible
from ai_whisperer.context_management import ContextManager # Import ContextManager
from ai_whisperer.ai_loop import run_ai_loop # Import the refactored AI loop
from pathlib import Path
import os
import json
from ai_whisperer import PromptSystem # Import PromptSystem
from ai_whisperer.prompt_system import PromptNotFoundError
import traceback
from datetime import datetime, timezone

# Potentially import build_ascii_directory_tree if needed
from ai_whisperer.utils import build_ascii_directory_tree

logger = get_logger(__name__)  # Get logger for execution engine

def handle_code_generation(engine: ExecutionEngine, task_definition: dict, prompt_system: PromptSystem):
    """
    Handles the execution of a 'code_generation' task.
    """
    task_id = task_definition.get('subtask_id')
    logger.info(f"Starting code_generation handler for task: {task_id}")
    logger.debug(f"Task {task_id}: Received task_definition: {task_definition}")
    log_event(
        log_message=LogMessage(
            LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "code_gen_start",
            f"Starting code generation handler for task {task_id}.", subtask_id=task_id,
            details={"task_definition_keys": list(task_definition.keys())}
        )
    )

    # --- Main Handler Logic (detailed in sections below) ---
    try:
        # 1. Context Gathering
        prompt_context = _gather_context(engine, task_definition, task_id, logger)

        # 2. Prompt Construction
        initial_prompt = _construct_initial_prompt(prompt_system, task_definition, task_id, prompt_context, logger)
 
        # 3. AI Interaction & Tool Execution Loop
        # Get ContextManager from StateManager
        context_manager = engine.state_manager.get_context_manager(task_id)
        if context_manager is None:
            raise TaskExecutionError(f"ContextManager not found for task {task_id} in StateManager.")

        # Pass delegate_manager to run_ai_loop (required argument)
        delegate_manager = getattr(engine, 'delegate_manager', None)
        if delegate_manager is None:
            logger.warning(f"Task {task_id}: DelegateManager not found on engine. Proceeding without delegate notifications.") # Change error to warning
            # We can still proceed with run_ai_loop, but delegate notifications within the loop will be skipped
        final_ai_result = run_ai_loop(engine, task_definition, task_id, initial_prompt, logger, context_manager, delegate_manager)
        logger.info(f"Task {task_id}: AI interaction loop finished.")


        # 4. Test Execution / Validation
        # NOTE: Validation is currently faked as per user instruction.
        validation_passed, validation_details = _execute_validation(engine, task_definition, task_id, logger)
        logger.info(f"Task {task_id}: Validation executed. Passed: {validation_passed}")

        # 5. Final Result Processing & State Update
        if validation_passed:
            final_task_result = {
                "message": "Code generation completed and validation passed.",
                "ai_result": final_ai_result, # Could be final AI message or last tool outputs
                "validation_details": validation_details
            }
            logger.info(f"Task {task_id} completed successfully.")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "code_gen_success",
                    f"Code generation task {task_id} completed and validated successfully.", subtask_id=task_id,
                    details=validation_details
                )
            )
            # StateManager update happens in the main engine loop upon successful return
            return final_task_result # Return structured result
        else:
            error_message = f"Code generation task {task_id} failed validation."
            logger.error(f"{error_message} Details: {validation_details}")
            log_event(
                log_message=LogMessage(
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
        logger.error(error_message, exc_info=True)
        log_event(
            log_message=LogMessage(
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
                logger.debug(f"Task {task_id}: Generated directory tree for: {artifact_path_str}")
            else:
                logger.warning(f"Task {task_id}: Artifact not found or not a file/directory: {artifact_path_str}")
                context.append(f"--- Artifact Not Found: {artifact_path_str} ---\nContent not available.\n--- End Artifact Not Found: {artifact_path_str} ---\n")
        except FileNotFoundError:
            logger.warning(f"Task {task_id}: File not found for artifact: {artifact_path_str}")
            context.append(f"--- File Not Found: {artifact_path_str} ---\nContent not available.\n--- End File Not Found: {artifact_path_str} ---\n")
        except IOError as e:
            logger.warning(f"Task {task_id}: Error reading artifact {artifact_path_str}: {e}")
            context.append(f"--- Error Reading Artifact: {artifact_path_str} ---\nError: {e}\n--- End Error Reading Artifact: {artifact_path_str} ---\n")
        except Exception as e:
            logger.error(f"Task {task_id}: Unexpected error processing artifact {artifact_path_str}: {e}", exc_info=True)
            context.append(f"--- Unexpected Error Processing Artifact: {artifact_path_str} ---\nError: {e}\n--- End Unexpected Error Processing Artifact: {artifact_path_str} ---\n")

    return "\n".join(context)


def _construct_initial_prompt(prompt_system: PromptSystem, task_definition: dict, task_id: str, prompt_context: str, logger) -> str:
    """Constructs the initial prompt for the AI agent using the PromptSystem."""
    logger.info(f"Task {task_id}: Constructing initial prompt using PromptSystem.")

    try:
        # Use PromptSystem to get the formatted prompt for code generation
        # Assuming the prompt name is 'code_generation' in the 'agents' category
        output_artifacts = task_definition.get('output_artifacts', [])

        # Add explicit tool call instruction to the top of the instructions
        explicit_tool_instruction = (
            "IMPORTANT: When calling tools, do NOT wrap tool calls in print(), return, or any other function. "
            "Call the tool directly, e.g., write_file(...). Do not output any code outside of tool calls unless explicitly instructed. "
            "For example, DO NOT do: print(write_file(...)) or return write_file(...). Only use: write_file(...)."
        )
        orig_instructions = task_definition.get('instructions', ['No instructions provided.'])
        instructions = [explicit_tool_instruction] + orig_instructions

        initial_prompt = prompt_system.get_formatted_prompt(
            "agents",
            "code_generation",
            include_tools=True, # Include tool instructions
            task_description=task_definition.get('description', 'No description provided.'),
            instructions="\n".join(instructions),
            context=prompt_context if prompt_context else "No input artifacts provided or context gathered.",
            constraints="\n".join(task_definition.get('constraints', ['No constraints provided.'])),
            output_artifacts="\n".join(output_artifacts) if output_artifacts else "(None specified)",
            raw_task_json=task_definition.get('raw_text', json.dumps(task_definition, indent=2)) # Use raw_text if available, otherwise dump the dict
        )

        if logger:
            logger.debug(f"Task {task_id}: Constructed initial prompt (length: {len(initial_prompt)} chars)")
        log_event(
            log_message=LogMessage(
                LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "code_gen_initial_prompt",
                f"Initial prompt for task {task_id} (length: {len(initial_prompt)} chars)", subtask_id=task_id
            )
        )
        return initial_prompt

    except PromptNotFoundError as e:
        error_message = f"Prompt not found for code generation task {task_id}: {e}"
        logger.error(error_message)
        log_event(
            log_message=LogMessage(
                LogLevel.ERROR,
                ComponentType.EXECUTION_ENGINE,
                "code_gen_prompt_not_found",
                error_message,
                subtask_id=task_id,
                details={"error": str(e)},
            )
        )
        raise TaskExecutionError(error_message) from e
    except Exception as e:
        error_message = f"An unexpected error occurred while constructing prompt for code generation task {task_id}: {e}"
        logger.exception(error_message)
        log_event(
            log_message=LogMessage(
                LogLevel.CRITICAL,
                ComponentType.EXECUTION_ENGINE,
                "code_gen_prompt_construction_error",
                error_message,
                subtask_id=task_id,
                details={"error": str(e), "traceback": traceback.format_exc()},
            )
        )
        raise TaskExecutionError(error_message) from e

def _execute_validation(engine, task_definition, task_id, logger) -> tuple[bool, dict]:
    """Executes validation criteria, typically shell commands."""
    validation_criteria = task_definition.get('validation_criteria')
    validation_details = {"commands_executed": [], "overall_status": "skipped"}
    overall_passed = True

    # Basic validation: check that files listed in 'expected_output_files' or 'output_artifacts' exist
    expected_files = task_definition.get('expected_output_files')
    if expected_files is None:
        expected_files = task_definition.get('output_artifacts', [])
    missing_files = []
    checked_files = []
    # If no validation_criteria and no expected_files, skip validation
    if not task_definition.get('validation_criteria') and not expected_files:
        validation_details["overall_status"] = "skipped"
        validation_details["commands_executed"] = []
        return True, validation_details

    if isinstance(expected_files, list) and all(isinstance(f, str) for f in expected_files) and expected_files:
        try:
            from ai_whisperer.path_management import PathManager
            path_manager = PathManager.get_instance()
        except Exception as e:
            path_manager = None
            if logger:
                logger.warning(f"Task {task_id}: Could not import or initialize PathManager: {e}")
        for file_path in expected_files:
            resolved_path = file_path
            input_path_obj = None
            output_dir_obj = None
            if path_manager is not None:
                try:
                    input_path_obj = Path(file_path)
                    output_dir_obj = Path(path_manager.output_path)
                    # If absolute, use as-is
                    if input_path_obj.is_absolute():
                        resolved_path = str(input_path_obj.resolve())
                    else:
                        # If the first part of the input path matches the output dir name, strip it
                        input_parts = input_path_obj.parts
                        output_dir_name = output_dir_obj.name
                        if input_parts and input_parts[0] == output_dir_name:
                            input_path_obj = Path(*input_parts[1:])
                        candidate = (output_dir_obj / input_path_obj).resolve()
                        resolved_path = str(candidate)
                except Exception as e:
                    if logger:
                        logger.warning(f"Task {task_id}: Failed to normalize/resolve path '{file_path}': {e}")
            checked_files.append(file_path)
            # Only create Path object once for resolved_path
            resolved_path_obj = Path(resolved_path)
            abs_resolved_path = str(resolved_path_obj.resolve())
            if logger:
                logger.info(f"Task {task_id}: Checking file existence: original='{file_path}', resolved='{resolved_path}', abs='{abs_resolved_path}'")
                logger.info(f"Task {task_id}: Current working directory: '{os.getcwd()}'")
            # Only append to missing_files if the file is actually missing
            if not resolved_path_obj.is_file():
                if logger:
                    logger.warning(f"Task {task_id}: File does not exist: resolved='{resolved_path}' (from '{file_path}'), abs='{abs_resolved_path}'")
                missing_files.append(file_path)
        # Only include missing_files that are actually missing
        validation_details["checked_files"] = checked_files
        validation_details["missing_files"] = missing_files
        if missing_files:
            validation_details["overall_status"] = "failed"
            overall_passed = False
            if logger:
                logger.warning(f"Task {task_id}: Validation failed. Missing files: {missing_files}")
        else:
            validation_details["overall_status"] = "passed"
            overall_passed = True
            if logger:
                logger.info(f"Task {task_id}: Validation passed. All expected files exist.")
    else:
        if logger:
            logger.warning(f"Task {task_id}: No 'expected_output_files' or 'output_artifacts' found or format is incorrect.")
        validation_details["overall_status"] = "skipped"
        overall_passed = True

    return overall_passed, validation_details
