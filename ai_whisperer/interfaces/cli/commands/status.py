from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry
import time
from ai_whisperer.version import __version__

_START_TIME = time.time()

class StatusCommand(Command):
    name = 'status'
    description = 'Returns a simple status message.'

    def run(self, args: str, context=None):
        uptime = int(time.time() - _START_TIME)
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        return f"Status: OK\nVersion: {__version__}\nUptime: {uptime_str}"

# Register the command
CommandRegistry.register(StatusCommand)
