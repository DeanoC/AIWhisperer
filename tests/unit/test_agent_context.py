import pytest

from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.context.provider import ContextProvider

@pytest.fixture
def agent_context():
    return AgentContext(agent_id="agent-123", system_prompt="You are a helpful assistant.")

def test_inherits_context_provider(agent_context):
    assert isinstance(agent_context, ContextProvider)

def test_store_and_retrieve_messages(agent_context):
    msg1 = {"role": "user", "content": "Hello"}
    msg2 = {"role": "assistant", "content": "Hi there!"}
    agent_context.store_message(msg1)
    agent_context.store_message(msg2)
    messages = agent_context.retrieve_messages()
    assert messages == [msg1, msg2]

def test_filter_messages_by_role(agent_context):
    agent_context.store_message({"role": "user", "content": "A"})
    agent_context.store_message({"role": "assistant", "content": "B"})
    agent_context.store_message({"role": "user", "content": "C"})
    user_msgs = agent_context.get_messages_by_role("user")
    assert user_msgs == [
        {"role": "user", "content": "A"},
        {"role": "user", "content": "C"},
    ]

def test_system_prompt_handling(agent_context):
    assert agent_context.get_system_prompt() == "You are a helpful assistant."
    agent_context.set_system_prompt("New prompt")
    assert agent_context.get_system_prompt() == "New prompt"

def test_conversation_history(agent_context):
    agent_context.store_message({"role": "user", "content": "Q1"})
    agent_context.store_message({"role": "assistant", "content": "A1"})
    agent_context.store_message({"role": "user", "content": "Q2"})
    history = agent_context.get_conversation_history()
    assert history == [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "Q2"},
    ]

def test_metadata_storage_and_retrieval(agent_context):
    agent_context.set_metadata("foo", "bar")
    assert agent_context.get_metadata("foo") == "bar"
    assert agent_context.get_metadata("missing", default=42) == 42

def test_agent_specific_metadata(agent_context):
    agent_context.set_metadata("agent_id", "agent-123")
    agent_context.set_metadata("custom", {"x": 1})
    assert agent_context.get_metadata("agent_id") == "agent-123"
    assert agent_context.get_metadata("custom") == {"x": 1}