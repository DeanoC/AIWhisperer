import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any

from .exceptions import ConfigError

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000"
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"
DEFAULT_ORCHESTRATOR_PROMPT_PATH = "prompts/orchestrator_default.md"
DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH = "prompts/subtask_generator_default.md"


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
            return f.read()
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
            if config is None:
                config = {}
            if not isinstance(config, dict):
                raise ConfigError(f"Invalid configuration format in {config_path}. Expected a dictionary, got {type(config).__name__}.")
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file {config_path}: {e}") from e
    except Exception as e:
        raise ConfigError(f"Error reading configuration file {config_path}: {e}") from e

    # --- Basic Validation ---
    required_keys = ['openrouter', 'prompts']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys in {config_path}: {', '.join(missing_keys)}")

    openrouter_config = config.get('openrouter')
    if not isinstance(openrouter_config, dict):
        raise ConfigError(f"Invalid 'openrouter' section in {config_path}. Expected a dictionary.")

    prompts_config = config.get('prompts')
    if not isinstance(prompts_config, dict):
        raise ConfigError(f"Invalid 'prompts' section in {config_path}. Expected a dictionary, got {type(prompts_config).__name__}.")

    # --- API Key Handling (Simplified) ---
    # Assign the key from environment (already validated)
    openrouter_config['api_key'] = api_key_from_env

    # --- Load Optional Settings with Defaults ---
    openrouter_config['site_url'] = openrouter_config.get('site_url', DEFAULT_SITE_URL)
    openrouter_config['app_name'] = openrouter_config.get('app_name', DEFAULT_APP_NAME)

    config['output_dir'] = config.get('output_dir', DEFAULT_OUTPUT_DIR)
    config.pop('prompt_override_path', None)

    # --- Load Prompt Contents ---
    orchestrator_prompt_path = prompts_config.get('orchestrator_prompt_path')
    prompts_config['orchestrator_prompt_content'] = _load_prompt_content(
        orchestrator_prompt_path, DEFAULT_ORCHESTRATOR_PROMPT_PATH, config_dir  # Pass config_dir
    )

    subtask_generator_prompt_path = prompts_config.get('subtask_generator_prompt_path')
    prompts_config['subtask_generator_prompt_content'] = _load_prompt_content(
        subtask_generator_prompt_path, DEFAULT_SUBTASK_GENERATOR_PROMPT_PATH, config_dir  # Pass config_dir
    )

    # --- Final Validation (Simplified) ---
    # Validate only 'model' is present in openrouter config, as api_key is handled via env var
    required_openrouter_keys = ['model']  # Only model is required *in the file*
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}")

    return config
