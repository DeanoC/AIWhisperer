import uuid

class TaskExecutionError(Exception):
    """Custom exception for task execution errors."""
    pass

class ExecutionEngine:
    """
    Executes tasks defined in a plan, managing state and handling dependencies.
    """
    def __init__(self, state_manager):
        """
        Initializes the ExecutionEngine.

        Args:
            state_manager: An object responsible for managing the state of tasks.
                           It is expected to have methods like set_task_state,
                           get_task_status, store_task_result, and get_task_result.
        """
        if state_manager is None:
            raise ValueError("State manager cannot be None.")
        self.state_manager = state_manager
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
        
        # Simulate task execution based on instructions or type for more dynamic tests
        # For now, using a simple failure condition as in the test placeholder
        if task_id == "task_that_fails":
            raise TaskExecutionError(f"Task {task_id} failed intentionally.")
        
        # Simulate successful execution and result
        # A real task executor would produce a more meaningful result.
        return f"Result of {task_id}"

    def execute_plan(self, plan_data):
        """
        Executes the given plan sequentially.

        Args:
            plan_data (dict): The plan data, typically from a PlanParser,
                              containing a list of task definitions.
        """
        if not plan_data or not isinstance(plan_data.get("plan"), list):
            # Handle empty or invalid plan (e.g., log a warning or error)
            # For now, just return as per test expectations for empty/None plans.
            return

        self.task_queue = list(plan_data.get("plan", []))

        for task_def in self.task_queue:
            task_id = task_def.get('step_id')
            if not task_id:
                # Handle missing step_id (e.g., log error, skip task)
                # For now, assume valid task_def as per plan_parser validation
                print(f"Warning: Task definition missing 'step_id': {task_def}")
                continue

            self.state_manager.set_task_state(task_id, "pending")

            # Check dependencies
            dependencies = task_def.get("depends_on", [])
            can_execute = True
            if dependencies:
                for dep_id in dependencies:
                    dep_status = self.state_manager.get_task_status(dep_id)
                    # A task can only run if all its dependencies are 'completed'.
                    if dep_status != "completed":
                        self.state_manager.set_task_state(
                            task_id, 
                            "skipped", 
                            {"reason": f"Dependency {dep_id} not met. Status: {dep_status}"}
                        )
                        can_execute = False
                        break 
            
            if not can_execute:
                continue

            self.state_manager.set_task_state(task_id, "in-progress")
            try:
                result = self._execute_single_task(task_def)
                self.state_manager.set_task_state(task_id, "completed")
                self.state_manager.save_state()
                self.state_manager.store_task_result(task_id, result)
            except TaskExecutionError as e:
                self.state_manager.set_task_state(task_id, "failed", {"error": str(e)})
                # Design document implies continuing with other tasks if one fails.
            except Exception as e:
                # Catch any other unexpected error during task execution
                error_message = f"Unexpected error during execution of task {task_id}: {str(e)}"
                self.state_manager.set_task_state(task_id, "failed", {"error": error_message})
                # Optionally, log this unexpected error more verbosely.
                print(f"ERROR: {error_message}")


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