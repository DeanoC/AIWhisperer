import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging  # Import logging

logging.basicConfig(level=logging.DEBUG)

from .exceptions import ConfigError

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
        # No specific path given, use the default - relative to the CONFIG directory first
        default_path_config_dir = config_dir / default_path_str
        if default_path_config_dir.is_file():
            resolved_path = default_path_config_dir
        else:
            # Default path not found relative to config dir, try relative to project root as a fallback
            project_root = Path(__file__).parent.parent.parent
            default_path_project_root = project_root / default_path_str
            if default_path_project_root.is_file():
                resolved_path = default_path_project_root
            else:
                # Default path not found in either location.
                error_msg = f"Default prompt file not found: {default_path_str} (relative to config dir: {config_dir} or project root: {project_root})"
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


def load_config(config_path: str) -> Dict[str, Any]:
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

    # --- API Key Handling (Simplified) ---
    # Assign the key from environment (already validated)
    openrouter_config["api_key"] = api_key_from_env

    # --- Load Optional Settings with Defaults ---
    openrouter_config["site_url"] = openrouter_config.get("site_url", DEFAULT_SITE_URL)
    openrouter_config["app_name"] = openrouter_config.get("app_name", DEFAULT_APP_NAME)

    config["output_dir"] = config.get("output_dir", DEFAULT_OUTPUT_DIR)
    config.pop("prompt_override_path", None)  # Remove old prompt override key - handled by new prompt loading

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
    if not isinstance(task_prompts_config, dict):
        if task_prompts_config is not None:  # Only warn if the key exists but is wrong type
            logging.warning(f"'task_prompts' section in {config_path} is not a dictionary. Using empty dictionary.")
        # Raise ConfigError if task_prompts is explicitly set but not a dictionary
        if "task_prompts" in config and not isinstance(config["task_prompts"], dict):
            raise ConfigError(f"Invalid 'task_prompts' section in {config_path}. Expected a dictionary.")
    else:
        config["task_prompts"] = task_prompts_config  # Use the existing dictionary

    config["task_prompts_content"] = {}
    config["task_model_configs"] = {}
    config["runner_agent_type_prompts_content"] = {}  # New: For runner agent defaults
    config["global_runner_default_prompt_content"] = None  # New: For global runner default

    # Load prompt content for each task specified in task_prompts (Existing logic)
    config_dir = path.parent  # Get the directory containing the config file
    # Use config.get('task_prompts', {}) to safely iterate even if task_prompts is missing
    for task_name, prompt_path_str in config.get("task_prompts", {}).items():
        if not isinstance(prompt_path_str, (str, type(None))):  # Allow None for default path
            raise ConfigError(
                f"Invalid prompt path for task '{task_name}' in {config_path}. Expected a string or null."
            )
        # Determine default prompt path based on task name
        default_prompt_path_str = f"prompts/{task_name}_default.md"
        config["task_prompts_content"][task_name] = _load_prompt_content(
            prompt_path_str, default_prompt_path_str, config_dir
        )

    # Load default prompts for known tasks if not explicitly specified (Existing logic)
    default_tasks = DEFAULT_TASKS
    project_root = Path(__file__).parent.parent.parent
    for task_name in default_tasks:
        if task_name not in config["task_prompts_content"]:
            default_prompt_path_str = f"prompts/{task_name}_default.md"
            try:
                config["task_prompts_content"][task_name] = _load_prompt_content(
                    None, default_prompt_path_str, config_dir, project_dir=project_root  # Pass project_root as fallback
                )
                # Also add to task_prompts with None to indicate default was used
                if "task_prompts" not in config or not isinstance(config["task_prompts"], dict):
                    config["task_prompts"] = {}  # Ensure it's a dict if missing or wrong type
                config["task_prompts"][task_name] = None
            except ConfigError as e:
                logging.warning(f"Could not load default prompt for '{task_name}': {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading default prompt for '{task_name}': {e}")

    # --- New: Load Runner Agent Type Defaults ---
    if "prompts" in config and isinstance(config["prompts"], dict):
        prompts_config = config["prompts"]

        if "agent_type_defaults" in prompts_config and isinstance(prompts_config["agent_type_defaults"], dict):
            for agent_type, prompt_path_str in prompts_config["agent_type_defaults"].items():
                if isinstance(prompt_path_str, str):
                    try:
                        # Try to load from config directory first
                        prompt_file_path = config_dir / prompt_path_str
                        if prompt_file_path.is_file():
                            with open(prompt_file_path, "r", encoding="utf-8") as f:
                                config["runner_agent_type_prompts_content"][agent_type] = f.read()
                            logging.debug(
                                f"Loaded runner agent type default prompt for '{agent_type}': {config['runner_agent_type_prompts_content'][agent_type][:100]}..."
                            )  # Add logging
                        else:
                            # Try project root as fallback
                            project_root = Path(__file__).parent.parent.parent
                            prompt_file_path = project_root / prompt_path_str
                            if prompt_file_path.is_file():
                                with open(prompt_file_path, "r", encoding="utf-8") as f:
                                    config["runner_agent_type_prompts_content"][agent_type] = f.read()
                                logging.debug(
                                    f"Loaded runner agent type default prompt for '{agent_type}': {config['runner_agent_type_prompts_content'][agent_type][:100]}..."
                                )  # Add logging
                            else:
                                logging.warning(
                                    f"Runner agent type default prompt file not found: {prompt_path_str} for agent type '{agent_type}'."
                                )
                    except Exception as e:
                        logging.error(
                            f"Error reading runner agent type default prompt file {prompt_path_str} for '{agent_type}': {e}"
                        )
                else:
                    logging.warning(f"Invalid prompt path for runner agent type '{agent_type}': must be a string.")

        # --- New: Load Global Runner Default Prompt ---
        if "global_runner_default_prompt_path" in prompts_config and isinstance(
            prompts_config["global_runner_default_prompt_path"], str
        ):
            try:
                global_prompt_path_str = prompts_config["global_runner_default_prompt_path"]
                # Try to load from config directory first
                prompt_file_path = config_dir / global_prompt_path_str
                if prompt_file_path.is_file():
                    with open(prompt_file_path, "r", encoding="utf-8") as f:
                        config["global_runner_default_prompt_content"] = f.read()
                    logging.debug(
                        f"Loaded global runner default prompt: {config['global_runner_default_prompt_content'][:100]}..."
                    )  # Add logging
                else:
                    # Try project root as fallback
                    project_root = Path(__file__).parent.parent.parent
                    prompt_file_path = project_root / global_prompt_path_str
                    if prompt_file_path.is_file():
                        with open(prompt_file_path, "r", encoding="utf-8") as f:
                            config["global_runner_default_prompt_content"] = f.read()
                        logging.debug(
                            f"Loaded global runner default prompt: {config['global_runner_default_prompt_content'][:100]}..."
                        )  # Add logging
                    else:
                        logging.warning(f"Global runner default prompt file not found: {global_prompt_path_str}.")
            except Exception as e:
                logging.error(f"Error reading global runner default prompt file {global_prompt_path_str}: {e}")

        # --- New: Load Default Global Runner Prompt if not specified ---
        if config["global_runner_default_prompt_content"] is None:
            project_root = Path(__file__).parent.parent.parent
            default_global_prompt_path_str = "prompts/global_runner_fallback_default.md"
            try:
                config["global_runner_default_prompt_content"] = _load_prompt_content(
                    None,
                    default_global_prompt_path_str,
                    config_dir,
                    project_dir=project_root,  # Pass project_root as fallback
                )
                logging.debug(f"Loaded default global runner prompt.")
            except ConfigError as e:
                logging.warning(f"Could not load default global runner prompt: {e}")
            except Exception as e:
                logging.error(f"Unexpected error loading default global runner prompt: {e}")

    # Determine model config for each task that has a prompt defined (Existing logic)
    # If a task has a prompt, it must have a model config (either default or task-specific)
    for task_name in config["task_prompts_content"].keys():
        task_model_settings = config["task_models"].get(task_name, {})
        if not isinstance(task_model_settings, dict):
            # This check is already present, but ensure it's correctly placed after getting the value
            raise ConfigError(f"Invalid model settings for task '{task_name}' in {config_path}. Expected a dictionary.")

        # Merge task-specific settings with default openrouter settings
        # Task-specific settings override defaults
        merged_model_config = openrouter_config.copy()  # Start with default openrouter config
        merged_model_config.update(task_model_settings)  # Apply task-specific overrides

        # Ensure required keys are present after merging (at least 'model')
        required_task_model_keys = ["model"]
        missing_task_model_keys = [key for key in required_task_model_keys if not merged_model_config.get(key)]
        if missing_task_model_keys:
            raise ConfigError(
                f"Missing or empty required keys in model config for task '{task_name}' after merging: {', '.join(missing_task_model_keys)}"
            )

        config["task_model_configs"][task_name] = merged_model_config

    # --- Final Validation --- (Existing logic)
    # Validate only 'model' is present in openrouter config, as api_key is handled via env var
    # This check is now less critical as task_model_configs are validated, but keep for base config
    required_openrouter_keys = ["model"]  # Only model is required *in the file*
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(
            f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}"
        )
    logging.debug(f"Loaded config: {config}")
    return config
