import os
import json
import tempfile
import shutil
from pathlib import Path
from interactive_server.services.project_manager import ProjectManager
from interactive_server.models.project import ProjectCreate, ProjectUpdate
import pytest

def test_project_settings_persistence():
    # Setup temp project directory
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        project_dir = Path(tmpdir) / "proj1"
        project_dir.mkdir()
        data_dir.mkdir()
        
        # Create ProjectManager
        manager = ProjectManager(data_dir)
        
        # Create a project
        create_data = ProjectCreate(name="TestProj", path=str(project_dir))
        project = manager.create_project(create_data)
        
        # Update settings
        update_data = ProjectUpdate(settings={
            "default_agent": "alice",
            "auto_save": False,
            "external_agent_type": "openai"
        })
        manager.update_project(project.id, update_data)
        
        # Reload manager to simulate restart
        manager2 = ProjectManager(data_dir)
        loaded_project = manager2.get_project(project.id)
        
        # Assert settings persisted
        assert loaded_project.settings.default_agent == "alice"
        assert loaded_project.settings.auto_save is False
        assert getattr(loaded_project.settings, "external_agent_type", None) == "openai"
        
        # Also check .WHISPER/project.json
        whisper_path = Path(loaded_project.whisper_path)
        project_json = whisper_path / "project.json"
        with open(project_json) as f:
            data = json.load(f)
        assert data["settings"]["default_agent"] == "alice"
        assert data["settings"]["auto_save"] is False
        assert data["settings"].get("external_agent_type") == "openai"
