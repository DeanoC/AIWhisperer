from typing import Dict, Type
from ai_whisperer.interfaces.cli.commands.base import Command

class CommandRegistry:
    """
    Registry for all available commands.
    """
    _commands: Dict[str, Type[Command]] = {}

    @classmethod
    def register(cls, command_cls: Type[Command]):
        name = getattr(command_cls, 'name', None)
        if not name:
            raise ValueError('Command class must have a name attribute')
        cls._commands[name] = command_cls

    @classmethod
    def get(cls, name: str) -> Type[Command]:
        return cls._commands.get(name)

    @classmethod
    def all(cls) -> Dict[str, Type[Command]]:
        return dict(cls._commands)
