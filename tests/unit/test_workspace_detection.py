import pytest
import os
from pathlib import Path

# Placeholder for the actual function to be implemented
from ai_whisperer.workspace_detection import find_whisper_workspace, WorkspaceNotFoundError

def test_whisper_folder_detected_in_current_dir(tmp_path):
    """Test detection of .WHISPER folder in current directory"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    os.chdir(tmp_path)
    assert find_whisper_workspace() == tmp_path

def test_whisper_folder_detected_in_parent_dir(tmp_path):
    """Test detection of .WHISPER folder in parent directory"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    os.chdir(subdir)
    assert find_whisper_workspace() == tmp_path

def test_no_whisper_folder_raises_error(tmp_path):
    """Test error when no .WHISPER folder found"""
    os.chdir(tmp_path)
    with pytest.raises(WorkspaceNotFoundError):
        find_whisper_workspace()

def test_whisper_folder_stops_at_filesystem_root(tmp_path):
    """Test search stops at filesystem root"""
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    os.chdir(deep)
    with pytest.raises(WorkspaceNotFoundError):
        find_whisper_workspace()

def test_whisper_folder_with_workspace_config(tmp_path):
    """Test .WHISPER folder with workspace.yaml config"""
    whisper_dir = tmp_path / ".WHISPER"
    whisper_dir.mkdir()
    config_file = whisper_dir / "workspace.yaml"
    config_file.write_text("key: value\n")
    os.chdir(tmp_path)
    # This test will be extended when load_workspace_config is implemented
    assert find_whisper_workspace() == tmp_path
