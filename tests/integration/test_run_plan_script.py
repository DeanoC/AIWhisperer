import subprocess
import os
import sys
import pytest

import tempfile # Import tempfile

def test_run_plan_script():
    """
    Integration test to run the ai_whisperer.main module directly using the virtual environment's Python.
    Simulates the core execution flow of the run command.
    """
    # Use absolute paths from the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    overview_path = os.path.join(project_root, 'tests/code_generator/n_times_4/overview_n_times_4.json')
    overview_path = os.path.abspath(overview_path)

    # Locate the .venv Python executable
    venv_python_path = os.path.join(project_root, ".venv", "Scripts", "python.exe") # Windows default
    if not os.path.exists(venv_python_path):
        venv_python_path = os.path.join(project_root, ".venv", "bin", "python") # Linux/macOS/other default

    assert os.path.exists(venv_python_path), f"Virtual environment Python executable not found at {venv_python_path}"

    # Define the state file path within a temporary directory for this test
    with tempfile.TemporaryDirectory(prefix="test_run_plan_script_state_") as tmpdir:
        state_file_path = os.path.join(tmpdir, "state.json")

        # Build the command to run the ai_whisperer.main module
        command = [
            venv_python_path,
            "-m", "ai_whisperer.main",
            "--config", os.path.join(project_root, "tests/code_generator/aiwhisperer_config.yaml"),
            "run",
            "--plan-file", overview_path,
            "--state-file", state_file_path
        ]

        # Set working directory to project root for correct module resolution
        result = subprocess.run(command, cwd=project_root, capture_output=True, text=True)

        print('STDOUT:', result.stdout)
        print('STDERR:', result.stderr, file=sys.stderr)

        # Assert the process exited successfully
        assert result.returncode == 0, f"Script failed with exit code {result.returncode}. STDOUT: {result.stdout}, STDERR: {result.stderr}"

        # Check if the output file was created
        output_file_path = os.path.join(project_root, 'tests/code_generator/n_times_4/output/n_times_4.py')
        assert os.path.exists(output_file_path), f"Output file not found at {output_file_path}"

        # Check the content of the output file (basic check)
        # This is a bad test, as the AI might generate different code each time.
        with open(output_file_path, 'r') as f:
            output_content = f.read()
        assert "def multiply_by_4(n):" in output_content, f"Unexpected content in output file: {output_content}"
        assert "return n * 4" in output_content, f"Unexpected content in output file: {output_content}"

        # Optional: Further assertions on the state file or output if needed
        # For this test, we primarily care that the execution completes without error.
