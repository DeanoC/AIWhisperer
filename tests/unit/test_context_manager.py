import pytest
# Assuming ContextManager will be in src/ai_whisperer/context_management.py
from ai_whisperer.context_management import ContextManager

# Create a placeholder class for now so tests can run without import errors

def test_context_manager_initialization():
    """Tests that ContextManager is initialized with an empty history."""
    cm = ContextManager()
    assert cm.get_history() == []

def test_add_message():
    """Tests adding a single message to the history."""
    cm = ContextManager()
    message = {"role": "user", "content": "Hello"}
    cm.add_message(message)
    assert cm.get_history() == [message]

def test_add_multiple_messages():
    """Tests adding multiple messages to the history."""
    cm = ContextManager()
    message1 = {"role": "user", "content": "Hello"}
    message2 = {"role": "assistant", "content": "Hi"}
    cm.add_message(message1)
    cm.add_message(message2)
    assert cm.get_history() == [message1, message2]

def test_get_history_with_limit():
    """Tests retrieving a limited number of messages from the history."""
    cm = ContextManager()
    messages = [
        {"role": "user", "content": "Msg 1"},
        {"role": "assistant", "content": "Msg 2"},
        {"role": "user", "content": "Msg 3"},
        {"role": "assistant", "content": "Msg 4"},
    ]
    for msg in messages:
        cm.add_message(msg)

    assert cm.get_history(limit=2) == messages[-2:]
    assert cm.get_history(limit=1) == messages[-1:]
    assert cm.get_history(limit=10) == messages # Limit greater than history size

def test_clear_history():
    """Tests clearing the conversation history."""
    cm = ContextManager()
    message1 = {"role": "user", "content": "Hello"}
    cm.add_message(message1)
    cm.clear_history()
    assert cm.get_history() == []

def test_message_roles():
    """Tests adding messages with different roles."""
    cm = ContextManager()
    system_msg = {"role": "system", "content": "System message"}
    user_msg = {"role": "user", "content": "User message"}
    assistant_msg = {"role": "assistant", "content": "Assistant message"}

    cm.add_message(system_msg)
    cm.add_message(user_msg)
    cm.add_message(assistant_msg)

    history = cm.get_history()
    assert len(history) == 3
    assert history[0]["role"] == "system"
    assert history[1]["role"] == "user"
    assert history[2]["role"] == "assistant"

# Note: These tests are written against a placeholder ContextManager.
# They will need to be run against the actual implementation once it's created
# to verify correctness. The current tests should pass against the placeholder.