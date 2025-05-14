import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging  # Import logging

logging.basicConfig(level=logging.DEBUG)

from .exceptions import ConfigError
from .path_management import PathManager # Import PathManager

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000"
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"
# Default tasks for which prompt content is loaded if not explicitly specified in the configuration.
# These tasks represent key functionalities of the application, such as initial_plan workflows,
# generating subtasks, and refining requirements. Default prompts for these tasks are located
# in the 'prompts/' directory and are loaded automatically if not overridden in the config.
DEFAULT_TASKS = ["initial_plan", "subtask_generator", "refine_requirements"]


def _load_prompt_content(
    prompt_path_str: Optional[str], default_path_str: str, config_dir: Path, project_dir: Optional[Path] = None
) -> str:
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
        # No specific path given, use the default - try relative to PathManager's project_path first
        path_manager = PathManager.get_instance()
        project_path_from_manager = Path(path_manager.project_path)
        default_path_project_root = project_path_from_manager / default_path_str
        if default_path_project_root.is_file():
            resolved_path = default_path_project_root
        else:
            # Default path not found relative to PathManager's project_path, try relative to the CONFIG directory as a fallback
            default_path_config_dir = config_dir / default_path_str
            if default_path_config_dir.is_file():
                resolved_path = default_path_config_dir
            else:
                # Default path not found in either location.
                error_msg = f"Default prompt file not found: {default_path_str} (relative to PathManager project_path: {project_path_from_manager} or config dir: {config_dir})"
                raise ConfigError(error_msg)

    # This check should technically be redundant now if logic above is correct, but kept for safety.
    if not resolved_path:
        raise ConfigError(error_msg or "Could not determine prompt file path.")  # Should not happen

    try:
        with open(resolved_path, "r", encoding="utf-8") as f:
            content = f.read()
            return content
    except Exception as e:
        raise ConfigError(f"Error reading prompt file {resolved_path}: {e}") from e


def _load_default_prompt_content(task_name: str, config_dir: Path) -> str:
    """
    Loads the default prompt content for a given task name.
    """
    if task_name not in DEFAULT_TASKS:
        raise ConfigError(f"No default prompt available for unknown task: {task_name}")
    default_path_str = f"prompts/{task_name}_default.md"
    return _load_prompt_content(
        prompt_path_str=None,
        default_path_str=default_path_str,
        config_dir=config_dir
    )

class TaskPromptsContentOnDemand(dict):
    """
    Dictionary-like object that loads default prompt content on demand for known tasks.
    Also supports test-specific prompts, falling back to the global runner default if not found.
    """
    def __init__(self, initial, config_dir, global_runner_default_loader=None):
        super().__init__(initial)
        self._config_dir = config_dir
        self._global_runner_default_loader = global_runner_default_loader

    def __getitem__(self, key):
        value = super().get(key, None)
        if value is None and key in DEFAULT_TASKS:
            # Try to load the default prompt content on demand
            try:
                value = _load_default_prompt_content(key, self._config_dir)
                self[key] = value  # Cache it
            except Exception:
                value = None
        # For test-specific prompts, fallback to global runner default if not found
        if value is None and self._global_runner_default_loader is not None:
            try:
                value = self._global_runner_default_loader()
                self[key] = value  # Cache it
            except Exception:
                value = None
        return value

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except Exception:
            return default


def load_config(config_path: str, cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file, validates required keys, handles API key precedence,
    and loads prompt file contents. Initializes the PathManager with config and CLI values.

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

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                raise ConfigError(
                    f"Invalid configuration format in {config_path}. Expected a dictionary, got {type(config).__name__}."
                )
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
    tasks_to_process = list(task_prompts.keys())

    config["task_prompts_content"] = {}
    config["task_model_configs"] = {}  # <-- Ensure this dict exists before use

    # Load prompt content for each task specified in task_prompts
    for task_name in tasks_to_process:
        prompt_path_str = config["task_prompts"][task_name]
        # Only load if a specific prompt_path_str is provided
        if prompt_path_str is None:
            # If prompt_path_str is None, content is None, default will be loaded on demand
            config["task_prompts_content"][task_name] = None
        elif isinstance(prompt_path_str, str):
            config["task_prompts_content"][task_name] = _load_prompt_content(
                prompt_path_str, "", config_dir # Pass empty string for default_path_str as it's not used here
            )
        else:
            # If prompt_path_str is not a string, raise an error
            raise ConfigError(f"Invalid prompt path for task '{task_name}'. Expected a string.")

    # Helper to load the global runner default prompt on demand
    def _global_runner_default_loader():
        content = config.get("global_runner_default_prompt_content")
        if content is not None:
            return content
        # Try to load it if not already loaded
        default_global_prompt_path_str = "prompts/global_runner_fallback_default.md"
        path_manager = PathManager.get_instance()
        resolved_default_path = path_manager.resolve_path(default_global_prompt_path_str)
        default_prompt_file_path = Path(resolved_default_path)
        if default_prompt_file_path.is_file():
            with open(default_prompt_file_path, "r", encoding="utf-8") as f:
                content = f.read()
            config["global_runner_default_prompt_content"] = content
            return content
        return None

    # Replace the dict with the on-demand loader, passing the global fallback loader
    config["task_prompts_content"] = TaskPromptsContentOnDemand(
        config["task_prompts_content"], config_dir, global_runner_default_loader=_global_runner_default_loader
    )

    # --- New: Load Runner Agent Type Defaults ---
    # Keep this section as it loads specific runner agent defaults, not general task defaults
    if "prompts" in config and isinstance(config["prompts"], dict):
        prompts_config = config["prompts"]

        if "agent_type_defaults" in prompts_config and isinstance(prompts_config["agent_type_defaults"], dict):
            for agent_type, prompt_path_str in prompts_config["agent_type_defaults"].items():
                if isinstance(prompt_path_str, str):
                    try:
                        # Use PathManager to resolve the path
                        resolved_prompt_path = path_manager.resolve_path(prompt_path_str)
                        prompt_file_path = Path(resolved_prompt_path)
                        if prompt_file_path.is_file():
                            with open(prompt_file_path, "r", encoding="utf-8") as f:
                                config["runner_agent_type_prompts_content"][agent_type] = f.read()
                            logging.debug(
                                f"Loaded runner agent type default prompt for '{agent_type}': {config['runner_agent_type_prompts_content'][agent_type][:100]}..."
                            )
                        else:
                            logging.warning(
                                f"Runner agent type default prompt file not found: {prompt_path_str} (resolved to {resolved_prompt_path}) for agent type '{agent_type}'."
                            )
                    except Exception as e:
                        logging.error(
                            f"Error reading runner agent type default prompt file {prompt_path_str} for '{agent_type}': {e}"
                        )
                else:
                    logging.warning(f"Invalid prompt path for runner agent type '{agent_type}': must be a string.")

        # --- New: Load Global Runner Default Prompt ---
        # Keep this section as it loads a specific global default, not general task defaults
        if "global_runner_default_prompt_path" in prompts_config and isinstance(
            prompts_config["global_runner_default_prompt_path"], str
        ):
            try:
                global_prompt_path_str = prompts_config["global_runner_default_prompt_path"]
                # Use PathManager to resolve the path
                resolved_prompt_path = path_manager.resolve_path(global_prompt_path_str)
                prompt_file_path = Path(resolved_prompt_path)
                if prompt_file_path.is_file():
                    with open(prompt_file_path, "r", encoding="utf-8") as f:
                        config["global_runner_default_prompt_content"] = f.read()
                    logging.debug(
                        f"Loaded global runner default prompt: {config['global_runner_default_prompt_content'][:100]}..."
                    )
                else:
                    logging.warning(f"Global runner default prompt file not found: {global_prompt_path_str} (resolved to {resolved_prompt_path}).")
            except Exception as e:
                logging.error(f"Error reading global runner default prompt file {global_prompt_path_str}: {e}")

        # --- New: Load Default Global Runner Prompt if not specified ---
        # Keep this section as it loads a specific global default, not general task defaults
        if getattr(config, "global_runner_default_prompt_content", None) is None:
            default_global_prompt_path_str = "prompts/global_runner_fallback_default.md"
            try:
                # Use PathManager to resolve the default path
                resolved_default_path = path_manager.resolve_path(default_global_prompt_path_str)
                default_prompt_file_path = Path(resolved_default_path)

                if default_prompt_file_path.is_file():
                     with open(default_prompt_file_path, "r", encoding="utf-8") as f:
                        config["global_runner_default_prompt_content"] = f.read()
                     logging.debug(f"Loaded default global runner prompt.")
                else:
                    logging.warning(f"Default global runner prompt file not found: {default_global_prompt_path_str} (resolved to {resolved_default_path}).")

            except Exception as e:
                logging.error(f"Unexpected error loading default global runner prompt: {e}")


    # Determine model config for each task that has a prompt defined
    for task_name in config["task_prompts_content"].keys():
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

    required_openrouter_keys = ["model"]
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(
            f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}"
        )
    return config
