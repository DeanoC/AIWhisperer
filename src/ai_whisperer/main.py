import sys
from .cli import main

# Entry point for the application
if __name__ == "__main__":
    # Retrieve the list of command objects from the CLI main function
    commands = main()
    # Execute each command in the list
    for command in commands:
        command.execute()
    # Exit the program with status code 0 (success)
    sys.exit(0)
