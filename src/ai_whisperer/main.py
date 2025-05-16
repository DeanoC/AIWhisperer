import sys
import logging # Import logging
from .cli import cli
from ai_whisperer.ai_service_interaction import OpenRouterAPI

logger = logging.getLogger(__name__) # Get logger instance

# Entry point for the application
if __name__ == "__main__":
    try:
        commands = cli()
        logger.debug("Executing commands...")
        exit_code = 0
        for command in commands:
            # Use the execute() method for all commands
            result = command.execute() if hasattr(command, "execute") else None
            # Treat any result that is False, None, or a dict with 'validation_failed' as failure
            if result is False or result is None:
                exit_code = 1
            elif isinstance(result, dict) and result.get("validation_failed"):
                exit_code = 1
            elif isinstance(result, int) and result != 0:
                exit_code = result
        logger.debug("Command execution finished.")
        logger.debug("Exiting application.")
        sys.exit(exit_code)
    except SystemExit as e:
        raise e
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
