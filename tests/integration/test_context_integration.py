import os
import tempfile
import pytest

from ai_whisperer.context.agent_context import AgentContext
from ai_whisperer.context_management import ContextManager
from ai_whisperer.agents.context_manager import AgentContextManager

def test_context_lifecycle_creation_usage_persistence_recovery():
    ctx = AgentContext(agent_id="agent1", system_prompt="You are a helpful AI.")
    ctx.store_message({"role": "user", "content": "Hello"})
    ctx.set_metadata("foo", "bar")
    ctx.set("session", "abc123")

    # Check storage and retrieval
    assert ctx.agent_id == "agent1"
    assert ctx.get_metadata("foo") == "bar"
    assert ctx.get_system_prompt() == "You are a helpful AI."
    assert ctx.retrieve_messages() == [{"role": "user", "content": "Hello"}]
    assert ctx.get("session") == "abc123"

    # Test persistence and recovery
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        ctx.save_to_file(tmp.name)
        recovered = AgentContext.load_from_file(tmp.name)
        assert recovered.get("session") == "abc123"
        assert recovered._version == ctx._version
        os.unlink(tmp.name)

def test_multi_agent_context_isolation():
    ctx1 = AgentContext(agent_id="agentA")
    ctx2 = AgentContext(agent_id="agentB")
    ctx1.store_message({"role": "user", "content": "A"})
    ctx2.store_message({"role": "user", "content": "B"})
    ctx1.set("shared", "no")
    ctx2.set("shared", "yes")

    assert ctx1.retrieve_messages() == [{"role": "user", "content": "A"}]
    assert ctx2.retrieve_messages() == [{"role": "user", "content": "B"}]
    assert ctx1.get("shared") == "no"
    assert ctx2.get("shared") == "yes"

def test_context_sharing_and_isolation():
    ctx1 = AgentContext(agent_id="agentX")
    ctx2 = AgentContext(agent_id="agentX")
    ctx1.set("foo", "bar")
    ctx2.set("foo", "baz")
    assert ctx1.get("foo") == "bar"
    assert ctx2.get("foo") == "baz"
    # Ensure no accidental sharing
    ctx1.set("unique", "value1")
    assert ctx2.get("unique") is None

def test_error_recovery_on_corrupted_file():
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp:
        tmp.write('{"bad": "data"}')
        tmp_path = tmp.name
    with pytest.raises(RuntimeError):
        AgentContext.load_from_file(tmp_path)
    os.unlink(tmp_path)

def test_contextmanager_compatibility():
    # Legacy ContextManager should work with new context
    mgr = ContextManager()
    mgr.add_message({"role": "user", "content": "legacy"}, agent_id="legacy_agent")
    history = mgr.get_history(agent_id="legacy_agent")
    assert history == [{"role": "user", "content": "legacy"}]
    mgr.clear_history(agent_id="legacy_agent")
    assert mgr.get_history(agent_id="legacy_agent") == []

def test_agentcontextmanager_compatibility():
    # AgentContextManager should initialize and manage agent context
    class DummyAgent:
        prompt_file = "dummy_prompt"
    class DummyPromptSystem:
        pass
    mgr = AgentContextManager(DummyAgent(), ".", DummyPromptSystem())
    ctx = mgr._initialize_agent_context()
    assert ctx is not None

def test_thread_safety_of_agent_context():
    import threading

    ctx = AgentContext(agent_id="threaded")
    def add_messages():
        for i in range(100):
            ctx.store_message({"role": "user", "content": f"msg{i}"})

    threads = [threading.Thread(target=add_messages) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 5 threads x 100 messages = 500 messages
    assert len(ctx.retrieve_messages()) == 500