import pytest
from ai_whisperer.services.agents.session_manager import AgentSession
from ai_whisperer.services.agents.registry import Agent
from pathlib import Path

@pytest.fixture
def registry():
    class DummyRegistry:
        def __init__(self):
            self._agents = {
                "P": Agent(
                    agent_id="P",
                    name="Patricia the Planner",
                    role="planner",
                    description="Creates structured implementation plans",
                    tool_tags=["filesystem", "analysis", "planning"],
                    prompt_file="agent_planner.md",
                    context_sources=["workspace_structure", "existing_schemas", "recent_changes"],
                    color="#4CAF50"
                ),
                "T": Agent(
                    agent_id="T",
                    name="Tessa the Tester",
                    role="tester",
                    description="Generates comprehensive test suites",
                    tool_tags=["filesystem", "testing", "analysis"],
                    prompt_file="agent_tester.md",
                    context_sources=["existing_tests", "code_coverage", "test_patterns"],
                    color="#2196F3"
                )
            }
        def get_agent(self, agent_id):
            return self._agents.get(agent_id.upper())
        def list_agents(self):
            return list(self._agents.values())
    return DummyRegistry()

@pytest.fixture
def engine():
    class DummyEngine:
        workspace_path = Path("/tmp/workspace")
    return DummyEngine()

@pytest.fixture
def session(registry, engine):
    return AgentSession(registry, engine)

def test_handoff_protocol(session):
    session.switch_agent("P")
    handler = session.agent_handlers["P"]
    # Simulate a conversation that triggers handoff
    conversation = [
        {"role": "user", "content": "I want to test this feature."},
        {"role": "agent", "content": "Let me hand you off to Tessa the Tester."}
    ]
    handler.can_handoff = lambda conv: "T"  # Always handoff to T
    next_agent = handler.can_handoff(conversation)
    assert next_agent == "T"
    assert session.switch_agent(next_agent)
    assert session.current_agent.agent_id == "T"

def test_context_transfer_between_agents(session):
    session.switch_agent("P")
    session.conversation_history.append({"role": "user", "content": "Pat context"})
    session.switch_agent("T")
    session.conversation_history.append({"role": "user", "content": "Tessa context"})
    session.switch_agent("P")
    assert any("Pat context" in m["content"] for m in session.conversation_history)
    session.switch_agent("T")
    assert any("Tessa context" in m["content"] for m in session.conversation_history)

def test_agent_recommendation_system(session):
    session.switch_agent("P")
    handler = session.agent_handlers["P"]
    # Simulate recommendation
    handler.recommend_agent = lambda conv: ["T"]
    recs = handler.recommend_agent([{"role": "user", "content": "I want to test this feature."}])
    assert "T" in recs
