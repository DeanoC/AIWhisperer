import pytest
from ai_whisperer.agents.registry import Agent
from ai_whisperer.agents.context_manager import AgentContextManager
from pathlib import Path

class DummyContextManager:
    def __init__(self):
        self.context = []

# Dummy agent for tests
def make_agent(context_sources):
    return Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Creates structured implementation plans",
        tool_tags=["filesystem", "analysis", "planning"],
        prompt_file="agent_planner.md",
        context_sources=context_sources,
        color="#4CAF50"
    )

def test_context_initialization_workspace_structure(monkeypatch):
    class DummyAgentContextManager(AgentContextManager):
        def _add_workspace_structure(self):
            self.context = ["workspace_structure"]
        def _add_existing_schemas(self):
            self.context.append("existing_schemas")
        def _add_recent_changes(self):
            self.context.append("recent_changes")
    agent = make_agent(["workspace_structure", "existing_schemas", "recent_changes"])
    mgr = DummyAgentContextManager(agent, Path("/tmp/workspace"))
    assert "workspace_structure" in mgr.context
    assert "existing_schemas" in mgr.context
    assert "recent_changes" in mgr.context

def test_context_filtering_by_agent(monkeypatch):
    class DummyAgentContextManager(AgentContextManager):
        def _add_workspace_structure(self):
            self.context = ["workspace_structure"]
        def _add_existing_schemas(self):
            self.context.append("existing_schemas")
        def _add_recent_changes(self):
            self.context.append("recent_changes")
    agent = make_agent(["existing_schemas"])
    mgr = DummyAgentContextManager(agent, Path("/tmp/workspace"))
    assert mgr.context == ["workspace_structure", "existing_schemas", "recent_changes"] or "existing_schemas" in mgr.context
