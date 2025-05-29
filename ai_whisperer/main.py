"""
Main entry point for AI Whisperer CLI.

Note: The CLI mode is being phased out in favor of the interactive web interface.
This is a simplified version without the old monitor/delegate system.
"""
import logging
import sys
from ai_whisperer.cli import cli

logger = logging.getLogger(__name__)

# Entry point for the application
if __name__ == "__main__":
    print("AIWhisperer CLI Mode")
    print("Note: For the best experience, use the interactive web interface:")
    print("  1. Run: python -m interactive_server.main")
    print("  2. In another terminal: cd frontend && npm start")
    print("  3. Open http://localhost:3000\n")
    
    try:
        # Parse CLI arguments and get commands
        commands, config = cli(sys.argv[1:])
        
        # Execute commands
        for command in commands:
            exit_code = command.execute()
            if exit_code != 0:
                sys.exit(exit_code)
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")
        sys.exit(1)