"""
Shared fixtures for Debbie agent configuration tests.
"""

import pytest
import yaml
import os
from pathlib import Path

from ai_whisperer.services.agents.registry import Agent


@pytest.fixture
def agents_config():
    """Load agents configuration from YAML"""
    # Try multiple paths to find the config file
    possible_paths = [
        Path("config/agents/agents.yaml"),  # From project root
        Path(__file__).parent.parent.parent.parent / "config" / "agents" / "agents.yaml",  # Relative to test file
        Path(os.getcwd()) / "config" / "agents" / "agents.yaml",  # From current directory
    ]
    
    for config_path in possible_paths:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
    
    # If not found, return a mock config for testing
    return {
        'agents': {
            'd': {
                'name': 'Debbie the Debugger',
                'role': 'debugging_assistant, batch_processor',
                'description': 'Intelligent debugging companion and batch script processor for AIWhisperer',
                'tool_tags': ['debugging', 'monitoring', 'testing', 'analysis', 'filesystem', 'command', 'batch'],
                'prompt_file': 'debbie_debugger.prompt.md',
                'context_sources': ['session_history', 'error_logs', 'performance_metrics', 'workspace_structure', 'batch_scripts']
            }
        }
    }


@pytest.fixture
def debbie_config(agents_config):
    """Get Debbie's configuration from the agents config"""
    return agents_config['agents'].get('d')


@pytest.fixture
def debbie_agent(debbie_config):
    """Create Debbie agent from config"""
    if not debbie_config:
        return None
    return Agent(
        agent_id='d',
        name=debbie_config['name'],
        role=debbie_config['role'],
        description=debbie_config['description'],
        tool_tags=debbie_config.get('tool_tags', []),
        prompt_file=debbie_config['prompt_file'],
        context_sources=debbie_config.get('context_sources', []),
        color=debbie_config.get('color', '#888888'),
        icon=debbie_config.get('icon', '🤖'),
        tool_sets=debbie_config.get('tool_sets'),
        allow_tools=debbie_config.get('allow_tools'),
        deny_tools=debbie_config.get('deny_tools'),
        continuation_config=debbie_config.get('continuation_config')
    )