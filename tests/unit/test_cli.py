
import pytest
from unittest.mock import patch, MagicMock

from monitor.user_message_delegate import UserMessageLevel # Import UserMessageLevel

# Minimal valid config for CLI commands to not error
minimal_config = {
    "openrouter": {
        "api_key": "mock_api_key",
        "model": "mock_model",
        "params": {"temperature": 0.5},
        "site_url": "mock_url",
        "app_name": "mock_app",
    },
    "prompts": {
        "subtask_generator_prompt_content": "dummy"
    },
    "output_dir": "./test_output/",
}

# Import the main function and command classes
from ai_whisperer.cli import cli
from ai_whisperer.path_management import PathManager # Import load_config to mock it
# Define a fixture to capture stdout/stderr for testing SystemExit messages
@pytest.fixture
def capsys_sys_exit(capsys):
    """Fixture to capture stdout/stderr when SystemExit occurs."""
    yield capsys

# Mock the command classes to prevent actual execution
@pytest.fixture(autouse=True)
def mock_commands():
    with patch('ai_whisperer.cli.ListModelsCliCommand') as MockListModelsCliCommand, \
         patch('ai_whisperer.cli.GenerateInitialPlanCliCommand') as MockGenerateInitialPlanCliCommand, \
         patch('ai_whisperer.cli.GenerateOverviewPlanCliCommand') as MockGenerateOverviewPlanCliCommand, \
         patch('ai_whisperer.cli.RefineCliCommand') as MockRefineCliCommand, \
         patch('ai_whisperer.cli.RunCliCommand') as MockRunCliCommand:
        yield {
            "ListModelsCliCommand": MockListModelsCliCommand,
            "GenerateInitialPlanCliCommand": MockGenerateInitialPlanCliCommand,
            "GenerateOverviewPlanCliCommand": MockGenerateOverviewPlanCliCommand,
            "RefineCliCommand": MockRefineCliCommand,
            "RunCliCommand": MockRunCliCommand,
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
        mock_load_config.return_value = minimal_config # Return a minimal valid config
        yield mock_load_config # Yield the mock object

# --- Test Cases for Each Command ---

def test_list_models_command_valid_args(mock_commands):
    """Test parsing valid arguments for the list-models command."""
    args = ["--config", "path/to/config.yaml", "list-models"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["ListModelsCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_csv=None,
        delegate_manager=ANY, # Expect the delegate manager
        detail_level=UserMessageLevel.INFO # Expect the default detail level
    )
    assert isinstance(commands[0], MagicMock) # Check if the mocked object is returned
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_list_models_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the list-models command with --config before the command."""
    args = ["--config", "path/to/config.yaml", "list-models"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["ListModelsCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_csv=None,
        delegate_manager=ANY, # Expect the delegate manager
        detail_level=UserMessageLevel.INFO # Expect the default detail level
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_list_models_command_with_output_csv(mock_commands):
    """Test parsing valid arguments for the list-models command with --output-csv."""
    args = ["--config", "path/to/config.yaml", "list-models", "--output-csv", "output.csv"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["ListModelsCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_csv="output.csv",
        delegate_manager=ANY, # Expect the delegate manager
        detail_level=UserMessageLevel.INFO # Expect the default detail level
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_list_models_command_missing_config(capsys_sys_exit):
    """Test list-models command with missing --config argument."""
    args = ["list-models"]
    with pytest.raises(SystemExit) as e:
        cli(args)
    assert e.type == SystemExit
    assert e.value.code != 0 # Should exit with a non-zero code on error
    captured = capsys_sys_exit.readouterr()
    assert "the following arguments are required: --config" in captured.err

def test_list_models_command_with_detail_level(mock_commands):
    """Test parsing valid arguments for the list-models command with --detail-level."""
    args = ["--config", "path/to/config.yaml", "list-models", "--detail-level", "detail"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    from monitor.user_message_delegate import UserMessageLevel # Import UserMessageLevel

    mock_commands["ListModelsCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_csv=None,
        delegate_manager=ANY,
        detail_level=UserMessageLevel.DETAIL # Assert that detail_level is passed correctly
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_generate_initial_plan_command_valid_args(mock_commands):
    """Test parsing valid arguments for the generate initial-plan command."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateInitialPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="output",
        requirements_path="reqs.md",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_generate_initial_plan_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the generate initial-plan command with --config before the command."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateInitialPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="output",
        requirements_path="reqs.md",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary


def test_generate_initial_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate-initial-plan command with --output."""
    args = ["--config", "config.yaml", "generate", "initial-plan", "reqs.md", "--output", "plans"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateInitialPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="plans",
        requirements_path="reqs.md",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

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
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateOverviewPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="output",
        initial_plan_path="initial.json",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_generate_overview_plan_command_global_config_before_command(mock_commands):
    """Test parsing valid arguments for the generate overview-plan command with --config before the command."""
    args = ["--config", "config.yaml", "generate", "overview-plan", "initial.json"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateOverviewPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="output",
        initial_plan_path="initial.json",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_generate_overview_plan_command_with_output(mock_commands):
    """Test parsing valid arguments for the generate overview-plan command with --output."""
    args = ["--config", "config.yaml", "generate", "overview-plan", "initial.json", "--output", "overview_plans"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateOverviewPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="overview_plans",
        initial_plan_path="initial.json",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

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
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 2 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["GenerateInitialPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="plans",
        requirements_path="reqs.md",
        delegate_manager=ANY
    )
    mock_commands["GenerateOverviewPlanCliCommand"].assert_called_once_with(
        config=minimal_config,
        output_dir="plans",
        initial_plan_path="<output_of_generate_initial_plan_command>",
        delegate_manager=ANY
    )
    assert all(isinstance(command, MagicMock) for command in commands) # Assert that all elements in the command list are MagicMock
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_refine_command_valid_args(mock_commands):
    """Test parsing valid arguments for the refine command."""
    args = ["--config", "config.yaml", "refine", "input.md"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["RefineCliCommand"].assert_called_once_with(
        config=minimal_config,
        input_file="input.md",
        iterations=1,
        prompt_file=None,
        output=None,
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

def test_refine_command_with_optional_args(mock_commands):
    """Test parsing valid arguments for the refine command with optional args."""
    args = ["--config", "config.yaml", "refine", "input.md", "--iterations", "5", "--prompt-file", "prompt.txt", "--output", "refined.md"]
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["RefineCliCommand"].assert_called_once_with(
        config=minimal_config,
        input_file="input.md",
        iterations=5,
        prompt_file="prompt.txt",
        output="refined.md",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

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
    commands, parsed_args = cli(args) # Unpack the tuple

    assert len(commands) == 1 # Assert the length of the command list
    from unittest.mock import ANY
    mock_commands["RunCliCommand"].assert_called_once_with(
        config=minimal_config,
        plan_file="plan.json",
        state_file="state.json",
        delegate_manager=ANY
    )
    assert isinstance(commands[0], MagicMock)
    assert isinstance(parsed_args, dict) # Assert that the second element is the parsed arguments dictionary

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
