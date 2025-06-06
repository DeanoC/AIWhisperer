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
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "send_mail_with_switch"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Send a message to another agent and wait for their response (synchronous communication)"
    
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
        to_agent = kwargs.get('to_agent', '')
        subject = kwargs.get('subject', '')
        body = kwargs.get('body', '')
        
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Starting: from={current_agent}, to={to_agent}, subject='{subject}'")
        logger.debug(f"[SEND_MAIL_WITH_SWITCH] Full kwargs: {kwargs}")
        logger.debug(f"[SEND_MAIL_WITH_SWITCH] Body content: '{body}'")
        
        # First, send the mail normally (get structured result)
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Calling parent send_mail...")
        result_dict = super().execute(**kwargs)
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Parent send_mail result: {result_dict}")
        
        # Check if the mail was sent successfully
        if not result_dict.get("sent", False):
            logger.error(f"[SEND_MAIL_WITH_SWITCH] Mail send failed: {result_dict.get('error')}")
            return result_dict
            
        # Extract message ID from structured result
        message_id = result_dict.get("message_id")
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Mail sent successfully with message_id: {message_id}")
        
        # Check current mailbox state for debugging
        mailbox = get_mailbox()
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Checking mailbox state after send...")
        
        # Check what's in the target agent's mailbox
        target_messages = mailbox.check_mail(to_agent)
        logger.info(f"[SEND_MAIL_WITH_SWITCH] Messages in {to_agent}'s mailbox: {len(target_messages)}")
        for idx, msg in enumerate(target_messages):
            logger.info(f"[SEND_MAIL_WITH_SWITCH] Message {idx}: id={msg.message_id}, from={msg.from_agent}, subject='{msg.subject}'")
            
        # Check if we're sending to another agent (not user)
        if to_agent and self._session_manager and session_id:
            try:
                # Store the original agent
                self._original_agent = current_agent
                
                # Log the synchronous switch
                logger.info(f"[SEND_MAIL_WITH_SWITCH] Initiating synchronous agent switch: {current_agent} -> {to_agent}")
                
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
                
                logger.info(f"[SEND_MAIL_WITH_SWITCH] Agent switch metadata added: {switch_metadata}")
                return result_dict
                
            except Exception as e:
                logger.error(f"[SEND_MAIL_WITH_SWITCH] Failed to prepare agent switch: {e}")
                # Don't fail the mail send, just return the original result
                
        return result_dict