import pytest
import json
import jsonschema
from pathlib import Path
from unittest.mock import (
    patch,
    MagicMock,
    mock_open,
    PropertyMock,
)  # Import PropertyMock
import builtins  # Import builtins

from src.ai_whisperer.orchestrator import Orchestrator, DEFAULT_SCHEMA_PATH
from src.ai_whisperer.exceptions import (
    ConfigError,
    PromptError,
    HashMismatchError,
    OrchestratorError,
    ProcessingError,
    OpenRouterAPIError,
)

# --- Fixtures ---


@pytest.fixture
def mock_config():
    """Provides a basic valid configuration dictionary."""
    return {
        "openrouter": {
            "api_key": "test_api_key",
            "model": "test_model",
            "params": {"temperature": 0.7},
        },
        "prompts": {
            # This section might not be directly used by Orchestrator itself
            # but is required by the config loader
            "some_prompt": "template"
        },
        "output_dir": "./test_output/",  # Use a specific test output dir
        # prompt_override_path is no longer used
        "task_prompts_content": {  # Add loaded prompt content to the mock config
            "orchestrator": "Mock Orchestrator Prompt Content"
        },
        "task_model_configs": {  # Add task model config to the mock config
            "orchestrator": {
                "api_key": "test_api_key",
                "model": "test_model",
                "params": {"temperature": 0.7},
            }
        },
    }


@pytest.fixture
def mock_schema_content():
    """Provides a basic valid JSON schema content."""
    return json.dumps(
        {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "input_hashes": {
                    "type": "object",
                    "properties": {
                        "requirements_md": {"type": "string"},
                        "config_json": {"type": "string"},
                        "prompt_file": {"type": "string"},
                    },
                    "required": ["requirements_md", "config_json", "prompt_file"],
                },
                "plan": {"type": "array"},
            },
            "required": ["task_id", "input_hashes", "plan"],
        }
    )


@pytest.fixture
def mock_prompt_content():
    """Provides basic prompt template content."""
    return "# Mock Prompt\n\nYou are an AI assistant tasked with converting a user's natural language requirements into a structured JSON task plan.\n\n**User Requirements Provided:**\n\n```text\n{{md_content}}\n```\n\n"


@pytest.fixture
def mock_requirements_content():
    """Provides basic requirements markdown content."""
    return "# Project Requirements\n- Do the thing"


@pytest.fixture
def mock_valid_api_response_json():
    """Provides a basic valid JSON structure matching the mock schema."""
    return {
        "task_id": "task-123",
        "input_hashes": {
            "requirements_md": "req_hash",
            "config_json": "config_hash",
            "prompt_file": "prompt_hash",
        },
        "plan": [{"subtask_id": "step-1", "description": "First step"}],
    }


@pytest.fixture
def setup_orchestrator_files(tmp_path, mock_schema_content):
    """Sets up necessary default files (schema) in a temporary directory."""
    # Simulate the project structure relative to a mock package root within tmp_path
    mock_package_root = tmp_path / "src" / "ai_whisperer"
    mock_package_root.mkdir(parents=True, exist_ok=True)

    # Create a mock default prompt file so load_config can find it if needed
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    default_prompt_path = prompts_dir / "orchestrator_default.md"
    default_prompt_path.write_text("Default Orchestrator Content", encoding="utf-8")

    # Mock schema files
    schema_dir = mock_package_root / "schemas"
    schema_dir.mkdir(exist_ok=True)

    # Mock task schema file
    task_schema_path = schema_dir / "task_schema.json"
    task_schema_path.write_text(mock_schema_content, encoding="utf-8")

    # Mock subtask schema file (minimal valid schema)
    subtask_schema_content = """{
  "type": "object",
  "properties": {
    "description": {
      "type": "string",
      "description": "A detailed description of the subtask's purpose and instructions."
    },
    "instructions": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "description": "Specific instructions for the AI agent executing this subtask."
    },
    "input_artifacts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Input artifacts for the subtask."
    },
    "output_artifacts": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Output artifacts for the subtask."
    },
    "constraints": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Constraints that must be adhered to while executing the subtask."
    },
    "validation_criteria": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Criteria for validating the output of the subtask."
    },
    "subtask_id": {
      "type": "string",
      "description": "Unique identifier for the subtask (e.g., UUID)",
      "format": "uuid"
    },
    "task_id": {
      "type": "string",
      "description": "ID of the parent task plan this subtask belongs to.",
      "format": "uuid"
    }
  },
  "required": [
    "description",
    "instructions",
    "input_artifacts",
    "output_artifacts",
    "constraints",
    "validation_criteria",
    "subtask_id",
      "task_id"
  ],

  "additionalProperties": false
}"""
    subtask_schema_path = schema_dir / "subtask_schema.json"
    subtask_schema_path.write_text(subtask_schema_content, encoding="utf-8")

    # Patch the constants in orchestrator module to point to tmp_path locations
    # Note: DEFAULT_SCHEMA_PATH is for the main task schema used by Orchestrator.__init__
    with patch("src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH", task_schema_path):
        # The fixture now only creates the files and yields the paths/content
        yield {
            "schema_path": task_schema_path,  # Keep this for backward compatibility if needed
            "task_schema_path": task_schema_path,
            "subtask_schema_path": subtask_schema_path,
            "subtask_schema_content": subtask_schema_content,  # Yield subtask schema content
            "tmp_path": tmp_path,
            "default_prompt_path": default_prompt_path,  # Include the path to the created default prompt
        }
        # No teardown needed for json_validator state here, patching in test handles it


# --- Test Cases ---


def test_orchestrator_init_success(mock_config, setup_orchestrator_files):
    """Tests successful initialization of the Orchestrator."""
    orchestrator = Orchestrator(mock_config)
    assert orchestrator.config == mock_config
    assert orchestrator.task_schema is not None  # Check schema loaded
    assert (
        orchestrator.openrouter_client.model
        == mock_config["task_model_configs"]["orchestrator"]["model"]
    )
    assert (
        orchestrator.openrouter_client.params
        == mock_config["task_model_configs"]["orchestrator"]["params"]
    )


def test_orchestrator_init_missing_openrouter_config(setup_orchestrator_files):
    """Tests initialization fails if 'openrouter' config is missing."""
    bad_config = {"prompts": {}, "output_dir": "."}
    with pytest.raises(
        ConfigError, match="'openrouter' configuration section is missing"
    ):
        Orchestrator(bad_config)


def test_orchestrator_init_schema_not_found(mock_config, tmp_path):
    """Tests initialization fails if the schema file cannot be found."""
    # Don't use setup_orchestrator_files fixture, ensure schema doesn't exist
    # Patch the path constant to point to a non-existent file
    non_existent_schema_path = tmp_path / "non_existent_schema.json"
    with patch(
        "src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH", non_existent_schema_path
    ):
        with pytest.raises(FileNotFoundError):
            Orchestrator(mock_config)


def test_orchestrator_init_invalid_schema_json(mock_config, tmp_path):
    """Tests initialization fails if the schema file contains invalid JSON."""
    schema_path = tmp_path / "invalid_schema.json"
    schema_path.write_text("this is not json", encoding="utf-8")
    with patch("src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH", schema_path):
        with pytest.raises(ConfigError, match="Invalid JSON in schema file"):
            Orchestrator(mock_config)


# --- Subtask Generation Tests ---


class TestOrchestratorSubtasks:
    @pytest.fixture
    def mock_config(self):
        return {
            "openrouter": {"api_key": "test_key", "model": "test_model", "params": {}},
            "output_dir": "/tmp/output",
            "task_prompts_content": {  # Provide loaded prompt content
                "orchestrator": "Mock Orchestrator Prompt Content for Subtask Test"
            },
            "task_model_configs": {  # Provide task model config
                "orchestrator": {
                    "api_key": "test_key",
                    "model": "test_model",
                    "params": {},
                }
            },
        }

    @pytest.fixture
    def orchestrator(self, mock_config, setup_orchestrator_files):
        # The schema loading is now handled by setup_orchestrator_files patching DEFAULT_SCHEMA_PATH
        # and Orchestrator.__init__ reading from that path.
        # We just need to ensure the mock_config has the necessary prompt content.
        return Orchestrator(mock_config)

    # mock_prompt_content fixture is no longer needed as prompt content is in mock_config

    @patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI.call_chat_completion")
    @patch("src.ai_whisperer.orchestrator.Path.is_file", return_value=True)
    @patch("src.ai_whisperer.orchestrator.calculate_sha256", return_value="test_hash")
    @patch("src.ai_whisperer.orchestrator.json.loads")
    @patch("os.replace")
    @patch("os.makedirs")
    @patch(
        "os.path.exists", return_value=True
    )  # Assume directory exists for simplicity in this test
    @patch(
        "builtins.open", new_callable=mock_open
    )  # Keep open for reading requirements.md
    def test_generate_full_project_plan(
        self,
        mock_open_file,
        mock_path_exists,
        mock_makedirs,
        mock_replace,
        mock_json_loads,
        mock_hash,
        mock_is_file,
        mock_api_call,
        orchestrator,
        mock_prompt_content,
        mock_requirements_content,
        setup_orchestrator_files,
    ):
        # Configure the mock_open_file to return mock requirements content when requirements.md is opened
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            mock_requirements_content
        )

        # The API call should return a simple JSON string wrapped in code fences to simulate AI response
        mock_api_call.return_value = """```json
    {
      "natural_language_goal": "Test goal",
      "plan": [
    {"subtask_id": "step1"},
    {"subtask_id": "step2"}
      ]
    }

**Output:**

# Orchestrator Default Prompt
```

You are an AI assistant tasked with converting a user's natural language requirements into a structured JSON task plan.

**Input:**

1. **User Requirements:** A markdown document containing the user's goal.

**Output:**

Produce **only** a JSON document, enclosed in ```json fences, adhering strictly to the following schema:

The JSON document must be an object with the following properties:
- natural_language_goal (string): A concise summary of the user's main objective
- overall_context (string, optional): Shared background information, constraints, style guides, etc., applicable to all steps
- plan (array): An array of step objects, each with:
  - subtask_id (string): Unique identifier for this step within the task (e.g., 'step-1', 'generate-code')
  - description (string): Human-readable description of the step's purpose
  - depends_on (array of strings, default []): List of subtask_ids that must be completed before this step
  - type (string): Categorizes the step type. Prefer types from the prioritized list in instructions (e.g., 'planning', 'code_generation', 'test_generation', 'file_edit', 'validation', 'documentation').
  - input_artifacts (array of strings, default []): List of required input file paths or data identifiers
  - output_artifacts (array of strings, default []): List of expected output file paths or data identifiers
  - instructions (string): Detailed instructions for the AI agent executing this step. MUST be a single string, using proper JSON string escaping with newline characters (\n) for readability.
  - constraints (array of strings, default []): Specific rules or conditions the output must satisfy
  - validation_criteria (array of strings, default []): Conditions to check for successful completion
  - model_preference (object or null, default null): Optional model preferences with properties like provider, model, temperature, and max_tokens
  - provider (string): The model provider (e.g., 'openai', 'cohere', 'anthropic')
Required properties: natural_language_goal, plan
No additional properties are allowed at the top level.

**Instructions:**

1. **Analyze the provided `User Requirements` EXCLUSIVELY.**
   * **Your entire response MUST be based SOLELY on the User Requirements section.**
   * **DO NOT invent, hallucinate, or generate plans for features or tasks NOT explicitly described in the `User Requirements`.**
   * **If the `User Requirements` describes Feature X, the generated plan MUST implement Feature X and ONLY Feature X.**
2. Focus on the core task requirements and structure.
3. Set the `natural_language_goal` field to a concise summary of the user's main objective **based *only* on the requirements in `User Requirements`**.
4. If applicable, populate the `overall_context` field with a **single string** containing any shared background information, constraints, or style guides relevant to the entire task **as derived from `User Requirements`**. Do not use complex objects or nested structures here. If not applicable, omit this field or set it to an empty string.
6. Decompose the requirements **from `User Requirements`** into a logical sequence of steps (plan). Define `subtask_id`, `description`, `depends_on` (if any), and `agent_spec` for each step. **The entire plan must directly implement the requirements specified in `User Requirements`.** **Use concise, descriptive, `snake_case` names for `subtask_id` (e.g., `generate_tests`, `implement_feature`). Avoid hyphens.** Ensure `depends_on` is always present, using an empty list `[]` for initial steps.
7. Populate the `agent_spec` with appropriate `type`, `input_artifacts`, `output_artifacts`, detailed `instructions`, and optionally `constraints` and `validation_criteria`, **all derived from the analysis of `User Requirements`**.
   * **Include meaningful `validation_criteria` for all step types, including `planning` and `documentation`, to clearly verify step completion.**
       * For `planning` steps, consider adding an output artifact (e.g., `docs/analysis_summary.md`) and validating its creation and content clarity. Example:

           ```json
           "output_artifacts": [
             "docs/analysis_summary.md"
           ],
           "validation_criteria": [
             "docs/analysis_summary.md exists.",
             "docs/analysis_summary.md clearly identifies required code changes and test scenarios.",
             "docs/analysis_summary.md outlines a high-level implementation plan."
           ]
           ```

       * For `documentation` steps, ensure criteria explicitly cover all documented items separately. Example:

           ```json
           "validation_criteria": [
             "README.md clearly documents the new CLI option.",
             "CLI help message clearly documents the new CLI option."
           ]
           ```

   * **Use explicit and consistent relative paths for artifacts** (e.g., `src/module/file.py`, `tests/unit/test_file.py`, `docs/feature.md`). Ensure consistency in path structure (e.g., always use `tests/unit/` for unit tests).

8. **IMPORTANT JSON FORMATTING GUIDELINES:** For text fields that might contain special characters:

   * For `overall_context`, ensure proper JSON string escaping:

   ```json
   "overall_context": "This is text with special characters: colons, dashes, etc.\nThe newline character ensures proper formatting."
   ```

  * Similarly for `agent_spec.instructions`:

   ```json
   "instructions": "Step 1: Do this first.\nStep 2: Then do this next."
   ```

9. **Prioritize Agent Types:** When assigning the `agent_spec.type`, prioritize using types from the following list where applicable:
   * `planning`: For steps involving breaking down tasks, analyzing requirements, or designing approaches.
   * `code_generation`: For steps that write new code files or significant code blocks.
   * `test_generation`: Specifically for generating unit tests or test cases.
   * `file_edit`: For steps that modify existing files (code, configuration, documentation). Use this instead of `code_generation` for modifications.
   * `validation`: For steps that check code quality, run tests, or verify outputs against criteria (e.g., linting, testing execution, schema validation).
   * `documentation`: For steps focused on writing or updating documentation (READMEs, docstrings, comments).
   * `file_io`: For basic file operations like creating directories, moving files, etc., if needed as separate steps.
   * `analysis`: For steps focused on understanding existing code or data before modification or generation.
   * `refinement`: For steps specifically designed to improve or correct the output of a previous step based on feedback or validation results.
   If none of these fit well, you may use another descriptive type.
10. **Strict Test-Driven Development (TDD):** This project MANDATES a strict TDD methodology. For **any** step involving the creation or modification of executable code (i.e., `type: 'code_generation'` or `type: 'file_edit'`) **required by `User Requirements`**:

* **Test Generation First:** The plan **must** include a dedicated step (`type: 'test_generation'`) that **strictly precedes** the corresponding `code_generation` or `file_edit` step in the plan sequence. This test step must generate tests specifically for the code that will be created or modified in the subsequent step.
* **Dependency on Tests:** The `code_generation` or `file_edit` step **must** list the corresponding `test_generation` step ID in its `depends_on` list.
* **Validation After:** Following the `code_generation` or `file_edit` step, the plan **must** include a dedicated step (`type: 'validation'`) responsible for executing the specific tests generated in the preceding `test_generation` step. This validation step **must** depend on the `code_generation` or `file_edit` step.
* **Test Generation Instructions:** The `test_generation` step's instructions should emphasize creating tests that thoroughly verify the requirements for the *specific code being generated/modified in the next step*. Avoid special casing (e.g., use randomized or varied inputs/identifiers where appropriate, not just fixed examples). Its `validation_criteria` must ensure the test file(s) are created or updated appropriately (e.g., `tests/unit/test_my_feature.py exists`, `tests/unit/test_my_feature.py contains test_new_functionality`).
* **Validation Instructions:** The `validation` step's instructions must specify running the relevant tests generated in the preceding test step (e.g., using `pytest tests/unit/test_my_feature.py::test_new_functionality`). Its `validation_criteria` must confirm that the test execution command runs successfully and that the specific tests pass (e.g., `pytest tests/unit/test_my_feature.py::test_new_functionality executes successfully`, `Test test_new_functionality in tests/unit/test_my_feature.py passes`).
* **Code/Edit Agent Instructions:** The instructions for the `code_generation` or `file_edit` agent **must** explicitly forbid implementing code that *only* passes the specific generated tests (i.e., no special-case logic tailored solely to the tests). The code must correctly implement the required functionality as described in the requirements.

11. **Code Reuse:** For steps with `type: 'code_generation'` or `type: 'file_edit'` **required by `User Requirements`**, ensure the `agent_spec.instructions` explicitly directs the executor agent to:

* First, examine the existing codebase (especially potentially relevant utility modules like `utils.py`, `config.py`, `exceptions.py`, etc.) for functions, classes, constants, or custom exceptions that can be reused to fulfill the task. **Mention specific potentially relevant modules (including `exceptions.py` if error handling is involved) in the instructions.**
* Only implement new logic if suitable existing code cannot be found or adapted.
* If reusing code, ensure it's imported and used correctly according to project conventions.

12. **JSON Syntax for Strings:** Pay close attention to valid JSON syntax. **ABSOLUTELY DO NOT use markdown-style backticks (`) within JSON string values.** This applies especially to array items in fields like `validation_criteria`, `constraints`, `input_artifacts`, and `output_artifacts`.

* **Correct:** Use properly escaped JSON strings (e.g., `"README.md"`) when referring to files or code elements in these arrays.
* **Incorrect (DO NOT DO THIS):**

       ```json
       "validation_criteria": [
         "`README.md` contains documentation", // INVALID JSON
         "Check `src/main.py` for changes" // INVALID JSON
       ]
       ```

* **Correct Example:**

       ```json
       "validation_criteria": [
         "README.md contains documentation",
         "Check src/main.py for changes",
         "Output file output/result.txt exists"
       ]
       ```

* Backticks (`) are ONLY acceptable when they are part of the *content* of a properly escaped JSON string.

13. Format the `description` and `instructions` fields clearly and actionably. **Crucially, the `instructions` field MUST be a single JSON string.** Use proper JSON string escaping with newline characters (`\n`) and internal markdown formatting (e.g., bullet points, numbered lists, and backticks for code elements *within this string*) for clarity, similar to the project's planning documents.

* **Example of correct multi-line instructions string:**

       ```json
       "instructions": "# Action 1\nUpdate the file `config.py` based on X.\n- Detail A\n- Detail B\n# Action 2\nGenerate the second file using Y."
       ```

* **Do NOT generate a JSON array like `"instructions": ["Line 1", "Line 2"]`.**

14. **JSON Structure:** Ensure the generated JSON is perfectly valid. Each property must follow proper JSON syntax with commas separating properties and no trailing comma after the last property. Arrays and objects must be properly closed with matching brackets and braces. All property names must be enclosed in double quotes.

**User Requirements Provided:**

```text
{md_content}
```
"""
        # Define the raw data expected before postprocessing adds hashes/id
        raw_plan_data = {"plan": [{"subtask_id": "step1"}, {"subtask_id": "step2"}]}
        # Define the data expected AFTER postprocessing and for the file read-back
        # This should include task_id and input_hashes at the top level
        expected_plan_data = {
            "task_id": "mock_task_id_1",
            "natural_language_goal": "Mock natural language goal",  # Added missing field
            "input_hashes": {
                "requirements_md": "test_hash",
                "config_yaml": "test_hash",
                "prompt_file": "test_hash",
            },
            "plan": [
                {
                    "subtask_id": "step1",
                    "file_path": "output/subtask_step1.json",
                    "depends_on": [],
                    "type": "test_type_1",
                },
                {
                    "subtask_id": "step2",
                    "file_path": "output/subtask_step2.json",
                    "depends_on": ["step1"],
                    "type": "test_type_2",
                },
            ],
        }
        # Convert to JSON string for mock_open
        expected_json_content = json.dumps(expected_plan_data)

        # Mock json loads - ensure we provide enough mock returns
        # The StopIteration error indicates we need more return values
        mock_json_loads.side_effect = [
            # Call 1: Parse the raw API response JSON string
            raw_plan_data,
            # Call 2: Inside add_items_postprocessor
            raw_plan_data,
            # Call 3: After postprocessing in generate_initial_json
            expected_plan_data,
            # Call 4: Reading file back in generate_full_project_plan
            expected_plan_data,
            # Call 5: Add extra return value for any additional calls
            expected_plan_data,
            # Call 6: Add another value just to be safe
            expected_plan_data,
        ]

        # Mock jsonschema validation and subtask generator
        # Also mock json.load specifically for reading the saved task plan file
        with patch("src.ai_whisperer.orchestrator.jsonschema.validate"):
            with patch(
                "src.ai_whisperer.subtask_generator.SubtaskGenerator"
            ) as mock_subtask_gen:

                with patch(
                    "src.ai_whisperer.orchestrator.json.load"
                ) as mock_json_load_file:
                    # Configure mock_json_load_file to return the expected data when the task plan file is read
                    # This mock is needed because StateManager.load_state uses json.load
                    mock_json_load_file.return_value = expected_plan_data

                    mock_generator = MagicMock()
                    # Updated mock return values to match the new subtask schema
                    mock_generator.generate_subtask.side_effect = [
                        (
                            Path("/tmp/output/subtask_step1.json"),
                            {
                                "subtask_id": "mock_subtask_id_1",
                                "task_id": "mock_task_id_1",
                                "description": "Mock description 1",
                                "instructions": ["Mock instruction 1"],
                                "input_artifacts": [],
                                "output_artifacts": [],
                                "constraints": [],
                                "validation_criteria": [],
                            },
                        ),
                        (
                            Path("/tmp/output/subtask_step2.json"),
                            {
                                "subtask_id": "mock_subtask_id_2",
                                "task_id": "mock_task_id_1",
                                "description": "Mock description 2",
                                "instructions": ["Mock instruction 2"],
                                "input_artifacts": [],
                                "output_artifacts": [],
                                "constraints": [],
                                "validation_criteria": [],
                            },
                        ),
                    ]
                    mock_subtask_gen.return_value = mock_generator
                    # Call the method under test
                    result = orchestrator.generate_full_project_plan(
                        "requirements.md", "config.json"
                    )
                    # Check that the openrouter call had the correct arguments
                    mock_api_call.assert_called_once()
                    call_args = mock_api_call.call_args
                    assert "prompt_text" in call_args[1]
                    assert "model" in call_args[1]
                    assert "params" in call_args[1]
                    assert call_args[1]["model"] == orchestrator.openrouter_client.model
                    assert (
                        call_args[1]["params"] == orchestrator.openrouter_client.params
                    )
                    # Assertions
                    assert result is not None
                    assert "task_plan" in result
                    assert "subtasks" in result
                    assert len(result["subtasks"]) == 2
                    assert result["subtasks"][0] == Path(
                        "/tmp/output/subtask_step1.json"
                    )
                    assert mock_generator.generate_subtask.call_count == 2

    @patch("src.ai_whisperer.ai_service_interaction.OpenRouterAPI.call_chat_completion")
    @patch("src.ai_whisperer.orchestrator.Path.is_file", return_value=True)
    @patch("src.ai_whisperer.orchestrator.calculate_sha256", return_value="test_hash")
    @patch("src.ai_whisperer.orchestrator.json.loads")
    @patch("os.replace")
    @patch("os.makedirs")
    @patch(
        "os.path.exists", return_value=True
    )  # Assume directory exists for simplicity in this test
    @patch(
        "builtins.open", new_callable=mock_open
    )  # Keep open for reading requirements.md
    def test_generate_full_project_plan_no_steps(
        self,
        mock_open_file,
        mock_path_exists,
        mock_makedirs,
        mock_replace,
        mock_json_loads,
        mock_hash,
        mock_is_file,
        mock_api_call,
        orchestrator,
        mock_prompt_content,
        mock_requirements_content,
    ):
        # Configure the mock_open_file to return mock requirements content when requirements.md is opened
        mock_open_file.return_value.__enter__.return_value.read.return_value = (
            mock_requirements_content
        )

        initial_result = {}
        mock_api_call.return_value = '```json\n{\n  "plan": []\n}\n```'

        # Mock json loads for empty task plan
        raw_empty_plan_data = {"plan": []}
        expected_empty_plan_data = {
            "natural_language_goal": "Mock natural language goal",  # Added missing field
            "plan": [],  # Empty plan is correct here
            "input_hashes": {
                "requirements_md": "test_hash",
                "config_yaml": "test_hash",
                "prompt_file": "test_hash",
            },
            "task_id": "mock_task_id_2",
        }
        # Define the data expected AFTER postprocessing and for the file read-back for the no_steps case
        expected_empty_plan_data_read = {
            "task_id": "mock_task_id_2",
            "natural_language_goal": "Mock natural language goal",  # Added missing field
            "input_hashes": {
                "requirements_md": "test_hash",
                "config_yaml": "test_hash",
                "prompt_file": "test_hash",
            },
            "plan": [],  # Empty plan is correct here
        }

        # Add extra mock returns to prevent StopIteration

        mock_json_loads.side_effect = [
            # Call 1: Inside add_items_postprocessor
            raw_empty_plan_data,
            # Call 2: After postprocessing in generate_initial_json
            expected_empty_plan_data,
            # Call 3: Reading file back in generate_full_project_plan
            expected_empty_plan_data_read,
            # Call 4: Add extra return value for any additional calls
            expected_empty_plan_data_read,
            # Call 5: Add another value just to be safe
            expected_empty_plan_data_read,
        ]
        # Mock jsonschema validation and subtask generator
        # Also mock json.load specifically for reading the saved task plan file
        with patch("src.ai_whisperer.orchestrator.jsonschema.validate"):
            with patch(
                "src.ai_whisperer.subtask_generator.SubtaskGenerator"
            ) as mock_subtask_gen:

                with patch(
                    "src.ai_whisperer.orchestrator.json.load"
                ) as mock_json_load_file:
                    # Configure mock_json_load_file to return the expected data for the no_steps case
                    # This mock is needed because StateManager.load_state uses json.load
                    mock_json_load_file.return_value = expected_empty_plan_data_read

                    mock_generator = MagicMock()
                    mock_subtask_gen.return_value = mock_generator

                    # Call the method under test
                    # Add schema to result_data before calling pipeline.process
                    result_data_with_schema = {
                        **initial_result,
                        "schema": orchestrator.task_schema,
                    }
                    result = orchestrator.generate_full_project_plan(
                        "requirements.md", "config.json"
                    )

        # Check that the openrouter call had the correct arguments
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args
        assert "prompt_text" in call_args[1]
        assert "model" in call_args[1]
        assert "params" in call_args[1]
        assert call_args[1]["model"] == orchestrator.openrouter_client.model
        assert call_args[1]["params"] == orchestrator.openrouter_client.params
        # Assertions
        assert result is not None
        assert "task_plan" in result
        assert "subtasks" in result
        assert len(result["subtasks"]) == 0  # Expect 0 subtasks for empty plan
        assert (
            mock_generator.generate_subtask.call_count == 0
        )  # Ensure generate_subtask was not called
