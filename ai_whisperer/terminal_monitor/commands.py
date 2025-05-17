import logging
import sys
import debugpy
from abc import ABC, abstractmethod
from ai_whisperer.delegate_manager import DelegateManager
from user_message_delegate import UserMessageLevel

logger = logging.getLogger(__name__)

class BaseCommand(ABC):
    name: str = ""
    aliases: list[str] = []
    help_text: str = "No help available for this command."
    treat_args_as_single_string: bool = False # New flag for argument parsing

    def __init__(self, config_path: str):
        self.config_path = config_path

    @abstractmethod
    def execute(self, args: list[str]):
        pass

class ExitCommand(BaseCommand):
    name = "exit"
    aliases = ["quit", "q"]
    help_text = "Exits the AIWhisperer monitor application."

    def __init__(self, config_path: str,):
        super().__init__(config_path)

    def execute(self, args: list[str]):

        logger.debug("ExitCommand.execute called") # Keep debug log
        sys.stderr.write("DEBUG: ExitCommand.execute: Reached point before calling monitor_instance.stop()\n") # Added stderr write
        logger.debug("ExitCommand.execute: About to call self.state_manager.stop()") # Keep debug log
        # Signal the monitor to stop gracefully
        self.state_manager.stop()
        logger.debug("ExitCommand.execute: self.state_manager.stop() returned.") # Keep debug log

from ai_whisperer.state_management import StateManager # Import StateManager

class DebuggerCommand(BaseCommand):
    name = "debugger"
    aliases = ["dbg"]
    help_text = "Activates debug mode, allowing an external debugger to attach."

    def __init__(self, config_path: str, state_manager: StateManager):
        super().__init__(config_path)
        self.state_manager = state_manager

    def execute(self, args: list[str]):
        delegate_manager = DelegateManager.get_instance()
        delegate_manager.invoke_notification(
            sender=self,
            event_type="user_message_display",
            event_data={"message": "Debugger active. Waiting for connection...", "level": UserMessageLevel.INFO}
        )
        # This will pause execution until a debugger attaches
        debugpy.listen(("127.0.0.1", 5678)) # Example port, should be configurable
        debugpy.wait_for_client()
        delegate_manager.invoke_notification(
            sender=self,
            event_type="user_message_display",
            event_data={"message": "Debugger attached.", "level": UserMessageLevel.INFO}
        )

class AskCommand(BaseCommand):
    name = "ask"
    aliases = []
    help_text = "Sends the provided query string to the configured AI model."
    treat_args_as_single_string = True # Set the flag for AskCommand

    def __init__(self, config_path: str, state_manager: StateManager):
        super().__init__(config_path)
        self.state_manager = state_manager

    def execute(self, args: list[str]):
        delegate_manager = DelegateManager.get_instance()
        if not args:
            delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={"message": "Error: 'ask' command requires a query string.", "level": UserMessageLevel.INFO}
            )
            return

        query_string = " ".join(args)
        # Removed debug prints for sending query and mocked response
        # print(f"Sending query to AI: {query_string}")
        # print("AI response (mocked): This is a mocked AI response.")
        # In a real scenario, this would call the AI interaction service, potentially using self.state_manager
        # For this subtask, we just removed the prints.
class HelpCommand(BaseCommand):
    name = "help"
    aliases = []
    help_text = "Displays help information about available commands."

    def execute(self, args: list[str]):
        delegate_manager = DelegateManager.get_instance()
        if not args:
            delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={"message": "Available commands:", "level": UserMessageLevel.INFO}
            )
            # Use a set to keep track of seen command instances to avoid duplicates due to aliases
            seen_commands = set()
            for command in command_registry.values():
                if command not in seen_commands:
                    delegate_manager.invoke_notification(
                        sender=self,
                        event_type="user_message_display",
                        event_data={"message": f"  {command.name}: {command.help_text.splitlines()[0]}", "level": UserMessageLevel.DETAIL}
                    )
                    seen_commands.add(command)
            return
        
        command_name = args[0]
        command = command_registry.get(command_name)
        if command:
            delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={"message": command.help_text, "level": UserMessageLevel.INFO}
            )
        else:
            delegate_manager.invoke_notification(
                sender=self,
                event_type="user_message_display",
                event_data={"message": f"Error: Unknown command '{command_name}'. Type 'help' for a list of commands.", "level": UserMessageLevel.INFO}
            )

# Conceptual command registry (actual implementation might be elsewhere)
command_registry = {}

def register_command(command_class):
    # Only instantiate commands that inherit directly from BaseCommand and don't require extra args
    # Commands requiring extra args (like monitor_instance) will be instantiated elsewhere (e.g., in TerminalMonitor)
    if command_class == ExitCommand: # Skip instantiation for ExitCommand here
        command_registry[command_class.name] = command_class # Register the class itself
        for alias in command_class.aliases:
             command_registry[alias] = command_class
    else:
        # This function is now less generic as some commands require more than just config_path
        # Consider refactoring command registration if more complex initializations are needed.
        # For now, we'll handle the simple cases here.
        if command_class == ExitCommand:
            # ExitCommand is instantiated in TerminalMonitor
            command_registry[command_class.name] = command_class # Register the class itself
            for alias in command_class.aliases:
                 command_registry[alias] = command_class
        elif command_class in [DebuggerCommand, AskCommand, HelpCommand]: # Commands requiring config_path and state_manager
             # We cannot instantiate here as state_manager is not available.
             # These commands will be instantiated in TerminalMonitor.
             command_registry[command_class.name] = command_class # Register the class itself
             for alias in command_class.aliases:
                  command_registry[alias] = command_class
        else:
            # Default instantiation for commands only requiring config_path
            instance = command_class("dummy_config_path") # Pass a dummy config path for now
            command_registry[instance.name] = instance
            for alias in instance.aliases:
                command_registry[alias] = instance
        return command_class

# Register the initial commands (registering classes for commands instantiated in TerminalMonitor)
register_command(ExitCommand)
register_command(DebuggerCommand)
register_command(AskCommand)
register_command(HelpCommand)