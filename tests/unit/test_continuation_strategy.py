"""
Test continuation strategy implementation.
"""
import pytest
from ai_whisperer.agents.continuation_strategy import ContinuationStrategy


class TestContinuationStrategy:
    """Test the ContinuationStrategy class."""
    
    def test_init_with_no_config(self):
        """Test initialization with no config."""
        strategy = ContinuationStrategy()
        assert strategy.config == {}
        assert strategy.rules == []
        assert strategy.default_message == "Please continue with the next step."
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = {
            "rules": [
                {
                    "trigger_tools": ["list_rfcs"],
                    "keywords": ["create", "new"],
                    "continuation_message": "Create the RFC now."
                }
            ],
            "default_message": "Custom default message"
        }
        strategy = ContinuationStrategy(config)
        assert len(strategy.rules) == 1
        assert strategy.default_message == "Custom default message"
    
    def test_should_continue_no_tool_calls(self):
        """Test should_continue returns False when no tool calls."""
        strategy = ContinuationStrategy()
        result = {"response": "Just text"}
        assert not strategy.should_continue(result, "create an RFC")
    
    def test_should_continue_with_matching_rule(self):
        """Test should_continue returns True when rule matches."""
        config = {
            "rules": [
                {
                    "trigger_tools": ["list_rfcs"],
                    "keywords": ["create"],
                    "continuation_message": "Create the RFC now."
                }
            ]
        }
        strategy = ContinuationStrategy(config)
        result = {
            "tool_calls": [
                {"function": {"name": "list_rfcs"}}
            ]
        }
        assert strategy.should_continue(result, "create an RFC")
    
    def test_should_continue_no_matching_keyword(self):
        """Test should_continue returns False when keyword doesn't match."""
        config = {
            "rules": [
                {
                    "trigger_tools": ["list_rfcs"],
                    "keywords": ["create"],
                    "continuation_message": "Create the RFC now."
                }
            ]
        }
        strategy = ContinuationStrategy(config)
        result = {
            "tool_calls": [
                {"function": {"name": "list_rfcs"}}
            ]
        }
        assert not strategy.should_continue(result, "show me RFCs")
    
    def test_get_continuation_message_default(self):
        """Test get_continuation_message returns default when no rules match."""
        strategy = ContinuationStrategy()
        msg = strategy.get_continuation_message(["some_tool"], "some message")
        assert msg == "Please continue with the next step."
    
    def test_get_continuation_message_with_rule(self):
        """Test get_continuation_message returns rule-specific message."""
        config = {
            "rules": [
                {
                    "trigger_tools": ["list_rfcs"],
                    "keywords": ["create"],
                    "continuation_message": "Create the RFC now."
                }
            ]
        }
        strategy = ContinuationStrategy(config)
        msg = strategy.get_continuation_message(["list_rfcs"], "create an RFC")
        assert msg == "Create the RFC now."
    
    def test_get_continuation_message_dynamic_test(self):
        """Test dynamic message replacement for test keyword."""
        config = {
            "rules": [
                {
                    "trigger_tools": ["list_rfcs"],
                    "keywords": ["test"],
                    "continuation_message": "Create a {test}."
                }
            ]
        }
        strategy = ContinuationStrategy(config)
        msg = strategy.get_continuation_message(["list_rfcs"], "test RFC creation")
        assert "test RFC with title" in msg
        assert "Test User" in msg