import argparse
import sys
import logging

# Import necessary components from the application
from .config import load_config
from .processing import read_markdown, format_prompt, process_response, save_yaml
from .openrouter_api import call_openrouter
from .exceptions import AIWhispererError, ConfigError, OpenRouterAPIError, OpenRouterConnectionError
from .utils import setup_logging, setup_rich_output
from rich.console import Console # Import Console for type hinting if needed

# Get a logger for this module
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the AI Whisperer CLI application.

    Parses command-line arguments, loads configuration, reads requirements,
    formats a prompt, calls the OpenRouter API, processes the response,
    and saves the result as a YAML file.
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

        # --- Restore original processing logic ---
        console.print(f"Reading requirements from: {args.requirements}")
        md_content = read_markdown(args.requirements)
        logger.debug("Markdown requirements read successfully.")

        prompt_template = config['prompts']['task_generation']
        # Pass the openrouter section as config_vars, plus any other top-level vars if needed
        prompt_config_vars = config.get('openrouter', {})
        logger.info("Formatting prompt...")
        formatted_prompt = format_prompt(prompt_template, md_content, prompt_config_vars)
        logger.debug(f"Formatted prompt: {formatted_prompt[:100]}...") # Log truncated prompt

        console.print(f"Calling OpenRouter API (model: {config.get('openrouter', {}).get('model', 'N/A')})...")
        try:
            # Use the new call_openrouter function signature
            api_response = call_openrouter(
                prompt_text=formatted_prompt, # Use keyword arg for clarity
                config=config # Pass the whole config dict
            )
            logger.info("Received response from API.")
            logger.debug(f"API Response: {api_response[:100]}...") # Log truncated response

        except (OpenRouterAPIError, OpenRouterConnectionError) as e: # Catch specific OpenRouter errors
            logger.error(f"OpenRouter API call failed: {e}", exc_info=False)
            logger.debug(f"OpenRouter API error details:", exc_info=True)
            console.print(f"[bold red]OpenRouter API Error:[/bold red] {e}")
            sys.exit(1)
        # End API call section

        console.print("Processing API response...")
        processed_data = process_response(api_response)
        logger.debug("API response processed successfully.")

        console.print(f"Saving generated YAML to: {args.output}")
        save_yaml(processed_data, args.output)
        logger.info(f"Task YAML saved successfully to {args.output}.")

        console.print(f"[green]Successfully generated task YAML: {args.output}[/green]")
        # --- End Restore original processing logic ---

    except ConfigError as e: # Keep ConfigError handling separate
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
