# AI Whisperer - CLI Shell Design Plan

This document outlines the proposed design and structure for the initial Python command-line application shell, as defined in `Planning/Current Task.md`.

## 1. Project Structure

```text
d:\Projects\AIWhisperer\
├── .github/             # Optional: GitHub specific files (e.g., issue templates, workflows)
├── AI Notes/
│   └── cli-shell-design-plan.md  # This file
├── Planning/
│   ├── Current Task.md
│   └── Initial/
│       └── AI Coding Assistant Tool_ Research and Design Report.md
├── docs/                  # User documentation (for static site generation)
│   ├── index.md            # Landing page/overview
│   ├── usage.md            # How to use the CLI
│   └── configuration.md    # Details on config.yaml structure
├── src/
│   └── ai_whisperer/
│       ├── __init__.py
│       ├── main.py             # Main CLI entry point, argument parsing
│       ├── config.py           # Load and validate config.yaml
│       ├── openrouter_api.py   # Interact with OpenRouter API
│       ├── processing.py       # Read MD, format prompt, process response, write YAML
│       ├── exceptions.py       # Custom exception classes
│       └── utils.py            # Utility functions (e.g., colored output setup)
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_openrouter_api.py  # Requires mocking
│   ├── test_processing.py
│   └── test_main.py            # Integration/CLI tests
├── .gitignore                  # Git ignore rules
├── CODE_OF_CONDUCT.md          # Code of Conduct
├── CONTRIBUTING.md             # Contribution guidelines
├── LICENSE                     # Project license file (e.g., MIT, Apache 2.0)
├── README.md                   # Project overview, setup, usage
├── config.yaml.example         # Example configuration file structure
└── requirements.txt            # Python dependencies
```

## 2. Core Components & Responsibilities

* **`main.py`**:
  * Uses `argparse` for CLI argument parsing (`--requirements`, `--config`, `--output`).
  * Initializes logging and colored output (via `utils.py`).
  * Orchestrates the workflow:
    1. Load config (`config.py`).
    2. Read requirements markdown (`processing.py`).
    3. Format prompt (`processing.py`).
    4. Call OpenRouter API (`openrouter_api.py`).
    5. Process response into YAML (`processing.py`).
    6. Save output YAML (`processing.py`).
  * Handles top-level exceptions using custom exceptions from `exceptions.py` and provides user-friendly, colored error messages.
* **`config.py`**:
  * Defines a function `load_config(config_path)` that reads the YAML file.
  * Uses `PyYAML` for parsing.
  * Validates the presence of required keys (e.g., `openrouter_api_key`, `model`, `prompts`).
  * Returns a configuration object (e.g., a dictionary or a simple class/dataclass).
  * Raises `ConfigError` (from `exceptions.py`) for file not found, parsing errors, or missing keys.
* **`openrouter_api.py`**:
  * Defines a function `call_openrouter(api_key, model, prompt_text, params)` (or potentially a class if state is needed later).
  * Uses the `requests` library to make POST requests to the OpenRouter chat completions endpoint.
  * Constructs necessary headers (Authorization with API key) and payload.
  * Handles potential `requests` exceptions (connection errors, timeouts).
  * Checks the API response status code and content for errors (e.g., authentication, rate limits, invalid model).
  * Raises `APIError` (from `exceptions.py`) for API-specific issues.
  * Returns the content of the successful response (likely the generated text).
* **`processing.py`**:
  * `read_markdown(file_path)`: Reads the content of the requirements `.md` file. Raises `ProcessingError` if file not found/readable.
  * `format_prompt(template, md_content, config_vars)`: Takes a prompt template (from config), the markdown content, and other config variables, returning the final string to send to the API.
  * `process_response(response_text)`: Takes the raw text response from OpenRouter. Attempts to parse or structure it according to the preliminary YAML format defined in `Planning/Initial/`. This might be basic initially. Raises `ProcessingError` if the response cannot be processed.
  * `save_yaml(data, output_path)`: Saves the processed data structure to the specified output YAML file. Uses `PyYAML`. Raises `ProcessingError` on file writing issues.
* **`exceptions.py`**:
  * Defines custom exception classes inheriting from `Exception`:
    * `AIWhispererError` (base exception)
    * `ConfigError(AIWhispererError)`
    * `APIError(AIWhispererError)`
    * `ProcessingError(AIWhispererError)`
* **`utils.py`**:
  * `setup_logging()`: Configures basic logging (e.g., to console or file).
  * `setup_rich_output()`: Configures `rich` for colored console output (e.g., setting up a `Console` object). Could provide helper functions for printing errors/info in color.

## 3. Initial Dependencies (`requirements.txt`)

```txt
PyYAML>=6.0,<7.0
requests>=2.30,<3.0
pytest>=7.0,<8.0
rich>=13.0,<14.0
# argparse is built-in
```

## 4. TDD Workflow Outline

1. **Setup**: Create project structure, `requirements.txt`, basic `.gitignore`, `config.yaml.example`. Set up `venv`. Install deps.
2. **Exceptions**: Define custom exceptions in `exceptions.py`.
3. **Config**:
   * Write tests in `test_config.py` for `load_config`: valid YAML, file not found, invalid YAML, missing keys.
   * Run `pytest` to confirm the new tests fail as expected.
   * Implement `load_config` in `config.py` to pass tests.
4. **Processing (File I/O)**:
   * Write tests in `test_processing.py` for `read_markdown` (reads file, handles not found) and `save_yaml` (writes data, handles errors).
   * Run `pytest` to confirm the new tests fail as expected.
   * Implement these functions in `processing.py`.
5. **Processing (Core Logic)**:
   * Write tests for `format_prompt` (correctly inserts variables).
   * Write tests for `process_response` (handles expected basic response structure, handles errors). *Note: This will be simple initially.*
   * Run `pytest` to confirm the new tests fail as expected.
   * Implement these functions.
6. **OpenRouter API**:
   * Write tests in `test_openrouter_api.py` for `call_openrouter`. Use `pytest-mock` or `unittest.mock` to mock the `requests.post` call. Test successful calls, API error responses, connection errors.
   * Run `pytest` to confirm the new tests fail as expected.
   * Implement `call_openrouter` in `openrouter_api.py`.
7. **Utilities**:
   * Implement basic logging/output setup in `utils.py`. Tests might be minimal here initially.
8. **Main/CLI**:
   * Write tests in `test_main.py` using `pytest`'s `capsys` fixture or mocking subprocesses/entry points to test argument parsing and the main orchestration flow (checking if core functions are called with correct args). Mock dependencies (`config`, `processing`, `openrouter_api`).
   * Run `pytest` to confirm the new tests fail as expected.
   * Implement `main.py` entry point and argument handling.

## 5. Planning Checklist

* [x] Define project structure
* [x] Define core component responsibilities
* [x] List initial dependencies
* [x] Outline TDD workflow
* [x] Create initial project folders and files (`src/`, `tests/`, `docs/`, `__init__.py`s, `requirements.txt`, `.gitignore`, `config.yaml.example`, `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`)
* [x] Set up virtual environment (`venv`)
* [x] Install dependencies (`pip install -r requirements.txt`)
* [x] Implement `exceptions.py`
* [x] Write tests for `config.py`
* [x] Implement `config.py`
* [x] Write tests for `processing.py` (file I/O)
* [x] Implement `processing.py` (file I/O)
* [x] Write tests for `processing.py` (core logic)
* [x] Implement `processing.py` (core logic)
* [x] Write tests for `openrouter_api.py` (mocking needed)
* [x] Implement `openrouter_api.py`
* [x] Implement `utils.py`
* [x] Write tests for `main.py` (integration/mocking)
* [x] Implement `main.py`
* [x] Create basic `README.md`
