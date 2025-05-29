from abc import ABC, abstractmethod
import asyncio
from pathlib import Path
import logging
import yaml
import json
from pathlib import Path
import threading # Import threading
from typing import Optional

from ai_whisperer.ai_loop.ai_config import AIConfig
from ai_whisperer.context_management import ContextManager
# Delegate system removed
from ai_whisperer.execution_engine import ExecutionEngine
from .user_message_level import UserMessageLevel
from .state_management import StateManager # Import StateManager

from .config import load_config
from .logging_custom import LogMessage, LogLevel, ComponentType, log_event # Import logging components for log_event
from .model_info_provider import ModelInfoProvider
from .plan_runner import PlanRunner
from .initial_plan_generator import InitialPlanGenerator
from .project_plan_generator import OverviewPlanGenerator
from .plan_parser import ParserPlan

logger = logging.getLogger(__name__)

class BaseCliCommand(ABC):
    """Base class for all CLI commands."""
    def __init__(self, config: dict):
        self.config = config
        self.config_path = config.get('config_path') if isinstance(config, dict) else None

    @abstractmethod
    def execute(self) -> int:
        """Executes the command logic."""
        pass

    @abstractmethod
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        """Sets up the UI for the command if applicable (Textual UI removed)."""
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")

class ListModelsCliCommand(BaseCliCommand):
    """Command to list available OpenRouter models."""
    def __init__(self, config: dict, output_csv: str, delegate_manager: DelegateManager, detail_level: UserMessageLevel):
        super().__init__(config)
        self.output_csv = output_csv
        self.delegate_manager = delegate_manager # Store delegate_manager
        self.detail_level = detail_level # Store detail_level

    def execute(self):
        """Lists available OpenRouter models."""
        logger.debug(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully for listing models.")

        model_provider = ModelInfoProvider(self.config)

        # Always get the model list for possible console output
        detailed_models = model_provider.list_models()

        # If output_csv is set, write to CSV and notify
        if self.output_csv:
            model_provider.list_models_to_csv(self.output_csv)
            import asyncio
            asyncio.run(self.delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={"message": f"Successfully wrote model list to CSV: {self.output_csv}", "level": UserMessageLevel.INFO}
            ))

        avail_text = f"Available OpenRouter Models ({len(detailed_models)}):"
        logger.debug(avail_text)
        import asyncio
        asyncio.run(self.delegate_manager.invoke_notification(
            sender=self,
            event_type="user_message_display",
            event_data={"message": avail_text, "level": UserMessageLevel.INFO}
        ))
        # Only print details in DETAIL mode
        if self.detail_level == UserMessageLevel.DETAIL:
            for model in detailed_models:
                model_id = model.get('id', 'N/A')
                model_text = f"| {model_id}"

                details = [model_text]
                if 'context_length' in model:
                    details.append(f"Context Length: {model['context_length']}")
                if 'supported_parameters' in model:
                    details.append(f"Supported Parameters: {model['supported_parameters']}")
                if 'pricing' in model and isinstance(model['pricing'], dict):
                    pricing_info = model['pricing']
                    if 'prompt' in pricing_info:
                        details.append(f"Prompt Pricing: {pricing_info['prompt']}")
                    if 'completion' in pricing_info:
                        details.append(f"Completion Pricing: {pricing_info['completion']}")
                #if 'description' in model:
                #    details.append(f"Description: {model['description']}")

                detail_text = f"{' | '.join(details)}"
                logger.debug(detail_text)
                # Always send details to delegate_manager in DETAIL mode
                import asyncio
                asyncio.run(self.delegate_manager.invoke_notification(
                    sender=self,
                    event_type="user_message_display",
                    event_data={"message": detail_text, "level": UserMessageLevel.DETAIL}
                ))
        else:
            for model in detailed_models:
                model_id = model.get('id', 'N/A')
                model_text = f"- {model_id}"
                logger.debug(model_text)
                import asyncio
                asyncio.run(self.delegate_manager.invoke_notification(
                    sender=self,
                    event_type="user_message_display",
                    event_data={"message": model_text, "level": UserMessageLevel.INFO}
                ))
        return 0
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")


class GenerateInitialPlanCliCommand(BaseCliCommand):
    """Command to generate initial task YAML or a detailed subtask."""
    def __init__(self, config: dict, output_dir: str, requirements_path: str = None, delegate_manager=None): # Add delegate_manager parameter
        super().__init__(config)
        self.output_dir = output_dir
        self.requirements_path = requirements_path
        self.delegate_manager = delegate_manager

    def execute(self):
        """Generates initial task YAML or a detailed subtask."""
        logger.debug("Generating initial task plan (config already loaded, not reloading).")

        if not self.requirements_path:
            raise ValueError("Requirements path is required for initial plan generation.")

        plan_generator = InitialPlanGenerator(self.config, self.delegate_manager, self.output_dir)
        logger.debug(f"Generating initial task plan from: {self.requirements_path}")

        result_path = plan_generator.generate_plan(self.requirements_path, self.config.get('config_path', ''))

        logger.debug(f"[green]Successfully generated task JSON: {result_path}[/green]")
        return 0
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")

class GenerateOverviewPlanCliCommand(BaseCliCommand):
    """Command to generate the overview plan and subtasks from an initial plan."""
    def __init__(self, config: dict, output_dir: str, initial_plan_path: str, delegate_manager=None): # Add delegate_manager parameter
        super().__init__(config)
        self.output_dir = output_dir
        self.initial_plan_path = initial_plan_path
        self.delegate_manager = delegate_manager # Store delegate_manager

    def execute(self):
        """Generates the overview plan and subtasks."""
        logger.info("Starting AI Whisperer overview plan and subtask generation...")
        logger.debug("Configuration loaded successfully.")

        project_plan_generator = OverviewPlanGenerator(self.config, self.output_dir)
        result = project_plan_generator.generate_full_plan(self.initial_plan_path, self.config.get('config_path', ''))

        logger.debug(f"[green]Successfully generated project plan:[/green]")
        logger.debug(f"- Task plan: {result['task_plan']}")
        if result["task_plan"] != result["overview_plan"]:
            logger.debug(f"- Overview plan: {result['overview_plan']}")
        logger.debug(f"- Subtasks generated: {len(result['subtasks'])}")
        for i, subtask_path in enumerate(result["subtasks"], 1):
            logger.debug(f"  {i}. {subtask_path}")

        return 0
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")

class RefineCliCommand(BaseCliCommand):
    """Command to refine a requirements document."""
    def __init__(self, config: dict, input_file: str, iterations: int = 1, prompt_file: str = None, output: str = None, delegate_manager=None): # Add delegate_manager parameter
        super().__init__(config)
        self.input_file = input_file
        self.iterations = iterations
        self.prompt_file = prompt_file
        self.output = output # This might need adjustment based on how refine handles output
        self.delegate_manager = delegate_manager # Store delegate_manager

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
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")

class RunCliCommand(BaseCliCommand):
    """Command to execute a project plan."""
    def __init__(self, config: dict, plan_file: str, state_file: str, monitor: bool = False, delegate_manager=None): # Add delegate_manager parameter
        # Accept config dict directly for consistency with other commands
        self.config = config
        self.plan_file = plan_file
        self.state_file = state_file
        self.monitor = monitor
        self.delegate_manager = delegate_manager # Store delegate_manager
        self._ai_runner_shutdown_event = threading.Event() # Event to signal AI Runner thread shutdown
        # Store the shutdown event in the delegate manager's shared state
        if self.delegate_manager:
            self.delegate_manager.set_shared_state("ai_runner_shutdown_event", self._ai_runner_shutdown_event)
        # Store config_path for logging/debugging compatibility
        if isinstance(self.config, dict):
            self.config_path = self.config.get('config_path', None)
            if 'config_path' not in self.config:
                self.config['config_path'] = self.config_path
        else:
            self.config_path = None

    def _run_plan_in_thread(self, plan_parser: ParserPlan, state_file_path: str, shutdown_event: Optional[threading.Event] = None, result_holder=None):
        logger.debug("_run_plan_in_thread started.")
        """Core plan execution logic to be run in a separate thread."""
        # Pass the shutdown_event to the PlanRunner
        plan_runner = PlanRunner(self.config, shutdown_event=shutdown_event, monitor=self.monitor, delegate_manager=self.delegate_manager)

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
            # Store the result in the result_holder if provided
            if result_holder is not None:
                result_holder[0] = plan_successful
        finally:
            logger.debug("_run_plan_in_thread finished.")
            # Removed the call to monitor_instance.stop() from here.
            # The main thread or the UI thread's shutdown process should handle the overall monitor shutdown.
            pass



    def execute(self):
        """Executes a project plan."""
        logger.info("Starting AI Whisperer run process...")
        logger.debug(f"RunCliCommand initialized with plan_file: {self.plan_file}, state_file: {self.state_file}, monitor: {self.monitor}, delegate_manager: {self.delegate_manager}") # Add logging for RunCliCommand initialization details
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
        # Use a mutable holder to capture the result from the thread
        thread_result = [None]
        ai_runner_thread = threading.Thread(
            target=self._run_plan_in_thread,
            args=(plan_parser, self.state_file, self._ai_runner_shutdown_event, thread_result),
            name="AIRunnerThread"
        )
        ai_runner_thread.start()
        logger.debug("AI Runner thread started.")
        logger.debug(f"AI Runner thread is alive: {ai_runner_thread.is_alive()}") # Log thread status

        # Flag to track if shutdown has been initiated by the main thread
        shutdown_initiated_by_main = False

        try:
            # The main thread waits for the AI Runner thread to finish.
            # The AI Runner thread will stop if the shutdown event is set (by the monitor or KeyboardInterrupt).
            logger.debug("Main thread waiting for AI Runner thread to join...")
            logger.debug(f"Main thread: _ai_runner_shutdown_event state before join: {self._ai_runner_shutdown_event.is_set()}") # Log event state
            logger.debug(f"Main thread: AI Runner thread is alive before join: {ai_runner_thread.is_alive()}") # Log thread status before join
            ai_runner_thread.join()
            logger.debug("AI Runner thread joined.")
            logger.debug(f"Main thread: AI Runner thread is alive after join: {ai_runner_thread.is_alive()}") # Log thread status after join
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
                logger.debug("Finally block: AI Runner thread is alive, waiting to join...") # Log thread status
                logger.debug("Finally block: Waiting for AI Runner thread to join...")
                ai_runner_thread.join()
                logger.debug("Finally block: AI Runner thread joined.")
                logger.debug(f"Finally block: AI Runner thread is alive after join: {ai_runner_thread.is_alive()}") # Log thread status
            if self.monitor and ui_thread and ui_thread.is_alive():
                 logger.debug("Finally block: Waiting for UI thread to join...")
                 ui_thread.join()
                 logger.debug("Finally block: UI thread joined.")
            logger.debug("Finally block finished.")

        # Return 0 for success, 1 for failure
        logger.debug(f"RunCliCommand execute finished. Thread result: {thread_result[0]}") # Log final result
        if thread_result[0] is True:
            return 0
        else:
            return 1
    def setup_ui(self, delegate_manager: DelegateManager, ai_config: AIConfig, context_manager: ContextManager, config: dict, **kwargs):
        raise NotImplementedError("setup_ui is not implemented. Textual UI has been removed. Implement websocket/react UI integration here.")
