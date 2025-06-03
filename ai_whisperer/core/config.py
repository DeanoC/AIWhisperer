"""
Module: ai_whisperer/config_hierarchical.py
Purpose: Hierarchical configuration management with environment-specific overrides

This module integrates the new hierarchical configuration system with the existing
AIWhisperer configuration interface. It supports:
- Base configurations from config/main.yaml
- Environment-specific overrides (development, test, production)
- Local overrides (gitignored)
- Backward compatibility with existing config.py interface

Key Components:
- HierarchicalConfigLoader: New configuration loading system
- load_config(): Updated interface with hierarchical support
- load_config_legacy(): Backward compatibility for old config files

Usage:
    config = load_config('config.yaml')  # Legacy mode
    config = load_config(environment='development')  # Hierarchical mode

Dependencies:
- scripts.hierarchical_config_loader: Core hierarchical loading logic
- ai_whisperer.exceptions: Configuration error handling
- ai_whisperer.path_management: Path management integration

Related:
- See CONFIG_CONSOLIDATION_COMPLETE.md for migration details
- See config/ directory for new hierarchical structure
"""

import yaml
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional, Dict, Any
import logging
import sys
# Add scripts directory to path to import hierarchical_config_loader
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from hierarchical_config_loader import HierarchicalConfigLoader
from ai_whisperer.core.exceptions import ConfigError
from ai_whisperer.utils.path import PathManager

logger = logging.getLogger(__name__)

# Default values for optional config settings
DEFAULT_SITE_URL = "http://localhost:8000"
DEFAULT_APP_NAME = "AIWhisperer"
DEFAULT_OUTPUT_DIR = "./output/"
DEFAULT_TASKS = ["initial_plan", "subtask_generator", "refine_requirements"]

def load_config(config_path: Optional[str] = None, 
               cli_args: Optional[Dict[str, Any]] = None,
               environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads configuration with support for both legacy and hierarchical modes.
    
    Args:
        config_path: Path to legacy config file (for backward compatibility)
        cli_args: Optional dictionary of parsed CLI arguments
        environment: Environment name for hierarchical loading ('development', 'test', 'production')
    
    Returns:
        A dictionary containing the loaded and validated configuration
        
    Raises:
        ConfigError: If configuration loading or validation fails
    """
    # Load .env file first, with error handling for CI/test environments
    try:
        load_dotenv()
        # Debug: Check if API key is loaded from environment
        api_key = os.getenv('OPENROUTER_API_KEY')
        if api_key:
            logger.debug(f"API key loaded from environment: {api_key[:10]}... (length: {len(api_key)})")
        else:
            logger.debug("No API key found in environment")
    except IOError as e:
        # In CI or test environments, the starting path might not exist
        logger.debug(f"Could not load .env file: {e}")
    
    # Determine loading mode
    if config_path and not environment:
        # Legacy mode - use specified config file
        logger.info(f"Loading configuration in legacy mode from: {config_path}")
        return load_config_legacy(config_path, cli_args)
    elif environment or not config_path:
        # Hierarchical mode - use new config structure
        env = environment or os.getenv('AIWHISPERER_ENV', 'development')
        logger.info(f"Loading configuration in hierarchical mode for environment: {env}")
        return load_config_hierarchical(env, cli_args)
    else:
        raise ConfigError("Must specify either config_path OR environment, not both")

def load_config_hierarchical(environment: str = 'development', 
                           cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load configuration using the new hierarchical structure.
    
    Args:
        environment: Environment name ('development', 'test', 'production')
        cli_args: Optional dictionary of parsed CLI arguments
        
    Returns:
        Merged configuration dictionary
        
    Raises:
        ConfigError: If configuration loading fails
    """
    try:
        # Initialize hierarchical config loader
        project_root = Path(__file__).parent.parent
        config_dir = project_root / "config"
        
        if not config_dir.exists():
            raise ConfigError(f"Configuration directory not found: {config_dir}")
        
        loader = HierarchicalConfigLoader(config_dir)
        config = loader.load_config(environment)
        
        # Validate and process the loaded configuration
        config = _validate_and_process_config(config, cli_args)
        
        logger.info(f"Successfully loaded hierarchical configuration for environment: {environment}")
        return config
        
    except Exception as e:
        raise ConfigError(f"Failed to load hierarchical configuration: {e}") from e

def load_config_legacy(config_path: str, cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Load configuration using the legacy single-file approach (backward compatibility).
    
    Args:
        config_path: Path to the configuration file
        cli_args: Optional dictionary of parsed CLI arguments
        
    Returns:
        Configuration dictionary
        
    Raises:
        ConfigError: If configuration loading fails
    """
    # Get API Key from Environment (Required Early)
    api_key_from_env = os.getenv("OPENROUTER_API_KEY")
    if not api_key_from_env:
        raise ConfigError("Required environment variable OPENROUTER_API_KEY is not set.")

    # Load and Parse Config File
    path = Path(config_path)
    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {config_path}")

    # Calculate config file hash early
    from ai_whisperer.utils.helpers import calculate_sha256
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

    # Inject API key into openrouter config
    if "openrouter" in config and isinstance(config["openrouter"], dict):
        config["openrouter"]["api_key"] = api_key_from_env

    # Validate and process the loaded configuration
    config = _validate_and_process_config(config, cli_args)
    
    logger.info(f"Successfully loaded legacy configuration from: {config_path}")
    return config

def _validate_and_process_config(config: Dict[str, Any], 
                                cli_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validate and process configuration regardless of loading method.
    
    Args:
        config: Raw configuration dictionary
        cli_args: Optional CLI arguments
        
    Returns:
        Processed and validated configuration
        
    Raises:
        ConfigError: If validation fails
    """
    # Basic Validation
    required_keys = ["openrouter"]
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys: {', '.join(missing_keys)}")

    openrouter_config = config.get("openrouter")
    if not isinstance(openrouter_config, dict):
        raise ConfigError("Invalid 'openrouter' section. Expected a dictionary.")

    # Validate required keys in openrouter section
    required_openrouter_keys = ["model"]
    missing_openrouter_keys = [key for key in required_openrouter_keys if not openrouter_config.get(key)]
    if missing_openrouter_keys:
        raise ConfigError(
            f"Missing or empty required keys in 'openrouter' section: {', '.join(missing_openrouter_keys)}"
        )

    # Ensure API key is present
    if not openrouter_config.get("api_key"):
        api_key_from_env = os.getenv("OPENROUTER_API_KEY")
        if not api_key_from_env:
            raise ConfigError("OPENROUTER_API_KEY not found in environment variables or config")
        openrouter_config["api_key"] = api_key_from_env
        logger.debug(f"API key set in config from env: {api_key_from_env[:10]}... (length: {len(api_key_from_env)})")
    else:
        logger.debug(f"API key already in config: {openrouter_config['api_key'][:10]}... (length: {len(openrouter_config['api_key'])})")

    # Load Optional Settings with Defaults
    openrouter_config["site_url"] = openrouter_config.get("site_url", DEFAULT_SITE_URL)
    openrouter_config["app_name"] = openrouter_config.get("app_name", DEFAULT_APP_NAME)

    # Extract path-related configurations
    path_config = {
        'project_path': config.get('project_path'),
        'output_path': config.get('output_dir', DEFAULT_OUTPUT_DIR),
        'workspace_path': config.get('workspace_path'),
    }

    # Initialize PathManager with config values and CLI arguments
    path_manager = PathManager.get_instance()
    path_manager.initialize(config_values=path_config, cli_args=cli_args)

    # Remove individual path keys from the main config dict after initializing PathManager
    config.pop("app_path", None)
    config.pop("project_path", None)
    config.pop("output_dir", None)
    config.pop("workspace_path", None)

    # Process Task-Specific Settings
    config = _process_task_settings(config)
    
    return config

def _process_task_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process task-specific model and prompt settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with processed task settings
    """
    openrouter_config = config["openrouter"]
    
    # Ensure task_models and task_prompts sections exist and are dictionaries
    task_models_config = config.get("task_models")
    if not isinstance(task_models_config, dict):
        if task_models_config is not None:
            logger.warning("'task_models' section is not a dictionary. Using empty dictionary.")
        config["task_models"] = {}
    else:
        config["task_models"] = task_models_config

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

    config["task_model_configs"] = {}

    # Determine model config for each task that has a prompt defined in task_prompts
    tasks_to_process = list(config["task_prompts"].keys())

    for task_name in tasks_to_process:
        task_model_settings = config["task_models"].get(task_name, {})
        if not isinstance(task_model_settings, dict):
            raise ConfigError(f"Invalid model settings for task '{task_name}'. Expected a dictionary.")

        merged_model_config = openrouter_config.copy()
        merged_model_config.update(task_model_settings)

        required_task_model_keys = ["model"]
        missing_task_model_keys = [key for key in required_task_model_keys if not merged_model_config.get(key)]
        if missing_task_model_keys:
            raise ConfigError(
                f"Missing or empty required keys in model config for task '{task_name}' after merging: {', '.join(missing_task_model_keys)}"
            )

        config["task_model_configs"][task_name] = merged_model_config

    # Ensure 'task_prompts_content' key is always present
    if "task_prompts_content" not in config:
        config["task_prompts_content"] = {}

    return config

def get_agent_config(agent_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load agent-specific configuration from the hierarchical structure.
    
    Args:
        agent_name: Optional specific agent name to load
        
    Returns:
        Agent configuration dictionary
    """
    try:
        project_root = Path(__file__).parent.parent
        agents_config_path = project_root / "config" / "agents" / "agents.yaml"
        
        if not agents_config_path.exists():
            logger.warning(f"Agent config file not found: {agents_config_path}")
            return {}
        
        with open(agents_config_path, 'r', encoding='utf-8') as f:
            agents_config = yaml.safe_load(f) or {}
        
        if agent_name:
            return agents_config.get(agent_name, {})
        
        return agents_config
        
    except Exception as e:
        logger.error(f"Failed to load agent configuration: {e}")
        return {}

def get_tools_config() -> Dict[str, Any]:
    """
    Load tools configuration from the hierarchical structure.
    
    Returns:
        Tools configuration dictionary
    """
    try:
        project_root = Path(__file__).parent.parent
        tools_config_path = project_root / "config" / "agents" / "tools.yaml"
        
        if not tools_config_path.exists():
            logger.warning(f"Tools config file not found: {tools_config_path}")
            return {}
        
        with open(tools_config_path, 'r', encoding='utf-8') as f:
            tools_config = yaml.safe_load(f) or {}
        
        return tools_config
        
    except Exception as e:
        logger.error(f"Failed to load tools configuration: {e}")
        return {}

def get_schema_path(schema_name: str) -> Path:
    """
    Get the path to a JSON schema file in the new hierarchical structure.
    
    Args:
        schema_name: Name of the schema file (with or without .json extension)
        
    Returns:
        Path to the schema file
        
    Raises:
        ConfigError: If schema file is not found
    """
    project_root = Path(__file__).parent.parent
    schemas_dir = project_root / "config" / "schemas"
    
    # Ensure .json extension
    if not schema_name.endswith('.json'):
        schema_name += '.json'
    
    schema_path = schemas_dir / schema_name
    
    if not schema_path.exists():
        raise ConfigError(f"Schema file not found: {schema_path}")
    
    return schema_path

# Backward compatibility aliases
load_config_from_file = load_config_legacy

# Migration helper function
def migrate_to_hierarchical_config(old_config_path: str, environment: str = 'development') -> None:
    """
    Helper function to migrate from old config format to new hierarchical structure.
    
    Args:
        old_config_path: Path to the old configuration file
        environment: Target environment for the migration
    """
    logger.info(f"Migrating configuration from {old_config_path} to hierarchical structure")
    
    # Load old config
    with open(old_config_path, 'r', encoding='utf-8') as f:
        old_config = yaml.safe_load(f)
    
    # Extract components for hierarchical structure
    project_root = Path(__file__).parent.parent
    config_dir = project_root / "config"
    
    # Update main.yaml with base settings
    main_config_path = config_dir / "main.yaml"
    if old_config.get("openrouter"):
        # Preserve existing main.yaml structure and just update necessary parts
        if main_config_path.exists():
            with open(main_config_path, 'r', encoding='utf-8') as f:
                main_config = yaml.safe_load(f) or {}
        else:
            main_config = {}
        
        # Merge openrouter settings
        main_config.update({
            "openrouter": old_config["openrouter"],
            "workspace_ignore_patterns": old_config.get("workspace_ignore_patterns", [])
        })
        
        with open(main_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(main_config, f, default_flow_style=False)
    
    # Create environment-specific overrides if needed
    env_config_path = config_dir / "development" / f"{environment}.yaml"
    env_config_path.parent.mkdir(exist_ok=True)
    
    env_overrides = {}
    if old_config.get("task_models"):
        env_overrides["task_models"] = old_config["task_models"]
    if old_config.get("task_prompts"):
        env_overrides["task_prompts"] = old_config["task_prompts"]
    
    if env_overrides:
        with open(env_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(env_overrides, f, default_flow_style=False)
    
    logger.info(f"Migration completed. New config structure available in {config_dir}")
