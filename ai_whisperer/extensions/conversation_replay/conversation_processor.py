"""
Conversation processor for AIWhisperer conversation replay mode.
Handles loading and parsing of conversation files (text files with messages).

This is NOT for batch processing! Each line in the conversation file is sent
as a message to the AI agent, simulating an interactive conversation.
"""

import os
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class ConversationFileNotFoundError(Exception):
    """Raised when a conversation file cannot be found."""
    pass


class ConversationProcessor:
    """Processes conversation files for replay."""
    
    def __init__(self, conversation_path: str):
        """
        Initialize with path to conversation file.
        
        Args:
            conversation_path: Path to the conversation file to process
        """
        self.conversation_path = conversation_path
        self.messages: List[str] = []
        self.current_index = 0
        self.loaded = False
        
    def load_conversation(self) -> None:
        """
        Load and parse the conversation file.
        
        Raises:
            ConversationFileNotFoundError: If conversation file doesn't exist
            IOError: If file cannot be read
        """
        if not os.path.exists(self.conversation_path):
            raise ConversationFileNotFoundError(f"Conversation file not found: {self.conversation_path}")
            
        logger.info(f"Loading conversation from: {self.conversation_path}")
        
        try:
            with open(self.conversation_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Process lines, skipping comments and empty lines
            self.messages = []
            for line_num, line in enumerate(lines, 1):
                # Strip whitespace
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    continue
                    
                # Add valid message
                self.messages.append(stripped)
                logger.debug(f"Line {line_num}: Added message '{stripped}'")
                
            self.loaded = True
            self.current_index = 0
            logger.info(f"Loaded {len(self.messages)} messages from conversation")
            
        except IOError as e:
            logger.error(f"Failed to read conversation file: {e}")
            raise
            
    def get_next_message(self) -> Optional[str]:
        """
        Get the next message from the conversation.
        
        Returns:
            The next message string, or None if no more messages
        """
        if not self.loaded:
            raise RuntimeError("Conversation not loaded. Call load_conversation() first.")
            
        if self.current_index >= len(self.messages):
            return None
            
        message = self.messages[self.current_index]
        self.current_index += 1
        
        logger.debug(f"Returning message {self.current_index}/{len(self.messages)}: '{message}'")
        return message
        
    def reset(self) -> None:
        """Reset the message pointer to the beginning."""
        self.current_index = 0
        logger.debug("Conversation processor reset")
        
    def has_more_messages(self) -> bool:
        """Check if there are more messages to process."""
        return self.current_index < len(self.messages)
        
    def get_remaining_count(self) -> int:
        """Get the number of remaining messages."""
        return max(0, len(self.messages) - self.current_index)
        
    def peek_next_message(self) -> Optional[str]:
        """
        Peek at the next message without advancing the pointer.
        
        Returns:
            The next message string, or None if no more messages
        """
        if not self.loaded:
            raise RuntimeError("Conversation not loaded. Call load_conversation() first.")
            
        if self.current_index >= len(self.messages):
            return None
            
        return self.messages[self.current_index]
    
    # Backward compatibility methods (deprecated)
    def load_script(self) -> None:
        """Deprecated: Use load_conversation() instead."""
        logger.warning("load_script() is deprecated. Use load_conversation() instead.")
        return self.load_conversation()
    
    def get_next_command(self) -> Optional[str]:
        """Deprecated: Use get_next_message() instead."""
        logger.warning("get_next_command() is deprecated. Use get_next_message() instead.")
        return self.get_next_message()
    
    def has_more_commands(self) -> bool:
        """Deprecated: Use has_more_messages() instead."""
        return self.has_more_messages()
    
    def peek_next_command(self) -> Optional[str]:
        """Deprecated: Use peek_next_message() instead."""
        return self.peek_next_message()