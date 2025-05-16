import sys
import logging # Import logging
from .cli import cli
from ai_whisperer.ai_service_interaction import OpenRouterAPI

logger = logging.getLogger(__name__) # Get logger instance

# Entry point for the application
if __name__ == "__main__":
    # Retrieve the list of command objects from the CLI main function
    commands = cli()
    # Execute each command in the list
    logger.debug("Executing commands...")
    for command in commands:
        command.execute()
    logger.debug("Command execution finished.")
    # Exit the program with status code 0 (success)
    logger.debug("Exiting application.")
    sys.exit(0)
