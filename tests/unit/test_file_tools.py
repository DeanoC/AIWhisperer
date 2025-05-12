import pytest
import os
import tempfile
from unittest.mock import patch
import shutil

from src.ai_whisperer.tools.read_file_tool import ReadFileTool
from src.ai_whisperer.tools.write_file_tool import WriteTextFileTool

# Fixture to create a temporary directory within the project and a test file
@pytest.fixture
def temp_project_file():
    # Create a temporary directory within the current working directory (project root)
    temp_dir_prefix = "test_read_file_"
    temp_test_dir = tempfile.mkdtemp(prefix=temp_dir_prefix, dir=".")
    
    file_name = "test_file.txt"
    file_path_abs = os.path.join(temp_test_dir, file_name)
    file_path_relative = os.path.join(os.path.basename(temp_test_dir), file_name) # Path relative to project root

    content = "This is a test file.\nIt has multiple lines."
    with open(file_path_abs, "w", encoding="utf-8") as f:
        f.write(content)

    yield file_path_relative, content, temp_test_dir

    # Clean up the temporary directory
    shutil.rmtree(temp_test_dir)

# Fixture to create a temporary directory within the project for file not found errors
@pytest.fixture
def temp_project_dir():
    # Create a temporary directory within the current working directory (project root)
    temp_dir_prefix = "test_read_file_dir_"
    temp_test_dir = tempfile.mkdtemp(prefix=temp_dir_prefix, dir=".")
    
    yield os.path.basename(temp_test_dir) # Return relative path to the temporary directory

    # Clean up the temporary directory
    shutil.rmtree(temp_test_dir)


# Tests for ReadFileTool
def test_read_file_tool_name():
    """Tests the name property of ReadFileTool."""
    tool = ReadFileTool()
    assert tool.name == 'read_text_file'

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
    assert 'file_path' in schema['properties']
    assert schema['properties']['file_path']['type'] == 'string'
    assert 'required' in schema
    assert 'file_path' in schema['required']

def test_read_file_tool_openrouter_tool_definition():
    """Tests the Openrouter API definition for ReadFileTool."""
    tool = ReadFileTool()
    definition = tool.get_openrouter_tool_definition()

    assert isinstance(definition, dict)
    assert definition['type'] == 'function'
    assert 'function' in definition
    assert definition['function']['name'] == 'read_text_file'
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']
    assert definition['function']['parameters'] == tool.parameters_schema


def test_read_file_tool_ai_prompt_instructions():
    """Tests the AI prompt instructions for ReadFileTool."""
    tool = ReadFileTool()
    instructions = tool.get_ai_prompt_instructions()

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert 'read_text_file' in instructions
    assert 'file_path' in instructions

def test_read_file_tool_execute_success(temp_project_file):
    """Tests successful file reading using ReadFileTool with a relative path."""
    file_path_relative, expected_content, _ = temp_project_file
    tool = ReadFileTool()
    arguments = {'file_path': file_path_relative}
    result = tool.execute(arguments)

    assert result == expected_content

def test_read_file_tool_execute_file_not_found(temp_project_dir):
    """Tests ReadFileTool handling of FileNotFoundError with a relative path."""
    non_existent_file_relative = os.path.join(temp_project_dir, "non_existent_file.txt")
    tool = ReadFileTool()
    arguments = {'file_path': non_existent_file_relative}
    result = tool.execute(arguments)

    assert "Error: File not found" in result
    assert non_existent_file_relative in result # Check for the relative path in the error message

def test_read_file_tool_execute_permission_denied(temp_project_file):
    """Tests ReadFileTool handling of PermissionError with a relative path."""
    file_path_relative, _, _ = temp_project_file
    tool = ReadFileTool()
    arguments = {'file_path': file_path_relative}

    # Simulate permission denied error
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        result = tool.execute(arguments)

    assert "Error: Permission denied" in result
    assert file_path_relative in result # Check for the relative path in the error message

def test_read_file_tool_execute_missing_file_path():
    """Tests ReadFileTool handling of missing file_path argument."""
    tool = ReadFileTool()
    arguments = {}
    result = tool.execute(arguments)

    assert "Error: 'file_path' argument is missing." in result

def test_read_file_tool_execute_path_outside_project_dir():
    """Tests ReadFileTool handling of paths attempting to access outside the project directory."""
    tool = ReadFileTool()
    arguments = {'file_path': '../sensitive_file.txt'} # Attempt to go up a directory
    result = tool.execute(arguments)

    assert "Error: Access denied. File path" in result
    assert '../sensitive_file.txt' in result
    assert "resolves outside the project directory." in result

def test_read_file_tool_execute_unsupported_file_type(temp_project_dir):
    """Tests ReadFileTool handling of unsupported file types with a relative path."""
    binary_file_name = "test_binary.bin"
    binary_file_path_abs = os.path.join(os.path.abspath(temp_project_dir), binary_file_name)
    binary_file_path_relative = os.path.join(temp_project_dir, binary_file_name)

    with open(binary_file_path_abs, "wb") as f:
        f.write(b"\x00\x01\x02\x03")

    tool = ReadFileTool()
    arguments = {'file_path': binary_file_path_relative}
    result = tool.execute(arguments)

    assert "Error: File type not supported." in result
    assert "Only text files are allowed." in result

# Tests for WriteTextFileTool
def test_write_file_tool_name():
    """Tests the name property of WriteTextFileTool."""
    tool = WriteTextFileTool()
    assert tool.name == 'write_text_file'

def test_write_file_tool_description():
    """Tests the description property of WriteTextFileTool."""
    tool = WriteTextFileTool()
    assert isinstance(tool.description, str)
    assert len(tool.description) > 0

def test_write_file_tool_parameters_schema():
    """Tests the parameters_schema property of WriteTextFileTool."""
    tool = WriteTextFileTool()
    schema = tool.parameters_schema

    assert isinstance(schema, dict)
    assert schema['type'] == 'object'
    assert 'properties' in schema
    assert 'file_path' in schema['properties']
    assert schema['properties']['file_path']['type'] == 'string'
    assert 'content' in schema['properties']
    assert schema['properties']['content']['type'] == 'string'
    assert 'required' in schema
    assert 'file_path' in schema['required']
    assert 'content' in schema['required']

def test_write_file_tool_openrouter_api_definition():
    """Tests the Openrouter API definition for WriteTextFileTool."""
    tool = WriteTextFileTool()
    definition = tool.get_openrouter_tool_definition()

    assert isinstance(definition, dict)
    assert definition['function']['name'] == 'write_text_file'
    assert 'description' in definition['function']
    assert 'parameters' in definition['function']
    assert definition['function']['parameters'] == tool.parameters_schema

def test_write_file_tool_ai_prompt_instructions():
    """Tests the AI prompt instructions for WriteTextFileTool."""
    tool = WriteTextFileTool()
    instructions = tool.get_ai_prompt_instructions()

    assert isinstance(instructions, str)
    assert len(instructions) > 0
    assert 'write_text_file' in instructions
    assert 'file_path' in instructions
    assert 'content' in instructions

@pytest.mark.asyncio # Mark the test as async
async def test_write_file_tool_run_success(temp_project_dir):
    """Tests successful file writing using WriteTextFileTool."""
    temp_dir_relative = temp_project_dir
    file_name = "new_test_file.txt"
    file_path_relative = os.path.join(temp_dir_relative, file_name)
    content_to_write = "This is the content to write."

    tool = WriteTextFileTool()
    arguments = {'file_path': file_path_relative, 'content': content_to_write}
    # Call the execute method, not run
    result = await tool.execute(file_path=arguments['file_path'], content=arguments['content'])

    assert result['status'] == 'success'
    assert file_path_relative in result['message']

    # Verify content was written correctly
    with open(file_path_relative, 'r') as f:
        read_content = f.read()
    assert read_content == content_to_write

@pytest.mark.asyncio # Mark the test as async
async def test_write_file_tool_run_overwrite(temp_project_file):
    """Tests that WriteTextFileTool overwrites an existing file."""
    file_path_relative, original_content, _ = temp_project_file
    new_content = "This content overwrites the original."

    tool = WriteTextFileTool()
    arguments = {'file_path': file_path_relative, 'content': new_content}
    # Call the execute method, not run
    result = await tool.execute(file_path=arguments['file_path'], content=arguments['content'])

    assert result['status'] == 'success'
    assert file_path_relative in result['message']

    # Verify content was overwritten
    with open(file_path_relative, 'r') as f:
        read_content = f.read()
    assert read_content == new_content
    assert read_content != original_content

@pytest.mark.asyncio # Mark the test as async
async def test_write_file_tool_run_permission_denied(temp_project_file):
    """Tests WriteTextFileTool handling of PermissionError."""
    file_path_relative, _, _ = temp_project_file
    content_to_write = "Attempting to write."

    tool = WriteTextFileTool()
    arguments = {'file_path': file_path_relative, 'content': content_to_write}

    # Simulate permission denied error
    with patch('builtins.open', side_effect=IOError("Permission denied")):
        # Call the execute method, not run
        result = await tool.execute(file_path=arguments['file_path'], content=arguments['content'])

    assert result['status'] == 'error'
    assert "Error writing to file" in result['message']
    assert "Permission denied" in result['message']
    assert file_path_relative in result['message']

@pytest.mark.asyncio # Mark the test as async
async def test_write_file_tool_run_directory_not_exists(temp_project_dir):
    """Tests WriteTextFileTool handling when the directory does not exist."""
    non_existent_dir_relative = os.path.join(temp_project_dir, "non_existent_dir")
    file_path_relative = os.path.join(non_existent_dir_relative, "test_file.txt")
    content_to_write = "Content for non-existent directory."

    tool = WriteTextFileTool()
    arguments = {'file_path': file_path_relative, 'content': content_to_write}

    # Call the execute method, not run
    result = await tool.execute(file_path=arguments['file_path'], content=arguments['content'])

    assert result['status'] == 'error'
    assert "Error writing to file" in result['message']
    # The exact error message might vary by OS, but it should indicate a problem with the path/directory
    assert "No such file or directory" in result['message'] or "The system cannot find the path specified" in result['message']
    assert file_path_relative in result['message']

@pytest.mark.asyncio # Mark the test as async
async def test_write_file_tool_run_missing_arguments():
    """Tests WriteTextFileTool handling of missing arguments."""
    tool = WriteTextFileTool()

    # Missing content
    arguments_missing_content = {'file_path': 'some/path/file.txt'}
    with pytest.raises(TypeError): # The execute method signature requires both arguments
         # Call the execute method, not run
         await tool.execute(file_path=arguments_missing_content['file_path'])

    # Missing file_path
    arguments_missing_filepath = {'content': 'some content'}
    with pytest.raises(TypeError): # The execute method signature requires both arguments
         # Call the execute method, not run
         await tool.execute(content=arguments_missing_filepath['content'])

    # Missing both
    arguments_missing_both = {}
    with pytest.raises(TypeError): # The execute method signature requires both arguments
         # Call the execute method, not run
         await tool.execute()