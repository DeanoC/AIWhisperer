import pytest
from unittest.mock import MagicMock, patch

# Import the actual classes and the global registry/register function
from src.ai_whisperer.terminal_monitor.command_parser import CommandParser, UnknownCommandError
from src.ai_whisperer.terminal_monitor.commands import BaseCommand, command_registry, register_command

# Define simple concrete command classes for testing the parser
class ExitCommand(BaseCommand):
    name = "exit"
    aliases = ["quit", "q"]
    help_text = "Exits the application."

    def execute(self, args):
        # In the real implementation, this would likely signal the main loop to exit.
        # For testing, we mock sys.exit to prevent the test runner from exiting.
        import sys
        sys.exit(0)

class ListCommand(BaseCommand):
    name = "list"
    aliases = ["ls"]
    help_text = "Lists items."

    def execute(self, args):
        return "Item 1\nItem 2"

# Register the test commands with the global registry
# This might need to be done carefully to avoid interfering with other tests
# that might also register commands. For now, we assume this is acceptable
# in the test environment or that tests are run in isolation.
register_command(ExitCommand)
register_command(ListCommand)

# Fixture for a CommandParser using the global registry
@pytest.fixture
def command_parser():
    return CommandParser(command_registry)

# Tests for command coloring (will require mocking prompt_toolkit or checking output structure)
# These tests are conceptual and will likely need adjustment based on the actual implementation
def test_command_output_with_ansi_coloring(command_parser):
    # Simulate a command that produces ANSI colored output
    class ColoredOutputCommand(BaseCommand):
        name = "colored"
        help_text = "Outputs colored text."

        def execute(self, args):
            # ANSI escape codes for red text
            return "\033[91mThis is red text\033[0m"

    # Temporarily register the colored command
    register_command(ColoredOutputCommand)

    try:
        # Parse and execute the command
        parsed_command = command_parser.parse("colored")
        command_instance = command_registry.get(parsed_command.name)
        result = command_instance.execute(parsed_command.args)

        # Assert that the output contains the ANSI escape codes
        # This test is designed to pass if the raw ANSI codes are present,
        # which is the expected behavior before the coloring is actively processed/rendered.
        assert "\033[91mThis is red text\033[0m" in result

    finally:
        # Unregister the colored command to avoid interfering with other tests
        if "colored" in command_registry:
            del command_registry["colored"]
        # Note: The test commands are registered directly in the dictionary,
        # so no need to access _commands_by_class


def test_error_output_with_ansi_coloring(command_parser):
    # Simulate an error message that might contain ANSI coloring
    # This test assumes that error handling might also involve passing through ANSI codes
    # before they are potentially styled by the terminal.
    class ErrorColoredCommand(BaseCommand):
        name = "error_colored"
        help_text = "Outputs colored error text."

        def execute(self, args):
            # Simulate an error with ANSI colored text
            raise UnknownCommandError("\033[91mThis is a colored error message\033[0m")

    # Temporarily register the error colored command
    register_command(ErrorColoredCommand)

    try:
        # Parse the command
        parsed_command = command_parser.parse("error_colored")
        command_instance = command_registry.get(parsed_command.name)

        # Executing this command should raise the UnknownCommandError
        with pytest.raises(UnknownCommandError) as excinfo:
             command_instance.execute(parsed_command.args)

        # Assert that the exception message contains the ANSI escape codes
        assert "\033[91mThis is a colored error message\033[0m" in str(excinfo.value)

    finally:
        # Unregister the error colored command
        if "error_colored" in command_registry:
            del command_registry["error_colored"]
        # Note: The test commands are registered directly in the dictionary,
        # so no need to access _commands_by_class

def test_command_output_multiple_ansi_codes(command_parser):
    # Simulate output with multiple ANSI codes (e.g., bold and color)
    class MultiColoredCommand(BaseCommand):
        name = "multicolored"
        help_text = "Outputs text with multiple colors/styles."

        def execute(self, args):
            # ANSI escape codes for bold and blue text
            return "\033[1m\033[94mBold Blue Text\033[0m"

    register_command(MultiColoredCommand)

    try:
        parsed_command = command_parser.parse("multicolored")
        command_instance = command_registry.get(parsed_command.name)
        result = command_instance.execute(parsed_command.args)

        assert "\033[1m\033[94mBold Blue Text\033[0m" in result

    finally:
        if "multicolored" in command_registry:
            del command_registry["multicolored"]
        # Note: The test commands are registered directly in the dictionary,
        # so no need to access _commands_by_class

def test_command_output_mixed_text_and_ansi(command_parser):
    # Simulate output with mixed regular text and ANSI colored text
    class MixedOutputCommand(BaseCommand):
        name = "mixed"
        help_text = "Outputs mixed regular and colored text."

        def execute(self, args):
            return "Regular text \033[92mGreen Text\033[0m more regular text."

    register_command(MixedOutputCommand)

    try:
        parsed_command = command_parser.parse("mixed")
        command_instance = command_registry.get(parsed_command.name)
        result = command_instance.execute(parsed_command.args)

        assert "Regular text \033[92mGreen Text\033[0m more regular text." in result

    finally:
        if "mixed" in command_registry:
            del command_registry["mixed"]
        # Note: The test commands are registered directly in the dictionary,
        # so no need to access _commands_by_class

# Tests for help generation
# These tests will parse the command and then execute the returned command object.
def test_help_command_general(command_parser, capsys):
    parsed_command = command_parser.parse("help")
    command_class = command_registry.get(parsed_command.name)
    if command_class is None:
        raise UnknownCommandError(f"Command '{parsed_command.name}' not found.")
    # Instantiate the HelpCommand with mock arguments (only config_path needed for BaseCommand.__init__)
    command_instance = command_class("dummy_config_path")
    command_instance.execute(parsed_command.args)
    captured = capsys.readouterr()
    actual_output_lines = [line.strip() for line in captured.out.strip().splitlines()]

    # Check for the expected commands in the output
    assert "exit: Exits the application." in actual_output_lines
    assert "list: Lists items." in actual_output_lines
    assert "debugger: Activates debug mode, allowing an external debugger to attach." in actual_output_lines
    assert "ask: Sends the provided query string to the configured AI model." in actual_output_lines
    # The help command itself will also be listed
    assert "help: Displays help information about available commands." in actual_output_lines


def test_help_command_specific(command_parser, capsys):
    parsed_command = command_parser.parse("help exit")
    command_class = command_registry.get(parsed_command.name)
    if command_class is None:
        raise UnknownCommandError(f"Command '{parsed_command.name}' not found.")
    # Instantiate the HelpCommand with mock arguments (only config_path needed for BaseCommand.__init__)
    command_instance = command_class("dummy_config_path")
    command_instance.execute(parsed_command.args)
    captured = capsys.readouterr()
    # Check if the expected help text is present in the output
    assert "Exits the application." in captured.out

def test_help_command_alias(command_parser, capsys):
    parsed_command = command_parser.parse("help q")
    command_class = command_registry.get(parsed_command.name)
    if command_class is None:
        raise UnknownCommandError(f"Command '{parsed_command.name}' not found.")
    # Instantiate the HelpCommand with mock arguments (only config_path needed for BaseCommand.__init__)
    command_instance = command_class("dummy_config_path")
    command_instance.execute(parsed_command.args)
    captured = capsys.readouterr()
    # Check if the expected help text is present in the output
    assert "Exits the application." in captured.out

def test_help_command_not_found(command_parser, capsys):
    # Parsing a non-existent command should raise an error before execution
     with pytest.raises(UnknownCommandError, match="Command 'nonexistent' not found."):
         command_parser.parse("nonexistent")


# Tests for shortcut handling
# This will likely involve mocking the input handling part of prompt_toolkit
# and how it maps shortcuts to command strings before parsing.
# For now, we'll test the parser's ability to handle the shortcut string 'q'.
def test_shortcut_q_for_exit(command_parser):
    # The ExitCommand in the real implementation calls sys.exit(0), which will
    # terminate the test runner. We should mock sys.exit to prevent this.
    with patch('sys.exit') as mock_sys_exit:
        parsed_command = command_parser.parse("q")
        command_instance = command_registry.get(parsed_command.name)
        command_instance.execute(parsed_command.args)
        mock_sys_exit.assert_called_once_with(0)

# Tests for alias functionality
def test_alias_ls_for_list(command_parser):
    parsed_command = command_parser.parse("ls")
    command_instance = command_registry.get(parsed_command.name)
    result = command_instance.execute(parsed_command.args)
    assert result == "Item 1\nItem 2"

def test_alias_quit_for_exit(command_parser):
    # Mock sys.exit as in the shortcut test
    with patch('sys.exit') as mock_sys_exit:
        parsed_command = command_parser.parse("quit")
        command_instance = command_registry.get(parsed_command.name)
        command_instance.execute(parsed_command.args)
        mock_sys_exit.assert_called_once_with(0)

def test_unknown_alias(command_parser):
    # Test that an unknown alias is treated as an unknown command
    with pytest.raises(UnknownCommandError, match="Command 'unknownalias' not found."):
        command_parser.parse("unknownalias")
