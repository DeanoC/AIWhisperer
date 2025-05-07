# -*- coding: utf-8 -*-
"""Tests for the configuration loading functionality."""

import pytest
import json
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import logging

from src.ai_whisperer.config import (
    load_config,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SITE_URL,
    DEFAULT_APP_NAME,
    DEFAULT_ORCHESTRATOR_PROMPT_PATH,
    DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH
)
from src.ai_whisperer.exceptions import ConfigError

# Helper function to read actual default prompt content
def _read_actual_default_prompt(prompt_path):
    try:
        # Assuming tests run from the root directory
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        # Fallback or error if running from unexpected location
        # This might need adjustment based on test execution context
        pytest.fail(f"Could not read actual default prompt: {prompt_path}")

ACTUAL_DEFAULT_ORCH_CONTENT = _read_actual_default_prompt(DEFAULT_ORCHESTRATOR_PROMPT_PATH)
ACTUAL_DEFAULT_SUBTASK_CONTENT = _read_actual_default_prompt(DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH)

# --- Test Data ---
VALID_OPENROUTER_CONFIG_NO_KEY = {
    'model': 'test_model',
    'params': {'temperature': 0.7}
}

VALID_PROMPTS_CONFIG_PATHS = {
    'orchestrator_prompt_path': 'custom_orchestrator.md',
    'subtask_generator_prompt_path': 'custom_subtask.md'
}

VALID_CONFIG_DATA_NEW = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'prompts': VALID_PROMPTS_CONFIG_PATHS,
    'output_dir': '/custom/output'
}

CONFIG_MISSING_PROMPT_PATHS = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'prompts': {},
    'output_dir': '/custom/output'
}

CONFIG_MISSING_PROMPTS_SECTION = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'output_dir': '/custom/output'
}

CONFIG_PROMPTS_NOT_DICT = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'prompts': 'not_a_dictionary'
}

CONFIG_WITH_OLD_PROMPT_OVERRIDE = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'prompts': {},
    'prompt_override_path': 'old_override.md'
}

INVALID_JSON_CONTENT = ": invalid_json : :"
CONFIG_NOT_DICT = "- item1\n- item2"

# --- Fixtures ---

@pytest.fixture
def create_test_files(tmp_path):
    """Fixture to create temporary config and prompt files for tests."""
    files_created = {}
    default_prompt_contents = {}

    def _create_file(filename, content, is_json=False):
        # Convert Path to string if needed
        if isinstance(filename, Path):
            filename = str(filename)

        # Replace .json extension with .yaml if present
        if isinstance(filename, str) and filename.endswith('.json'):
            filename = filename.replace('.json', '.yaml')

        file_path = tmp_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, dict):
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(content, f, default_flow_style=False)
        else:
            file_path.write_text(str(content), encoding='utf-8')

        files_created[filename] = file_path
        return file_path

    # Create default prompt files relative to tmp_path
    default_orch_rel_path = Path(DEFAULT_ORCHESTRATOR_PROMPT_PATH)
    default_subtask_rel_path = Path(DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH)
    default_orch_content = "Default Orchestrator Content - From Fixture"
    default_subtask_content = "Default Subtask Generator Content - From Fixture"
    _create_file(default_orch_rel_path, default_orch_content)
    _create_file(default_subtask_rel_path, default_subtask_content)
    default_prompt_contents[DEFAULT_ORCHESTRATOR_PROMPT_PATH] = default_orch_content
    default_prompt_contents[DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH] = default_subtask_content

    return _create_file, default_prompt_contents

@pytest.fixture(autouse=True)
@patch('src.ai_whisperer.config.load_dotenv') # Mock load_dotenv for all tests in this module
def mock_load_dotenv(mock_dotenv, monkeypatch):
    """Fixture to mock load_dotenv and manage environment variables."""
    # Mock load_dotenv to do nothing
    mock_dotenv.return_value = None

    # Store the original API key but don't remove it by default
    # Individual tests that need to test missing API key should explicitly delete it
    original_value = os.environ.get("OPENROUTER_API_KEY")

    # Set a default API key if none exists to prevent tests from failing
    if not original_value:
        monkeypatch.setenv("OPENROUTER_API_KEY", "default-test-key")

    yield mock_dotenv # Yield the mock if needed, though usually not necessary

    # Restore original value after test
    if original_value is not None:
        monkeypatch.setenv("OPENROUTER_API_KEY", original_value)
    else:
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

# --- Test Cases ---

def test_load_config_success_new_prompts(create_test_files, monkeypatch):
    """Tests loading valid config with new prompt path structure."""
    _create_file, _ = create_test_files
    custom_orch_content = "Custom Orchestrator Content"
    custom_subtask_content = "Custom Subtask Content"
    custom_orch_path_str = VALID_PROMPTS_CONFIG_PATHS['orchestrator_prompt_path']
    custom_subtask_path_str = VALID_PROMPTS_CONFIG_PATHS['subtask_generator_prompt_path']
    _create_file(custom_orch_path_str, custom_orch_content)
    _create_file(custom_subtask_path_str, custom_subtask_content)

    config_path = _create_file("valid_config_new.yaml", VALID_CONFIG_DATA_NEW)

    mock_api_key = "env_key_for_success_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))

    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['model'] == VALID_OPENROUTER_CONFIG_NO_KEY['model']
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME
    assert config['output_dir'] == VALID_CONFIG_DATA_NEW['output_dir']

    assert 'prompts' in config
    assert config['prompts']['orchestrator_prompt_path'] == VALID_PROMPTS_CONFIG_PATHS['orchestrator_prompt_path']
    assert config['prompts']['subtask_generator_prompt_path'] == VALID_PROMPTS_CONFIG_PATHS['subtask_generator_prompt_path']
    assert config['prompts']['orchestrator_prompt_content'] == custom_orch_content
    assert config['prompts']['subtask_generator_prompt_content'] == custom_subtask_content

    assert 'prompt_override_path' not in config

def test_load_config_success_default_prompts(create_test_files, monkeypatch):
    """Tests loading config using default prompt paths when keys are missing."""
    _create_file, default_contents = create_test_files
    config_path = _create_file("config_missing_paths.yaml", CONFIG_MISSING_PROMPT_PATHS)

    mock_api_key = "env_key_for_default_prompts"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))

    assert config['openrouter']['api_key'] == mock_api_key
    assert 'prompts' in config
    assert config['prompts'].get('orchestrator_prompt_path') is None
    assert config['prompts'].get('subtask_generator_prompt_path') is None
    assert config['prompts']['orchestrator_prompt_content'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['prompts']['subtask_generator_prompt_content'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_file_not_found(tmp_path):
    """Tests loading a non-existent configuration file."""
    non_existent_file = tmp_path / "non_existent.yaml"
    with pytest.raises(ConfigError, match=r"Configuration file not found"):
        load_config(str(non_existent_file))

def test_load_config_invalid_yaml(create_test_files):
    """Tests loading a file with invalid YAML syntax."""
    _create_file, _ = create_test_files
    config_path = _create_file("invalid.yaml", INVALID_JSON_CONTENT)
    with pytest.raises(ConfigError, match=r"Error parsing YAML file"):
        load_config(str(config_path))

def test_load_config_missing_required_section_prompts(create_test_files):
    """Tests loading config missing the required 'prompts' section."""
    _create_file, _ = create_test_files
    config_path = _create_file("missing_prompts_section.yaml", CONFIG_MISSING_PROMPTS_SECTION)
    with pytest.raises(ConfigError, match=r"Missing required configuration keys.*prompts"):
        load_config(str(config_path))

def test_load_config_prompts_not_dict(create_test_files):
    """Tests loading config where 'prompts' is not a dictionary."""
    _create_file, _ = create_test_files
    config_path = _create_file("prompts_not_dict.yaml", CONFIG_PROMPTS_NOT_DICT)
    with pytest.raises(ConfigError, match=r"Invalid 'prompts' section.*Expected a dictionary"):
        load_config(str(config_path))

def test_load_config_missing_required_env_var_api_key(create_test_files):
    """Tests ConfigError when OPENROUTER_API_KEY environment variable is not set."""
    _create_file, _ = create_test_files
    config_data = {'openrouter': {'model': 'test_model'}, 'prompts': {}}
    config_path = _create_file("missing_api_key.yaml", config_data)

    expected_error = r"Required environment variable OPENROUTER_API_KEY is not set"

    # Pass an empty env_vars dict to simulate missing environment variables
    empty_env_vars = {}

    with pytest.raises(ConfigError, match=expected_error):
        load_config(str(config_path), env_vars=empty_env_vars)

def test_load_config_empty_file(create_test_files):
    """Tests loading an empty configuration file."""
    _create_file, _ = create_test_files
    config_path = _create_file("empty.yaml", "")
    with pytest.raises(ConfigError, match=r"Invalid configuration format|Error reading configuration file"):
        load_config(str(config_path))

def test_load_config_not_a_dictionary(create_test_files):
    """Tests loading a config file where the top level is not a dictionary."""
    _create_file, _ = create_test_files
    config_path = _create_file("not_dict.yaml", CONFIG_NOT_DICT)
    with pytest.raises(ConfigError, match=r"Invalid configuration format"):
        load_config(str(config_path))

def test_load_config_optional_keys_openrouter(create_test_files, monkeypatch):
    """Tests loading config with and without optional openrouter keys."""
    _create_file, _ = create_test_files
    mock_api_key = "env_key_for_optional_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    config_data_with = {
        'openrouter': {'model': 'test_model', 'site_url': 'site_url', 'app_name': 'app_name'},
        'prompts': {}
    }
    config_path_with = _create_file("config_opt_or_with.yaml", config_data_with)
    config = load_config(str(config_path_with))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['site_url'] == 'site_url'
    assert config['openrouter']['app_name'] == 'app_name'

    config_data_without = {'openrouter': {'model': 'test_model'}, 'prompts': {}}
    config_path_without = _create_file("config_opt_or_without.yaml", config_data_without)
    config = load_config(str(config_path_without))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME

def test_load_config_optional_key_output_dir(create_test_files, monkeypatch):
    """Tests loading config with and without optional output_dir key."""
    _create_file, _ = create_test_files
    mock_api_key = "env_key_for_output_dir_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    custom_output = "./custom_out"
    config_data_with = {'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY, 'prompts': {}, 'output_dir': custom_output}
    config_path_with = _create_file("config_opt_out_with.yaml", config_data_with)
    config = load_config(str(config_path_with))
    assert config['output_dir'] == custom_output
    assert config['openrouter']['api_key'] == mock_api_key

    config_data_without = {'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY, 'prompts': {}}
    config_path_without = _create_file("config_opt_out_without.yaml", config_data_without)
    config = load_config(str(config_path_without))
    assert config['output_dir'] == DEFAULT_OUTPUT_DIR
    assert config['openrouter']['api_key'] == mock_api_key

def test_load_config_ignores_old_prompt_override(create_test_files, monkeypatch):
    """Tests that the old top-level prompt_override_path is ignored."""
    _create_file, default_contents = create_test_files
    config_path = _create_file("config_old_override.yaml", CONFIG_WITH_OLD_PROMPT_OVERRIDE)

    mock_api_key = "env_key_for_old_override_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['prompts']['orchestrator_prompt_content'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['prompts']['subtask_generator_prompt_content'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_error_custom_prompt_not_found(create_test_files, monkeypatch):
    """Tests ConfigError when a specified custom prompt file is missing."""
    _create_file, _ = create_test_files
    missing_prompt_path_str = 'non_existent_prompt.md'
    config_data = {
        'openrouter': {'model': 'm'}, # Need model to pass initial validation
        'prompts': {'orchestrator_prompt_path': missing_prompt_path_str}
    }
    config_path = _create_file("config_missing_custom_prompt.yaml", config_data)

    mock_api_key = "env_key_for_prompt_error_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    expected_error_msg = f"Specified prompt file not found: {missing_prompt_path_str}"
    with pytest.raises(ConfigError, match=expected_error_msg):
        load_config(str(config_path))

def test_load_config_error_default_prompt_not_found(create_test_files, monkeypatch):
    """Tests ConfigError when a default prompt file is missing and not overridden."""
    _create_file, _ = create_test_files

    # Mock DEFAULT_ORCHESTRATOR_PROMPT_PATH to point to a non-existent file
    non_existent_path = 'non_existent_prompt_file.md'
    with patch('src.ai_whisperer.config.DEFAULT_ORCHESTRATOR_PROMPT_PATH', non_existent_path):
        config_path = _create_file("config_missing_paths_for_default_err.yaml", CONFIG_MISSING_PROMPT_PATHS)

        mock_api_key = "env_key_for_default_prompt_error"
        monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

        expected_error_msg = f"Default prompt file not found: {non_existent_path}"
        with pytest.raises(ConfigError, match=expected_error_msg):
            load_config(str(config_path))
