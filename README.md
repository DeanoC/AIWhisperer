# AI Whisperer

AI Whisperer is a Python command-line tool that takes your project requirements written in Markdown and uses an AI model (via OpenRouter) to generate structured task definitions in YAML format.

## Features

* Parses command-line arguments for requirements file, configuration file, and output file.
* Loads configuration (API keys, model details, prompts) from a YAML file.
* Reads requirements from a specified Markdown file.
* Formats a prompt using a template from the configuration.
* Interacts with the OpenRouter API to get AI model completions.
* Processes the API response (expecting YAML) and saves it to a file.
* Uses `rich` for colored console output and basic logging.
* Includes custom exceptions for error handling.
* Developed using TDD with `pytest`.
* Postprocessing pipeline for enhancing AI-generated content:
  * Clean backtick wrappers from YAML content
  * Add required items (task_id, input_hashes, subtask_id) automatically
  * More postprocessing steps can be added as needed

## Project development
The project_dev folder is used to track new features (rfc), done feature(done) and in progress (in_progress).
This structure is delibrately structured to assist AI in the development process.

AI Whisperer is a dog food tool, almost (so far all!) features and improvements go through its own system. This both improves and identifies issues and provides the benefits of controlled AI development process.


## Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url> # Replace with your repo URL
   cd AIWhisperer
   ```

2. **Create and activate a virtual environment:**

   ```bash
   # Windows
   py -3.12 -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

   *(Ensure you have Python 3.12 or compatible installed)*

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example configuration file:

   ```bash
   cp config.yaml.example config.yaml
   ```

2. Edit `config.yaml` and add your OpenRouter API key and desired model identifier:

   ```yaml
   openrouter:
     api_key: "YOUR_OPENROUTER_API_KEY" # Replace with your actual key
     model: "google/gemini-flash-1.5"   # Or any other model ID from OpenRouter
     params:
       temperature: 0.7
       # max_tokens: 1000 # Optional: Add other API parameters here

   prompts:
     task_generation: |
       Analyze the following requirements provided in Markdown format.
       Generate a list of tasks in YAML format based on these requirements.
       Each task should have a 'task' name and a 'description'.

       Requirements:
       ```markdown
       {md_content}
       ```

       YAML Output:
   ```

### Task-Specific Model Configuration

AI Whisperer now supports configuring different AI models for different tasks. This allows you to optimize performance and cost by selecting the most suitable model for each task type.

To configure task-specific models, add a `task_models` section to your `config.yaml`:

```yaml
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

If a task-specific model is not defined, the system will fall back to the default model configuration in the `openrouter` section.

See [Configuration Examples](docs/config_examples.md) for more detailed examples and options.

## Usage

Run the tool from the project's root directory:

```bash
python -m src.ai_whisperer.main --requirements <path/to/your/requirements.md> --config config.yaml --output <path/to/output/tasks.yaml>
```

**Example:**

```bash
# Assuming you have requirements.md in the root
python -m src.ai_whisperer.main --requirements requirements.md --config config.yaml --output generated_tasks.yaml
```

This will read `requirements.md`, use the settings in `config.yaml`, call the OpenRouter API, and save the resulting task list to `generated_tasks.yaml`.

* **`--list-models`**: Displays a list of available models from the OpenRouter API. Requires the `--config` argument to be specified as well.

    ```bash
    python -m src.ai_whisperer.main --list-models --config config.yaml
    ```

* **`--generate-subtask`**: Generates a detailed task implementation YAML from a step definition file. Requires both `--config` and `--step` arguments.

    ```bash
    python -m src.ai_whisperer.main --generate-subtask --config config.yaml --step path/to/step.yaml
    ```

    This will process the step definition from `step.yaml`, refine it into a detailed implementation plan, and save the result to a file in the output directory.

## Development

To run tests:

```bash
pip install -r requirements.txt # Ensure dev dependencies like pytest are installed
pytest
```
