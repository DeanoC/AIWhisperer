import pytest
from unittest.mock import patch, MagicMock

# Import the main function and command classes
from ai_whisperer.cli import cli
from ai_whisperer.config import load_config
from ai_whisperer.path_management import PathManager # Import load_config to mock it
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

# Mock setup_logging and load_config to prevent side effects during tests
@pytest.fixture(autouse=True)
def reset_path_manager_instance():
    PathManager._instance = None  # Reset the singleton instance
    PathManager._initialized = False  # Reset the initialized flag

@pytest.fixture(autouse=True)
def mock_setup(reset_path_manager_instance):
    with patch('ai_whisperer.logging_custom.setup_logging'), \
         patch('ai_whisperer.cli.load_config') as mock_load_config: # Mock load_config
        mock_load_config.return_value = {} # Return an empty dict for config
        yield mock_load_config # Yield the mock object

# --- Test Cases for Each Command ---

def test_list_models_command_valid_args(mock_commands):
    """Test parsing valid arguments for the list-models command."""
    args = ["--config", "path/to/config.yaml", "list-models"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_csv=None
    )
    assert isinstance(commands[0], MagicMock) # Check if the mocked object is returned

def test_list_models_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the list-models command with --config before the command."""
    args = ["--config", "path/to/config.yaml", "list-models"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_csv=None
    )
    assert isinstance(commands[0], MagicMock)

def test_list_models_command_with_output_csv(mock_commands):
    """Test parsing valid arguments for the list-models command with --output-csv."""
    args = ["--config", "path/to/config.yaml", "list-models", "--output-csv", "output.csv"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["ListModelsCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_csv="output.csv"
    )
    assert isinstance(commands[0], MagicMock)

def test_list_models_command_missing_config(capsys_sys_exit):
    """Test list-models command with missing --config argument."""
    args = ["list-models"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0 # Should exit with a non-zero code on error
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_initial_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate initial-plan command."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="output", # Default value
        requirements_path="reqs.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_initial_plan_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the generate initial-plan command with --config before the command."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="output", # Default value
        requirements_path="reqs.md"
    )
    assert isinstance(commands[0], MagicMock)


def test_generate_initial_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate-initial-plan command with --output."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md", "--output", "plans"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="plans",
        requirements_path="reqs.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_initial_plan_command_missing_requirements(capsys_sys_exit):
    """Test generate-initial-plan command with missing requirements argument."""
    args = ["generate", "initial-plan", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_initial_plan_command_missing_config(capsys_sys_exit):
    """Test generate-initial-plan command with missing --config argument."""
    args = ["generate", "initial-plan", "reqs.md"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_overview_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate overview-plan command."""
    args = ["--config", "config.yaml", "generate", "overview-plan", "initial.json"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="output", # Default value
        initial_plan_path="initial.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_overview_plan_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the generate overview-plan command with --config before the command."""
    args = ["--config", "config.yaml", "generate", "overview-plan", "initial.json"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="output", # Default value
        initial_plan_path="initial.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_overview_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate overview-plan command with --output."""
    args = ["--config", "config.yaml", "generate", "overview-plan", "initial.json", "--output", "overview_plans"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="overview_plans",
        initial_plan_path="initial.json"
    )
    assert isinstance(commands[0], MagicMock)

def test_generate_overview_plan_command_missing_initial_plan(capsys_sys_exit):
    """Test generate overview-plan command with missing initial-plan argument."""
    args = ["generate", "overview-plan", "--config", "config.yaml"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_overview_plan_command_missing_config(capsys_sys_exit):
    """Test generate overview-plan command with missing --config argument."""
    args = ["generate", "overview-plan", "initial.json"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_generate_full_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate full-plan command."""
    args = ["--config", "config.yaml", "generate", "full-plan", "reqs.md", "--output", "plans"]
    commands = cli(args)

    assert len(commands) == 2
    mock_commands["GenerateInitialPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="plans",
        requirements_path="reqs.md"
    )
    mock_commands["GenerateOverviewPlanCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        output_dir="plans",
        initial_plan_path="<output_of_generate_initial_plan_command>"
    )
    assert all(isinstance(command, MagicMock) for command in commands)

def test_refine_command_valid_args(mock_commands):
    """Test parsing valid arguments for the refine command."""
    args = ["--config", "config.yaml", "refine", "input.md"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["RefineCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        input_file="input.md",
        iterations=1, # Default value
        prompt_file=None, # Default value
        output=None # Default value
    )
    assert isinstance(commands[0], MagicMock)

def test_refine_command_with_optional_args(mock_commands):
    """Test parsing valid arguments for the refine command with optional args."""
    args = ["--config", "config.yaml", "refine", "input.md", "--iterations", "5", "--prompt-file", "prompt.txt", "--output", "refined.md"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["RefineCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        input_file="input.md",
        iterations=5,
        prompt_file="prompt.txt",
        output="refined.md"
    )
    assert isinstance(commands[0], MagicMock)

def test_refine_command_missing_input_file(capsys_sys_exit):
    """Test refine command with missing input_file argument."""
    args = ["--config", "config.yaml", "refine"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: input_file" in captured.err

def test_refine_command_missing_config(capsys_sys_exit):
    """Test refine command with missing --config argument."""
    args = ["refine", "input.md"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_run_command_valid_args(mock_commands):
    """Test parsing valid arguments for the run command."""
    args = ["--config", "config.yaml", "run", "--plan-file", "plan.json", "--state-file", "state.json"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["RunCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        plan_file="plan.json",
        state_file="state.json",
        monitor=False # Added expected monitor argument
    )
    assert isinstance(commands[0], MagicMock)

def test_run_command_missing_plan_file(capsys_sys_exit):
    """Test run command with missing --plan-file argument."""
    args = ["--config", "config.yaml", "run", "--state-file", "state.json"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --plan-file" in captured.err

def test_run_command_missing_state_file(capsys_sys_exit):
    """Test run command with missing --state-file argument."""
    args = ["--config", "config.yaml", "run", "--plan-file", "plan.json"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --state-file" in captured.err

def test_run_command_missing_config(capsys_sys_exit):
    """Test run command with missing --config argument."""
    args = ["run", "--plan-file", "plan.json", "--state-file", "state.json"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_run_command_with_monitor(mock_commands):
    """Test parsing arguments for the run command with --monitor."""
    args = ["--config", "config.yaml", "run", "--plan-file", "plan.json", "--state-file", "state.json", "--monitor"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["RunCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        plan_file="plan.json",
        state_file="state.json",
        monitor=True
    )
    assert isinstance(commands[0], MagicMock)

def test_run_command_without_monitor(mock_commands):
    """Test parsing arguments for the run command without --monitor."""
    args = ["--config", "config.yaml", "run", "--plan-file", "plan.json", "--state-file", "state.json"]
    commands = cli(args)

    assert len(commands) == 1
    mock_commands["RunCommand"].assert_called_once_with(
        config={}, # Pass the loaded config object
        plan_file="plan.json",
        state_file="state.json",
        monitor=False # Default value
    )
    assert isinstance(commands[0], MagicMock)

def test_cli_passes_path_args_to_load_config(mock_setup):
    """Test that path-related CLI arguments are passed to load_config."""
    # mock_setup fixture yields the mock_load_config object
    mock_load_config = mock_setup # Access the mock object yielded by mock_setup

    args = [
        "--config", "path/to/config.yaml",
        "--project-path", "/cli/project",
        "--output-path", "/cli/output",
        "--workspace-path", "/cli/workspace",
        "list-models" # A valid command is needed for parsing to complete
    ]
    cli(args)

    # Check that load_config was called with the correct cli_args
    mock_load_config.assert_called_once()
    called_cli_args = mock_load_config.call_args[1]['cli_args'] # Get the 'cli_args' keyword argument

    assert called_cli_args is not None
    assert isinstance(called_cli_args, dict)
    assert called_cli_args.get("project_path") == "/cli/project"
    assert called_cli_args.get("output_path") == "/cli/output"
    assert called_cli_args.get("workspace_path") == "/cli/workspace"
    assert called_cli_args.get("config") == "path/to/config.yaml" # config arg should also be present

def test_invalid_command(capsys_sys_exit):
    """Test with an invalid command."""
    args = ["invalid-command"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "invalid choice: 'invalid-command'" in captured.err

def test_no_command(capsys_sys_exit):
    """Test with no command provided."""
    args = []
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config, command" in captured.err
