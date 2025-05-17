import os
import json
import traceback
from pathlib import Path
from ai_whisperer.agent_handlers.code_generation import _execute_validation
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, log_event
def handle_validation(engine: ExecutionEngine, task_definition: dict) -> tuple[bool, dict]:
    """Executes validation criteria, typically shell commands."""
    task_id = task_definition.get('subtask_id')
    logger = engine.config.get('logger', None) # Get logger from engine config
    result = _execute_validation(engine, task_definition, task_id, logger)
    # Support both (bool, dict) and dict return types for test compatibility
    if isinstance(result, tuple) and len(result) == 2:
        overall_passed, validation_details = result
        if overall_passed:
            return overall_passed, validation_details
        else:
            error_message = f"Code generation task {task_id} failed validation."
            if logger:
                logger.error(f"{error_message} Details: {validation_details}")
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_validation_failed",
                    error_message, subtask_id=task_id, details=validation_details
                )
            )
            raise TaskExecutionError(error_message, details=validation_details)
    elif isinstance(result, dict):
        # If a dict is returned directly, treat as failure details
        error_message = f"Code generation task {task_id} failed validation."
        if logger:
            logger.error(f"{error_message} Details: {result}")
        log_event(
            log_message=LogMessage(
                LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "code_gen_validation_failed",
                error_message, subtask_id=task_id, details=result
            )
        )
        raise TaskExecutionError(error_message, details=result)
    else:
        # Unexpected return type
        error_message = f"Validation handler returned unexpected result type: {type(result)}"
        if logger:
            logger.error(error_message)
        raise TaskExecutionError(error_message)
