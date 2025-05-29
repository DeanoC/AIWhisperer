"""
Tests for GetFileContentTool
"""
import pytest
import os
import tempfile
from pathlib import Path

from ai_whisperer.tools.get_file_content_tool import GetFileContentTool
from ai_whisperer.path_management import PathManager
from ai_whisperer.exceptions import FileRestrictionError


@pytest.fixture
def setup_test_files():
    """Create temporary files for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        test_dir = Path(temp_dir)
        
        # Small text file
        small_file = test_dir / "small.txt"
        small_file.write_text("Line 1\nLine 2\nLine 3\nLine 4\nLine 5")
        
        # Large text file (300 lines)
        large_file = test_dir / "large.py"
        large_content = []
        for i in range(1, 301):
            large_content.append(f"# Line {i}")
        large_file.write_text("\n".join(large_content))
        
        # Binary file
        binary_file = test_dir / "binary.dat"
        binary_file.write_bytes(b'\x00\x01\x02\x03\xff\xfe\xfd')
        
        # UTF-8 file with special characters
        utf8_file = test_dir / "unicode.txt"
        utf8_file.write_text("Hello 世界\nΓειά σου κόσμε\n🌍🌎🌏", encoding='utf-8')
        
        # Empty file
        empty_file = test_dir / "empty.txt"
        empty_file.write_text("")
        
        # Initialize PathManager
        PathManager._reset_instance()
        pm = PathManager.get_instance()
        pm.initialize({
            'project_path': temp_dir,
            'output_path': os.path.join(temp_dir, "output"),
            'workspace_path': temp_dir
        })
        
        yield test_dir


def test_get_file_content_tool_properties():
    """Test basic properties of GetFileContentTool."""
    tool = GetFileContentTool()
    assert tool.name == "get_file_content"
    assert tool.category == "File System"
    assert set(tool.tags) == {"filesystem", "file_read", "analysis"}
    assert "get_file_content" in tool.get_ai_prompt_instructions()


def test_read_small_file(setup_test_files):
    """Test reading a small file completely."""
    tool = GetFileContentTool()
    
    result = tool.execute({"path": "small.txt"})
    
    assert "File: small.txt (5 lines)" in result
    assert "   1 | Line 1" in result
    assert "   2 | Line 2" in result
    assert "   3 | Line 3" in result
    assert "   4 | Line 4" in result
    assert "   5 | Line 5" in result


def test_read_with_line_range(setup_test_files):
    """Test reading specific line range."""
    tool = GetFileContentTool()
    
    result = tool.execute({
        "path": "small.txt",
        "start_line": 2,
        "end_line": 4
    })
    
    assert "File: small.txt (lines 2-4 of 5)" in result
    assert "   2 | Line 2" in result
    assert "   3 | Line 3" in result
    assert "   4 | Line 4" in result
    assert "Line 1" not in result
    assert "Line 5" not in result


def test_preview_mode(setup_test_files):
    """Test preview mode on large file."""
    tool = GetFileContentTool()
    
    result = tool.execute({
        "path": "large.py",
        "preview_only": True
    })
    
    assert "File: large.py" in result
    assert "Total lines: 300" in result
    assert "Preview: First 200 lines" in result
    assert "   1 | # Line 1" in result
    assert " 200 | " in result
    assert " 201 | " not in result  # Should stop at 200


def test_preview_mode_small_file(setup_test_files):
    """Test preview mode on file smaller than 200 lines."""
    tool = GetFileContentTool()
    
    result = tool.execute({
        "path": "small.txt",
        "preview_only": True
    })
    
    assert "File: small.txt" in result
    assert "Total lines: 5" in result
    assert "Preview: Complete file" in result
    assert "   1 | Line 1" in result
    assert "   5 | Line 5" in result


def test_read_empty_file(setup_test_files):
    """Test reading an empty file."""
    tool = GetFileContentTool()
    
    result = tool.execute({"path": "empty.txt"})
    
    assert "File: empty.txt (0 lines)" in result


def test_read_unicode_file(setup_test_files):
    """Test reading file with Unicode characters."""
    tool = GetFileContentTool()
    
    result = tool.execute({"path": "unicode.txt"})
    
    assert "Hello 世界" in result
    assert "Γειά σου κόσμε" in result
    assert "🌍🌎🌏" in result


def test_binary_file_detection(setup_test_files):
    """Test that binary files are detected and rejected."""
    tool = GetFileContentTool()
    
    result = tool.execute({"path": "binary.dat"})
    
    assert "Error:" in result
    assert "binary file" in result.lower()


def test_nonexistent_file(setup_test_files):
    """Test handling of non-existent file."""
    tool = GetFileContentTool()
    
    result = tool.execute({"path": "nonexistent.txt"})
    
    assert "Error: File 'nonexistent.txt' does not exist." in result


def test_directory_instead_of_file(setup_test_files):
    """Test handling when path points to directory."""
    # Create a directory
    (setup_test_files / "testdir").mkdir()
    
    tool = GetFileContentTool()
    result = tool.execute({"path": "testdir"})
    
    assert "Error: Path 'testdir' is not a file." in result


def test_outside_workspace_access():
    """Test that access outside workspace is denied."""
    tool = GetFileContentTool()
    
    with pytest.raises(FileRestrictionError):
        tool.execute({"path": "../outside.txt"})


def test_missing_path_argument():
    """Test error when path is missing."""
    tool = GetFileContentTool()
    
    result = tool.execute({})
    
    assert "Error: 'path' argument is required." in result


def test_invalid_line_range(setup_test_files):
    """Test handling of invalid line ranges."""
    tool = GetFileContentTool()
    
    # Start line beyond file length
    result = tool.execute({
        "path": "small.txt",
        "start_line": 10
    })
    assert "Error: start_line (10) exceeds total lines (5)" in result
    
    # Invalid range (start > end)
    result = tool.execute({
        "path": "small.txt",
        "start_line": 4,
        "end_line": 2
    })
    assert "Error: Invalid line range" in result


def test_line_range_adjustment(setup_test_files):
    """Test that end_line is adjusted if beyond file length."""
    tool = GetFileContentTool()
    
    result = tool.execute({
        "path": "small.txt",
        "start_line": 3,
        "end_line": 10  # Beyond file length
    })
    
    assert "File: small.txt (lines 3-5 of 5)" in result
    assert "   3 | Line 3" in result
    assert "   4 | Line 4" in result
    assert "   5 | Line 5" in result


def test_file_size_formatting(setup_test_files):
    """Test file size formatting in preview mode."""
    # Create a file larger than 1KB
    large_file = setup_test_files / "largefile.txt"
    large_file.write_text("x" * 2048)  # 2KB
    
    tool = GetFileContentTool()
    result = tool.execute({
        "path": "largefile.txt",
        "preview_only": True
    })
    
    assert "File size: 2.0KB" in result