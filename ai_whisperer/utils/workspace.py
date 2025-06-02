import os
import json
import logging
from pathlib import Path
from typing import Any

class WorkspaceNotFoundError(Exception):
    pass

def find_whisper_workspace(start_path=None):
    """
    Search for a .WHISPER folder starting from start_path (or cwd) and walking up to the filesystem root.
    Resolves symlinks and handles permission errors gracefully.
    Returns the Path to the workspace root (parent of .WHISPER).
    Raises WorkspaceNotFoundError if not found.
    """
    if start_path is None:
        current = Path.cwd().resolve()
    else:
        current = Path(start_path).resolve()
    visited = set()
    while True:
        try:
            real_current = current.resolve()
            if str(real_current) in visited:
                break  # Prevent infinite loops with symlinks
            visited.add(str(real_current))
            whisper = real_current / ".WHISPER"
            if whisper.is_dir():
                return str(real_current)
        except PermissionError as e:
            logging.warning(f"Permission denied while accessing {current}: {e}. Skipping to parent directory.")
        except Exception:
            pass  # Ignore other errors and continue up
        if current.parent == current:
            break
        current = current.parent
    raise WorkspaceNotFoundError("No .WHISPER folder found in current or parent directories.")

def load_project_json(workspace_path) -> Any:
    """
    Loads .WHISPER/project.json from the workspace and returns the parsed dict.
    Returns None if not found. Raises if invalid JSON.
    """
    whisper_dir = Path(workspace_path) / ".WHISPER"
    project_file = whisper_dir / "project.json"
    if not project_file.exists():
        return None
    with open(project_file, 'r') as f:
        return json.load(f)
