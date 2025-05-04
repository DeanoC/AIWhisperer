import argparse
import sys
import logging

# Import necessary components from the application
from .config import load_config
from .processing import read_markdown, format_prompt, process_response, save_yaml
from .openrouter_api import call_openrouter
from .exceptions import AIWhispererError, ConfigError, ProcessingError, APIError
from .utils import setup_logging, setup_rich_output
from rich.console import Console # Import Console for type hinting if needed

# Get a logger for this module
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the AI Whisperer CLI application."""
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

        # Validate required config sections (add more specific checks if needed)
        if 'openrouter' not in config or 'prompts' not in config:
            raise ConfigError("Configuration file must contain 'openrouter' and 'prompts' sections.")
        if 'task_generation' not in config['prompts']:
             raise ConfigError("Configuration file must contain 'task_generation' prompt under 'prompts'.")
        if 'api_key' not in config['openrouter'] or 'model' not in config['openrouter']:
             raise ConfigError("Configuration file must contain 'api_key' and 'model' under 'openrouter'.")

        console.print(f"Reading requirements from: {args.requirements}")
        md_content = read_markdown(args.requirements)
        logger.debug("Markdown requirements read successfully.")

        prompt_template = config['prompts']['task_generation']
        # Pass the openrouter section as config_vars, plus any other top-level vars if needed
        prompt_config_vars = config.get('openrouter', {})
        logger.info("Formatting prompt...")
        formatted_prompt = format_prompt(prompt_template, md_content, prompt_config_vars)
        logger.debug(f"Formatted prompt: {{formatted_prompt[:100]}}...") # Log truncated prompt

        api_key = config['openrouter']['api_key']
        model = config['openrouter']['model']
        api_params = config['openrouter'].get('params', {}) # Get optional params

        console.print(f"Calling OpenRouter API (model: {model})...")
        api_response = call_openrouter(api_key, model, formatted_prompt, api_params)
        logger.info("Received response from API.")
        logger.debug(f"API Response: {{api_response[:100]}}...") # Log truncated response

        console.print("Processing API response...")
        processed_data = process_response(api_response)
        logger.debug("API response processed successfully.")

        console.print(f"Saving generated YAML to: {args.output}")
        save_yaml(processed_data, args.output)
        logger.info(f"Task YAML saved successfully to {args.output}.")

        console.print(f"[green]Successfully generated task YAML: {args.output}[/green]")

    except AIWhispererError as e:
        logger.error(f"Application error: {e}", exc_info=False) # Log error message
        logger.debug(f"Application error details:", exc_info=True) # Log traceback at debug level
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
        console.print(f"[bold red]Unexpected Error:[/bold red] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
