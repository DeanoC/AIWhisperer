"""
Tests for tool tags and categories
"""
import pytest
from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.write_file_tool import WriteFileTool
from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
from ai_whisperer.tools.tool_registry import get_tool_registry


def test_read_file_tool_tags():
    """Test that ReadFileTool has correct tags and category."""
    tool = ReadFileTool()
    assert tool.name == "read_file"
    assert tool.category == "File System"
    assert set(tool.tags) == {"filesystem", "file_read", "analysis"}


def test_write_file_tool_tags():
    """Test that WriteFileTool has correct tags and category."""
    tool = WriteFileTool()
    assert tool.name == "write_file"
    assert tool.category == "File System"
    assert set(tool.tags) == {"filesystem", "file_write"}


def test_execute_command_tool_tags():
    """Test that ExecuteCommandTool has correct tags and category."""
    tool = ExecuteCommandTool()
    assert tool.name == "execute_command"
    assert tool.category == "System"
    assert set(tool.tags) == {"code_execution", "utility"}


def test_tool_registry_filtering_by_tags():
    """Test that tools can be filtered by tags through the registry."""
    registry = get_tool_registry()
    
    # Clear and re-register tools for test isolation
    registry._registered_tools.clear()
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ExecuteCommandTool())
    
    # Test filtering by filesystem tag
    filesystem_tools = registry.get_filtered_tools({"tags": ["filesystem"]})
    tool_names = [tool.name for tool in filesystem_tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "execute_command" not in tool_names
    
    # Test filtering by file_read tag
    read_tools = registry.get_filtered_tools({"tags": ["file_read"]})
    tool_names = [tool.name for tool in read_tools]
    assert "read_file" in tool_names
    assert "write_file" not in tool_names
    assert "execute_command" not in tool_names
    
    # Test filtering by code_execution tag
    exec_tools = registry.get_filtered_tools({"tags": ["code_execution"]})
    tool_names = [tool.name for tool in exec_tools]
    assert "execute_command" in tool_names
    assert "read_file" not in tool_names
    assert "write_file" not in tool_names
    
    # Test filtering by multiple tags (OR logic)
    multi_tag_tools = registry.get_filtered_tools({"tags": ["file_read", "file_write"]})
    tool_names = [tool.name for tool in multi_tag_tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "execute_command" not in tool_names


def test_tool_registry_filtering_by_category():
    """Test that tools can be filtered by category."""
    registry = get_tool_registry()
    
    # Clear and re-register tools for test isolation
    registry._registered_tools.clear()
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ExecuteCommandTool())
    
    # Test filtering by File System category
    fs_tools = registry.get_filtered_tools({"category": "File System"})
    tool_names = [tool.name for tool in fs_tools]
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "execute_command" not in tool_names
    
    # Test filtering by System category
    sys_tools = registry.get_filtered_tools({"category": "System"})
    tool_names = [tool.name for tool in sys_tools]
    assert "execute_command" in tool_names
    assert "read_file" not in tool_names
    assert "write_file" not in tool_names