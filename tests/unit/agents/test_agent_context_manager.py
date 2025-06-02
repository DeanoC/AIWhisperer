import pytest
from ai_whisperer.services.agents.registry import Agent
from ai_whisperer.services.agents.context_manager import AgentContextManager
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
    class DummyPrompt:
        @property
        def content(self):
            return "You are Patricia the Planner, an AI assistant specialized in creating structured implementation plans."
    class DummyPromptSystem:
        def get_prompt(self, category, name):
            return DummyPrompt()
    class DummyAgentContextManager(AgentContextManager):
        def _add_workspace_structure(self):
            self.context.append("workspace_structure")
        def _add_existing_schemas(self):
            self.context.append("existing_schemas")
        def _add_recent_changes(self):
            self.context.append("recent_changes")
    agent = make_agent(["workspace_structure", "existing_schemas", "recent_changes"])
    mgr = DummyAgentContextManager(agent, Path("/tmp/workspace"), prompt_system=DummyPromptSystem())
    # The first message should be the system prompt
    assert mgr.context[0]["role"] == "system"
    assert "Patricia the Planner" in mgr.context[0]["content"]
    # The rest of the context should include the sources
    assert "workspace_structure" in mgr.context
    assert "existing_schemas" in mgr.context
    assert "recent_changes" in mgr.context

def test_context_filtering_by_agent(monkeypatch):
    class DummyPrompt:
        @property
        def content(self):
            return "You are Patricia the Planner, an AI assistant specialized in creating structured implementation plans."
    class DummyPromptSystem:
        def get_prompt(self, category, name):
            return DummyPrompt()
    class DummyAgentContextManager(AgentContextManager):
        def _add_workspace_structure(self):
            self.context.append("workspace_structure")
        def _add_existing_schemas(self):
            self.context.append("existing_schemas")
        def _add_recent_changes(self):
            self.context.append("recent_changes")
    agent = make_agent(["existing_schemas"])
    mgr = DummyAgentContextManager(agent, Path("/tmp/workspace"), prompt_system=DummyPromptSystem())
    # The first message should be the system prompt
    assert mgr.context[0]["role"] == "system"
    assert "Patricia the Planner" in mgr.context[0]["content"]
    # The rest of the context should include the sources
    assert "existing_schemas" in mgr.context
