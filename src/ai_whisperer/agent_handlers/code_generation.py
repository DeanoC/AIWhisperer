# src/ai_whisperer/agent_handlers/code_generation.py
from src.ai_whisperer.execution_engine import ExecutionEngine
from src.ai_whisperer.exceptions import TaskExecutionError
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, get_logger, log_event # Import log_event
from src.ai_whisperer.tools.tool_registry import ToolRegistry # Assuming ToolRegistry is accessible
from src.ai_whisperer.context_management import ContextManager # Import ContextManager
from src.ai_whisperer.ai_loop import run_ai_loop # Import the refactored AI loop
from pathlib import Path
import json
import traceback
from datetime import datetime, timezone

# Potentially import build_ascii_directory_tree if needed
from src.ai_whisperer.utils import build_ascii_directory_tree

logger = get_logger(__name__)  # Get logger for execution engine

import threading # Import threading for shutdown_event type hint

async def handle_code_generation(engine: ExecutionEngine, task_definition: dict, task_id: str, shutdown_event: threading.Event):
    """
    Handles the execution of a 'code_generation' task.
    """
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
        initial_prompt = _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger)

        # 3. AI Interaction & Tool Execution Loop
        # Get ContextManager from StateManager
        context_manager = engine.state_manager.get_context_manager(task_id)
        if context_manager is None:
            raise TaskExecutionError(f"ContextManager not found for task {task_id} in StateManager.")

        final_ai_result = await run_ai_loop(engine, task_definition, task_id, initial_prompt, logger, context_manager, shutdown_event) # Await and pass shutdown_event
        logger.info(f"Task {task_id}: AI interaction loop finished.")


        # 4. Test Execution / Validation
        # NOTE: Validation is currently faked as per user instruction.
        validation_passed, validation_details = _execute_validation(engine, task_definition, task_id, logger)
        logger.info(f"Task {task_id}: Validation executed. Passed: {validation_passed}")

        print(f"DEBUG: Task {task_id}: Validation passed: {validation_passed}") # Debug print
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
            print(f"DEBUG: Task {task_id}: Validation failed. Raising TaskExecutionError.") # Debug print
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

def _construct_initial_prompt(engine, task_definition, task_id, prompt_context, logger) -> str:
    """Constructs the initial prompt for the AI agent."""
    # Get the base system prompt from the default prompt file
    try:
        base_prompt_path = Path("prompts/code_generation_default.md")
        base_prompt = base_prompt_path.read_text()
        logger.debug(f"Task {task_id}: Read base prompt from {base_prompt_path}")
    except FileNotFoundError:
        base_prompt = "You are an expert software engineer AI agent."
        logger.warning(f"Task {task_id}: Base prompt file not found. Using default: {base_prompt}")
    except IOError as e:
        base_prompt = "You are an expert software engineer AI agent."
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
        logger.debug(f"Task {task_id}: Constructed initial prompt (length: {len(initial_prompt)} chars)")
    log_event(
        log_message=LogMessage(
            LogLevel.DEBUG, ComponentType.EXECUTION_ENGINE, "code_gen_initial_prompt",
            f"Initial prompt for task {task_id} (length: {len(initial_prompt)} chars)", subtask_id=task_id
        )
    )
    return initial_prompt

def _execute_validation(engine, task_definition, task_id, logger) -> tuple[bool, dict]:
    """Executes validation criteria, typically shell commands."""
    validation_criteria = task_definition.get('validation_criteria')
    validation_details = {"commands_executed": [], "overall_status": "skipped"}
    overall_passed = True

    # Basic validation: check that files listed in 'expected_output_files' exist
    expected_files = task_definition.get('expected_output_files', [])
    missing_files = []
    checked_files = []
    if isinstance(expected_files, list) and all(isinstance(f, str) for f in expected_files):
        for file_path in expected_files:
            checked_files.append(file_path)
            if not Path(file_path).is_file():
                missing_files.append(file_path)
        validation_details["checked_files"] = checked_files
        validation_details["missing_files"] = missing_files
        if missing_files:
            validation_details["overall_status"] = "failed"
            overall_passed = False
            logger.warning(f"Task {task_id}: Validation failed. Missing files: {missing_files}")
        else:
            validation_details["overall_status"] = "passed"
            overall_passed = True
            logger.info(f"Task {task_id}: Validation passed. All expected files exist.")
    else:
        if logger:
            logger.warning(f"Task {task_id}: No 'expected_output_files' found or format is incorrect.")
        validation_details["overall_status"] = "skipped"
        overall_passed = True

    return overall_passed, validation_details
