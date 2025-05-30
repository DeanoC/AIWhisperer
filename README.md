# AI Whisperer

AI Whisperer is a Python-based AI development assistant that transforms project requirements written in Markdown into structured task definitions in JSON format. It features both command-line and interactive web interfaces for AI-powered software development workflows.

Designed for code development and project management, AI Whisperer enables you to:
- Convert requirements into detailed implementation plans
- Refine and iterate on plans using AI
- Generate comprehensive task breakdowns with subtasks
- Execute tasks through an interactive web interface with real-time AI assistance

The tool leverages a modular agent system where specialized AI agents (Alice the Assistant, Patricia the Planner, Tessa the Tester) collaborate to help you throughout the development process.

## Features

* **Dual Interface**: Command-line tool for batch processing and interactive web UI for real-time development
* **Multi-Agent System**: Specialized AI agents for different tasks (planning, coding, testing)
* **Stateless Architecture**: Clean, maintainable design with direct streaming support
* **Requirements Processing**: Converts Markdown requirements into structured JSON task plans
* **Plan Refinement**: Iteratively improve plans using AI feedback
* **Task Decomposition**: Automatically breaks down complex tasks into manageable subtasks
* **Real-time Collaboration**: WebSocket-based communication for instant AI responses
* **OpenRouter Integration**: Access to multiple AI models through a unified API
* **Test-Driven Development**: Built with TDD using `pytest`
* **Postprocessing Pipeline**: Automatically enhances AI-generated content:
  * Cleans formatting issues (backticks, quotes)
  * Adds required metadata (task_id, timestamps)
  * Validates and corrects JSON structure

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


### Interactive Mode (Recommended)

Start the interactive web interface:

```bash
# Start the backend server (recommended)
ai-whisperer-interactive

# Or, start manually:
python -m interactive_server.main

# In a separate terminal, start the frontend (requires Node.js)
cd frontend
npm start
```

Then open http://localhost:3000 in your browser to access the AI Whisperer interface.


### Command-Line Interface (Batch Mode)

For batch processing and automation:

```bash
# Run a batch script
ai-whisperer my_batch_script.txt --config config.yaml
```

Legacy commands (to be removed):
```bash
# Generate initial plan from requirements
python -m ai_whisperer.main generate initial-plan requirements.md --config config.yaml

# Generate overview with subtasks
python -m ai_whisperer.main generate overview-plan initial_plan.json --config config.yaml

# Generate complete plan (initial + overview + subtasks)
python -m ai_whisperer.main generate full-plan requirements.md --config config.yaml
```

### Available Commands

* **`list-models`**: List available AI models from OpenRouter

    ```bash
    python -m ai_whisperer.main list-models --config config.yaml --output-csv models.csv
    ```

* **`refine`**: Refine requirements using AI feedback

    ```bash
    python -m ai_whisperer.main refine requirements.md --config config.yaml [--iterations 3]
    ```

* **`generate initial-plan`**: Create initial task plan from requirements

    ```bash
    python -m ai_whisperer.main generate initial-plan requirements.md --config config.yaml
    ```

* **`generate overview-plan`**: Generate detailed breakdown with subtasks

    ```bash
    python -m ai_whisperer.main generate overview-plan initial_plan.json --config config.yaml
    ```

* **`generate full-plan`**: Complete planning pipeline (initial + overview + subtasks)

    ```bash
    python -m ai_whisperer.main generate full-plan requirements.md --config config.yaml
    ```

## Agent System

AI Whisperer features specialized AI agents that assist with different aspects of development:

* **Alice the Assistant** - General development support and guidance
* **Patricia the Planner** - Creates structured implementation plans from requirements
* **Tessa the Tester** - Generates comprehensive test suites and test plans

Agents can be switched on-the-fly in the interactive interface, allowing you to get specialized help for different tasks.

## Development

To run tests:

```bash
pip install -r requirements.txt # Ensure dev dependencies like pytest are installed
pytest
```

## Architecture

AI Whisperer uses a modern, stateless architecture:

* **Backend**: FastAPI server with WebSocket support for real-time communication
* **Frontend**: React TypeScript application with Material-UI components
* **Agent System**: Modular design allowing easy addition of new AI agents
* **Session Management**: Isolated sessions for concurrent users
* **Tool System**: Pluggable tools for file operations and command execution

For detailed architecture information, see [docs/architecture/](docs/architecture/).
