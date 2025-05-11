# Configuration Examples for AI Whisperer

This document provides detailed examples and options for configuring AI Whisperer, with a focus on the task-specific model configuration system.

## Basic Configuration

A minimal configuration file includes the OpenRouter API settings and prompt templates:

```yaml
# --- OpenRouter API Settings ---
openrouter:
  api_key: "YOUR_OPENROUTER_API_KEY"
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

# --- Other Application Settings ---
output_dir: "./output/"
```

## Task-Specific Model Configuration

### Full Example

This example shows a complete configuration with task-specific models for both "Subtask Generation" and "Orchestrator" tasks:

```yaml
# --- OpenRouter API Settings ---
openrouter:
  api_key: "YOUR_OPENROUTER_API_KEY"
  model: "mistralai/mistral-7b-instruct"  # Default model
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

# --- Prompt Templates ---
prompts:
  initial_plan_prompt_path: "prompts/initial_plan_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

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

# --- Other Application Settings ---
output_dir: "./output/"
```

### Partial Configuration

You can configure models for only some tasks. Tasks without specific configurations will use the default model:

```yaml
# --- OpenRouter API Settings ---
openrouter:
  api_key: "YOUR_OPENROUTER_API_KEY"
  model: "mistralai/mistral-7b-instruct"  # Default model for all tasks
  params:
    temperature: 0.7
    max_tokens: 2048

# --- Task-Specific Model Settings ---
task_models:
  "Subtask Generation":
    provider: "openrouter"
    model: "anthropic/claude-3-opus"
    params:
      temperature: 0.5
      max_tokens: 4096
  # No configuration for "Orchestrator", so it will use the default model
```

### Required and Optional Fields

Each task model configuration requires:

- `provider`: Currently only "openrouter" is supported, but the system is designed to allow other providers in the future
- `model`: The model identifier to use for this task

Optional fields include:

- `params`: A dictionary of model parameters (e.g., temperature, max_tokens)

### Fallback Mechanism

The system uses the following logic to determine which model configuration to use:

1. If a task-specific configuration exists in the `task_models` section for the requested task, use that configuration
2. If the task-specific configuration is for the "openrouter" provider, merge it with the default OpenRouter settings (API key, site_url, app_name)
3. If no task-specific configuration exists, fall back to the default model configuration in the `openrouter` section

## Future Extensions

The task-specific model configuration system is designed to be extensible:

1. **Adding New Tasks**: Simply add a new entry to the `task_models` section with the task name and model configuration
2. **Supporting New Providers**: The `provider` field allows for future expansion to support different AI providers
3. **Extending Parameters**: The `params` field can be extended with additional parameters specific to each model or provider