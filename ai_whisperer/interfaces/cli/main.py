import argparse
import asyncio
import sys
import logging
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
    
    # Conversation replay subcommand
    replay_parser = subparsers.add_parser(
        "replay", 
        aliases=["conversation", "converse"],
        help="Replay a conversation with AI agents"
    )
    replay_parser.add_argument(
        "conversation_file",
        metavar="CONVERSATION_FILE",
        type=str,
        help="Path to the conversation file (text file with messages)."
    )
    replay_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show messages that would be sent without actually running."
    )
    replay_parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for the entire conversation in seconds (default: 300)"
    )
    replay_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output including server logs"
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

    if parsed_args.command in ["replay", "conversation", "converse"]:
        # Use the conversation replay command
        from ai_whisperer.interfaces.cli.commands.conversation_replay import ConversationReplayCommand
        command = ConversationReplayCommand()
        
        # Build args string from parsed arguments
        args_list = [parsed_args.conversation_file]
        if parsed_args.dry_run:
            args_list.append('--dry-run')
        if hasattr(parsed_args, 'timeout'):
            args_list.extend(['--timeout', str(parsed_args.timeout)])
        if hasattr(parsed_args, 'verbose') and parsed_args.verbose:
            args_list.append('--verbose')
        
        result = command.run(' '.join(args_list))
        print(result)
        sys.exit(0)
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
