from abc import ABC, abstractmethod
from typing import Any, Dict
from ai_whisperer.interfaces.cli.commands.args import parse_args

class Command(ABC):
    """
    Abstract base class for all commands.
    """
    name: str = ''
    description: str = ''

    @abstractmethod
    def run(self, args: str, context: Dict[str, Any] = None) -> Any:
        """
        Execute the command with the given arguments and context.
        Args:
            args: The argument string passed to the command (e.g., everything after the command name)
            context: Optional context dict (user/session info, etc.)
        Returns:
            Any: The result of the command (string, dict, etc.)
        """
        pass

    def parse_args(self, argstr: str) -> Dict[str, Any]:
        """
        Helper to parse argument string into positional args and options.
        """
        return parse_args(argstr)
