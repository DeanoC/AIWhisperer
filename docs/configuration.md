# Configuration File (`config.yaml`)

The AI Whisperer application uses a YAML configuration file to customize its behavior. The configuration file should be placed in the project root directory or specified via command line arguments.

## Basic Structure

The configuration file follows this basic structure:

```yaml
# --- OpenRouter API Settings --- Required Section ---
openrouter:
  model: "mistralai/mistral-7b-instruct"  # Required: Model identifier
  params:                                  # Optional: Model parameters
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"        # Optional: Your project's URL
  app_name: "AIWhisperer"                  # Optional: Your application's name

# --- Prompt Templates --- Required Section ---
prompts:
  orchestrator_prompt_path: "prompts/orchestrator_default.md"       # Optional: Path to orchestrator prompt
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"  # Optional: Path to subtask generator prompt

# --- Task-Specific Model Settings --- Optional Section ---
task_models:
  "Subtask Generation":                    # Optional: Task-specific model configuration
    provider: "openrouter"                 # Required: Provider name
    model: "anthropic/claude-3-opus"       # Required: Model identifier
    params:                                # Optional: Model parameters
      temperature: 0.5
      max_tokens: 4096

# --- Other Application Settings --- Optional Section ---
output_dir: "./output/"                    # Optional: Output directory path
```

## Configuration Sections

### OpenRouter API Settings

The `openrouter` section contains settings for the OpenRouter API, which is used to access various AI models.

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `model` | Yes | - | The model identifier from OpenRouter (e.g., "mistralai/mistral-7b-instruct", "openai/gpt-4o") |
| `params` | No | - | Parameters to pass to the OpenRouter API for chat completions |
| `params.temperature` | No | - | Controls randomness (0.0 to 2.0). Higher values = more creative, lower = more deterministic |
| `params.max_tokens` | No | - | Maximum number of tokens to generate in the response |
| `site_url` | No | "http://localhost:8000" | Your project's URL (sent as HTTP-Referer) |
| `app_name` | No | "AIWhisperer" | Your application's name (sent as X-Title) |

**Note:** The OpenRouter API key MUST be provided via the `OPENROUTER_API_KEY` environment variable. You can set this variable directly in your shell or place it in a `.env` file in the project's root directory (e.g., `OPENROUTER_API_KEY="sk-or-v1-abc...xyz"`).

### Prompt Templates

The `prompts` section contains paths to prompt templates used by the application.

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `orchestrator_prompt_path` | No | "prompts/orchestrator_default.md" | Path to the prompt template used for generating the overall task plan |
| `subtask_generator_prompt_path` | No | "prompts/subtask_generator_default.md" | Path to the prompt template used for refining individual subtasks |

Paths can be absolute or relative to the configuration file's location.

### Task-Specific Model Settings

The `task_models` section allows you to specify different models for different tasks in the application.

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `task_models.<task_name>` | No | - | Configuration for a specific task |
| `task_models.<task_name>.provider` | Yes | - | Provider name (currently only "openrouter" is supported) |
| `task_models.<task_name>.model` | Yes | - | Model identifier for this task |
| `task_models.<task_name>.params` | No | - | Model parameters for this task |

Currently supported task names:
- "Subtask Generation": Used when generating individual subtasks
- "Orchestrator": Used when generating the overall project plan

If a task-specific configuration is not provided, the default model from the `openrouter` section will be used.

### Other Application Settings

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `output_dir` | No | "./output/" | Directory where generated task files will be saved |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | Your OpenRouter API key |

## Examples

### Minimal Configuration

```yaml
openrouter:
  model: "mistralai/mistral-7b-instruct"
  params:
    temperature: 0.7
    max_tokens: 2048

prompts:
  orchestrator_prompt_path: "prompts/orchestrator_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

output_dir: "./output/"
```

### Full Configuration with Task-Specific Models

```yaml
openrouter:
  model: "mistralai/mistral-7b-instruct"  # Default model
  params:
    temperature: 0.7
    max_tokens: 2048
  site_url: "http://localhost:8000"
  app_name: "AIWhisperer"

prompts:
  orchestrator_prompt_path: "prompts/orchestrator_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

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

output_dir: "./output/"
```

For more examples and advanced configurations, see [Configuration Examples](config_examples.md).
