"""
Tests for ListDirectoryTool
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.utils.path import PathManager
from ai_whisperer.core.exceptions import FileRestrictionError


@pytest.fixture
def setup_test_directory():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test structure
        test_dir = Path(temp_dir)
        
        # Create directories
        (test_dir / "src").mkdir()
        (test_dir / "src" / "components").mkdir()
        (test_dir / "tests").mkdir()
        (test_dir / ".hidden").mkdir()
        
        # Create files
        (test_dir / "README.md").write_text("# Test Project")
        (test_dir / "config.yaml").write_text("test: true")
        (test_dir / ".gitignore").write_text("*.pyc")
        (test_dir / "src" / "main.py").write_text("print('hello')")
        (test_dir / "src" / "components" / "app.py").write_text("class App: pass")
        (test_dir / "tests" / "test_main.py").write_text("def test(): pass")
        
        # Initialize PathManager with test directory
        PathManager._reset_instance()
        pm = PathManager.get_instance()
        pm.initialize({
            'project_path': temp_dir,
            'output_path': os.path.join(temp_dir, "output"),
            'workspace_path': temp_dir
        })
        
        yield test_dir


def test_list_directory_tool_properties():
    """Test basic properties of ListDirectoryTool."""
    tool = ListDirectoryTool()
    assert tool.name == "list_directory"
    assert tool.category == "File System"
    assert set(tool.tags) == {"filesystem", "directory_browse", "analysis"}
    assert "list_directory" in tool.get_ai_prompt_instructions()


def test_list_directory_flat(setup_test_directory):
    """Test flat directory listing."""
    tool = ListDirectoryTool()
    
    # List root directory
    result = tool.execute({"path": ".", "include_hidden": False})
    
    assert isinstance(result, dict)
    assert result['path'] == ''  # '.' is normalized to empty string
    entries = result['entries']
    
    # Check for expected entries
    dir_names = [e['name'] for e in entries if e['type'] == 'directory']
    file_names = [e['name'] for e in entries if e['type'] == 'file']
    
    assert 'src' in dir_names
    assert 'tests' in dir_names
    assert 'README.md' in file_names
    assert 'config.yaml' in file_names
    assert '.gitignore' not in file_names  # Hidden file excluded
    assert '.hidden' not in dir_names  # Hidden directory excluded


def test_list_directory_with_hidden(setup_test_directory):
    """Test directory listing with hidden files included."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "include_hidden": True})
    
    assert isinstance(result, dict)
    entries = result['entries']
    
    dir_names = [e['name'] for e in entries if e['type'] == 'directory']
    file_names = [e['name'] for e in entries if e['type'] == 'file']
    
    assert '.gitignore' in file_names
    assert '.hidden' in dir_names


def test_list_directory_subdirectory(setup_test_directory):
    """Test listing a subdirectory."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "src"})
    
    assert isinstance(result, dict)
    assert result['path'] == 'src'
    entries = result['entries']
    
    dir_names = [e['name'] for e in entries if e['type'] == 'directory']
    file_names = [e['name'] for e in entries if e['type'] == 'file']
    
    assert 'components' in dir_names
    assert 'main.py' in file_names


def test_list_directory_recursive(setup_test_directory):
    """Test recursive directory listing."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 2})
    
    assert isinstance(result, dict)
    assert result['recursive'] is True
    assert result['max_depth'] == 2
    entries = result['entries']
    
    # In recursive mode, entries are flattened with depth field
    # Check src directory at depth 0
    src_entries = [e for e in entries if e['path'] == 'src']
    assert len(src_entries) == 1
    assert src_entries[0]['type'] == 'directory'
    assert src_entries[0]['depth'] == 0
    
    # Check components directory at depth 1
    components_entries = [e for e in entries if e['path'] == 'src/components']
    assert len(components_entries) == 1
    assert components_entries[0]['type'] == 'directory'
    assert components_entries[0]['depth'] == 1
    
    # Check app.py at depth 2
    app_entries = [e for e in entries if e['name'] == 'app.py']
    assert len(app_entries) == 1
    assert app_entries[0]['path'] == 'src/components/app.py'
    assert app_entries[0]['depth'] == 2


def test_list_directory_recursive_depth_limit(setup_test_directory):
    """Test recursive listing respects max_depth."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 1})
    
    assert isinstance(result, dict)
    assert result['max_depth'] == 1
    entries = result['entries']
    
    # Should show src and components but not app.py (which would be at depth 2)
    # Check that we have entries at depth 0 and 1
    depths = [e['depth'] for e in entries]
    assert 0 in depths
    assert 1 in depths
    assert 2 not in depths  # Nothing at depth 2 due to limit
    
    # Should have src/components but not src/components/app.py
    paths = [e['path'] for e in entries]
    assert 'src/components' in paths
    assert 'src/components/app.py' not in paths


def test_list_directory_nonexistent_path(setup_test_directory):
    """Test handling of non-existent path."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "nonexistent"})
    
    assert isinstance(result, dict)
    assert 'error' in result
    assert "does not exist" in result['error']


def test_list_directory_file_not_directory(setup_test_directory):
    """Test handling when path is a file, not a directory."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "README.md"})
    
    assert isinstance(result, dict)
    assert 'error' in result
    assert "not a directory" in result['error']


def test_list_directory_outside_workspace():
    """Test that access outside workspace is denied."""
    tool = ListDirectoryTool()
    
    # Try to access parent directory
    result = tool.execute({"path": ".."})
    assert isinstance(result, dict)
    assert 'error' in result
    assert "outside" in result['error'].lower() or "denied" in result['error'].lower()


def test_list_directory_empty_directory(setup_test_directory):
    """Test listing an empty directory."""
    # Create an empty directory
    empty_dir = setup_test_directory / "empty"
    empty_dir.mkdir()
    
    tool = ListDirectoryTool()
    result = tool.execute({"path": "empty"})
    
    assert isinstance(result, dict)
    assert result['path'] == 'empty'
    assert len(result['entries']) == 0
    assert result['total_files'] == 0
    assert result['total_directories'] == 0


def test_list_directory_file_sizes(setup_test_directory):
    """Test that file sizes are displayed correctly."""
    # Create a larger file
    large_file = setup_test_directory / "large.txt"
    large_file.write_text("x" * 5000)  # 5KB file
    
    tool = ListDirectoryTool()
    result = tool.execute({"path": "."})
    
    assert isinstance(result, dict)
    entries = result['entries']
    
    large_entry = next((e for e in entries if e['name'] == 'large.txt'), None)
    assert large_entry is not None
    assert large_entry['size'] == 5000
    assert large_entry['size_formatted'] == '4.9 KB'


def test_list_directory_max_depth_validation(setup_test_directory):
    """Test that max_depth is validated to be within bounds."""
    tool = ListDirectoryTool()
    
    # Test max_depth too high
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 20})
    assert isinstance(result, dict)
    # Should be clamped to 10, but still work
    assert result['max_depth'] <= 10
    assert len(result['entries']) > 0
    
    # Test max_depth too low
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 0})
    assert isinstance(result, dict)
    # Should be clamped to 1
    assert result['max_depth'] == 1
    assert len(result['entries']) > 0