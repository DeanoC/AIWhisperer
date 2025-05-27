import pytest
from ai_whisperer.agents.registry import Agent, AgentRegistry
from pathlib import Path

PROMPTS_DIR = Path("/tmp/prompts")  # Dummy path for testing

def test_agent_dataclass_creation():
    agent = Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Creates structured implementation plans",
        tool_tags=["filesystem", "analysis", "planning"],
        prompt_file="agent_planner.md",
        context_sources=["workspace_structure", "existing_schemas", "recent_changes"],
        color="#4CAF50"
    )
    assert agent.agent_id == "P"
    assert agent.shortcut == "[P]"
    assert agent.name == "Patricia the Planner"
    assert "planning" in agent.tool_tags
    assert agent.color == "#4CAF50"

def test_agent_registry_loads_default_agents(monkeypatch):
    # Patch _load_default_agents to add a dummy agent
    def dummy_load(self):
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
            )
        }
    monkeypatch.setattr(AgentRegistry, "_load_default_agents", dummy_load)
    registry = AgentRegistry(prompts_dir=PROMPTS_DIR)
    assert registry.get_agent("P") is not None
    assert registry.get_agent("P").name == "Patricia the Planner"
    assert len(registry.list_agents()) == 1

def test_agent_registry_get_agent_invalid_id(monkeypatch):
    monkeypatch.setattr(AgentRegistry, "_load_default_agents", lambda self: None)
    registry = AgentRegistry(prompts_dir=PROMPTS_DIR)
    assert registry.get_agent("X") is None

def test_agent_registry_list_agents(monkeypatch):
    def dummy_load(self):
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
    monkeypatch.setattr(AgentRegistry, "_load_default_agents", dummy_load)
    registry = AgentRegistry(prompts_dir=PROMPTS_DIR)
    agents = registry.list_agents()
    assert len(agents) == 2
    ids = {a.agent_id for a in agents}
    assert "P" in ids and "T" in ids
