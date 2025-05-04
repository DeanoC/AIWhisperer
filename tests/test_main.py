import pytest
from unittest.mock import patch, MagicMock, call
import sys

# We need to manipulate sys.argv, so store the original
original_argv = sys.argv.copy()

# Import the actual function
from src.ai_whisperer.main import main

# Define dummy data for mocking
# Define dummy data for mocking
DUMMY_CONFIG = {
    'openrouter': {'api_key': 'test-key', 'model': 'test-model', 'params': {'temperature': 0.5}},
    'prompts': {'task_generation': 'Generate task for: {md_content}'}
}

# Create a class to wrap the config dictionary and provide the openrouter_api_key attribute
class ConfigWrapper:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        self.openrouter_api_key = config_dict['openrouter']['api_key']
    
    def __getitem__(self, key):
        return self.config_dict[key]
    
    def get(self, key, default=None):
        return self.config_dict.get(key, default)

# Create a wrapped config for tests that need the openrouter_api_key attribute
WRAPPED_CONFIG = ConfigWrapper(DUMMY_CONFIG)
DUMMY_MD_CONTENT = "# Test Markdown"
DUMMY_FORMATTED_PROMPT = "Generate task for: # Test Markdown"
DUMMY_API_RESPONSE = "task: Test Task\ndescription: Details"
DUMMY_PROCESSED_DATA = {'task': 'Test Task', 'description': 'Details'}
REQ_FILE = 'input.md'
CONF_FILE = 'config.yaml'
OUT_FILE = 'output.yaml'

@pytest.fixture(autouse=True)
def reset_sys_argv():
    """Reset sys.argv before each test."""
    sys.argv = original_argv.copy()
    yield
    sys.argv = original_argv # Ensure cleanup even if test fails

@pytest.fixture
def mock_dependencies():
    """Mock core functions used by main."""
    with patch('src.ai_whisperer.main.setup_logging') as mock_setup_logging, \
         patch('src.ai_whisperer.main.setup_rich_output') as mock_setup_rich, \
         patch('src.ai_whisperer.main.Console') as mock_console_cls, \
         patch('src.ai_whisperer.main.Orchestrator') as mock_orchestrator_cls: # Mock the Orchestrator class

        # If setup_rich_output returns a console instance, mock that instance
        mock_console_instance = MagicMock()
        mock_setup_rich.return_value = mock_console_instance

        # Mock the instance of Orchestrator and its methods
        mock_orchestrator_instance = MagicMock()
        mock_orchestrator_cls.return_value = mock_orchestrator_instance
        mock_orchestrator_instance.generate_initial_yaml.return_value = OUT_FILE # Mock return value

        mocks = {
            'setup_logging': mock_setup_logging,
            'setup_rich_output': mock_setup_rich,
            'console': mock_console_instance, # Provide the mocked console instance
            'orchestrator_cls': mock_orchestrator_cls, # Provide the mocked Orchestrator class
            'orchestrator_instance': mock_orchestrator_instance # Provide the mocked Orchestrator instance
        }
        yield mocks

@patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG)
def test_main_success_flow(mock_load_config, mock_dependencies):
    """Test the successful execution flow with required arguments."""
    sys.argv = [
        'ai-whisperer', # Script name (or however it's invoked)
        '--requirements', REQ_FILE,
        '--config', CONF_FILE,
        '--output', OUT_FILE
    ]

    main()

    # Verify mocks were called correctly
    mock_dependencies['setup_logging'].assert_called_once()
    mock_dependencies['setup_rich_output'].assert_called_once()
    mock_load_config.assert_called_once_with(CONF_FILE) # load_config is now mocked individually in relevant tests
    mock_dependencies['orchestrator_cls'].assert_called_once_with(WRAPPED_CONFIG) # Assert Orchestrator is instantiated with config
    mock_dependencies['orchestrator_instance'].generate_initial_yaml.assert_called_once_with( # Assert generate_initial_yaml is called
        requirements_md_path_str=REQ_FILE,
        config_path_str=CONF_FILE
    )
    # The following mocks are now called within the Orchestrator, so we don't assert them here
    # mock_dependencies['read_markdown'].assert_called_once_with(REQ_FILE)
    # mock_dependencies['format_prompt'].assert_called_once_with(...)
    # mock_dependencies['call_openrouter'].assert_called_once_with(...)
    # mock_dependencies['process_response'].assert_called_once_with(...)
    # mock_dependencies['save_yaml'].assert_called_once_with(DUMMY_PROCESSED_DATA, OUT_FILE) # save_yaml is called by orchestrator

    mock_dependencies['console'].print.assert_any_call(f"[green]Successfully generated task YAML: {OUT_FILE}[/green]")

@patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG)
def test_main_missing_requirements_arg(mock_load_config, mock_dependencies, capsys):
    """Test running main without the --requirements argument."""
    sys.argv = [
        'ai-whisperer',
        '--config', CONF_FILE,
        '--output', OUT_FILE
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1 # Expecting exit code 1 for manual error
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "Error: --requirements, --config, and --output are required for the main operation." in captured.err
    # load_config should not be called if args are missing

@patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG)
def test_main_missing_config_arg(mock_load_config, mock_dependencies, capsys):
    """Test running main without the --config argument."""
    sys.argv = [
        'ai-whisperer',
        '--requirements', REQ_FILE,
        '--output', OUT_FILE
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "Error: --requirements, --config, and --output are required for the main operation." in captured.err
    # load_config should not be called if args are missing

@patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG)
def test_main_missing_output_arg(mock_load_config, mock_dependencies, capsys):
    """Test running main without the --output argument."""
    sys.argv = [
        'ai-whisperer',
        '--requirements', REQ_FILE,
        '--config', CONF_FILE,
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "Error: --requirements, --config, and --output are required for the main operation." in captured.err
    # load_config should not be called if args are missing

# Add tests for error handling (e.g., if load_config raises ConfigError)
# These require the actual main function to exist and handle exceptions.
# We'll add them after the initial implementation.

# Example of an error handling test (to be enabled later)
# def test_main_handles_config_error(mock_dependencies):
#     """Test that main handles ConfigError gracefully."""
#     from src.ai_whisperer.exceptions import ConfigError
#     mock_dependencies['load_config'].side_effect = ConfigError("File not found")
#     sys.argv = ['ai-whisperer', '--requirements', REQ_FILE, '--config', 'bad.yaml', '--output', OUT_FILE]
#
#     with pytest.raises(SystemExit) as excinfo:
#          main()
#     assert excinfo.value.code != 0 # Should exit with error code
#     # Check that the error was printed using the rich console
#     mock_dependencies['console'].print.assert_any_call("[bold red]Error:[/bold red] Configuration error: File not found")

@patch('sys.exit')
@patch('builtins.print')
@patch('src.ai_whisperer.main.OpenRouterAPI')
def test_main_list_models_success(mock_openrouter_api, mock_print, mock_sys_exit, monkeypatch, mock_dependencies):
    """Test the --list-models flag for successful API call."""
    # Mock sys.argv using monkeypatch for better isolation
    # Include required arguments to prevent argparse from exiting early
    monkeypatch.setattr('sys.argv', ['main.py', '--list-models', '--config', 'dummy_config.yaml',
                                     '--requirements', REQ_FILE, '--output', OUT_FILE])
    
    mock_instance = MagicMock()
    mock_openrouter_api.return_value = mock_instance
    mock_instance.list_models.return_value = ['model-a', 'model-b']

    # Mock load_config specifically for this test
    with patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG) as mock_load_config:
        main()

    # In the --list-models flow, load_config is called in both the list-models block and the main try block
    # So we check that it was called with the expected argument, but don't assert the exact number of calls
    mock_load_config.assert_has_calls([call('dummy_config.yaml')])
    mock_openrouter_api.assert_called_once()
    mock_instance.list_models.assert_called_once()
    # The messages are printed using console.print, not the built-in print function
    mock_dependencies['console'].print.assert_any_call("[bold green]Available OpenRouter Models:[/bold green]")
    mock_dependencies['console'].print.assert_any_call("- model-a")
    mock_dependencies['console'].print.assert_any_call("- model-b")
    mock_sys_exit.assert_called_once_with(0)

@patch('sys.exit')
@patch('builtins.print')
@patch('src.ai_whisperer.main.OpenRouterAPI')
def test_main_list_models_api_error(mock_openrouter_api, mock_print, mock_sys_exit, capsys, monkeypatch, mock_dependencies):
    """Test the --list-models flag when the API call fails."""
    from src.ai_whisperer.exceptions import OpenRouterAPIError
    # Mock sys.argv using monkeypatch for better isolation
    # Include required arguments to prevent argparse from exiting early
    monkeypatch.setattr('sys.argv', ['main.py', '--list-models', '--config', 'dummy_config.yaml',
                                     '--requirements', REQ_FILE, '--output', OUT_FILE])

    mock_instance = MagicMock()
    mock_openrouter_api.return_value = mock_instance
    mock_instance.list_models.side_effect = OpenRouterAPIError("API Failed")

    # Mock load_config specifically for this test
    with patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG) as mock_load_config:
        main()

    # In the --list-models flow, load_config is called in both the list-models block and the main try block
    # So we check that it was called with the expected argument, but don't assert the exact number of calls
    mock_load_config.assert_has_calls([call('dummy_config.yaml')])
    mock_openrouter_api.assert_called_once()
    mock_instance.list_models.assert_called_once()
    # The error message is printed using print, but we're mocking sys.exit, so we need to check mock_print
    mock_print.assert_any_call("Error fetching models: API Failed", file=sys.stderr)
    mock_sys_exit.assert_called_once_with(1)

@patch('sys.exit')
@patch('builtins.print')
@patch('src.ai_whisperer.main.OpenRouterAPI')
@patch('src.ai_whisperer.main.load_config', return_value=WRAPPED_CONFIG)
def test_main_no_list_models_flag(mock_load_config, mock_openrouter_api, mock_print, mock_sys_exit, mock_dependencies):
    """Test that list_models is not called when --list-models is not used."""
    sys.argv = [
        'ai-whisperer', # Script name (or however it's invoked)
        '--requirements', REQ_FILE,
        '--config', CONF_FILE,
        '--output', OUT_FILE
    ]

    main()

    mock_openrouter_api.assert_not_called()
    mock_load_config.assert_called_once_with(CONF_FILE) # load_config should be called in the normal flow
    # Assert that the normal flow functions were called (using the existing mock_dependencies)
    mock_dependencies['orchestrator_cls'].assert_called_once_with(WRAPPED_CONFIG) # Assert Orchestrator is instantiated with config
    mock_dependencies['orchestrator_instance'].generate_initial_yaml.assert_called_once_with( # Assert generate_initial_yaml is called
        requirements_md_path_str=REQ_FILE,
        config_path_str=CONF_FILE
    )
    # mock_dependencies['read_markdown'].assert_called_once_with(REQ_FILE) # Removed as read_markdown is now in Orchestrator
    # mock_dependencies['save_yaml'].assert_called_once_with(DUMMY_PROCESSED_DATA, OUT_FILE) # save_yaml is called by orchestrator
    mock_sys_exit.assert_not_called() # Should not exit here in the normal flow



import pytest # Ensure pytest is imported

def test_main_list_models_missing_config(monkeypatch, capsys): # Removed mock_print and patch
    """Test the --list-models flag without the required --config argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', '--list-models'])

    with pytest.raises(SystemExit) as excinfo:
        main()

    # Check for error message printed to stderr
    captured = capsys.readouterr()
    assert "Error: --config argument is required when using --list-models." in captured.err
    assert excinfo.value.code == 1 # Check exit code
