import os
import json
from typing import Dict, Any

def analyze_workspace(workspace_path) -> list:
    """Return a flat list of files and folders in the workspace."""
    structure = []
    for root, dirs, files in os.walk(workspace_path):
        rel_root = os.path.relpath(root, workspace_path)
        if rel_root == ".":
            rel_root = ""
        for d in dirs:
            structure.append(os.path.join(rel_root, d) + "/")
        for f in files:
            structure.append(os.path.join(rel_root, f))
    return structure

def read_schema_files(schema_dir) -> Dict[str, Any]:
    """Read all JSON schema files in a directory."""
    schemas = {}
    for fname in os.listdir(schema_dir):
        if fname.endswith('.json'):
            with open(os.path.join(schema_dir, fname), 'r', encoding='utf-8') as f:
                schemas[fname] = json.load(f)
    return schemas

def validate_plan(plan: dict, schema: dict) -> bool:
    """Validate a plan dict against a JSON schema (very basic)."""
    # Only check required keys for now
    required = schema.get('required', [])
    for key in required:
        if key not in plan:
            return False
    return True
