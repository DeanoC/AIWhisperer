#!/usr/bin/env python3
"""Test agent loading to debug the issue"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path
from ai_whisperer.services.agents.registry import AgentRegistry
from ai_whisperer.utils.path import PathManager

# Initialize PathManager
path_manager = PathManager.get_instance()
path_manager.initialize_with_project_json({"path": "/home/deano/projects/AIWhisperer"})
print(f"Project path: {path_manager.project_path}")

# Test agent registry
prompts_dir = path_manager.project_path / "prompts" / "agents"
print(f"Prompts dir: {prompts_dir}")
print(f"Prompts dir exists: {prompts_dir.exists()}")

# Initialize agent registry
registry = AgentRegistry(prompts_dir)

# List agents
agents = registry.list_agents()
print(f"\nLoaded agents:")
for agent in agents:
    print(f"  {agent.agent_id}: {agent.name}")