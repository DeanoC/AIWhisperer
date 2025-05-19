# Model Selection Plan for Task-Specific Configuration

## Overview

This document outlines the plan for implementing a model-per-task configuration system in the AIWhisperer project. The current system uses a single model configuration for all AI tasks, but we need to extend this to support task-specific model selection for optimization.

## Configuration Structure

### Current Structure

The current `config.yaml` structure has a single model configuration under the `openrouter` section:

```yaml
# --- OpenRouter API Settings ---
openrouter:
  api_key: "test-api-key"  # This will be mocked in tests
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"
```

### Proposed Structure

We will extend the configuration to include a new `task_models` section that maps task names to their specific model configurations:

```yaml
# --- OpenRouter API Settings ---
openrouter:
  api_key: "test-api-key"  # This will be mocked in tests
  model: "mistralai/mistral-7b-instruct"  # Default model
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Task-Specific Model Settings ---
task_models:
  "Subtask Generation":
    provider: "openrouter"
    model: "anthropic/claude-3-opus"
    params:
      temperature: 0.5
      max_tokens: 4096
  "Orchestrator":
    provider: "openrouter"
    model: "mistralai/mistral-large"
    params:
      temperature: 0.8
      max_tokens: 8192
```

The existing `openrouter` section will be maintained for backward compatibility and will serve as the default model configuration when a task-specific model is not defined.

## Code Changes

### 1. Configuration Loading

We need to modify the `load_config` function in `src/ai_whisperer/config.py` to:
- Load and validate the new `task_models` section
- Ensure each task model configuration has the required fields (`provider`, `model`)
- Set default values for optional fields (e.g., `params`)

### 2. Model Selection Logic

We will create a new module `src/ai_whisperer/task_selector.py` with a function to select the appropriate model configuration based on the task name:

```python
def get_model_for_task(config: Dict[str, Any], task_name: str) -> Dict[str, Any]:
    """
    Get the model configuration for a specific task.
    
    Args:
        config: The loaded application configuration.
        task_name: The name of the task.
        
    Returns:
        The model configuration for the task, or the default model configuration if
        no task-specific configuration is found.
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
```

### 3. Integration with Existing Code

#### Subtask Generator

Modify the `SubtaskGenerator.__init__` method in `src/ai_whisperer/subtask_generator.py`:

```python
def __init__(self, config_path: str, overall_context: str = "", workspace_context: str = ""):
    try:
        self.config = load_config(config_path)
        
        # Get the model configuration for the "Subtask Generation" task
        from .task_selector import get_model_for_task
        model_config = get_model_for_task(self.config, "Subtask Generation")
        
        # Pass the task-specific model configuration to the OpenRouterAIService client
        self.openrouter_client = OpenRouterAIService(config=model_config)
        
        self.subtask_prompt_template = self.config['prompts']['subtask_generator_prompt_content']
        self.output_dir = Path(self.config['output_dir'])
        self.overall_context = overall_context
        self.workspace_context = workspace_context
    except ConfigError as e:
        # Re-raise ConfigError to be handled by the caller
        raise e
    except KeyError as e:
        raise ConfigError(f"Missing expected key in configuration: {e}") from e
    except Exception as e:
        # Catch any other unexpected errors during initialization
        raise SubtaskGenerationError(f"Failed to initialize SubtaskGenerator: {e}") from e
```

#### Orchestrator

Modify the `Orchestrator.__init__` method in `src/ai_whisperer/orchestrator.py`:

```python
def __init__(self, config: Dict[str, Any]):
    self.config = config
    self.output_dir = Path(config.get('output_dir', './output/'))
    self.prompt_override_path = config.get('prompt_override_path')
    
    # Get the model configuration for the "Orchestrator" task
    from .task_selector import get_model_for_task
    model_config = get_model_for_task(config, "Orchestrator")
    
    # Initialize OpenRouterAIService client with the task-specific model configuration
    from .openrouter_api import OpenRouterAIService
    self.openrouter_client = OpenRouterAIService(config=model_config)
    
    logger.info(f"Orchestrator initialized. Output directory: {self.output_dir}")
    
    # Load the validation schema
    # ... (rest of the method remains unchanged)
```

## Implementation Steps

1. **Update Configuration Schema Test**: Create a test file to validate the new configuration schema.
2. **Update Configuration Schema**: Modify the configuration loading logic to support task-specific model settings.
3. **Validate Configuration Schema**: Run the tests to ensure the updated schema works correctly.
4. **Generate Model Selection Logic Test**: Create tests for the model selection logic.
5. **Implement Model Selection Logic**: Create the task_selector.py module with the get_model_for_task function.
6. **Validate Model Selection Logic**: Run the tests to ensure the model selection logic works correctly.
7. **Integrate Model Selection Tests**: Create integration tests for the Subtask Generator and Orchestrator.
8. **Integrate Model Selection**: Modify the Subtask Generator and Orchestrator to use the model selection logic.
9. **Validate Model Integration**: Run the integration tests to ensure everything works together.
10. **Update Documentation**: Update the project documentation to reflect the new configuration system.

## Future Extensibility

This design allows for easy addition of new tasks and models in the future:

1. **Adding New Tasks**: Simply add a new entry to the `task_models` section in the configuration file with the task name and model configuration.

2. **Supporting New Model Providers**: The `provider` field in the task model configuration allows for future expansion to support different AI providers beyond OpenRouter.

3. **Extending Model Parameters**: The `params` field can be extended with additional parameters specific to each model or provider.

4. **Fallback Mechanism**: The system falls back to the default model configuration if a task-specific configuration is not found, ensuring backward compatibility.