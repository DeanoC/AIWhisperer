import pytest
import os
from pathlib import Path

# Assume these will eventually interact with the runner's file access logic
# which will use PathManager for restrictions.
# Currently, they are placeholders that will need to be integrated with the actual runner execution.

from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.write_file_tool import WriteFileTool
from ai_whisperer.path_management import PathManager # Import PathManager
from ai_whisperer.exceptions import FileRestrictionError # Import FileRestrictionError


# Define dummy workspace and output directories for testing
# These should ideally be set up by a test fixture that initializes PathManager
TEST_WORKSPACE_DIR = Path("./test_workspace").resolve()
TEST_OUTPUT_DIR = Path("./test_output").resolve()

# Create dummy files and directories for testing
@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    # Create test directories
    TEST_WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_WORKSPACE_DIR / "allowed_file.txt").write_text("This is an allowed file.")
    (TEST_OUTPUT_DIR / "initial_output.txt").write_text("Initial output content.")
    # Create a file outside the workspace and output directories
    outside_dir = Path("./outside_test_dir").resolve()
    outside_dir.mkdir(parents=True, exist_ok=True)
    (outside_dir / "sensitive_file.txt").write_text("This is a sensitive file.")

    # Initialize PathManager with test directories
    path_manager = PathManager.get_instance()
    path_manager._reset_instance() # Reset for clean test setup
    path_manager.initialize(config_values={
        'workspace_path': str(TEST_WORKSPACE_DIR),
        'output_path': str(TEST_OUTPUT_DIR)
    })


    yield

    # Clean up test directories
    import shutil
    if TEST_WORKSPACE_DIR.exists():
        shutil.rmtree(TEST_WORKSPACE_DIR)
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    if outside_dir.exists():
        shutil.rmtree(outside_dir)


# Helper function to initialize PathManager for tests
def initialize_path_manager():
    path_manager = PathManager.get_instance()
    # Only initialize if not already initialized (e.g., by a fixture)
    if not path_manager._initialized:
         path_manager.initialize(config_values={
            'workspace_path': str(TEST_WORKSPACE_DIR),
            'output_path': str(TEST_OUTPUT_DIR)
        })


# Test cases for reading files
def test_read_file_within_workspace():
    """Should allow reading a file within the workspace."""
    initialize_path_manager() # Initialize PathManager before using the tool
    file_path = TEST_WORKSPACE_DIR / "allowed_file.txt"
    read_tool = ReadFileTool()
    # Expecting the content of the file
    content = read_tool.execute(arguments={'path': str(file_path)})
    assert "allowed file" in content

def test_read_file_outside_workspace():
    """Should prevent reading a file outside the workspace."""
    initialize_path_manager() # Initialize PathManager before using the tool
    outside_file_path = Path("./outside_test_dir/sensitive_file.txt").resolve()
    read_tool = ReadFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        read_tool.execute(arguments={'path': str(outside_file_path)})
    assert "Access denied." in str(excinfo.value)

def test_read_file_using_relative_path_outside_workspace():
    """Should prevent reading a file outside the workspace using relative paths."""
    initialize_path_manager() # Initialize PathManager before using the tool
    # This path attempts to go up and out of the workspace
    relative_path = "../outside_test_dir/sensitive_file.txt"
    read_tool = ReadFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        read_tool.execute(arguments={'path': relative_path})
    assert "Access denied." in str(excinfo.value)


def test_read_file_using_absolute_path_outside_workspace():
    """Should prevent reading a file outside the workspace using absolute paths."""
    initialize_path_manager() # Initialize PathManager before using the tool
    outside_file_path = Path("./outside_test_dir/sensitive_file.txt").resolve()
    read_tool = ReadFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        read_tool.execute(arguments={'path': str(outside_file_path)})
    assert "Access denied." in str(excinfo.value)


# Test cases for writing files
def test_write_file_within_output():
    """Should allow writing a file within the output directory."""
    initialize_path_manager() # Initialize PathManager before using the tool
    file_path = TEST_OUTPUT_DIR / "new_output_file.txt"
    content = "This is a new output file."
    write_tool = WriteFileTool()
    # Expecting a success status
    result = write_tool.execute(path=str(file_path), content=content)
    assert result["status"] == "success"
    assert file_path.exists()
    assert file_path.read_text() == content

def test_write_file_outside_output():
    """Should prevent writing a file outside the output directory."""
    initialize_path_manager() # Initialize PathManager before using the tool
    outside_file_path = Path("./outside_test_dir/unauthorized_write.txt").resolve()
    content = "Attempting to write outside output."
    write_tool = WriteFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        write_tool.execute(path=str(outside_file_path), content=content)
    assert "Access denied." in str(excinfo.value)
    assert not outside_file_path.exists() # Ensure the file was not created


def test_write_file_using_relative_path_outside_output():
    """Should prevent writing a file outside the output directory using relative paths."""
    initialize_path_manager() # Initialize PathManager before using the tool
    # This path attempts to go up and out of the output directory
    relative_path = "../outside_test_dir/unauthorized_relative_write.txt"
    write_tool = WriteFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        write_tool.execute(path=relative_path, content="Relative write attempt.")
    assert "Access denied." in str(excinfo.value)
    unauthorized_file = Path("./outside_test_dir/unauthorized_relative_write.txt").resolve()
    assert not unauthorized_file.exists()


def test_write_file_using_absolute_path_outside_output():
    """Should prevent writing a file outside the output directory using absolute paths."""
    initialize_path_manager() # Initialize PathManager before using the tool
    outside_file_path = Path("./outside_test_dir/unauthorized_absolute_write.txt").resolve()
    content = "Attempting to write outside output with absolute path."
    write_tool = WriteFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        write_tool.execute(path=str(outside_file_path), content=content)
    assert "Access denied." in str(excinfo.value)
    assert not outside_file_path.exists()


# Additional test cases for edge cases and path handling
def test_read_file_from_output_dir():
    """Should prevent reading a file from the output directory (read-only workspace)."""
    initialize_path_manager() # Initialize PathManager before using the tool
    output_file_path = TEST_OUTPUT_DIR / "initial_output.txt"
    read_tool = ReadFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        read_tool.execute(arguments={'path': str(output_file_path)})
    assert "Access denied." in str(excinfo.value)


def test_write_file_to_workspace_dir():
    """Should prevent writing a file to the workspace directory (write-only output)."""
    initialize_path_manager() # Initialize PathManager before using the tool
    workspace_file_path = TEST_WORKSPACE_DIR / "unauthorized_write_to_workspace.txt"
    content = "Attempting to write to workspace."
    write_tool = WriteFileTool()
    # Expecting a FileRestrictionError
    with pytest.raises(FileRestrictionError) as excinfo:
        write_tool.execute(path=str(workspace_file_path), content=content)
    assert "Access denied." in str(excinfo.value)
    assert not workspace_file_path.exists()


def test_read_nonexistent_file_within_workspace():
    """Should raise FileNotFoundError for a nonexistent file within the workspace."""
    initialize_path_manager() # Initialize PathManager before using the tool
    nonexistent_file_path = TEST_WORKSPACE_DIR / "nonexistent_file.txt"
    read_tool = ReadFileTool()
    # Expecting FileNotFoundError
    with pytest.raises(FileNotFoundError):
        read_tool.execute(arguments={'path': str(nonexistent_file_path)})


def test_write_to_subdirectory_within_output():
    """Should allow writing to a subdirectory within the output directory."""
    initialize_path_manager() # Initialize PathManager before using the tool
    subdir_path = TEST_OUTPUT_DIR / "subdir"
    file_path = subdir_path / "nested_output.txt"
    content = "Content in nested directory."
    write_tool = WriteFileTool()
    # Expecting a success status
    result = write_tool.execute(path=str(file_path), content=content)
    assert result["status"] == "success"
    assert file_path.exists()
    assert file_path.read_text() == content


def test_read_file_with_dot_dot_in_path_within_workspace():
    """Should allow reading a file within the workspace using paths with '..' that stay within."""
    initialize_path_manager() # Initialize PathManager before using the tool
    # Assuming the current working directory is the project root
    # and the workspace is ./test_workspace
    # This path resolves to ./test_workspace/allowed_file.txt
    relative_path = "./test_workspace/../test_workspace/allowed_file.txt"
    read_tool = ReadFileTool()
    # Expecting the content of the file
    content = read_tool.execute(arguments={'path': relative_path})
    assert "allowed file" in content


def test_write_file_with_dot_dot_in_path_within_output():
    """Should allow writing a file within the output using paths with '..' that stay within."""
    initialize_path_manager() # Initialize PathManager before using the tool
    # Assuming the current working directory is the project root
    # and the output is ./test_output
    # This path resolves to ./test_output/nested/../new_file.txt -> ./test_output/new_file.txt
    relative_path = "./test_output/nested/../new_file_with_dot_dot.txt"
    content = "Content with dot dot in path."
    write_tool = WriteFileTool()
    # Expecting a success status
    result = write_tool.execute(path=relative_path, content=content)
    assert result["status"] == "success"
    # Use the resolved_path from the result to check for existence and content
    resolved_file_path = Path(result["resolved_path"])
    assert resolved_file_path.exists()
    assert resolved_file_path.read_text() == content