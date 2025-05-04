 import pytest
from unittest.mock import patch, MagicMock
import sys

# We need to manipulate sys.argv, so store the original
original_argv = sys.argv.copy()

# Import the actual function
from src.ai_whisperer.main import main

# Define dummy data for mocking
DUMMY_CONFIG = {
    'openrouter': {'api_key': 'test-key', 'model': 'test-model', 'params': {'temperature': 0.5}},
    'prompts': {'task_generation': 'Generate task for: {md_content}'}
}
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
    """Mock all core functions used by main."""
    with patch('src.ai_whisperer.main.load_config', return_value=DUMMY_CONFIG) as mock_load, \
         patch('src.ai_whisperer.main.read_markdown', return_value=DUMMY_MD_CONTENT) as mock_read, \
         patch('src.ai_whisperer.main.format_prompt', return_value=DUMMY_FORMATTED_PROMPT) as mock_format, \
         patch('src.ai_whisperer.main.call_openrouter', return_value=DUMMY_API_RESPONSE) as mock_call, \
         patch('src.ai_whisperer.main.process_response', return_value=DUMMY_PROCESSED_DATA) as mock_process, \
         patch('src.ai_whisperer.main.save_yaml') as mock_save, \
         patch('src.ai_whisperer.main.setup_logging') as mock_setup_logging, \
         patch('src.ai_whisperer.main.setup_rich_output') as mock_setup_rich, \
         patch('src.ai_whisperer.main.Console') as mock_console_cls: # Mock the Console class itself if needed

        # If setup_rich_output returns a console instance, mock that instance
        mock_console_instance = MagicMock()
        mock_setup_rich.return_value = mock_console_instance

        mocks = {
            'load_config': mock_load,
            'read_markdown': mock_read,
            'format_prompt': mock_format,
            'call_openrouter': mock_call,
            'process_response': mock_process,
            'save_yaml': mock_save,
            'setup_logging': mock_setup_logging,
            'setup_rich_output': mock_setup_rich,
            'console': mock_console_instance # Provide the mocked console instance
        }
        yield mocks

def test_main_success_flow(mock_dependencies):
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
    mock_dependencies['load_config'].assert_called_once_with(CONF_FILE)
    mock_dependencies['read_markdown'].assert_called_once_with(REQ_FILE)
    mock_dependencies['format_prompt'].assert_called_once_with(
        DUMMY_CONFIG['prompts']['task_generation'],
        DUMMY_MD_CONTENT,
        DUMMY_CONFIG['openrouter'] # Pass the openrouter sub-dict as config_vars
    )
    mock_dependencies['call_openrouter'].assert_called_once_with(
        DUMMY_CONFIG['openrouter']['api_key'],
        DUMMY_CONFIG['openrouter']['model'],
        DUMMY_FORMATTED_PROMPT,
        DUMMY_CONFIG['openrouter']['params']
    )
    mock_dependencies['process_response'].assert_called_once_with(DUMMY_API_RESPONSE)
    mock_dependencies['save_yaml'].assert_called_once_with(DUMMY_PROCESSED_DATA, OUT_FILE)
    mock_dependencies['console'].print.assert_any_call(f"[green]Successfully generated task YAML: {OUT_FILE}[/green]")

def test_main_missing_requirements_arg(mock_dependencies, capsys):
    """Test running main without the --requirements argument."""
    sys.argv = [
        'ai-whisperer',
        '--config', CONF_FILE,
        '--output', OUT_FILE
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0 # Expecting non-zero exit code for error
    # ArgumentParser should print usage to stderr
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "required: --requirements" in captured.err

def test_main_missing_config_arg(mock_dependencies, capsys):
    """Test running main without the --config argument."""
    sys.argv = [
        'ai-whisperer',
        '--requirements', REQ_FILE,
        '--output', OUT_FILE
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "required: --config" in captured.err

def test_main_missing_output_arg(mock_dependencies, capsys):
    """Test running main without the --output argument."""
    sys.argv = [
        'ai-whisperer',
        '--requirements', REQ_FILE,
        '--config', CONF_FILE,
    ]
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0
    captured = capsys.readouterr()
    assert "usage: ai-whisperer" in captured.err
    assert "required: --output" in captured.err

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

