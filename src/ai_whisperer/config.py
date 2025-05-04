import yaml
from pathlib import Path
from .exceptions import ConfigError

def load_config(config_path: str) -> dict:
    """
    Loads configuration from a YAML file.

    Args:
        config_path: The path to the configuration file.

    Returns:
        A dictionary containing the configuration.

    Raises:
        ConfigError: If the configuration file does not exist, is invalid
                     (e.g., not valid YAML, missing required keys), or cannot be read.
    """
    path = Path(config_path)
    if not path.is_file():
        # Raise ConfigError as expected by the test
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            # Handle empty file case (yaml.safe_load returns None)
            if config is None:
                config = {}
            if not isinstance(config, dict):
                raise ConfigError(f"Invalid configuration format in {config_path}. Expected a dictionary, got {type(config).__name__}.")
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML file {config_path}: {e}") from e
    except Exception as e: # Catch other potential file reading errors
        raise ConfigError(f"Error reading configuration file {config_path}: {e}") from e

    # --- Basic Validation ---
    # Check for essential top-level keys expected by the application core
    required_keys = ['openrouter', 'prompts']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys in {config_path}: {', '.join(missing_keys)}")

    # Check nested keys for openrouter
    openrouter_config = config.get('openrouter')
    if not isinstance(openrouter_config, dict):
         raise ConfigError(f"Invalid 'openrouter' section in {config_path}. Expected a dictionary.")

    required_openrouter_keys = ['api_key', 'model']
    missing_openrouter_keys = [key for key in required_openrouter_keys if key not in openrouter_config]
    if missing_openrouter_keys:
        raise ConfigError(f"Missing required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}")

    # Check prompts structure (basic check)
    prompts_config = config.get('prompts')
    if not isinstance(prompts_config, dict):
        raise ConfigError(f"Invalid 'prompts' section in {config_path}. Expected a dictionary.")
    if not prompts_config: # Ensure prompts dictionary is not empty if it exists
         raise ConfigError(f"'prompts' section in {config_path} cannot be empty.")

    return config
