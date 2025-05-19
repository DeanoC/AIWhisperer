import pytest
import logging
from typing import Dict, Any, List, Optional

# Import the actual classes
from ai_whisperer.tools.base_tool import AITool
from ai_whisperer.tools.tool_registry import ToolRegistry, get_tool_registry

# Dummy AITool implementations for testing
class DummyToolA(AITool):
    @property
    def name(self) -> str:
        return "tool_a"

    @property
    def description(self) -> str:
        return "Description A"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def get_ai_prompt_instructions(self) -> str:
        return "Instructions for Tool A"

    async def execute(self, **kwargs: Any) -> Any:
        return "Result A"

class DummyToolB(AITool):
    @property
    def name(self) -> str:
        return "tool_b"

    @property
    def description(self) -> str:
        return "Description B"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"param1": {"type": "string"}}, "required": ["param1"]}

    @property
    def category(self) -> Optional[str]:
        return "Utility"

    @property
    def tags(self) -> List[str]:
        return ["file_io", "read"]

    def get_ai_prompt_instructions(self) -> str:
        return "Instructions for Tool B"

    async def execute(self, **kwargs: Any) -> Any:
        return "Result B"

class DummyToolC(AITool):
    @property
    def name(self) -> str:
        return "tool_c"

    @property
    def description(self) -> str:
        return "Description C"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {"param2": {"type": "integer"}}}

    @property
    def category(self) -> Optional[str]:
        return "Data Analysis"

    @property
    def tags(self) -> List[str]:
        return ["data", "analyze"]


    def get_ai_prompt_instructions(self) -> str:
        return "Instructions for Tool C"

    async def execute(self, **kwargs: Any) -> Any:
        return "Result C"

# Helper function to get a clean registry instance for each test
@pytest.fixture
def registry():
    # Use the singleton instance but clear it before each test
    reg = get_tool_registry()
    reg._registered_tools.clear() # Clear registered tools for isolation
    return reg

# Tests for ToolRegistry
def test_register_and_get_tool(registry: ToolRegistry):
    """Tests registering and retrieving a tool by name."""
    tool_a = DummyToolA()
    registry.register_tool(tool_a)
    retrieved_tool = registry.get_tool_by_name("tool_a")
    assert retrieved_tool is not None
    assert retrieved_tool.name == "tool_a"
    assert retrieved_tool is tool_a # Ensure it's the same instance

def test_get_non_existent_tool(registry: ToolRegistry):
    """Tests retrieving a tool that does not exist."""
    retrieved_tool = registry.get_tool_by_name("non_existent_tool")
    assert retrieved_tool is None

def test_register_duplicate_tool(registry: ToolRegistry, caplog):
    """Tests registering a tool with a name that is already registered."""
    tool_a_1 = DummyToolA()
    tool_a_2 = DummyToolA() # Another instance with the same name

    registry.register_tool(tool_a_1)
    
    with caplog.at_level(logging.WARNING):
        registry.register_tool(tool_a_2)
    
    assert any("already registered" in record.message for record in caplog.records)

    retrieved_tool = registry.get_tool_by_name("tool_a")
    assert retrieved_tool is tool_a_1 # The first registered tool should remain

def test_get_all_tools(registry: ToolRegistry):
    """Tests retrieving a list of all registered tools."""
    tool_a = DummyToolA()
    tool_b = DummyToolB()
    registry.register_tool(tool_a)
    registry.register_tool(tool_b)

    all_tools = registry.get_all_tools()
    assert len(all_tools) == 2
    tool_names = sorted([tool.name for tool in all_tools])
    assert tool_names == ["tool_a", "tool_b"]

def test_get_all_tool_definitions(registry: ToolRegistry):
    """Tests retrieving Openrouter-compatible definitions for all tools."""
    tool_a = DummyToolA()
    tool_b = DummyToolB()
    registry.register_tool(tool_a)
    registry.register_tool(tool_b)

    all_definitions = registry.get_all_tool_definitions()
    assert len(all_definitions) == 2
    definition_names = sorted([defn['function']['name'] for defn in all_definitions])
    assert definition_names == ["tool_a", "tool_b"]

    # Basic check on structure
    for defn in all_definitions:
        assert defn['type'] == 'function'
        assert 'function' in defn
        assert 'name' in defn['function']
        assert 'description' in defn['function']
        assert 'parameters' in defn['function']

def test_get_all_ai_prompt_instructions(registry: ToolRegistry):
    """Tests retrieving consolidated AI prompt instructions for all tools."""
    tool_a = DummyToolA()
    tool_b = DummyToolB()
    registry.register_tool(tool_a)
    registry.register_tool(tool_b)

    all_instructions = registry.get_all_ai_prompt_instructions()
    # Order might vary depending on dictionary iteration, so check for presence
    assert "Instructions for Tool A" in all_instructions
    assert "Instructions for Tool B" in all_instructions
    assert "\n\n" in all_instructions # Check for separator

def test_get_filtered_tools(registry: ToolRegistry):
    """Tests filtering tools based on criteria."""
    tool_a = DummyToolA() # No category, no tags
    tool_b = DummyToolB() # Category: Utility, Tags: ["file_io", "read"]
    tool_c = DummyToolC() # Category: Data Analysis, Tags: ["data", "analyze"]

    registry.register_tool(tool_a)
    registry.register_tool(tool_b)
    registry.register_tool(tool_c)

    # Filter by category
    filtered_by_category = registry.get_filtered_tools({"category": "Utility"})
    assert len(filtered_by_category) == 1
    assert filtered_by_category[0].name == "tool_b"

    # Filter by tags (single tag)
    filtered_by_tag_read = registry.get_filtered_tools({"tags": ["read"]})
    assert len(filtered_by_tag_read) == 1
    assert filtered_by_tag_read[0].name == "tool_b"

    # Filter by tags (multiple tags - AND logic)
    filtered_by_tags_file_read = registry.get_filtered_tools({"tags": ["file_io", "read"]})
    assert len(filtered_by_tags_file_read) == 1
    assert filtered_by_tags_file_read[0].name == "tool_b"

    # Filter by tags (multiple tags - no match)
    filtered_by_tags_write = registry.get_filtered_tools({"tags": ["write"]})
    assert len(filtered_by_tags_write) == 0

    # Filter by category and tags
    filtered_by_cat_and_tags = registry.get_filtered_tools({"category": "Utility", "tags": ["file_io"]})
    assert len(filtered_by_cat_and_tags) == 1
    assert filtered_by_cat_and_tags[0].name == "tool_b"

    # Filter by name pattern
    filtered_by_name_pattern = registry.get_filtered_tools({"name_pattern": "tool_[bc]"})
    assert len(filtered_by_name_pattern) == 2
    filtered_names = sorted([tool.name for tool in filtered_by_name_pattern])
    assert filtered_names == ["tool_b", "tool_c"]

    # No criteria should return all tools
    filtered_no_criteria = registry.get_filtered_tools({})
    assert len(filtered_no_criteria) == 3

    # Filter by non-existent criteria value
    filtered_non_existent_cat = registry.get_filtered_tools({"category": "NonExistent"})
    assert len(filtered_non_existent_cat) == 0

    # Filter by non-existent tag
    filtered_non_existent_tag = registry.get_filtered_tools({"tags": ["non_existent_tag"]})
    assert len(filtered_non_existent_tag) == 0

# Add a test for registering a non-AITool object
def test_register_non_aitool(registry: ToolRegistry, caplog):
    """Tests attempting to register an object that is not an AITool."""
    non_tool_object = object()
    
    with caplog.at_level(logging.WARNING):
        registry.register_tool(non_tool_object)

    assert any("Attempted to register non-AITool object" in record.message for record in caplog.records)
    assert len(registry.get_all_tools()) == 0 # No tool should have been registered