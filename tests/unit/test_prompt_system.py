import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from src.ai_whisperer import PromptSystem, PromptResolver, PromptLoader, PromptConfiguration, Prompt, PromptNotFoundError
from src.ai_whisperer.path_management import PathManager

# Unit Tests
class TestPromptConfiguration(unittest.TestCase):
    def test_get_override_path(self):
        config_data = {
            "prompt_settings": {
                "overrides": {
                    "core.initial_plan": "path/to/my_override.md"
                }
            }
        }
        config = PromptConfiguration(config_data)
        self.assertEqual(config.get_override_path("core", "initial_plan"), "path/to/my_override.md")
        self.assertIsNone(config.get_override_path("core", "non_existent"))

    def test_get_base_path(self):
        config_data = {
            "prompt_settings": {
                "base_paths": {
                    "custom": "project_prompts/"
                }
            }
        }
        config = PromptConfiguration(config_data)
        self.assertEqual(config.get_base_path("custom"), "project_prompts/")
        self.assertIsNone(config.get_base_path("agents")) # Default not in config

    def test_get_definition_path(self):
        config_data = {
            "prompt_settings": {
                "definitions": {
                    "my_custom_category.new_utility_prompt": "path/to/new_utility.md"
                }
            }
        }
        config = PromptConfiguration(config_data)
        self.assertEqual(config.get_definition_path("my_custom_category", "new_utility_prompt"), "path/to/new_utility.md")
        self.assertIsNone(config.get_definition_path("core", "initial_plan"))


class TestPromptLoader(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="Test prompt content")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_prompt_content_success(self, mock_exists, mock_file):
        loader = PromptLoader()
        test_path = Path("fake/path/to/prompt.md")
        content = loader.load_prompt_content(test_path)
        mock_file.assert_called_once_with(test_path, 'r', encoding='utf-8')
        self.assertEqual(content, "Test prompt content")

    @patch("pathlib.Path.exists", return_value=False)
    def test_load_prompt_content_file_not_found(self, mock_exists):
        loader = PromptLoader()
        test_path = Path("non/existent/path.md")
        with self.assertRaises(FileNotFoundError):
            loader.load_prompt_content(test_path)

class TestPromptResolver(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.base_dir = self.temp_dir # Use temp_dir as base_dir for resolver tests
        self.prompts_dir = self.base_dir / "prompts"
        self.prompts_dir.mkdir()
        (self.prompts_dir / "core").mkdir()
        (self.prompts_dir / "agents").mkdir()
        (self.prompts_dir / "custom").mkdir()
        (self.prompts_dir / "custom" / "core").mkdir()
        (self.base_dir / "project_prompts").mkdir() # For custom base path test

        # Create dummy prompt files for PromptSystem tests
        (self.prompts_dir / "core" / "test.prompt.md").write_text("This is the prompt content.")
        (self.prompts_dir / "core" / "template.prompt.md").write_text("User: {{{user_name}}}\nTask: {{{task_description}}}")
        (self.prompts_dir / "core" / "initial_plan.prompt.md").write_text("Core initial plan prompt.")
        (self.prompts_dir / "agents" / "code_generation.prompt.md").write_text("Agent code generation prompt.")
        (self.base_dir / "project_prompts" / "my_project_prompt.prompt.md").write_text("Project specific prompt.")

        # Patch PathManager to use this temp project path and prompt path
        PathManager._reset_instance()
        PathManager.get_instance().initialize(config_values={'project_path': str(self.base_dir), 'prompt_path': str(self.base_dir)})
        print(f"[DEBUG] setUp: prompt_path={PathManager.get_instance().prompt_path}")
        print(f"[DEBUG] setUp: project_path={PathManager.get_instance().project_path}")

        self.mock_config = MagicMock(spec=PromptConfiguration)
        # Configure the mock config to return a dictionary for _config access for list_prompts test
        self.mock_config._config = {
            "prompt_settings": {
                "definitions": {
                    "my_custom_category.new_utility_prompt": str(self.base_dir / "project_prompts" / "my_project_prompt.prompt.md")
                }
            }
        }
        # Mock get_definition_path to return the path for the list_prompts test
        self.mock_config.get_definition_path.side_effect = lambda cat, name: str(self.base_dir / "project_prompts" / "my_project_prompt.prompt.md") if cat == "my_custom_category" and name == "new_utility_prompt" else None
        self.mock_config.get_override_path.return_value = None
        self.mock_config.get_base_path.side_effect = lambda category: "prompts/custom" if category == "custom" else None # Mock default custom base path

        # Use real instances of Resolver and Loader, but pass PathManager
        self.resolver = PromptResolver(self.mock_config, PathManager.get_instance())
        self.loader = PromptLoader()

        # Initialize PromptSystem with real dependencies and PathManager
        self.manager = PromptSystem(self.mock_config, path_manager=PathManager.get_instance())
        # Manually inject the real loader and resolver for testing purposes
        self.manager._loader = self.loader
        self.manager._resolver = self.resolver

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_resolve_prompt_path_override(self):
        override_path_relative = "custom_overrides/core/my_initial_plan.md"
        override_path_config = f"{{prompt_path}}/{override_path_relative}"
        override_path_absolute = PathManager.get_instance().resolve_path(override_path_config)
        override_path_absolute_obj = Path(override_path_absolute)
        override_path_absolute_obj.parent.mkdir(parents=True, exist_ok=True)
        override_path_absolute_obj.write_text("Override content")

        self.mock_config.get_override_path.return_value = override_path_config
        self.mock_config.get_definition_path.return_value = None # Ensure definition is not used

        resolved_path = self.resolver.resolve_prompt_path("core", "initial_plan")
        self.assertEqual(str(resolved_path.resolve()), str(override_path_absolute_obj.resolve()))
        self.mock_config.get_override_path.assert_called_once_with("core", "initial_plan")
        self.mock_config.get_definition_path.assert_not_called() # Definition is not checked if override exists


    def test_resolve_prompt_path_definition(self):
        # Use .prompt.md extension for new system
        definition_path_relative = "new_prompts/my_category/my_prompt.prompt.md"
        definition_path_config = f"{{prompt_path}}/{definition_path_relative}"
        # Use PathManager to resolve the config path, just like the resolver will
        resolved_definition_path = Path(PathManager.get_instance().resolve_path(definition_path_config))
        resolved_definition_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_definition_path.write_text("Definition content")

        self.mock_config.get_override_path.side_effect = lambda cat, name: None
        self.mock_config.get_definition_path.side_effect = lambda cat, name: definition_path_config if cat == "my_category" and name == "my_prompt" else None

        resolved_path = self.resolver.resolve_prompt_path("my_category", "my_prompt")
        print(f"[DEBUG] Definition: expected={resolved_definition_path.resolve()} resolved={resolved_path.resolve()}")
        self.assertEqual(str(resolved_path.resolve()), str(resolved_definition_path.resolve()))
        self.mock_config.get_override_path.assert_called_once_with("my_category", "my_prompt")
        self.mock_config.get_definition_path.assert_called_once_with("my_category", "my_prompt")


    def test_resolve_prompt_path_custom_directory_with_base_path(self):
        custom_base_path_relative = "project_prompts"
        custom_prompt_path_relative = "my_custom_category/my_prompt.prompt.md"
        custom_base_path_config = f"{{prompt_path}}/{custom_base_path_relative}"
        # Use PathManager to resolve the base path, just like the resolver will
        resolved_base_path = Path(PathManager.get_instance().resolve_path(custom_base_path_config))
        expected_path = resolved_base_path / custom_prompt_path_relative
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        expected_path.write_text("Custom base path content")

        self.mock_config.get_override_path.side_effect = lambda cat, name: None
        self.mock_config.get_definition_path.side_effect = lambda cat, name: None
        self.mock_config.get_base_path.side_effect = lambda category: custom_base_path_config if category == "custom" else None

        resolved_path = self.resolver.resolve_prompt_path("my_custom_category", "my_prompt")
        print(f"[DEBUG] Custom base: expected={expected_path.resolve()} resolved={resolved_path.resolve()}")
        self.assertEqual(str(resolved_path.resolve()), str(expected_path.resolve()))
        self.mock_config.get_override_path.assert_called_once_with("my_custom_category", "my_prompt")
        self.mock_config.get_definition_path.assert_called_once_with("my_custom_category", "my_prompt")
        self.mock_config.get_base_path.assert_any_call("custom") # Check for default custom base path


    def test_resolve_prompt_path_custom_directory_default_base_path(self):
        prompt_path = PathManager.get_instance().prompt_path
        custom_base_path = PathManager.get_instance().resolve_path("prompts/custom")
        custom_prompt_path_absolute = Path(custom_base_path) / "my_category" / "my_prompt.prompt.md"
        custom_prompt_path_absolute.parent.mkdir(parents=True, exist_ok=True)
        custom_prompt_path_absolute.write_text("Default custom base path content")

        self.mock_config.get_override_path.return_value = None
        self.mock_config.get_definition_path.return_value = None
        self.mock_config.get_base_path.side_effect = lambda category: "prompts/custom" if category == "custom" else None # Mock default custom base path

        resolved_path = self.resolver.resolve_prompt_path("my_category", "my_prompt")
        print(f"[DEBUG] Custom default: expected={custom_prompt_path_absolute.resolve()} resolved={resolved_path.resolve()}")
        self.assertEqual(str(resolved_path.resolve()), str(custom_prompt_path_absolute.resolve()))
        self.mock_config.get_override_path.assert_called_once_with("my_category", "my_prompt")
        self.mock_config.get_definition_path.assert_called_once_with("my_category", "my_prompt")
        self.mock_config.get_base_path.assert_any_call("custom") # Check for default custom base path


    def test_resolve_prompt_path_agent_directory(self):
        agent_prompt_path_relative = "prompts/agents/code_generation.prompt.md"
        agent_prompt_path_absolute = self.base_dir / agent_prompt_path_relative
        agent_prompt_path_absolute.parent.mkdir(parents=True, exist_ok=True)
        agent_prompt_path_absolute.write_text("Agent content")

        self.mock_config.get_override_path.return_value = None
        self.mock_config.get_definition_path.return_value = None
        self.mock_config.get_base_path.side_effect = lambda category: "prompts/custom" if category == "custom" else None # Mock default custom base path

        resolved_path = self.resolver.resolve_prompt_path("agents", "code_generation")
        self.assertEqual(resolved_path, agent_prompt_path_absolute)
        self.mock_config.get_override_path.assert_called_once_with("agents", "code_generation")
        self.mock_config.get_definition_path.assert_called_once_with("agents", "code_generation")
        self.mock_config.get_base_path.assert_any_call("custom") # Check for default custom base path


    def test_resolve_prompt_path_core_directory(self):
        core_prompt_path_relative = "prompts/core/initial_plan.prompt.md"
        core_prompt_path_absolute = self.base_dir / core_prompt_path_relative
        core_prompt_path_absolute.parent.mkdir(parents=True, exist_ok=True)
        core_prompt_path_absolute.write_text("Core content")

        self.mock_config.get_override_path.return_value = None
        self.mock_config.get_definition_path.return_value = None
        self.mock_config.get_base_path.side_effect = lambda category: "prompts/custom" if category == "custom" else None # Mock default custom base path

        resolved_path = self.resolver.resolve_prompt_path("core", "initial_plan")
        self.assertEqual(resolved_path, core_prompt_path_absolute)
        self.mock_config.get_override_path.assert_called_once_with("core", "initial_plan")
        self.mock_config.get_definition_path.assert_called_once_with("core", "initial_plan")
        self.mock_config.get_base_path.assert_any_call("custom") # Check for default custom base path


    def test_resolve_prompt_path_not_found(self):
        self.mock_config.get_override_path.return_value = None
        self.mock_config.get_definition_path.return_value = None
        self.mock_config.get_base_path.side_effect = lambda category: "prompts/custom" if category == "custom" else None # Mock default custom base path

        with self.assertRaises(PromptNotFoundError):
            self.resolver.resolve_prompt_path("non_existent_category", "non_existent_prompt")

        self.mock_config.get_override_path.assert_called_once_with("non_existent_category", "non_existent_prompt")
        self.mock_config.get_definition_path.assert_called_once_with("non_existent_category", "non_existent_prompt")
        self.mock_config.get_base_path.assert_any_call("custom") # Check for default custom base path



    # (Removed duplicate setUp and tearDown for PromptSystem manager tests)

    def test_get_prompt_success(self):
        # The resolver will find the real file in the temp directory
        prompt = self.manager.get_prompt("core", "test")

        self.assertIsInstance(prompt, Prompt)
        self.assertEqual(prompt.category, "core")
        self.assertEqual(prompt.name, "test")
        self.assertEqual(prompt.path, self.prompts_dir / "core" / "test.prompt.md")
        self.assertIsNotNone(prompt._loader) # Check if loader was injected

    def test_get_prompt_not_found(self):
        # The resolver will not find the file in the temp directory
        with self.assertRaises(PromptNotFoundError):
            self.manager.get_prompt("core", "non_existent")

    def test_list_prompts(self):
        # list_prompts relies on the config and the resolver's ability to find files.
        # With real files and a mocked config, we can test this.
        prompts = self.manager.list_prompts()

        # The hardcoded list in prompt_system.py list_prompts needs to be considered.
        # We expect the hardcoded ones plus the one from the mocked definition.
        expected_prompts = [
            ("core", "initial_plan"),
            ("core", "subtask_generator"),
            ("agents", "code_generation"),
            ("my_custom_category", "new_utility_prompt") # From mocked definition
        ]
        # Sort both lists for reliable comparison
        self.assertEqual(sorted(prompts), sorted(expected_prompts))

        prompts_core = self.manager.list_prompts(category="core")
        self.assertEqual(sorted(prompts_core), sorted([("core", "initial_plan"), ("core", "subtask_generator")]))

        prompts_agents = self.manager.list_prompts(category="agents")
        self.assertEqual(sorted(prompts_agents), sorted([("agents", "code_generation")]))

        prompts_custom = self.manager.list_prompts(category="my_custom_category")
        self.assertEqual(sorted(prompts_custom), sorted([("my_custom_category", "new_utility_prompt")]))


if __name__ == '__main__':
    unittest.main()