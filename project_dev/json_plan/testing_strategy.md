# Testing Strategy for YAML to JSON Migration

## Introduction

This document outlines the testing strategy for migrating the AI Whisperer project from YAML to JSON using a direct approach without backward compatibility. Comprehensive testing is crucial to ensure that the migration doesn't introduce regressions or new bugs. The testing strategy covers unit tests, integration tests, and end-to-end tests with a focus on JSON-only functionality.

## Current Test Coverage

The project currently has several test files that test YAML-related functionality:

1. `tests/test_problematic_yaml.py`: Tests the postprocessing pipeline with problematic YAML content
2. `tests/unit/test_postprocessing_*.py`: Unit tests for various postprocessing steps
3. `tests/integration/test_postprocessing_integration.py`: Integration tests for the postprocessing pipeline
4. `tests/test_orchestrator.py`: Tests for the Orchestrator class
5. `tests/test_subtask_generator.py`: Tests for the SubtaskGenerator class

## Required Changes

### 1. Update Test Files

#### Rename Test Files

Some test files should be renamed to reflect the switch from YAML to JSON:

- `tests/test_problematic_yaml.py` → `tests/test_problematic_json.py`
- `tests/unit/test_postprocessing_yaml_*.py` → `tests/unit/test_postprocessing_json_*.py` (if any)

#### Update Test Content

Update the content of test files to use JSON instead of YAML:

1. Replace YAML test data with equivalent JSON test data
2. Update assertions to check for JSON-specific behavior
3. Update test method names to reflect JSON testing

### 2. Create New Test Files

Create new test files for JSON-specific functionality:

1. `tests/unit/test_format_json.py`: Tests for the new format_json step
2. `tests/unit/test_json_validation.py`: Tests for JSON schema validation

### 3. Update Existing Tests

#### `tests/test_problematic_json.py` (formerly `tests/test_problematic_yaml.py`)

```python
import os
import sys
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.scripted_steps.format_json import format_json
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

# The problematic JSON content
# This ensures the test always uses the same content
PROBLEMATIC_JSON = """```json
{
  "natural_language_goal": "Enhance the `--list-models` command to provide detailed model information and optionally export it to a CSV file.",
  "overall_context": "The goal is to improve the user experience when listing available models using the `ai-whisperer` CLI by providing richer information and an export option.",
  "plan": [
    {
      "step_id": "plan_implementation",
      "description": "Analyze the requirements and plan the necessary code modifications in main.py and the OpenRouter API module.",
      "depends_on": [],
      "agent_spec": {
        "type": "planning",
        "input_artifacts": [
          "main.py",
          "ai_whisperer/openrouter_api.py"
        ],
        "output_artifacts": [
          "docs/list_models_enhancement_plan.md"
        ],
        "instructions": "Analyze the feature request for enhancing the `--list-models` command.\nIdentify the specific changes needed in `main.py` to handle the new `--output-csv` argument and integrate with the enhanced API call.",
        "validation_criteria": [
          "docs/list_models_enhancement_plan.md exists.",
          "docs/list_models_enhancement_plan.md outlines changes to main.py for argument parsing."
        ]
      }
    }
  ]
}
```
"""

def test_problematic_json():
    """
    Test that mimics orchestrator.py's behavior but uses the problematic JSON content.
    This test should reproduce the errors that orchestrator.py encounters.
    """
    # Use the problematic JSON constant
    json_string = PROBLEMATIC_JSON

    # Create a log file for detailed output
    with open("test_output.txt", "w") as f:
        f.write("=== TEST OUTPUT ===\n\n")
        f.write(f"Original JSON string:\n{json_string}\n\n")

    # Print the original JSON string for debugging
    print(f"Original JSON string starts with: {json_string[:50]}")
    print(f"Original JSON string ends with: {json_string[-50:] if len(json_string) > 50 else json_string}")

    # Create result_data with items to add (similar to orchestrator.py)
    result_data = {
        "items_to_add": {
            "top_level": {
                "task_id": "test-task-id",
                "input_hashes": {"test": "hash"},
            }
        },
        "success": True,
        "steps": {},
        "logs": [],
    }

    # Create the postprocessing pipeline with the JSON-specific steps
    pipeline = PostprocessingPipeline(
        scripted_steps=[
            clean_backtick_wrapper,
            escape_text_fields,
            format_json,
            validate_syntax,
            handle_required_fields,
            add_items_postprocessor
        ]
    )

    try:
        # Process each step individually to identify which one is failing
        current_json = json_string
        current_data = result_data.copy()

        print("Starting pipeline processing step by step:")

        # Step 1: clean_backtick_wrapper
        print("\nStep 1: clean_backtick_wrapper")
        current_json, current_data = clean_backtick_wrapper(current_json, current_data)
        print(f"After clean_backtick_wrapper, JSON content:\n{current_json}")
        with open("test_output.txt", "a") as f:
            f.write("\n=== Step 1: clean_backtick_wrapper ===\n")
            f.write(f"JSON content:\n{current_json}\n")

        # Step 2: escape_text_fields
        print("\nStep 2: escape_text_fields")
        current_json, current_data = escape_text_fields(current_json, current_data)
        print(f"After escape_text_fields, JSON content:\n{current_json}")
        with open("test_output.txt", "a") as f:
            f.write("\n=== Step 2: escape_text_fields ===\n")
            f.write(f"JSON content:\n{current_json}\n")

        # Step 3: format_json
        print("\nStep 3: format_json")
        current_json, current_data = format_json(current_json, current_data)
        print(f"After format_json, JSON content:\n{current_json}")
        with open("test_output.txt", "a") as f:
            f.write("\n=== Step 3: format_json ===\n")
            f.write(f"JSON content:\n{current_json}\n")

        # Try to parse after format_json to check if it's valid
        try:
            test_json = json.loads(current_json)
            print("JSON is valid after format_json")
        except Exception as e:
            print(f"JSON is invalid after format_json: {e}")

        # Step 4: validate_syntax
        print("\nStep 4: validate_syntax")
        current_json, current_data = validate_syntax(current_json, current_data)
        print(f"After validate_syntax, JSON starts with: {current_json[:100]}")

        # Step 5: handle_required_fields
        print("\nStep 5: handle_required_fields")
        current_json, current_data = handle_required_fields(current_json, current_data)
        print(f"After handle_required_fields, JSON starts with: {current_json[:100]}")

        # Step 6: add_items_postprocessor
        print("\nStep 6: add_items_postprocessor")
        current_json, current_data = add_items_postprocessor(current_json, current_data)
        print(f"After add_items_postprocessor, JSON starts with: {current_json[:100]}")

        # Now run the full pipeline for comparison
        print("\nRunning full pipeline:")
        processed_json, postprocessing_result = pipeline.process(json_string, result_data.copy())
        print(f"JSON string after full pipeline processing:\n{processed_json[:100]}")

        # Try to parse the processed JSON
        json_data = json.loads(processed_json)
        print(f"JSON data after parsing:\n{json_data}")
        # Test passes only if no exception is raised
    except Exception as e:
        print(f"Pipeline raised an exception: {e}")
        assert False, f"Pipeline failed with exception: {e}"

if __name__ == "__main__":
    test_problematic_json()
```

#### `tests/unit/test_format_json.py` (new file)

```python
import pytest
import json
from src.postprocessing.scripted_steps.format_json import format_json

def test_format_json_with_valid_json_string():
    """Test format_json with a valid JSON string."""
    # Arrange
    json_string = '{"key1":"value1","key2":"value2"}'
    expected_json = json.dumps(json.loads(json_string), indent=2)

    # Act
    result, data = format_json(json_string)

    # Assert
    assert result == expected_json
    assert data["success"] is True
    assert "Successfully formatted JSON." in data["logs"]

def test_format_json_with_valid_json_dict():
    """Test format_json with a valid JSON dictionary."""
    # Arrange
    json_dict = {"key1": "value1", "key2": "value2"}

    # Act
    result, data = format_json(json_dict)

    # Assert
    assert result == json_dict
    assert data["success"] is True
    assert "Formatted JSON dictionary." in data["logs"]

def test_format_json_with_invalid_json():
    """Test format_json with an invalid JSON string."""
    # Arrange
    invalid_json = '{"key1":"value1","key2":}'

    # Act
    result, data = format_json(invalid_json)

    # Assert
    assert result == invalid_json  # Should return the original content
    assert data["success"] is True
    assert any("JSON parsing error" in log for log in data["logs"])

def test_format_json_with_empty_string():
    """Test format_json with an empty string."""
    # Arrange
    empty_string = ""

    # Act
    result, data = format_json(empty_string)

    # Assert
    assert result == empty_string
    assert data["success"] is True
    assert "No content to format." in data["logs"]
```

#### `tests/unit/test_validate_syntax.py` (update)

```python
import pytest
import json
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax

def test_validate_syntax_with_valid_json_string():
    """Test validate_syntax with a valid JSON string."""
    # Arrange
    json_string = '{"key1":"value1","key2":"value2"}'
    expected_json = json.dumps(json.loads(json_string), indent=2)

    # Act
    result, data = validate_syntax(json_string)

    # Assert
    assert result == expected_json
    assert data["success"] is True
    assert "JSON syntax is valid." in data["logs"]

def test_validate_syntax_with_valid_json_dict():
    """Test validate_syntax with a valid JSON dictionary."""
    # Arrange
    json_dict = {"key1": "value1", "key2": "value2"}

    # Act
    result, data = validate_syntax(json_dict)

    # Assert
    assert result == json_dict
    assert data["success"] is True
    assert "Input is a dictionary, no syntax validation needed." in data["logs"]

def test_validate_syntax_with_invalid_json():
    """Test validate_syntax with an invalid JSON string."""
    # Arrange
    invalid_json = '{"key1":"value1","key2":}'

    # Act
    result, data = validate_syntax(invalid_json)

    # Assert
    assert result == invalid_json  # Should return the original content
    assert data["success"] is True
    assert any("JSON syntax error" in log for log in data["logs"])

def test_validate_syntax_with_empty_string():
    """Test validate_syntax with an empty string."""
    # Arrange
    empty_string = ""

    # Act
    result, data = validate_syntax(empty_string)

    # Assert
    assert result == empty_string
    assert data["success"] is True
    assert "No content to validate syntax for." in data["logs"]
```

### 4. Update Integration Tests

Update the integration tests to use JSON instead of YAML:

```python
import pytest
import json
from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.scripted_steps.format_json import format_json
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

def test_postprocessing_pipeline_integration():
    """Test the entire postprocessing pipeline with a JSON string."""
    # Arrange
    json_string = """```json
    {
      "natural_language_goal": "Test goal",
      "plan": [
        {
          "step_id": "test_step",
          "description": "Test description",
          "agent_spec": {
            "type": "test",
            "input_artifacts": ["test_input"],
            "output_artifacts": ["test_output"],
            "instructions": "Test instructions"
          }
        }
      ]
    }
    ```"""

    result_data = {
        "items_to_add": {
            "top_level": {
                "task_id": "test-task-id",
                "input_hashes": {"test": "hash"},
            }
        },
        "success": True,
        "steps": {},
        "logs": [],
    }

    pipeline = PostprocessingPipeline(
        scripted_steps=[
            clean_backtick_wrapper,
            escape_text_fields,
            format_json,
            validate_syntax,
            handle_required_fields,
            add_items_postprocessor
        ]
    )

    # Act
    processed_json, postprocessing_result = pipeline.process(json_string, result_data)

    # Assert
    assert postprocessing_result["success"] is True

    # Parse the processed JSON
    json_data = json.loads(processed_json)

    # Check that the items were added
    assert json_data["task_id"] == "test-task-id"
    assert json_data["input_hashes"] == {"test": "hash"}

    # Check that the original content is preserved
    assert json_data["natural_language_goal"] == "Test goal"
    assert len(json_data["plan"]) == 1
    assert json_data["plan"][0]["step_id"] == "test_step"
```

### 5. Update Orchestrator and SubtaskGenerator Tests

Update the tests for the Orchestrator and SubtaskGenerator classes to use JSON instead of YAML:

```python
import pytest
import json
from pathlib import Path
from src.ai_whisperer.orchestrator import Orchestrator

def test_orchestrator_generate_initial_json(mocker):
    """Test the generate_initial_json method of the Orchestrator class."""
    # Arrange
    config = {
        "openrouter": {
            "api_key": "test_key",
            "model": "test_model",
            "params": {}
        }
    }
    orchestrator = Orchestrator(config)

    # Mock the necessary methods and functions
    mocker.patch.object(orchestrator, "_load_prompt_template", return_value=("test_prompt", Path("test_prompt_path")))
    mocker.patch.object(orchestrator, "_calculate_input_hashes", return_value={"test": "hash"})
    mocker.patch("builtins.open", mocker.mock_open(read_data="test_requirements"))
    mocker.patch.object(orchestrator.openrouter_client, "call_chat_completion", return_value='{"test": "response"}')
    mocker.patch.object(orchestrator, "save_json", return_value=Path("test_output_path"))

    # Act
    result = orchestrator.generate_initial_json("test_requirements_path", "test_config_path")

    # Assert
    assert result == Path("test_output_path")
    orchestrator._load_prompt_template.assert_called_once()
    orchestrator._calculate_input_hashes.assert_called_once()
    orchestrator.openrouter_client.call_chat_completion.assert_called_once()
    orchestrator.save_json.assert_called_once()
```

## Test Data Migration

Create a utility script to convert existing YAML test data to JSON:

```python
import yaml
import json
import os
import glob

def convert_yaml_to_json(yaml_file_path, json_file_path):
    """Convert a YAML file to JSON."""
    with open(yaml_file_path, 'r') as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    with open(json_file_path, 'w') as json_file:
        json.dump(yaml_data, json_file, indent=2)

def convert_all_yaml_test_data():
    """Convert all YAML test data files to JSON."""
    # Find all YAML test data files
    yaml_files = glob.glob('tests/**/*.yaml', recursive=True)

    for yaml_file in yaml_files:
        # Create the corresponding JSON file path
        json_file = yaml_file.replace('.yaml', '.json')

        # Convert the file
        convert_yaml_to_json(yaml_file, json_file)

        print(f"Converted {yaml_file} to {json_file}")

if __name__ == "__main__":
    convert_all_yaml_test_data()
```

## Test Execution Strategy

1. Create a snapshot of the existing YAML tests for reference
2. Create new JSON-specific tests for all components
3. Replace all existing YAML tests with JSON equivalents
4. Run the complete JSON test suite to ensure everything works as expected

## Continuous Integration

Update the CI/CD pipeline to run the new JSON-only tests. Since we're taking a direct approach without backward compatibility, there's no need to maintain both YAML and JSON tests.

## Conclusion

The testing strategy for migrating from YAML to JSON involves creating new JSON-specific tests and completely replacing existing YAML tests. By taking a direct approach without maintaining backward compatibility, we can focus solely on ensuring the JSON implementation is robust and reliable. This approach simplifies the testing process and allows us to move quickly to a cleaner, more maintainable codebase. The comprehensive test suite will ensure that all components work correctly with JSON and that the migration is successful.
