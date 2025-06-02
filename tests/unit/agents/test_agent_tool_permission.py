import pytest
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.services.agents.registry import Agent

def get_tools_for_agent(agent: Agent, registry: ToolRegistry):
    # If allow_tools is set, only those tools are allowed
    if hasattr(agent, 'allow_tools') and agent.allow_tools:
        return [t for t in registry.get_all_tools() if t.name in agent.allow_tools]
    # Default: tag filtering, then apply deny_tools if present
    tools = registry.get_filtered_tools({"tags": agent.tool_tags})
    if hasattr(agent, 'deny_tools') and agent.deny_tools:
        tools = [t for t in tools if t.name not in agent.deny_tools]
    return tools

class DummyToolA(AITool):
    @property
    def name(self):
        return "tool_a"
    @property
    def description(self):
        return "Tool A"
    @property
    def parameters_schema(self):
        return {}
    @property
    def tags(self):
        return ["filesystem", "analysis"]
    def get_ai_prompt_instructions(self):
        return "Use tool_a for filesystem or analysis."
    def execute(self, **kwargs):
        return "A"

class DummyToolB(AITool):
    @property
    def name(self):
        return "tool_b"
    @property
    def description(self):
        return "Tool B"
    @property
    def parameters_schema(self):
        return {}
    @property
    def tags(self):
        return ["testing"]
    def get_ai_prompt_instructions(self):
        return "Use tool_b for testing."
    def execute(self, **kwargs):
        return "B"

def test_agent_tool_permission_allow():
    registry = ToolRegistry()
    registry.reset_tools()
    tool_a = DummyToolA()
    tool_b = DummyToolB()
    registry.register_tool(tool_a)
    registry.register_tool(tool_b)
    agent = Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Planner agent",
        tool_tags=["filesystem", "analysis"],
        prompt_file="planner.md",
        context_sources=[],
        color="#4CAF50"
    )
    agent.allow_tools = ["tool_b"]
    tools = get_tools_for_agent(agent, registry)
    assert tool_b in tools
    assert tool_a not in tools

def test_agent_tool_permission_deny():
    registry = ToolRegistry()
    registry.reset_tools()
    tool_a = DummyToolA()
    tool_b = DummyToolB()
    registry.register_tool(tool_a)
    registry.register_tool(tool_b)
    agent = Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Planner agent",
        tool_tags=["filesystem", "analysis", "testing"],
        prompt_file="planner.md",
        context_sources=[],
        color="#4CAF50"
    )
    agent.deny_tools = ["tool_b"]
    tools = get_tools_for_agent(agent, registry)
    assert tool_a in tools
    assert tool_b not in tools
