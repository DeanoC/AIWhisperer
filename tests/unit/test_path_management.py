import pytest
import os
from unittest.mock import patch

# Import the actual PathManager class
from src.ai_whisperer.path_management import PathManager

@pytest.fixture(autouse=True)
def reset_path_manager_instance():
    """Fixture to reset the PathManager singleton before each test."""
    PathManager._reset_instance()
    yield
    PathManager._reset_instance() # Ensure reset after test as well

def test_singleton_instance():
    """Test that get_instance returns the same instance."""
    instance1 = PathManager.get_instance()
    instance2 = PathManager.get_instance()
    assert instance1 is instance2

    def test_accessing_paths_before_initialization():
        """Test that accessing paths before initialization raises an error."""
        instance = PathManager.get_instance()
        with pytest.raises(RuntimeError, match="PathManager not initialized."):
            _ = instance.app_path
        with pytest.raises(RuntimeError, match="PathManager not initialized."):
            _ = instance.project_path
        with pytest.raises(RuntimeError, match="PathManager not initialized."):
            _ = instance.output_path
        with pytest.raises(RuntimeError, match="PathManager not initialized."):
            _ = instance.workspace_path
        with pytest.raises(RuntimeError, match="PathManager not initialized."):
            instance.resolve_path("some/path")


    def test_initialization_with_defaults():
        """Test initialization with default values."""
        instance = PathManager.get_instance()
        instance.initialize()
        assert instance.project_path == os.getcwd()
        assert instance.output_path == os.path.join(os.getcwd(), "output")
        assert instance.workspace_path == os.getcwd()
        assert instance.app_path is None # Assuming app_path has no default


    @patch('os.getcwd', return_value='/mock/cwd')
    def test_initialization_with_config(self, mock_getcwd):
        """Test initialization with config values overriding defaults."""
        config = {
            'project_path': '/config/project',
            'output_path': '/config/output',
            'app_path': '/config/app'
        }
        instance = PathManager.get_instance()
        instance.initialize(config_values=config)
        assert instance.project_path == '/config/project'
        assert instance.output_path == '/config/output'
        assert instance.workspace_path == '/config/project' # workspace defaults to project if not in config/cli
        assert instance.app_path == '/config/app'

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_initialization_with_cli_args(self, mock_getcwd):
        """Test initialization with CLI arguments overriding config and defaults."""
        config = {
            'project_path': '/config/project',
            'output_path': '/config/output',
            'workspace_path': '/config/workspace_config',
            'app_path': '/config/app'
        }
        cli_args = {
            'project_path': '/cli/project',
            'workspace_path': '/cli/workspace_cli'
        }
        instance = PathManager.get_instance()
        instance.initialize(config_values=config, cli_args=cli_args)
        assert instance.project_path == '/cli/project'
        assert instance.output_path == '/config/output' # Not overridden by CLI
        assert instance.workspace_path == '/cli/workspace_cli'
        assert instance.app_path == '/config/app' # Not overridden by CLI

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_no_template(self, mock_getcwd):
        """Test resolve_path with a string containing no template variables."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'project_path': '/test/project'})
        path_string = "some/relative/path.txt"
        assert instance.resolve_path(path_string) == path_string

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_app_path_template(self, mock_getcwd):
        """Test resolve_path with {app_path} template."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'app_path': '/test/app'})
        template_string = "{app_path}/src/module.py"
        assert instance.resolve_path(template_string) == "/test/app/src/module.py"

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_project_path_template(self, mock_getcwd):
        """Test resolve_path with {project_path} template."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'project_path': '/test/project'})
        template_string = "{project_path}/data/input.csv"
        assert instance.resolve_path(template_string) == "/test/project/data/input.csv"

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_output_path_template(self, mock_getcwd):
        """Test resolve_path with {output_path} template."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'output_path': '/test/output'})
        template_string = "{output_path}/results/output.json"
        assert instance.resolve_path(template_string) == "/test/output/results/output.json"

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_workspace_path_template(self, mock_getcwd):
        """Test resolve_path with {workspace_path} template."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'workspace_path': '/test/workspace'})
        template_string = "{workspace_path}/temp/file.log"
        assert instance.resolve_path(template_string) == "/test/workspace/temp/file.log"

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_multiple_templates(self, mock_getcwd):
        """Test resolve_path with multiple template variables."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={
            'app_path': '/test/app',
            'project_path': '/test/project',
            'output_path': '/test/output',
            'workspace_path': '/test/workspace'
        })
        template_string = "{project_path}/src/{app_path}/output/{output_path}/workspace/{workspace_path}/file.txt"
        expected = "/test/project/src//test/app/output//test/output/workspace//test/workspace/file.txt"
        # Note: The expected path might look odd with double slashes depending on how paths are joined.
        # A more robust implementation would use os.path.join or pathlib.
        # For this test, we are just checking simple string replacement.
        assert instance.resolve_path(template_string) == expected

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_unknown_template(self, mock_getcwd):
        """Test resolve_path with an unknown template variable."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'project_path': '/test/project'})
        template_string = "{project_path}/data/{unknown_template}/file.txt"
        assert instance.resolve_path(template_string) == "/test/project/data/{unknown_template}/file.txt"

    @patch('os.getcwd', return_value='/mock/cwd')
    def test_resolve_path_template_not_set(self, mock_getcwd):
        """Test resolve_path with a template variable whose corresponding path is not set."""
        instance = PathManager.get_instance()
        instance.initialize(cli_args={'project_path': '/test/project'}) # app_path is not set
        template_string = "{app_path}/src/module.py"
        assert instance.resolve_path(template_string) == "/src/module.py" # Should replace with empty string if None