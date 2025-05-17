import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging  # Import logging

logging.basicConfig(level=logging.DEBUG)

from .exceptions import ConfigError
from ai_whisperer.path_management import PathManager

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000"
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"
# Default tasks for which prompt content is loaded if not explicitly specified in the configuration.
# These tasks represent key functionalities of the application, such as initial_plan workflows,
# generating subtasks, and refining requirements. Default prompts for these tasks are located
# in the 'prompts/' directory and are loaded automatically if not overridden in the config.
DEFAULT_TASKS = ["initial_plan", "subtask_generator", "refine_requirements"]


def load_config(config_path: str, cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file, validates required keys, handles API key precedence,
    and initializes the PathManager with config and CLI values.

    Args:
        config_path: The path to the configuration file.
        cli_args: Optional dictionary of parsed CLI arguments.

    Returns:
        A dictionary containing the loaded and validated configuration, including prompt content.

    Raises:
        ConfigError: If the configuration file does not exist, is invalid YAML,
                     is missing required keys/sections, contains empty required values,
                     if the API key is missing, or if prompt files cannot be loaded.
    """
    # Load .env file first
    load_dotenv()

    # --- Get API Key from Environment --- Required Early ---
    api_key_from_env = os.getenv("OPENROUTER_API_KEY")
    if not api_key_from_env:
        raise ConfigError("Required environment variable OPENROUTER_API_KEY is not set.")

    # --- Load and Parse Config File ---
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    config_dir = path.parent  # Get the directory containing the config file

    # --- Calculate config file hash early ---
    from .utils import calculate_sha256
    try:
        config_file_hash = calculate_sha256(path)
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise ConfigError(
                    f"Invalid configuration format in {config_path}. Expected a dictionary, got {type(config).__name__}."
                )
        # Store the config file hash in the config dict for downstream use
        config["config_file_hash"] = config_file_hash
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file {config_path}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Error reading configuration file {config_path}: {e}") from e

    # --- Basic Validation ---
    required_keys = ["openrouter"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys in {config_path}: {', '.join(missing_keys)}")

    openrouter_config = config.get("openrouter")
    if not isinstance(openrouter_config, dict):
        raise ConfigError(f"Invalid 'openrouter' section in {config_path}. Expected a dictionary.")

    # --- Validate required keys in openrouter section ---
    required_openrouter_keys = ["model"]
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(
            f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}"
        )

    # --- API Key Handling (Simplified) ---
    # Assign the key from environment (already validated)
    openrouter_config["api_key"] = api_key_from_env

    # --- Load Optional Settings with Defaults ---
    openrouter_config["site_url"] = openrouter_config.get("site_url", DEFAULT_SITE_URL)
    openrouter_config["app_name"] = openrouter_config.get("app_name", DEFAULT_APP_NAME)

    # Extract path-related configurations
    path_config = {
        'project_path': config.get('project_path'),
        'output_path': config.get('output_dir', DEFAULT_OUTPUT_DIR),  # Map output_dir from config to output_path in PathManager
        'workspace_path': config.get('workspace_path'),
        # app_path is determined by the application's location and should not be configurable
    }

    # Initialize PathManager with config values and CLI arguments
    path_manager = PathManager.get_instance()
    # Pass both config_values and cli_args to initialize
    # Note: app_path is not passed here as it's determined internally by PathManager
    path_manager.initialize(config_values=path_config, cli_args=cli_args)

    # Remove individual path keys from the main config dict after initializing PathManager
    config.pop("app_path", None)
    config.pop("project_path", None)
    config.pop("output_dir", None)
    config.pop("workspace_path", None)

    # --- Process Task-Specific Settings (Models and Prompts) ---
    # Ensure task_models and task_prompts sections exist and are dictionaries
    task_models_config = config.get("task_models")
    if not isinstance(task_models_config, dict):
        if task_models_config is not None:  # Only warn if the key exists but is wrong type
            logging.warning(f"'task_models' section in {config_path} is not a dictionary. Using empty dictionary.")
        config["task_models"] = {}
    else:
        config["task_models"] = task_models_config  # Use the existing dictionary

    task_prompts_config = config.get("task_prompts")
    if task_prompts_config is None:
        # If missing, fill with default keys set to None
        config["task_prompts"] = {k: None for k in DEFAULT_TASKS}
    elif isinstance(task_prompts_config, dict):
        # If present but not all keys, fill missing with None
        for k in DEFAULT_TASKS:
            if k not in task_prompts_config:
                task_prompts_config[k] = None
        config["task_prompts"] = task_prompts_config
    else:
        raise ConfigError("Invalid 'task_prompts' section. Expected a dictionary.")

    # Determine which tasks to process (only those explicitly in task_prompts)
    task_prompts = config.get("task_prompts", {})
    if not isinstance(task_prompts, dict):
        raise ConfigError("Invalid 'task_prompts' section. Expected a dictionary.")

    # Only use the keys present in the config's task_prompts

    # --- Process Task-Specific Settings (Models) ---
    # Ensure task_models section exists and is a dictionary
    task_models_config = config.get("task_models")
    if not isinstance(task_models_config, dict):
        if task_models_config is not None:  # Only warn if the key exists but is wrong type
            logging.warning(f"'task_models' section in {config_path} is not a dictionary. Using empty dictionary.")
        config["task_models"] = {}
    else:
        config["task_models"] = task_models_config  # Use the existing dictionary

    # Ensure task_prompts section exists and is a dictionary (but don't load content here)
    task_prompts_config = config.get("task_prompts")
    if task_prompts_config is None:
        config["task_prompts"] = {k: None for k in DEFAULT_TASKS}
    elif isinstance(task_prompts_config, dict):
        for k in DEFAULT_TASKS:
            if k not in task_prompts_config:
                task_prompts_config[k] = None
        config["task_prompts"] = task_prompts_config
    else:
        raise ConfigError("Invalid 'task_prompts' section. Expected a dictionary.")

    config["task_model_configs"] = {}  # Ensure this dict exists before use

    # Determine model config for each task that has a prompt defined in task_prompts
    # We iterate over task_prompts keys to know which tasks are relevant
    tasks_to_process = list(config["task_prompts"].keys())

    for task_name in tasks_to_process:
        task_model_settings = config["task_models"].get(task_name, {})
        if not isinstance(task_model_settings, dict):
            raise ConfigError(f"Invalid model settings for task '{task_name}' in {config_path}. Expected a dictionary.")

        merged_model_config = openrouter_config.copy()
        merged_model_config.update(task_model_settings)

        required_task_model_keys = ["model"]
        missing_task_model_keys = [key for key in required_task_model_keys if not merged_model_config.get(key)]
        if missing_task_model_keys:
            raise ConfigError(
                f"Missing or empty required keys in model config for task '{task_name}' after merging: {', '.join(missing_task_model_keys)}"
            )

        config["task_model_configs"][task_name] = merged_model_config

    # Ensure 'task_prompts_content' key is always present (empty dict if not loaded here)
    if "task_prompts_content" not in config:
        config["task_prompts_content"] = {}

    required_openrouter_keys = ["model"]
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(
            f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}"
        )
    return config
