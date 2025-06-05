"""
Test natural language AI-to-AI communication via mailbox.

This test suite verifies that agents can communicate naturally through
the mailbox system without special protocols or tools.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import Mock, patch

from ai_whisperer.extensions.mailbox.mailbox import Mail, MessagePriority, get_mailbox
from ai_whisperer.services.agents.factory import AgentFactory
from ai_whisperer.services.execution.ai_loop import AILoop


class TestNaturalAIToAICommunication:
    """Test natural language communication between AI agents."""
    
    @pytest.fixture
    def mailbox(self):
        """Get a clean mailbox instance."""
        mb = get_mailbox()
        mb.clear_all()
        return mb
    
    def test_claude_sends_natural_request_to_debbie(self, mailbox):
        """Test Claude sending a natural language request to Debbie."""
        # Claude sends a friendly request
        mail = Mail(
            from_agent="Claude",
            to_agent="Debbie",
            subject="Help with workspace analysis",
            body="Hi Debbie! Could you help me understand the structure of this project? "
                 "I'm particularly interested in:\n"
                 "1. The main components and their organization\n"
                 "2. Any recent changes or updates\n"
                 "3. The testing structure\n\n"
                 "Thanks for your help!",
            priority=MessagePriority.NORMAL
        )
        
        message_id = mailbox.send_mail(mail)
        
        # Verify Debbie receives it
        debbie_mail = mailbox.get_mail("Debbie")
        assert len(debbie_mail) == 1
        assert debbie_mail[0].from_agent == "Claude"
        assert "workspace analysis" in debbie_mail[0].subject
        assert "help me understand" in debbie_mail[0].body
        
    def test_debbie_sends_natural_response(self, mailbox):
        """Test Debbie sending a natural language response."""
        # Simulate Debbie's response
        response = Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject="Re: Help with workspace analysis",
            body="Hi Claude! I've analyzed the workspace and here's what I found:\n\n"
                 "**Project Structure:**\n"
                 "- The project is organized into several main components:\n"
                 "  - `ai_whisperer/`: Core application code\n"
                 "  - `interactive_server/`: WebSocket server for UI\n"
                 "  - `tests/`: Comprehensive test suite\n"
                 "  - `prompts/`: Agent prompt definitions\n\n"
                 "**Recent Changes:**\n"
                 "- Added MCP (Model Context Protocol) integration\n"
                 "- Implemented Claude-specific tools for mailbox access\n"
                 "- Enhanced the tool registry with lazy loading\n\n"
                 "**Testing Structure:**\n"
                 "- Unit tests in `tests/unit/`\n"
                 "- Integration tests in `tests/integration/`\n"
                 "- Conversation replay tests for AI interactions\n\n"
                 "Let me know if you need more details on any specific area!",
            priority=MessagePriority.NORMAL
        )
        
        mailbox.send_mail(response)
        
        # Verify Claude receives it
        claude_mail = mailbox.get_mail("Claude")
        assert len(claude_mail) == 1
        assert claude_mail[0].from_agent == "Debbie"
        assert "Project Structure:" in claude_mail[0].body
        
    def test_multi_turn_conversation(self, mailbox):
        """Test a multi-turn conversation between agents."""
        # Turn 1: Claude asks
        mailbox.send_mail(Mail(
            from_agent="Claude",
            to_agent="Debbie",
            subject="Testing question",
            body="Hey Debbie, how many test files do we have in the project?"
        ))
        
        # Turn 2: Debbie responds
        mailbox.send_mail(Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject="Re: Testing question",
            body="I found 87 test files (files matching *test*.py pattern). "
                 "Would you like me to break this down by category?"
        ))
        
        # Turn 3: Claude follows up
        mailbox.send_mail(Mail(
            from_agent="Claude",
            to_agent="Debbie",
            subject="Re: Testing question",
            body="Yes please! Can you show me the breakdown by directory?"
        ))
        
        # Turn 4: Debbie provides details
        mailbox.send_mail(Mail(
            from_agent="Debbie",
            to_agent="Claude",
            subject="Re: Testing question",
            body="Here's the breakdown:\n"
                 "- tests/unit/: 45 files\n"
                 "- tests/integration/: 32 files\n"
                 "- tests/performance/: 10 files\n\n"
                 "The unit tests cover individual components, integration tests "
                 "verify system interactions, and performance tests measure resource usage."
        ))
        
        # Verify conversation flow
        debbie_messages = mailbox.get_mail("Debbie")
        claude_messages = mailbox.get_mail("Claude")
        
        assert len(debbie_messages) == 2  # Claude's questions
        assert len(claude_messages) == 2  # Debbie's responses
        
        # Check conversation threading
        assert all("Testing question" in msg.subject for msg in debbie_messages)
        assert all("Testing question" in msg.subject for msg in claude_messages)
        
    def test_agent_collaboration_request(self, mailbox):
        """Test one agent asking another for collaboration."""
        # Patricia asks Debbie for help
        mail = Mail(
            from_agent="Patricia",
            to_agent="Debbie",
            subject="Need debugging help",
            body="Hi Debbie! I'm working on an RFC for async agents and I'm getting "
                 "some errors when I try to test the mailbox integration. Could you help "
                 "me debug this? The error seems to be related to the context manager."
        )
        
        mailbox.send_mail(mail)
        
        # Debbie offers to help
        response = Mail(
            from_agent="Debbie",
            to_agent="Patricia",
            subject="Re: Need debugging help",
            body="Of course! I'd be happy to help debug the mailbox integration. "
                 "Let me check a few things:\n\n"
                 "1. First, I'll verify the context manager is properly initialized\n"
                 "2. Then I'll trace through the mailbox send/receive flow\n"
                 "3. I'll check for any recent changes that might affect this\n\n"
                 "Can you share the specific error message you're seeing?"
        )
        
        mailbox.send_mail(response)
        
        # Verify collaboration
        debbie_mail = mailbox.get_mail("Debbie")
        patricia_mail = mailbox.get_mail("Patricia")
        
        assert len(debbie_mail) == 1
        assert "RFC for async agents" in debbie_mail[0].body
        
        assert len(patricia_mail) == 1
        assert "help debug the mailbox integration" in patricia_mail[0].body
        
    def test_broadcast_message(self, mailbox):
        """Test sending a message to all agents (empty to_agent)."""
        # Alice sends announcement to all
        announcement = Mail(
            from_agent="Alice",
            to_agent="",  # Empty means all agents
            subject="System maintenance notice",
            body="Hi everyone! Just a heads up that we'll be updating the tool registry "
                 "in about 30 minutes. This might cause brief interruptions. Thanks!"
        )
        
        mailbox.send_mail(announcement)
        
        # Each agent should receive it
        for agent in ["Debbie", "Patricia", "Eamonn", "Claude"]:
            agent_mail = mailbox.get_mail(agent)
            assert any(
                msg.subject == "System maintenance notice" and msg.from_agent == "Alice"
                for msg in agent_mail
            )


class TestMailboxErrorScenarios:
    """Test error handling in mailbox communication."""
    
    @pytest.fixture
    def mailbox(self):
        """Get a clean mailbox instance."""
        mb = get_mailbox()
        mb.clear_all()
        return mb
    
    def test_message_to_nonexistent_agent(self, mailbox):
        """Test sending message to non-existent agent."""
        # This should work - the message goes to the mailbox
        # but the agent might not exist to read it
        mail = Mail(
            from_agent="Claude",
            to_agent="NonExistentAgent",
            subject="Test message",
            body="This agent doesn't exist"
        )
        
        message_id = mailbox.send_mail(mail)
        assert message_id is not None
        
        # Message is in mailbox but no one will read it
        messages = mailbox.get_mail("NonExistentAgent")
        assert len(messages) == 1