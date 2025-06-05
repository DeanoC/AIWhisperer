"""
Module: ai_whisperer/tools/claude/claude_check_mail_tool.py
Purpose: Claude CLI tool to check mailbox for agent responses

This tool allows Claude CLI to check for responses from agents,
especially important after delegating tasks to Debbie.

Part of the hybrid-hybrid system for agent communication.
"""

from ai_whisperer.tools.check_mail_tool import CheckMailTool

class ClaudeCheckMailTool(CheckMailTool):
    """Claude CLI's tool for checking mailbox messages."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "claude_check_mail"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Check mailbox for messages from AIWhisperer agents (responses to your requests)"
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["claude", "mailbox", "communication", "responses"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for Claude on how to use this tool."""
        return """Use claude_check_mail to check for responses from AIWhisperer agents.

After sending a task to Debbie or another agent via claude_mailbox, use this
to check for their response.

Usage:
- Check all mail: claude_check_mail()
- Check unread only: claude_check_mail(status="unread")
- Check from specific agent: claude_check_mail(from_agent="Debbie")
- Check high priority: claude_check_mail(priority="high")

The tool returns a list of messages with their content, sender, and status.
"""
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to check mail."""
        # Ensure we're checking mail for Claude
        if '_to_agent' not in kwargs:
            kwargs['_to_agent'] = 'Claude'
        
        # Call parent implementation
        return super().execute(**kwargs)