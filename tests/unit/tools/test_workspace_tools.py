"""
Unit tests for workspace tools registration and availability
"""
import pytest
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.tools.search_files_tool import SearchFilesTool
from ai_whisperer.tools.get_file_content_tool import GetFileContentTool


def test_workspace_tools_can_be_instantiated():
    """Test that all workspace tools can be created."""
    # Instantiate tools
    list_tool = ListDirectoryTool()
    search_tool = SearchFilesTool()
    content_tool = GetFileContentTool()
    
    # Verify names
    assert list_tool.name == "list_directory"
    assert search_tool.name == "search_files"
    assert content_tool.name == "get_file_content"
    
    # Verify categories
    assert list_tool.category == "File System"
    assert search_tool.category == "File System"
    assert content_tool.category == "File System"


def test_workspace_tools_have_correct_tags():
    """Test that workspace tools have appropriate tags."""
    list_tool = ListDirectoryTool()
    search_tool = SearchFilesTool()
    content_tool = GetFileContentTool()
    
    # Check list_directory tags
    assert "filesystem" in list_tool.tags
    assert "directory_browse" in list_tool.tags
    assert "analysis" in list_tool.tags
    
    # Check search_files tags
    assert "filesystem" in search_tool.tags
    assert "file_search" in search_tool.tags
    assert "analysis" in search_tool.tags
    
    # Check get_file_content tags
    assert "filesystem" in content_tool.tags
    assert "file_read" in content_tool.tags
    assert "analysis" in content_tool.tags


def test_workspace_tools_registration():
    """Test that workspace tools can be registered and retrieved."""
    registry = get_tool_registry()
    
    # Clear registry for test
    registry._registered_tools.clear()
    
    # Register workspace tools
    registry.register_tool(ListDirectoryTool())
    registry.register_tool(SearchFilesTool())
    registry.register_tool(GetFileContentTool())
    
    # Verify all tools are registered
    all_tools = registry.get_all_tools()
    tool_names = [tool.name for tool in all_tools]
    
    assert "list_directory" in tool_names
    assert "search_files" in tool_names
    assert "get_file_content" in tool_names
    
    # Verify individual retrieval
    assert registry.get_tool_by_name("list_directory") is not None
    assert registry.get_tool_by_name("search_files") is not None
    assert registry.get_tool_by_name("get_file_content") is not None


def test_workspace_tools_filtering():
    """Test filtering workspace tools by tags."""
    registry = get_tool_registry()
    
    # Clear and register tools
    registry._registered_tools.clear()
    registry.register_tool(ListDirectoryTool())
    registry.register_tool(SearchFilesTool())
    registry.register_tool(GetFileContentTool())
    
    # Filter by directory_browse tag
    browse_tools = registry.get_filtered_tools({"tags": ["directory_browse"]})
    assert len(browse_tools) == 1
    assert browse_tools[0].name == "list_directory"
    
    # Filter by file_search tag
    search_tools = registry.get_filtered_tools({"tags": ["file_search"]})
    assert len(search_tools) == 1
    assert search_tools[0].name == "search_files"
    
    # Filter by file_read tag
    read_tools = registry.get_filtered_tools({"tags": ["file_read"]})
    assert len(read_tools) == 1
    assert read_tools[0].name == "get_file_content"
    
    # Filter by analysis tag (should get all three)
    analysis_tools = registry.get_filtered_tools({"tags": ["analysis"]})
    assert len(analysis_tools) == 3