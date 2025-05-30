

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


def cli(args=None):
    """Main entry point for the AI Whisperer CLI application (batch mode only)."""
    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application (batch mode only)",
        prog="ai-whisperer",
    )

    parser.add_argument(
        "script",
        metavar="SCRIPT",
        type=str,
        help="Path to the batch script to execute."
    )
    parser.add_argument(
        "--config",
        metavar="CONFIG",
        type=str,
        required=True,
        help="Path to the configuration YAML file. (Required)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Echo commands only, do not start server or connect."
    )

    if args is not None:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    # Setup logging (no config file required for batch mode)
    logging_custom.setup_logging()
    global logger
    logger = logging_custom.get_logger(__name__)

    script_path = getattr(parsed_args, "script")
    config_path = getattr(parsed_args, "config")
    dry_run = getattr(parsed_args, "dry_run", False)

    # Load config and .env (enforces API key and config validation)
    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(2)

    command = BatchModeCliCommand(script_path=script_path, config=config, dry_run=dry_run)
    exit_code = command.execute()
    sys.exit(exit_code)

