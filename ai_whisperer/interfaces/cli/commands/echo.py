from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry

class EchoCommand(Command):
    name = 'echo'
    description = 'Echoes back the provided arguments.'

    def run(self, args: str, context=None):
        return args or ''

# Register the command
CommandRegistry.register(EchoCommand)
