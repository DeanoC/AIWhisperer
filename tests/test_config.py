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
)
from src.ai_whisperer.exceptions import ConfigError

# Helper function to read actual default prompt content (for comparison if needed, though config loads content now)
# This function is kept for potential future use or if specific tests need to verify default file content directly.
def _read_actual_default_prompt_content(prompt_relative_path):
    """Reads the content of a default prompt file relative to the project root."""
    try:
        project_root = Path(__file__).parent.parent # Assuming tests run from the root directory
        prompt_path = project_root / prompt_relative_path
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        pytest.fail(f"Could not read actual default prompt: {prompt_relative_path}")

# Define expected default prompt content by reading the actual files
# These are used to verify that load_config correctly loads the default content
ACTUAL_DEFAULT_ORCH_CONTENT = _read_actual_default_prompt_content("prompts/orchestrator_default.md")
ACTUAL_DEFAULT_SUBTASK_CONTENT = _read_actual_default_prompt_content("prompts/subtask_generator_default.md")

# --- Test Data ---
VALID_OPENROUTER_CONFIG_NO_KEY = {
    'model': 'test_model',
    'params': {'temperature': 0.7}
}

VALID_PROMPTS_CONFIG_PATHS = {
    'orchestrator': 'custom_orchestrator.md',
    'subtask_generator': 'custom_subtask.md'
}

VALID_CONFIG_DATA_NEW = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'task_prompts': VALID_PROMPTS_CONFIG_PATHS,
    'output_dir': '/custom/output'
}

CONFIG_MISSING_TASK_PROMPTS_SECTION = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'output_dir': '/custom/output'
}



CONFIG_EMPTY_TASK_PROMPTS = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'task_prompts': {},
    'output_dir': '/custom/output'
}

CONFIG_TASK_PROMPTS_NOT_DICT = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'task_prompts': 'not_a_dictionary'
}

CONFIG_WITH_OLD_PROMPT_OVERRIDE = {
    'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
    'task_prompts': {},
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

    # Create default prompt files relative to tmp_path, simulating project structure
    # These are needed so load_config can find them when testing default loading
    default_orch_rel_path = Path("prompts/orchestrator_default.md")
    default_subtask_rel_path = Path("prompts/subtask_generator_default.md")
    default_orch_content = ACTUAL_DEFAULT_ORCH_CONTENT # Use actual content for fixture
    default_subtask_content = ACTUAL_DEFAULT_SUBTASK_CONTENT # Use actual content for fixture
    _create_file(default_orch_rel_path, default_orch_content)
    _create_file(default_subtask_rel_path, default_subtask_content)
    default_prompt_contents[str(default_orch_rel_path)] = default_orch_content
    default_prompt_contents[str(default_subtask_rel_path)] = default_subtask_content

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
    custom_orch_path_str = VALID_PROMPTS_CONFIG_PATHS['orchestrator']
    custom_subtask_path_str = VALID_PROMPTS_CONFIG_PATHS['subtask_generator']
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

    assert 'task_prompts' in config
    assert config['task_prompts']['orchestrator'] == VALID_PROMPTS_CONFIG_PATHS['orchestrator']
    assert config['task_prompts']['subtask_generator'] == VALID_PROMPTS_CONFIG_PATHS['subtask_generator']

    assert 'prompt_override_path' not in config # Ensure old key is not present
    assert 'task_prompts_content' in config # Ensure new content key is present
    assert config['task_prompts_content']['orchestrator'] == custom_orch_content
    assert config['task_prompts_content']['subtask_generator'] == custom_subtask_content

def test_load_config_success_empty_task_prompts(create_test_files, monkeypatch):
    """Tests loading config with an empty task_prompts section."""
    _create_file, default_contents = create_test_files
    config_path = _create_file("config_empty_task_prompts.yaml", CONFIG_EMPTY_TASK_PROMPTS)

    mock_api_key = "env_key_for_empty_task_prompts"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))

    assert config['openrouter']['api_key'] == mock_api_key
    assert 'task_prompts' in config
    # Updated assertion to expect default tasks with None when input task_prompts is empty
    assert config['task_prompts'] == {'orchestrator': None, 'subtask_generator': None, 'refine_requirements': None}
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

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

def test_load_config_task_prompts_not_dict(create_test_files):
    """Tests loading config where 'task_prompts' is not a dictionary."""
    _create_file, _ = create_test_files
    config_path = _create_file("task_prompts_not_dict.yaml", CONFIG_TASK_PROMPTS_NOT_DICT)
    with pytest.raises(ConfigError, match=r"Invalid 'task_prompts' section.*Expected a dictionary"):
        load_config(str(config_path))

def test_load_config_missing_required_env_var_api_key(create_test_files, monkeypatch):
    """Tests ConfigError when OPENROUTER_API_KEY environment variable is not set."""
    _create_file, _ = create_test_files
    config_data = {'openrouter': {'model': 'test_model'}, 'prompts': {}}
    config_path = _create_file("missing_api_key.yaml", config_data)

    expected_error = r"Required environment variable OPENROUTER_API_KEY is not set"

    # Use patch.dict to temporarily remove the environment variable
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': ''}, clear=True):
        with pytest.raises(ConfigError, match=expected_error):
            load_config(str(config_path))

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
        'task_prompts': {}
    }
    config_path_with = _create_file("config_opt_or_with.yaml", config_data_with)
    config = load_config(str(config_path_with))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['site_url'] == 'site_url'
    assert config['openrouter']['app_name'] == 'app_name'
    assert 'task_prompts' in config and isinstance(config['task_prompts'], dict)

    config_data_without = {'openrouter': {'model': 'test_model'}, 'task_prompts': {}}
    config_path_without = _create_file("config_opt_or_without.yaml", config_data_without)
    config = load_config(str(config_path_without))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME
    assert 'task_prompts' in config and isinstance(config['task_prompts'], dict)

    # Test with task_prompts section missing entirely
    config_data_missing_section = {'openrouter': {'model': 'test_model'}}
    config_path_missing_section = _create_file("config_opt_or_missing_task_prompts.yaml", config_data_missing_section)
    config = load_config(str(config_path_missing_section))
    assert config['openrouter']['api_key'] == mock_api_key
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME
    # Updated assertion to expect default tasks with None when input task_prompts is missing
    assert 'task_prompts' in config and config['task_prompts'] == {'orchestrator': None, 'subtask_generator': None, 'refine_requirements': None}
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_optional_key_output_dir(create_test_files, monkeypatch):
    """Tests loading config with and without optional output_dir key."""
    _create_file, _ = create_test_files
    mock_api_key = "env_key_for_output_dir_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    custom_output = "./custom_out"
    config_data_with = {'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY, 'task_prompts': {}, 'output_dir': custom_output}
    config_path_with = _create_file("config_opt_out_with.yaml", config_data_with)
    config = load_config(str(config_path_with))
    assert config['output_dir'] == custom_output
    assert config['openrouter']['api_key'] == mock_api_key
    assert 'task_prompts' in config and isinstance(config['task_prompts'], dict) # Ensure task_prompts is present and a dict
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

    config_data_without = {'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY, 'task_prompts': {}}
    config_path_without = _create_file("config_opt_out_without.yaml", config_data_without)
    config = load_config(str(config_path_without))
    assert config['output_dir'] == DEFAULT_OUTPUT_DIR
    assert config['openrouter']['api_key'] == mock_api_key
    assert 'task_prompts' in config and isinstance(config['task_prompts'], dict) # Ensure task_prompts is present and a dict
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

    # Test with task_prompts section missing entirely
    config_data_missing_section = {'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY}
    config_path_missing_section = _create_file("config_opt_out_missing_task_prompts.yaml", config_data_missing_section)
    config = load_config(str(config_path_missing_section))
    assert config['output_dir'] == DEFAULT_OUTPUT_DIR
    assert config['openrouter']['api_key'] == mock_api_key
    # Updated assertion to expect default tasks with None when input task_prompts is missing
    assert 'task_prompts' in config and config['task_prompts'] == {'orchestrator': None, 'subtask_generator': None, 'refine_requirements': None}
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_ignores_old_prompt_override(create_test_files, monkeypatch):
    """Tests that the old top-level prompt_override_path is ignored."""
    _create_file, default_contents = create_test_files
    config_path = _create_file("config_old_override.yaml", CONFIG_WITH_OLD_PROMPT_OVERRIDE)

    mock_api_key = "env_key_for_old_override_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))
    assert config['openrouter']['api_key'] == mock_api_key
    # Assert that the old override path is ignored and task_prompts is empty as specified
    assert 'prompt_override_path' not in config
    # Updated assertion to expect default tasks with None when input task_prompts is empty
    assert config['task_prompts'] == {'orchestrator': None, 'subtask_generator': None, 'refine_requirements': None}
    assert 'task_prompts_content' in config # Ensure new content key is present
    # Updated assertion to check for actual default content
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_error_custom_prompt_not_found(create_test_files, monkeypatch):
    """Tests ConfigError when a specified custom prompt file is missing."""
    _create_file, _ = create_test_files
    missing_prompt_path_str = 'non_existent_prompt.md'
    config_data = {
        'openrouter': {'model': 'm'}, # Need model to pass initial validation
        'task_prompts': {'orchestrator': missing_prompt_path_str}
    }
    config_path = _create_file("config_missing_custom_prompt.yaml", config_data)

    mock_api_key = "env_key_for_prompt_error_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    expected_error_msg = r"Specified prompt file not found: .*non_existent_prompt.md \(relative to .*\)"
    with pytest.raises(ConfigError, match=expected_error_msg):
        load_config(str(config_path))

def test_load_config_success_default_prompts(create_test_files, monkeypatch):
    """Tests loading config where task_prompts specifies using default paths (None)."""
    _create_file, default_contents = create_test_files
    config_data = {
        'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
        'task_prompts': {
            'orchestrator': None, # Use default
            'subtask_generator': None # Use default
        },
        'output_dir': '/custom/output'
    }
    config_path = _create_file("config_default_prompts.yaml", config_data)

    mock_api_key = "env_key_for_default_prompts_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)
    config = load_config(str(config_path))

    assert config['openrouter']['api_key'] == mock_api_key
    assert config['output_dir'] == '/custom/output'
    assert 'task_prompts' in config
    assert config['task_prompts']['orchestrator'] is None
    assert config['task_prompts']['subtask_generator'] is None
    assert 'task_prompts_content' in config
    assert config['task_prompts_content']['orchestrator'] == ACTUAL_DEFAULT_ORCH_CONTENT
    assert config['task_prompts_content']['subtask_generator'] == ACTUAL_DEFAULT_SUBTASK_CONTENT

def test_load_config_invalid_prompt_path_type(create_test_files, monkeypatch):
    """Tests ConfigError when a prompt path value is not a string or None."""
    _create_file, _ = create_test_files
    config_data = {
        'openrouter': {'model': 'm'},
        'task_prompts': {'orchestrator': 123} # Invalid type
    }
    config_path = _create_file("config_invalid_prompt_type.yaml", config_data)

    mock_api_key = "env_key_for_invalid_prompt_type_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    expected_error_msg = r"Invalid prompt path for task 'orchestrator'.*Expected a string."
    with pytest.raises(ConfigError, match=expected_error_msg):
        load_config(str(config_path))

def test_load_config_missing_task_model_config(create_test_files, monkeypatch):
    """Tests ConfigError when a task with a prompt has no corresponding model config."""
    _create_file, default_contents = create_test_files
    _create_file("prompts/dummy_missing_model_prompt.md", "Dummy content for missing model test") # Create dummy prompt file
    config_data = {
        'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
        'task_prompts': {
            'orchestrator': None,
            'missing_model_task': 'prompts/dummy_missing_model_prompt.md' # Specify prompt path
        },
        'task_models': {
            'orchestrator': {'model': 'orch_model'}
        }
    }
    config_path = _create_file("config_missing_task_model.yaml", config_data)

    mock_api_key = "env_key_for_missing_model_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    # Assert that no ConfigError is raised and the config loads successfully
    config = load_config(str(config_path))

    # Assert that the fallback to the base openrouter model is applied
    assert 'task_model_configs' in config
    assert 'missing_model_task' in config['task_model_configs']
    assert config['task_model_configs']['missing_model_task']['model'] == VALID_OPENROUTER_CONFIG_NO_KEY['model']

def test_load_config_invalid_task_model_settings_type(create_test_files, monkeypatch):
    """Tests ConfigError when task model settings are not a dictionary."""
    _create_file, default_contents = create_test_files
    _create_file("prompts/missing_model_task_default.md", "Dummy content") # Create dummy prompt file
    config_data = {
        'openrouter': VALID_OPENROUTER_CONFIG_NO_KEY,
        'task_prompts': {
            'orchestrator': None,
        },
        'task_models': {
            'orchestrator': "not_a_dict" # Invalid type
        }
    }
    config_path = _create_file("config_invalid_task_model_type.yaml", config_data)

    mock_api_key = "env_key_for_invalid_task_model_type_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    expected_error_msg = r"Invalid model settings for task 'orchestrator'.*Expected a dictionary."
    with pytest.raises(ConfigError, match=expected_error_msg):
        load_config(str(config_path))

def test_load_config_missing_openrouter_model(create_test_files, monkeypatch):
    """Tests ConfigError when the base openrouter config is missing the 'model' key."""
    _create_file, default_contents = create_test_files
    config_data = {
        'openrouter': {'params': {'temp': 0.5}}, # Missing 'model' key
        'task_prompts': {}
    }
    config_path = _create_file("config_missing_base_model.yaml", config_data)

    mock_api_key = "env_key_for_missing_base_model_test"
    monkeypatch.setenv("OPENROUTER_API_KEY", mock_api_key)

    # Updated expected error message to match the task model config validation error
    expected_error_msg = r"Missing or empty required keys in model config for task 'orchestrator' after merging: model"
    with pytest.raises(ConfigError, match=expected_error_msg):
        load_config(str(config_path))
