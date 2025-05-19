import os
import shutil
import pytest
from pathlib import Path
import subprocess

PLAN_DIR = Path(__file__).parent
PLAN_JSON = PLAN_DIR / "overview_n_times_4.json"
OUTPUT_FILE = PLAN_DIR / "output" / "n_times_4.py"
RUN_SCRIPT = PLAN_DIR / "run_plan.ps1"

@pytest.fixture(autouse=True)
def clean_output():
    output_dir = PLAN_DIR / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    yield
    # Clean up after test
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_plan_passes_if_output_file_present():
    # Create the output file
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("def multiply_by_4(n):\n    return n * 4\n")
    # Run the plan using the PowerShell script
    # Construct the command to run the PowerShell script
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass", # Add Bypass execution policy for the script
        "-Command",
        str(RUN_SCRIPT),
        str(PLAN_JSON)
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    # The process should exit with zero code if validation passes
    assert result.returncode == 0, f"Expected success, got exit code {result.returncode}. Output: {result.stdout}\n{result.stderr}"
    assert "passed" in result.stdout.lower() or "success" in result.stdout.lower(), f"Expected success message. Output: {result.stdout}\n{result.stderr}"

import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the main cli function and necessary components
from ai_whisperer.cli import cli
from ai_whisperer.cli_commands import RunCliCommand
from ai_whisperer.path_management import PathManager

# New test case to simulate running the CLI with a plan file programmatically
def test_cli_run_command_programmatic(clean_output):
    """
    Tests running the CLI with a plan file programmatically, simulating the PowerShell script execution.
    This test allows for direct Python debugging of the CLI execution flow.
    """
    # Use the temporary directory created by the clean_output fixture
    tmpdir = str(PLAN_DIR / "output")

    config_path = PLAN_DIR.parent / "aiwhisperer_config.yaml" # Correct path to config file
    plan_path = PLAN_DIR / "overview_n_times_4.json"
    state_path = Path(tmpdir) / "state.json"

    # Ensure the config and plan files exist (they should be in the test directory)
    assert config_path.exists()
    assert plan_path.exists()

    # Mock the OpenRouterAIService call within the ExecutionEngine
    # This is necessary because we are not mocking the RunCliCommand or ExecutionEngine
    # We need to mock the actual AI service interaction.
    # Create a mock DelegateManager
    mock_delegate_manager = MagicMock()

    def control_side_effect(sender, control_type, *args, **kwargs):
        if control_type == "engine_request_pause":
            return False
        return False  # or handle other controls as needed

    mock_delegate_manager.invoke_control.side_effect = control_side_effect

    with patch('ai_whisperer.ai_service.openrouter_ai_service.OpenRouterAIService.call_chat_completion') as mock_call_chat_completion:
        # Use side_effect to simulate a tool call on the first call, and a final content message on the second call
        tool_call_response = {
            "message": {
                "tool_calls": [
                    {
                        "id": "call_abc",
                        "function": {
                            "name": "write_to_file",
                            "arguments": '{"path": "output/n_times_4.py", "content": "def n_times_4(x):\\n    return x * 4\\n", "line_count": 2}'
                        }
                    }
                ]
            },
            "finish_reason": "tool_calls"
        }
        final_content_response = {
            "message": {
                "content": "Code generation complete."
            },
            "finish_reason": "stop"
        }
        mock_call_chat_completion.side_effect = [tool_call_response, final_content_response]

        # Mock the tool execution itself
        with patch('ai_whisperer.tools.tool_registry.ToolRegistry.get_tool_by_name') as mock_get_tool_by_name:
            mock_write_tool = MagicMock()
            def write_to_file_side_effect(path, content, line_count=None):
                # Actually create the file in the test's output directory so validation passes
                # If the path is relative, resolve it relative to the test's output dir
                output_dir = Path(tmpdir)
                output_path = Path(path)
                if not output_path.is_absolute():
                    # Mimic the validator's logic: if the first part matches output dir name, strip it
                    input_parts = output_path.parts
                    output_dir_name = output_dir.name
                    if input_parts and input_parts[0] == output_dir_name:
                        output_path = Path(*input_parts[1:])
                    output_path = output_dir / output_path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(content)
                return {"success": True, "message": "File written successfully."}
            mock_write_tool.execute.side_effect = write_to_file_side_effect
            mock_get_tool_by_name.return_value = mock_write_tool

            # Mock PathManager.get_instance().initialize to prevent re-initialization issues
            with patch('ai_whisperer.path_management.PathManager.get_instance') as mock_get_path_manager_instance:
                mock_path_manager_instance = MagicMock(spec=PathManager)
                # Configure the mock PathManager to return expected paths
                mock_path_manager_instance.project_path = str(PLAN_DIR.parent.parent) # Assuming project root is two levels up
                mock_path_manager_instance.output_path = str(Path(tmpdir).resolve())
                mock_path_manager_instance.workspace_path = str(Path(".").resolve()) # Assuming workspace is current dir for test
                mock_path_manager_instance.is_path_within_workspace.side_effect = lambda p: Path(p).resolve().is_relative_to(Path(".").resolve())
                mock_path_manager_instance.is_path_within_output.side_effect = lambda p: Path(p).resolve().is_relative_to(Path(tmpdir).resolve())
                mock_get_path_manager_instance.return_value = mock_path_manager_instance

                # Call the cli function with the run command arguments
                # We need to pass the arguments as a list of strings, similar to sys.argv
                args = [
                    "--config", str(config_path),
                    "run",
                    "--plan-file", str(plan_path),
                    "--state-file", str(state_path)
                ]

                commands, parsed_args = cli(args, delegate_manager=mock_delegate_manager)

                # The cli function should return a list containing one RunCliCommand instance
                assert len(commands) == 1
                run_command = commands[0]
                assert isinstance(run_command, RunCliCommand) # Check if it's a real RunCliCommand instance

                # Explicitly execute the command
                run_command.execute()

                # Now check the state file to see if the plan completed successfully
                assert state_path.exists()
                with open(state_path, 'r') as f:
                    state_data = json.load(f)

                # Assert that the task in the plan is marked as completed
                assert "tasks" in state_data
                # Get the actual subtask ID from the loaded plan data
                with open(plan_path, 'r') as f:
                    plan_data = json.load(f)
                subtask_id = plan_data["plan"][0]["subtask_id"]


                assert subtask_id in state_data["tasks"], f"Subtask ID {subtask_id} not in state: {state_data['tasks']}"
                print("DEBUG: Task state:", state_data["tasks"][subtask_id])
                assert state_data["tasks"][subtask_id]["status"] == "completed", f"Task state: {state_data['tasks'][subtask_id]}"

                # Assert that the output file was created (mocked by mock_write_tool)
                # We check if the mock tool's execute method was called with the correct arguments.
                mock_write_tool.execute.assert_called_once_with(path="output/n_times_4.py", content='def n_times_4(x):\n    return x * 4\n', line_count=2)

# Ensure necessary imports are present
from ai_whisperer.cli import cli
from ai_whisperer.cli_commands import RunCliCommand
from ai_whisperer.path_management import PathManager
from unittest.mock import patch, MagicMock
import tempfile
import os
import json
from pathlib import Path
import subprocess
import shutil

# Re-define fixtures and existing test if needed, or ensure they are imported/accessible
# Assuming the existing fixtures and test are defined above this new test case

# Ensure the existing test still works with the new imports
# (No changes needed to the existing test function itself)

# Re-define constants if necessary (or ensure they are at the top of the file)
# PLAN_DIR, PLAN_JSON, OUTPUT_FILE, RUN_SCRIPT

# Re-define clean_output fixture if necessary
# @pytest.fixture(autouse=True)
# def clean_output():
#     ...