import pytest
from unittest.mock import patch, MagicMock
import tempfile
import os
from pathlib import Path

from src.ai_whisperer.commands import GenerateOverviewPlanCommand
from src.ai_whisperer.project_plan_generator import OverviewPlanGenerator

class TestGenerateOverviewPlanCommand:

    @pytest.fixture
    def mock_config_path(self):
        return "fake_config.yaml"

    @pytest.fixture
    def mock_output_dir(self):
        return "fake_output_dir"

    @pytest.fixture
    def mock_initial_plan_path(self):
        # Create a temporary file to simulate an initial plan file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp_plan_file:
            tmp_plan_file.write('{"tasks": []}') # Write some dummy JSON content
            tmp_plan_path = tmp_plan_file.name
        yield tmp_plan_path
        os.unlink(tmp_plan_path) # Clean up the temporary file

    @pytest.fixture
    def mock_console_print(self):
        with patch.object(console, 'print') as mock_print:
            yield mock_print

    @patch('src.ai_whisperer.commands.load_config')
    @patch('src.ai_whisperer.commands.OverviewPlanGenerator')
    def test_generate_overview_plan_success(self, mock_overview_plan_generator, mock_load_config, mock_config_path, mock_output_dir, mock_initial_plan_path, mock_console_print):
        """Tests successful generation of an overview plan."""
        mock_load_config.return_value = {"mock": "config"} # Return a dummy config
        mock_overview_plan_instance = mock_overview_plan_generator.return_value
        mock_overview_plan_instance.generate_full_plan.return_value = {
            "task_plan": "fake_task_plan.json",
            "overview_plan": "fake_overview_plan.json",
            "subtasks": ["fake_subtask_1.json", "fake_subtask_2.json"]
        }

        command = GenerateOverviewPlanCommand(
            config_path=mock_config_path,
            output_dir=mock_output_dir,
            initial_plan_path=mock_initial_plan_path
        )
        exit_code = command.execute()

        mock_load_config.assert_called_once_with(mock_config_path)
        mock_overview_plan_generator.assert_called_once_with(command.config, mock_output_dir)
        mock_overview_plan_instance.generate_full_plan.assert_called_once_with(mock_initial_plan_path, mock_config_path)
        mock_console_print.assert_any_call("[green]Successfully generated project plan:[/green]")
        mock_console_print.assert_any_call("- Task plan: fake_task_plan.json")
        mock_console_print.assert_any_call("- Overview plan: fake_overview_plan.json")
        mock_console_print.assert_any_call("- Subtasks generated: 2")
        mock_console_print.assert_any_call("  1. fake_subtask_1.json")
        mock_console_print.assert_any_call("  2. fake_subtask_2.json")
        assert exit_code == 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_generate_overview_plan_actual_server(self, tmp_path):
        """Tests generating overview plan with an actual server and initial plan file."""
        # This test requires a valid configuration with actual servers defined in config.yaml.
        # It will attempt to interact with configured servers.
        # If no servers are configured or accessible, this test might fail.

        # Create a temporary initial plan file
        initial_plan_content = """
{
    "task_id": "test_task_123",
    "natural_language_goal": "Create a simple Python script.",
    "input_hashes": {
        "requirements_md": "fake_hash_req",
        "config_yaml": "fake_hash_config",
        "prompt_file": "fake_hash_prompt"
    },
    "plan": [
        {
            "subtask_id": "step_1",
            "description": "Create a Python file.",
            "depends_on": [],
            "type": "code_generation",
            "input_artifacts": [],
            "output_artifacts": ["hello_world.py"],
            "instructions": ["Write a python script that prints 'Hello, World!'"],
            "constraints": [],
            "validation_criteria": []
        }
    ]
}
"""
        initial_plan_file = tmp_path / "initial_plan.json"
        initial_plan_file.write_text(initial_plan_content)

        # Define a temporary output directory within the project's directory
        output_dir = Path("tests") / "temp_output" / tmp_path.name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use a real config file path
        config_path = "config.yaml"

        command = GenerateOverviewPlanCommand(
            config_path=config_path,
            output_dir=str(output_dir),
            initial_plan_path=initial_plan_file
        )

        # Execute the command and assert that it runs without raising an exception
        try:
            command.execute()
            assert True # Command executed without exception
        except Exception as e:
            pytest.fail(f"Command execution failed with exception: {e}")

        # Assert that output files were created in the output directory
        # The exact names of the output files might depend on the OverviewPlanGenerator implementation,
        # but we can check if files with expected patterns were created.
        output_files = list(output_dir.iterdir())
        assert any("overview" in f.name and f.suffix == ".json" for f in output_files), "Overview plan file not created."
        assert any("subtask" in f.name and f.suffix == ".json" for f in output_files), "Subtask file(s) not created."

    # Add more test cases here as needed, e.g., for error handling