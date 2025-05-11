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

    # --- Generate Command with Subcommands ---
    generate_parser = subparsers.add_parser("generate", help="Generate plans and projects")
    generate_subparsers = generate_parser.add_subparsers(dest="subcommand", required=True, help="Type of generation")
    
    # Initial Plan Subcommand
    initial_plan_parser = generate_subparsers.add_parser("initial-plan", help="Generate the initial task plan YAML")
    initial_plan_parser.add_argument(
        "requirements_path", 
        help="Path to the requirements Markdown file. Required for initial plan generation."
    )
    initial_plan_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    initial_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # Overview Plan Subcommand
    overview_plan_parser = generate_subparsers.add_parser("overview-plan", help="Generate the overview plan and subtasks from an initial plan")
    overview_plan_parser.add_argument(
        "initial_plan_path",
        help="Path to the initial task plan JSON file.",
    )
    overview_plan_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    overview_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # Full Plan Subcommand
    full_plan_parser = generate_subparsers.add_parser("full-plan", help="Generate a complete project plan (initial plan, overview, and subtasks)")
    full_plan_parser.add_argument(
        "requirements_path",
        help="Path to the requirements Markdown file.",
    )
    full_plan_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    full_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

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
        elif parsed_args.command == "generate":
            if parsed_args.subcommand == "initial-plan":
                commands = [GenerateInitialPlanCommand(
                    config_path=parsed_args.config,
                    output_dir=parsed_args.output,
                    requirements_path=parsed_args.requirements_path,
                )]
            elif parsed_args.subcommand == "overview-plan":
                commands = [GenerateOverviewPlanCommand(
                    config_path=parsed_args.config,
                    output_dir=parsed_args.output,
                    initial_plan_path=parsed_args.initial_plan_path
                )]
            elif parsed_args.subcommand == "full-plan":
                commands = [
                    GenerateInitialPlanCommand(
                        config_path=parsed_args.config,
                        output_dir=parsed_args.output,
                        requirements_path=parsed_args.requirements_path
                    ),
                    GenerateOverviewPlanCommand(
                        config_path=parsed_args.config,
                        output_dir=parsed_args.output,
                        initial_plan_path="<output_of_generate_initial_plan_command>"
                    )
                ]
            else:
                raise ValueError(f"Unknown subcommand for generate: {parsed_args.subcommand}")
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
