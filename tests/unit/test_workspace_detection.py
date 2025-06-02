import pytest
import os
from pathlib import Path

# Import the actual functions
from ai_whisperer.utils.workspace import find_whisper_workspace, WorkspaceNotFoundError

def test_whisper_folder_detected_in_current_dir(tmp_path):
    """Test detection of .WHISPER folder in current directory"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    
    # Save current directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = find_whisper_workspace()
        assert result == str(tmp_path)
    finally:
        # Always restore original directory
        os.chdir(original_cwd)

def test_whisper_folder_detected_in_parent_dir(tmp_path):
    """Test detection of .WHISPER folder in parent directory"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    
    # Save current directory
    original_cwd = os.getcwd()
    try:
        os.chdir(subdir)
        result = find_whisper_workspace()
        assert result == str(tmp_path)
    finally:
        # Always restore original directory
        os.chdir(original_cwd)

def test_no_whisper_folder_raises_error(tmp_path):
    """Test error when no .WHISPER folder found"""
    # Save current directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        with pytest.raises(WorkspaceNotFoundError):
            find_whisper_workspace()
    finally:
        # Always restore original directory
        os.chdir(original_cwd)

def test_whisper_folder_stops_at_filesystem_root(tmp_path):
    """Test search stops at filesystem root"""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    
    # Save current directory
    original_cwd = os.getcwd()
    try:
        os.chdir(deep)
        with pytest.raises(WorkspaceNotFoundError):
            find_whisper_workspace()
    finally:
        # Always restore original directory
        os.chdir(original_cwd)

def test_whisper_folder_with_workspace_config(tmp_path):
    """Test .WHISPER folder with workspace.yaml config"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    config_file = whisper_dir / "workspace.yaml"
    config_file.write_text("key: value\n")
    
    # Save current directory
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = find_whisper_workspace()
        assert result == str(tmp_path)
        # Test that config file exists
        assert config_file.exists()
    finally:
        # Always restore original directory
        os.chdir(original_cwd)
