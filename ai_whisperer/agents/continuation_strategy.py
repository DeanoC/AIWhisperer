"""
Continuation strategy for agents to define when and how to continue after tool execution.
This allows agents to have custom continuation behavior without hardcoding in the session manager.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ContinuationStrategy:
    """
    Defines continuation behavior for an agent after tool execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize continuation strategy with configuration.
        
        Args:
            config: Configuration dict with 'rules' and optional 'default_message'
        """
        self.config = config or {}
        self.rules = self.config.get('rules', [])
        self.default_message = self.config.get('default_message', 'Please continue with the next step.')
    
    def should_continue(self, result: Dict[str, Any], original_message: str) -> bool:
        """
        Determine if continuation is needed after tool execution.
        
        Args:
            result: The result from agent.process_message with tool_calls
            original_message: The original user message
            
        Returns:
            True if continuation is needed, False otherwise
        """
        # Only continue if we have tool calls
        if not isinstance(result, dict) or not result.get('tool_calls'):
            return False
        
        # Extract tool names
        tool_calls = result.get('tool_calls', [])
        tool_names = [tc.get('function', {}).get('name', '') for tc in tool_calls]
        
        # Check each rule
        for rule in self.rules:
            trigger_tools = rule.get('trigger_tools', [])
            keywords = rule.get('keywords', [])
            
            # Check if any trigger tool was called
            if any(tool in tool_names for tool in trigger_tools):
                # Check if any keyword is in the original message
                message_lower = original_message.lower()
                if any(keyword in message_lower for keyword in keywords):
                    logger.info(f"Continuation triggered by rule: {rule}")
                    return True
        
        return False
    
    def get_continuation_message(self, tool_names: List[str], original_message: str) -> str:
        """
        Get the appropriate continuation message based on context.
        
        Args:
            tool_names: List of tool names that were just executed
            original_message: The original user message
            
        Returns:
            The continuation message to send
        """
        message_lower = original_message.lower()
        
        # Check rules for specific continuation messages
        for rule in self.rules:
            trigger_tools = rule.get('trigger_tools', [])
            keywords = rule.get('keywords', [])
            
            # Check if this rule applies
            if any(tool in tool_names for tool in trigger_tools):
                if any(keyword in message_lower for keyword in keywords):
                    # Use rule's continuation message if provided
                    if 'continuation_message' in rule:
                        # Support dynamic messages based on context
                        msg = rule['continuation_message']
                        if 'test' in message_lower and '{test}' in msg:
                            msg = msg.replace('{test}', 'test RFC with title "Test RFC", author "Test User", and body "This is a test RFC for validating the system"')
                        return msg
        
        return self.default_message