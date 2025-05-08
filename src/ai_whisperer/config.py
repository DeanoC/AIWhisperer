import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging # Import logging

logging.basicConfig(level=logging.DEBUG)

from .exceptions import ConfigError

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000"
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"
# Default tasks for which prompt content is loaded if not explicitly specified in the configuration.
# These tasks represent key functionalities of the application, such as orchestrating workflows,
# generating subtasks, and refining requirements. Default prompts for these tasks are located
# in the 'prompts/' directory and are loaded automatically if not overridden in the config.
DEFAULT_TASKS = ['orchestrator', 'subtask_generator', 'refine_requirements']

def _load_prompt_content(prompt_path_str: Optional[str], default_path_str: str, config_dir: Path) -> str:
    """Loads prompt content from a given path or its default.

    User-specified paths (prompt_path_str) are resolved relative to the config directory.
    Default paths (default_path_str) are resolved relative to the project root.
    """
    resolved_path: Optional[Path] = None
    error_msg: Optional[str] = None

    if prompt_path_str:
        # If a specific path is given, it MUST exist - relative to the config directory
        prompt_path = config_dir / prompt_path_str
        if prompt_path.is_file():
            resolved_path = prompt_path
        else:
            # Specified path not found, raise error immediately.
            error_msg = f"Specified prompt file not found: {prompt_path_str} (relative to {config_dir})"
            raise ConfigError(error_msg)
    else:
        # No specific path given, use the default - relative to the PROJECT ROOT, not config dir
        # Determine the project root directory (2 levels up from the source file)
        project_root = Path(__file__).parent.parent.parent
        default_path = project_root / default_path_str
        if default_path.is_file():
            resolved_path = default_path
        else:
            # Default path not found.
            error_msg = f"Default prompt file not found: {default_path_str} (relative to project root: {project_root})"
            raise ConfigError(error_msg)

    # This check should technically be redundant now if logic above is correct, but kept for safety.
    if not resolved_path:
         raise ConfigError(error_msg or "Could not determine prompt file path.") # Should not happen

    try:
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content
    except Exception as e:
        raise ConfigError(f"Error reading prompt file {resolved_path}: {e}") from e


def load_config(config_path: str, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file, validates required keys, handles API key precedence,
    and loads prompt file contents.

    Args:
        config_path: The path to the configuration file.
        env_vars: Optional dictionary of environment variables for testing purposes.
                  If provided, these override any environment variables loaded from .env file.

    Returns:
        A dictionary containing the loaded and validated configuration, including prompt content.

    Raises:
        ConfigError: If the configuration file does not exist, is invalid YAML,
                     is missing required keys/sections, contains empty required values,
                     if the API key is missing, or if prompt files cannot be loaded.
    """
    # Load .env file first (only if env_vars not provided)
    if env_vars is None:
        load_dotenv()
        env_vars = os.environ

    # --- Get API Key from Environment --- Required Early ---
    api_key_from_env = env_vars.get('OPENROUTER_API_KEY')
    if not api_key_from_env:
        raise ConfigError("Required environment variable OPENROUTER_API_KEY is not set.")

    # --- Load and Parse Config File ---
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    config_dir = path.parent  # Get the directory containing the config file

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise ConfigError(f"Invalid configuration format in {config_path}. Expected a dictionary, got {type(config).__name__}.")
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file {config_path}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Error reading configuration file {config_path}: {e}") from e

    # --- Basic Validation ---
    required_keys = ['openrouter']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys in {config_path}: {', '.join(missing_keys)}")

    openrouter_config = config.get('openrouter')
    if not isinstance(openrouter_config, dict):
        raise ConfigError(f"Invalid 'openrouter' section in {config_path}. Expected a dictionary.")

    # --- API Key Handling (Simplified) ---
    # Assign the key from environment (already validated)
    openrouter_config['api_key'] = api_key_from_env

    # --- Load Optional Settings with Defaults ---
    openrouter_config['site_url'] = openrouter_config.get('site_url', DEFAULT_SITE_URL)
    openrouter_config['app_name'] = openrouter_config.get('app_name', DEFAULT_APP_NAME)

    config['output_dir'] = config.get('output_dir', DEFAULT_OUTPUT_DIR)
    config.pop('prompt_override_path', None) # Remove old prompt override key - handled by new prompt loading

    # --- Process Task-Specific Settings (Models and Prompts) ---
    # Ensure task_models and task_prompts sections exist and are dictionaries
    task_models_config = config.get('task_models')
    if not isinstance(task_models_config, dict):
        if task_models_config is not None: # Only warn if the key exists but is wrong type
             logging.warning(f"'task_models' section in {config_path} is not a dictionary. Using empty dictionary.")
        config['task_models'] = {}
    else:
        config['task_models'] = task_models_config # Use the existing dictionary

    task_prompts_config = config.get('task_prompts')
    if not isinstance(task_prompts_config, dict):
        if task_prompts_config is not None: # Only warn if the key exists but is wrong type
             logging.warning(f"'task_prompts' section in {config_path} is not a dictionary. Using empty dictionary.")
        # Raise ConfigError if task_prompts is explicitly set but not a dictionary
        if 'task_prompts' in config and not isinstance(config['task_prompts'], dict):
             raise ConfigError(f"Invalid 'task_prompts' section in {config_path}. Expected a dictionary.")
    else:
        config['task_prompts'] = task_prompts_config # Use the existing dictionary


    config['task_prompts_content'] = {}
    config['task_model_configs'] = {}

    # Load prompt content for each task specified in task_prompts
    config_dir = path.parent # Get the directory containing the config file
    # Use config.get('task_prompts', {}) to safely iterate even if task_prompts is missing
    for task_name, prompt_path_str in config.get('task_prompts', {}).items():
        if not isinstance(prompt_path_str, (str, type(None))): # Allow None for default path
             raise ConfigError(f"Invalid prompt path for task '{task_name}' in {config_path}. Expected a string or null.")
        # Determine default prompt path based on task name
        default_prompt_path_str = f"prompts/{task_name}_default.md"
        config['task_prompts_content'][task_name] = _load_prompt_content(
            prompt_path_str, default_prompt_path_str, config_dir
        )

    # Load default prompts for known tasks if not explicitly specified
    default_tasks = DEFAULT_TASKS
    project_root = Path(__file__).parent.parent.parent
    for task_name in default_tasks:
        if task_name not in config['task_prompts_content']:
            default_prompt_path_str = f"prompts/{task_name}_default.md"
            default_path = project_root / default_prompt_path_str
            if default_path.is_file():
                try:
                    with open(default_path, 'r', encoding='utf-8') as f:
                        config['task_prompts_content'][task_name] = f.read()
                        # Also add to task_prompts with None to indicate default was used
                        if 'task_prompts' not in config or not isinstance(config['task_prompts'], dict):
                             config['task_prompts'] = {} # Ensure it's a dict if missing or wrong type
                        config['task_prompts'][task_name] = None
                except Exception as e:
                    logging.warning(f"Could not load default prompt for '{task_name}' from {default_path}: {e}")
            else:
                 logging.warning(f"Default prompt file not found for '{task_name}': {default_path}")

    # Determine model config for each task that has a prompt defined
    # If a task has a prompt, it must have a model config (either default or task-specific)
    for task_name in config['task_prompts_content'].keys():
        task_model_settings = config['task_models'].get(task_name, {})
        if not isinstance(task_model_settings, dict):
             # This check is already present, but ensure it's correctly placed after getting the value
             raise ConfigError(f"Invalid model settings for task '{task_name}' in {config_path}. Expected a dictionary.")

        # Merge task-specific settings with default openrouter settings
        # Task-specific settings override defaults
        merged_model_config = openrouter_config.copy() # Start with default openrouter config
        merged_model_config.update(task_model_settings) # Apply task-specific overrides

        # Ensure required keys are present after merging (at least 'model')
        required_task_model_keys = ['model']
        missing_task_model_keys = [key for key in required_task_model_keys if not merged_model_config.get(key)]
        if missing_task_model_keys:
             raise ConfigError(f"Missing or empty required keys in model config for task '{task_name}' after merging: {', '.join(missing_task_model_keys)}")

        config['task_model_configs'][task_name] = merged_model_config

    # --- Final Validation ---
    # Validate only 'model' is present in openrouter config, as api_key is handled via env var
    # This check is now less critical as task_model_configs are validated, but keep for base config
    required_openrouter_keys = ['model']  # Only model is required *in the file*
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}")
    logging.debug(f"Loaded config: {config}")
    return config
