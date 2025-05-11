import pytest
import sys
import json
import argparse  # Import argparse
from unittest.mock import patch, MagicMock
from pathlib import Path

# Assuming the main CLI entry point is in src/ai_whisperer/main.py
# and the run command logic is within a function like run_command_handler
# or accessible via the main entry point function.
# We'll need to patch sys.argv and potentially the entry point function.

# Mock the necessary components


# Fixture for tests that need sys.exit patched (normal success/failure cases)
@pytest.fixture
def mock_dependencies():
    with patch("src.ai_whisperer.main.Orchestrator") as MockOrchestrator, patch(
        "src.ai_whisperer.main.load_config"
    ) as mock_load_config, patch("src.ai_whisperer.main.ParserPlan") as MockParserPlan, patch(
        "sys.exit"
    ) as mock_sys_exit, patch(
        "src.ai_whisperer.main.setup_rich_output"
    ) as mock_setup_rich_output:
        # Configure mocks
        mock_orchestrator_instance = MockOrchestrator.return_value
        mock_orchestrator_instance.run_plan.return_value = None
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Configure the mocked ParserPlan instance
        mock_parser_plan_instance = MockParserPlan.return_value
        # Assume main calls load_overview_plan based on traceback
        mock_parser_plan_instance.load_overview_plan.return_value = None  # load methods don't return value
        mock_parser_plan_instance.get_parsed_plan.return_value = {
            "task_id": "test-task",
            "plan": [],
        }  # Configure return for get_parsed_plan

        yield MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output


# Fixture for tests that must let sys.exit raise SystemExit (argparse error cases)
@pytest.fixture
def mock_dependencies_no_exit_patch():
    with patch("src.ai_whisperer.main.Orchestrator") as MockOrchestrator, patch(
        "src.ai_whisperer.main.load_config"
    ) as mock_load_config, patch("src.ai_whisperer.main.ParserPlan") as MockParserPlan, patch(
        "src.ai_whisperer.main.setup_rich_output"
    ) as mock_setup_rich_output:
        mock_orchestrator_instance = MockOrchestrator.return_value
        mock_orchestrator_instance.run_plan.return_value = None
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        # Configure the mocked ParserPlan instance
        mock_parser_plan_instance = MockParserPlan.return_value
        # Assume main calls load_overview_plan based on traceback
        mock_parser_plan_instance.load_overview_plan.return_value = None  # load methods don't return value
        mock_parser_plan_instance.get_parsed_plan.return_value = {
            "task_id": "test-task",
            "plan": [],
        }  # Configure return for get_parsed_plan

        yield MockOrchestrator, mock_load_config, MockParserPlan, mock_setup_rich_output


# Import the main entry point function after patching dependencies
# This assumes the CLI logic is in a function like `cli_entry_point` in main.py
# If the logic is directly in the script, we might need a different approach
# or refactor main.py to have a testable function.
# For now, let's assume there's a function like `main` that parses args and calls handlers.
# We'll need to adjust the import based on the actual structure of main.py
# Assuming a structure where `main()` is the entry point and it calls a handler based on subparsers.
# We'll patch `sys.argv` and call `main.main()`.

# Need to import main after patching, but before tests that use it.
# This might require a slight adjustment depending on how main.py is structured.
# Let's assume `main.py` has a function `main()` that processes CLI args.
# We'll import it within the test functions or fixtures if needed, or rely on patching sys.argv
# and then importing main to trigger the arg parsing.

# Let's try importing main here and see if patching sys.argv before calling main.main() works.
# If main.py executes logic on import, this might need adjustment.
# Assuming main.py has an `if __name__ == "__main__": main()` block.
# We will patch sys.argv and then call main.main() in tests.

# Need to import main after the patch setup, but before tests run.
# Let's import it inside the test functions or use a fixture that imports it.
# A fixture seems cleaner.


@pytest.fixture
def run_main_command(mock_dependencies):
    # This fixture will set sys.argv and call the main entry point function.
    # We need to import main *after* setting up patches and sys.argv.
    # This is a bit tricky with how Python imports work and script execution.
    # A common pattern is to have a testable function in main.py that takes args directly.
    # If main.py is structured with `if __name__ == "__main__": main()`,
    # we can patch sys.argv and then import main to trigger the execution of the `main()` function.
    # However, patching sys.argv and then importing might not work as expected if arg parsing
    # happens at the top level of main.py.

    # Let's assume main.py has a function `cli_entry_point()` that we can call.
    # If not, we'll need to adjust based on the actual structure.
    # For now, let's assume we can patch sys.argv and call a function.
    # We'll need to import main *within* the test function or fixture after patching sys.argv.

    def _run_main(args):
        from src.ai_whisperer import main

        return main.main(args)

    return _run_main


# --- Test Cases ---


def test_run_command_parses_required_args(run_main_command, mock_dependencies):
    """Test that the run command correctly parses required arguments."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output) = mock_dependencies

    plan_file = "path/to/plan.json"
    state_file = "path/to/state.json"
    config_file = "path/to/config.yaml"

    exit_code = run_main_command(["run", "--plan-file", plan_file, "--state-file", state_file, "--config", config_file])

    # Verify load_config was called with the correct config file
    mock_load_config.assert_called_once_with(config_file)

    # Verify ParserPlan was instantiated and load_overview_plan was called
    MockParserPlan.assert_called_once_with()  # Assuming no args needed for instantiation
    mock_parser_plan_instance = MockParserPlan.return_value
    # Assuming main calls load_overview_plan based on traceback
    mock_parser_plan_instance.load_overview_plan.assert_called_once_with(str(Path(plan_file)))
    # The plan data is now obtained via get_parsed_plan, which is mocked in the fixture

    # Verify Orchestrator was instantiated with correct config (output_dir might need adjustment based on plan)
    # The plan mentions output_dir="." as a possibility. Let's assume this for now.
    MockOrchestrator.assert_called_once_with(mock_load_config.return_value, output_dir=".")

    # Verify run_plan was called with the correct plan data and state file
    mock_orchestrator_instance = MockOrchestrator.return_value
    mock_orchestrator_instance.run_plan.assert_called_once_with(
        plan_parser=mock_parser_plan_instance, state_file_path=state_file
    )

    # Verify sys.exit(0) was called on success
    assert exit_code == 0


def test_run_command_missing_plan_file(run_main_command, mock_dependencies_no_exit_patch):
    """Test that the run command exits with an error if --plan-file is missing."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_setup_rich_output) = mock_dependencies_no_exit_patch

    # Run command without --plan-file
    # Run command without --plan-file
    # Use fixture that does NOT patch sys.exit so SystemExit is raised
    def _run():
        return run_main_command(["run", "--state-file", "state.json", "--config", "config.yaml"])

    with pytest.raises(SystemExit) as excinfo:
        _run()
    assert excinfo.value.code == 2
    # Note: argparse prints error to stderr, which pytest captures.
    # We are not asserting console output here as argparse handles it.


def test_run_command_missing_state_file(run_main_command, mock_dependencies_no_exit_patch):
    """Test that the run command exits with an error if --state-file is missing."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_setup_rich_output) = mock_dependencies_no_exit_patch

    # Run command without --state-file
    # Run command without --state-file
    def _run():
        return run_main_command(["run", "--plan-file", "plan.json", "--config", "config.yaml"])

    with pytest.raises(SystemExit) as excinfo:
        _run()
    assert excinfo.value.code == 2


def test_run_command_missing_config_file(run_main_command, mock_dependencies_no_exit_patch):
    """Test that the run command exits with an error if --config is missing."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_setup_rich_output) = mock_dependencies_no_exit_patch

    # Run command without --config
    # Run command without --config
    def _run():
        return run_main_command(["run", "--plan-file", "plan.json", "--state-file", "state.json"])

    with pytest.raises(SystemExit) as excinfo:
        _run()
    assert excinfo.value.code == 2


from src.ai_whisperer.plan_parser import (
    PlanFileNotFoundError,
    PlanInvalidJSONError,
    PlanValidationError,
    SubtaskFileNotFoundError,
    SubtaskInvalidJSONError,
    SubtaskValidationError,
    PlanNotLoadedError,
)


def test_run_command_plan_file_not_found(run_main_command, mock_dependencies):
    """Test that the run command handles PlanFileNotFoundError for the plan file."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output) = mock_dependencies

    # Get the mocked ParserPlan instance
    mock_parser_plan_instance = MockParserPlan.return_value

    # Configure mock_parser_plan_instance.load_overview_plan to raise PlanFileNotFoundError
    plan_file = "nonexistent/plan.json"
    mock_parser_plan_instance.load_overview_plan.side_effect = PlanFileNotFoundError(
        f"Overview plan file not found: {plan_file}"
    )

    state_file = "path/to/state.json"
    config_file = "path/to/config.yaml"

    run_main_command(["run", "--plan-file", plan_file, "--state-file", state_file, "--config", config_file])

    # Verify ParserPlan was instantiated and load_overview_plan was called
    MockParserPlan.assert_called_once_with()
    mock_parser_plan_instance.load_overview_plan.assert_called_once_with(str(Path(plan_file)))

    # Verify sys.exit(1) was called
    mock_sys_exit.assert_called_once_with(1)
    # Verify an error message indicating file not found was printed
    mock_setup_rich_output.return_value.print.assert_called()
    # You could add more specific checks on the console output if needed


def test_run_command_invalid_plan_json(run_main_command, mock_dependencies):
    """Test that the run command handles PlanInvalidJSONError for the plan file."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output) = mock_dependencies

    # Get the mocked ParserPlan instance
    mock_parser_plan_instance = MockParserPlan.return_value

    # Configure mock_parser_plan_instance.load_overview_plan to raise PlanInvalidJSONError
    plan_file = "path/to/invalid.json"
    mock_parser_plan_instance.load_overview_plan.side_effect = PlanInvalidJSONError(
        f"Malformed JSON in file {plan_file}: Invalid JSON"
    )

    state_file = "path/to/state.json"
    config_file = "path/to/config.yaml"

    run_main_command(["run", "--plan-file", plan_file, "--state-file", state_file, "--config", config_file])

    # Verify ParserPlan was instantiated and load_overview_plan was called
    MockParserPlan.assert_called_once_with()
    mock_parser_plan_instance.load_overview_plan.assert_called_once_with(str(Path(plan_file)))

    # Verify sys.exit(1) was called
    mock_sys_exit.assert_called_once_with(1)
    # Verify an error message indicating invalid JSON was printed
    mock_setup_rich_output.return_value.print.assert_called()


def test_run_command_plan_not_dict(run_main_command, mock_dependencies):
    """Test that the run command handles PlanValidationError for plan file content that is not a JSON object."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output) = mock_dependencies

    # Get the mocked ParserPlan instance
    mock_parser_plan_instance = MockParserPlan.return_value

    # Configure mock_parser_plan_instance.load_overview_plan to raise PlanValidationError
    plan_file = "path/to/list_plan.json"
    mock_parser_plan_instance.load_overview_plan.side_effect = PlanValidationError(
        f"'plan' field in '{plan_file}' must be a list."
    )

    state_file = "path/to/state.json"
    config_file = "path/to/config.yaml"

    run_main_command(["run", "--plan-file", plan_file, "--state-file", state_file, "--config", config_file])

    # Verify ParserPlan was instantiated and load_overview_plan was called
    MockParserPlan.assert_called_once_with()
    mock_parser_plan_instance.load_overview_plan.assert_called_once_with(str(Path(plan_file)))

    # Verify sys.exit(1) was called
    mock_sys_exit.assert_called_once_with(1)
    # Verify an error message indicating the plan must be a JSON object was printed
    mock_setup_rich_output.return_value.print.assert_called()


def test_run_command_orchestrator_error(run_main_command, mock_dependencies):
    """Test that the run command handles errors raised by the Orchestrator."""
    (MockOrchestrator, mock_load_config, MockParserPlan, mock_sys_exit, mock_setup_rich_output) = mock_dependencies

    # Assuming there's an OrchestratorError defined in ai_whisperer.exceptions
    # If not, we might need to define a custom exception for testing or use a generic Exception.
    # Let's assume AIWhispererError is the base exception as per the plan's error handling section.
    from src.ai_whisperer.exceptions import AIWhispererError

    # Configure the mocked orchestrator's run_plan to raise an error
    mock_orchestrator_instance = MockOrchestrator.return_value
    mock_orchestrator_instance.run_plan.side_effect = AIWhispererError("Orchestration failed")

    plan_file = "path/to/plan.json"
    state_file = "path/to/state.json"
    config_file = "path/to/config.yaml"

    run_main_command(["run", "--plan-file", plan_file, "--state-file", state_file, "--config", config_file])

    # Verify sys.exit(1) was called
    mock_sys_exit.assert_called_once_with(1)
    # Verify an error message indicating orchestration error was printed
    mock_setup_rich_output.return_value.print.assert_called()


# Note: Testing state management mocking directly in main.py is not needed based on the plan,
# as state management is handled within the Orchestrator. The tests for Orchestrator
# should cover state management interactions.

# If main.py were to directly call state_management functions, we would add tests like:
# def test_run_command_loads_and_saves_state(run_main_command, mock_dependencies):
#     with patch('src.ai_whisperer.main.state_management.load_state') as mock_load_state, \
#          patch('src.ai_whisperer.main.state_management.save_state') as mock_save_state:
#         # Configure mocks and run command
#         # Assert mock_load_state and mock_save_state were called with correct args
#         pass
