from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import log_event

def handle_no_op(engine: ExecutionEngine, task_definition: dict):
    """
    Handle a no-op (no operation) task.
    Implementation moved from ExecutionEngine._handle_no_op.
    """
    self = engine
    task_id = task_definition.get('subtask_id')
    logger = self.config.get('logger', None)
    if logger:
        logger.info(f"Executing no-op task {task_id}")
    log_event(
        log_message=LogMessage(
            LogLevel.INFO,
            ComponentType.EXECUTION_ENGINE,
            "executing_no_op_task",
            f"Executing no-op task {task_id}",
            subtask_id=task_id,
        )
    )
    return f"No-op task {task_id} completed successfully."
