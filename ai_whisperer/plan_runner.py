"""
This module contains the PlanRunner class, responsible for executing a project plan.
"""

import logging
import traceback
import threading # Import threading
from typing import Dict, Any, Optional # Import Optional

from .delegate_manager import DelegateManager # Import DelegateManager
from .config import load_config
from .tools.tool_registry import get_tool_registry
from .tools.read_file_tool import ReadFileTool
from .tools.write_file_tool import WriteFileTool
from .tools.execute_command_tool import ExecuteCommandTool
from .exceptions import OrchestratorError, PlanNotLoadedError
from .plan_parser import ParserPlan
from .state_management import StateManager
from .execution_engine import ExecutionEngine
from .logging_custom import (
    setup_logging,
    get_logger,
    LogMessage,
    LogLevel,
    ComponentType,
    log_event,
)

logger = logging.getLogger(__name__)
logger.propagate = False

class PlanRunner:
    """
    Executes a project plan from a parsed plan object.
    """
    def __init__(self, config: Dict[str, Any], shutdown_event: threading.Event, monitor: bool = False, delegate_manager: Optional[DelegateManager] = None): # Add delegate_manager parameter
        """
        Initializes the PlanRunner with application configuration.

        Args:
            config: The loaded application configuration dictionary.
        """
        self.config = config
        self.shutdown_event = shutdown_event # Store the shutdown event
        self.monitor_enabled = monitor # Store the monitor flag
        self.delegate_manager = delegate_manager # Store delegate_manager
        self._register_tools()
        logger.info("PlanRunner initialized.")

    def _register_tools(self):
        """Registers the necessary tools with the ToolRegistry."""
        tool_registry = get_tool_registry()
        # Register main tool instances only (no legacy aliases)
        tool_registry.register_tool(ReadFileTool())
        tool_registry.register_tool(WriteFileTool())
        tool_registry.register_tool(ExecuteCommandTool())

        logger.debug("Tools registered with ToolRegistry.")

    def run_plan(self, plan_parser: ParserPlan, state_file_path: str) -> bool:
        """
        Executes a overview plan from a parsed plan object.

        Args:
            plan_parser: A ParserPlan instance with the loaded plan.
            state_file_path: Path to the state file for loading/saving state.

        Returns:
            bool: True if the plan execution completed successfully (no failed tasks), False otherwise.

        Raises:
            PlanNotLoadedError: If the plan_parser does not have a loaded plan.
            IOError: If there are issues loading or saving the state file.
            OrchestratorError: For other orchestration-specific issues.
        """
        logger.info("Starting plan execution...")
        log_event(LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_start", "Starting plan execution."))
        logger.debug(f"PlanRunner initialized with delegate_manager: {self.delegate_manager}") # Log delegate_manager
        try:
            plan_data = plan_parser.get_parsed_plan()
            if plan_data is None:
                raise PlanNotLoadedError("Plan data is not loaded in the provided ParserPlan.")
        except PlanNotLoadedError as e:
            logger.error(f"Plan not loaded: {e}")
            log_event(LogMessage(LogLevel.ERROR, ComponentType.RUNNER, "plan_not_loaded", f"Plan not loaded: {e}"))
            raise  # Re-raise the original exception

        # Initialize or load state
        logger.debug(f"Loading state from: {state_file_path}") # Log state file path
        state_manager = StateManager(state_file_path)
        try:
            state_manager.load_state()
            logger.info(f"Loaded state from {state_file_path}")
            log_event(
                LogMessage(LogLevel.INFO, ComponentType.RUNNER, "state_loaded", f"Loaded state from {state_file_path}")
            )
        except FileNotFoundError:
            logger.info(f"State file not found at {state_file_path}. Starting with empty state.")
            log_event(
                LogMessage(
                    LogLevel.INFO,
                    ComponentType.RUNNER,
                    "state_file_not_found",
                    f"State file not found at {state_file_path}. Starting with empty state.",
                )
            )
            try:
                state_manager.initialize_state(plan_data)  # Initialize with plan data
            except IOError as e:
                logger.error(f"Error initializing state and saving to {state_file_path}: {e}")
                log_event(
                    LogMessage(
                        LogLevel.ERROR,
                        ComponentType.RUNNER,
                        "state_initialize_save_error",
                        f"Error initializing state and saving to {state_file_path}: {e}",
                    )
                )
                raise OrchestratorError(f"Failed to initialize state and save to {state_file_path}: {e}") from e
        except IOError as e:
            logger.error(f"Error loading state from {state_file_path}: {e}")
            log_event(
                LogMessage(
                    LogLevel.ERROR,
                    ComponentType.RUNNER,
                    "state_load_error",
                    f"Error loading state from {state_file_path}: {e}",
                )
            )
            raise OrchestratorError(f"Failed to load state from {state_file_path}: {e}") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading state from {state_file_path}: {e}")
            log_event(
                LogMessage(
                    LogLevel.CRITICAL,
                    ComponentType.RUNNER,
                    "state_load_unexpected_error",
                    f"An unexpected error occurred while loading state from {state_file_path}: {e}",
                    details={"error": str(e), "traceback": traceback.format_exc()},
                )
            )
            raise OrchestratorError(
                f"An unexpected error occurred while loading state from {state_file_path}: {e}"
            ) from e

        # Initialize Execution Engine
        logger.debug("Initializing Execution Engine...") # Log before initializing Execution Engine
        # Use the provided monitor instance if available, otherwise create a new one
        config_path = self.config.get('config_path') if isinstance(self.config, dict) and 'config_path' in self.config else None
        # Pass the shutdown event to the ExecutionEngine
        # Create PromptSystem instance
        from .prompt_system import PromptSystem, PromptConfiguration
        prompt_system = PromptSystem(PromptConfiguration(self.config))
        monitor = getattr(self, 'monitor_enabled', None)

        execution_engine = ExecutionEngine(state_manager, self.config, prompt_system, shutdown_event=self.shutdown_event, delegate_manager=self.delegate_manager) # Pass delegate_manager
        logger.info("Execution Engine initialized.")
        log_event(
            LogMessage(
                LogLevel.INFO, ComponentType.RUNNER, "execution_engine_initialized", "Execution Engine initialized."
            )
        )

        # Execute the plan
        plan_successful = True  # Flag to track overall plan success
        try:
            logger.debug("Calling execution_engine.execute_plan...") # Log before calling execute_plan
            execution_engine.execute_plan(plan_parser)
            logger.debug("execution_engine.execute_plan finished.") # Log after calling execute_plan
            logger.info("Execution Engine finished plan execution.")
            log_event(
                LogMessage(
                    LogLevel.INFO,
                    ComponentType.RUNNER,
                    "execution_engine_finished",
                    "Execution Engine finished plan execution.",
                )
            )
        except Exception as e:
            logger.exception(f"An unexpected error occurred during plan execution: {e}")
            log_event(
                LogMessage(
                    LogLevel.CRITICAL,
                    ComponentType.RUNNER,
                    "plan_execution_unexpected_error",
                    f"An unexpected error occurred during plan execution: {e}",
                    details={"error": str(e), "traceback": traceback.format_exc()},
                )
            )
            plan_successful = False  # Set flag to False on unexpected error
            # Do not re-raise here, allow state to be saved and status checked

        # Save final state
        logger.debug(f"Saving final state to: {state_file_path}") # Log before saving state
        try:
            state_manager.save_state()
            logger.debug("Final state saved.") # Log after saving state
            logger.info(f"Saved final state to {state_file_path}")
            log_event(
                LogMessage(
                    LogLevel.INFO, ComponentType.RUNNER, "state_saved", f"Saved final state to {state_file_path}."
                )
            )
        except IOError as e:
            logger.error(f"Error saving final state to {state_file_path}: {e}")
            log_event(
                LogMessage(
                    LogLevel.ERROR,
                    ComponentType.RUNNER,
                    "state_save_error",
                    f"Error saving final state to {state_file_path}: {e}",
                )
            )
            plan_successful = False  # Consider save errors as plan failure
            raise OrchestratorError(f"Failed to save final state to {state_file_path}: {e}") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred while saving final state to {state_file_path}: {e}")
            log_event(
                LogMessage(
                    LogLevel.CRITICAL,
                    ComponentType.RUNNER,
                    "state_save_unexpected_error",
                    f"An unexpected error occurred while saving final state to {state_file_path}: {e}",
                    details={"error": str(e), "traceback": traceback.format_exc()},
                )
            )
            plan_successful = False  # Consider unexpected save errors as plan failure
            # Do not re-raise here

        # Check if any tasks failed in the state manager
        logger.debug("Checking for failed tasks in state manager...") # Log before checking failed tasks
        failed_tasks = [
            task_id
            for task_id, task_state in state_manager.state.get("tasks", {}).items()
            if task_state.get("status") == "failed"
        ]

        if failed_tasks:
            logger.error(
                f"Plan execution finished with failures for plan: {state_manager.state.get('plan_id', 'unknown')}"
            )
            log_event(
                LogMessage(
                    LogLevel.ERROR,
                    ComponentType.RUNNER,
                    "plan_execution_failed",
                    f"Plan execution finished with failures. Failed tasks: {', '.join(failed_tasks)}",
                )
            )
            plan_successful = False  # Set flag to False if any task failed

        if plan_successful:
            logger.debug("Plan execution successful.") # Log success
            logger.info(
                f"Plan execution finished successfully for plan: {state_manager.state.get('plan_id', 'unknown')}"
            )
            log_event(
                LogMessage(
                    LogLevel.INFO,
                    ComponentType.RUNNER,
                    "plan_execution_success",
                    "Plan execution finished successfully.",
                )
            )
            # Assert delegate_manager is never None
            assert self.delegate_manager is not None, "delegate_manager must not be None in PlanRunner."
            self.delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={
                    "message": "Plan execution passed.",
                    "level": "INFO"
                }
            )
            return True  # Indicate overall success
        else:
            logger.debug("Plan execution failed.") # Log failure
            logger.error(
                f"Plan execution finished with overall failure for plan: {state_manager.state.get('plan_id', 'unknown')}"
            )
            log_event(
                LogMessage(
                    LogLevel.ERROR,
                    ComponentType.RUNNER,
                    "plan_execution_overall_failure",
                    "Plan execution finished with overall failure.",
                )
            )
            return False  # Indicate overall failure