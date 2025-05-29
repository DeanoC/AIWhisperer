
import argparse
import sys
import logging
from pathlib import Path
from .exceptions import ConfigError
from .cli_commands import BatchModeCliCommand, BaseCliCommand
from . import logging_custom
from .config import load_config
from ai_whisperer.path_management import PathManager

logger = None

def cli(args=None) -> list[BaseCliCommand]:
    """Main entry point for the AI Whisperer CLI application (batch mode only)."""
    # Remove the global delegate_manager declaration
    # global delegate_manager # Removed
    # Logging will be set up after argument parsing to use the config path.
    # --- Argument Parsing ---

    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application (batch mode only)",
        prog="ai-whisperer",
    )
    parser.add_argument(
        "batch-mode",
        metavar="SCRIPT",
        type=str,
        help="Path to the batch script to execute."
    )

    try:
        if args is not None:
            parsed_args = parser.parse_args(args)
        else:
            parsed_args = parser.parse_args()

        # Setup logging (no config file required for batch mode)
        logging_custom.setup_logging()
        global logger
        logger = logging_custom.get_logger(__name__)

        script_path = getattr(parsed_args, "batch_mode")
        command = BatchModeCliCommand(script_path=script_path)
        return [command], {}

    except SystemExit as e:
        raise e


# Removed execute_commands_and_capture_output and all references to DelegateManager for batch-mode isolation

