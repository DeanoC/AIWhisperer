import pytest
from unittest import mock
from ai_whisperer import workspace_detection

# Example CLI entrypoint (to be replaced with actual CLI logic)
def cli_entrypoint(workspace_path):
    # Simulate CLI validation logic
    workspace_detection.find_whisper_workspace(workspace_path)
    return True

def test_cli_validates_workspace_before_execution(tmp_path):
    """Test CLI validates workspace before running commands"""
    workspace = tmp_path / "project"
    (workspace / ".WHISPER").mkdir(parents=True)
    # Should not raise
    assert cli_entrypoint(str(workspace)) is True
    # Should raise if not present
    with pytest.raises(workspace_detection.WorkspaceNotFoundError):
        cli_entrypoint(str(tmp_path / "no_workspace"))

def test_cli_workspace_error_message(tmp_path):
    """Test CLI shows helpful error message for missing workspace"""
    with pytest.raises(workspace_detection.WorkspaceNotFoundError) as excinfo:
        cli_entrypoint(str(tmp_path / "no_workspace"))
    assert "No .WHISPER folder found" in str(excinfo.value) or "Permission denied" in str(excinfo.value)
