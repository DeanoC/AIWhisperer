import yaml
from pathlib import Path
import os
from dotenv import load_dotenv # Import load_dotenv
from typing import Optional # Import Optional

from .exceptions import ConfigError

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000" # Or some generic placeholder
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"


def load_config(config_path: str) -> dict:
    """
    Loads configuration from a YAML file, validates required keys, and handles API key precedence.

    The function performs the following steps:
    1. Loads environment variables from a .env file (if present).
    2. Checks if the configuration file exists.
    3. Parses the YAML file.
    4. Validates the presence of top-level keys ('openrouter').
    5. Validates the structure of the 'openrouter' section.
    6. Determines the OpenRouter API key, prioritizing the 'OPENROUTER_API_KEY'
       environment variable over the 'api_key' in the config file.
    7. Adds default values for optional 'site_url', 'app_name', 'output_dir',
       and handles optional 'prompt_override_path'.
    8. Validates the presence and non-emptiness of required keys within 'openrouter'
       ('api_key', 'model').
    9. Ensures 'prompts' section exists, defaulting to an empty dictionary if missing.

    Args:
        config_path: The path to the configuration file.

    Returns:
        A dictionary containing the loaded and validated configuration.

    Raises:
        ConfigError: If the configuration file does not exist, is invalid YAML,
                     is missing required keys/sections, contains empty required values,
                     or if the API key is missing from both the config file and
                     the environment variable.
    """
    load_dotenv() # Load environment variables from .env file

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
    # 'prompts' is now optional
    required_keys = ['openrouter']
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys in {config_path}: {', '.join(missing_keys)}")

    # Check nested keys for openrouter
    openrouter_config = config.get('openrouter')
    if not isinstance(openrouter_config, dict):
         raise ConfigError(f"Invalid 'openrouter' section in {config_path}. Expected a dictionary.")

    # --- API Key Handling (Prioritize Environment Variable) ---
    # Check for api_key in config first, but prioritize environment variable
    api_key_from_env = os.getenv('OPENROUTER_API_KEY')
    api_key_from_config = openrouter_config.get('api_key')

    if api_key_from_env:
        # Use environment variable if available, overriding config file
        openrouter_config['api_key'] = api_key_from_env
        # Optional: Log that env var is being used
        # print("Using OpenRouter API key from environment variable.")
    elif not api_key_from_config:
        # If not in env and not in config, raise error
        raise ConfigError(f"Missing required key 'api_key' in 'openrouter' section of {config_path} and OPENROUTER_API_KEY environment variable not set.")
    # If only in config, it's already loaded, no action needed.

    # --- Load Optional Settings with Defaults ---
    # OpenRouter specific optional settings
    openrouter_config['site_url'] = openrouter_config.get('site_url', DEFAULT_SITE_URL)
    openrouter_config['app_name'] = openrouter_config.get('app_name', DEFAULT_APP_NAME)

    # General application optional settings (add them to the top-level config dict)
    config['output_dir'] = config.get('output_dir', DEFAULT_OUTPUT_DIR)
    config['prompt_override_path'] = config.get('prompt_override_path', None) # Default to None if not present

    # Ensure 'prompts' section exists, defaulting to empty dict if missing
    config.setdefault('prompts', {})
    # Validate that 'prompts' is a dictionary if it exists
    if not isinstance(config['prompts'], dict):
        raise ConfigError(f"Invalid 'prompts' section in {config_path}. Expected a dictionary, got {type(config['prompts']).__name__}.")

    # --- Continue Validation ---
    # Validate required keys within 'openrouter'
    required_openrouter_keys = ['api_key', 'model']
    missing_openrouter_keys = [key for key in required_openrouter_keys if key not in openrouter_config or not openrouter_config[key]]
    if missing_openrouter_keys:
        raise ConfigError(f"Missing or empty required keys in 'openrouter' section of {config_path}: {', '.join(missing_openrouter_keys)}")

    return config
