import pytest
from ai_whisperer.agents.planner_tools import (
    analyze_workspace,
    read_schema_files,
    validate_plan
)


def test_analyze_workspace(tmp_path):
    # Create dummy files and folders
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# Project")
    structure = analyze_workspace(tmp_path)
    norm = lambda p: p.replace("\\", "/")
    structure_norm = [norm(s) for s in structure]
    assert "src/" in structure_norm
    assert "src/main.py" in structure_norm
    assert "README.md" in structure_norm

def test_read_schema_files(tmp_path):
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "user.json").write_text('{"type": "object"}')
    schemas = read_schema_files(tmp_path / "schemas")
    assert "user.json" in schemas
    assert schemas["user.json"]["type"] == "object"

def test_validate_plan():
    plan = {
        "tasks": [
            {"description": "Export users", "status": "pending"}
        ],
        "format": "json"
    }
    schema = {
        "type": "object",
        "properties": {
            "tasks": {"type": "array"},
            "format": {"type": "string"}
        },
        "required": ["tasks", "format"]
    }
    assert validate_plan(plan, schema) is True
    # Invalid plan (missing tasks)
    bad_plan = {"format": "json"}
    assert not validate_plan(bad_plan, schema)
