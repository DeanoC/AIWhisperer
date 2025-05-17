import shlex
from prompt_toolkit.history import InMemoryHistory
from ai_whisperer.exceptions import AIWhispererError # Import base exception

class CommandParser:
    def __init__(self, command_registry):
        self.command_registry = command_registry

    def parse(self, command_string: str):
        """
        Parses a command string into a command name and a list of arguments.
        """
        if not command_string or command_string.strip() == "":
            raise ValueError("Command string cannot be empty or contain only spaces.")

        # Use shlex to handle splitting while respecting quotes
        lexer = shlex.shlex(command_string, posix=True)
        lexer.whitespace_split = True
        lexer.quotes = '"'
        lexer.escape = '' # Disable escape character handling for simplicity initially

        parts = list(lexer)

        if not parts:
            raise ValueError("Command string cannot be empty after parsing.")

        command_name = parts[0]
        args = parts[1:]
        command_instance = self.command_registry.get(command_name)
        # Check if the command exists in the registry and requires special argument parsing
        command_instance = self.command_registry.get(command_name)
        if command_instance is None:
            raise UnknownCommandError(f"Command '{command_name}' not found.")
        
        # Check if the command has a special flag for treating arguments as a single string
        if command_instance and getattr(command_instance, 'treat_args_as_single_string', False):
            # For commands that treat arguments as a single string,
            # find the rest of the string after the command name
            first_space_index = command_string.find(' ')
            if first_space_index != -1:
                # Extract the rest of the string as the single argument
                single_arg = command_string[first_space_index:].strip()
                args = [single_arg] if single_arg else []
            else:
                args = [] # No argument provided after the command
        else:
            # For other commands or if command not found, use shlex parsing for arguments
            args = parts[1:]

        parsed_command = ParsedCommand(command_name, args)
        return parsed_command   

class CommandParsingError(AIWhispererError):
    """Exception raised for errors during command parsing."""
    pass

class UnknownCommandError(AIWhispererError):
    """Exception raised when a command is not found in the registry."""
    pass

class ParsedCommand:
    def __init__(self, name: str, args: list[str]):
        self.name = name
        self.args = args

class CommandHistory(InMemoryHistory):
    """
    Command history using prompt_toolkit's InMemoryHistory.
    Can be extended later for persistent history.
    """
    pass