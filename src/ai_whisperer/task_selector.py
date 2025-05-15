import logging
from typing import Dict, Any, Optional
from pathlib import Path
from .exceptions import ConfigError
from .prompt_system import PromptSystem # Import PromptSystem

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


def get_prompt_for_task(prompt_system: PromptSystem, task_name: str) -> str:
    """
    Get the prompt content for a specific task using the PromptSystem.

    Args:
        prompt_system: An instance of the PromptSystem.
        task_name: The name of the task.

    Returns:
        The prompt content string for the task.

    Raises:
        ConfigError: If the prompt is not found by the PromptSystem.
    """
    logger.debug(f"get_prompt_for_task called with task_name: {task_name}")

    try:
        # Assuming task names directly map to prompt names in a 'tasks' category
        # This might need adjustment based on actual prompt organization
        prompt_content = prompt_system.get_prompt_content("tasks", task_name)
        logger.debug(f"Successfully retrieved prompt for task '{task_name}' from PromptSystem.")
        return prompt_content
    except PromptSystem.PromptNotFoundError as e:
        logger.error(f"Prompt not found for task '{task_name}': {e}")
        raise ConfigError(f"Prompt not found for task '{task_name}': {e}") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting prompt for task '{task_name}': {e}")
        raise ConfigError(f"Error getting prompt for task '{task_name}': {e}") from e
