import argparse
from abc import ABC, abstractmethod
from pathlib import Path
import logging
import yaml
import json
import os
import csv

from .config import load_config
from .exceptions import AIWhispererError, ConfigError, OpenRouterAPIError, SubtaskGenerationError, SchemaValidationError
from .utils import setup_logging, setup_rich_output
from .ai_service_interaction import OpenRouterAPI
from rich.console import Console
from .model_info_provider import ModelInfoProvider
from .plan_runner import PlanRunner
from .initial_plan_generator import InitialPlanGenerator
from .project_plan_generator import ProjectPlanGenerator
from .plan_parser import ParserPlan

logger = logging.getLogger(__name__)
console = Console() # Initialize console here for use in command classes

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
        console.print(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully for listing models.")

        model_provider = ModelInfoProvider(self.config)

        if self.output_csv:
            model_provider.list_models_to_csv(self.output_csv)
            console.print(f"[green]Successfully wrote model list to CSV: {self.output_csv}[/green]")
        else:
            detailed_models = model_provider.list_models()
            console.print("[bold green]Available OpenRouter Models:[/bold green]")
            for model in detailed_models:
                 if isinstance(model, str):
                    console.print(f"- {model}")
                 else:
                    console.print(f"- {model.get('id', 'N/A')}")
        return 0

class GenerateInitialPlanCommand(BaseCommand):
    """Command to generate initial task YAML or a detailed subtask."""
    def __init__(self, config_path: str, output_dir: str, requirements_path: str = None):
        super().__init__(config_path)
        self.output_dir = output_dir
        self.requirements_path = requirements_path

    def execute(self):
        """Generates initial task YAML or a detailed subtask."""
        console.print(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully.")

        if not self.requirements_path:
            raise ValueError("Requirements path is required for initial plan generation.")

        plan_generator = InitialPlanGenerator(self.config, self.output_dir)
        console.print(f"Generating initial task plan from: {self.requirements_path}")

        result_path = plan_generator.generate_plan(self.requirements_path, self.config_path)

        console.print(f"[green]Successfully generated task JSON: {result_path}[/green]")
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

        project_plan_generator = ProjectPlanGenerator(self.config, self.output_dir)
        result = project_plan_generator.generate_full_plan(self.initial_plan_path, self.config_path)

        console.print(f"[green]Successfully generated project plan:[/green]")
        console.print(f"- Task plan: {result['task_plan']}")
        if result["task_plan"] != result["overview_plan"]:
            console.print(f"- Overview plan: {result['overview_plan']}")
        console.print(f"- Subtasks generated: {len(result['subtasks'])}")
        for i, subtask_path in enumerate(result["subtasks"], 1):
            console.print(f"  {i}. {subtask_path}")

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
        console.print(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully.")

        # Placeholder for refine logic - will need to integrate Orchestrator or similar
        console.print("[yellow]Refine command not fully implemented in command object yet.[/yellow]")
        # Example of how it might look, based on original cli.py:
        # from .orchestrator import Orchestrator
        # orchestrator = Orchestrator(self.config, self.output)
        # current_input_file = self.input_file
        # for i in range(self.iterations):
        #     console.print(f"[yellow]Refinement iteration {i+1} of {self.iterations}...[/yellow]")
        #     result = orchestrator.refine_requirements(input_filepath_str=current_input_file)
        #     current_input_file = result
        # console.print(f"[green]Successfully refined requirements: {result}[/green]")
        return 0 # Or appropriate exit code

class RunCommand(BaseCommand):
    """Command to execute a project plan."""
    def __init__(self, config_path: str, plan_file: str, state_file: str):
        super().__init__(config_path)
        self.plan_file = plan_file
        self.state_file = state_file

    def execute(self):
        """Executes a project plan."""
        logger.info("Starting AI Whisperer run process...")
        console.print(f"Loading configuration from: {self.config_path}")
        logger.debug("Configuration loaded successfully.")

        plan_file_path = Path(self.plan_file)
        console.print(f"Loading plan from: {plan_file_path}")
        plan_parser = ParserPlan()
        plan_parser.load_overview_plan(str(plan_file_path))
        logger.debug("Plan file parsed and validated successfully.")

        plan_runner = PlanRunner(self.config)

        logger.debug("Calling plan_runner.run_plan...")
        plan_successful = plan_runner.run_plan(plan_parser=plan_parser, state_file_path=self.state_file)
        logger.debug(f"plan_runner.run_plan returned: {plan_successful}")

        if plan_successful:
            console.print("[green]Plan execution completed successfully.[/green]")
            logger.debug("Returning 0 for success.")
            return 0
        else:
            console.print("[bold red]Plan execution finished with failures.[/bold red]")
            logger.debug("Returning 1 for failures.")
            return 1