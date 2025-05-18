from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os

from ai_whisperer.cli_commands import GenerateInitialPlanCliCommand
from ai_whisperer.initial_plan_generator import InitialPlanGenerator
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.config import load_config

@pytest.fixture
def initialize_path_manager(tmp_path):
    """Fixture to initialize the PathManager singleton with a temporary path and prompt path."""
    from ai_whisperer.path_management import PathManager # Import PathManager
    PathManager.get_instance().initialize(config_values={'project_path': str(tmp_path), 'prompt_path': str(tmp_path)})

@pytest.fixture
def reset_path_manager():
    """Fixture to reset the PathManager singleton after each test."""
    from ai_whisperer.path_management import PathManager # Import PathManager
    yield
    PathManager._reset_instance()

class TestGenerateInitialPlanCliCommand:

    @pytest.fixture
    def mock_config_path(self):
        return "fake_config.yaml"

    @pytest.fixture
    def mock_output_dir(self):
        return "fake_output_dir"

    @patch('ai_whisperer.cli_commands.InitialPlanGenerator')
    def test_generate_initial_plan_success(self, mock_initial_plan_generator, mock_config_path, mock_output_dir):
        """Tests successful generation of an initial plan."""
        mock_initial_plan_instance = mock_initial_plan_generator.return_value
        mock_initial_plan_instance.generate_plan.return_value = "fake_plan_path.json"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as tmp_req_file:
            tmp_req_file.write("This is a test requirement.")
            tmp_req_path = tmp_req_file.name

        # Simulate config dict as would be passed by CLI
        config = {"mock": "config", "config_path": mock_config_path}
        command = GenerateInitialPlanCliCommand(
            config=config,
            output_dir=mock_output_dir,
            requirements_path=tmp_req_path,
            delegate_manager=DelegateManager()
        )
        exit_code = command.execute()

        # The real InitialPlanGenerator is called with (config, delegate_manager, output_dir)
        mock_initial_plan_generator.assert_called_once_with(command.config, command.delegate_manager, mock_output_dir)
        mock_initial_plan_instance.generate_plan.assert_called_once_with(tmp_req_path, mock_config_path)
        assert exit_code == 0

        os.unlink(tmp_req_path) # Clean up the temporary file

    @patch('ai_whisperer.cli_commands.InitialPlanGenerator')
    def test_generate_initial_plan_no_requirements_path(self, mock_initial_plan_generator, mock_config_path, mock_output_dir):
        """Tests generating initial plan without requirements path."""
        config = {"mock": "config", "config_path": mock_config_path}
        command = GenerateInitialPlanCliCommand(
            config=config,
            output_dir=mock_output_dir,
            requirements_path=None, # Explicitly set to None
            delegate_manager=DelegateManager()
        )
        with pytest.raises(ValueError, match="Requirements path is required for initial plan generation."):
            command.execute()
        mock_initial_plan_generator.assert_not_called() # InitialPlanGenerator should not be called

    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_initial_plan_actual_server(self, tmp_path, initialize_path_manager, reset_path_manager):
        """Tests generating initial plan with an actual server and requirements file."""
        # This test requires a valid configuration with actual servers defined in config.yaml.
        # It will attempt to interact with configured servers.
        # If no servers are configured or accessible, this test might fail.


        # Create a temporary requirements file
        requirements_content = "Generate a simple 'Hello World' Python script."
        requirements_file = tmp_path / "requirements.md"
        requirements_file.write_text(requirements_content)

        # Define a temporary output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Use a real config file path
        config_path = "config.yaml"
        config = load_config(config_path)
        config["config_path"] = config_path

        command = GenerateInitialPlanCliCommand(
            config=config,
            output_dir=str(output_dir),
            requirements_path=str(requirements_file),
            delegate_manager=DelegateManager()
        )

        # Execute the command and assert that it runs without raising an exception
        try:
            command.execute()
            assert True # Command executed without exception
        except Exception as e:
            pytest.fail(f"Command execution failed with exception: {e}")

        # Assert that an output file was created in the output directory
        output_files = list(output_dir.iterdir())
        assert len(output_files) > 0, "No output file was created."