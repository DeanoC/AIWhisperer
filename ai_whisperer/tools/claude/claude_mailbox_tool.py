"""
Module: ai_whisperer/tools/claude/claude_mailbox_tool.py
Purpose: Claude CLI mailbox tool for agent communication

This tool provides Claude CLI with mailbox access to communicate with
AIWhisperer agents (especially Debbie) and delegate complex tasks.

Part of the hybrid-hybrid system that gives Claude minimal direct tools
but full system access through agent delegation.
"""

from ai_whisperer.tools.send_mail_tool import SendMailTool

class ClaudeMailboxTool(SendMailTool):
    """Claude CLI's mailbox tool for agent communication."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "claude_mailbox"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return "Send messages to AIWhisperer agents (especially Debbie) to delegate complex tasks"
    
    @property
    def parameters_schema(self) -> dict:
        """Return the parameters schema."""
        schema = super().parameters_schema
        # Update the description to be Claude-specific
        schema["properties"]["to_agent"]["description"] = "Agent name (e.g., 'Debbie', 'Patricia', 'Alice'). Debbie has full system access."
        return schema
    
    @property
    def tags(self) -> list:
        """Return the tool tags."""
        return ["claude", "mailbox", "communication", "delegation"]
    
    def get_ai_prompt_instructions(self) -> str:
        """Return instructions for Claude on how to use this tool."""
        return """Use claude_mailbox to communicate with AIWhisperer agents, especially Debbie.

Debbie is your primary assistant with full system access. She can:
- Execute any AIWhisperer tool or command
- Debug system issues  
- Run complex workflows
- Access all agent capabilities

Usage:
- For complex AIWhisperer operations: claude_mailbox(to_agent="Debbie", subject="Task Request", body="Please run the test suite...")
- For planning tasks: claude_mailbox(to_agent="Patricia", subject="RFC Review", body="Can you review this RFC...")
- For general help: claude_mailbox(to_agent="Alice", subject="Question", body="How do I...")

The agents will respond via mailbox. Check your mail for responses.
"""
    
    def execute(self, **kwargs) -> dict:
        """Execute the tool to send mail."""
        # Add Claude as the sender
        if '_from_agent' not in kwargs:
            kwargs['_from_agent'] = 'Claude'
        
        # Call parent implementation
        return super().execute(**kwargs)