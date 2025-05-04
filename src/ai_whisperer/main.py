import argparse
import sys
import logging

# Import necessary components from the application
from .config import load_config
from .orchestrator import Orchestrator # Import Orchestrator
from .exceptions import AIWhispererError, ConfigError, OpenRouterAPIError # Import needed exceptions
from .utils import setup_logging, setup_rich_output
from .openrouter_api import OpenRouterAPI # Import the OpenRouterAPI class
from rich.console import Console

# Get a logger for this module
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the AI Whisperer CLI application.

    Parses command-line arguments, loads configuration, initializes the orchestrator,
    and generates the task YAML file.
    """
    # Setup logging and rich console output first
    setup_logging() # Basic logging setup
    console = setup_rich_output()

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Generate task YAML from requirements using an AI model via OpenRouter.",
        prog="ai-whisperer" # Set the program name for usage messages
    )
    parser.add_argument(
        "--requirements",
        required=False, # Changed to False, will check manually
        help="Path to the requirements Markdown file. Required for main operation."
    )
    parser.add_argument(
        "--config",
        required=False, # Changed to False, will check manually where needed
        help="Path to the configuration YAML file. Required for most operations."
    )
    parser.add_argument(
        "--output",
        required=False, # Changed to False, will check manually
        help="Path to save the generated task YAML file. Required for main operation."
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available OpenRouter models and exit."
    )
    # Add optional arguments later if needed (e.g., --verbose, --prompt-name)

    # Use parse_known_args to avoid conflicts with pytest arguments during testing
    args, unknown = parser.parse_known_args()

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
            client = OpenRouterAPI(config)

            # Fetch and print models
            console.print("Fetching available OpenRouter models...")
            models = client.list_models()
            console.print("[bold green]Available OpenRouter Models:[/bold green]")
            for model in models:
                console.print(f"- {model}")
            sys.exit(0) # Exit after listing models

        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)
        except OpenRouterAPIError as e:
            print(f"Error fetching models: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred while listing models: {e}", file=sys.stderr)
            sys.exit(1)

    # --- Core Application Logic ---
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
            config_path_str=args.config # Corrected argument name
        )

        # Use the returned path in the success message
        console.print(f"[green]Successfully generated task YAML: {generated_yaml_path}[/green]")
        # --- End Orchestrator Logic ---

    except ConfigError as e: # Keep ConfigError handling
        logger.error(f"Configuration error: {e}", exc_info=False)
        logger.debug(f"Configuration error details:", exc_info=True)
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)
    except AIWhispererError as e: # Catch other potential app errors
        logger.error(f"Application error: {e}", exc_info=False)
        logger.debug(f"Application error details:", exc_info=True)
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except SystemExit as e: # Catch SystemExit from argparse
        # Argparse handles printing help/errors, just exit
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
