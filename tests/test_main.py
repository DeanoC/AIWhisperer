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
    'prompts': {'task_generation': 'Generate task for: {md_content}'}
}

# Create a class to wrap the config dictionary and provide the openrouter_api_key attribute
class ConfigWrapper:
    def __init__(self, config_dict):
        self.config_dict = config_dict
        
    def __getitem__(self, key):
        return self.config_dict[key]
        
    def get(self, key, default=None):
        return self.config_dict.get(key, default)

# Add API key attribute
class ExConfig:
    def __init__(self):
        self.openrouter_api_key = "test-key"

class TestMain:
    """Test cases for the main.py module."""

    # Define constants to avoid repetition in tests
    REQ_FILE = 'test_requirements.md'
    CONF_FILE = 'config.yaml'
    OUT_FILE = 'output.yaml'
    WRAPPED_CONFIG = ConfigWrapper(DUMMY_CONFIG)
    DUMMY_PROCESSED_DATA = {'natural_language_goal': 'Test goal', 'tasks': [{'id': 'task1', 'description': 'Test task'}]}

    @classmethod
    def setup_class(cls):
        """Setup for TestMain."""
        sys.argv = original_argv.copy() # Restore original sys.argv before each test
        
    def setup_method(self, method):
        """Setup before each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv before each test

    def teardown_method(self, method):
        """Cleanup after each test method."""
        sys.argv = original_argv.copy() # Restore original sys.argv after each test

    @patch('sys.exit')
    @patch('src.ai_whisperer.main.setup_rich_output')
    @patch('src.ai_whisperer.main.setup_logging')
    @patch('src.ai_whisperer.main.Orchestrator')
    @patch('src.ai_whisperer.main.load_config')
    def test_main_success_flow(self, mock_load_config, mock_orchestrator_cls, mock_setup_logging, mock_setup_rich, mock_sys_exit):
        """Test the main function's happy path with all required arguments."""
        # Setup test data and mocks
        mock_load_config.return_value = self.WRAPPED_CONFIG # Return wrapped config object
        mock_console = MagicMock() # Mock Console
        mock_setup_rich.return_value = mock_console # Have setup_rich_output return our mock console
        mock_orchestrator_instance = MagicMock() # Mock Orchestrator instance
        mock_orchestrator_cls.return_value = mock_orchestrator_instance # Have Orchestrator() return our mock instance
        mock_orchestrator_instance.generate_initial_yaml.return_value = 'generated_output.yaml' # Mock the output path

        # Set command-line arguments
        sys.argv = ['main.py', '--requirements', self.REQ_FILE, '--config', self.CONF_FILE, '--output', self.OUT_FILE]
        
        # Call the function
        main()
        
        # Verify calls and sequence
        mock_setup_logging.assert_called_once() # Logging setup should be called exactly once
        mock_setup_rich.assert_called_once() # Rich console setup should be called exactly once
        mock_load_config.assert_called_once_with(self.CONF_FILE) # load_config should be called once with config file
        mock_orchestrator_cls.assert_called_once_with(self.WRAPPED_CONFIG) # Orchestrator should be instantiated with config
        mock_orchestrator_instance.generate_initial_yaml.assert_called_once_with( # generate_initial_yaml should be called
            requirements_md_path_str=self.REQ_FILE,
            config_path_str=self.CONF_FILE
        )
        mock_sys_exit.assert_not_called() # Should not exit in the normal flow
        # And finally check that the output was printed to console
        expected_print_call = call(f"[green]Successfully generated task YAML: generated_output.yaml[/green]")
        assert expected_print_call in mock_console.print.call_args_list

    @patch('sys.exit')
    def test_main_missing_requirements_arg(self, mock_sys_exit):
        """Test the main function handles missing required arguments."""
        # Set command-line args (missing --requirements)
        sys.argv = ['main.py', '--config', self.CONF_FILE, '--output', self.OUT_FILE]
        
        # Call the function
        with pytest.raises(SystemExit):
            main()
            
        # Verify it tried to exit with error code
        mock_sys_exit.assert_called_once_with(1)

    @patch('sys.exit')
    def test_main_missing_config_arg(self, mock_sys_exit):
        """Test the main function handles missing config argument."""
        # Set command-line args (missing --config)
        sys.argv = ['main.py', '--requirements', self.REQ_FILE, '--output', self.OUT_FILE]
        
        # Call the function
        with pytest.raises(SystemExit):
            main()
            
        # Verify it tried to exit with error code
        mock_sys_exit.assert_called_once_with(1)

    def test_main_missing_output_arg(self):
        """Test the main function handles missing output argument."""
        # Set command-line args (missing --output)
        sys.argv = ['main.py', '--requirements', self.REQ_FILE, '--config', self.CONF_FILE]
        
        # Call the function
        with pytest.raises(SystemExit):
            main()

    # --- Test list_models functionality ---
    @patch('sys.exit')
    @patch('src.ai_whisperer.main.setup_rich_output')
    @patch('src.ai_whisperer.main.setup_logging')
    @patch('src.ai_whisperer.main.OpenRouterAPI')
    @patch('src.ai_whisperer.main.load_config')
    def test_main_list_models_success(self, mock_load_config, mock_api_cls, mock_setup_logging, mock_setup_rich, mock_sys_exit):
        """Test successful models listing."""
        # Setup mocks
        mock_load_config.return_value = self.WRAPPED_CONFIG
        mock_console = MagicMock()
        mock_setup_rich.return_value = mock_console
        mock_api_instance = MagicMock()
        mock_api_cls.return_value = mock_api_instance
        mock_api_instance.list_models.return_value = ['model1', 'model2']
        
        # Set command-line args for list models
        sys.argv = ['main.py', '--list-models', '--config', self.CONF_FILE]
        
        # Call the function
        with pytest.raises(SystemExit) as excinfo:
            main()
        
        # Verify the right API calls were made and output generated
        mock_load_config.assert_called_once_with(self.CONF_FILE)
        mock_api_cls.assert_called_once_with(self.WRAPPED_CONFIG['openrouter'])
        mock_api_instance.list_models.assert_called_once()
        assert excinfo.value.code == 0  # Should exit with success code
        # Check that the models were printed to console
        assert any("model1" in str(call_args) for call_args in mock_console.print.call_args_list)
        assert any("model2" in str(call_args) for call_args in mock_console.print.call_args_list)

    @patch('sys.exit')
    @patch('src.ai_whisperer.main.setup_rich_output')
    @patch('src.ai_whisperer.main.setup_logging')
    @patch('src.ai_whisperer.main.OpenRouterAPI')
    @patch('src.ai_whisperer.main.load_config')
    def test_main_list_models_api_error(self, mock_load_config, mock_api_cls, mock_setup_logging, mock_setup_rich, mock_sys_exit):
        """Test list_models error handling."""
        # Setup mocks
        mock_load_config.return_value = self.WRAPPED_CONFIG
        mock_console = MagicMock()
        mock_setup_rich.return_value = mock_console
        mock_api_instance = MagicMock()
        mock_api_cls.return_value = mock_api_instance
        mock_api_instance.list_models.side_effect = Exception("API Error")
        
        # Set command-line args for list models
        sys.argv = ['main.py', '--list-models', '--config', self.CONF_FILE]
        
        # Call the function
        with pytest.raises(SystemExit) as excinfo:
            main()
        
        # Verify error handling
        mock_load_config.assert_called_once_with(self.CONF_FILE)
        mock_api_cls.assert_called_once_with(self.WRAPPED_CONFIG['openrouter'])
        mock_api_instance.list_models.assert_called_once()
        assert excinfo.value.code == 1  # Should exit with error code

    def test_main_no_list_models_flag(self):
        """Test that normal flow is followed when --list-models is not present."""
        # Use monkeypatch instead of sys.argv manipulation to avoid affecting other tests
        with patch('sys.argv', ['main.py', '--requirements', self.REQ_FILE, '--config', self.CONF_FILE, '--output', self.OUT_FILE]), \
             patch('src.ai_whisperer.main.load_config', return_value=self.WRAPPED_CONFIG), \
             patch('src.ai_whisperer.main.setup_rich_output'), \
             patch('src.ai_whisperer.main.setup_logging'), \
             patch('src.ai_whisperer.main.Orchestrator') as mock_orchestrator_cls:
                
            # Setup mock orchestrator
            mock_orchestrator_instance = MagicMock()
            mock_orchestrator_cls.return_value = mock_orchestrator_instance
            
            # Call the function
            main()
            
            # Verify the orchestrator was called (i.e., didn't take the list_models path)
            mock_orchestrator_cls.assert_called_once()
            mock_orchestrator_instance.generate_initial_yaml.assert_called_once()

def test_main_list_models_missing_config(monkeypatch, capsys):
    """Test the --list-models flag without the required --config argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', '--list-models'])

    with pytest.raises(SystemExit) as excinfo:
        main()

    # Check for error message printed to stderr
    captured = capsys.readouterr()
    assert "Error: --config argument is required when using --list-models." in captured.err
    assert excinfo.value.code == 1

def test_main_generate_subtask_missing_config(monkeypatch, capsys):
    """Test the --generate-subtask flag without the required --config argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', '--generate-subtask', '--step', 'test_step.yaml'])

    with pytest.raises(SystemExit) as excinfo:
        main()

    # Check for error message printed to stderr
    captured = capsys.readouterr()
    assert "Error: --config argument is required when using --generate-subtask." in captured.err
    assert excinfo.value.code == 1

def test_main_generate_subtask_missing_step(monkeypatch, capsys):
    """Test the --generate-subtask flag without the required --step argument."""
    # Mock sys.argv using monkeypatch
    monkeypatch.setattr('sys.argv', ['main.py', '--generate-subtask', '--config', 'config.yaml'])

    with pytest.raises(SystemExit) as excinfo:
        main()

    # Check for error message printed to stderr
    captured = capsys.readouterr()
    assert "Error: --step argument is required when using --generate-subtask." in captured.err
    assert excinfo.value.code == 1

@patch('src.ai_whisperer.main.SubtaskGenerator')
@patch('yaml.safe_load')
@patch('builtins.open', new_callable=MagicMock)
@patch('src.ai_whisperer.main.load_config')
def test_main_generate_subtask_success(mock_load_config, mock_open, mock_yaml_load,
                                      mock_generator_cls, monkeypatch):
    """Test the --generate-subtask flag with a successful outcome."""
    # Set up test data
    STEP_FILE = 'test_step.yaml'
    CONFIG_FILE = 'config.yaml'
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
    monkeypatch.setattr('sys.argv', ['main.py', '--generate-subtask', '--config', CONFIG_FILE, '--step', STEP_FILE])
    
    # Run with additional mocks
    with patch('src.ai_whisperer.main.setup_rich_output', return_value=mock_console), \
         patch('src.ai_whisperer.main.setup_logging'), \
         patch('sys.exit') as mock_exit:
         
        # Run the function
        main()
        
        # Check load_config was called with config file
        mock_load_config.assert_called_with(CONFIG_FILE)
        
        # Check open was called with step file path
        path_found = False
        for call_args in mock_open.call_args_list:
            if isinstance(call_args[0][0], Path) and str(call_args[0][0]).endswith(STEP_FILE):
                path_found = True
                break
        assert path_found, f"No call found opening Path to {STEP_FILE}"
        
        # Check yaml.safe_load was called
        mock_yaml_load.assert_called_once()
        
        # Check SubtaskGenerator initialized correctly
        mock_generator_cls.assert_called_once_with(CONFIG_FILE)
        
        # Check generate_subtask called with step data
        mock_generator_instance.generate_subtask.assert_called_once_with(STEP_DATA)
        
        # Check success message printed
        output_path_printed = False
        for call_args in mock_console.print.call_args_list:
            if len(call_args[0]) > 0 and isinstance(call_args[0][0], str) and OUTPUT_PATH in call_args[0][0]:
                output_path_printed = True
                break
        assert output_path_printed, f"Success message with {OUTPUT_PATH} not printed"
        
        # Check program exited with success code
        mock_exit.assert_called_once_with(0)
