import argparse
import sys
import logging

# Import necessary components from the application
from .config import load_config
from .orchestrator import Orchestrator # Import Orchestrator
from .exceptions import AIWhispererError, ConfigError # Keep relevant exceptions
from .utils import setup_logging, setup_rich_output
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
        required=True,
        help="Path to the requirements Markdown file."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the configuration YAML file."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to save the generated task YAML file."
    )
    # Add optional arguments later if needed (e.g., --verbose, --prompt-name)

    # Use parse_known_args to avoid conflicts with pytest arguments during testing
    args, unknown = parser.parse_known_args()

    try:
        # --- Core Application Logic ---
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
