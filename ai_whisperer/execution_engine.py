import time  # Import time for duration calculation
from pathlib import Path  # Import Path
import json
import threading  # Import threading for Event
import asyncio # Import asyncio for async operations

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService
from ai_whisperer.exceptions import TaskExecutionError, FileRestrictionError, PromptNotFoundError
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.path_management import PathManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.logging_custom import LogMessage, LogLevel, ComponentType, get_logger, log_event  # Import logging components and log_event
from ai_whisperer.state_management import StateManager
from ai_whisperer.plan_parser import ParserPlan
from ai_whisperer.prompt_system import PromptSystem
from ai_whisperer.exceptions import (
    ConfigError,
    OpenRouterAIServiceError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterConnectionError,
)  # Import AI interaction components
import traceback  # Import traceback for detailed error logging

logger = get_logger(__name__)  # Get logger for execution engine
logger.propagate = False

class ExecutionEngine:
    """
    Executes tasks defined in a plan, managing state and handling dependencies.
    Integrates logging and a general delegation system for visibility and control of the execution process.
    """

    def __init__(self, state_manager: StateManager, config: dict, prompt_system: PromptSystem, delegate_manager: DelegateManager, shutdown_event: threading.Event = None):
        """
        Initializes the ExecutionEngine.

        Args:
            state_manager: An object responsible for managing the state of tasks.
                Expected to have methods like set_task_state, get_task_status, store_task_result, and get_task_result.
            config: The global configuration dictionary.
            prompt_system: An instance of the PromptSystem.
            shutdown_event: An event that signals when execution should stop.
        """
        if state_manager is None:
            raise ValueError("State manager cannot be None.")
        if config is None:
            raise ValueError("Configuration cannot be None.")
        if prompt_system is None:
             raise ValueError("PromptSystem cannot be None.")

        self.state_manager = state_manager
        self.config = config  # Store the global configuration
        self.prompt_system = prompt_system # Store the PromptSystem instance
        self.shutdown_event = shutdown_event if shutdown_event is not None else threading.Event() # Use provided event or create a new one
        self.task_queue = []
        self.path_manager = PathManager.get_instance()
        self.delegate_manager = delegate_manager # Store the injected DelegateManager
        self._pause_event = threading.Event() # Add pause event
        self._paused = False # Add paused state flag
        self._pause_event.set() # Start in unpaused state

        # Initialize AI Service Interaction once
        try:
            # Map relevant config values to AIConfig arguments
            # Ensure we are getting values from the 'openrouter' section of the config
            openrouter_config_section = self.config.get('openrouter', {})
            if not openrouter_config_section:
                 logger.warning("OpenRouter configuration section is missing in config. AI interaction tasks may fail.")
                 log_event(
                     log_message=LogMessage(
                         LogLevel.WARNING,
                         ComponentType.EXECUTION_ENGINE,
                         "openrouter_config_section_missing",
                         "OpenRouter configuration section is missing in config. AI interaction tasks may fail.",
                     )
                 )
                 self.aiservice = None
                 self.ai_config = None # Also set ai_config to None
            else:
                self.ai_config = AIConfig(
                    api_key=openrouter_config_section.get('api_key', ''),
                    model_id=openrouter_config_section.get('model', ''),
                    temperature=openrouter_config_section.get('params', {}).get('temperature', 0.7),
                    max_tokens=openrouter_config_section.get('params', {}).get('max_tokens', None),
                    site_url=openrouter_config_section.get('site_url', 'http://AIWhisperer:8000'),
                    app_name=openrouter_config_section.get('app_name', 'AIWhisperer'),
                )
                if not self.ai_config.api_key or not self.ai_config.model_id:
                    logger.warning("OpenRouter API key or model ID is missing in config. AI interaction tasks may fail.")
                    log_event(
                        log_message=LogMessage(
                            LogLevel.WARNING,
                            ComponentType.EXECUTION_ENGINE,
                            "openrouter_api_key_or_model_missing",
                            "OpenRouter API key or model ID is missing in config. AI interaction tasks may fail.",
                        )
                    )
                    self.aiservice = None # Set to None if essential config is missing
                else:
                    self.aiservice = OpenRouterAIService(self.ai_config, shutdown_event=self.shutdown_event)

        except ConfigError as e:
            error_message = f"Failed to initialize OpenRouter API due to configuration error: {e}"
            logger.error(error_message, exc_info=True)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_service_init_config_error",
                    error_message,
                    details={"error": str(e)},
                )
            )
            self.aiservice = None  # Set to None on config error
            self.ai_config = None
            # Decide whether to raise an exception here or allow execution to continue
            # For now, we'll allow execution to continue but AI tasks will fail
        except Exception as e:
            error_message = f"An unexpected error occurred during OpenRouter API initialization: {e}"
            logger.exception(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.CRITICAL,
                    ComponentType.EXECUTION_ENGINE,
                    "ai_service_init_unexpected_error",
                    error_message,
                    details={"error": str(e), "traceback": traceback.format_exc()},
                )
            )
            self.aiservice = None  # Set to None on unexpected error
            self.ai_config = None
            # Decide whether to raise an exception here or allow execution to continue
            # For now, we'll allow execution to continue but AI tasks will fail


        # Import agent handler functions
        from .agent_handlers.ai_interaction import handle_ai_interaction
        from .agent_handlers.planning import handle_planning
        from .agent_handlers.validation import handle_validation
        from .agent_handlers.no_op import handle_no_op
        from .agent_handlers.code_generation import handle_code_generation

        # Initialize the agent type handler table
        self.agent_type_handlers = {
            "ai_interaction": lambda engine_instance, task_def_arg: handle_ai_interaction(engine_instance, task_def_arg, engine_instance.prompt_system), # Use external handler
            "planning": lambda engine_instance, task_def_arg: handle_planning(engine_instance, task_def_arg),
            "validation": lambda task_definition: handle_validation(self, task_definition), # Validation handler is not async
            "no_op": lambda task_definition: handle_no_op(self, task_definition), # No-op handler is async
            "code_generation": lambda engine_instance, task_def_arg: handle_code_generation(engine_instance, task_def_arg, engine_instance.prompt_system),
            # Add other agent types and their handlers here, ensuring they accept only task_definition
        }

    def pause_engine(self):
        """Pauses the execution engine."""
        if not self._paused:
            logger.info("Execution engine pausing...")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "engine_pausing",
                    "Execution engine pausing.",
                )
            )
            self._paused = True
            self._pause_event.clear() # Clear the event to block the loop

    def resume_engine(self):
        """Resumes the execution engine."""
        if self._paused:
            logger.info("Execution engine resuming...")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "engine_resuming",
                    "Execution engine resuming.",
                )
            )
            self._paused = False
            self._pause_event.set() # Set the event to unblock the loop

    async def _collect_ai_history(self, task_id, visited_tasks=None):
        """
        Recursively collects conversation history from preceding AI interaction tasks.

        Args:
            task_id (str): The ID of the current task.
            visited_tasks (set): A set of task IDs already visited to prevent cycles.

        Returns:
            list: A list of message dictionaries representing the conversation history.
        """
        if visited_tasks is None:
            visited_tasks = set()

        if task_id in visited_tasks:
            return []  # Avoid infinite recursion

        visited_tasks.add(task_id)

        history = []
        task_def = next((t for t in self.task_queue if t.get("subtask_id") == task_id), None)

        if not task_def:
            return []

        # Recursively collect history from dependencies first
        dependencies = task_def.get("depends_on", [])
        for dep_id in dependencies:
            # Await the recursive call if _collect_ai_history becomes async
            history.extend(await self._collect_ai_history(dep_id, visited_tasks))

        # Add the current task's history if it's an AI interaction task
        if task_def.get("type") == "ai_interaction":
            # Get conversation history from StateManager's ContextManager
            conversation_history = self.state_manager.get_conversation_history(task_id)
            history.extend(conversation_history)
            if conversation_history:
                 logger.debug(f"Added conversation history for task {task_id} (length: {len(conversation_history)})")

        return history

    async def _execute_planning_task(self, task_id, task_def, plan_parser: ParserPlan):
        """
        Executes a planning task by loading and executing the subtask from a file.

        Args:
            task_id (str): The ID of the task.
            task_def (dict): The task definition.
            plan_parser (ParserPlan): The parser containing loaded subtask content.

        Returns:
            str: The result of the subtask execution.

        Raises:
            TaskExecutionError: If the task execution fails.
        """
        file_path = task_def.get("file_path")
        if not file_path:
            error_message = f"Planning task {task_id} is missing 'file_path'."
            logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "planning_task_missing_filepath",
                    error_message,
                    subtask_id=task_id,
                )
            )
            raise TaskExecutionError(error_message)

        try:
            # Get the loaded subtask content from the PlanParser
            subtask_data = plan_parser.get_subtask_content(task_id)

            if subtask_data is None:
                 # This case should ideally not happen if PlanParser loaded correctly,
                 # but handle defensively.
                 error_message = f"Detailed task definition not found in PlanParser for planning task {task_id} referenced by file_path: {file_path}"
                 logger.error(error_message)
                 log_event(
                     log_message=LogMessage(
                         LogLevel.ERROR,
                         ComponentType.EXECUTION_ENGINE,
                         "detailed_task_def_not_found_in_parser",
                         error_message,
                         subtask_id=task_id,
                         details={"file_path": file_path},
                     )
                 )
                 raise TaskExecutionError(error_message)


            logger.info(f"Executing planning task {task_id} from subtask definition.")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "executing_subtask_definition",
                    f"Executing planning task {task_id} from subtask definition.",
                    subtask_id=task_id,
                    details={"subtask_id": task_id},
                )
            )

            # Execute the task defined in the subtask file
            if isinstance(subtask_data, dict):
                # Await the async call to _execute_single_task
                result = await self._execute_single_task(subtask_data, plan_parser)
                logger.info(f"Planning task {task_id} (from subtask) completed.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "planning_task_subtask_completed",
                        f"Planning task {task_id} (from subtask) completed.",
                        subtask_id=task_id,
                    )
                )
                return result
            else:
                error_message = (
                    f"Invalid subtask definition format for planning task {task_id}. Expected a dictionary, but PlanParser returned {type(subtask_data).__name__}."
                )
                logger.error(error_message)
                log_event(
                    log_message=LogMessage(
                        LogLevel.ERROR,
                        ComponentType.EXECUTION_ENGINE,
                        "invalid_subtask_definition_format",
                        error_message,
                        subtask_id=task_id,
                        details={"subtask_id": task_id, "returned_type": type(subtask_data).__name__},
                    )
                )
                raise TaskExecutionError(error_message)

        except TaskExecutionError:
             # Re-raise TaskExecutionError if it was raised by _execute_single_task
             raise
        except Exception as e:
            error_message = f"An unexpected error occurred during planning task {task_id} execution from subtask definition: {e}"
            logger.exception(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.CRITICAL,
                    ComponentType.EXECUTION_ENGINE,
                    "planning_task_subtask_unexpected_error",
                    error_message,
                    subtask_id=task_id,
                    details={
                        "subtask_id": task_id,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    },
                )
            )
            raise TaskExecutionError(error_message) from e


    async def _execute_single_task(self, task_definition, plan_parser: ParserPlan):
        """
        Executes a single task based on its agent type.

        Args:
            task_definition (dict): The definition of the task to execute.
            plan_parser (ParserPlan): The parser containing loaded plan/subtask content.

        Returns:
            any: The result of the task execution. Can be a string, dict, etc.

        Raises:
            TaskExecutionError: If the task execution fails.
        """
        task_id = task_definition.get("subtask_id", "unknown_task")
        agent_type = task_definition.get("type")

        logger.info(f"Executing task {task_id} with agent type: {agent_type}")
        log_event(
            log_message=LogMessage(
                LogLevel.INFO,
                ComponentType.EXECUTION_ENGINE,
                "task_execution_start",
                f"Executing task {task_id} with agent type: {agent_type}",
                subtask_id=task_id,
                details={"agent_type": agent_type},
            )
        )

        if agent_type is None:
            error_message = f"Task {task_id} is missing type."
            logger.info("Processing task: %s", task_definition)
            logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "task_missing_type",
                    error_message,
                    subtask_id=task_id,
                )
            )
            raise TaskExecutionError(error_message)

        # Use the agent type handler table to execute the task
        logger.debug(f"Task {task_id}: DelegateManager state before calling handler: {self.delegate_manager}") # Add debug log
        if agent_type in self.agent_type_handlers:
            # Call the handler function (which might return a coroutine) and await the result.
            # The lambda is defined to accept engine_instance and task_def_arg.
            handler = self.agent_type_handlers[agent_type]
            # Get the handler function for this agent type
            handler = self.agent_type_handlers[agent_type]
            
            # Check if the handler is async
            if asyncio.iscoroutinefunction(handler):
                # Call async handler with self and task_definition
                return await handler(self, task_definition, self.prompt_system)
            else:
                # Call sync handler with self and task_definition
                return handler(self, task_definition)
        else:
            # Handle unsupported agent types
            error_message = f"Unsupported agent type for task {task_id}: {agent_type}"
            logger.error(error_message)
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "unsupported_agent_type",
                    error_message,
                    subtask_id=task_id,
                    details={"agent_type": agent_type},
                )
            )
            raise TaskExecutionError(error_message)

    async def execute_plan(self, plan_parser: ParserPlan):
        """
        Executes the given plan sequentially.

        Args:
            plan_parser: An instance of ParserPlan containing the parsed plan data.
        """
        if plan_parser is None:
            logger.error("Attempted to execute a None plan parser.")
            log_event(
                log_message=LogMessage(
                    LogLevel.ERROR,
                    ComponentType.EXECUTION_ENGINE,
                    "execute_none_plan_parser",
                    "Attempted to execute a None plan parser.",
                )
            )
            raise ValueError("Plan parser cannot be None.")

        plan_data = plan_parser.get_parsed_plan()
        plan_id = plan_data.get("task_id", "unknown_plan")
        logger.info(f"Starting execution of plan: {plan_id}")
        log_event(
            log_message=LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_started", f"Starting execution of plan: {plan_id}")
        )
        # Await the async invoke_notification call
        await self.delegate_manager.invoke_notification(self, "engine_started", None)

        if not isinstance(plan_data.get("plan"), list):
            # Handle empty or invalid plan (e.g., log a warning or error)
            logger.warning(f"Invalid plan data provided for plan {plan_id}. 'plan' key is missing or not a list.")
            log_event(
                log_message=LogMessage(
                    LogLevel.WARNING,
                    ComponentType.EXECUTION_ENGINE,
                    "invalid_plan_structure",
                    f"Invalid plan data provided for plan {plan_id}. 'plan' key is missing or not a list.",
                    )
                )
            log_event(
                log_message=LogMessage(
                    LogLevel.WARNING,
                    ComponentType.RUNNER,
                    "plan_execution_finished",
                    f"Plan {plan_id} finished with warning: Invalid plan structure.",
                )
            )
            # For now, just return as per test expectations for empty/None plans.
            return

        self.task_queue = list(plan_data.get("plan", []))

        for task_def_overview in self.task_queue:
            # Check for pause request at the beginning of each task iteration (Await the async call)
            if self.delegate_manager and await self.delegate_manager.invoke_control(self, "engine_request_pause"):
                logger.info(f"Execution engine paused before task {task_def_overview.get('subtask_id', 'unknown_task')}")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "engine_paused",
                        f"Execution engine paused before task {task_def_overview.get('subtask_id', 'unknown_task')}.",
                        subtask_id=task_def_overview.get('subtask_id', 'unknown_task'),
                    )
                )
                # In a real implementation, this would involve waiting on an event
                # For now, we just log and continue, but the test should ideally
                # register a delegate that returns True and verify the log message.
                while self._paused and not self.shutdown_event.is_set():
                    # Use asyncio.sleep in an async context
                    await asyncio.sleep(0.1) # Wait with a timeout to allow checking shutdown_event
                if self.shutdown_event.is_set():
                    logger.info("Shutdown requested while paused. Stopping execution.")
                    log_event(
                        log_message=LogMessage(
                            LogLevel.INFO,
                            ComponentType.EXECUTION_ENGINE,
                            "engine_shutdown_while_paused",
                            "Shutdown requested while paused. Stopping execution.",
                        )
                    )
                    break # Exit the main loop for graceful shutdown

            # Check for stop request at the beginning of each task iteration (Await the async call)
            if self.delegate_manager and await self.delegate_manager.invoke_control(self, "engine_request_stop"):
               logger.info(f"Execution engine stop requested before task {task_def_overview.get('subtask_id', 'unknown_task')}. Initiating graceful shutdown.")
               log_event(
                   log_message=LogMessage(
                       LogLevel.INFO,
                       ComponentType.EXECUTION_ENGINE,
                       "engine_stop_requested",
                       f"Execution engine stop requested before task {task_def_overview.get('subtask_id', 'unknown_task')}. Initiating graceful shutdown.",
                       subtask_id=task_def_overview.get('subtask_id', 'unknown_task'),
                   )
               )
               self.shutdown_event.set() # Signal shutdown
               break # Exit the main loop for graceful shutdown

            task_id = task_def_overview.get("subtask_id")
            if not task_id:
                # Handle missing subtask_id (e.g., log error, skip task)
                logger.error(f"Task definition missing 'subtask_id': {task_def_overview}. Skipping task.")
                log_event(
                    log_message=LogMessage(
                        LogLevel.ERROR,
                        ComponentType.EXECUTION_ENGINE,
                        "missing_subtask_id",
                        f"Task definition missing 'subtask_id': {task_def_overview}. Skipping task.",
                    )
                )
                continue

            # Determine the effective task definition: either from file_path or the overview definition
            task_def_effective = task_def_overview
            file_path = task_def_overview.get("file_path")
            if file_path:
                # Get the loaded subtask content from the PlanParser
                task_def_detailed = plan_parser.get_subtask_content(task_id)

                if task_def_detailed:
                    logger.info(f"Using detailed task definition from file for task {task_id}.")
                    log_event(
                        log_message=LogMessage(
                            LogLevel.INFO,
                            ComponentType.EXECUTION_ENGINE,
                            "using_detailed_task_def",
                            f"Using detailed task definition for task {task_id} from file.",
                            subtask_id=task_id,
                            details={"file_path": file_path},
                        )
                    )
                    task_def_effective = task_def_detailed
                    # Ensure task_id is consistent between overview and detailed definition
                    if task_def_effective.get("subtask_id") != task_id:
                         logger.warning(f"Subtask ID mismatch for task {task_id}. Overview ID: {task_id}, Detailed ID: {task_def_effective.get('subtask_id')}. Using Overview ID.")
                         task_def_effective["subtask_id"] = task_id # Prioritize overview ID for state management
                else:
                    # This case should ideally not happen if PlanParser loaded correctly,
                    # but handle defensively.
                    error_message = f"Detailed task definition not found in PlanParser for task {task_id} referenced by file_path: {file_path}"
                    logger.error(error_message)
                    log_event(
                        log_message=LogMessage(
                            LogLevel.ERROR,
                            ComponentType.EXECUTION_ENGINE,
                            "detailed_task_def_not_found_in_parser",
                            error_message,
                            subtask_id=task_id,
                            details={"file_path": file_path},
                        )
                    )
                    self.state_manager.set_task_state(task_id, "failed", {"error": error_message})
                    continue # Skip to the next task if detailed definition is missing

            self.state_manager.set_task_state(task_id, "pending")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "task_pending",
                    f"Task {task_id} is pending.",
                    subtask_id=task_id,
                )
            )

            # Check dependencies
            dependencies = task_def_effective.get("depends_on", []) # Check dependencies in the effective task definition
            can_execute = True
            if dependencies:
                logger.info(f"Checking dependencies for task {task_id}: {dependencies}")
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "checking_dependencies",
                        f"Checking dependencies for task {task_id}.",
                        subtask_id=task_id,
                        details={"dependencies": dependencies},
                    )
                )
                for dep_id in dependencies:
                    dep_status = self.state_manager.get_task_status(dep_id)
                    # A task can only run if all its dependencies are 'completed'.
                    if dep_status != "completed":
                        logger.warning(
                            f"Dependency {dep_id} not met for task {task_id}. Status: {dep_status}. Skipping task."
                        )
                        self.state_manager.set_task_state(
                            task_id, "skipped", {"reason": f"Dependency {dep_id} not met. Status: {dep_status}"}
                        )
                        log_event(
                            log_message=LogMessage(
                                LogLevel.WARNING,
                                ComponentType.EXECUTION_ENGINE,
                                "task_skipped_dependency",
                                f"Task {task_id} skipped due to unmet dependency {dep_id}.",
                                subtask_id=task_id,
                                details={"dependency_id": dep_id, "dependency_status": dep_status},
                            )
                        )
                        can_execute = False
                        break

            if not can_execute:
                continue

            if self.config.get('logger'):
                self.config['logger'].debug(f"Executing task: {task_id}")

            self.state_manager.set_task_state(task_id, "in-progress")
            log_event(
                log_message=LogMessage(
                    LogLevel.INFO,
                    ComponentType.EXECUTION_ENGINE,
                    "task_in_progress",
                    f"Task {task_id} is in progress.",
                    subtask_id=task_id,
                )
            )

            start_time = time.time()  # Start timing the task execution
            try:
                await self.delegate_manager.invoke_notification(self, "task_execution_started", {"task_id": task_id, "task_details": task_def_effective})
                # Always call _execute_single_task with the effective task definition (Await the async call)
                result = await self._execute_single_task(task_def_effective, plan_parser)

                end_time = time.time()  # End timing
                duration_ms = (end_time - start_time) * 1000  # Duration in milliseconds

                self.state_manager.set_task_state(task_id, "completed")
                self.state_manager.store_task_result(task_id, result)
                self.state_manager.save_state() # Not async
                await self.delegate_manager.invoke_notification(self, "task_execution_completed", {"task_id": task_id, "status": "completed", "result_summary": str(result)[:100]})
                log_event(
                    log_message=LogMessage(
                        LogLevel.INFO,
                        ComponentType.EXECUTION_ENGINE,
                        "task_completed",
                        f"Task {task_id} completed successfully.",
                        subtask_id=task_id,
                        duration_ms=duration_ms,
                    )
                )
            except Exception as e: # This block will now handle all exceptions
                end_time = time.time()  # End timing
                duration_ms = (end_time - start_time) * 1000  # Duration in milliseconds
                if isinstance(e, TaskExecutionError):
                     # Handle TaskExecutionError specifically
                    error_message = str(e)
                    logger.error(f"Task {task_id} failed: {error_message}")
                    self.state_manager.set_task_state(task_id, "failed", {"error": error_message})

                    await self.delegate_manager.invoke_notification(self, "engine_error_occurred", {"error_type": type(e).__name__, "error_message": error_message})
                    log_event(
                         log_message=LogMessage(
                            LogLevel.ERROR,
                            ComponentType.EXECUTION_ENGINE,
                            "task_failed",
                            f"Task {task_id} failed: {error_message}",
                            subtask_id=task_id,
                            duration_ms=duration_ms,
                            details={"error": error_message, "traceback": traceback.format_exc()},
                        )
                    )
                    # Store the task result with error details
                    task_result_details = {
                        "status": "failed",
                        "error": error_message,
                        "error_details": e.details if hasattr(e, 'details') else None
                    }
                    self.state_manager.store_task_result(task_id, task_result_details)
                    self.state_manager.save_state() # Not async
                else:
                    # Handle any other unexpected error during task execution
                    error_message = f"Unexpected error during execution of task {task_id}: {str(e)}"
                    logger.exception(f"Unexpected error during execution of task {task_id}")  # Log with traceback
                    self.state_manager.set_task_state(task_id, "failed", {"error": error_message})
                    await self.delegate_manager.invoke_notification(self, "engine_error_occurred", event_data={"error_type": type(e).__name__, "error_message": error_message}) # Invoke engine_error_occurred delegate
                    log_event(
                         log_message=LogMessage(
                            LogLevel.CRITICAL,
                            ComponentType.EXECUTION_ENGINE,
                            "task_failed_unexpected",
                            error_message,
                            subtask_id=task_id,
                            duration_ms=duration_ms,
                            details={"error": error_message, "traceback": traceback.format_exc()},
                        )
                    )
                    # Store the task result with error details
                    task_result_details = {
                        "status": "failed",
                        "error": error_message,
                        "error_details": {"traceback": traceback.format_exc()} # Include traceback for unexpected errors
                    }
                    self.state_manager.store_task_result(task_id, task_result_details)
                    self.state_manager.save_state() # Not async


        logger.info(f"Finished execution of plan: {plan_id}")
        log_event(
            log_message=LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_finished", f"Finished execution of plan: {plan_id}")
        )
        if self.delegate_manager:
            await self.delegate_manager.invoke_notification(self, "engine_stopped", None)

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
