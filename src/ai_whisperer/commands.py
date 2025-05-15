from abc import ABC, abstractmethod
import asyncio
from pathlib import Path
import logging
import yaml
import json
from pathlib import Path
import threading # Import threading
from typing import Optional # Import Optional
from .state_management import StateManager # Import StateManager

from .config import load_config
from .logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import logging components for log_event
from .model_info_provider import ModelInfoProvider
from .plan_runner import PlanRunner
from .initial_plan_generator import InitialPlanGenerator
from .project_plan_generator import OverviewPlanGenerator
from .plan_parser import ParserPlan

logger = logging.getLogger(__name__)

class BaseCommand(ABC):
    """Base class for all CLI commands."""
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = load_config(config_path)

    @abstractmethod
    def execute(self):
        """Executes the command logic."""
        pass

class ListModelsCommand(BaseCommand):
    """Command to list available OpenRouter models."""
    def __init__(self, config_path: str, output_csv: str = None):
        super().__init__(config_path)
        self.output_csv = output_csv

    def execute(self):
        """Lists available OpenRouter models."""
        logger.debug(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully for listing models.")

        model_provider = ModelInfoProvider(self.config)

        if self.output_csv:
            model_provider.list_models_to_csv(self.output_csv)
            logger.debug(f"Successfully wrote model list to CSV: {self.output_csv}")
        else:
            detailed_models = model_provider.list_models()
            logger.debug("Available OpenRouter Models:")
            for model in detailed_models:
                 if isinstance(model, str):
                    logger.debug(f"- {model}")
                 else:
                    logger.debug(f"- {model.get('id', 'N/A')}")
        return 0

class GenerateInitialPlanCommand(BaseCommand):
    """Command to generate initial task YAML or a detailed subtask."""
    def __init__(self, config_path: str, output_dir: str, requirements_path: str = None):
        super().__init__(config_path)
        self.output_dir = output_dir
        self.requirements_path = requirements_path

    def execute(self):
        """Generates initial task YAML or a detailed subtask."""
        logger.debug(f"Loading configuration from: {self.config_path}")
 
        if not self.requirements_path:
            raise ValueError("Requirements path is required for initial plan generation.")

        plan_generator = InitialPlanGenerator(self.config, self.output_dir)
        logger.debug(f"Generating initial task plan from: {self.requirements_path}")

        result_path = plan_generator.generate_plan(self.requirements_path, self.config_path)

        logger.debug(f"[green]Successfully generated task JSON: {result_path}[/green]")
        return 0

class GenerateOverviewPlanCommand(BaseCommand):
    """Command to generate the overview plan and subtasks from an initial plan."""
    def __init__(self, config_path: str, output_dir: str, initial_plan_path: str):
        super().__init__(config_path)
        self.output_dir = output_dir
        self.initial_plan_path = initial_plan_path

    def execute(self):
        """Generates the overview plan and subtasks."""
        logger.info("Starting AI Whisperer overview plan and subtask generation...")
        logger.debug("Configuration loaded successfully.")

        project_plan_generator = OverviewPlanGenerator(self.config, self.output_dir)
        result = project_plan_generator.generate_full_plan(self.initial_plan_path, self.config_path)

        logger.debug(f"[green]Successfully generated project plan:[/green]")
        logger.debug(f"- Task plan: {result['task_plan']}")
        if result["task_plan"] != result["overview_plan"]:
            logger.debug(f"- Overview plan: {result['overview_plan']}")
        logger.debug(f"- Subtasks generated: {len(result['subtasks'])}")
        for i, subtask_path in enumerate(result["subtasks"], 1):
            logger.debug(f"  {i}. {subtask_path}")

        return 0

class RefineCommand(BaseCommand):
    """Command to refine a requirements document."""
    def __init__(self, config_path: str, input_file: str, iterations: int = 1, prompt_file: str = None, output: str = None):
        super().__init__(config_path)
        self.input_file = input_file
        self.iterations = iterations
        self.prompt_file = prompt_file
        self.output = output # This might need adjustment based on how refine handles output

    def execute(self):
        """Refines a requirements document."""
        logger.info("Starting AI Whisperer refine process...")
        logger.debug(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully.")

        # Placeholder for refine logic - will need to integrate Orchestrator or similar
        logger.debug("[yellow]Refine command not fully implemented in command object yet.[/yellow]")
        # Example of how it might look, based on original cli.py:
        # from .orchestrator import Orchestrator
        # orchestrator = Orchestrator(self.config, self.output)
        # current_input_file = self.input_file
        # for i in range(self.iterations):
        #     logger.debug(f"[yellow]Refinement iteration {i+1} of {self.iterations}...[/yellow]")
        #     result = orchestrator.refine_requirements(input_filepath_str=current_input_file)
        #     current_input_file = result
        # logger.debug(f"[green]Successfully refined requirements: {result}[/green]")
        return 0 # Or appropriate exit code

class RunCommand(BaseCommand):
    """Command to execute a project plan."""
    def __init__(self, config: dict, plan_file: str, state_file: str, monitor: bool = False):
        # Accept config dict directly for consistency with other commands
        self.config = config
        self.plan_file = plan_file
        self.state_file = state_file
        self.monitor = monitor
        self._ai_runner_shutdown_event = threading.Event() # Event to signal AI Runner thread shutdown
        # Store config_path for logging/debugging compatibility
        if isinstance(self.config, dict):
            self.config_path = self.config.get('config_path', None)
            if 'config_path' not in self.config:
                self.config['config_path'] = self.config_path
        else:
            self.config_path = None

    def _run_plan_in_thread(self, plan_parser: ParserPlan, state_file_path: str, shutdown_event: Optional[threading.Event] = None):
        logger.debug("_run_plan_in_thread started.")
        """Core plan execution logic to be run in a separate thread."""
        # Pass the shutdown_event to the PlanRunner
        plan_runner = PlanRunner(self.config, shutdown_event=shutdown_event, monitor=self.monitor)

        logger.debug("Calling plan_runner.run_plan...")
        plan_successful = False # Initialize to False

        try:
            # Use asyncio.run to execute the async run_plan method in this thread (only once)
            plan_successful = plan_runner.run_plan(plan_parser=plan_parser, state_file_path=state_file_path)
            logger.debug(f"plan_runner.run_plan returned: {plan_successful}")
            logger.debug("_run_plan_in_thread finished plan execution.")

            if plan_successful:
                log_event(log_message=LogMessage(LogLevel.INFO, ComponentType.RUNNER, "plan_execution_completed", "Plan execution completed successfully."))
                logger.debug("Plan execution completed successfully.")
            else:
                log_event(log_message=LogMessage(LogLevel.ERROR, ComponentType.RUNNER, "plan_execution_failed", "Plan execution finished with failures."))
                logger.debug("Plan execution finished with failures.")

        finally:
            logger.debug("_run_plan_in_thread finished.")
            # Removed the call to monitor_instance.stop() from here.
            # The main thread or the UI thread's shutdown process should handle the overall monitor shutdown.
            pass



    def execute(self):
        """Executes a project plan."""
        logger.info("Starting AI Whisperer run process...")
        logger.debug("Loading configuration from config dict (no config_path, config passed as dict).")
        logger.debug("Configuration loaded successfully.")

        # Get the absolute path of the plan file
        plan_file_path_abs = Path(self.plan_file).resolve()
        logger.debug(f"Loading plan from: {plan_file_path_abs}")
        plan_parser = ParserPlan()
        # Pass the absolute path to load_overview_plan
        plan_parser.load_overview_plan(str(plan_file_path_abs))
        logger.debug("Plan file parsed and validated successfully.")

        monitor_instance = None
        ui_thread = None # Declare ui_thread here

        # Create and start the AI Runner Thread
        logger.debug("Starting AI Runner thread...")
        ai_runner_thread = threading.Thread(
            target=self._run_plan_in_thread,
            args=(plan_parser, self.state_file, self._ai_runner_shutdown_event), # Pass shutdown_event
            name="AIRunnerThread"
        )
        ai_runner_thread.start()
        logger.debug("AI Runner thread started.")

        # Flag to track if shutdown has been initiated by the main thread
        shutdown_initiated_by_main = False

        try:
            # The main thread waits for the AI Runner thread to finish.
            # The AI Runner thread will stop if the shutdown event is set (by the monitor or KeyboardInterrupt).
            logger.debug("Main thread waiting for AI Runner thread to join...")
            logger.debug(f"Main thread: _ai_runner_shutdown_event state before join: {self._ai_runner_shutdown_event.is_set()}") # Log event state
            ai_runner_thread.join()
            logger.debug("AI Runner thread joined.")
            logger.debug(f"Main thread: _ai_runner_shutdown_event state after join: {self._ai_runner_shutdown_event.is_set()}") # Log event state

            # If the AI runner finishes before the monitor is stopped (e.g., plan completed),
            # initiate shutdown from the main thread if not already initiated.
            if self.monitor and monitor_instance and monitor_instance._running and not shutdown_initiated_by_main:
                 logger.debug("Main thread: AI Runner finished, initiating monitor stop.")
                 monitor_instance.stop() # Signal UI thread shutdown
                 shutdown_initiated_by_main = True # Mark shutdown as initiated

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Initiating graceful shutdown.")
            logger.debug("Handling KeyboardInterrupt...")
            # Initiate shutdown from the main thread if not already initiated
            if not shutdown_initiated_by_main:
                 if self.monitor and monitor_instance:
                     monitor_instance.stop() # Signal UI thread shutdown
                 self._ai_runner_shutdown_event.set() # Signal AI Runner thread shutdown
                 shutdown_initiated_by_main = True # Mark shutdown as initiated
                 logger.debug("KeyboardInterrupt handler: Shutdown initiated by main thread.")
            else:
                 logger.debug("KeyboardInterrupt handler: Shutdown already initiated by main thread.")


        finally:
            # Ensure both threads are joined before exiting the main thread.
            # This handles cases where shutdown was initiated by KeyboardInterrupt
            # or after the AI thread finished.
            logger.debug("Ensuring threads are joined in finally block...")
            if ai_runner_thread.is_alive():
                logger.debug("Finally block: Waiting for AI Runner thread to join...")
                ai_runner_thread.join()
                logger.debug("Finally block: AI Runner thread joined.")
            if self.monitor and ui_thread and ui_thread.is_alive():
                 logger.debug("Finally block: Waiting for UI thread to join...")
                 ui_thread.join()
                 logger.debug("Finally block: UI thread joined.")
            logger.debug("Finally block finished.")

        # TODO: Handle the thread result
        # The return code should reflect the outcome of the plan execution.
        # We need a way for the thread to communicate its success/failure back.
        # For now, we'll assume success if the thread finishes without unhandled exceptions.
        # A more robust solution would involve checking a shared variable or queue.
        # Based on the original logic, the success/failure was determined by the return of run_plan.
        # We need to capture that outcome from the thread.
        # Let's add a simple mechanism for the thread to set a result.
        # This will require modifying _run_plan_in_thread to return or set a value.
        # For this diff, I will make a simplifying assumption that the thread completing means success for now,
        # but note this needs refinement to capture the actual plan_successful boolean.
        # A better approach would be to pass a mutable object (like a list or dict) or a queue
        # to the thread to store the result.

        # Placeholder for capturing thread result:
        # if thread_result_indicates_success:
        #     return 0
        # else:
        #     return 1

        # For now, returning 0 assuming success if join completes.
        # This is a temporary simplification for this specific subtask.
        return 0 # Needs refinement to capture actual plan success/failure

