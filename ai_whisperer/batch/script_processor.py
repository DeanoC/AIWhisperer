"""
Script processor for Debbie the Debugger.
Handles loading and parsing of batch scripts with support for comments and blank lines.
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class ScriptFileNotFoundError(Exception):
    """Raised when a script file cannot be found."""
    pass


class ScriptProcessor:
    """Processes batch scripts for execution."""
    
    def __init__(self, script_path: str):
        """
        Initialize with path to script file.
        
        Args:
            script_path: Path to the script file to process
        """
        self.script_path = script_path
        self.commands: List[str] = []
        self.current_index = 0
        self.loaded = False
        
    def load_script(self) -> None:
        """
        Load and parse the script file.
        
        Raises:
            ScriptFileNotFoundError: If script file doesn't exist
            IOError: If file cannot be read
        """
        if not os.path.exists(self.script_path):
            raise ScriptFileNotFoundError(f"Script file not found: {self.script_path}")
            
        logger.info(f"Loading script from: {self.script_path}")
        
        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Process lines, skipping comments and empty lines
            self.commands = []
            for line_num, line in enumerate(lines, 1):
                # Strip whitespace
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    continue
                    
                # Add valid command
                self.commands.append(stripped)
                logger.debug(f"Line {line_num}: Added command '{stripped}'")
                
            self.loaded = True
            self.current_index = 0
            logger.info(f"Loaded {len(self.commands)} commands from script")
            
        except IOError as e:
            logger.error(f"Failed to read script file: {e}")
            raise
            
    def get_next_command(self) -> Optional[str]:
        """
        Get the next command from the script.
        
        Returns:
            The next command string, or None if no more commands
        """
        if not self.loaded:
            raise RuntimeError("Script not loaded. Call load_script() first.")
            
        if self.current_index >= len(self.commands):
            return None
            
        command = self.commands[self.current_index]
        self.current_index += 1
        
        logger.debug(f"Returning command {self.current_index}/{len(self.commands)}: '{command}'")
        return command
        
    def reset(self) -> None:
        """Reset the command pointer to the beginning."""
        self.current_index = 0
        logger.debug("Script processor reset")
        
    def has_more_commands(self) -> bool:
        """Check if there are more commands to process."""
        return self.current_index < len(self.commands)
        
    def get_remaining_count(self) -> int:
        """Get the number of remaining commands."""
        return max(0, len(self.commands) - self.current_index)
        
    def peek_next_command(self) -> Optional[str]:
        """
        Peek at the next command without advancing the pointer.
        
        Returns:
            The next command string, or None if no more commands
        """
        if not self.loaded:
            raise RuntimeError("Script not loaded. Call load_script() first.")
            
        if self.current_index >= len(self.commands):
            return None
            
        return self.commands[self.current_index]