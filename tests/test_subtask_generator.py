# -*- coding: utf-8 -*-
"""Tests for the Subtask Generator functionality."""

import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call

# Assuming the core logic will be in src.ai_whisperer.subtask_generator
# Import necessary exceptions and potentially the class/functions once they exist
from src.ai_whisperer.exceptions import ConfigError, SubtaskGenerationError, SchemaValidationError
from src.ai_whisperer.openrouter_api import OpenRouterAPIError

# --- Test Data ---
MOCK_CONFIG = {
    'openrouter': {
        'api_key': 'mock_api_key',
        'model': 'mock_model',
        'params': {'temperature': 0.5},
        'site_url': 'mock_url',
        'app_name': 'mock_app'
    },
    'prompts': {
        'subtask_generator_prompt_content': "Refine this step: {subtask_yaml}",
        # Add other prompt contents if needed by the generator
    },
    'output_dir': './test_output/'
}

VALID_INPUT_STEP = {
    'step_id': 'test_step_1',
    'description': 'Implement the core logic for feature X.',
    'depends_on': [],
    'context': { # Example context, might need mocking
        'relevant_files': ['src/feature_x.py', 'tests/test_feature_x.py']
    }
}

MOCK_AI_RESPONSE_YAML_VALID = """
step_id: test_step_1_refined
description: Implement the core logic for feature X in src/feature_x.py.
agent_spec:
  type: code_generation
  input_artifacts:
    - src/feature_x.py
  output_artifacts:
    - src/feature_x.py
  instructions: >
    Implement the main function according to the requirements.
constraints:
  - Must handle edge cases A and B.
validation_criteria:
  - Unit tests in tests/test_feature_x.py pass.
"""

MOCK_AI_RESPONSE_YAML_INVALID_SCHEMA = """
step_id: test_step_1_invalid
description: Missing required fields.
# agent_spec is missing
"""

# --- Fixtures ---

@pytest.fixture
def mock_load_config():
    """Fixture to mock load_config."""
    # Adjust the patch target based on where load_config will be called from
    with patch('src.ai_whisperer.subtask_generator.load_config') as mock:
        mock.return_value = MOCK_CONFIG
        yield mock

@pytest.fixture
def mock_openrouter_client():
    """Fixture to mock the OpenRouterAPI client."""
    # Adjust the patch target based on where OpenRouterAPI will be instantiated
    with patch('src.ai_whisperer.subtask_generator.OpenRouterAPI') as mock_cls:
        mock_instance = MagicMock()
        # Set attributes on the mock instance if they are accessed directly
        mock_instance.model = MOCK_CONFIG['openrouter']['model']
        mock_instance.params = MOCK_CONFIG['openrouter']['params']
        mock_cls.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_filesystem():
    """Fixture to mock file system operations (open, write, exists, etc.)."""
    # Using mock_open for basic file writing simulation
    m_open = mock_open()
    # Patch pathlib.Path.mkdir as the code now uses it
    with patch('builtins.open', m_open), \
         patch('pathlib.Path.mkdir') as mock_path_mkdir, \
         patch('pathlib.Path.exists') as mock_exists:
        # Default behavior: pretend files don't exist unless specifically handled
        mock_exists.return_value = False
        # Ensure Path.mkdir is also mocked for consistency
        mock_path_mkdir.return_value = None
        yield {
            'open': m_open,
            'path_mkdir': mock_path_mkdir, # Use this key now
            'exists': mock_exists
        }

@pytest.fixture
def mock_schema_validation():
    """Fixture to mock schema validation."""
    # Patch where the function is imported/used by the class under test
    with patch('src.ai_whisperer.subtask_generator.validate_against_schema') as mock_validate:
        # Default: Assume valid unless side_effect is set in test
        mock_validate.return_value = None
        yield mock_validate


# --- Test Cases ---

def test_subtask_generator_initialization(mock_load_config):
    """Tests if the SubtaskGenerator initializes correctly."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    generator = SubtaskGenerator('dummy_config_path.yaml')
    assert generator.config == MOCK_CONFIG
    mock_load_config.assert_called_once_with('dummy_config_path.yaml')

def test_generate_subtask_success(mock_load_config, mock_openrouter_client, mock_filesystem, mock_schema_validation):
    """Tests successful generation and saving of a subtask YAML."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    from unittest.mock import ANY
    from pathlib import Path

    # Pass the output_dir from MOCK_CONFIG during instantiation
    generator = SubtaskGenerator('dummy_config.yaml', output_dir=MOCK_CONFIG['output_dir'])

    # Mock AI response using the correct method name
    mock_openrouter_client.call_chat_completion.return_value = MOCK_AI_RESPONSE_YAML_VALID

    # Mock os.path.exists to simulate output file not existing initially
    mock_filesystem['exists'].return_value = False

    output_path = generator.generate_subtask(VALID_INPUT_STEP)

    # 1. Verify prompt preparation (check call to call_chat_completion)
    mock_openrouter_client.call_chat_completion.assert_called_once()
    call_args, call_kwargs = mock_openrouter_client.call_chat_completion.call_args
    # Check keyword arguments used in the call
    assert 'prompt_text' in call_kwargs
    assert VALID_INPUT_STEP['description'] in call_kwargs['prompt_text']
    assert 'model' in call_kwargs
    assert call_kwargs['model'] == mock_openrouter_client.model # Check if model from client is passed
    assert 'params' in call_kwargs
    assert call_kwargs['params'] == mock_openrouter_client.params # Check if params from client are passed
    # 2. Verify schema validation call
    parsed_yaml = yaml.safe_load(MOCK_AI_RESPONSE_YAML_VALID)

    # Define the expected schema path relative to the project root
    expected_schema_path = Path("src/ai_whisperer/schemas/subtask_schema.json")

    # Update the assertion to include subtask_id and the correct schema path
    mock_schema_validation.assert_called_with(
        {
            **parsed_yaml, # Use dictionary unpacking
            'subtask_id': ANY # Expect the subtask_id key
        },
        expected_schema_path # Expect the actual schema path
    )

    # 3. Verify output file path generation
    # Match the generator's filename format
    expected_output_filename = f"subtask_{VALID_INPUT_STEP['step_id']}.yaml"
    expected_output_dir = Path(MOCK_CONFIG['output_dir'])
    expected_path = expected_output_dir / expected_output_filename
    # Compare Path objects directly
    assert output_path == expected_path.resolve()

    # 4. Verify directory creation and file writing
    # Check Path.mkdir call
    mock_filesystem['path_mkdir'].assert_called_once_with(parents=True, exist_ok=True)
    # Check open call (expects Path object, which is correct now)
    mock_filesystem['open'].assert_called_once_with(expected_path, 'w', encoding='utf-8')
    handle = mock_filesystem['open']()
    written_content = "".join(call.args[0] for call in handle.write.call_args_list)
    assert 'step_id: test_step_1_refined' in written_content

def test_generate_subtask_ai_error(mock_load_config, mock_openrouter_client):
    """Tests handling of API errors from OpenRouter."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    generator = SubtaskGenerator('dummy_config.yaml')
    mock_openrouter_client.call_chat_completion.side_effect = OpenRouterAPIError("AI failed")

    with pytest.raises(SubtaskGenerationError, match="AI interaction failed"):
        generator.generate_subtask(VALID_INPUT_STEP)

def test_generate_subtask_schema_validation_error(mock_load_config, mock_openrouter_client, mock_schema_validation):
    """Tests handling of schema validation errors."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    generator = SubtaskGenerator('dummy_config.yaml')
    mock_openrouter_client.call_chat_completion.return_value = MOCK_AI_RESPONSE_YAML_INVALID_SCHEMA
    mock_schema_validation.side_effect = SchemaValidationError("Invalid schema: Missing agent_spec")

    # Expect the error message defined in the mock's side_effect
    with pytest.raises(SchemaValidationError, match="Invalid schema: Missing agent_spec"):
        generator.generate_subtask(VALID_INPUT_STEP)

def test_generate_subtask_file_write_error(mock_load_config, mock_openrouter_client, mock_filesystem, mock_schema_validation):
    """Tests handling of errors during file writing."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    generator = SubtaskGenerator('dummy_config.yaml', output_dir=MOCK_CONFIG['output_dir'])
    mock_openrouter_client.call_chat_completion.return_value = MOCK_AI_RESPONSE_YAML_VALID
    mock_filesystem['open'].side_effect = IOError("Disk full")

    with pytest.raises(SubtaskGenerationError, match="Failed to write output file"):
        generator.generate_subtask(VALID_INPUT_STEP)

def test_generate_subtask_yaml_parsing_error(mock_load_config, mock_openrouter_client):
    """Tests handling of invalid YAML responses from the AI."""
    from src.ai_whisperer.subtask_generator import SubtaskGenerator
    generator = SubtaskGenerator('dummy_config.yaml')
    mock_openrouter_client.call_chat_completion.return_value = "invalid: yaml: content"

    with pytest.raises(SubtaskGenerationError, match="Failed to parse AI response as YAML"):
        generator.generate_subtask(VALID_INPUT_STEP)