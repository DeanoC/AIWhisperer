import pytest
import os
from src.postprocessing.scripted_steps.normalize_indentation import normalize_indentation
from src.postprocessing.scripted_steps.clean_backtick_wrapper import clean_backtick_wrapper
from src.postprocessing.scripted_steps.escape_text_fields import escape_text_fields
from src.postprocessing.pipeline import PostprocessingPipeline

@pytest.mark.parametrize("input_yaml, expected_yaml", [
    # Correctly indented YAML
    ("key:\n  subkey: value\n", "key:\n  subkey: value\n"),
    # Inconsistent indentation (mixed spaces and tabs)
    ("key:\n\t  subkey: value\n", "key:\n  subkey: value\n"),
    # Excessive indentation
    ("key:\n        subkey: value\n", "key:\n  subkey: value\n"),
    # Insufficient indentation
    ("key:\n subkey: value\n", "key:\n  subkey: value\n"),
    # Edge case: Empty file
    ("", ""),
    # Edge case: File with only comments
    ("# This is a comment\n", "# This is a comment\n"),
    # Complex nested structure with list items (similar to the problematic case)
    ("""natural_language_goal: "Enhance the command"
plan:
  - step_id: planning_feature
    description: "Analyze the requirements"
    depends_on: []
    agent_spec:
      type: planning
      input_artifacts:
        - file1.py
      output_artifacts: []
      instructions: |
        Analyze the feature request.
        Identify the changes needed.
      validation_criteria:
        - The plan is clear.
""", """natural_language_goal: "Enhance the command"
plan:
  - step_id: planning_feature
    description: "Analyze the requirements"
    depends_on: []
    agent_spec:
      type: planning
      input_artifacts:
        - file1.py
      output_artifacts: []
      instructions: |
        Analyze the feature request.
        Identify the changes needed.
      validation_criteria:
        - The plan is clear.
"""),
    # Note: Backtick code block markers should be handled by clean_backtick_wrapper, not normalize_indentation
])
def test_normalize_indentation(input_yaml, expected_yaml):
    # Call the function with the required signature (yaml_content, result)
    result, updated_result = normalize_indentation(input_yaml, None)
    # Assert that the returned YAML content matches the expected YAML
    assert result == expected_yaml

def test_normalize_indentation_with_real_world_example():
    """
    Test the normalize_indentation function with a real-world example
    from temp.txt that was causing YAML parsing issues.

    This test reproduces the orchestrator's postprocessing pipeline by first
    cleaning the backtick wrapper and then normalizing the indentation.
    """
    # Create a test file with content from temp.txt
    test_file_path = os.path.join(os.path.dirname(__file__), 'test_indentation_example.txt')

    # Write a simplified version of temp.txt
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write("""```yaml
natural_language_goal: Enhance the `--list-models` command to output comprehensive model details to the console and optionally to a CSV file.
overall_context: |
  Implement the feature request to improve the `--list-models` command in the ai-whisperer tool. The implementation should adhere to a strict Test-Driven Development (TDD) approach. Focus on modifying `main.py` and the OpenRouter API interaction to fetch and display/export detailed model information. Ensure code reuse where possible, examining existing utility modules.
plan:
  - step_id: planning_list_models_enhancement
    description: Analyze the requirements and outline the necessary code changes and test cases for enhancing the list-models command.
    depends_on: []
    agent_spec:
      type: planning
      input_artifacts:
        - '# Feature Request: Improve OpenRouter List Models Results'
      output_artifacts:
        - docs/list_models_enhancement_plan.md
      instructions: |
        Analyze the provided feature request markdown file.
        Outline the specific changes needed in `main.py` to handle the new `--output-csv` argument.
        Identify how the OpenRouter API interaction needs to be modified to fetch detailed model information instead of just names.
        Determine the structure of the data to be exported to CSV.
        List the specific unit tests required to verify:
        - Handling of the `--output-csv` argument.
        - Correct fetching of comprehensive model data from the API.
        - Proper formatting and writing of data to the CSV file when the argument is provided.
        - Continued correct console output when the argument is not provided.
        Consider how to represent the comprehensive model metadata (features, costs, context window, provider) in both console output and CSV format.
        Examine existing files like `main.py`, `OpenRouterAPI.py`, and any utility modules to identify potential code reuse opportunities.
        Document the plan in `docs/list_models_enhancement_plan.md`.
      validation_criteria:
        - docs/list_models_enhancement_plan.md exists.
        - docs/list_models_enhancement_plan.md clearly outlines changes needed in `main.py` and `OpenRouterAPI.py`.
        - docs/list_models_enhancement_plan.md identifies key data fields to retrieve and export.
        - docs/list_models_enhancement_plan.md lists specific test cases to be implemented.
        - docs/list_models_enhancement_plan.md identifies potential code reuse areas.
  - step_id: test_generate_list_models_argument_parsing
    description: Generate unit tests for parsing the new `--output-csv` command-line argument.
    depends_on:
      - planning_list_models_enhancement
    agent_spec:
      type: test_generation
      input_artifacts:
        - src/main.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - tests/unit/test_main_cli.py
      instructions: |
        Create or update the unit test file `tests/unit/test_main_cli.py`.
        Generate tests specifically for the command-line argument parsing logic in `main.py`.
        Tests should cover:
        - Running `ai-whisperer --list-models --config config.yaml` (no --output-csv).
        - Running `ai-whisperer --list-models --config config.yaml --output-csv models.csv`.
        - Ensure the argument parser correctly identifies the `--output-csv` argument and its value.
        - Consider edge cases like missing argument value or incorrect usage if applicable to the argument parser library.
        The tests should verify that the argument is correctly parsed and available for use within the application logic.
        Avoid implementing logic that only passes these specific tests; the parsing should be general.
        Examine existing test files in `tests/unit/` for structure guidance.
      validation_criteria:
        - tests/unit/test_main_cli.py exists.
        - tests/unit/test_main_cli.py contains tests specifically for `--output-csv` argument parsing.
        - Tests cover cases with and without the `--output-csv` argument.
  - step_id: implement_list_models_argument_parsing
    description: Modify `main.py` to accept the new `--output-csv` command-line argument.
    depends_on:
      - test_generate_list_models_argument_parsing
    agent_spec:
      type: file_edit
      input_artifacts:
        - src/main.py
        - tests/unit/test_main_cli.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - src/main.py
      instructions: |
        Modify the `argparse` setup in `src/main.py`.
        Add an optional argument `--output-csv` which expects a file path as its value, specifically for use with the `--list-models` command.
        Ensure that existing command-line arguments and functionality are not broken.
        Do not implement the logic for fetching or saving data yet, only the argument parsing part.
        Examine existing code in `src/main.py` and utility modules.
        Ensure the implementation passes the tests defined in `tests/unit/test_main_cli.py`.
      validation_criteria:
        - Parsed arguments in `main.py` include the `--output-csv` option when provided.
        - Parsed arguments in `main.py` do not include the `--output-csv` option when not provided.
        - Existing command-line arguments are parsed correctly.
  - step_id: validate_list_models_argument_parsing
    description: Run tests to validate the `--output-csv` command-line argument parsing.
    depends_on:
      - implement_list_models_argument_parsing
    agent_spec:
      type: validation
      input_artifacts:
        - src/main.py
        - tests/unit/test_main_cli.py
      instructions: |
        Execute the specific tests in `tests/unit/test_main_cli.py` that verify the `--output-csv` command-line argument parsing.
        Use `pytest` to run the tests.
      validation_criteria:
        - pytest tests/unit/test_main_cli.py executes successfully.
        - All tests related to `--output-csv` argument parsing in tests/unit/test_main_cli.py pass.
  - step_id: test_generate_openrouter_api_details
    description: Generate unit tests for fetching comprehensive model details from the OpenRouter API.
    depends_on:
      - validate_list_models_argument_parsing
    agent_spec:
      type: test_generation
      input_artifacts:
        - src/OpenRouterAPI.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - tests/unit/test_openrouter_api.py
      instructions: |
        Create or update the unit test file `tests/unit/test_openrouter_api.py`.
        Generate tests specifically for the `OpenRouterAPI.list_models()` method or a new method if created.
        The tests should use mocking to simulate the OpenRouter API response.
        Tests should verify that the method:
        - Makes the correct API call to fetch comprehensive model details (not just basic names).
        - Correctly parses the API response to extract required details like features, costs, context window, and provider for multiple models.
        - Returns model data in a structured format suitable for display and export (e.g., a list of dictionaries or objects).
        Avoid special casing the implementation to pass only these tests.
        Examine existing test files in `tests/unit/` for structure guidance.
      validation_criteria:
        - tests/unit/test_openrouter_api.py exists.
        - tests/unit/test_openrouter_api.py contains tests for fetching and parsing comprehensive model details.
        - Tests use mocking to simulate API responses.
        - Tests verify extraction of details like features, costs, context window, provider, etc.
  - step_id: implement_openrouter_api_details_fetch
    description: Modify the OpenRouter API integration to fetch comprehensive model details.
    depends_on:
      - test_generate_openrouter_api_details
    agent_spec:
      type: file_edit
      input_artifacts:
        - src/OpenRouterAPI.py
        - tests/unit/test_openrouter_api.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - src/OpenRouterAPI.py
      instructions: |
        Modify the `OpenRouterAPI.list_models()` method or create a new method in `src/OpenRouterAPI.py`.
        Update the API call to OpenRouter to request detailed model information.
        Parse the API response to extract the required metadata for each model (features, cost per input/output token, context window size, provider information, and any other relevant available attributes).
        Return this detailed information in a structured format (e.g., a list of dictionaries).
        Ensure the implementation passes the tests defined in `tests/unit/test_openrouter_api.py`.
        Examine existing code in `src/OpenRouterAPI.py` and utility modules for code reuse.
      validation_criteria:
        - src/OpenRouterAPI.py is modified to fetch and parse detailed model information.
        - The modified method returns a list of dictionaries or similar structure containing comprehensive model data.
  - step_id: validate_openrouter_api_details_fetch
    description: Run tests to validate fetching comprehensive model details from the OpenRouter API.
    depends_on:
      - implement_openrouter_api_details_fetch
    agent_spec:
      type: validation
      input_artifacts:
        - src/OpenRouterAPI.py
        - tests/unit/test_openrouter_api.py
      instructions: |
        Execute the specific tests in `tests/unit/test_openrouter_api.py` that verify fetching and parsing comprehensive model details.
        Use `pytest` to run the tests.
      validation_criteria:
        - pytest tests/unit/test_openrouter_api.py executes successfully.
        - All tests related to fetching and parsing detailed model information in tests/unit/test_openrouter_api.py pass.
  - step_id: test_generate_csv_export
    description: Generate unit tests for formatting and exporting model details to a CSV file.
    depends_on:
      - validate_openrouter_api_details_fetch
    agent_spec:
      type: test_generation
      input_artifacts:
        - src/main.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - tests/unit/test_main_csv_export.py
      instructions: |
        Create or update the unit test file `tests/unit/test_main_csv_export.py`.
        Generate tests specifically for the logic that formats and writes the detailed model data to a CSV file.
        The tests should:
        - Use mock data representing the comprehensive model details fetched from the API.
        - Verify that when the `--output-csv` argument is provided, the data is correctly formatted into CSV rows (including headers).
        - Verify that the formatted data is written to the specified file path.
        - Verify the content and structure of the generated CSV file.
        - Consider potential issues like special characters in data or missing fields.
        Avoid implementing logic that only passes these specific tests.
        Examine existing test files in `tests/unit/` for structure guidance.
      validation_criteria:
        - tests/unit/test_main_csv_export.py exists.
        - tests/unit/test_main_csv_export.py contains tests for CSV formatting and writing.
        - Tests use mock data and verify the output CSV content and structure.
  - step_id: implement_csv_export_logic
    description: Implement the logic in `main.py` to format and export model details to CSV.
    depends_on:
      - test_generate_csv_export
      - validate_list_models_argument_parsing
      - validate_openrouter_api_details_fetch
    agent_spec:
      type: file_edit
      input_artifacts:
        - src/main.py
        - src/OpenRouterAPI.py
        - tests/unit/test_main_csv_export.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - src/main.py
      instructions: |
        Modify the `main.py` script in the section handling the `--list-models` command.
        Retrieve the detailed model information using the enhanced OpenRouter API method.
        Check if the `--output-csv` argument was provided during argument parsing.
        If `--output-csv` is provided:
        - Format the detailed model data into a structure suitable for CSV (e.g., list of lists or dictionaries).
        - Include appropriate header row(s).
        - Write the formatted data to the file path specified by the `--output-csv` argument.
        If `--output-csv` is NOT provided:
        - Continue to print a simple list of model names (or potentially a more detailed console output as per the proposed solution's spirit, but ensure the original simple list behavior is still possible). The primary focus of this step is CSV export.
        Ensure the implementation passes the tests defined in `tests/unit/test_main_csv_export.py`.
        Examine existing code in `src/main.py` and utility modules for code reuse, specifically regarding file handling or data formatting.
      validation_criteria:
        - src/main.py is modified to handle the `--output-csv` argument for the `--list-models` command.
        - When `--output-csv` is provided, a file is created at the specified path.
        - The created CSV file contains a header row and detailed model data formatted correctly.
        - When `--output-csv` is not provided, console output still functions (though the content might be enhanced later, the basic flow should remain).
  - step_id: validate_csv_export_logic
    description: Run tests to validate the CSV export functionality.
    depends_on:
      - implement_csv_export_logic
    agent_spec:
      type: validation
      input_artifacts:
        - src/main.py
        - tests/unit/test_main_csv_export.py
      instructions: |
        Execute the specific tests in `tests/unit/test_main_csv_export.py` that verify the CSV export logic.
        Use `pytest` to run the tests.
      validation_criteria:
        - pytest tests/unit/test_main_csv_export.py executes successfully.
        - All tests related to CSV formatting and writing in tests/unit/test_main_csv_export.py pass.
  - step_id: implement_console_output_enhancement
    description: Enhance the console output for `--list-models` when CSV output is not requested.
    depends_on:
      - validate_csv_export_logic # Depend on CSV logic being done, as it uses the same data source
    agent_spec:
      type: file_edit
      input_artifacts:
        - src/main.py
        - src/OpenRouterAPI.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - src/main.py
      instructions: |
        Modify the `main.py` script in the section handling the `--list-models` command when the `--output-csv` argument is NOT provided.
        Instead of just printing model names, print a more detailed summary of each model using the comprehensive data fetched from the OpenRouter API.
        Present the information clearly in the console, possibly using formatting to align columns or highlight key details (e.g., model name, provider, cost per token, context window).
        Ensure the original behavior of listing models to the console is still functional, just with enhanced details.
        Examine existing code in `src/main.py` and utility modules for code reuse regarding console output formatting.
      validation_criteria:
        - src/main.py is modified to provide detailed console output for `--list-models` when `--output-csv` is not used.
        - Console output includes details like model name, provider, cost, and context window for each model.
        - The output is formatted for readability in the console.
  - step_id: test_generate_console_output_enhancement
    description: Generate unit tests for the enhanced console output of model details.
    depends_on:
      - implement_console_output_enhancement # Generate tests after basic implementation to verify output format
    agent_spec:
      type: test_generation
      input_artifacts:
        - src/main.py
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - tests/unit/test_main_console_output.py
      instructions: |
        Create a new unit test file `tests/unit/test_main_console_output.py`.
        Generate tests for the enhanced console output of the `--list-models` command when `--output-csv` is not used.
        The tests should:
        - Use mock data representing the comprehensive model details.
        - Capture the standard output (stdout) when running the `--list-models` command without `--output-csv`.
        - Verify that the captured output contains the expected detailed information for multiple models.
        - Verify the formatting of the console output (e.g., presence of key information, basic structure).
        Avoid implementing logic that only passes these specific tests.
        Examine existing test files in `tests/unit/` for structure guidance.
      validation_criteria:
        - tests/unit/test_main_console_output.py exists.
        - tests/unit/test_main_console_output.py contains tests for the enhanced console output.
        - Tests capture stdout and verify the content and basic formatting of the model details.
  - step_id: validate_console_output_enhancement
    description: Run tests to validate the enhanced console output.
    depends_on:
      - test_generate_console_output_enhancement
    agent_spec:
      type: validation
      input_artifacts:
        - src/main.py
        - tests/unit/test_main_console_output.py
      instructions: |
        Execute the specific tests in `tests/unit/test_main_console_output.py` that verify the enhanced console output.
        Use `pytest` to run the tests.
      validation_criteria:
        - pytest tests/unit/test_main_console_output.py executes successfully.
        - All tests related to console output enhancement in tests/unit/test_main_console_output.py pass.
  - step_id: update_documentation
    description: Update documentation (README, CLI help) to reflect the new `--output-csv` option and enhanced output.
    depends_on:
      - validate_console_output_enhancement
      - validate_csv_export_logic
    agent_spec:
      type: documentation
      input_artifacts:
        - README.md
        - src/main.py # For CLI help string
        - docs/list_models_enhancement_plan.md
      output_artifacts:
        - README.md
        - src/main.py # For updated CLI help string
      instructions: |
        Update the `README.md` file to include documentation for the `--list-models` command enhancement.
        Explain the new `--output-csv` option, its purpose, and how to use it with an example usage command.
        Describe the detailed information now available in the console output when `--output-csv` is not used.
        Update the help string within `src/main.py` for the `--list-models` argument parser to include information about the new `--output-csv` option.
      validation_criteria:
        - README.md is updated with details about the `--list-models` enhancement.
        - README.md explains the `--output-csv` option and its usage.
        - README.md describes the enhanced console output.
        - The help message for `ai-whisperer --list-models` includes documentation for the `--output-csv` option.
```""")

    try:
        # Read the test file
        with open(test_file_path, 'r', encoding='utf-8') as f:
            input_yaml = f.read()

        # Create a pipeline with clean_backtick_wrapper, escape_text_fields, and normalize_indentation
        # This matches the orchestrator's pipeline order
        pipeline = PostprocessingPipeline(
            scripted_steps=[clean_backtick_wrapper, escape_text_fields, normalize_indentation]
        )

        # Process the YAML string
        try:
            modified_yaml_string, result = pipeline.process(input_yaml)
            assert False, "Expected an exception but none was raised"
        except Exception as e:
            # Verify that the exception is the expected one
            assert "Error normalizing indentation" in str(e)
            assert "expected <block end>, but found '<block mapping start>'" in str(e)

    finally:
        # Clean up the test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
