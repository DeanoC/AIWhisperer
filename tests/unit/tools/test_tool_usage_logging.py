import pytest
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.services.agents.registry import Agent
from ai_whisperer.tools.tool_usage_logging import log_tool_usage, get_tool_usage_log

class DummyTool(AITool):
    @property
    def name(self):
        return "dummy_tool"
    @property
    def description(self):
        return "A dummy tool."
    @property
    def parameters_schema(self):
        return {"type": "object"}
    def get_ai_prompt_instructions(self):
        return "Use dummy_tool."
    def execute(self, **kwargs):
        return "ok"

def test_tool_usage_logging():
    agent = Agent(
        agent_id="P",
        name="Patricia the Planner",
        role="planner",
        description="Planner agent",
        tool_tags=["filesystem"],
        prompt_file="planner.md",
        context_sources=[],
        color="#4CAF50"
    )
    tool = DummyTool()
    params = {"foo": "bar"}
    result = tool.execute(**params)
    entry = log_tool_usage(agent, tool, params, result)
    log = get_tool_usage_log()
    assert entry in log
    assert log[-1]["agent_id"] == "P"
    assert log[-1]["tool_name"] == "dummy_tool"
    assert log[-1]["params"] == params
    assert log[-1]["result"] == result
