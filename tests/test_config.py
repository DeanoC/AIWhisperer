# -*- coding: utf-8 -*-
"""Tests for the configuration loading functionality."""

import pytest
import yaml
from pathlib import Path
from src.ai_whisperer.config import load_config
from src.ai_whisperer.exceptions import ConfigError

# Define valid and invalid config data structures for reuse
VALID_CONFIG_DATA = {
    'openrouter': {
        'api_key': 'test_api_key',
        'model': 'test_model',
        'params': {'temperature': 0.7}
    },
    'prompts': {
        'task_generation': 'Generate tasks based on: {requirements}'
    }
}

INVALID_YAML_CONTENT = ": invalid_yaml : :"

CONFIG_MISSING_TOP_KEY = {
    # 'openrouter': { ... }, # Missing openrouter
    'prompts': {
        'task_generation': 'Generate tasks based on: {requirements}'
    }
}

CONFIG_MISSING_NESTED_KEY = {
    'openrouter': {
        # 'api_key': 'test_api_key', # Missing api_key
        'model': 'test_model'
    },
    'prompts': {
        'task_generation': 'Generate tasks based on: {requirements}'
    }
}

CONFIG_EMPTY_PROMPTS = {
    'openrouter': {
        'api_key': 'test_api_key',
        'model': 'test_model'
    },
    'prompts': {}
}

CONFIG_NOT_DICT = "- item1\n- item2"

@pytest.fixture
def create_test_config_file(tmp_path):
    """Fixture to create temporary config files for tests."""
    files_created = []
    def _create_file(filename, content):
        file_path = tmp_path / filename
        if isinstance(content, dict):
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(content, f)
        else:
            file_path.write_text(content, encoding='utf-8')
        files_created.append(file_path)
        return file_path
    yield _create_file
    # Cleanup can be added here if needed, though tmp_path handles it

# --- Test Cases ---

def test_load_config_success(create_test_config_file):
    """Tests loading a valid configuration file."""
    config_path = create_test_config_file("valid_config.yaml", VALID_CONFIG_DATA)
    config = load_config(str(config_path))
    assert config == VALID_CONFIG_DATA
    assert config['openrouter']['api_key'] == 'test_api_key'
    assert 'task_generation' in config['prompts']

def test_load_config_file_not_found(tmp_path):
    """Tests loading a non-existent configuration file."""
    non_existent_file = tmp_path / "non_existent.yaml"
    with pytest.raises(ConfigError, match=r"Configuration file not found"):
        load_config(str(non_existent_file))

def test_load_config_invalid_yaml(create_test_config_file):
    """Tests loading a file with invalid YAML syntax."""
    config_path = create_test_config_file("invalid.yaml", INVALID_YAML_CONTENT)
    with pytest.raises(ConfigError, match=r"Error parsing YAML file"):
        load_config(str(config_path))

def test_load_config_missing_required_key(create_test_config_file):
    """Tests loading a config file missing a required top-level key."""
    config_path = create_test_config_file("missing_key.yaml", CONFIG_MISSING_TOP_KEY)
    with pytest.raises(ConfigError, match=r"Missing required configuration keys.*openrouter"):
        load_config(str(config_path))

def test_load_config_missing_nested_required_key(create_test_config_file):
    """Tests loading a config file missing a required nested key."""
    config_path = create_test_config_file("missing_nested_key.yaml", CONFIG_MISSING_NESTED_KEY)
    with pytest.raises(ConfigError, match=r"Missing required keys in 'openrouter' section.*api_key"):
        load_config(str(config_path))

def test_load_config_empty_file(create_test_config_file):
    """Tests loading an empty configuration file."""
    config_path = create_test_config_file("empty.yaml", "")
    # Expecting missing keys error because the loaded dict will be empty
    with pytest.raises(ConfigError, match=r"Missing required configuration keys"):
        load_config(str(config_path))

def test_load_config_empty_prompts(create_test_config_file):
    """Tests loading a config file with an empty prompts dictionary."""
    config_path = create_test_config_file("empty_prompts.yaml", CONFIG_EMPTY_PROMPTS)
    with pytest.raises(ConfigError, match=r"'prompts' section .* cannot be empty"):
        load_config(str(config_path))

def test_load_config_not_a_dictionary(create_test_config_file):
    """Tests loading a config file where the top level is not a dictionary."""
    config_path = create_test_config_file("not_dict.yaml", CONFIG_NOT_DICT)
    with pytest.raises(ConfigError, match=r"Invalid configuration format.*Expected a dictionary"):
        load_config(str(config_path))
