import pathlib
from ai_whisperer.exceptions import FileRestrictionError
import pytest
from ai_whisperer.path_management import PathManager

import pytest
import os
import tempfile
from unittest.mock import patch
import shutil

from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.write_file_tool import WriteFileTool

# Fixture to initialize PathManager for tests that require it




# Generic PathManager fixture for tests that don't use temp dirs/files
@pytest.fixture
def path_manager_initialized():
    PathManager._reset_instance()
    pm = PathManager.get_instance()
    project_path = os.getcwd()
    output_path = os.path.join(project_path, "output")
    workspace_path = project_path
    pathlib.Path(output_path).mkdir(parents=True, exist_ok=True)
    pm.initialize({
        'project_path': project_path,
        'output_path': output_path,
        'workspace_path': workspace_path
    })
    yield True


# Fixture to create a temporary directory within the project and a test file, and initialize PathManager
@pytest.fixture
def temp_project_file():
    temp_dir = tempfile.mkdtemp(prefix="test_file_tools_workspace_")
    file_name = "test_file.txt"
    file_path_abs = os.path.join(temp_dir, file_name)
    file_path_relative = file_name  # Relative to workspace/output
    content = "This is a test file.\nIt has multiple lines."
    with open(file_path_abs, "w", encoding="utf-8") as f:
        f.write(content)

    # PathManager setup: workspace and output are the same temp dir
    PathManager._reset_instance()
    pm = PathManager.get_instance()
    pm.initialize({
        'project_path': temp_dir,
        'output_path': temp_dir,
        'workspace_path': temp_dir
    })

    yield file_path_relative, content, temp_dir, file_path_abs

    shutil.rmtree(temp_dir)


# Fixture to create a temporary directory within the project for file not found errors, and initialize PathManager
@pytest.fixture
def temp_project_dir():
    temp_dir = tempfile.mkdtemp(prefix="test_file_tools_workspace_")
    PathManager._reset_instance()
    pm = PathManager.get_instance()
    pm.initialize({
        'project_path': temp_dir,
        'output_path': temp_dir,
        'workspace_path': temp_dir
    })
    yield temp_dir
    shutil.rmtree(temp_dir)


# Tests for ReadFileTool
def test_read_file_tool_name():
    """Tests the name property of ReadFileTool."""
    tool = ReadFileTool()
    assert tool.name == 'read_file'

def test_read_file_tool_description():
    """Tests the description property of ReadFileTool."""
    tool = ReadFileTool()
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0

def test_read_file_tool_parameters_schema():
    """Tests the parameters_schema property of ReadFileTool."""
    tool = ReadFileTool()
    schema = tool.parameters_schema

    assert isinstance(schema, dict)
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'path' in schema['properties']
    assert schema['properties']['path']['type'] == 'string'
    assert 'required' in schema
    assert 'path' in schema['required']

def test_read_file_tool_openrouter_tool_definition():
    """Tests the Openrouter API definition for ReadFileTool."""
    tool = ReadFileTool()
    definition = tool.get_openrouter_tool_definition()

    assert isinstance(definition, dict)
    assert definition['type'] == 'function'
    assert 'function' in definition
    assert definition['function']['name'] == 'read_file'
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']
    assert definition['function']['parameters'] == tool.parameters_schema


def test_read_file_tool_ai_prompt_instructions():
    """Tests the AI prompt instructions for ReadFileTool."""
    tool = ReadFileTool()
    instructions = tool.get_ai_prompt_instructions()

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert 'read_file' in instructions
    assert 'path' in instructions

def test_read_file_tool_execute_success(temp_project_file):
    """Tests successful file reading using ReadFileTool with a relative path."""
    file_path_relative, expected_content, temp_dir, file_path_abs = temp_project_file
    tool = ReadFileTool()
    arguments = {'path': file_path_relative}
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        result = tool.execute(arguments)
    finally:
        os.chdir(old_cwd)
    assert expected_content.splitlines()[0] in result

def test_read_file_tool_execute_file_not_found(temp_project_dir):
    """Tests ReadFileTool handling of FileNotFoundError with a relative path."""
    non_existent_file_relative = "non_existent_file.txt"
    tool = ReadFileTool()
    arguments = {'path': non_existent_file_relative}
    old_cwd = os.getcwd()
    os.chdir(temp_project_dir)
    try:
        tool.execute(arguments)
    except FileNotFoundError:
        pass
    else:
        assert False, "Expected FileNotFoundError"
    finally:
        os.chdir(old_cwd)

def test_read_file_tool_execute_permission_denied(temp_project_file):
    """Tests ReadFileTool handling of PermissionError with a relative path."""
    file_path_relative, _, temp_dir, file_path_abs = temp_project_file
    tool = ReadFileTool()
    arguments = {'path': file_path_relative}
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = tool.execute(arguments)
    finally:
        os.chdir(old_cwd)
    assert "Permission denied" in result or "denied" in result

def test_read_file_tool_execute_missing_file_path(path_manager_initialized):
    """Tests ReadFileTool handling of missing file_path argument."""
    tool = ReadFileTool()
    arguments = {}
    result = tool.execute(arguments)
    assert "argument is missing" in result or "missing" in result

def test_read_file_tool_execute_path_outside_project_dir(path_manager_initialized):
    """Tests ReadFileTool handling of paths attempting to access outside the project directory."""
    tool = ReadFileTool()
    arguments = {'path': '../sensitive_file.txt'}
    temp_dir = tempfile.mkdtemp(prefix="test_file_tools_workspace_")
    PathManager._reset_instance()
    pm = PathManager.get_instance()
    pm.initialize({
        'project_path': temp_dir,
        'output_path': temp_dir,
        'workspace_path': temp_dir
    })
    old_cwd = os.getcwd()
    os.chdir(temp_dir)
    try:
        with pytest.raises(FileRestrictionError) as excinfo:
            tool.execute(arguments)
        assert "Access denied" in str(excinfo.value) or "outside the workspace directory" in str(excinfo.value)
        assert '../sensitive_file.txt' in str(excinfo.value)
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir)

def test_read_file_tool_execute_unsupported_file_type(temp_project_dir):
    """Tests ReadFileTool handling of unsupported file types."""
    # Create a binary file for testing
    binary_file_name = "test_binary.bin"
    binary_file_path_abs = os.path.join(temp_project_dir, binary_file_name)
    binary_file_path_relative = binary_file_name
    with open(binary_file_path_abs, "wb") as f:
        f.write(b"\x00\x01\x02\x03")
    tool = ReadFileTool()
    arguments = {'path': binary_file_path_relative}
    old_cwd = os.getcwd()
    os.chdir(temp_project_dir)
    try:
        result = tool.execute(arguments)
    finally:
        os.chdir(old_cwd)
    # The tool currently returns the raw bytes as a string, so check for that
    assert "\x00\x01\x02\x03" in result or result.strip() == "1 | \x00\x01\x02\x03"

# Tests for WriteFileTool
def test_write_file_tool_name():
    """Tests the name property of WriteFileTool."""
    tool = WriteFileTool()
    assert tool.name == 'write_to_file'

def test_write_file_tool_description():
    """Tests the description property of WriteFileTool."""
    tool = WriteFileTool()
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0

def test_write_file_tool_parameters_schema():
    """Tests the parameters_schema property of WriteFileTool."""
    tool = WriteFileTool()
    schema = tool.parameters_schema

    assert isinstance(schema, dict)
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'path' in schema['properties']
    assert schema['properties']['path']['type'] == 'string'
    assert 'content' in schema['properties']
    assert schema['properties']['content']['type'] == 'string'
    assert 'required' in schema
    assert 'path' in schema['required']
    assert 'content' in schema['required']

def test_write_file_tool_openrouter_api_definition():
    """Tests the Openrouter API definition for WriteFileTool."""
    tool = WriteFileTool()
    definition = tool.get_openrouter_tool_definition()

    assert isinstance(definition, dict)
    assert definition['function']['name'] == 'write_to_file'
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']
    assert definition['function']['parameters'] == tool.parameters_schema

def test_write_file_tool_ai_prompt_instructions():
    """Tests the AI prompt instructions for WriteFileTool."""
    tool = WriteFileTool()
    instructions = tool.get_ai_prompt_instructions()

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert 'write_to_file' in instructions
    assert 'path' in instructions
    assert 'content' in instructions

def test_write_file_tool_run_success(temp_project_dir):
    """Tests successful file writing using WriteFileTool."""
    file_name = "new_test_file.txt"
    file_path_relative = file_name
    content_to_write = "This is the content to write."
    tool = WriteFileTool()
    result = tool.execute(file_path_relative, content_to_write)
    assert result['status'] == 'success'
    assert file_path_relative in result['message']
    abs_path = os.path.join(temp_project_dir, file_name)
    with open(abs_path, 'r') as f:
        read_content = f.read()
    assert read_content == content_to_write

def test_write_file_tool_run_overwrite(temp_project_file):
    """Tests that WriteFileTool overwrites an existing file."""
    file_path_relative, original_content, temp_dir, file_path_abs = temp_project_file
    new_content = "This content overwrites the original."
    tool = WriteFileTool()
    result = tool.execute(file_path_relative, new_content)
    assert result['status'] == 'success'
    assert file_path_relative in result['message']
    with open(file_path_abs, 'r') as f:
        read_content = f.read()
    assert read_content == new_content
    assert read_content != original_content

def test_write_file_tool_run_permission_denied(temp_project_file):
    """Tests WriteFileTool handling of PermissionError."""
    file_path_relative, _, temp_dir, file_path_abs = temp_project_file
    content_to_write = "Attempting to write."
    tool = WriteFileTool()
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        result = tool.execute(file_path_relative, content_to_write)
    assert result['status'] == 'error'
    assert "Error writing to file" in result['message'] or "Permission denied" in result['message']
    assert file_path_relative in result['message']

def test_write_file_tool_run_directory_created(temp_project_dir):
    """Tests WriteFileTool creates parent directories if they do not exist."""
    non_existent_dir_relative = "non_existent_dir"
    file_path_relative = os.path.join(non_existent_dir_relative, "test_file.txt")
    content_to_write = "Content for non-existent directory."
    non_existent_dir_abs = os.path.join(temp_project_dir, non_existent_dir_relative)
    if os.path.exists(non_existent_dir_abs):
        shutil.rmtree(non_existent_dir_abs)
    tool = WriteFileTool()
    result = tool.execute(file_path_relative, content_to_write)
    assert result['status'] == 'success'
    assert file_path_relative in result['message']
    assert os.path.exists(non_existent_dir_abs)
    assert os.path.isdir(non_existent_dir_abs)
    file_path_abs = os.path.join(temp_project_dir, file_path_relative)
    assert os.path.exists(file_path_abs)
    assert os.path.isfile(file_path_abs)
    with open(file_path_abs, 'r') as f:
        read_content = f.read()
    assert read_content == content_to_write
    shutil.rmtree(non_existent_dir_abs)

def test_write_file_tool_run_missing_arguments():
    """Tests WriteFileTool handling of missing arguments."""
    tool = WriteFileTool()

    # Missing content
    with pytest.raises(TypeError):
        tool.execute('some/path/file.txt')

    with pytest.raises(TypeError):
        tool.execute(content='some content')

    with pytest.raises(TypeError):
        tool.execute()