import argparse
import sys
import logging
import yaml
import json
from pathlib import Path
import os
import csv

# Import necessary components from the application
from .config import load_config
from .exceptions import AIWhispererError, ConfigError, OpenRouterAPIError, SubtaskGenerationError, SchemaValidationError
from .utils import setup_logging, setup_rich_output
from rich.console import Console
from .commands import ListModelsCommand, GenerateInitialPlanCommand, GenerateOverviewPlanCommand, RefineCommand, RunCommand, BaseCommand # Import command classes
from . import logging_custom as logging

logger = logging.get_logger(__name__)

def main(args=None) -> list[BaseCommand]:
    """Main entry point for the AI Whisperer CLI application.

    Parses command-line arguments and instantiates the appropriate command object.
    Accepts an optional 'args' parameter for testability (list of CLI args, or None to use sys.argv).
    Returns the instantiated command object.
    """
    # Add debug print to confirm main function execution
    print("DEBUG: Entered main function")
    # Add debug print to confirm execution reaches setup_logging
    print("DEBUG: About to call setup_logging")
    # Setup logging and rich console output first (keep this here for initial setup)
    setup_logging()
    console = setup_rich_output()

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application for generating task plans and refining requirements.",
        prog="ai-whisperer",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    parser.add_argument(
        "--project-dir", type=str, default=None, help="Path to the project directory (overrides auto-detection)."
    )

    # --- Generate Initial Plan Command ---
    generate_initial_plan_parser = subparsers.add_parser("generate-initial-plan", help="Generate the initial task plan YAML")
    generate_initial_plan_parser.add_argument(
        "--requirements",
        required=True, # Requirements path is required for initial plan generation
        help="Path to the requirements Markdown file. Required for initial plan generation.",
    )
    generate_initial_plan_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    generate_initial_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # --- Generate Overview Plan Command ---
    generate_overview_plan_parser = subparsers.add_parser("generate-overview-plan", help="Generate the overview plan and subtasks from an initial plan")
    generate_overview_plan_parser.add_argument(
        "--initial-plan",
        required=True,
        help="Path to the initial task plan JSON file.",
    )
    generate_overview_plan_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    generate_overview_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # --- Generate Full Project Command ---
    generate_full_project_parser = subparsers.add_parser("generate-full-project", help="Generate a complete project plan (initial plan, overview, and subtasks)")
    generate_full_project_parser.add_argument(
        "--requirements",
        required=True,
        help="Path to the requirements Markdown file.",
    )
    generate_full_project_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    generate_full_project_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # --- List Models Command ---
    list_models_parser = subparsers.add_parser("list-models", help="List available OpenRouter models")
    list_models_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file."
    )
    list_models_parser.add_argument(
        "--output-csv", type=str, required=False, help="Path to output CSV file for --list-models command."
    )

    # --- Refine Command ---
    refine_parser = subparsers.add_parser("refine", help="Refine a requirements document using an AI model")
    refine_parser.add_argument("input_file", help="Path to the input requirements document to refine.")
    refine_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file."
    )
    refine_parser.add_argument(
        "--prompt-file",
        required=False,
        help="Path to a custom prompt file. If not provided, a default prompt will be used.",
    )
    refine_parser.add_argument("--iterations", type=int, default=1, help="Number of refinement iterations to perform.")
    refine_parser.add_argument("--output", required=False, help="Path to output directory or file.")

    # --- Run Command ---
    run_parser = subparsers.add_parser("run", help="Execute a project plan from an overview JSON file.")
    run_parser.add_argument(
        "--plan-file", required=True, help="Path to the input overview JSON file containing the task plan."
    )
    run_parser.add_argument(
        "--state-file",
        required=True,
        help="Path to the state file. Used for loading previous state and saving current state.",
    )
    run_parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration YAML file.",
    )

     # Use parse_args (let argparse handle errors and exit codes)
    try:
        if args is not None:
            parsed_args = parser.parse_args(args)
        else:
            parsed_args = parser.parse_args()
        logger.debug("Using parse_args.")
        logger.debug(f"Parsed arguments: {parsed_args}")
        logger.debug(f"Command: {parsed_args.command}")

        # Determine project directory (might need adjustment depending on how this is used later)
        if parsed_args.project_dir:
            project_dir = Path(parsed_args.project_dir).resolve()
        else:
            # Fallback to previous logic or default
            project_dir = Path(__file__).parent.parent.parent.resolve()


        # --- Instantiate Command Object ---
        command_object = None
        if parsed_args.command == "list-models":
            commands = [ListModelsCommand(
                config_path=parsed_args.config,
                output_csv=parsed_args.output_csv
            )]
        elif parsed_args.command == "generate-initial-plan":
            commands = [GenerateInitialPlanCommand(
                config_path=parsed_args.config,
                output_dir=parsed_args.output,
                requirements_path=parsed_args.requirements,
            )]
        elif parsed_args.command == "generate-overview-plan":
             commands = [GenerateOverviewPlanCommand(
                 config_path=parsed_args.config,
                 output_dir=parsed_args.output,
                 initial_plan_path=parsed_args.initial_plan
             )]
        elif parsed_args.command == "generate-full-project":
            # This command returns a list of the two sub-commands
            commands = [
                GenerateInitialPlanCommand(
                    config_path=parsed_args.config,
                    output_dir=parsed_args.output,
                    requirements_path=parsed_args.requirements
                ),
                # The initial_plan_path for GenerateOverviewPlanCommand will need to be
                # determined after the GenerateInitialPlanCommand is executed.
                # For now, we'll use a placeholder. The execution logic outside of main()
                # will need to handle this dependency.
                GenerateOverviewPlanCommand(
                    config_path=parsed_args.config,
                    output_dir=parsed_args.output,
                    initial_plan_path="<output_of_generate_initial_plan_command>" # Placeholder
                )
            ]
        elif parsed_args.command == "refine":
            commands = [RefineCommand(
                config_path=parsed_args.config,
                input_file=parsed_args.input_file,
                iterations=parsed_args.iterations,
                prompt_file=parsed_args.prompt_file,
                output=parsed_args.output
            )]
        elif parsed_args.command == "run":
            commands = [RunCommand(
                config_path=parsed_args.config,
                plan_file=parsed_args.plan_file,
                state_file=parsed_args.state_file
            )]
        else:
            parser.print_help()
            # This should not be reached due to required=True in subparsers, but as a fallback
            raise ValueError(f"Unknown command: {parsed_args.command}")

        return commands

    except SystemExit as e:
        # Allow SystemExit from argparse to propagate
        raise e
    # Remove all other specific exception catches to allow them to propagate
    # The calling code will handle exceptions and return codes.

# Add entry point to invoke main function
if __name__ == "__main__":
    main()
