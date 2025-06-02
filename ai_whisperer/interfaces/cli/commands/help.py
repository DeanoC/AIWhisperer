from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry
from ai_whisperer.interfaces.cli.commands.errors import CommandError

class HelpCommand(Command):
    name = 'help'
    description = 'Show help for all commands or a specific command.'

    def run(self, args: str, context=None):
        parsed = self.parse_args(args)
        commands = CommandRegistry.all()
        if parsed['args']:
            cmd_name = parsed['args'][0]
            cmd_cls = commands.get(cmd_name)
            if not cmd_cls:
                raise CommandError(f"Unknown command: {cmd_name}")
            desc = getattr(cmd_cls, 'description', '(no description)')
            return f"/{cmd_name}: {desc}"
        else:
            lines = ["Available commands:"]
            for name, cls in sorted(commands.items()):
                desc = getattr(cls, 'description', '(no description)')
                lines.append(f"/{name}: {desc}")
            return '\n'.join(lines)

# Register the command
CommandRegistry.register(HelpCommand)
