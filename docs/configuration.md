# ---

## AI Service Configuration (Required)

- The `openrouter.api_key` is required and must be set via the `OPENROUTER_API_KEY` environment variable (never commit API keys to source).
- The `model` field is required; see OpenRouter docs for available models.
- `timeout_seconds` sets the maximum time (in seconds) for any AI service request (default: 60, can be increased for long-running tasks).
- `cache` enables in-memory caching of API responses for efficiency.

## Session Management Settings

- **Session timeouts**: Controlled by `timeout_seconds` in the `openrouter` section. If a session or AI service call exceeds this, a timeout notification is sent to the client.
- **Max sessions**: The default implementation does not hard-limit concurrent sessions, but you can add a limit in your deployment or extend the session manager.
- **Cleanup**: Sessions are automatically cleaned up on disconnect, error, or timeout to prevent resource leaks.

## Resource Limit Recommendations

- **Memory**: Each session consumes memory for context/history and AI state. Monitor usage under load and adjust `max_tokens`, session timeouts, or add a session limit as needed.
- **Timeouts**: For most use cases, 60–120 seconds is sufficient for `timeout_seconds`. Increase for long-running tasks, but beware of resource exhaustion.
- **Concurrency**: For high concurrency, run multiple server processes and use a load balancer.

## Security Considerations

- **API Keys**: Always set `OPENROUTER_API_KEY` via environment variable or `.env` file. Never commit secrets to source control.
- **Session Isolation**: Each WebSocket/session is isolated; no data is shared between sessions unless explicitly coded.
- **User Input**: Validate and sanitize all user input in production deployments.

## Cross-References

- See [Architecture](architecture.md) for how configuration impacts runtime behavior.
- See [API Documentation](interactive_mode_api.md) for how timeouts and errors are surfaced to clients.

# ---
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

# --- Prompt System Configuration --- Optional Section ---
prompt_system:
  prompt_base_dir: prompts # Define the base directory for prompts.
  sections: # Define prompt sections.
    example_section:
      - name: example_prompt # Define individual prompts within a section.
        path: example_section/example_prompt.md # Path relative to prompt_base_dir.
        description: This is an example prompt. # Optional description.
        is_default: false # Optional: Default prompt for this section.
      - name: default
        path: example_section/default.md
        description: This is the default prompt for the example_section.
        is_default: true
    another_section:
      - name: example_prompt_no_section_default
        path: another_section/example_prompt_no_section_default.md
        description: This is an example prompt in another_section without a section default.
        is_default: false
  global_defaults: # Define global default prompts.
    - name: global_runner_fallback_default
      path: global_runner_fallback_default.md
      description: This is a global fallback default prompt.

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
| `cache` | No | `false` | Boolean (`true` or `false`). Enables or disables in-memory caching for OpenRouter API responses. When `true`, responses to identical requests (model, messages, params, tools, response_format) are cached for the lifetime of the `OpenRouterAIService` object. |
| `timeout_seconds` | No | `60` | Integer. Timeout in seconds for API requests to OpenRouter and session timeouts. |

**Note:** The OpenRouter API key MUST be provided via the `OPENROUTER_API_KEY` environment variable. You can set this variable directly in your shell or place it in a `.env` file in the project's root directory (e.g., `OPENROUTER_API_KEY="sk-or-v1-abc...xyz"`). Never commit API keys to source control.

### Prompt System Configuration

The `prompt_system` section configures the new prompt loading system. This system provides a structured way to organize, load, and manage prompt templates.

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `prompt_base_dir` | No | `prompts` | The base directory where prompt files are located. All prompt paths defined in `sections` and `global_defaults` are relative to this directory. |
| `sections` | No | - | A dictionary defining prompt sections. Each key is a section name, and the value is a list of prompt configurations within that section. |
| `sections.<section_name>` | No | - | A list of prompt configurations for the specified section. |
| `sections.<section_name>[].name` | Yes | - | The unique name of the prompt within its section. |
| `sections.<section_name>[].path` | Yes | - | The path to the prompt file, relative to `prompt_base_dir`. |
| `sections.<section_name>[].description` | No | - | An optional description of the prompt. |
| `sections.<section_name>[].is_default` | No | `false` | A boolean indicating if this prompt is the default for its section. Only one prompt per section should have `is_default` set to `true`. |
| `global_defaults` | No | - | A list of global default prompt configurations. These prompts are used as a fallback if a specific prompt or section default is not found. |
| `global_defaults[].name` | Yes | - | The unique name of the global default prompt. |
| `global_defaults[].path` | Yes | - | The path to the global default prompt file, relative to `prompt_base_dir`. |
| `global_defaults[].description` | No | - | An optional description of the global default prompt. |

**Prompt Resolution Hierarchy:**

When a prompt is requested, the system resolves the correct prompt file based on the following hierarchy:

1.  **Specific Prompt Request:** If a specific section and prompt name are requested (e.g., `get_prompt("example_section", "example_prompt")`), the system looks for a matching entry in the `sections` configuration.
2.  **Section Default:** If a section is requested but no specific prompt name is provided, or if the requested prompt name is not found in the section, the system looks for the prompt with `is_default: true` within that section.
3.  **Global Defaults:** If neither a specific prompt nor a section default is found, the system looks for a matching prompt name in the `global_defaults` list.
4.  **File System Fallback (Implicit):** If a prompt is not explicitly defined in the configuration, the system may attempt to resolve it based on a predefined directory structure within the `prompt_base_dir` (e.g., `prompt_base_dir/section_name/prompt_name.md`). This behavior is part of the system's internal logic and provides a convention-over-configuration option.

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

If a task-specific configuration is not provided, the default model from the `openrouter` section will be used. All model and parameter options are passed directly to the OpenRouter API.

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

prompt_system:
  prompt_base_dir: prompts
  sections:
    core:
      - name: initial_plan
        path: core/initial_plan.md
        description: Prompt for generating the initial project plan.
        is_default: true
      - name: subtask_generator
        path: core/subtask_generator.md
        description: Prompt for generating individual subtasks.
    agents:
      - name: ai_interaction
        path: agents/ai_interaction.md
        description: Default prompt for AI interaction agents.
        is_default: true
      - name: planning
        path: agents/planning.md
        description: Default prompt for planning agents.
        is_default: true
  global_defaults:
    - name: global_runner_fallback_default
      path: global_runner_fallback_default.md
      description: Global fallback prompt for the runner.

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

prompt_system:
  prompt_base_dir: prompts
  sections:
    core:
      - name: initial_plan
        path: core/initial_plan.md
        description: Prompt for generating the initial project plan.
        is_default: true
      - name: subtask_generator
        path: core/subtask_generator.md
        description: Prompt for generating individual subtasks.
    agents:
      - name: ai_interaction
        path: agents/ai_interaction.md
        description: Default prompt for AI interaction agents.
        is_default: true
      - name: planning
        path: agents/planning.md
        description: Default prompt for planning agents.
        is_default: true
    custom_feature:
      - name: custom_prompt_for_feature_x
        path: custom_feature/feature_x_prompt.md
        description: A custom prompt for a specific feature.
        is_default: false
  global_defaults:
    - name: global_runner_fallback_default
      path: global_runner_fallback_default.md
      description: Global fallback prompt for the runner.

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
