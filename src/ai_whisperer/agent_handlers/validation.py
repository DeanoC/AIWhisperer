import os
import json
import traceback
from pathlib import Path
from ai_whisperer.agent_handlers.code_generation import _execute_validation
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.tools.tool_registry import ToolRegistry
from src.ai_whisperer.exceptions import TaskExecutionError
from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType
def handle_validation(engine: ExecutionEngine, task_definition: dict) -> tuple[bool, dict]:
    """Executes validation criteria, typically shell commands."""
    task_id = task_definition.get('subtask_id')
    logger = engine.config.get('logger', None) # Get logger from engine config
    return _execute_validation(engine, task_definition, task_id, logger)
