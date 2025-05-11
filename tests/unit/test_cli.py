import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Import the main function and command classes
from ai_whisperer.cli import main
from ai_whisperer.commands import (
    ListModelsCommand,
    GenerateInitialPlanCommand,
    GenerateOverviewPlanCommand,
    RefineCommand,
    RunCommand,
)

# Define a fixture to capture stdout/stderr for testing SystemExit messages
@pytest.fixture
def capsys_sys_exit(capsys):
    """Fixture to capture stdout/stderr when SystemExit occurs."""
    yield capsys

# Mock the command classes to prevent actual execution
@pytest.fixture(autouse=True)
def mock_commands():
    with patch('ai_whisperer.cli.ListModelsCommand') as MockListModelsCommand, \
         patch('ai_whisperer.cli.GenerateInitialPlanCommand') as MockGenerateInitialPlanCommand, \
         patch('ai_whisperer.cli.GenerateOverviewPlanCommand') as MockGenerateOverviewPlanCommand, \
         patch('ai_whisperer.cli.RefineCommand') as MockRefineCommand, \
         patch('ai_whisperer.cli.RunCommand') as MockRunCommand:
        yield {
            "ListModelsCommand": MockListModelsCommand,
            "GenerateInitialPlanCommand": MockGenerateInitialPlanCommand,
            "GenerateOverviewPlanCommand": MockGenerateOverviewPlanCommand,
            "RefineCommand": MockRefineCommand,
            "RunCommand": MockRunCommand,
        }

# Mock setup_logging and setup_rich_output to prevent side effects during tests
@pytest.fixture(autouse=True)
def mock_setup():
    with patch('ai_whisperer.cli.setup_logging'), \
         patch('ai_whisperer.cli.setup_rich_output'):
        yield

# --- Test Cases for Each Command ---

def test_list_models_command_valid_args(mock_commands):
    """Test parsing valid arguments for the list-models command."""
    args = ["list-models", "--config", "path/to/config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config_path="path/to/config.yaml",
        output_csv=None
    )
    assert isinstance(commands[0], MagicMock) # Check if the mocked object is returned

def test_list_models_command_with_output_csv(mock_commands):
    """Test parsing valid arguments for the list-models command with --output-csv."""
    args = ["list-models", "--config", "path/to/config.yaml", "--output-csv", "output.csv"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config_path="path/to/config.yaml",
        output_csv="output.csv"
    )
    assert isinstance(commands[0], MagicMock)

def test_list_models_command_missing_config(capsys_sys_exit):
    """Test list-models command with missing --config argument."""
    args = ["list-models"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0 # Should exit with a non-zero code on error
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_initial_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate-initial-plan command."""
    args = ["generate-initial-plan", "--requirements", "reqs.md", "--config", "config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config_path="config.yaml",
        output_dir="output", # Default value
        requirements_path="reqs.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_initial_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate-initial-plan command with --output."""
    args = ["generate-initial-plan", "--requirements", "reqs.md", "--config", "config.yaml", "--output", "plans"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config_path="config.yaml",
        output_dir="plans",
        requirements_path="reqs.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_initial_plan_command_missing_requirements(capsys_sys_exit):
    """Test generate-initial-plan command with missing --requirements argument."""
    args = ["generate-initial-plan", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --requirements" in captured.err

def test_generate_initial_plan_command_missing_config(capsys_sys_exit):
    """Test generate-initial-plan command with missing --config argument."""
    args = ["generate-initial-plan", "--requirements", "reqs.md"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_overview_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate-overview-plan command."""
    args = ["generate-overview-plan", "--initial-plan", "initial.json", "--config", "config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config_path="config.yaml",
        output_dir="output", # Default value
        initial_plan_path="initial.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_overview_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate-overview-plan command with --output."""
    args = ["generate-overview-plan", "--initial-plan", "initial.json", "--config", "config.yaml", "--output", "overview_plans"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config_path="config.yaml",
        output_dir="overview_plans",
        initial_plan_path="initial.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_overview_plan_command_missing_initial_plan(capsys_sys_exit):
    """Test generate-overview-plan command with missing --initial-plan argument."""
    args = ["generate-overview-plan", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --initial-plan" in captured.err

def test_generate_overview_plan_command_missing_config(capsys_sys_exit):
    """Test generate-overview-plan command with missing --config argument."""
    args = ["generate-overview-plan", "--initial-plan", "initial.json"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err


def test_refine_command_valid_args(mock_commands):
    """Test parsing valid arguments for the refine command."""
    args = ["refine", "input.md", "--config", "config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["RefineCommand"].assert_called_once_with(
        config_path="config.yaml",
        input_file="input.md",
        iterations=1, # Default value
        prompt_file=None, # Default value
        output=None # Default value
    )
    assert isinstance(commands[0], MagicMock)

def test_refine_command_with_optional_args(mock_commands):
    """Test parsing valid arguments for the refine command with optional args."""
    args = ["refine", "input.md", "--config", "config.yaml", "--iterations", "5", "--prompt-file", "prompt.txt", "--output", "refined.md"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["RefineCommand"].assert_called_once_with(
        config_path="config.yaml",
        input_file="input.md",
        iterations=5,
        prompt_file="prompt.txt",
        output="refined.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_refine_command_missing_input_file(capsys_sys_exit):
    """Test refine command with missing input_file argument."""
    args = ["refine", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: input_file" in captured.err

def test_refine_command_missing_config(capsys_sys_exit):
    """Test refine command with missing --config argument."""
    args = ["refine", "input.md"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_run_command_valid_args(mock_commands):
    """Test parsing valid arguments for the run command."""
    args = ["run", "--plan-file", "plan.json", "--state-file", "state.json", "--config", "config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["RunCommand"].assert_called_once_with(
        config_path="config.yaml",
        plan_file="plan.json",
        state_file="state.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_run_command_missing_plan_file(capsys_sys_exit):
    """Test run command with missing --plan-file argument."""
    args = ["run", "--state-file", "state.json", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --plan-file" in captured.err

def test_run_command_missing_state_file(capsys_sys_exit):
    """Test run command with missing --state-file argument."""
    args = ["run", "--plan-file", "plan.json", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --state-file" in captured.err

def test_run_command_missing_config(capsys_sys_exit):
    """Test run command with missing --config argument."""
    args = ["run", "--plan-file", "plan.json", "--state-file", "state.json"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_invalid_command(capsys_sys_exit):
    """Test with an invalid command."""
    args = ["invalid-command"]
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "invalid choice: 'invalid-command'" in captured.err

def test_no_command(capsys_sys_exit):
    """Test with no command provided."""
    args = []
    with pytest.raises(SystemExit) as e:
        main(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: command" in captured.err

def test_project_dir_argument(mock_commands):
    """Test the --project-dir argument."""
    args = ["--project-dir", "/fake/project", "list-models", "--config", "config.yaml"]
    commands = main(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config_path="config.yaml",
        output_csv=None
    )
    assert isinstance(commands[0], MagicMock)
    # Note: The project_dir argument is parsed but not directly used in the command instantiation
    # in the current cli.py logic, so we primarily test that parsing doesn't fail and the
    # correct command is still instantiated.