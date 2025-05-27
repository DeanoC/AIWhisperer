import pytest
from ai_whisperer.tools.tool_registry import ToolRegistry
from ai_whisperer.tools.base_tool import AITool

class DummyTool(AITool):
    @property
    def name(self):
        return "dummy_tool"
    @property
    def description(self):
        return "A dummy tool for testing."
    @property
    def parameters_schema(self):
        return {}
    @property
    def tags(self):
        return ["test", "dummy"]
    @property
    def category(self):
        return "Testing"
    def get_ai_prompt_instructions(self):
        return "Use dummy_tool for testing."
    def execute(self, **kwargs):
        return "executed"

def test_tool_tag_filtering():
    registry = ToolRegistry()
    registry.reset_tools()
    tool1 = DummyTool()
    registry.register_tool(tool1)
    filtered = registry.get_filtered_tools({"tags": ["test"]})
    assert tool1 in filtered
    filtered_none = registry.get_filtered_tools({"tags": ["notag"]})
    assert tool1 not in filtered_none

def test_tool_category_filtering():
    registry = ToolRegistry()
    registry.reset_tools()
    tool1 = DummyTool()
    registry.register_tool(tool1)
    filtered = registry.get_filtered_tools({"category": "Testing"})
    assert tool1 in filtered
    filtered_none = registry.get_filtered_tools({"category": "Other"})
    assert tool1 not in filtered_none

def test_tool_name_pattern_filtering():
    registry = ToolRegistry()
    registry.reset_tools()
    tool1 = DummyTool()
    registry.register_tool(tool1)
    filtered = registry.get_filtered_tools({"name_pattern": "dummy_.*"})
    assert tool1 in filtered
    filtered_none = registry.get_filtered_tools({"name_pattern": "real_.*"})
    assert tool1 not in filtered_none
