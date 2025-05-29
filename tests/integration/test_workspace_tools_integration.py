"""
Integration tests for workspace tools
"""
import pytest
import os
import tempfile
from pathlib import Path

from ai_whisperer.plan_runner import PlanRunner
from ai_whisperer.tools.tool_registry import get_tool_registry
from ai_whisperer.path_management import PathManager
import threading


@pytest.fixture
def setup_runner():
    """Setup PlanRunner with initialized tools."""
    # Reset registry to ensure clean state
    registry = get_tool_registry()
    registry._registered_tools.clear()
    
    # Create PlanRunner which registers tools
    config = {"output_dir": "output"}
    shutdown_event = threading.Event()
    runner = PlanRunner(config, shutdown_event)
    
    yield runner
    
    # Cleanup
    registry._registered_tools.clear()


def test_all_tools_registered(setup_runner):
    """Test that all workspace tools are registered."""
    registry = get_tool_registry()
    all_tools = registry.get_all_tools()
    tool_names = [tool.name for tool in all_tools]
    
    # Check core tools
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "execute_command" in tool_names
    
    # Check new workspace tools
    assert "list_directory" in tool_names
    assert "search_files" in tool_names
    assert "get_file_content" in tool_names


def test_filesystem_tag_filtering(setup_runner):
    """Test filtering tools by filesystem tag."""
    registry = get_tool_registry()
    
    # Get all tools with filesystem tag
    fs_tools = registry.get_filtered_tools({"tags": ["filesystem"]})
    fs_tool_names = [tool.name for tool in fs_tools]
    
    # Should include all file operation tools
    assert "read_file" in fs_tool_names
    assert "write_file" in fs_tool_names
    assert "list_directory" in fs_tool_names
    assert "search_files" in fs_tool_names
    assert "get_file_content" in fs_tool_names
    
    # Should not include non-filesystem tools
    assert "execute_command" not in fs_tool_names


def test_file_read_tag_filtering(setup_runner):
    """Test filtering tools by file_read tag."""
    registry = get_tool_registry()
    
    # Get tools with file_read tag
    read_tools = registry.get_filtered_tools({"tags": ["file_read"]})
    read_tool_names = [tool.name for tool in read_tools]
    
    # Should include read tools
    assert "read_file" in read_tool_names
    assert "get_file_content" in read_tool_names
    
    # Should not include write or browse tools
    assert "write_file" not in read_tool_names
    assert "list_directory" not in read_tool_names


def test_directory_browse_tag_filtering(setup_runner):
    """Test filtering tools by directory_browse tag."""
    registry = get_tool_registry()
    
    # Get tools with directory_browse tag
    browse_tools = registry.get_filtered_tools({"tags": ["directory_browse"]})
    browse_tool_names = [tool.name for tool in browse_tools]
    
    # Should include only list_directory
    assert "list_directory" in browse_tool_names
    assert len(browse_tool_names) == 1


def test_file_search_tag_filtering(setup_runner):
    """Test filtering tools by file_search tag."""
    registry = get_tool_registry()
    
    # Get tools with file_search tag
    search_tools = registry.get_filtered_tools({"tags": ["file_search"]})
    search_tool_names = [tool.name for tool in search_tools]
    
    # Should include only search_files
    assert "search_files" in search_tool_names
    assert len(search_tool_names) == 1


def test_analysis_tag_filtering(setup_runner):
    """Test filtering tools by analysis tag."""
    registry = get_tool_registry()
    
    # Get tools with analysis tag
    analysis_tools = registry.get_filtered_tools({"tags": ["analysis"]})
    analysis_tool_names = [tool.name for tool in analysis_tools]
    
    # Should include all tools that help with analysis
    assert "read_file" in analysis_tool_names
    assert "list_directory" in analysis_tool_names
    assert "search_files" in analysis_tool_names
    assert "get_file_content" in analysis_tool_names
    
    # Should not include write tools
    assert "write_file" not in analysis_tool_names


def test_workspace_tools_with_pathmanager():
    """Test that workspace tools work with PathManager."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize PathManager
        PathManager._reset_instance()
        pm = PathManager.get_instance()
        pm.initialize({
            'project_path': temp_dir,
            'output_path': os.path.join(temp_dir, "output"),
            'workspace_path': temp_dir
        })
        
        # Create test files
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello World")
        
        # Create runner and get tools
        config = {"output_dir": os.path.join(temp_dir, "output")}
        shutdown_event = threading.Event()
        runner = PlanRunner(config, shutdown_event)
        
        registry = get_tool_registry()
        
        # Test list_directory
        list_tool = registry.get_tool_by_name("list_directory")
        result = list_tool.execute({"path": "."})
        assert "test.txt" in result
        
        # Test search_files
        search_tool = registry.get_tool_by_name("search_files")
        result = search_tool.execute({"pattern": "*.txt"})
        assert "test.txt" in result
        
        # Test get_file_content
        content_tool = registry.get_tool_by_name("get_file_content")
        result = content_tool.execute({"path": "test.txt"})
        assert "Hello World" in result