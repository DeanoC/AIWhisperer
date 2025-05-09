import uuid
import time # Import time for duration calculation

from .logging import LogMessage, LogLevel, ComponentType, get_logger # Import logging components
from .monitoring import TerminalMonitor # Import TerminalMonitor
from .state_management import StateManager # Import StateManager

logger = get_logger(__name__) # Get logger for execution engine

class TaskExecutionError(Exception):
    """Custom exception for task execution errors."""
    pass

class ExecutionEngine:
    """
    Executes tasks defined in a plan, managing state and handling dependencies.
    Integrates logging and monitoring for visibility into the execution process.
    """
    def __init__(self, state_manager: StateManager, monitor: TerminalMonitor):
        """
        Initializes the ExecutionEngine.

        Args:
            state_manager: An object responsible for managing the state of tasks.
                           It is expected to have methods like set_task_state,
                           get_task_status, store_task_result, and get_task_result.
            monitor: An object responsible for displaying execution progress and logs.
                     It is expected to have methods like add_log_message, set_active_step,
                     and update_display.
        """
        if state_manager is None:
            raise ValueError("State manager cannot be None.")
        if monitor is None:
             raise ValueError("Monitor cannot be None.")

        self.state_manager = state_manager
        self.monitor = monitor
        self.task_queue = []
        # In a real scenario, a TaskExecutor component would handle individual task logic.
        # This would be responsible for interacting with different agent types.
        # self.task_executor = TaskExecutor(state_manager)

    def _execute_single_task(self, task_definition):
        """
        Placeholder for executing a single task.
        In a real implementation, this would involve dispatching to a task executor
        based on task_definition['agent_spec']['type'] and handling interactions.

        Args:
            task_definition (dict): The definition of the task to execute.

        Returns:
            str: A simulated result of the task execution.

        Raises:
            TaskExecutionError: If the task is designed to fail for testing.
        """
        task_id = task_definition.get('step_id', 'unknown_task')

        # Simulate AI service interaction
        logger.info(f"Simulating AI service call for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.AI_SERVICE, "api_call_simulated", f"Simulating AI service call for task {task_id}", step_id=task_id))
        # In a real scenario, this would be an actual API call
        time.sleep(0.1) # Simulate API latency
        logger.info(f"Simulated AI service call completed for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.AI_SERVICE, "api_call_simulated_complete", f"Simulated AI service call completed for task {task_id}", step_id=task_id))


        # Simulate file operation
        logger.info(f"Simulating file operation for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.FILE_OPERATIONS, "file_op_simulated", f"Simulating file operation for task {task_id}", step_id=task_id))
        # In a real scenario, this would be a file read/write
        time.sleep(0.05) # Simulate file operation latency
        logger.info(f"Simulated file operation completed for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.FILE_OPERATIONS, "file_op_simulated_complete", f"Simulated file operation completed for task {task_id}", step_id=task_id))


        # Simulate terminal command execution
        logger.info(f"Simulating terminal command for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.TERMINAL_INTERACTION, "terminal_cmd_simulated", f"Simulating terminal command for task {task_id}", step_id=task_id))
        # In a real scenario, this would be a terminal command execution
        time.sleep(0.2) # Simulate terminal command latency
        logger.info(f"Simulated terminal command completed for task {task_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.TERMINAL_INTERACTION, "terminal_cmd_simulated_complete", f"Simulated terminal command completed for task {task_id}", step_id=task_id))


        # Simulate task execution based on instructions or type for more dynamic tests
        # For now, using a simple failure condition as in the test placeholder
        if task_id == "task_that_fails":
            logger.error(f"Task {task_id} failed intentionally.")
            self.monitor.add_log_message(LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "task_failed_intentional", f"Task {task_id} failed intentionally.", step_id=task_id))
            raise TaskExecutionError(f"Task {task_id} failed intentionally.")

        # Simulate successful execution and result
        # A real task executor would produce a more meaningful result.
        result = f"Result of {task_id}"
        logger.info(f"Task {task_id} executed successfully.")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_executed_success", f"Task {task_id} executed successfully.", step_id=task_id))
        return result

    def execute_plan(self, plan_data):
        """
        Executes the given plan sequentially.

        Args:
            plan_data (dict): The plan data, typically from a PlanParser,
                               containing a list of task definitions.
        """
        if plan_data is None:
            logger.error("Attempted to execute a None plan.")
            self.monitor.add_log_message(LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "execute_none_plan", "Attempted to execute a None plan."))
            raise ValueError("Plan data cannot be None.")

        plan_id = plan_data.get("task_id", "unknown_plan")
        logger.info(f"Starting execution of plan: {plan_id}")
        self.monitor.set_plan_name(plan_id)
        self.monitor.set_runner_status_info(f"Executing plan: {plan_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_started", f"Starting execution of plan: {plan_id}"))


        if not isinstance(plan_data.get("plan"), list):
            # Handle empty or invalid plan (e.g., log a warning or error)
            logger.warning(f"Invalid plan data provided for plan {plan_id}. 'plan' key is missing or not a list.")
            self.monitor.add_log_message(LogMessage(LogLevel.WARNING, ComponentType.RUNNER, "invalid_plan_structure", f"Invalid plan data provided for plan {plan_id}. 'plan' key is missing or not a list."))
            self.monitor.set_runner_status_info(f"Plan {plan_id} finished with warning: Invalid plan structure.")
            self.monitor.add_log_message(LogMessage(LogLevel.WARNING, ComponentType.RUNNER, "plan_execution_finished", f"Plan {plan_id} finished with warning: Invalid plan structure."))
            # For now, just return as per test expectations for empty/None plans.
            return

        self.task_queue = list(plan_data.get("plan", []))

        for task_def in self.task_queue:
            task_id = task_def.get('step_id')
            if not task_id:
                # Handle missing step_id (e.g., log error, skip task)
                logger.error(f"Task definition missing 'step_id': {task_def}. Skipping task.")
                self.monitor.add_log_message(LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "missing_step_id", f"Task definition missing 'step_id': {task_def}. Skipping task."))
                continue

            self.state_manager.set_task_state(task_id, "pending")
            self.monitor.set_active_step(task_id)
            self.monitor.set_runner_status_info(f"Pending: {task_id}")
            self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_pending", f"Task {task_id} is pending.", step_id=task_id))


            # Check dependencies
            dependencies = task_def.get("depends_on", [])
            can_execute = True
            if dependencies:
                logger.info(f"Checking dependencies for task {task_id}: {dependencies}")
                self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "checking_dependencies", f"Checking dependencies for task {task_id}.", step_id=task_id, details={"dependencies": dependencies}))
                for dep_id in dependencies:
                    dep_status = self.state_manager.get_task_status(dep_id)
                    # A task can only run if all its dependencies are 'completed'.
                    if dep_status != "completed":
                        logger.warning(f"Dependency {dep_id} not met for task {task_id}. Status: {dep_status}. Skipping task.")
                        self.state_manager.set_task_state(
                            task_id,
                            "skipped",
                            {"reason": f"Dependency {dep_id} not met. Status: {dep_status}"}
                        )
                        self.monitor.add_log_message(LogMessage(LogLevel.WARNING, ComponentType.EXECUTION_ENGINE, "task_skipped_dependency", f"Task {task_id} skipped due to unmet dependency {dep_id}.", step_id=task_id, details={"dependency_id": dep_id, "dependency_status": dep_status}))
                        can_execute = False
                        break

            if not can_execute:
                continue

            self.state_manager.set_task_state(task_id, "in-progress")
            self.monitor.set_runner_status_info(f"In Progress: {task_id}")
            self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_in_progress", f"Task {task_id} is in progress.", step_id=task_id))

            start_time = time.time() # Start timing the task execution
            try:
                result = self._execute_single_task(task_def)
                end_time = time.time() # End timing
                duration_ms = (end_time - start_time) * 1000 # Duration in milliseconds

                self.state_manager.set_task_state(task_id, "completed")
                self.state_manager.save_state()
                self.state_manager.store_task_result(task_id, result)
                self.monitor.set_runner_status_info(f"Completed: {task_id}")
                self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.EXECUTION_ENGINE, "task_completed", f"Task {task_id} completed successfully.", step_id=task_id, duration_ms=duration_ms))

            except TaskExecutionError as e:
                end_time = time.time() # End timing
                duration_ms = (end_time - start_time) * 1000 # Duration in milliseconds
                error_message = str(e)
                logger.error(f"Task {task_id} failed: {error_message}")
                self.state_manager.set_task_state(task_id, "failed", {"error": error_message})
                self.monitor.set_runner_status_info(f"Failed: {task_id}")
                self.monitor.add_log_message(LogMessage(LogLevel.ERROR, ComponentType.EXECUTION_ENGINE, "task_failed", f"Task {task_id} failed: {error_message}", step_id=task_id, duration_ms=duration_ms, details={"error": error_message}))
                # Design document implies continuing with other tasks if one fails.
            except Exception as e:
                end_time = time.time() # End timing
                duration_ms = (end_time - start_time) * 1000 # Duration in milliseconds
                # Catch any other unexpected error during task execution
                error_message = f"Unexpected error during execution of task {task_id}: {str(e)}"
                logger.exception(f"Unexpected error during execution of task {task_id}") # Log with traceback
                self.state_manager.set_task_state(task_id, "failed", {"error": error_message})
                self.monitor.set_runner_status_info(f"Failed: {task_id}")
                self.monitor.add_log_message(LogMessage(LogLevel.CRITICAL, ComponentType.EXECUTION_ENGINE, "task_failed_unexpected", error_message, step_id=task_id, duration_ms=duration_ms, details={"error": error_message, "traceback": traceback.format_exc()}))


        # After each task, clear the active step in the monitor
        self.monitor.set_active_step(None)

        logger.info(f"Finished execution of plan: {plan_id}")
        self.monitor.set_runner_status_info(f"Plan execution finished: {plan_id}")
        self.monitor.add_log_message(LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_finished", f"Finished execution of plan: {plan_id}"))


    def get_task_status(self, task_id):
        """
        Returns the status of a specific task.

        Args:
            task_id (str): The ID of the task.

        Returns:
            str or None: The status of the task, or None if not found.
        """
        return self.state_manager.get_task_status(task_id)

    def get_task_result(self, task_id):
        """
        Returns the intermediate result of a specific task.

        Args:
            task_id (str): The ID of the task.

        Returns:
            any or None: The result of the task, or None if not found or not completed.
        """
        return self.state_manager.get_task_result(task_id)