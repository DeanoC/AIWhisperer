# OpenRouter API Integration - Foundational Task

**Goal:** Implement the foundational `ai_whisperer.openrouter_api` module for basic API interaction and integrate it minimally into the CLI shell.

**Scope:** This task focuses *only* on creating a robust and testable module to communicate with the OpenRouter API. Complex prompt engineering, detailed response parsing/validation, and YAML generation based on the full design report (`Planning/Initial/AI Coding Assistant Tool_ Research and Design Report.md`) are **out of scope** for this task and will be handled subsequently.

**Detailed Plan:** Refer to `AI Notes/openrouter-integration-plan.md` for specific implementation steps, module design, and testing strategy.

**Summary of Steps for this Task:**

1. Take a `.md` file path as a command-line argument (handled by existing shell).
2. Take a `.yaml` file path as a command-line argument for configuration (handled by existing shell). The configuration module (`config.py`) should be updated to securely handle the OpenRouter API key, preferably via an environment variable (`OPENROUTER_API_KEY`).
3. The shell will read the `.md` file content and the configuration (handled by existing shell).
4. **Placeholder Request Formulation:** For this task, the main application flow (`main.py`) will use a simple, hardcoded placeholder prompt. *Actual prompt construction using `.md` content and config prompts is deferred.*
5. **API Call:** The application will call a function within the new `ai_whisperer.openrouter_api` module, passing the placeholder prompt and configuration details (API key, model, parameters). This module will handle the actual HTTP request to OpenRouter.
6. **Basic Response Handling:** The `openrouter_api` module will return the raw text response from the OpenRouter API upon success. The `main.py` integration will simply print this raw response to the console. *Detailed response parsing and transformation into the target YAML format are deferred.*
7. **Output:** The raw response (or an error message) will be printed to the console. *Saving structured YAML is deferred.*

This task provides the essential API communication layer required for subsequent development.

## Command Line Interface (CLI) Requirements

* The application must be runnable from the command line.
* Use standard libraries like `argparse` or `click` to handle command-line arguments (e.g., `--requirements <path_to.md>`, `--config <path_to.yaml>`, `--output <path_to_output.yaml>`).
* Provide clear feedback to the user, including status messages and error reports.
* Utilize colored output for enhanced readability (e.g., using libraries like `rich` or `colorama`), especially for errors and prompts.
* *Future Enhancement:* Consider adding a REPL (Read-Eval-Print Loop) mode for interactive configuration or task definition.

## Error Handling Requirements

* Implement robust error handling for file operations (reading inputs, writing outputs), API interactions, and configuration parsing.
* Log errors to a designated log file or stream.
* On critical errors (e.g., missing input file, invalid config, API authentication failure), the application should stop execution and provide a clear, user-friendly error message indicating the source of the problem (e.g., filename, line number if applicable).
* Handle OpenRouter API errors gracefully within the `openrouter_api` module (e.g., authentication errors, rate limits, model errors, server errors, network issues) using custom exceptions defined in `exceptions.py`. Report them clearly to the calling code (`main.py`).

## Development Requirements

1. A detailed plan for this specific task is documented in `AI Notes/openrouter-integration-plan.md`.
2. Code plan should be reviewed and approved by the team before any tests or code are written.
3. Employ Test Driven Development (TDD): write tests before writing the corresponding code.
4. All tests should be written in separate test files (e.g., in a `tests/` directory) and use the `pytest` framework.
    * Unit tests for `openrouter_api.py` must cover successful calls and specific error conditions (auth, rate limits, server errors, network issues) using mocking, as detailed in the plan.
5. All tests must pass before any code is committed to the repository. Run tests via a simple command (e.g., `pytest`).
6. Code should handle expected variations and edge cases identified during planning and testing without requiring special-case logic where possible.
7. Test data should cover a range of scenarios, including valid inputs, invalid inputs, and edge cases. Randomization can be used where appropriate, but predictable tests for specific cases are essential.
8. The code should be written in **Python 3.12** (or a similarly stable recent version) and run within a project-specific virtual environment (`venv`). A `requirements.txt` file should list all dependencies (including the chosen HTTP client library, e.g., `requests` or `httpx`).
9. The code must be well-documented with docstrings for modules, classes, and functions, and inline comments for complex logic sections.
10. The code must be written in a modular way. Create a dedicated module for OpenRouter API interactions (`openrouter_api.py`). Define custom exceptions in `exceptions.py`.
11. Keep code files focused and relatively small, ideally containing a single class or a set of related functions per file.
12. Organize the codebase using a hierarchical folder structure (e.g., `src/ai_whisperer/cli`, `src/ai_whisperer/config`, `src/ai_whisperer/openrouter_api`, `tests/`).
13. The implementation plan for this task is located at `AI Notes/openrouter-integration-plan.md`. Follow the checklist within that document.
