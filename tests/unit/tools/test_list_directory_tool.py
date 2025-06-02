"""
Tests for ListDirectoryTool
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from ai_whisperer.tools.list_directory_tool import ListDirectoryTool
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError


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
    
    assert "Contents of workspace root:" in result
    assert "[DIR]  src/" in result
    assert "[DIR]  tests/" in result
    assert "[FILE] README.md" in result
    assert "[FILE] config.yaml" in result
    assert ".gitignore" not in result  # Hidden file excluded
    assert ".hidden" not in result  # Hidden directory excluded


def test_list_directory_with_hidden(setup_test_directory):
    """Test directory listing with hidden files included."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "include_hidden": True})
    
    assert "[FILE] .gitignore" in result
    assert "[DIR]  .hidden/" in result


def test_list_directory_subdirectory(setup_test_directory):
    """Test listing a subdirectory."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "src"})
    
    assert "Contents of src:" in result
    assert "[DIR]  components/" in result
    assert "[FILE] main.py" in result


def test_list_directory_recursive(setup_test_directory):
    """Test recursive directory listing."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 2})
    
    assert "Workspace root:" in result
    assert "src/" in result
    assert "├── components/" in result
    assert "│   └── app.py" in result
    assert "└── main.py" in result
    assert "tests/" in result
    assert "└── test_main.py" in result


def test_list_directory_recursive_depth_limit(setup_test_directory):
    """Test recursive listing respects max_depth."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 1})
    
    # Should show src/components/ but not app.py inside it
    assert "src/" in result
    assert "├── components/" in result
    assert "app.py" not in result  # Beyond depth limit


def test_list_directory_nonexistent_path(setup_test_directory):
    """Test handling of non-existent path."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "nonexistent"})
    
    assert "Error: Path 'nonexistent' does not exist." in result


def test_list_directory_file_not_directory(setup_test_directory):
    """Test handling when path is a file, not a directory."""
    tool = ListDirectoryTool()
    
    result = tool.execute({"path": "README.md"})
    
    assert "Error: Path 'README.md' is not a directory." in result


def test_list_directory_outside_workspace():
    """Test that access outside workspace is denied."""
    tool = ListDirectoryTool()
    
    # Try to access parent directory
    with pytest.raises(FileRestrictionError):
        tool.execute({"path": ".."})


def test_list_directory_empty_directory(setup_test_directory):
    """Test listing an empty directory."""
    # Create an empty directory
    empty_dir = setup_test_directory / "empty"
    empty_dir.mkdir()
    
    tool = ListDirectoryTool()
    result = tool.execute({"path": "empty"})
    
    assert "Directory is empty." in result


def test_list_directory_file_sizes(setup_test_directory):
    """Test that file sizes are displayed correctly."""
    # Create a larger file
    large_file = setup_test_directory / "large.txt"
    large_file.write_text("x" * 5000)  # 5KB file
    
    tool = ListDirectoryTool()
    result = tool.execute({"path": "."})
    
    assert "[FILE] large.txt (4.9KB)" in result


def test_list_directory_max_depth_validation(setup_test_directory):
    """Test that max_depth is validated to be within bounds."""
    tool = ListDirectoryTool()
    
    # Test max_depth too high
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 20})
    # Should be clamped to 10, but still work
    assert "Workspace root:" in result
    
    # Test max_depth too low
    result = tool.execute({"path": ".", "recursive": True, "max_depth": 0})
    # Should be clamped to 1
    assert "src/" in result