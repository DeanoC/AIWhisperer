import argparse
import sys
import logging
from ai_whisperer.interfaces.cli.batch import BatchModeCliCommand
from ai_whisperer.core import logging
from ai_whisperer.core.config import load_config
logger = None

def cli(args=None):
    """Main entry point for the AI Whisperer CLI application."""

    parser = argparse.ArgumentParser(
        description="AI Whisperer CLI application",
        prog="ai-whisperer",
    )
    
    # Global config option (required)
    parser.add_argument(
        "--config",
        metavar="CONFIG",
        type=str,
        required=True,
        help="Path to the configuration YAML file. (Required)"
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Batch mode subcommand
    batch_parser = subparsers.add_parser("batch", help="Run batch mode script")
    batch_parser.add_argument(
        "script",
        metavar="SCRIPT",
        type=str,
        help="Path to the batch script to execute."
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Echo commands only, do not start server or connect."
    )
    
    # Interactive mode subcommand (placeholder)
    interactive_parser = subparsers.add_parser("interactive", help="Start interactive server")
    interactive_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )

    if args is not None:
        parsed_args = parser.parse_args(args)
    else:
        parsed_args = parser.parse_args()

    # If no command is provided, print help and exit
    if not parsed_args.command:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    logging.setup_logging()
    global logger
    logger = logging.get_logger(__name__)

    # Load config and .env (enforces API key and config validation)
    try:
        config = load_config(parsed_args.config)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(2)

    if parsed_args.command == "batch":
        script_path = parsed_args.script
        dry_run = getattr(parsed_args, "dry_run", False)
        command = BatchModeCliCommand(script_path=script_path, config=config, dry_run=dry_run)
        exit_code = command.execute()
        sys.exit(exit_code)
    elif parsed_args.command == "interactive":
        print("Interactive mode not yet implemented")
        print("Use: python -m interactive_server.main --port", parsed_args.port)
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

def main():
    """Standard Python main function entry point."""
    cli()

if __name__ == "__main__":
    main()
