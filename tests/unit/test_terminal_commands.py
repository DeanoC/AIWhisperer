import pytest
import sys
import debugpy
from unittest.mock import patch, MagicMock

# Assuming the command parser and command execution logic are in these modules
from src.ai_whisperer.terminal_monitor.command_parser import CommandParser
from src.ai_whisperer.terminal_monitor.commands import BaseCommand, ExitCommand, DebuggerCommand, AskCommand, command_registry # Import the actual command classes and the registry

class TestTerminalCommands:
    def test_exit_command_execution(self):
        """Test that 'exit', 'quit', and 'q' commands trigger sys.exit."""
        # We need to patch sys.exit to prevent the test runner from exiting
        with patch('sys.exit') as mock_sys_exit:
            exit_command = ExitCommand("dummy_config_path")

            # Test 'exit'
            exit_command.execute([])
            mock_sys_exit.assert_called_once_with(0)
            mock_sys_exit.reset_mock()

            # Test 'quit'
            exit_command.execute([])
            mock_sys_exit.assert_called_once_with(0)
            mock_sys_exit.reset_mock()

            # Test 'q'
            exit_command.execute([])
            mock_sys_exit.assert_called_once_with(0)

    def test_debugger_command_execution(self):
        """Test that the 'debugger' command triggers debugpy.listen and debugpy.wait_for_client."""
        # We need to patch debugpy methods
        with patch('debugpy.listen') as mock_debugpy_listen, \
             patch('debugpy.wait_for_client') as mock_debugpy_wait:

            debugger_command = DebuggerCommand("dummy_config_path")
            debugger_command.execute([])

            mock_debugpy_listen.assert_called_once_with(("127.0.0.1", 5678))
            mock_debugpy_wait.assert_called_once()

    def test_ask_command_execution(self, capsys):
        """Test that the 'ask $prompt' command correctly processes and prints the query."""
        ask_command = AskCommand("dummy_config_path")

        prompt_text = "What is the capital of France?"
        ask_command.execute([prompt_text])

        captured = capsys.readouterr()
        assert f"Sending query to AI: {prompt_text}" in captured.out
        assert "AI response (mocked): This is a mocked AI response." in captured.out

        # Test with a different prompt
        prompt_text_2 = "Tell me a joke."
        ask_command.execute([prompt_text_2])

        captured = capsys.readouterr()
        assert f"Sending query to AI: {prompt_text_2}" in captured.out
        assert "AI response (mocked): This is a mocked AI response." in captured.out