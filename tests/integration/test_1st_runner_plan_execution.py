import os
import pytest
from src.ai_whisperer.plan_runner import PlanRunner
import tempfile

from src.ai_whisperer.config import load_config
from src.ai_whisperer.plan_parser import ParserPlan

# Define the path to the 1st_runner_test plan
PLAN_PATH = "tests/runner_tests/first_full_test/overview_first_full_test.json"
OUTPUT_DIR = "tests/runner_tests/first_full_test/output/" # Assuming output files are created here

@pytest.fixture
def plan_runner():
    """Fixture to provide a PlanRunner instance with loaded configuration."""
    # Load the configuration from the YAML file
    config = load_config("project_dev/aiwhisperer_config.yaml")

    # PlanRunner expects a config dictionary
    return PlanRunner(config)

@pytest.mark.integration
def test_1st_runner_plan_execution_success(plan_runner: PlanRunner):
    """
    Test that the 1st_runner_test plan executes successfully using the PlanRunner.
    """
    # Create a temporary state file path
# Explicitly remove the temporary state file to ensure a clean run
    # Create a temporary state file and get its path
    tmp_state_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    state_file_path = tmp_state_file.name
    tmp_state_file.close() # Close the file handle immediately after getting the name

# Explicitly remove the temporary state file to ensure a clean run
    os.remove(state_file_path)
    # Ensure the output directory exists and is empty before the test
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for file_name in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Define paths for generated files
    generated_script_path = os.path.join(PLAN_PATH, "generate_squares.py")
    output_file_path = os.path.join(OUTPUT_DIR, "test.txt")

    # Clean up previous runs if files exist
    if os.path.exists(generated_script_path):
        os.remove(generated_script_path)
    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    try:
        # Create a ParserPlan instance and load the plan
        plan_parser = ParserPlan()
        plan_parser.load_overview_plan(PLAN_PATH)

        # Run the plan
        success = plan_runner.run_plan(plan_parser, state_file_path)

        # Assert that the plan execution was successful
        assert success is True, "1st_runner_test plan execution failed"

        # Add assertions to verify the outcome of the plan execution
        # Based on docs/runner_test_analysis.md, the plan should create:
        # - generate_squares.py (in the plan directory)
        # - test.txt (in the output directory of the plan)

        assert os.path.exists(generated_script_path), f"Generated script not found at {generated_script_path}"
        assert os.path.exists(output_file_path), f"Output file not found at {output_file_path}"

        # Verify content of test.txt
        # The expected content is a sequence of squares from 1 to 10, each on a new line.
        expected_content = "\n".join([str(i**2) for i in range(1, 11)]) + "\n" # Add newline at the end

        with open(output_file_path, "r") as f:
            output_content = f.read()

        assert output_content == expected_content, f"Output file content mismatch. Expected:\n{expected_content}\nGot:\n{output_content}"

    except Exception as e:
        pytest.fail(f"An error occurred during plan execution: {e}")
    finally:
        # Clean up the temporary state file and generated/output files
        if os.path.exists(state_file_path):
            os.remove(state_file_path)
        if os.path.exists(generated_script_path):
            os.remove(generated_script_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)