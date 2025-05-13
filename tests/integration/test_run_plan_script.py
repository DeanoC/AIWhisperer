import subprocess
import os
import sys
import pytest

def test_run_plan_script():
    """
    Integration test to run the run_plan.ps1 PowerShell script with -Clean, -y, and overview_n_times_4.json as arguments.
    Equivalent to the VSCode launch configuration, but omits -DebugPython.
    """
    # Use absolute paths from the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    script_path = os.path.join(project_root, 'tests/code_generator/n_times_4/run_plan.ps1')
    overview_path = os.path.join(project_root, 'tests/code_generator/n_times_4/overview_n_times_4.json')
    script_path = os.path.abspath(script_path)
    overview_path = os.path.abspath(overview_path)
    
    # Build the command
    command = [
        'powershell',
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-Command', f". '{script_path}' -Clean -y '{overview_path}'"
    ]
    
    # Set working directory to workspace root
    # Run from the project root
    result = subprocess.run(command, cwd=project_root, capture_output=True, text=True)
    print('STDOUT:', result.stdout)
    print('STDERR:', result.stderr, file=sys.stderr)
    assert result.returncode == 0, f"Script failed with exit code {result.returncode}"
