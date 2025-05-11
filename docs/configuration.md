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
| `site_url` | No | "<http://localhost:8000>" | Your project's URL (sent as HTTP-Referer) |
| `app_name` | No | "AIWhisperer" | Your application's name (sent as X-Title) |
| `cache` | No | `false` | Boolean (`true` or `false`). Enables or disables in-memory caching for OpenRouter API responses. When `true`, responses to identical requests (model, messages, params, tools, response_format) are cached for the lifetime of the `OpenRouterAPI` object. |
| `timeout_seconds` | No | `60` | Integer. Timeout in seconds for API requests to OpenRouter. |

**Note:** The OpenRouter API key MUST be provided via the `OPENROUTER_API_KEY` environment variable. You can set this variable directly in your shell or place it in a `.env` file in the project's root directory (e.g., `OPENROUTER_API_KEY="sk-or-v1-abc...xyz"`).

### Prompt Templates

The `prompts` section contains paths to prompt templates used by the application.

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `orchestrator_prompt_path` | No | "prompts/orchestrator_default.md" | Path to the prompt template used for generating the overall task plan |
| `subtask_generator_prompt_path` | No | "prompts/subtask_generator_default.md" | Path to the prompt template used for refining individual subtasks |

Paths can be absolute or relative to the configuration file's location.

> **Note:** If you use the `--project-dir` CLI argument, all relative paths (including prompt templates) will be resolved relative to the specified project directory.

### Runner/ExecutionEngine Agent Prompts

This section defines default prompts for specific agent types that are used by the ExecutionEngine (Runner). These prompts serve as the base instructions for agents when executing tasks, and their selection follows a specific fallback mechanism.

| Setting                                   | Required | Default | Description                                                                                                                               |
| :---------------------------------------- | :------- | :------ | :---------------------------------------------------------------------------------------------------------------------------------------- |
| `prompts.agent_type_defaults`             | No       | -       | A dictionary defining default prompt paths for specific agent types used by the ExecutionEngine/Runner.                                   |
| `prompts.agent_type_defaults.<agent_type>`| No       | -       | Path to the default prompt file for the specified `<agent_type>`. Paths are relative to the config file.                                  |
| `prompts.global_runner_default_prompt_path`| No       | -       | Path to a global default prompt file for the Runner, used as a fallback if no agent-specific default or task instructions are available. |

**Prompt Selection Logic for Runner Agents:**

When the ExecutionEngine (Runner) executes a task with a specific `agent_spec.type`, it determines the prompt to use based on the following hierarchy:

1.  The Runner first attempts to find a prompt in `prompts.agent_type_defaults` that matches the `agent_spec.type` of the current task.
2.  If a matching agent-specific default prompt is **not found**, the Runner will then use the content of `task_definition['instructions']` from the task plan, provided these instructions are present and not empty.
3.  If a matching agent-specific default prompt is **not found** AND `task_definition['instructions']` are also missing or empty, the Runner will then use the prompt specified by `prompts.global_runner_default_prompt_path` (if this path is configured).
4.  If none of the above (agent-specific default, task instructions, or global runner default) are available, the agent might operate without a base system prompt, which could lead to unpredictable behavior or errors.

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

  # --- Agent-Type Default Prompts (for Runner/ExecutionEngine Agents) ---
  # This section defines default prompts for specific agent types that are
  # referenced in the 'agent_spec.type' field of tasks executed by the
  # ExecutionEngine (Runner).
  agent_type_defaults:
    ai_interaction: "prompts/defaults/runner/ai_interaction_default.md"
    planning: "prompts/defaults/runner/planning_default.md"
    # custom_agent_type: "prompts/defaults/runner/custom_agent_default.md"

  # --- Optional: Global Default Prompt (for Runner/ExecutionEngine Agents) ---
  # This prompt is used by the ExecutionEngine as a last resort if no
  # agent-type specific prompt (from agent_type_defaults) is found for the
  # current agent_spec.type AND the task_definition['instructions'] are also missing or empty.
  global_runner_default_prompt_path: "prompts/global_runner_fallback_default.md"

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
  cache: true  # Enable API response caching
  timeout_seconds: 120 # Set a custom timeout

prompts:
  orchestrator_prompt_path: "prompts/orchestrator_default.md"
  subtask_generator_prompt_path: "prompts/subtask_generator_default.md"

  # --- Agent-Type Default Prompts (for Runner/ExecutionEngine Agents) ---
  # This section defines default prompts for specific agent types that are
  # referenced in the 'agent_spec.type' field of tasks executed by the
  # ExecutionEngine (Runner).
  agent_type_defaults:
    ai_interaction: "prompts/defaults/runner/ai_interaction_default.md"
    planning: "prompts/defaults/runner/planning_default.md"
    # custom_agent_type: "prompts/defaults/runner/custom_agent_default.md"

  # --- Optional: Global Default Prompt (for Runner/ExecutionEngine Agents) ---
  # This prompt is used by the ExecutionEngine as a last resort if no
  # agent-type specific prompt (from agent_type_defaults) is found for the
  # current agent_spec.type AND the task_definition['instructions'] are also missing or empty.
  global_runner_default_prompt_path: "prompts/global_runner_fallback_default.md"

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
