import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .exceptions import ConfigError

logger = logging.getLogger(__name__)


def get_model_for_task(config: Dict[str, Any], task_name: str) -> Dict[str, Any]:
    """
    Get the model configuration for a specific task.

    Args:
        config: The loaded application configuration.
        task_name: The name of the task.

    Returns:
        The model configuration for the task, or the default model configuration if
        no task-specific configuration is found.

    Raises:
        ConfigError: If the task model configuration is missing required fields.
    """
    task_models = config.get("task_models", {})
    task_config = task_models.get(task_name)

    if task_config:
        # Ensure the task config has the required fields
        if "provider" not in task_config or "model" not in task_config:
            raise ConfigError(f"Task model configuration for '{task_name}' is missing required fields.")

        # If the provider is 'openrouter', merge with the default openrouter config
        if task_config.get("provider") == "openrouter":
            openrouter_config = config.get("openrouter", {})
            merged_config = {
                "api_key": openrouter_config.get("api_key"),
                "site_url": openrouter_config.get("site_url", "http://localhost:8000"),
                "app_name": openrouter_config.get("app_name", "AIWhisperer"),
                "model": task_config.get("model"),
                "params": task_config.get("params", {}),
            }
            return merged_config

        # For other providers, return the task config as is
        return task_config

    # If no task-specific configuration is found, return the default openrouter config
    return config.get("openrouter", {})


def get_prompt_for_task(config: Dict[str, Any], task_name: str, project_dir: Optional[Path] = None) -> tuple[str, Path]:
    """
    Get the prompt for a specific task.

    Args:
        config: The loaded application configuration.
        task_name: The name of the task.
        project_dir: Optional project directory to resolve prompt paths.

    Returns:
        The prompt string for the task, or the default prompt if no task-specific prompt is found.

    Raises:
        ConfigError: If the prompt is missing or not a string.
    """
    logger.debug(f"get_prompt_for_task called with task_name: {task_name}")
    logger.debug(f"Config received by get_prompt_for_task: {config}")
    task_prompts = config.get("task_prompts", {})
    prompt_path = task_prompts.get(task_name)

    if prompt_path is not None:
        logger.debug(f"Found prompt_path in config for task '{task_name}': {prompt_path}")
        if not isinstance(prompt_path, str):
            raise ConfigError(f"Prompt for task '{task_name}' must be a string.")
        if Path(prompt_path).exists():
            logger.debug(f"Prompt file exists at {prompt_path}. Reading content.")
            return (Path(prompt_path).read_text(encoding="utf-8"), prompt_path)
        else:
            logger.debug(f"Prompt file not found at configured path: {prompt_path}")

    # Try to load default prompt from file
    default_prompt_path = (project_dir or Path(__file__).parent) / "prompts" / f"{task_name}_default.md"
    logger.debug(f"Checking for default prompt file at: {default_prompt_path}")
    if default_prompt_path.exists():
        logger.debug(f"Default prompt file found at {default_prompt_path}. Reading content.")
        return (default_prompt_path.read_text(encoding="utf-8"), default_prompt_path)

    logger.error(f"No prompt found for task '{task_name}' and no default prompt is set.")
    raise ConfigError(f"No prompt found for task '{task_name}' and no default prompt is set.")
