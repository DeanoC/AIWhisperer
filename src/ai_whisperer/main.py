import argparse
import sys
import logging
import yaml
from pathlib import Path
import os # Added for os.path.splitext

# Import necessary components from the application
from .config import load_config
from .orchestrator import Orchestrator
from .subtask_generator import SubtaskGenerator
from .exceptions import (
    AIWhispererError,
    ConfigError,
    OpenRouterAPIError,
    SubtaskGenerationError,
    SchemaValidationError
)
from .utils import setup_logging, setup_rich_output
from .openrouter_api import OpenRouterAPI
from rich.console import Console

# Get a logger for this module
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the AI Whisperer CLI application.

    Parses command-line arguments, loads configuration, initializes components,
    and performs the requested operation (generate task YAML, list models, generate subtask, or full project plan).
    """
    # Setup logging and rich console output first
    setup_logging()
    console = setup_rich_output()


    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application for generating task plans and refining requirements.",
        prog="ai-whisperer"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # --- Task Generation Command ---
    generate_parser = subparsers.add_parser("generate", help="Generate task YAML or full project plan")
    generate_parser.add_argument(
        "--requirements",
        required=True,
        help="Path to the requirements Markdown file. Required for task YAML generation."
    )
    generate_parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration YAML file. Required for most operations."
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Directory for output files."
    )
    generate_parser.add_argument(
        "--generate-subtask",
        action="store_true",
        help="Generate a detailed subtask YAML from a step definition."
    )
    generate_parser.add_argument(
        "--step",
        help="Path to the input step YAML file. Required when using --generate-subtask."
    )
    generate_parser.add_argument(
        "--full-project",
        action="store_true",
        help="Generate a complete project plan with task YAML and all subtasks."
    )

    # --- List Models Command ---
    list_models_parser = subparsers.add_parser("list-models", help="List available OpenRouter models")
    list_models_parser.add_argument(
        "--config",
        required=True, # Config is required to list models
        help="Path to the configuration YAML file."
    )
    list_models_parser.add_argument(
        "--output-csv",
        type=str,
        required=False,
        help="Path to output CSV file for --list-models command."
    )

    # --- Refine Command ---
    refine_parser = subparsers.add_parser("refine", help="Refine a requirements document using an AI model")
    refine_parser.add_argument(
        "input_file",
        help="Path to the input requirements document to refine."
    )
    refine_parser.add_argument(
        "--config",
        required=True, # Config is required for AI interaction
        help="Path to the configuration YAML file."
    )
    refine_parser.add_argument(
        "--prompt-file",
        required=False,
        help="Path to a custom prompt file. If not provided, a default prompt will be used."
    )
    refine_parser.add_argument(
        "--iterations",
        type=int,
        default=1,
        help="Number of refinement iterations to perform."
    )
    refine_parser.add_argument(
        "--output",
        required=False,
        help="Path to output directory or file."
    )

    # Use parse_known_args to avoid conflicts with pytest arguments during testing
    # Check if running under pytest
    if 'pytest' in sys.modules:
        args, unknown = parser.parse_known_args()
        logger.debug("Running under pytest, using parse_known_args.")
    else:
        args = parser.parse_args()
        unknown = [] # No unknown arguments expected when not under pytest
        logger.debug("Not running under pytest, using parse_args.")

    logger.debug(f"Parsed arguments: {args}")
    logger.debug(f"Unknown arguments: {unknown}")
    logger.debug(f"Command: {args.command}")

    # If no command is provided (which shouldn't happen with required=True, but as a safeguard)
    if args.command is None:
        parser.print_help()
        sys.exit(2)

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
            client = OpenRouterAPI(config['openrouter'])
            # Fetch detailed models
            console.print("Fetching available OpenRouter models...")
            detailed_models = client.list_models()

            if args.output_csv:
                # Output to CSV
                csv_filepath = Path(args.output_csv)
                csv_filepath.parent.mkdir(parents=True, exist_ok=True) # Ensure directory exists
                
                import csv # Import csv module here

                with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['id', 'name', 'supported_parameters', 'context_length', 'input_cost', 'output_cost','description', ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for model in detailed_models:
                        # Extract pricing information
                        pricing = model.get('pricing', {})
                        input_cost = pricing.get('prompt', 0) # Default to 0 if not found
                        output_cost = pricing.get('completion', 0) # Default to 0 if not found

                        writer.writerow({
                            'id': model.get('id', ''),
                            'name': model.get('name', ''),
                            'supported_parameters': model.get('supported_parameters', []), # Include supported parameters
                            'context_length': model.get('context_length', ''),
                            'input_cost': input_cost,
                            'output_cost': output_cost,
                            'description': model.get('description', '')
                        })
                console.print(f"[green]Successfully wrote model list to CSV: {csv_filepath}[/green]")
            else:
                # Output to console (backward compatibility)
                console.print("[bold green]Available OpenRouter Models:[/bold green]")
                logger.debug(f"Type of detailed_models: {type(detailed_models)}, Content: {detailed_models}") # Debug log
                for model in detailed_models:
                    if isinstance(model, str):
                        console.print(f"- {model}") # Print string directly if it's a string
                    else:
                        console.print(f"- {model.get('id', 'N/A')}") # Print ID if it's a dictionary
            
            raise SystemExit(0)
            return # Ensure exit in test environments

        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            raise SystemExit(1)
        except OpenRouterAPIError as e:
            print(f"Error fetching models: {e}", file=sys.stderr)
            raise SystemExit(1)
        except Exception as e:
            print(f"An unexpected error occurred while listing models: {e}", file=sys.stderr)
            raise SystemExit(1)

    # --- Handle Subtask Generation ---
    elif getattr(args, 'generate_subtask', False):
        try:
            # Check required arguments
            if not args.config:
                print("Error: --config argument is required when using --generate-subtask.", file=sys.stderr)
                raise SystemExit(1)
            if not args.step:
                print("Error: --step argument is required when using --generate-subtask.", file=sys.stderr)
                raise SystemExit(1)

            # Load configuration
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully for subtask generation.")

            # Load the input step file
            step_path = Path(args.step)
            console.print(f"Loading step definition from: {step_path}")
            
            try:
                with open(step_path, 'r', encoding='utf-8') as f:
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
            console.print(f"Generating detailed subtask from step: {step_data.get('step_id', 'unknown')}")
            output_path = subtask_generator.generate_subtask(step_data)

            # Success
            console.print(f"[green]Successfully generated subtask YAML: {output_path}[/green]")
            sys.exit(0)
            return # Ensure exit in test environments

        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            sys.exit(1)
        except SubtaskGenerationError as e:
            logger.error(f"Subtask generation error: {e}", exc_info=False)
            console.print(f"[bold red]Subtask Generation Error:[/bold red] {e}")
            sys.exit(1)
        except SchemaValidationError as e:
            logger.error(f"Schema validation error: {e}", exc_info=False)
            console.print(f"[bold red]Schema Validation Error:[/bold red] {e}")
            sys.exit(1)
        except Exception as e:
            logger.critical(f"An unexpected error occurred during subtask generation: {e}", exc_info=True)
            console.print(f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details.")
            sys.exit(1)

    # --- Handle Full Project Plan Generation ---
    elif getattr(args, 'full_project', False):
        try:
            # Check for required arguments for full project generation
            if not args.requirements or not args.config:
                print("Error: --requirements and --config are required for full project generation.", file=sys.stderr)
                raise SystemExit(1)

            logger.info("Starting AI Whisperer full project generation...")
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully.")

            # Create the Orchestrator with the right output directory
            orchestrator = Orchestrator(config, args.output)


            # Generate full project plan (main YAML + subtasks)
            result = orchestrator.generate_full_project_plan(args.requirements, args.config)
            logger.info(f"Generated task plan: {result['task_plan']}")
            logger.info(f"Generated {len(result['subtasks'])} subtasks")

            # Report success
            console.print(f"[green]Successfully generated project plan:[/green]")
            console.print(f"- Task plan: {result['task_plan']}")
            if result['task_plan'] != result['overview_plan']:
                console.print(f"- Overview plan: {result['overview_plan']}")

            console.print(f"- Subtasks generated: {len(result['subtasks'])}")
            for i, subtask_path in enumerate(result['subtasks'], 1):
                console.print(f"  {i}. {subtask_path}")
            
            sys.exit(0)
            return # Ensure exit in test environments
        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            raise SystemExit(1)
        except AIWhispererError as e:
            logger.error(f"Application error: {e}", exc_info=False)
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise SystemExit(1)
        except Exception as e:
            logger.critical(f"An unexpected error occurred during project generation: {e}", exc_info=True)
            console.print(f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details.")
            raise SystemExit(1)

    # --- Handle Main Task YAML Generation and Refine Command ---
    # Only proceed to main logic if no special flags were active
    else:
        # Explicitly check if any special flags are active and return if so
        if getattr(args, 'list_models', False) or getattr(args, 'generate_subtask', False) or getattr(args, 'full_project', False):
            return

        try:
            logger.info("Starting AI Whisperer process...")
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully.")

            if args.command == "refine":
                # Handle the refine command
                orchestrator = Orchestrator(config, args.output)
                input_file = args.input_file
                iterations = args.iterations
                for i in range(iterations):
                    console.print(f"[yellow]Refinement iteration {i+1} of {iterations}...[/yellow]")
                    result = orchestrator.refine_requirements(
                        input_filepath_str=input_file,
                    )
                    # Update input_file with the result for the next iteration
                    input_file = result
                    
                console.print(f"[green]Successfully refined requirements: {result}[/green]")
            else:
                # Default: generate command
                orchestrator = Orchestrator(config, args.output)
                console.print(f"Generating initial task plan from: {args.requirements}")
                # Generate only the main task plan YAML
                result = orchestrator.generate_initial_json(args.requirements, args.config)
                logger.info(f"Generated task YAML: {result}")
                # Use the returned path in the success message
                console.print(f"[green]Successfully generated task JSON: {result}[/green]")
        except ConfigError as e:
            logger.error(f"Configuration error: {e}", exc_info=False)
            logger.debug(f"Configuration error details:", exc_info=True)
            console.print(f"[bold red]Configuration Error:[/bold red] {e}")
            raise SystemExit(1)
        except AIWhispererError as e:
            logger.error(f"Application error: {e}", exc_info=False)
            logger.debug(f"Application error details:", exc_info=True)
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise SystemExit(1)
        except Exception as e:
            # Catch any other unexpected errors
            logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
            console.print(f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details.")
            raise SystemExit(1)

if __name__ == "__main__":
    main()