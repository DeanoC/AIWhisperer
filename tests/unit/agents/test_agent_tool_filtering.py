import pytest
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.services.agents.registry import Agent

def get_tools_for_agent(agent: Agent, registry: ToolRegistry):
    return registry.get_filtered_tools({"tags": agent.tool_tags})

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

def test_agent_tool_filtering():
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
    tools = get_tools_for_agent(agent, registry)
    assert tool_a in tools
    assert tool_b not in tools
