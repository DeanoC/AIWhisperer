"""
Tool registration for Mailbox system.
Registers mailbox tools that all agents can use for communication.
"""
import logging
from typing import List

from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.send_mail_tool import SendMailTool
from ai_whisperer.tools.check_mail_tool import CheckMailTool
from ai_whisperer.tools.reply_mail_tool import ReplyMailTool
from ai_whisperer.tools.tool_registry import get_tool_registry

logger = logging.getLogger(__name__)


def get_mailbox_tools() -> List[AITool]:
    """Get all mailbox communication tools"""
    return [
        SendMailTool(),
        CheckMailTool(),
        ReplyMailTool()
    ]


def register_mailbox_tools() -> None:
    """Register mailbox tools with the tool registry"""
    tool_registry = get_tool_registry()
    
    for tool in get_mailbox_tools():
        tool_registry.register_tool(tool)
        logger.info(f"Registered mailbox tool: {tool.name}")


def is_mailbox_tool(tool_name: str) -> bool:
    """Check if a tool name is a mailbox tool"""
    mailbox_tool_names = {'send_mail', 'check_mail', 'reply_mail'}
    return tool_name in mailbox_tool_names