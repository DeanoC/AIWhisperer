import pytest
import asyncio
import os
import platform

from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool

# Helper to get a simple, non-destructive command based on OS
def get_simple_success_command():
    if platform.system() == "Windows":
        return "echo Hello World" # 'dir' can be verbose, 'echo' is simpler
    else:
        return "echo Hello World"

def get_simple_error_command():
    # This command should ideally produce a non-zero return code and possibly stderr
    if platform.system() == "Windows":
        return "dir __non_existent_file_or_directory__" # This will write to stderr
    else:
        return "ls __non_existent_file_or_directory__"


@pytest.fixture
def tool():
    return ExecuteCommandTool()

def test_execute_command_tool_name(tool):
    assert tool.name == "execute_command"

def test_execute_command_tool_description(tool):
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0
    assert "Executes a CLI command" in tool.description

def test_execute_command_tool_parameters_schema(tool):
    schema = tool.parameters_schema
    assert isinstance(schema, dict)
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'command' in schema['properties']
    assert schema['properties']['command']['type'] == 'string'
    assert 'cwd' in schema['properties']
    assert schema['properties']['cwd']['type'] == 'string'
    assert 'required' in schema
    assert 'command' in schema['required']

def test_execute_command_tool_category(tool):
    assert tool.category == "System"

def test_execute_command_tool_tags(tool):
    assert isinstance(tool.tags, list)
    assert "cli" in tool.tags
    assert "system" in tool.tags

def test_execute_command_tool_ai_prompt_instructions(tool):
    instructions = tool.get_ai_prompt_instructions()
    assert isinstance(instructions, str)
    assert "execute_command" in instructions
    assert "command (string, required)" in instructions
    assert "cwd (string, optional)" in instructions
    assert "stdout" in instructions
    assert "stderr" in instructions
    assert "returncode" in instructions

def test_execute_success_simple(tool):
    """Tests successful execution of a simple command."""
    command_to_run = get_simple_success_command()
    result = tool.execute(command=command_to_run)

    assert isinstance(result, dict)
    assert "stdout" in result
    assert "stderr" in result
    assert "returncode" in result
    assert result["returncode"] == 0
    assert "Hello World" in result["stdout"] 
    # stderr might be empty or contain minor warnings depending on shell, so not strictly checking its content for success
    # For echo, stderr should be empty on most systems
    if platform.system() == "Windows":
         # Windows echo might add extra newline
        assert result["stdout"].strip() == "Hello World"
    else:
        assert result["stdout"] == "Hello World\n"
    assert result["stderr"] == ""


def test_execute_success_with_cwd(tool, tmp_path):
    """Tests successful command execution with a specified cwd."""
    # tmp_path is a pytest fixture providing a temporary directory path (pathlib.Path object)
    test_file_name = "test_in_cwd.txt"
    
    # Command to create a file in the current directory
    if platform.system() == "Windows":
        command_to_run = f"echo test_content > {test_file_name}"
    else:
        command_to_run = f"echo test_content > {test_file_name}"

    result = tool.execute(command=command_to_run, cwd=str(tmp_path))

    assert result["returncode"] == 0
    assert os.path.exists(tmp_path / test_file_name)
    with open(tmp_path / test_file_name, "r") as f:
        content = f.read()
        if platform.system() == "Windows":
            assert "test_content" in content.strip() # Windows echo might add extra newline
        else:
            assert "test_content" in content


def test_execute_command_not_found(tool):
    """Tests execution of a non-existent command."""
    non_existent_command = "my_super_non_existent_command_12345"
    result = tool.execute(command=non_existent_command)

    assert isinstance(result, dict)
    assert "stdout" in result
    assert "stderr" in result
    assert "returncode" in result
    assert result["returncode"] != 0 # Should be non-zero
    # Specific error message for command not found can vary by OS/shell
    # The tool's own FileNotFoundError handling should catch this
    assert "Error: Command not found" in result["stderr"] or "is not recognized" in result["stderr"] or "No such file or directory" in result["stderr"]


def test_execute_command_produces_stderr_and_nonzero_return(tool):
    """Tests a command that is expected to produce stderr and a non-zero return code."""
    command_to_run = get_simple_error_command()
    result = tool.execute(command=command_to_run)
    
    assert isinstance(result, dict)
    assert "stdout" in result
    assert "stderr" in result
    assert "returncode" in result
    assert result["returncode"] != 0
    assert len(result["stderr"]) > 0 # Expect some error message
    if platform.system() == "Windows":
        assert "file not found" in result["stderr"].lower()
    else:
        assert "No such file or directory" in result["stderr"]

def test_execute_empty_command(tool):
    """Tests execution of an empty command string."""
    # Behavior of empty command can vary. Some shells might do nothing, others error.
    # The tool should handle it gracefully. subprocess.run with shell=True might just return 0.
    result = tool.execute(command="")
    
    assert isinstance(result, dict)
    # Depending on the shell, an empty command might be a no-op (return 0) or an error.
    # We are mostly checking that the tool doesn't crash.
    # If it's a no-op, stdout/stderr would be empty.
    # If it's an error, stderr would have content.
    assert "returncode" in result
    # if result["returncode"] == 0:
    #     assert result["stdout"] == ""
    #     assert result["stderr"] == ""
    # else:
    #     assert len(result["stderr"]) > 0
    # For now, just ensure it runs and returns the dict structure
    assert "stdout" in result
    assert "stderr" in result

# It's hard to reliably test the generic "Exception as e" block without
# more intricate mocking of subprocess.run itself to raise specific other errors.
# The FileNotFoundError is the most common and testable external issue.