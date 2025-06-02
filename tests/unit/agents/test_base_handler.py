"""
Unit tests for ai_whisperer.agents.base_handler

Tests for the BaseAgentHandler abstract base class that provides the foundation
for all agent handlers in the system. This is a CRITICAL module for agent
system architecture.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from abc import ABC
from typing import Dict, Any, Optional

from ai_whisperer.services.agents.base import BaseAgentHandler
from ai_whisperer.services.agents.registry import Agent


class ConcreteAgentHandler(BaseAgentHandler):
    """Concrete implementation of BaseAgentHandler for testing."""
    
    def __init__(self, agent: Agent, engine: Any):
        super().__init__(agent, engine)
        self.message_history = []
        self.handoff_agent = None
    
    async def handle_message(self, message: str, conversation_history: list[Dict]) -> Dict[str, Any]:
        """Test implementation of handle_message."""
        self.message_history.append(message)
        return {
            "response": f"Handled: {message}",
            "agent": self.agent.name if self.agent else "unknown",
            "history_count": len(conversation_history)
        }
    
    def can_handoff(self, conversation_history: list[Dict]) -> Optional[str]:
        """Test implementation of can_handoff."""
        return self.handoff_agent


class TestBaseAgentHandlerInit:
    """Test BaseAgentHandler initialization."""
    
    def test_init_with_valid_parameters(self):
        """Test initialization with valid agent and engine."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "test_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        assert handler.agent == mock_agent
        assert handler.engine == mock_engine
        assert handler.context_manager is None
    
    def test_init_with_none_agent(self):
        """Test initialization with None agent."""
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(None, mock_engine)
        
        assert handler.agent is None
        assert handler.engine == mock_engine
        assert handler.context_manager is None
    
    def test_init_with_none_engine(self):
        """Test initialization with None engine."""
        mock_agent = Mock(spec=Agent)
        
        handler = ConcreteAgentHandler(mock_agent, None)
        
        assert handler.agent == mock_agent
        assert handler.engine is None
        assert handler.context_manager is None
    
    def test_init_with_custom_agent_object(self):
        """Test initialization with custom agent object."""
        # Create a custom agent object
        class CustomAgent:
            def __init__(self, name):
                self.name = name
                self.capabilities = ["test"]
        
        custom_agent = CustomAgent("custom_test")
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(custom_agent, mock_engine)
        
        assert handler.agent == custom_agent
        assert handler.agent.name == "custom_test"
        assert handler.engine == mock_engine


class TestBaseAgentHandlerAbstractMethods:
    """Test abstract method enforcement."""
    
    def test_cannot_instantiate_base_class(self):
        """Test that BaseAgentHandler cannot be instantiated directly."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseAgentHandler(mock_agent, mock_engine)
    
    def test_must_implement_handle_message(self):
        """Test that subclasses must implement handle_message."""
        class IncompleteHandler(BaseAgentHandler):
            def can_handoff(self, conversation_history: list[Dict]) -> Optional[str]:
                return None
        
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler(mock_agent, mock_engine)
    
    def test_must_implement_can_handoff(self):
        """Test that subclasses must implement can_handoff."""
        class IncompleteHandler(BaseAgentHandler):
            async def handle_message(self, message: str, conversation_history: list[Dict]) -> Dict[str, Any]:
                return {}
        
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteHandler(mock_agent, mock_engine)
    
    def test_concrete_implementation_works(self):
        """Test that complete concrete implementation works."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        # Should not raise any exception
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        assert isinstance(handler, BaseAgentHandler)


class TestBaseAgentHandlerMessageHandling:
    """Test message handling functionality."""
    
    @pytest.mark.asyncio
    async def test_handle_message_basic(self):
        """Test basic message handling."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "test_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        message = "Hello, test message"
        conversation_history = [{"role": "user", "content": "previous message"}]
        
        result = await handler.handle_message(message, conversation_history)
        
        assert result["response"] == "Handled: Hello, test message"
        assert result["agent"] == "test_agent"
        assert result["history_count"] == 1
        assert message in handler.message_history
    
    @pytest.mark.asyncio
    async def test_handle_message_empty_history(self):
        """Test message handling with empty conversation history."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "test_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        message = "Test message"
        conversation_history = []
        
        result = await handler.handle_message(message, conversation_history)
        
        assert result["response"] == "Handled: Test message"
        assert result["history_count"] == 0
    
    @pytest.mark.asyncio
    async def test_handle_message_multiple_calls(self):
        """Test multiple message handling calls."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "test_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        messages = ["First message", "Second message", "Third message"]
        
        for i, message in enumerate(messages):
            conversation_history = [{"role": "user", "content": f"msg_{j}"} for j in range(i)]
            result = await handler.handle_message(message, conversation_history)
            
            assert result["response"] == f"Handled: {message}"
            assert result["history_count"] == i
        
        assert handler.message_history == messages
    
    @pytest.mark.asyncio
    async def test_handle_message_with_none_agent(self):
        """Test message handling when agent is None."""
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(None, mock_engine)
        
        message = "Test message"
        conversation_history = []
        
        result = await handler.handle_message(message, conversation_history)
        
        assert result["response"] == "Handled: Test message"
        assert result["agent"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_handle_message_with_complex_history(self):
        """Test message handling with complex conversation history."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "complex_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        conversation_history = [
            {"role": "user", "content": "First user message"},
            {"role": "assistant", "content": "First assistant response"},
            {"role": "user", "content": "Second user message"},
            {"role": "system", "content": "System message"},
        ]
        
        message = "Current message"
        
        result = await handler.handle_message(message, conversation_history)
        
        assert result["response"] == "Handled: Current message"
        assert result["history_count"] == 4


class TestBaseAgentHandlerHandoff:
    """Test agent handoff functionality."""
    
    def test_can_handoff_returns_none(self):
        """Test can_handoff when no handoff is needed."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        conversation_history = [{"role": "user", "content": "test"}]
        result = handler.can_handoff(conversation_history)
        
        assert result is None
    
    def test_can_handoff_returns_agent_name(self):
        """Test can_handoff when handoff is needed."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        handler.handoff_agent = "specialized_agent"
        
        conversation_history = [{"role": "user", "content": "test"}]
        result = handler.can_handoff(conversation_history)
        
        assert result == "specialized_agent"
    
    def test_can_handoff_with_empty_history(self):
        """Test can_handoff with empty conversation history."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        result = handler.can_handoff([])
        
        assert result is None
    
    def test_can_handoff_with_different_scenarios(self):
        """Test can_handoff with different conversation scenarios."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test different handoff scenarios
        scenarios = [
            ([], None),
            ([{"role": "user", "content": "simple"}], None),
            ([{"role": "user", "content": "complex task"}], None),
        ]
        
        for history, expected in scenarios:
            result = handler.can_handoff(history)
            assert result == expected


class TestBaseAgentHandlerIntegration:
    """Integration tests for BaseAgentHandler."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow of message handling and handoff checking."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "workflow_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Initial conversation
        conversation_history = []
        
        # Handle first message
        message1 = "Start conversation"
        result1 = await handler.handle_message(message1, conversation_history)
        conversation_history.append({"role": "user", "content": message1})
        conversation_history.append({"role": "assistant", "content": result1["response"]})
        
        # Check handoff after first message
        handoff1 = handler.can_handoff(conversation_history)
        assert handoff1 is None
        
        # Handle second message
        message2 = "Continue conversation"
        result2 = await handler.handle_message(message2, conversation_history)
        
        # Verify results
        assert result1["response"] == "Handled: Start conversation"
        assert result2["response"] == "Handled: Continue conversation"
        assert len(handler.message_history) == 2
    
    def test_handler_state_independence(self):
        """Test that multiple handlers maintain independent state."""
        mock_agent1 = Mock(spec=Agent)
        mock_agent1.name = "agent1"
        mock_agent2 = Mock(spec=Agent)
        mock_agent2.name = "agent2"
        
        mock_engine1 = Mock()
        mock_engine2 = Mock()
        
        handler1 = ConcreteAgentHandler(mock_agent1, mock_engine1)
        handler2 = ConcreteAgentHandler(mock_agent2, mock_engine2)
        
        # Set different handoff states
        handler1.handoff_agent = "handoff1"
        handler2.handoff_agent = "handoff2"
        
        # Verify independence
        assert handler1.agent != handler2.agent
        assert handler1.engine != handler2.engine
        assert handler1.handoff_agent != handler2.handoff_agent
        assert handler1.message_history is not handler2.message_history  # Different objects
    
    @pytest.mark.asyncio
    async def test_error_handling_in_concrete_implementation(self):
        """Test error handling in concrete implementation."""
        class ErrorAgentHandler(BaseAgentHandler):
            async def handle_message(self, message: str, conversation_history: list[Dict]) -> Dict[str, Any]:
                if "error" in message.lower():
                    raise ValueError("Simulated error")
                return {"response": "Success"}
            
            def can_handoff(self, conversation_history: list[Dict]) -> Optional[str]:
                return None
        
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ErrorAgentHandler(mock_agent, mock_engine)
        
        # Test normal operation
        result = await handler.handle_message("normal message", [])
        assert result["response"] == "Success"
        
        # Test error case
        with pytest.raises(ValueError, match="Simulated error"):
            await handler.handle_message("error message", [])


class TestBaseAgentHandlerAttributeAccess:
    """Test attribute access and modification."""
    
    def test_agent_attribute_access(self):
        """Test accessing and modifying agent attribute."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "initial_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test initial access
        assert handler.agent == mock_agent
        assert handler.agent.name == "initial_agent"
        
        # Test modification
        new_agent = Mock(spec=Agent)
        new_agent.name = "new_agent"
        handler.agent = new_agent
        
        assert handler.agent == new_agent
        assert handler.agent.name == "new_agent"
    
    def test_engine_attribute_access(self):
        """Test accessing and modifying engine attribute."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        mock_engine.version = "1.0"
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test initial access
        assert handler.engine == mock_engine
        assert handler.engine.version == "1.0"
        
        # Test modification
        new_engine = Mock()
        new_engine.version = "2.0"
        handler.engine = new_engine
        
        assert handler.engine == new_engine
        assert handler.engine.version == "2.0"
    
    def test_context_manager_attribute(self):
        """Test context_manager attribute behavior."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test initial state
        assert handler.context_manager is None
        
        # Test setting context manager
        mock_context_manager = Mock()
        handler.context_manager = mock_context_manager
        
        assert handler.context_manager == mock_context_manager


class TestBaseAgentHandlerTypeHints:
    """Test type hint compliance and edge cases."""
    
    @pytest.mark.asyncio
    async def test_handle_message_return_type(self):
        """Test that handle_message returns correct type."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "test_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        result = await handler.handle_message("test", [])
        
        assert isinstance(result, dict)
        assert all(isinstance(k, str) for k in result.keys())
    
    def test_can_handoff_return_type(self):
        """Test that can_handoff returns correct type."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test None return
        result_none = handler.can_handoff([])
        assert result_none is None
        
        # Test string return
        handler.handoff_agent = "test_agent"
        result_str = handler.can_handoff([])
        assert isinstance(result_str, str)
    
    def test_conversation_history_type_handling(self):
        """Test handling of different conversation history types."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Test with properly typed history
        valid_history = [
            {"role": "user", "content": "message"},
            {"role": "assistant", "content": "response"}
        ]
        
        result = handler.can_handoff(valid_history)
        assert result is None  # Default implementation
        
        # Test with empty history
        empty_history = []
        result_empty = handler.can_handoff(empty_history)
        assert result_empty is None


class TestBaseAgentHandlerEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_handle_message_with_special_characters(self):
        """Test message handling with special characters."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "special_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        special_messages = [
            "Message with émojis 🚀✨",
            "Message with unicode: Ω≈ç√∫˜µ≤≥÷",
            "Message with newlines\nand\ttabs",
            "",  # Empty message
            "   ",  # Whitespace only
        ]
        
        for message in special_messages:
            result = await handler.handle_message(message, [])
            assert result["response"] == f"Handled: {message}"
    
    def test_can_handoff_with_large_history(self):
        """Test can_handoff with very large conversation history."""
        mock_agent = Mock(spec=Agent)
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Create large conversation history
        large_history = []
        for i in range(1000):
            large_history.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} with some content"
            })
        
        # Should handle large history without issues
        result = handler.can_handoff(large_history)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_concurrent_message_handling(self):
        """Test concurrent message handling."""
        mock_agent = Mock(spec=Agent)
        mock_agent.name = "concurrent_agent"
        mock_engine = Mock()
        
        handler = ConcreteAgentHandler(mock_agent, mock_engine)
        
        # Create multiple concurrent tasks
        async def handle_concurrent_message(msg_id):
            return await handler.handle_message(f"Message {msg_id}", [])
        
        tasks = [handle_concurrent_message(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Verify all messages were handled
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result["response"] == f"Handled: Message {i}"
        
        # Verify all messages were recorded
        assert len(handler.message_history) == 10