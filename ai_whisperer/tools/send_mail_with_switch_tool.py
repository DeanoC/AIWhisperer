"""
Module: ai_whisperer/tools/send_mail_with_switch_tool.py
Purpose: Enhanced send mail tool that supports synchronous agent switching

This module extends the base send_mail tool to support synchronous agent switching
when sending messages to other agents.
"""

import json
import logging
from typing import Optional, Dict, Any
from ai_whisperer.tools.send_mail_tool import SendMailTool
from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox

logger = logging.getLogger(__name__)

class SendMailWithSwitchTool(SendMailTool):
    """Enhanced send mail tool that triggers agent switching for synchronous communication."""
    
    def __init__(self):
        super().__init__()
        self._session_manager = None
        self._original_agent = None
        
    def set_session_manager(self, session_manager):
        """Set the session manager for agent switching."""
        self._session_manager = session_manager
        
    def execute(self, **kwargs) -> str:
        """Execute the send mail tool with agent switching support."""
        # Get the session context if available
        session_id = kwargs.get('_session_id')
        current_agent = kwargs.get('_agent_name', 'unknown')
        
        # First, send the mail normally
        result_str = super().execute(**kwargs)
        
        # Check if the mail was sent successfully
        if "Error" in result_str:
            return result_str
            
        # Extract message ID from result string if present
        message_id = None
        if "ID:" in result_str:
            try:
                # Extract ID from format "... (ID: xxx). ..."
                id_start = result_str.find("ID:") + 3
                id_end = result_str.find(")", id_start)
                message_id = result_str[id_start:id_end].strip()
            except:
                pass
            
        # Check if we're sending to another agent (not user)
        to_agent = kwargs.get('to_agent', '')
        if to_agent and self._session_manager and session_id:
            try:
                # Store the original agent
                self._original_agent = current_agent
                
                # Log the synchronous switch
                logger.info(f"Initiating synchronous agent switch: {current_agent} -> {to_agent}")
                
                # Create a result that includes switch metadata
                switch_metadata = {
                    'switch_type': 'synchronous_mail',
                    'from_agent': current_agent,
                    'to_agent': to_agent,
                    'message_id': message_id,
                    'return_to': current_agent
                }
                
                # Return enhanced result as JSON string with switch instruction
                enhanced_result = {
                    'message': result_str,
                    'success': True,
                    'message_id': message_id,
                    'agent_switch': switch_metadata,
                    'switch_to_agent': to_agent,
                    'switch_reason': f"Processing mail from {current_agent}"
                }
                
                # Return as formatted string that includes switch info
                return f"{result_str}\n[Agent switch required: {current_agent} -> {to_agent}]"
                
            except Exception as e:
                logger.error(f"Failed to prepare agent switch: {e}")
                # Don't fail the mail send, just return the original result
                
        return result_str