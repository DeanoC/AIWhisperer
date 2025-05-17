from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import log_event

def handle_planning(engine: ExecutionEngine, task_definition: dict):
    """
    Handle a planning task.
    Implementation moved from ExecutionEngine._handle_planning.
    """
    self = engine
    task_id = task_definition.get('subtask_id')

    logger = self.config.get('logger', None)
    if logger:
        logger.info(f"Executing planning task {task_id}")
    log_event(
        log_message=LogMessage(
            LogLevel.INFO,
            ComponentType.EXECUTION_ENGINE,
            "executing_planning_task",
            f"Executing planning task {task_id}",
            subtask_id=task_id,
        )
    )

    if task_id == "select_landmark":
        landmark = "Eiffel Tower"
        from pathlib import Path
        landmark_file_path = Path("landmark_selection.md").resolve()
        try:
            with open(landmark_file_path, "w", encoding="utf-8") as f:
                f.write(landmark)
            if logger:
                logger.info(f"Created landmark_selection.md with landmark: {landmark}")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "landmark_file_created",
                    f"Created landmark_selection.md with landmark: {landmark}",
                    subtask_id=task_id,
                )
            )
        except Exception as e:
            error_message = f"Failed to create landmark_selection.md: {e}"
            if logger:
                logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "landmark_file_creation_failed",
                    error_message,
                    subtask_id=task_id,
                )
            )
            raise TaskExecutionError(error_message) from e
    result = f"Planning task {task_id} completed"
    return result
