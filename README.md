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
* **New:** Refine requirement documents using AI to improve clarity and completeness.

*   **Improved Terminal Monitor:** A redesigned real-time terminal monitor display featuring three segmented, ASCII-outlined sections, colored output for event types, pretty-printed and syntax-highlighted JSON for monitor events, and suppression of non-monitor output for a cleaner view of plan execution.
## Demonstrating Core Functionality: The Simple Country Test

The enhanced AIWhisperer runner is capable of executing complex plans that involve real-time interactions with AI services. The `simple_country_test` serves as a key integration test designed to showcase and validate this core functionality.

This test confirms the runner's ability to:

*   Orchestrate a sequence of diverse tasks, including planning, AI queries, and validation steps.
*   Successfully interact with an AI service (OpenRouter) to obtain dynamic responses.
*   Manage and pass data (as artifacts) between different tasks in the plan.
*   Maintain conversation history across multiple AI interactions to ensure context awareness.
*   Execute validation logic based on the outputs received from the AI.

The high-level flow of the `simple_country_test` involves: selecting a landmark, asking the AI for its country, validating the country, asking the AI for the capital, validating the capital, asking the AI if the landmark is in the capital, and finally validating this fact. The successful execution of this test demonstrates the runner's readiness for more complex automated workflows involving AI.

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
python -m src.ai_whisperer.main generate --requirements <path/to/your/requirements.md> --config config.yaml --output <path/to/output/tasks.yaml>
python -m src.ai_whisperer.main list-models --config .\project_dev\aiwhisperer_config.yaml --output-csv models.csv

```

**Example:**

```bash
# Assuming you have requirements.md in the root
python -m src.ai_whisperer.main --requirements requirements.md --config config.yaml --output generated_tasks.yaml
```

This will read `requirements.md`, use the settings in `config.yaml`, call the OpenRouter API, and save the resulting task list to `generated_tasks.yaml`.

*   **`--list-models`**: Displays a list of available models from the OpenRouter API. Requires the `--config` argument to be specified as well.

    ```bash
    python -m src.ai_whisperer.main --list-models --config config.yaml
    ```

*   **`--generate-subtask`**: Generates a detailed task implementation YAML from a step definition file. Requires both `--config` and `--step` arguments.

    ```bash
    python -m src.ai_whisperer.main --generate-subtask --config config.yaml --step path/to/step.yaml
    ```

    This will process the step definition from `step.yaml`, refine it into a detailed implementation plan, and save the result to a file in the output directory.

*   **`refine`**: Refines an existing requirement document using an AI model.

    ```bash
    python -m src.ai_whisperer.main refine <path/to/requirements.md> --config config.yaml [--prompt-file <path/to/prompt.txt>] [--iterations <number>]
    ```

    This command will take the specified requirements file, process it with an AI model (optionally using a custom prompt and multiple iterations), rename the original file with a `.original` suffix, and save the refined content back to the original filename.

*   **`run`**: Executes a project plan from an overview JSON file and manages the state file. See the [Usage Documentation](docs/usage.md) for detailed information.

    ```bash
    python -m src.ai_whisperer.main run --plan-file <path/to/plan.json> --state-file <path/to/state.json> --config <path/to/config.yaml> [--monitor | -m]
    ```

    *   **`--monitor`**, **`-m`**: Enables the terminal monitor during the task execution, providing real-time updates on the plan's progress.

The project_dev folder shows how I currently use aiwhisperer to implement features in it self.
A starting feature request can be generated with any AI chat with a prompt similar to
the following with context from something like

```text
Write a feature request in a similar style to patch_hash_task_id.md to the same rfc folder called more_yaml_postprocessing that will implement postprocessing similar to our existing postprocessing system that is designed to clean up results from our AI calls in code rather than requiring the ai to format the document.
Currently our prompts have strict rules
```

Currently a prompt like

```text
We are implementing a new feature more_yaml_postprocessing with more_yaml_postprocessing_aiwhisperer_config.yaml being our structure high level plan.
It has already had refinement for each subtask in the same folder with the anme subtask_%subtask name%.yaml, these should be considered better versions then then the subtask defined in the high level task plan.

You job is to work though the plan, implementing the feature.
You MUST do it using strict order following a strict test-first driven methology.
Filenames in the plans may be slightly wrong so check the codebase to see if existing files/folder structure would be better.

Anytime you aren't sure of the best course of action, ask me
```

can be used to start implementing the feature. Obviously AI will need help, but the goal of AI Whisperer is to reduce this.

## Development

To run tests:

```bash
pip install -r requirements.txt # Ensure dev dependencies like pytest are installed
pytest
```

## Example dogfood feature developer prompt to roocode orchestrator

```text
We are implementing a feature request
@/project_dev/in_dev/logging-and-monitoring/overview_logging-and-monitoring_aiwhisperer_config.json
This is part of a much larger feature described here @/project_dev/rfc/runner/aiwhisperer_runner_plan.md This is purely for references, we are NOT to do anything but what is the feature request .json you have.
We follow a strict test-first driven design metholodogy, and you are reasonable for enforcing this. The USER gets angry if not followed or any task gets down before the previous one is finished.
It is also your responsibility to ensure the overview document step completed fields are keep upto date for each step

Are you ready?
