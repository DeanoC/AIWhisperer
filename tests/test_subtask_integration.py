import pytest
from unittest.mock import patch, MagicMock, call
import sys
from pathlib import Path

# We need to manipulate sys.argv, so store the original
original_argv = sys.argv.copy()

# Import the actual function
from src.ai_whisperer.main import main

# Define dummy data for mocking
DUMMY_CONFIG = {
    'openrouter': {'api_key': 'test-key', 'model': 'test-model', 'params': {'temperature': 0.5}},
    'prompts': {'task_generation': 'Generate task for: {md_content}',
                'subtask_generator_prompt_content': 'Generate subtask for: {{ step_description }}'}
}

# Constants for testing
STEP_FILE = 'test_step.yaml'
CONFIG_FILE = 'config.yaml'
REQ_FILE = 'test_requirements.md'
OUT_FILE = 'output.yaml'

# Test for --list-models flag without config
def test_main_list_models_missing_config(monkeypatch, capsys):
    """Test the --list-models flag without the required --config argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', 'list-models'])

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            main()

    # Check for error message printed to stderr
    captured = capsys.readouterr()
    assert "required: --config" in captured.err

# Test for --generate-subtask flag without config
def test_main_generate_subtask_missing_config(monkeypatch, capsys):
    """Test the --generate-subtask flag without the required --config argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', 'generate', '--generate-subtask', '--step', 'test_step.yaml'])

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            main()

    # Check for error message printed to stderr, matching argparse output
    captured = capsys.readouterr()
    assert "--config" in captured.err and "required" in captured.err

# Test for --generate-subtask flag without step
def test_main_generate_subtask_missing_step(monkeypatch, capsys):
    """Test the --generate-subtask flag without the required --step argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', 'generate', '--generate-subtask', '--config', CONFIG_FILE])

    with pytest.raises(SystemExit) as excinfo:
        with patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            main()

    # Check for error message printed to stderr, matching argparse output
    captured = capsys.readouterr()
    assert "--step" in captured.err and "required" in captured.err

# Test successful subtask generation
@patch('src.ai_whisperer.main.SubtaskGenerator')
@patch('yaml.safe_load')
@patch('builtins.open', new_callable=MagicMock)
@patch('src.ai_whisperer.main.load_config')
def test_main_generate_subtask_success(mock_load_config, mock_open, mock_yaml_load,
                                      mock_generator_cls, monkeypatch):
    """Test the --generate-subtask flag with a successful outcome."""
    # Set up test data
    STEP_DATA = {
        'step_id': 'test_step_1',
        'description': 'Test step'
    }
    OUTPUT_PATH = 'output/test_step_1_subtask.yaml'
    
    # Set up mocks
    mock_load_config.return_value = DUMMY_CONFIG
    mock_yaml_load.return_value = STEP_DATA
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    mock_generator_instance = MagicMock()
    mock_generator_cls.return_value = mock_generator_instance
    mock_generator_instance.generate_subtask.return_value = OUTPUT_PATH
    mock_console = MagicMock()
    
    # Mock command line arguments
    monkeypatch.setattr('sys.argv', ['main.py', 'generate', '--generate-subtask', '--config', CONFIG_FILE, '--step', STEP_FILE])
    
    # Run with additional mocks
    with patch('src.ai_whisperer.main.setup_rich_output', return_value=mock_console), \
         patch('src.ai_whisperer.main.setup_logging'), \
         patch('src.ai_whisperer.main.Orchestrator'), \
         patch('sys.exit'):

        # Call the function - we're only interested in what gets called, 
        # not whether it exits properly in this test
        try:
            main()
        except SystemExit:
            pass
        
        # Check if our specific task was called
        # Expect the second argument 'output' based on the actual call
        mock_generator_cls.assert_called_once_with(CONFIG_FILE, 'output')

        # Check if the subtask was generated
        
        mock_generator_instance.generate_subtask.assert_called_once_with(STEP_DATA)
        
        # Check if success message was printed
        success_call_found = False
        for call_args in mock_console.print.call_args_list:
            if len(call_args[0]) > 0 and isinstance(call_args[0][0], str) and OUTPUT_PATH in call_args[0][0]:
                success_call_found = True
                break
        assert success_call_found, "Success message with output path not printed"
