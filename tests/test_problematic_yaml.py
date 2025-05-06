import os
import sys
import yaml

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.postprocessing.pipeline import PostprocessingPipeline
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation
from src.postprocessing.scripted_steps.validate_syntax import validate_syntax
from src.postprocessing.scripted_steps.handle_required_fields import handle_required_fields
from src.postprocessing.scripted_steps.add_items_postprocessor import add_items_postprocessor

# The problematic YAML content from temp.txt
# This ensures the test always uses the same content, even if temp.txt is overwritten
PROBLEMATIC_YAML = """```yaml
natural_language_goal: Enhance the `--list-models` command to display detailed OpenRouter model information, optionally exporting it to a CSV file.
overall_context: |
  The project requires strict Test-Driven Development (TDD).
  Code modifications and generations must follow the TDD cycle: Test Generation -> Code/Edit -> Validation (Test Execution).
  When modifying or generating code, reuse existing utility functions, constants, and exception handling from modules like `utils.py`, `config.py`, and `exceptions.py` where appropriate.
plan:
  - step_id: planning_list_models_enhancement
    description: Analyze the requirements, identify necessary code modifications in main.py and the OpenRouter API class, and outline the structure for fetching, formatting, and saving model data.
    depends_on: []
    agent_spec:
      type: planning
      input_artifacts:
        - main.py
        - openrouter_api.py
        - README.md
      output_artifacts:
        - docs/list_models_enhancement_plan.md
      instructions: |
        Analyze the user requirements for enhancing the `--list-models` command.
        Identify the specific changes needed in `main.py` to handle the new `--output-csv` argument and call the enhanced API method.
        Analyze the changes needed in `openrouter_api.py` to fetch comprehensive model details instead of just names from the OpenRouter API.
        Determine the structure of the data to be retrieved and how it should be formatted for both console output and CSV export.
        Outline a high-level implementation plan, including the steps for modifying the CLI parser, the API call, data processing, and CSV writing.
        Consider how to handle potential API response variations or errors.
        Create a summary document (`docs/list_models_enhancement_plan.md`) detailing the analysis and plan.
      validation_criteria:
        - "docs/list_models_enhancement_plan.md exists"
        - "docs/list_models_enhancement_plan.md clearly identifies required code changes in main.py and openrouter_api.py"
        - "docs/list_models_enhancement_plan.md outlines the data structure for model details"
        - "docs/list_models_enhancement_plan.md describes the high-level implementation steps"
"""

def test_problematic_yaml():
    """
    Test that mimics orchestrator.py's behavior but uses the problematic YAML content.
    This test should reproduce the errors that orchestrator.py encounters.
    """
    # Use the problematic YAML constant instead of reading from temp.txt
    yaml_string = PROBLEMATIC_YAML

    # Print the original YAML string for debugging
    print(f"Original YAML string starts with: {yaml_string[:50]}")
    print(f"Original YAML string ends with: {yaml_string[-50:] if len(yaml_string) > 50 else yaml_string}")

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

    # Create the postprocessing pipeline with the same steps as orchestrator.py
    pipeline = PostprocessingPipeline(
        scripted_steps=[
            clean_backtick_wrapper,
            escape_text_fields,
            normalize_indentation,
            validate_syntax,
            handle_required_fields,
            add_items_postprocessor
        ]
    )

    processed_yaml, postprocessing_result = pipeline.process(yaml_string, result_data.copy())
    print(f"YAML string after postprocessing:\n{processed_yaml}")

    # Try to parse the processed YAML
    yaml_data = yaml.safe_load(processed_yaml)
    print(f"YAML data after parsing:\n{yaml_data}")

if __name__ == "__main__":
    test_problematic_yaml()
