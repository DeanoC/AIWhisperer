import argparse
import sys
import logging
import yaml
import json
from pathlib import Path
import os
import csv

from monitor.user_message_delegate import UserMessageLevel

# Import necessary components from the application
from .config import load_config
from .exceptions import AIWhispererError, ConfigError, OpenRouterAIServiceError, SubtaskGenerationError, SchemaValidationError
from .cli_commands import ListModelsCliCommand, GenerateInitialPlanCliCommand, GenerateOverviewPlanCliCommand, RefineCliCommand, RunCliCommand, BaseCliCommand
from . import logging_custom
from ai_whisperer.path_management import PathManager
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.ai_service.openrouter_ai_service import OpenRouterAIService

logger = None # Will be initialized in main after logging is configured
delegate_manager = None # Will be initialized in main after logging is configured

def user_message_level_type(value: str) -> UserMessageLevel:
    """Custom argparse type function for UserMessageLevel."""
    try:
        return UserMessageLevel[value.upper()]
    except KeyError:
        raise argparse.ArgumentTypeError(
            f"Invalid detail level: {value}. Choose from {list(UserMessageLevel.__members__.keys())}"
        )

def cli(args=None, delegate_manager: DelegateManager = None) -> list[BaseCliCommand]:
    """Main entry point for the AI Whisperer CLI application.
    
    Parses command-line arguments and instantiates the appropriate command object.
    Accepts an optional 'args' parameter for testability (list of CLI args, or None to use sys.argv).
    Accepts an optional 'delegate_manager' instance.
    Returns the instantiated command object.
    """
    # Remove the global delegate_manager declaration
    # global delegate_manager # Removed
    # Logging will be set up after argument parsing to use the config path.
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application for generating task plans and refining requirements.",
        prog="ai-whisperer",
    )

    # Add global arguments to the main parser
    parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Wait for a debugger to attach before running."
    )
    parser.add_argument(
        "--detail-level",
        type=user_message_level_type, # Use the custom type function
        choices=list(UserMessageLevel),
        default=UserMessageLevel.INFO, # Change default to INFO
        help="Set the detail level for output messages (INFO, DETAIL). Defaults to INFO."
    )

    parser.add_argument(
        "--interactive", action="store_true", help="Enable interactive mode."
    )

    # Add path-related global arguments
    # app_path is determined by the application's location and should not be configurable via CLI
    # parser.add_argument( # Removed --app-path CLI argument
    #     "--app-path", type=str, default=None, help="Path to the application directory (overrides config, maps to app_path in PathManager)."
    # )
    parser.add_argument(
        "--project-path", type=str, default=None, help="Path to the project directory (overrides config, maps to project_path in PathManager)."
    )
    parser.add_argument(
        "--output-path", type=str, default=None, help="Path to the output directory (overrides config, maps to output_path in PathManager)."
    )
    parser.add_argument(
        "--workspace-path", type=str, default=None, help="Path to the workspace directory (overrides config, maps to workspace_path in PathManager)."
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Generate Command with Subcommands ---
    generate_parser = subparsers.add_parser("generate", help="Generate plans and projects")
    generate_subparsers = generate_parser.add_subparsers(dest="subcommand", required=True, help="Type of generation")
    
    # Initial Plan Subcommand
    initial_plan_parser = generate_subparsers.add_parser("initial-plan", help="Generate the initial task plan YAML")
    initial_plan_parser.add_argument(
        "requirements_path",
        help="Path to the requirements Markdown file. Required for initial plan generation."
    )
    initial_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # Overview Plan Subcommand
    overview_plan_parser = generate_subparsers.add_parser("overview-plan", help="Generate the overview plan and subtasks from an initial plan")
    overview_plan_parser.add_argument(
        "initial_plan_path",
        help="Path to the initial task plan JSON file.",
    )
    overview_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # Full Plan Subcommand
    full_plan_parser = generate_subparsers.add_parser("full-plan", help="Generate a complete project plan (initial plan, overview, and subtasks)")
    full_plan_parser.add_argument(
        "requirements_path",
        help="Path to the requirements Markdown file.",
    )
    full_plan_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")

    # --- List Models Command ---
    list_models_parser = subparsers.add_parser("list-models", help="List available OpenRouter models")
    list_models_parser.add_argument(
        "--output-csv", type=str, required=False, help="Path to output CSV file for --list-models command."
    )
    list_models_parser.add_argument( # Add detail-level argument to list-models subparser
        "--detail-level",
        type=user_message_level_type,
        choices=list(UserMessageLevel),
        default=UserMessageLevel.INFO,
        help="Set the detail level for output messages (INFO, DETAIL). Defaults to INFO."
    )

    # --- Refine Command ---
    refine_parser = subparsers.add_parser("refine", help="Refine a requirements document using an AI model")
    refine_parser.add_argument("input_file", help="Path to the input requirements document to refine.")
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

    # Use parse_args (let argparse handle errors and exit codes)
    try:
        if args is not None:
            parsed_args = parser.parse_args(args)
        else:
            parsed_args = parser.parse_args()

        # --- Debugger Wait Logic ---
        if getattr(parsed_args, "debug", False):
            try:
                import debugpy
                delegate_manager.invoke_notification(
                    sender=None, # Or a more appropriate sender
                    event_type="user_message_display",
                    event_data={"message": "Waiting for debugger attach on port 5678...", "level": UserMessageLevel.INFO}
                )
                debugpy.listen(("0.0.0.0", 5678))
                debugpy.wait_for_client()
                delegate_manager.invoke_notification(
                    sender=None, # Or a more appropriate sender
                    event_type="user_message_display",
                    event_data={"message": "Debugger attached.", "level": UserMessageLevel.INFO}
                )
            except ImportError:
                delegate_manager.invoke_notification(
                    sender=None, # Or a more appropriate sender
                    event_type="user_message_display",
                    event_data={"message": "debugpy is not installed. Please install it to use --debug.", "level": UserMessageLevel.INFO}
                )
                sys.exit(1)

        # --- Setup Custom Logging ---
        # Load the configuration path from parsed arguments
        config_file_path = getattr(parsed_args, "config", None)
        logging_custom.setup_logging(config_path=config_file_path)

        # Initialize the module-level logger for cli.py after setup
        global logger # Declare intention to modify the module-level logger
        logger = logging_custom.get_logger(__name__)

        if logger: # Check if logger was successfully initialized
            logger.debug("Custom logging initialized and cli.py logger is active.")

        logger.debug("Using parse_args.")
        logger.debug(f"Parsed arguments: {parsed_args}")
        logger.debug(f"Command: {parsed_args.command}")

        # Load configuration, passing parsed_args for PathManager initialization
        config = load_config(str(config_file_path), cli_args=vars(parsed_args))
        if config is None or not isinstance(config, dict) or not config:
            logger.error(f"Configuration failed to load or is empty. Config path: {config_file_path}")
            raise ConfigError(f"Configuration failed to load or is empty. Config path: {config_file_path}")

        config["detail_level"] = parsed_args.detail_level;

        # --- Ensure PathManager is always initialized with the loaded config ---
        try:
            from ai_whisperer.path_management import PathManager
            PathManager.get_instance().initialize(config_values=config, cli_args=vars(parsed_args))
            if logger:
                logger.debug(f"PathManager initialized with config: {config}")
        except Exception as e:
            if logger:
                logger.error(f"Failed to initialize PathManager with config: {e}")


        # --- Instantiate Command Object ---
        # Instantiate the centralized DelegateManager
        commands = [] # Initialize commands list
        if parsed_args.command == "list-models":
            if logger:
                logger.debug("Creating ListModelsCliCommand and passing DelegateManager.")
            commands.append(ListModelsCliCommand(
                config=config, # Pass the loaded config object
                output_csv=parsed_args.output_csv,
                delegate_manager=delegate_manager, # Pass the delegate manager
                detail_level=parsed_args.detail_level # Pass the detail level
            ))
        elif parsed_args.command == "generate":
            if parsed_args.subcommand == "initial-plan":
                if logger:
                    logger.debug("Creating GenerateInitialPlanCliCommand and passing DelegateManager.")
                commands.append(GenerateInitialPlanCliCommand(
                    config=config, # Pass the loaded config object
                    output_dir=parsed_args.output,
                    requirements_path=parsed_args.requirements_path,
                    delegate_manager=delegate_manager # Pass the delegate manager
                ))
            elif parsed_args.subcommand == "overview-plan":
                if logger:
                    logger.debug("Creating GenerateOverviewPlanCliCommand and passing DelegateManager.")
                commands.append(GenerateOverviewPlanCliCommand(
                    config=config, # Pass the loaded config object
                    output_dir=parsed_args.output,
                    initial_plan_path=parsed_args.initial_plan_path,
                    delegate_manager=delegate_manager # Pass the delegate manager
                ))
            elif parsed_args.subcommand == "full-plan":
                if logger:
                    logger.debug("Creating GenerateInitialPlanCliCommand (for full-plan) and passing DelegateManager.")
                commands.append(
                    GenerateInitialPlanCliCommand(
                        config=config, # Pass the loaded config object
                        output_dir=parsed_args.output,
                        requirements_path=parsed_args.requirements_path,
                        delegate_manager=delegate_manager # Pass the delegate manager
                    )
                )
                if logger:
                    logger.debug("Creating GenerateOverviewPlanCliCommand (for full-plan) and passing DelegateManager.")
                commands.append(
                    GenerateOverviewPlanCliCommand(
                        config=config, # Pass the loaded config object
                        output_dir=parsed_args.output,
                        initial_plan_path="<output_of_generate_initial_plan_command>",
                        delegate_manager=delegate_manager # Pass the delegate manager
                    )
                )
            else:
                raise ValueError(f"Unknown subcommand for generate: {parsed_args.subcommand}")
        elif parsed_args.command == "refine":
            if logger:
                logger.debug("Creating RefineCliCommand and passing DelegateManager.")
            commands.append(RefineCliCommand(
                config=config, # Pass the loaded config object
                input_file=parsed_args.input_file,
                iterations=parsed_args.iterations,
                prompt_file=parsed_args.prompt_file,
                output=parsed_args.output,
                delegate_manager=delegate_manager # Pass the delegate manager
            ))
        elif parsed_args.command == "run":
            if logger:
                logger.debug("Creating RunCliCommand and passing DelegateManager.")
            commands.append(RunCliCommand(
                config=config, # Pass the loaded config object
                plan_file=parsed_args.plan_file,
                state_file=parsed_args.state_file,
                delegate_manager=delegate_manager # Pass the delegate manager
            ))
        else:
            parser.print_help()
            raise ValueError(f"Unknown command: {parsed_args.command}")

        # --- Activate Interactive Mode if requested ---
        if getattr(parsed_args, "interactive", False):
            if logger:
                logger.debug("Interactive mode requested. Activating...")
            # Set interactive flag in config so main logic can branch correctly
            config["interactive"] = True
            delegate_manager.invoke_notification(
                sender=None,
                event_type="user_message_display",
                event_data={"message": "Interactive mode activated.", "level": UserMessageLevel.INFO}
            )

        return commands, config

    except SystemExit as e:
        # Allow SystemExit from argparse to propagate
        raise e
    # Remove all other specific exception catches to allow them to propagate
    # The calling code will handle exceptions and return codes.

import io # Import io for capturing stdout

def execute_commands_and_capture_output(commands: list[BaseCliCommand], delegate_manager: DelegateManager) -> str:
    """
    Executes a list of command objects and captures their standard output.

    Args:
        commands: A list of BaseCliCommand objects to execute.
        delegate_manager: The DelegateManager instance to use.

    Returns:
        A string containing the captured standard output.
    """
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    try:
        for command in commands:
            command.execute()
    except Exception as e:
        # Print errors to stderr, which is not captured by StringIO
        print(f"Error during command execution: {e}", file=sys.stderr)
        raise e # Re-raise the exception

    finally:
        sys.stdout = old_stdout

