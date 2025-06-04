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
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the send mail tool with agent switching support."""
        # Get the session context if available
        session_id = kwargs.get('_session_id')
        current_agent = kwargs.get('_agent_name', 'unknown')
        
        # First, send the mail normally (get structured result)
        result_dict = super().execute(**kwargs)
        
        # Check if the mail was sent successfully
        if not result_dict.get("sent", False):
            return result_dict
            
        # Extract message ID from structured result
        message_id = result_dict.get("message_id")
            
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
                
                # Add switch metadata to result
                result_dict.update({
                    'agent_switch_required': True,
                    'agent_switch': switch_metadata,
                    'switch_to_agent': to_agent,
                    'switch_reason': f"Processing mail from {current_agent}"
                })
                
                return result_dict
                
            except Exception as e:
                logger.error(f"Failed to prepare agent switch: {e}")
                # Don't fail the mail send, just return the original result
                
        return result_dict