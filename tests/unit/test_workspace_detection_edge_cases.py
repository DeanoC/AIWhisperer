import os
import pytest
import tempfile
import shutil
from pathlib import Path
from ai_whisperer.workspace_detection import find_whisper_workspace, WorkspaceNotFoundError, load_project_json


def test_symlink_handling(tmp_path):
    """Test workspace detection handles symlinks correctly"""
    # Create .WHISPER workspace
    workspace = tmp_path / "project"
    whisper = workspace / ".WHISPER"
    whisper.mkdir(parents=True)
    # Create a subdirectory and a symlink to it
    subdir = workspace / "subdir"
    subdir.mkdir()
    symlink = tmp_path / "symlinked_subdir"
    symlink.symlink_to(subdir, target_is_directory=True)
    # Test detection from symlinked directory
    detected = find_whisper_workspace(str(symlink))
    assert detected == str(workspace)


def test_permission_denied_handling(tmp_path):
    """Test graceful handling of permission denied errors"""
    workspace = tmp_path / "project"
    whisper = workspace / ".WHISPER"
    whisper.mkdir(parents=True)
    restricted = tmp_path / "restricted"
    restricted.mkdir()
    # Remove permissions
    restricted.chmod(0)
    try:
        with pytest.raises(WorkspaceNotFoundError):
            find_whisper_workspace(str(restricted))
    finally:
        restricted.chmod(0o700)  # Restore permissions for cleanup


def test_corrupted_workspace_config(tmp_path):
    """Test handling of corrupted project.json"""
    workspace = tmp_path / "project"
    whisper = workspace / ".WHISPER"
    whisper.mkdir(parents=True)
    project_json = whisper / "project.json"
    project_json.write_text("{ invalid json }")
    with pytest.raises(Exception):
        load_project_json(str(workspace))


def test_multiple_whisper_folders_in_hierarchy(tmp_path):
    """Test behavior with nested .WHISPER folders (should pick closest)"""
    parent = tmp_path / "parent"
    child = parent / "child"
    parent.mkdir()
    child.mkdir()
    (parent / ".WHISPER").mkdir()
    (child / ".WHISPER").mkdir()
    detected = find_whisper_workspace(str(child))
    assert detected == str(child)
