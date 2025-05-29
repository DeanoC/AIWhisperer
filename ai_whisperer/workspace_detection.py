import os
from pathlib import Path


import json
from typing import Any

class WorkspaceNotFoundError(Exception):
    pass

def find_whisper_workspace(start_path=None):
    """
    Search for a .WHISPER folder starting from start_path (or cwd) and walking up to the filesystem root.
    Returns the Path to the workspace root (parent of .WHISPER).
    Raises WorkspaceNotFoundError if not found.
    """
    if start_path is None:
        current = Path.cwd()
    else:
        current = Path(start_path).resolve()
    while True:
        whisper = current / ".WHISPER"
        if whisper.is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise WorkspaceNotFoundError("No .WHISPER folder found in current or parent directories.")

def load_project_json(workspace_path) -> Any:
    """
    Loads .WHISPER/project.json from the workspace and returns the parsed dict.
    Returns None if not found or invalid.
    """
    whisper_dir = Path(workspace_path) / ".WHISPER"
    project_file = whisper_dir / "project.json"
    if not project_file.exists():
        return None
    try:
        with open(project_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None
