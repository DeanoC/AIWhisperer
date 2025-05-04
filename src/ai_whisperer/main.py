import argparse
import sys
import logging
import yaml
from pathlib import Path

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
    and performs the requested operation (generate task YAML, list models, or generate subtask).
    """
    # Setup logging and rich console output first
    setup_logging()
    console = setup_rich_output()

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Generate task YAML from requirements using an AI model via OpenRouter.",
        prog="ai-whisperer"
    )
    parser.add_argument(
        "--requirements",
        required=False,
        help="Path to the requirements Markdown file. Required for task YAML generation."
    )
    parser.add_argument(
        "--config",
        required=False,
        help="Path to the configuration YAML file. Required for most operations."
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Path to save the generated task YAML file. Required for task YAML generation."
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available OpenRouter models and exit."
    )
    parser.add_argument(
        "--generate-subtask",
        action="store_true",
        help="Generate a detailed subtask YAML from a step definition."
    )
    parser.add_argument(
        "--step",
        help="Path to the input step YAML file. Required when using --generate-subtask."
    )
    
    # Use parse_known_args to avoid conflicts with pytest arguments during testing
    args, unknown = parser.parse_known_args()

    # --- Handle OpenRouter Models Listing ---
    if args.list_models:
        try:
            # Check if config path is provided
            if not args.config:
                print("Error: --config argument is required when using --list-models.", file=sys.stderr)
                sys.exit(1)

            # Load configuration to get API key
            console.print(f"Loading configuration from: {args.config}")
            config = load_config(args.config)
            logger.debug("Configuration loaded successfully for listing models.")

            # Instantiate OpenRouterAPI client
            client = OpenRouterAPI(config['openrouter'])

            # Fetch and print models
            console.print("Fetching available OpenRouter models...")
            models = client.list_models()
            console.print("[bold green]Available OpenRouter Models:[/bold green]")
            for model in models:
                console.print(f"- {model}")
            sys.exit(0)

        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)
        except OpenRouterAPIError as e:
            print(f"Error fetching models: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while listing models: {e}", file=sys.stderr)
            sys.exit(1)

    # --- Handle Subtask Generation ---
    if args.generate_subtask:
        try:
            # Check required arguments
            if not args.config:
                print("Error: --config argument is required when using --generate-subtask.", file=sys.stderr)
                sys.exit(1)
            if not args.step:
                print("Error: --step argument is required when using --generate-subtask.", file=sys.stderr)
                sys.exit(1)

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
                sys.exit(1)
            except (yaml.YAMLError, ValueError) as e:
                console.print(f"[bold red]Error:[/bold red] Invalid step YAML: {e}")
                sys.exit(1)

            # Initialize subtask generator
            console.print("Initializing subtask generator...")
            subtask_generator = SubtaskGenerator(args.config)
            logger.info("Subtask generator initialized.")

            # Generate subtask
            console.print(f"Generating detailed subtask from step: {step_data.get('step_id', 'unknown')}")
            output_path = subtask_generator.generate_subtask(step_data)

            # Success
            console.print(f"[green]Successfully generated subtask YAML: {output_path}[/green]")
            sys.exit(0)

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

    # --- Handle Main Task YAML Generation ---
    try:
        # Check for required arguments for core logic
        if not args.requirements or not args.config or not args.output:
             parser.print_usage(file=sys.stderr)
             print("Error: --requirements, --config, and --output are required for the main operation.", file=sys.stderr)
             sys.exit(1)

        logger.info("Starting AI Whisperer process...")
        console.print(f"Loading configuration from: {args.config}")
        config = load_config(args.config)
        logger.debug("Configuration loaded successfully.")

        # --- Use Orchestrator ---
        console.print("Initializing orchestrator...")
        orchestrator = Orchestrator(config)
        logger.info("Orchestrator initialized.")

        console.print(f"Generating initial task plan from: {args.requirements}")
        # Call the orchestrator method with corrected argument names
        generated_yaml_path = orchestrator.generate_initial_yaml(
            requirements_md_path_str=args.requirements,
            config_path_str=args.config
        )

        # Use the returned path in the success message
        console.print(f"[green]Successfully generated task YAML: {generated_yaml_path}[/green]")
        # --- End Orchestrator Logic ---

    except ConfigError as e:
        logger.error(f"Configuration error: {e}", exc_info=False)
        logger.debug(f"Configuration error details:", exc_info=True)
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)
    except AIWhispererError as e:
        logger.error(f"Application error: {e}", exc_info=False)
        logger.debug(f"Application error details:", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except SystemExit as e:
        # Catch SystemExit from argparse
        # Re-raise if needed for testing frameworks to catch it
        if "pytest" in sys.modules:
             raise e
        else:
             sys.exit(e.code) # Ensure correct exit code
    except Exception as e:
        # Catch any other unexpected errors
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        console.print(f"[bold red]Unexpected Error:[/bold red] An unexpected error occurred. Please check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()