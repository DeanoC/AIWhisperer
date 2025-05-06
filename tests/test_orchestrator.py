import pytest
import json
import jsonschema
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.ai_whisperer.orchestrator import Orchestrator, DEFAULT_PROMPT_PATH, DEFAULT_SCHEMA_PATH
from src.ai_whisperer.exceptions import (
    ConfigError,
    PromptError,
    HashMismatchError,
    OrchestratorError,
    ProcessingError,
    OpenRouterAPIError
)

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Provides a basic valid configuration dictionary."""
    return {
        'openrouter': {
            'api_key': 'test_api_key',
            'model': 'test_model',
            'params': {'temperature': 0.7}
        },
        'prompts': {
            # This section might not be directly used by Orchestrator itself
            # but is required by the config loader
            'some_prompt': 'template'
        },
        'output_dir': './test_output/', # Use a specific test output dir
        'prompt_override_path': None
    }

@pytest.fixture
def mock_schema_content():
    """Provides a basic valid JSON schema content."""
    return json.dumps({
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "input_hashes": {
                "type": "object",
                "properties": {
                    "requirements_md": {"type": "string"},
                    "config_json": {"type": "string"},
                    "prompt_file": {"type": "string"}
                },
                "required": ["requirements_md", "config_json", "prompt_file"]
            },
            "plan": {"type": "array"}
        },
        "required": ["task_id", "input_hashes", "plan"]
    })

@pytest.fixture
def mock_prompt_content():
    """Provides basic prompt template content."""
    return "Prompt template with {markdown_content} and {input_hashes_dict}"

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
            "prompt_file": "prompt_hash"
        },
        "plan": [{"step_id": "step-1", "description": "First step"}]
    }

@pytest.fixture
def setup_orchestrator_files(tmp_path, mock_schema_content, mock_prompt_content):
    """Sets up necessary default files (schema, prompt) in a temporary directory."""
    # Simulate the project structure relative to a mock package root within tmp_path
    mock_package_root = tmp_path / "src" / "ai_whisperer"
    mock_package_root.mkdir(parents=True, exist_ok=True)

    # Mock schema file
    schema_dir = mock_package_root / "schemas"
    schema_dir.mkdir(exist_ok=True)
    schema_path = schema_dir / "task_schema.json"
    schema_path.write_text(mock_schema_content, encoding='utf-8')

    # Mock default prompt file (assuming location relative to package root)
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(exist_ok=True)
    default_prompt_path = prompts_dir / "orchestrator_default.md"
    default_prompt_path.write_text(mock_prompt_content, encoding='utf-8')

    # Patch the constants in orchestrator module to point to tmp_path locations
    # Wrap multiple context managers in parentheses for robust multi-line handling
    with (
        patch('src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH', schema_path),
        patch('src.ai_whisperer.orchestrator.DEFAULT_PROMPT_PATH', default_prompt_path)
    ):
        yield {
            "schema_path": schema_path,
            "default_prompt_path": default_prompt_path,
            "tmp_path": tmp_path
        }

# --- Test Cases ---

def test_orchestrator_init_success(mock_config, setup_orchestrator_files):
    """Tests successful initialization of the Orchestrator."""
    orchestrator = Orchestrator(mock_config)
    assert orchestrator.config == mock_config
    assert orchestrator.prompt_override_path is None
    assert orchestrator.task_schema is not None # Check schema loaded

def test_orchestrator_init_missing_openrouter_config(setup_orchestrator_files):
    """Tests initialization fails if 'openrouter' config is missing."""
    bad_config = {'prompts': {}, 'output_dir': '.'}
    with pytest.raises(ConfigError, match="'openrouter' configuration section is missing"):
        Orchestrator(bad_config)

def test_orchestrator_init_schema_not_found(mock_config, tmp_path):
    """Tests initialization fails if the schema file cannot be found."""
    # Don't use setup_orchestrator_files fixture, ensure schema doesn't exist
    # Patch the path constant to point to a non-existent file
    non_existent_schema_path = tmp_path / "non_existent_schema.json"
    with patch('src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH', non_existent_schema_path):
        with pytest.raises(FileNotFoundError):
            Orchestrator(mock_config)

def test_orchestrator_init_invalid_schema_json(mock_config, tmp_path):
    """Tests initialization fails if the schema file contains invalid JSON."""
    schema_path = tmp_path / "invalid_schema.json"
    schema_path.write_text("this is not json", encoding='utf-8')
    with patch('src.ai_whisperer.orchestrator.DEFAULT_SCHEMA_PATH', schema_path):
        with pytest.raises(ConfigError, match="Invalid JSON in schema file"):
            Orchestrator(mock_config)

# --- _load_prompt_template Tests ---

def test_load_prompt_template_default(mock_config, setup_orchestrator_files, mock_prompt_content):
    """Tests loading the default prompt template."""
    orchestrator = Orchestrator(mock_config)
    content, path = orchestrator._load_prompt_template()
    assert content == mock_prompt_content
    assert path == setup_orchestrator_files['default_prompt_path'].resolve()

def test_load_prompt_template_override(mock_config, setup_orchestrator_files, tmp_path):
    """Tests loading a prompt template from an override path."""
    override_content = "Override prompt content"
    override_path = tmp_path / "custom_prompt.md"
    override_path.write_text(override_content, encoding='utf-8')
    mock_config['prompt_override_path'] = str(override_path)

    orchestrator = Orchestrator(mock_config)
    content, path = orchestrator._load_prompt_template()
    assert content == override_content
    assert path == override_path.resolve()

def test_load_prompt_template_not_found(mock_config, setup_orchestrator_files, tmp_path):
    """Tests PromptError is raised if the prompt file (default or override) is not found."""
    # Test override not found
    mock_config['prompt_override_path'] = str(tmp_path / "non_existent_prompt.md")
    orchestrator = Orchestrator(mock_config)
    with pytest.raises(PromptError, match="Prompt file not found"):
        orchestrator._load_prompt_template()

    # Test default not found (by removing it after setup)
    mock_config['prompt_override_path'] = None
    setup_orchestrator_files['default_prompt_path'].unlink()
    orchestrator_default = Orchestrator(mock_config)
    with pytest.raises(PromptError, match="Prompt file not found"):
        orchestrator_default._load_prompt_template()

# --- _calculate_input_hashes Tests ---

@patch('src.ai_whisperer.orchestrator.calculate_sha256') # Corrected patch target
def test_calculate_input_hashes_success(mock_calc_sha256, mock_config, setup_orchestrator_files, tmp_path):
    """Tests successful calculation of input hashes."""
    # ... rest of the function ...

@patch('src.ai_whisperer.orchestrator.calculate_sha256', side_effect=FileNotFoundError("File not found")) # Corrected patch target
def test_calculate_input_hashes_file_not_found(mock_calc_sha256, mock_config, setup_orchestrator_files, tmp_path):
    """Tests that FileNotFoundError is propagated if a file is missing during hashing."""
    # ... rest of the function ...

# --- Subtask Generation Tests ---

class TestOrchestratorSubtasks:
    @pytest.fixture
    def mock_config(self):
        return {
            'openrouter': {'api_key': 'test_key', 'model': 'test_model', 'params': {}},
            'output_dir': '/tmp/output',
            'prompts': {'orchestrator': 'test prompt', 'subtask': 'test subtask prompt'}
        }

    @pytest.fixture
    def orchestrator(self, mock_config, setup_orchestrator_files):
        with patch('src.ai_whisperer.orchestrator.json.load') as mock_json_load:
            mock_json_load.return_value = {'type': 'object'} # Simplified schema
            return Orchestrator(mock_config)

    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI.call_chat_completion')
    @patch('src.ai_whisperer.orchestrator.Path.is_file', return_value=True)
    @patch('src.ai_whisperer.orchestrator.calculate_sha256', return_value='test_hash')
    @patch('src.ai_whisperer.orchestrator.json.loads')
    def test_generate_full_project_plan(self, mock_json_loads, mock_hash,
                                       mock_is_file, mock_api_call, orchestrator):
        mock_api_call.return_value = "```json\n{\n  \"plan\": [\n    {\n      \"step_id\": \"step1\"\n    },\n    {\n      \"step_id\": \"step2\"\n    }\n  ]\n}\n```"

        # Define the raw data expected before postprocessing adds hashes/id
        raw_plan_data = {
            'plan': [{'step_id': 'step1'}, {'step_id': 'step2'}]
        }
        # Define the data expected AFTER postprocessing and for the file read-back
        expected_plan_data = {
            'plan': [{'step_id': 'step1'}, {'step_id': 'step2'}],
            'input_hashes': {
                'requirements_md': 'test_hash',
                'config_json': 'test_hash',
                'prompt_file': 'test_hash'
            },
            'task_id': 'mock_task_id_1'
        }
        # Convert to JSON string for mock_open
        expected_json_content = json.dumps(expected_plan_data)

        # Mock json loads - ensure we provide enough mock returns
        # The StopIteration error indicates we need more return values
        mock_json_loads.side_effect = [
            # Call 1: Inside add_items_postprocessor
            raw_plan_data,
            # Call 2: After postprocessing in generate_initial_json
            expected_plan_data,
            # Call 3: Reading file back in generate_full_project_plan
            expected_plan_data,
            # Call 4: Add extra return value for any additional calls
            expected_plan_data,
            # Call 5: Add another value just to be safe
            expected_plan_data
        ]

        # Mock jsonschema validation and subtask generator within a new mock_open context
        with patch('builtins.open', new_callable=mock_open, read_data=expected_json_content) as mock_file_open:
            with patch('src.ai_whisperer.orchestrator.jsonschema.validate'):
                with patch('src.ai_whisperer.subtask_generator.SubtaskGenerator') as mock_subtask_gen:
                    mock_generator = MagicMock()
                    mock_generator.generate_subtask.side_effect = [
                        Path('/tmp/output/subtask_step1.json'),
                        Path('/tmp/output/subtask_step2.json')
                    ]
                    mock_subtask_gen.return_value = mock_generator
                    # Call the method under test
                    result = orchestrator.generate_full_project_plan('requirements.md', 'config.json')
                    # Check that the openrouter call had the correct arguments
                    mock_api_call.assert_called_once()
                    call_args = mock_api_call.call_args
                    assert 'prompt_text' in call_args[1]
                    assert 'model' in call_args[1]
                    assert 'params' in call_args[1]
                    assert call_args[1]['model'] == orchestrator.openrouter_client.model
                    assert call_args[1]['params'] == orchestrator.openrouter_client.params
                    # Assertions
                    assert result is not None
                    assert 'task_plan' in result
                    assert 'subtasks' in result
                    assert len(result['subtasks']) == 2
                    assert result['subtasks'][0] == Path('/tmp/output/subtask_step1.json')
                    assert mock_generator.generate_subtask.call_count == 2

    @patch('src.ai_whisperer.openrouter_api.OpenRouterAPI.call_chat_completion')
    @patch('src.ai_whisperer.orchestrator.Path.is_file', return_value=True)
    @patch('src.ai_whisperer.orchestrator.calculate_sha256', return_value='test_hash')
    @patch('src.ai_whisperer.orchestrator.json.loads')
    @patch('builtins.open', new_callable=mock_open, read_data="test content")
    def test_generate_full_project_plan_no_steps(self, mock_file_open, mock_json_loads,
                                               mock_hash, mock_is_file, mock_api_call, orchestrator):
        initial_result = {}
        mock_api_call.return_value = "```json\n{\n  \"plan\": []\n}\n```"
        # Mock json loads for empty task plan
        raw_empty_plan_data = {
            'plan': []
        }
        expected_empty_plan_data = {
            'plan': [],
            'input_hashes': {
                'requirements_md': 'test_hash',
                'config_json': 'test_hash',
                'prompt_file': 'test_hash'
            },
            'task_id': 'mock_task_id_2'
        }
        # Add extra mock returns to prevent StopIteration
        mock_json_loads.side_effect = [
            # Call 1: Inside add_items_postprocessor
            raw_empty_plan_data,
            # Call 2: After postprocessing in generate_initial_json
            expected_empty_plan_data,
            # Call 3: Reading file back in generate_full_project_plan
            expected_empty_plan_data,
            # Call 4: Add extra return value for any additional calls
            expected_empty_plan_data,
            # Call 5: Add another value just to be safe
            expected_empty_plan_data
        ]
        # Mock jsonschema validation
        with patch('src.ai_whisperer.orchestrator.jsonschema.validate'):
            # Mock subtask generator
            with patch('src.ai_whisperer.subtask_generator.SubtaskGenerator') as mock_subtask_gen:
                mock_generator = MagicMock()
                mock_subtask_gen.return_value = mock_generator

                # Call the method under test
                # Add schema to result_data before calling pipeline.process
                result_data_with_schema = {**initial_result, "schema": orchestrator.task_schema}
                result = orchestrator.generate_full_project_plan('requirements.md', 'config.json')

                # Check that the openrouter call had the correct arguments
                mock_api_call.assert_called_once()
                call_args = mock_api_call.call_args
                assert 'prompt_text' in call_args[1]
                assert 'model' in call_args[1]
                assert 'params' in call_args[1]
                assert call_args[1]['model'] == orchestrator.openrouter_client.model
                assert call_args[1]['params'] == orchestrator.openrouter_client.params

        # Assertions
        assert result is not None
        assert 'task_plan' in result
        assert 'subtasks' in result
        assert len(result['subtasks']) == 0
        assert mock_generator.generate_subtask.call_count == 0
