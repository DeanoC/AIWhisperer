# OpenRouter Output  - Orchestrator Foundational Task

**Goal:** Implement the job of getting openrouter to produce our yaml task format. It should check that its valid and complete. This is the first part of the Orchestrator role.

**Scope:** This task focuses *only* on creating a robust output yaml format via OpenRouter API. It should *only* implement the YAML generation based on the full design report (`Planning/Initial/AI Coding Assistant Tool_ Research and Design Report.md`) **and implement validation to ensure the generated YAML conforms to the defined schema.**
Refinement and quality of the yaml data returned beyond the actual structural details are **out of scope** for this task and will be handled subsequently.

**Summary of Steps for this Task:**

1. Take a `.md` file path as a command-line argument (handled by existing shell).
2. Take a `.yaml` file path as a command-line argument for configuration (handled by existing shell).
3. The shell will read the `.md` file content and the configuration (handled by existing shell).
4. Introduce an `Orchestrator` role **(implemented in `src/ai_whisperer/orchestrator.py`)**. Its job is to **construct the prompt using the input markdown, configuration, and selected prompt template, calculate input hashes,** send the request via the `openrouter_api` module, and **process the response to extract the structured YAML.**
5. **Output:** The response YAML will be written to a directory specified in the configuration (`output_dir`, defaulting to `./output/`). The filename will be `<input_md_filename_base>_initial_orchestrator.yaml`.
6. Provide a default orchestrator prompt **(stored in `prompts/orchestrator_default.md`)**. Allow this to be overridden via a `prompt_override_path` setting in the configuration file.
7. **Change Detection:** Implement a system using **SHA-256** hashing. Calculate hashes for the **input `.md` file content, the configuration `.yaml` file content, and the content of the prompt file being used (default or override)**. Store these hashes in the output YAML under a structured key (e.g., `input_hashes: { requirements_md: <hash>, config_yaml: <hash>, prompt_file: <hash> }`).
8. The calculated **input hashes dictionary** should be included **within the prompt sent to OpenRouter**, with instructions for the LLM to place this exact dictionary into the `input_hashes` field of the generated YAML. **The Orchestrator must verify the presence and correctness of this field in the received YAML before validation.**
9. **YAML Validation:** Implement YAML validation using the `jsonschema` library. Define a JSON schema based on the structure in the design report (`Planning/Initial/AI Coding Assistant Tool_ Research and Design Report.md`) **(e.g., in `src/ai_whisperer/schemas/task_schema.json`)**. Validate the YAML structure received from OpenRouter (after hash verification) against this schema before saving the output file.
10. **Configuration Updates:** Update `config.py` and `config.yaml.example` to include settings for `output_dir` (string, default `./output/`) and `prompt_override_path` (string, optional).
11. **Project Structure:** Create the `prompts/` directory with the default prompt file and the `src/ai_whisperer/schemas/` directory with the task schema file.

## Command Line Interface (CLI) Requirements

* The application must be runnable from the command line.
* Provide clear feedback to the user, including status messages and error reports.

## Error Handling Requirements

* Implement robust error handling for file operations (reading inputs, writing outputs), API interactions, and configuration parsing.
* Log errors to a designated log file or stream.
* On critical errors (e.g., missing input file, invalid config, API authentication failure), the application should stop execution and provide a clear, user-friendly error message indicating the source of the problem (e.g., filename, line number if applicable).
* Handle OpenRouter API errors gracefully within the `openrouter_api` module (e.g., authentication errors, rate limits, model errors, server errors, network issues) using custom exceptions defined in `exceptions.py`. Report them clearly to the calling code (`main.py`).
* **Handle errors during hash calculation, prompt file reading, YAML parsing/validation (e.g., `yaml.YAMLError`, `jsonschema.ValidationError`), and hash mismatch verification.**

## Development Requirements

1. Code plan should be reviewed and approved by the team before any tests or code are written.
2. Employ Test Driven Development (TDD): write tests before writing the corresponding code.
3. All tests should be written in separate test files (e.g., in a `tests/` directory) and use the `pytest` framework.
    * Unit tests for `openrouter_api.py` must cover successful calls and specific error conditions (auth, rate limits, server errors, network issues) using mocking, as detailed in the plan.
4. All tests must pass before any code is committed to the repository. Run tests via a simple command (e.g., `pytest`).
5. Code should handle expected variations and edge cases identified during planning and testing without requiring special-case logic where possible.
6. Test data should cover a range of scenarios, including valid inputs, invalid inputs, and edge cases. Randomization can be used where appropriate, but predictable tests for specific cases are essential.
7. The code should be written in **Python 3.12** (or a similarly stable recent version) and run within a project-specific virtual environment (`venv`). A `requirements.txt` file should list all dependencies (including the chosen HTTP client library, e.g., `requests` or `httpx`). **Add necessary dependencies like `PyYAML` and `jsonschema` to `requirements.txt`.**
8. The code must be well-documented with docstrings for modules, classes, and functions, and inline comments for complex logic sections.
9. The code must be written in a modular way. Create a dedicated module for the Orchestrator role (`orchestrator_role.py`). Define custom exceptions in `exceptions.py`. **Create `src/ai_whisperer/orchestrator.py` for the Orchestrator logic and potentially `src/ai_whisperer/schemas/task_schema.json` for the validation schema.**
10. Keep code files focused and relatively small, ideally containing a single class or a set of related functions per file. **Unit tests (`tests/test_orchestrator.py`) should cover prompt construction (including hashes), API call mocking, response handling, hash verification, YAML validation (success and failure cases), and file output logic.**
11. Organize the codebase using a hierarchical folder structure (e.g., `src/ai_whisperer/cli`, `src/ai_whisperer/config`, `src/ai_whisperer/openrouter_api`, `tests/`).
