# Orchestrator YAML Generation - Implementation Plan

**Date:** May 4, 2025

**Goal:** Implement the initial Orchestrator functionality as defined in the refined `Planning/Outrouter output.md`. This involves taking input markdown and configuration, generating a prompt with input hashes, calling the OpenRouter API, verifying the returned hash, validating the response YAML against a schema, and saving the validated output.

**Scope:**

* **In Scope:**
  * Creating the `src/ai_whisperer/orchestrator.py` module.
  * Implementing hashing logic (SHA-256) for input markdown, config YAML, and prompt file content.
  * Implementing prompt construction logic, incorporating the input markdown content, configuration details, selected prompt template content, and the calculated input hashes dictionary.
  * Integrating with `openrouter_api.py` to send the request.
  * Implementing response processing: extracting the YAML content, verifying the `input_hashes` field matches the calculated hashes.
  * Creating the JSON schema (`src/ai_whisperer/schemas/task_schema.json`) based on the design report.
  * Implementing YAML validation using `PyYAML` for parsing and `jsonschema` for validation against the schema.
  * Implementing output file writing logic according to the specified naming convention and directory (`<input_md_filename_base>_initial_orchestrator.yaml` in `output_dir`).
  * Updating `config.py` and `config.yaml.example` with `output_dir` and `prompt_override_path`.
  * Creating the `prompts/` directory and the default prompt file `orchestrator_default.md`.
  * Adding `PyYAML` and `jsonschema` to `requirements.txt`.
  * Writing unit tests (`tests/test_orchestrator.py`) covering hashing, prompt generation, response handling (hash check, validation), and file output.
  * Integrating the Orchestrator logic into `main.py`.
* **Out of Scope:**
  * Implementing the full iterative refinement loops (pre/post-execution checks) described in the design report.
  * Executing any steps defined *within* the generated YAML.
  * Advanced error recovery beyond reporting failures.
  * Refining the quality/content of the LLM-generated YAML beyond structural validity.

**Implementation Details:**

1. **Project Structure & Setup:**
   * Create directory `prompts/`.
   * Create file `prompts/orchestrator_default.md` with initial placeholder content (e.g., instructing the LLM to convert the user requirements into the specified YAML format, including the provided `input_hashes`).
   * Create directory `src/ai_whisperer/schemas/`.
   * Create file `src/ai_whisperer/schemas/task_schema.json` and define the JSON schema corresponding to the YAML structure in the design report.
   * Add `PyYAML` and `jsonschema` to `requirements.txt`. Run `pip install -r requirements.txt` in the virtual environment.
2. **Configuration (`config.py`, `config.yaml.example`):**
   * Add `output_dir: str = "./output/"` to `AppConfig` in `config.py`.
   * Add `prompt_override_path: Optional[str] = None` to `AppConfig`.
   * Update `config.yaml.example` to include these new fields with comments.
   * Update `tests/test_config.py` if necessary.
3. **Hashing (`utils.py` or `orchestrator.py`):**
   * Implement a function `calculate_sha256(file_path: str) -> str` to read a file and return its SHA-256 hash. Handle potential `FileNotFoundError`.
   * Implement a function `calculate_content_sha256(content: str) -> str` to hash string content directly.
4. **Orchestrator Module (`orchestrator.py`):**
   * Define an `Orchestrator` class or functions.
   * **Initialization:** Takes `AppConfig` and input file paths.
   * **Hashing:**
     * Calculate hashes for the input markdown file, the config file, and the prompt file (using `prompt_override_path` if provided, else the default path). Store these in a dictionary `input_hashes`.
   * **Prompt Loading:** Read the content of the selected prompt file (default or override). Handle `FileNotFoundError`.
   * **Prompt Construction:** Create the final prompt string to send to the LLM. This should include:
     * Content from the loaded prompt template.
     * The full content of the input markdown file.
     * The `input_hashes` dictionary (formatted as a string, perhaps YAML or JSON within the prompt).
     * Clear instructions for the LLM to structure the output as YAML according to the schema and to include the *exact* `input_hashes` dictionary under the `input_hashes:` key in the output YAML.
   * **API Call:** Call `openrouter_api.call_openrouter` with the constructed prompt and configuration. Handle potential exceptions from the API module.
   * **Response Processing:**
     * Parse the LLM response string as YAML using `yaml.safe_load`. Handle `yaml.YAMLError`.
     * **Hash Verification:** Check if the parsed YAML is a dictionary and contains the `input_hashes` key. Compare the value of this key against the `input_hashes` dictionary calculated earlier. Raise a specific error (e.g., `InputHashMismatchError` defined in `exceptions.py`) if they don't match.
     * **Schema Validation:** Use `jsonschema.validate` to validate the parsed YAML data against the loaded schema from `task_schema.json`. Handle `jsonschema.ValidationError` and `jsonschema.SchemaError`. Load the schema once, perhaps during Orchestrator initialization.
   * **Output Writing:**
     * Determine the output filename: `<input_md_filename_base>_initial_orchestrator.yaml`.
     * Create the `output_dir` if it doesn't exist (`os.makedirs(exist_ok=True)`).
     * Write the *validated* YAML data back to the output file using `yaml.dump`. Handle file writing errors.
5. **Exceptions (`exceptions.py`):**
   * Define `InputHashMismatchError(Exception)`.
   * Define `YAMLValidationError(Exception)` (or reuse/wrap `jsonschema.ValidationError`).
   * Define `PromptTemplateError(Exception)`.
6. **Main Integration (`main.py`):**
   * Instantiate the `Orchestrator` after loading config and requirements.
   * Call the main orchestrator method (e.g., `orchestrator.run()`).
   * Wrap the call in a try/except block to catch potential Orchestrator-specific errors (Hashing errors, Prompt errors, `InputHashMismatchError`, `YAMLValidationError`, API errors) and print user-friendly messages.
7. **Testing (`tests/test_orchestrator.py`):**
   * Use `pytest` and mocking (`unittest.mock` or `pytest-mock`).
   * Mock file reads (`open`), hash calculations if needed, `openrouter_api.call_openrouter`, `yaml.safe_load`, `jsonschema.validate`, `yaml.dump`, `os.makedirs`.
   * Test hash calculation logic (mock file reads).
   * Test prompt loading (default and override paths, file not found).
   * Test prompt construction includes all necessary parts (markdown content, hashes).
   * Test successful workflow: mock API call returns valid YAML matching schema and hashes -> check `yaml.dump` is called correctly.
   * Test API error handling.
   * Test YAML parsing error (`yaml.YAMLError`).
   * Test hash mismatch error (`InputHashMismatchError`).
   * Test schema validation errors (`jsonschema.ValidationError`).
   * Test output directory creation and file writing.

**Checklist:**

* [X] Create `prompts/` directory. (Implicitly done by creating file within it)
* [X] Create `prompts/orchestrator_default.md`.
* [X] Create `src/ai_whisperer/schemas/` directory. (Implicitly done by creating file within it)
* [X] Create and define `src/ai_whisperer/schemas/task_schema.json`.
* [X] Add `PyYAML`, `jsonschema` to `requirements.txt`.
* [X] Run `pip install -r requirements.txt`.
* [X] Update `AppConfig` in `config.py` (`output_dir`, `prompt_override_path`).
* [X] Update `config.yaml.example`.
* [X] Update `tests/test_config.py`.
* [X] Implement hashing function(s) (in `utils.py`).
* [X] Define custom exceptions in `exceptions.py`.
* [X] Implement `Orchestrator` class/functions in `orchestrator.py`.
  * [X] Hashing logic.
  * [X] Prompt loading logic.
  * [X] Prompt construction logic.
  * [X] API call integration.
  * [X] Response parsing (`yaml.safe_load`).
  * [X] Hash verification logic.
  * [X] Schema validation logic (`jsonschema.validate`).
  * [X] Output file writing logic (`yaml.dump`).
* [X] Implement unit tests in `tests/test_orchestrator.py`.
  * [X] Test hashing.
  * [X] Test prompt loading.
  * [X] Test prompt construction.
  * [X] Test successful workflow (mocked API, validation, output).
  * [X] Test API error handling.
  * [X] Test YAML parsing error.
  * [X] Test hash mismatch error.
  * [X] Test schema validation error.
  * [X] Test output writing logic.
* [X] Integrate `Orchestrator` into `main.py` with error handling.
* [X] Ensure all tests pass (`pytest`).
* [X] Document new code with docstrings.
* [X] Review and refine `prompts/orchestrator_default.md`.
* [X] Manually test the end-to-end flow with `test_requirements.md` and `test.yaml`.
