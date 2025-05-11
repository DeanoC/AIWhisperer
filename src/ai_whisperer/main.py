import argparse
import sys
import logging
import yaml
import json
from pathlib import Path
import os  # Added for os.path.splitext

# Import necessary components from the application
from .config import load_config
from .orchestrator import Orchestrator
from .subtask_generator import SubtaskGenerator
from .plan_parser import ParserPlan  # Import ParserPlan
from .exceptions import AIWhispererError, ConfigError, OpenRouterAPIError, SubtaskGenerationError, SchemaValidationError
from .utils import setup_logging, setup_rich_output
from .ai_service_interaction import OpenRouterAPI
from rich.console import Console

# Get a logger for this module
logger = logging.getLogger(__name__)


def main(args=None):
    """Main entry point for the AI Whisperer CLI application.

    Parses command-line arguments, loads configuration, initializes components,
    and performs the requested operation (generate task YAML, list models, generate subtask, or full project plan).
    Accepts an optional 'args' parameter for testability (list of CLI args, or None to use sys.argv).
    """
    # Setup logging and rich console output first
    setup_logging()
    console = setup_rich_output()

    # TODO - add this as a command line argument
    # Uncomment for debugging
    # import debugpy
    # debugpy.listen(("localhost", 5678))
    # print("Waiting for debugger to attach...")
    # debugpy.wait_for_client()

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

    # --- Task Generation Command ---
    generate_parser = subparsers.add_parser("generate", help="Generate task YAML or full project plan")
    generate_parser.add_argument(
        "--requirements",
        required=False,  # Changed from True to False
        help="Path to the requirements Markdown file. Required for task YAML generation and full project generation.",
    )
    generate_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file. Required for most operations."
    )
    generate_parser.add_argument("--output", type=str, default="output", help="Directory for output files.")
    generate_parser.add_argument(
        "--generate-subtask", action="store_true", help="Generate a detailed subtask YAML from a step definition."
    )
    generate_parser.add_argument(
        "--step", help="Path to the input step YAML file. Required when using --generate-subtask."
    )
    generate_parser.add_argument(
        "--full-project", action="store_true", help="Generate a complete project plan with task YAML and all subtasks."
    )
    # --- List Models Command ---
    list_models_parser = subparsers.add_parser("list-models", help="List available OpenRouter models")
    list_models_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file."  # Config is required to list models
    )
    list_models_parser.add_argument(
        "--output-csv", type=str, required=False, help="Path to output CSV file for --list-models command."
    )

    # --- Refine Command ---
    refine_parser = subparsers.add_parser("refine", help="Refine a requirements document using an AI model")
    refine_parser.add_argument("input_file", help="Path to the input requirements document to refine.")
    refine_parser.add_argument(
        "--config", required=True, help="Path to the configuration YAML file."  # Config is required for AI interaction
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
        help="Path to the configuration YAML file. Required for orchestrator and AI interactions.",
    )

    # Use parse_args (let argparse handle errors and exit codes)
    if args is not None:
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    print("--- After Argument Parsing ---")  # Added print
    logger.debug("Using parse_args.")
    logger.debug(f"Parsed arguments: {args}")
    logger.debug(f"Command: {args.command}")

    # Guard: For test/patching edge cases, ensure required arguments for 'run' are present before command handling
    if args.command == "run":
        # Only check if any required argument is None (should not happen in normal argparse usage)
        if (
            not getattr(args, "plan_file", None)
            or not getattr(args, "state_file", None)
            or not getattr(args, "config", None)
        ):
            print("the following arguments are required: --plan-file, --state-file, --config", file=sys.stderr)
            raise SystemExit(2)

    # Determine project directory
    if args.project_dir:
        project_dir = Path(args.project_dir).resolve()
    else:
        # Fallback to previous logic or default
        project_dir = Path(__file__).parent.parent.parent.resolve()

    print("--- Before Handling Commands ---")  # Added print
    # --- Handle Commands ---
    if args.command == "list-models":
        try:
            # Check if config path is provided
            # Load configuration to get API key
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully for listing models.")

            logger.debug(f"OpenRouterAPI config: {config.get('openrouter')}")
            # Instantiate OpenRouterAPI client
            client = OpenRouterAPI(config["openrouter"])
            # Fetch detailed models
            console.print("Fetching available OpenRouter models...")
            detailed_models = client.list_models()

            if args.output_csv:
                # Output to CSV
                csv_filepath = Path(args.output_csv)
                csv_filepath.parent.mkdir(parents=True, exist_ok=True)

                import csv  # Import csv module here

                with open(csv_filepath, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = [
                        "id",
                        "name",
                        "supported_parameters",
                        "context_length",
                        "input_cost",
                        "output_cost",
                        "description",
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for model in detailed_models:
                        # Extract pricing information
                        pricing = model.get("pricing", {})
                        input_cost = pricing.get("prompt", 0)  # Default to 0 if not found
                        output_cost = pricing.get("completion", 0)  # Default to 0 if not found

                        writer.writerow(
                            {
                                "id": model.get("id", ""),
                                "name": model.get("name", ""),
                                "supported_parameters": model.get(
                                    "supported_parameters", []
                                ),  # Include supported parameters
                                "context_length": model.get("context_length", ""),
                                "input_cost": input_cost,
                                "output_cost": output_cost,
                                "description": model.get("description", ""),
                            }
                        )
                console.print(f"[green]Successfully wrote model list to CSV: {csv_filepath}[/green]")
            else:
                # Output to console (backward compatibility)
                console.print("[bold green]Available OpenRouter Models:[/bold green]")
                logger.debug(
                    f"Type of detailed_models: {type(detailed_models)}, Content: {detailed_models}"
                )  # Debug log
                for model in detailed_models:
                    if isinstance(model, str):
                        console.print(f"- {model}")  # Print string directly if it's a string
                    else:
                        console.print(f"- {model.get('id', 'N/A')}")  # Print ID if it's a dictionary

            raise SystemExit(0)
            return  # Ensure exit in test environments

        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            raise SystemExit(1)
        except OpenRouterAPIError as e:
            print(f"Error fetching models: {e}", file=sys.stderr)
            raise SystemExit(1)
        except Exception as e:
            print(f"An unexpected error occurred while listing models: {e}", file=sys.stderr)
            raise SystemExit(1)

    # --- Handle Generate Command ---
    elif args.command == "generate":
        try:
            # Load configuration
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully.")
            print("--- After Loading Config in Generate Command ---")  # Added print
            print("--- After Loading Config in Generate Command ---")  # Added print

            # Handle Subtask Generation
            if args.generate_subtask:
                # Check required arguments
                if not args.step:
                    # Let argparse handle required argument errors
                    parser.error("the following arguments are required: --step")

                # Load the input step file
                step_path = Path(args.step)
                console.print(f"Loading step definition from: {step_path}")

                try:
                    with open(step_path, "r", encoding="utf-8") as f:
                        step_data = yaml.safe_load(f)
                        if not isinstance(step_data, dict):
                            raise ValueError("Step definition must be a YAML dictionary/object")
                except FileNotFoundError:
                    console.print(f"[bold red]Error:[/bold red] Step file not found: {step_path}")
                    raise SystemExit(1)
                except (yaml.YAMLError, ValueError) as e:
                    console.print(f"[bold red]Error:[/bold red] Invalid step YAML: {e}")
                    raise SystemExit(1)

                # Initialize subtask generator
                console.print("Initializing subtask generator...")
                subtask_generator = SubtaskGenerator(args.config, args.output)
                logger.info("Subtask generator initialized.")

                # Generate subtask
                console.print(f"Generating detailed subtask from step: {step_data.get('subtask_id', 'unknown')}")
                output_path = subtask_generator.generate_subtask(step_data)

                # Success
                console.print(f"[green]Successfully generated subtask YAML: {output_path}[/green]")
                return  # Success, let main() return normally

            # Handle Full Project Plan Generation
            elif args.full_project:
                # Check for required arguments for full project generation
                if not args.requirements:
                    parser.error("the following arguments are required: --requirements")

                logger.info("Starting AI Whisperer full project generation...")
                # config is already loaded above
                logger.debug("Configuration loaded successfully.")

                # Create the Orchestrator with the right output directory
                orchestrator = Orchestrator(config, args.output)
                print("--- Before Calling generate_full_project_plan ---")  # Added print
                # Generate full project plan (main YAML + subtasks)
                result = orchestrator.generate_full_project_plan(args.requirements, args.config)
                print("--- After Calling generate_full_project_plan ---")  # Added print
                logger.info(f"Generated task plan: {result['task_plan']}")
                logger.info(f"Generated {len(result['subtasks'])} subtasks")

                # Report success
                console.print(f"[green]Successfully generated project plan:[/green]")
                console.print(f"- Task plan: {result['task_plan']}")
                if result["task_plan"] != result["overview_plan"]:
                    console.print(f"- Overview plan: {result['overview_plan']}")

                console.print(f"- Subtasks generated: {len(result['subtasks'])}")
                for i, subtask_path in enumerate(result["subtasks"], 1):
                    console.print(f"  {i}. {subtask_path}")

                return  # Success, let main() return normally

            # Default: generate initial task YAML
            else:
                # Check for required arguments
                if not args.requirements:
                    parser.error("the following arguments are required: --requirements")

                orchestrator = Orchestrator(config, args.output)
                console.print(f"Generating initial task plan from: {args.requirements}")
                print("--- Before Calling generate_initial_json ---")  # Added print
                # Generate only the main task plan YAML
                result = orchestrator.generate_initial_json(args.requirements, args.config)
                print("--- After Calling generate_initial_json ---")  # Added print
                logger.info(f"Generated task YAML: {result}")
                # Use the returned path in the success message
                console.print(f"[green]Successfully generated task JSON: {result}[/green]")
                return  # Success, let main() return normally

        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            logger.debug(f"Configuration error details:", exc_info=True)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            raise SystemExit(1)
        except SubtaskGenerationError as e:
            logger.error(f"Subtask generation error: {e}", exc_info=False)
            console.print(f"[bold red]Subtask Generation Error:[/bold red] {e}")
            sys.exit(1)
        except SchemaValidationError as e:
            logger.error(f"Schema validation error: {e}", exc_info=False)
            console.print(f"[bold red]Schema Validation Error:[/bold red] {e}")
            sys.exit(1)
        except AIWhispererError as e:
            logger.error(f"Application error: {e}", exc_info=False)
            logger.debug(f"Application error details:", exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
        except Exception as e:
            # Catch any other unexpected errors
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            console.print(
                f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details."
            )
            sys.exit(1)

    # --- Handle Run Command ---

    elif args.command == "run":
        # Guard: Let argparse handle required arguments, but double-check for None (for test/patching edge cases)
        if (
            not getattr(args, "plan_file", None)
            or not getattr(args, "state_file", None)
            or not getattr(args, "config", None)
        ):
            parser.error("the following arguments are required: --plan-file, --state-file, --config")
        try:
            logger.info("Starting AI Whisperer run process...")
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully.")
            print("--- After Loading Config in Run Command ---")  # Added print
            print("--- After Loading Config in Run Command ---")  # Added print

            # Load the plan overview JSON
            plan_file_path = Path(args.plan_file)
            console.print(f"Loading plan from: {plan_file_path}")
            # Create an OverviewPlanParser instance
            console.print(f"Parsing plan file: {plan_file_path}")
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(str(plan_file_path))
            logger.debug("Plan file parsed and validated successfully.")

            # Create the Orchestrator
            orchestrator = Orchestrator(config, output_dir=".")

            # Run the plan
            print("--- Before Calling run_plan ---")  # Added print
            plan_successful = orchestrator.run_plan(plan_parser=plan_parser, state_file_path=args.state_file)
            print("--- After Calling run_plan ---")  # Added print

            if plan_successful:
                console.print("[green]Plan execution completed successfully.[/green]")
                return 0  # Success, return 0 for testability
            else:
                console.print("[bold red]Plan execution finished with failures.[/bold red]")
                return 1  # Return non-zero status code

        except FileNotFoundError:
            logger.error(f"Plan file not found: {plan_file_path}", exc_info=False)
            console.print(f"[bold red]Error:[/bold red] Plan file not found: {plan_file_path}")
            return 1
        except (SchemaValidationError, FileNotFoundError, json.JSONDecodeError, SchemaValidationError) as e:
            logger.error(f"Plan parsing or validation error: {e}", exc_info=False)
            console.print(f"[bold red]Plan Parsing/Validation Error:[/bold red] {e}")
            return 1
        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            return 1
        except AIWhispererError as e:
            logger.error(f"Application error: {e}", exc_info=False)
            console.print(f"[bold red]Error:[/bold red] {e}")
            return 1
        except Exception as e:
            logger.critical(f"An unexpected error occurred during 'run' command: {e}", exc_info=True)
            console.print(
                f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details."
            )
            return 1

    # --- Handle Refine Command ---
    elif args.command == "refine":
        try:
            logger.info("Starting AI Whisperer process...")
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully.")
            print("--- After Loading Config in Refine Command ---")  # Added print
            print("--- After Loading Config in Refine Command ---")  # Added print

            # Handle the refine command
            orchestrator = Orchestrator(config, args.output)
            input_file = args.input_file
            iterations = args.iterations
            print("--- Before Refinement Loop ---")  # Added print
            for i in range(iterations):
                console.print(f"[yellow]Refinement iteration {i+1} of {iterations}...[/yellow]")
                result = orchestrator.refine_requirements(input_filepath_str=input_file)
                print(f"--- After Refinement Iteration {i+1} ---")  # Added print
                # Update input_file with the result for the next iteration
                input_file = result

            console.print(f"[green]Successfully refined requirements: {result}[/green]")
            return  # Success, let main() return normally
        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            logger.debug(f"Configuration error details:", exc_info=True)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            raise SystemExit(1)
        except AIWhispererError as e:
            logger.error(f"Application error: {e}", exc_info=False)
            logger.debug(f"Application error details:", exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)
        except Exception as e:
            # Catch any other unexpected errors
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            console.print(
                f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details."
            )
            sys.exit(1)

    # --- Handle Unknown Command ---
    else:
        # This else should ideally not be reached if required=True is set for subparsers,
        # but as a fallback or for unexpected scenarios, we can print usage or an error.
        parser.print_help()
        sys.exit(1)  # Exit with error code

    return 0  # Default success exit code


if __name__ == "__main__":
    main()
