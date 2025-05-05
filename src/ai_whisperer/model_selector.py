from typing import Dict, Any

from .exceptions import ConfigError

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
    task_models = config.get('task_models', {})
    task_config = task_models.get(task_name)
    
    if task_config:
        # Ensure the task config has the required fields
        if 'provider' not in task_config or 'model' not in task_config:
            raise ConfigError(f"Task model configuration for '{task_name}' is missing required fields.")
        
        # If the provider is 'openrouter', merge with the default openrouter config
        if task_config.get('provider') == 'openrouter':
            openrouter_config = config.get('openrouter', {})
            merged_config = {
                'api_key': openrouter_config.get('api_key'),
                'site_url': openrouter_config.get('site_url', 'http://localhost:8000'),
                'app_name': openrouter_config.get('app_name', 'AIWhisperer'),
                'model': task_config.get('model'),
                'params': task_config.get('params', {})
            }
            return merged_config
        
        # For other providers, return the task config as is
        return task_config
    
    # If no task-specific configuration is found, return the default openrouter config
    return config.get('openrouter', {})