import pytest
import yaml
import json  # Added for compatibility with existing code
from pathlib import Path
import tempfile
import os
from unittest.mock import patch

from src.ai_whisperer.config import load_config, _load_prompt_content
from src.ai_whisperer.exceptions import ConfigError


# Helper function to create a temporary config file with the given content
def create_temp_config(content, is_json=False):  # Keep parameter for backward compatibility
    temp_dir = tempfile.gettempdir()
    config_path = Path(temp_dir) / "test_config.yaml"  # Use .yaml extension

    # Always write as YAML, regardless of is_json parameter
    with open(config_path, "w", encoding="utf-8") as f:
        if isinstance(content, dict):
            yaml.dump(content, f, default_flow_style=False)
        else:
            f.write(content)

    return str(config_path)


# Mock environment variables for testing
@pytest.fixture
def mock_env_vars():
    return {"OPENROUTER_API_KEY": "test-api-key"}


# Test case 1: Valid configuration with models defined for both 'Subtask Generation' and 'Initial Plan'
@patch("src.ai_whisperer.config._load_prompt_content", return_value="mocked prompt content")
def test_valid_task_models_config(mock_load_prompt, mock_env_vars, monkeypatch):
    config_content = """
# --- OpenRouter API Settings ---
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

# --- Task-Specific Model Settings ---
task_models:
  "Subtask Generation":
    provider: "openrouter"
    model: "anthropic/claude-3-opus"
    params:
      temperature: 0.5
      max_tokens: 4096
  "Initial Plan":
    provider: "openrouter"
    model: "mistralai/mistral-large"
    params:
      temperature: 0.8
      max_tokens: 8192

# --- Other Application Settings ---
output_dir: "./output/"
"""

    config_path = create_temp_config(config_content)

    try:
        # Mock the prompt loading to avoid file not found errors
        # This is a simplified approach - in a real test, you might want to mock the file system
        # Use monkeypatch to set environment variables for this test
        monkeypatch.setenv("OPENROUTER_API_KEY", mock_env_vars["OPENROUTER_API_KEY"])
        config = load_config(config_path)

        # Verify the task_models section exists and has the expected structure
        assert "task_models" in config, "task_models section is missing"
        task_models = config["task_models"]

        # Verify Subtask Generation configuration
        assert "Subtask Generation" in task_models, "Subtask Generation task is missing"
        subtask_gen = task_models["Subtask Generation"]
        assert subtask_gen["provider"] == "openrouter", "Provider should be 'openrouter'"
        assert subtask_gen["model"] == "anthropic/claude-3-opus", "Model is incorrect"
        assert subtask_gen["params"]["temperature"] == 0.5, "Temperature is incorrect"
        assert subtask_gen["params"]["max_tokens"] == 4096, "Max tokens is incorrect"

        # Verify Initial Plan configuration
        assert "initial_plan" in task_models, "Initial Plan task is missing"
        initial_plan = task_models["initial_plan"]
        assert initial_plan["provider"] == "openrouter", "Provider should be 'openrouter'"
        assert initial_plan["model"] == "mistralai/mistral-large", "Model is incorrect"
        assert initial_plan["params"]["temperature"] == 0.8, "Temperature is incorrect"
        assert initial_plan["params"]["max_tokens"] == 8192, "Max tokens is incorrect"

    finally:
        # Clean up the temporary file
        if os.path.exists(config_path):
            os.remove(config_path)


# Test case 2: Configuration with missing task-specific model definitions
@patch("src.ai_whisperer.config._load_prompt_content", return_value="mocked prompt content")
def test_missing_task_models_config(mock_load_prompt, mock_env_vars, monkeypatch):
    config_content = """
# --- OpenRouter API Settings ---
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

# --- Task-Specific Model Settings ---
task_models:
  # Missing 'Subtask Generation' and 'Initial Plan' tasks
  "subtask_generation": {
    "model": "anthropic/claude-3-opus",
    "params": {
      "temperature": 0.5,
      "max_tokens": 4096
    }
  },
  "initial_plan": {
    "model": "mistralai/mistral-large",
    "params": {
      "temperature": 0.8,
      "max_tokens": 8192
    }
  }

# --- Other Application Settings ---
output_dir: "./output/"
"""

    config_path = create_temp_config(config_content)

    try:
        # The config should load successfully even without task-specific models
        # Use monkeypatch to set environment variables for this test
        monkeypatch.setenv("OPENROUTER_API_KEY", mock_env_vars["OPENROUTER_API_KEY"])
        config = load_config(config_path)

        # Verify the task_models section exists and is an empty dictionary
        assert "task_models" in config, "task_models section is missing"
        assert config["task_models"] == {}, "task_models should be an empty dictionary"

    finally:
        # Clean up the temporary file
        if os.path.exists(config_path):
            os.remove(config_path)


# Test case 3: Configuration with invalid model definitions
@patch("src.ai_whisperer.config._load_prompt_content", return_value="mocked prompt content")
def test_invalid_task_model_definition(mock_load_prompt, mock_env_vars, monkeypatch):
    config_content = """
# --- OpenRouter API Settings ---
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

# --- Task-Specific Model Settings ---
task_models:
  "subtask_generation":
    # Missing 'provider' field
    model: "anthropic/claude-3-opus"
    params:
      temperature: 0.5
      max_tokens: 4096
  "initial_plan":
    provider: "openrouter"
    # Missing 'model' field
    params:
      temperature: 0.8
      max_tokens: 8192

# --- Other Application Settings ---
output_dir: "./output/"
"""

    config_path = create_temp_config(config_content)

    try:
        # The config should load successfully, but we'll validate the task models separately
        # Use monkeypatch to set environment variables for this test
        monkeypatch.setenv("OPENROUTER_API_KEY", mock_env_vars["OPENROUTER_API_KEY"])
        config = load_config(config_path)

        # Verify the task_models section exists
        assert "task_models" in config, "task_models section is missing"
        task_models = config["task_models"]

        # Verify Subtask Generation configuration is invalid (missing provider)
        assert "Subtask Generation" in task_models, "Subtask Generation task is missing"
        subtask_gen = task_models["Subtask Generation"]
        assert "provider" not in subtask_gen, "Provider should be missing"

        # Verify Initial Plan configuration is invalid (missing model)
        assert "initial_plan" in task_models, "Initial Plan task is missing"
        initial_plan = task_models["initial_plan"]
        assert "model" not in initial_plan, "Model should be missing"

    finally:
        # Clean up the temporary file
        if os.path.exists(config_path):
            os.remove(config_path)


# Test case 4: Configuration with unexpected keys or incorrect data types
@patch("src.ai_whisperer.config._load_prompt_content", return_value="mocked prompt content")
def test_unexpected_keys_in_task_models(mock_load_prompt, mock_env_vars, monkeypatch):
    config_content = """
# --- OpenRouter API Settings ---
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

# --- Task-Specific Model Settings ---
task_models:
  "subtask_generation":
    provider: "openrouter"
    model: "anthropic/claude-3-opus"
    params:
      temperature: 0.5
      max_tokens: 4096
    unexpected_key: "unexpected_value"  # Unexpected key
  "initial_plan":
    provider: 123  # Incorrect data type (should be string)
    model: ["mistralai/mistral-large"]  # Incorrect data type (should be string)
    params:
      temperature: "0.8"  # Incorrect data type (should be float)
      max_tokens: "8192"  # Incorrect data type (should be int)

# --- Other Application Settings ---
output_dir: "./output/"
"""

    config_path = create_temp_config(config_content)

    try:
        # The config should load successfully, but we'll check for unexpected keys and types
        # Use monkeypatch to set environment variables for this test
        monkeypatch.setenv("OPENROUTER_API_KEY", mock_env_vars["OPENROUTER_API_KEY"])
        config = load_config(config_path)

        # Verify the task_models section exists
        assert "task_models" in config, "task_models section is missing"
        task_models = config["task_models"]

        # Verify Subtask Generation configuration has unexpected key
        assert "Subtask Generation" in task_models, "Subtask Generation task is missing"
        subtask_gen = task_models["Subtask Generation"]
        assert "unexpected_key" in subtask_gen, "Unexpected key is missing"
        assert subtask_gen["unexpected_key"] == "unexpected_value", "Unexpected value is incorrect"

        # Verify Initial Plan configuration has incorrect data types
        assert "initial_plan" in task_models, "Initial Plan task is missing"
        initial_plan = task_models["initial_plan"]
        assert initial_plan["provider"] == 123, "Provider should be an integer (incorrect type)"
        assert isinstance(initial_plan["model"], list), "Model should be a list (incorrect type)"
        assert initial_plan["params"]["temperature"] == "0.8", "Temperature should be a string (incorrect type)"
        assert initial_plan["params"]["max_tokens"] == "8192", "Max tokens should be a string (incorrect type)"

    finally:
        # Clean up the temporary file
        if os.path.exists(config_path):
            os.remove(config_path)
