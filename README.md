# AI Whisperer

AI Whisperer is a Python command-line tool that takes your project requirements written in Markdown and uses an AI model (via OpenRouter) to generate an initial structured task definitions in json format.

It is designed for code development and project management, allowing you to define tasks based on requirements, refine them, and generate an overview plan with subtasks. The tool can be used to automate the planning and execution of tasks, enhancing productivity and clarity in software development.

It can then refine these plans, and generate an overview plan with
separate subtasks for each task, which can be executed in a controlled manner either via IDE or CLI based AI systems.

It has an experimental 'runner' that can execute these plans, managing state and artifacts, and providing a real-time terminal monitor for plan execution. Eventually this should be more focused
than the more general tools like [roocode] but its thats a long way away off.

It is designed to help automate the process of planning and executing tasks based on requirements, leveraging AI to enhance productivity and clarity.

## Features

* Reads requirements and features from a Markdown file.
* Uses OpenRouter API to get AIs to do work.
* Generates structured task definitions in JSON format.
* Supports refinement of plans and tasks using AI.
* Generates an overview plan with subtasks for each task.
* Executes plans with a runner that manages state and artifacts.
* Provides a real-time terminal monitor for plan execution.
* Developed using TDD with `pytest`.
* Postprocessing pipeline for enhancing AI-generated content:
  * Clean backtick wrappers from YAML content
  * Add required items (task_id, input_hashes, subtask_id) automatically
  * More postprocessing steps can be added as needed

## Project development

The project_dev folder is used to track new features (rfc), done feature(done) and in progress (in_progress).
This structure is deliberately structured to assist AI in the development process.

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
   ```

### Path Management System

AI Whisperer uses a flexible path management system, implemented in `src/ai_whisperer/path_management.py`, to resolve all important directories and file locations. These paths are available throughout the program and can be referenced in configuration or code:

* `{app_path}`: The root of the AI Whisperer codebase (for built-in resources).
* `{project_path}`: The root of your current project (typically your working directory).
* `{output_path}`: Where generated outputs are written (defaults to `{project_path}/output`).
* `{workspace_path}`: The workspace root (defaults to `{project_path}`).
* `{prompt_path}`: The base directory for prompt files (defaults to `{project_path}`, but can be overridden).

These variables are resolved at runtime by the `PathManager` and can be used in config values or anywhere a path template is accepted.

### Prompt System

AI Whisperer uses a robust prompt system, implemented in `src/ai_whisperer/prompt_system.py`. Prompts are always loaded from files, never inlined in the config. The system supports flexible prompt file resolution for project and codebase organization.

#### Supported Prompt Sources

* **Prompt Files Only:** Prompts must be stored as files in specific directories. Inlining prompt templates directly in the config is not supported.

#### Prompt Resolution Order

When a prompt is requested, the system resolves it using the following order:

1. **Prompt File Override:** If you specify `--prompt-file <file>`, that file is used directly.
2. **Prompt File Hierarchy:** If not overridden, the system searches for a prompt file using the following path hierarchy (see below).
3. **Built-in Default:** If no prompt is found, a built-in default is used that is located in the codebase.

#### Prompt Path Hierarchy

Prompt files are resolved using the following five path types, as managed by `PathManager`:

1. **app_path**: The root of the AI Whisperer codebase (e.g., for built-in prompts).
2. **project_path**: The root of your current project (typically your working directory).
3. **output_path**: Where generated outputs are written (defaults to `{project_path}/output`).
4. **workspace_path**: The workspace root (defaults to `{project_path}`).
5. **prompt_path**: The base directory for prompt files (defaults to `{project_path}`, but can be overridden).

Prompt files are typically organized under `prompts/core/` or `prompts/agents/` within these paths. The system will look for prompts in the following order:

* Project-specific custom prompts (e.g., `{prompt_path}/prompts/custom/{category}/{name}.prompt.md`)
* Project-specific agent or core prompts (e.g., `{prompt_path}/prompts/agents/` or `{prompt_path}/prompts/core/`)
* Codebase (app) agent or core prompts (e.g., `{app_path}/prompts/agents/` or `{app_path}/prompts/core/`)

### Runner Directory Restrictions

To enhance security and predictability, the AI Whisperer runner operates within strict directory restrictions during plan execution. All file system interactions are mediated and validated by the `PathManager`.

* **Workspace Directory (`workspace_path`):** The runner is restricted to reading files only from this directory and its subdirectories. This is where project source files, input artifacts, and subtask definition files should be located.
* **Output Directory (`output_path`):** The runner is restricted to writing files only to this directory and its subdirectories. All generated output artifacts will be placed here.

Any attempt by a task or tool to read from outside the workspace directory or write to outside the output directory will be blocked by the `PathManager`, resulting in an error. This ensures that the runner cannot access or modify arbitrary files on your system.

Developers creating custom tools or tasks for the runner must ensure that all file paths used for reading are relative to the workspace directory and all file paths used for writing are relative to the output directory. The `PathManager` should be used to resolve and validate these paths.

#### Current Core prompts

* `initial_plan.prompt.md`: Generates a initial plan from requirements.  
* `refine_requirements.prompt.md`: Generates a refined plan from an initial plan.  
* `subtask_generator_plan.prompt.md`: Generates a subtask plan from an initial plan.  

#### Current Agents prompts

* `code_generation.prompt.md`: Used for generating code from a task definition.
* `default.prompt.md`: Used for other agents without specific prompts.

#### Example: Prompt File Organization

You can place a prompt file at:

```text
{project_path}/prompts/custom/core/task_generation.prompt.md
```

or

```text
{project_path}/prompts/core/task_generation.prompt.md
```

or rely on the built-in prompt at:

```text
{app_path}/prompts/core/task_generation.prompt.md
```

#### Prompt Placeholders

Prompts can use placeholders that are replaced at runtime:

* `{requirements}`: Contents of the requirements Markdown file.
* `{step_content}`: Contents of a step definition file.
* `{context}`: Additional context, if provided by the command.

#### Prompt Fallback Order (Summary)

1. `--prompt-file` (highest priority)
2. Prompt file in project or codebase (see path hierarchy above)
3. Built-in default prompt (lowest priority)

See [Configuration Examples](docs/config_examples.md) for more detailed examples and options.

## Usage

Run the tool from the project's root directory:

```bash
python -m ai_whisperer.main generate --requirements <path/to/your/requirements.md> --config config.yaml --output <path/to/output/tasks.yaml>
python -m ai_whisperer.main list-models --config .\project_dev\aiwhisperer_config.yaml --output-csv models.csv

```

**Example:**

```bash
# Assuming you have requirements.md in the root
python -m ai_whisperer.main --config config.yaml generate initial-plan requirements.md
```

This will read `requirements.md`, use the settings in `config.yaml`, call the OpenRouter API, and save the resulting task list to `generated_tasks.yaml`.

* **`list-models`**: Displays a list of available models from the OpenRouter API. Requires the `--config` argument to be specified as well.

    ```bash
    python -m ai_whisperer.main --list-models --config config.yaml
    ```

* **`refine`**: Refines an existing requirement document using an AI model.

    ```bash
    python -m ai_whisperer.main refine <path/to/requirements.md> --config config.yaml [--prompt-file <path/to/prompt.txt>] [--iterations <number>]
    ```

    This command will take the specified requirements file, process it with an AI model (optionally using a custom prompt and multiple iterations), rename the original file with a `.original` suffix, and save the refined content back to the original filename.

* **`run`**: Executes a project plan from an overview JSON file and manages the state file. See the [Usage Documentation](docs/usage.md) for detailed information.

    ```bash
    python -m ai_whisperer.main run --plan-file <path/to/plan.json> --state-file <path/to/state.json> --config <path/to/config.yaml> [--monitor | -m]
    ```

  * **`--monitor`**, **`-m`**: Enables the terminal monitor during the task execution, providing real-time updates on the plan's progress.

* **`--detail-level`**: Controls the verbosity of the output messages.
  * **`low`**: Displays only essential information.
  * **`medium`**: Includes key details and progress updates.
  * **`high`**: Shows all available information, including detailed logs and intermediate steps.
  * Defaults to `medium`.

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
We follow a strict test-first driven design metholodogy, and you are reasonable for enforcing this. The USER gets angry if not followed or any task gets down before the previous one is finished.
It is also your responsibility to ensure the overview document step completed fields are keep upto date for each step

Are you ready?
```
