# -*- coding: utf-8 -*-
"""Tests for the configuration loading functionality."""

import pytest
import yaml
import os  # Import os for monkeypatching environment variables
from pathlib import Path
from src.ai_whisperer.config import load_config, DEFAULT_OUTPUT_DIR, DEFAULT_SITE_URL, DEFAULT_APP_NAME
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
    'openrouter': {'api_key': 'dummy_key', 'model': 'test_model'},
    'prompts': {},
    'output_dir': '/tmp/aiw_test_output'
}

CONFIG_NOT_DICT = "- item1\n- item2"

CONFIG_MISSING_PROMPTS = {
    'openrouter': {'api_key': 'dummy_key', 'model': 'test_model'},
    'output_dir': '/tmp/aiw_test_output'
}

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

def test_load_config_success(create_test_config_file, monkeypatch): # Add monkeypatch
    """Tests loading a valid configuration file."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var
    config_path = create_test_config_file("valid_config.yaml", VALID_CONFIG_DATA)
    config = load_config(str(config_path))

    # Create expected config including defaults added by load_config
    expected_config = VALID_CONFIG_DATA.copy()
    # Ensure the expected key matches the data used to create the file
    expected_config['openrouter']['api_key'] = VALID_CONFIG_DATA['openrouter']['api_key']
    expected_config['openrouter']['site_url'] = DEFAULT_SITE_URL
    expected_config['openrouter']['app_name'] = DEFAULT_APP_NAME
    expected_config['output_dir'] = DEFAULT_OUTPUT_DIR
    expected_config['prompt_override_path'] = None

    assert config == expected_config # Compare against expected structure with defaults
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

def test_load_config_missing_nested_required_key(create_test_config_file, monkeypatch): # Add monkeypatch
    """Tests loading a config file missing a required nested key (api_key)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var
    config_path = create_test_config_file("missing_nested_key.yaml", CONFIG_MISSING_NESTED_KEY)
    expected_error_pattern = r"Missing required key 'api_key' in 'openrouter' section.*and OPENROUTER_API_KEY environment variable not set"
    with pytest.raises(ConfigError, match=expected_error_pattern):
        load_config(str(config_path))

def test_load_config_empty_file(create_test_config_file):
    """Tests loading an empty configuration file."""
    config_path = create_test_config_file("empty.yaml", "")
    with pytest.raises(ConfigError, match=r"Missing required configuration keys"):
        load_config(str(config_path))

def test_load_config_not_a_dictionary(create_test_config_file):
    """Tests loading a config file where the top level is not a dictionary."""
    config_path = create_test_config_file("not_dict.yaml", CONFIG_NOT_DICT)
    with pytest.raises(ConfigError, match=r"Invalid configuration format.*Expected a dictionary"):
        load_config(str(config_path))

def test_load_config_api_key_precedence(create_test_config_file, monkeypatch):
    """Tests API key loading precedence (Env Var > Config File) and missing key error."""
    env_api_key = "env_key_123"
    config_api_key = "config_key_456"

    # --- Case 1: API Key only in Environment Variable ---
    monkeypatch.setenv("OPENROUTER_API_KEY", env_api_key)
    config_data_no_key = {
        'openrouter': {'model': 'test_model'},
        'prompts': {'task_generation': 'prompt'}
    }
    config_path_no_key = create_test_config_file("config_no_key.yaml", config_data_no_key)
    config = load_config(str(config_path_no_key))
    assert config['openrouter']['api_key'] == env_api_key
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var

    # --- Case 2: API Key only in Config File ---
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var
    config_data_with_key = {
        'openrouter': {'api_key': config_api_key, 'model': 'test_model'},
        'prompts': {'task_generation': 'prompt'}
    }
    config_path_with_key = create_test_config_file("config_with_key.yaml", config_data_with_key)
    config = load_config(str(config_path_with_key))
    assert config['openrouter']['api_key'] == config_api_key

    # --- Case 3: API Key in Both Env Var and Config File (Env Var should win) ---
    monkeypatch.setenv("OPENROUTER_API_KEY", env_api_key)
    # Reread the config file that *does* have a key
    config_path_with_key_again = create_test_config_file("config_with_key_again.yaml", config_data_with_key)
    config = load_config(str(config_path_with_key_again))
    assert config['openrouter']['api_key'] == env_api_key # Env var takes precedence
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var

    # --- Case 4: API Key Missing in Both ---
    monkeypatch.setenv("OPENROUTER_API_KEY", "") # Explicitly clear env var
    # Reread the config file that does *not* have a key
    config_path_no_key_again = create_test_config_file("config_no_key_again.yaml", config_data_no_key)
    with pytest.raises(ConfigError, match=r"Missing required key 'api_key' in 'openrouter' section.*and OPENROUTER_API_KEY environment variable not set"):
        load_config(str(config_path_no_key_again))

def test_load_config_optional_keys(create_test_config_file):
    """Tests loading config with and without optional keys (site_url, app_name)."""
    # Config with optional keys provided
    config_data_with_optional = {
        'openrouter': {
            'api_key': 'test_key',
            'model': 'test_model',
            'site_url': 'https://mytestsite.com',
            'app_name': 'MyTestApp'
        },
        'prompts': {'task_generation': 'prompt'}
    }
    config_path_with = create_test_config_file("config_with_opt.yaml", config_data_with_optional)
    config = load_config(str(config_path_with))
    assert config['openrouter']['site_url'] == 'https://mytestsite.com'
    assert config['openrouter']['app_name'] == 'MyTestApp'

    # Config without optional keys (should use defaults)
    config_data_without_optional = {
        'openrouter': {
            'api_key': 'test_key',
            'model': 'test_model'
        },
        'prompts': {'task_generation': 'prompt'}
    }
    config_path_without = create_test_config_file("config_without_opt.yaml", config_data_without_optional)
    config = load_config(str(config_path_without))
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME

def test_load_config_general_optional_keys(create_test_config_file):
    """Tests loading config with and without general optional keys (output_dir, prompt_override_path)."""
    # Config with optional keys provided
    custom_output_dir = "./custom_output"
    custom_prompt_path = "./custom_prompt.md"
    config_data_with_optional = {
        'openrouter': {
            'api_key': 'test_key',
            'model': 'test_model'
        },
        'prompts': {'task_generation': 'prompt'},
        'output_dir': custom_output_dir,
        'prompt_override_path': custom_prompt_path
    }
    config_path_with = create_test_config_file("config_with_opt_gen.yaml", config_data_with_optional)
    config = load_config(str(config_path_with))
    assert config['output_dir'] == custom_output_dir
    assert config['prompt_override_path'] == custom_prompt_path

    # Config without optional keys (should use defaults)
    config_data_without_optional = {
        'openrouter': {
            'api_key': 'test_key',
            'model': 'test_model'
        },
        'prompts': {'task_generation': 'prompt'}
    }
    config_path_without = create_test_config_file("config_without_opt_gen.yaml", config_data_without_optional)
    config = load_config(str(config_path_without))
    assert config['output_dir'] == DEFAULT_OUTPUT_DIR
    assert config['prompt_override_path'] is None

def test_load_config_missing_prompts_section(create_test_config_file, monkeypatch):
    """Tests loading a config file missing the entire 'prompts' section."""
    # Ensure API key env var isn't interfering
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    config_path = create_test_config_file("missing_prompts.yaml", CONFIG_MISSING_PROMPTS)
    config = load_config(str(config_path))

    # Check that 'prompts' defaults to an empty dict
    assert 'prompts' in config
    assert config['prompts'] == {}
    # Check other defaults are still applied
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME
    assert config['output_dir'] == CONFIG_MISSING_PROMPTS['output_dir'] # Should use value from file
    assert config['prompt_override_path'] is None

def test_load_config_empty_prompts_section(create_test_config_file, monkeypatch):
    """Tests loading a config file with an empty 'prompts: {}' section."""
    # Ensure API key env var isn't interfering
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    config_path = create_test_config_file("empty_prompts.yaml", CONFIG_EMPTY_PROMPTS)

    # Load the config directly, no error expected
    config = load_config(str(config_path))

    # Check that 'prompts' is an empty dict as provided
    assert 'prompts' in config
    assert config['prompts'] == {}
    # Check other defaults are still applied
    assert config['openrouter']['site_url'] == DEFAULT_SITE_URL
    assert config['openrouter']['app_name'] == DEFAULT_APP_NAME
    assert config['output_dir'] == CONFIG_EMPTY_PROMPTS['output_dir'] # Should use value from file
    assert config['prompt_override_path'] is None
