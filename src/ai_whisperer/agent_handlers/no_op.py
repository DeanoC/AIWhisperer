from src.ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType

def handle_no_op(engine, task_definition, task_id):
    """
    Handle a no-op (no operation) task.
    Implementation moved from ExecutionEngine._handle_no_op.
    """
    self = engine
    logger = self.config.get('logger', None)
    if logger:
        logger.info(f"Executing no-op task {task_id}")
    self.monitor.add_log_message(
        LogMessage(
            LogLevel.INFO,
            ComponentType.EXECUTION_ENGINE,
            "executing_no_op_task",
            f"Executing no-op task {task_id}",
            subtask_id=task_id,
        )
    )
    return f"No-op task {task_id} completed successfully."
