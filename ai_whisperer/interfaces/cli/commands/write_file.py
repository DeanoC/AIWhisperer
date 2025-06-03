"""
Write File Command

This command provides a direct interface to the write_file tool,
allowing users and agents to write files through the command system.
This supports the agent-first architecture by providing both:
1. Direct command access (/write_file path content)  
2. Tool integration through the existing WriteFileTool

Usage:
    /write_file <path> <content>
    /write_file path/to/file.txt This is the content to write

The command delegates to the WriteFileTool to perform the actual file operation,
ensuring consistent behavior between command and tool usage.
"""

from ai_whisperer.interfaces.cli.commands.base import Command
from ai_whisperer.interfaces.cli.commands.errors import CommandError
from ai_whisperer.interfaces.cli.commands.registry import CommandRegistry
from ai_whisperer.tools.write_file_tool import WriteFileTool
import logging

logger = logging.getLogger(__name__)

class WriteFileCommand(Command):
    name = "write_file"
    description = "Write content to a file using the agent file system tools"
    
    def run(self, args: str, context=None) -> str:
        """
        Execute the write_file command.
        
        Args:
            args: Command arguments in format "path content"
            context: Command execution context (optional)
            
        Returns:
            Success or error message
        """
        if not args.strip():
            raise CommandError("Usage: /write_file <path> <content>")
        
        # Parse arguments - first word is path, rest is content
        parts = args.strip().split(' ', 1)
        if len(parts) < 2:
            raise CommandError("Usage: /write_file <path> <content>")
        
        file_path = parts[0]
        content = parts[1]
        
        logger.info(f"[WriteFileCommand] Writing to file: {file_path}")
        
        try:
            # Use the existing WriteFileTool to perform the operation
            tool = WriteFileTool()
            result = tool.execute(path=file_path, content=content)
            
            if result.get('status') == 'success':
                return f"✅ File written successfully: {result.get('resolved_path', file_path)}"
            else:
                error_msg = result.get('message', 'Unknown error')
                raise CommandError(f"Failed to write file: {error_msg}")
                
        except Exception as e:
            logger.error(f"[WriteFileCommand] Error writing file {file_path}: {e}")
            raise CommandError(f"Error writing file: {str(e)}")

# Register the command
CommandRegistry.register(WriteFileCommand)
