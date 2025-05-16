import unittest
import tempfile
import shutil
from pathlib import Path
import os
from unittest.mock import patch

from src.ai_whisperer import PromptSystem, PromptConfiguration, Prompt, PromptNotFoundError


class TestPromptLoadingIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory structure for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.prompts_dir = self.temp_dir / "prompts"
        self.prompts_dir.mkdir()
        (self.prompts_dir / "core").mkdir()
        (self.prompts_dir / "agents").mkdir()
        (self.prompts_dir / "custom").mkdir()
        (self.prompts_dir / "custom" / "core").mkdir()
        (self.temp_dir / "project_prompts").mkdir() # For custom base path test

        # Create dummy prompt files
        (self.prompts_dir / "core" / "initial_plan.prompt.md").write_text("Core initial plan prompt.")
        (self.prompts_dir / "agents" / "code_generation.prompt.md").write_text("Agent code generation prompt.")
        (self.prompts_dir / "custom" / "my_feature").mkdir(parents=True, exist_ok=True)
        (self.prompts_dir / "custom" / "my_feature" / "special_task.prompt.md").write_text("Custom special task prompt.")
        # Ensure the override file is created at custom/core/initial_plan.override.prompt.md (relative to prompt_path)
        override_dir = self.temp_dir / "custom" / "core"
        override_dir.mkdir(parents=True, exist_ok=True)
        (override_dir / "initial_plan.override.prompt.md").write_text("Custom override initial plan prompt.")
        (self.temp_dir / "project_prompts" / "my_project_prompt.prompt.md").write_text("Project specific prompt.")

        # Create a dummy config file
        self.config_data = {
            "prompt_settings": {
                "base_paths": {
                    "custom": "project_prompts",
                    "core": "prompts/custom"
                },
                # Use a relative path for the override, matching the actual file location
                "overrides": {
                    "core.initial_plan": "custom/core/initial_plan.override.prompt.md"
                },
                "definitions": {
                    "project.my_prompt": "project_prompts/my_project_prompt.prompt.md"
                }
            }
        }
        self.config = PromptConfiguration(self.config_data)
        self.manager = PromptSystem(self.config, self.temp_dir)

        # --- PathManager initialization for integration tests ---
        from ai_whisperer.path_management import PathManager
        PathManager._reset_instance()
        PathManager.get_instance().initialize(config_values={
            'project_path': str(self.temp_dir),
            'prompt_path': str(self.temp_dir)
        })

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_prompt_resolution_hierarchy(self):
        # Test override
        prompt_override = self.manager.get_prompt("core", "initial_plan")
        print(f"[DEBUG] prompt_override.path: {prompt_override.path}")
        print(f"[DEBUG] expected: {self.temp_dir / 'custom/core/initial_plan.override.prompt.md'}")
        print(f"[DEBUG] exists: { (self.temp_dir / 'custom/core/initial_plan.override.prompt.md').exists() }")
        print(f"[DEBUG] fallback exists: { (self.temp_dir / 'prompts/core/initial_plan.prompt.md').exists() }")
        # Normalize paths for robust comparison on Windows
        expected_path = self.temp_dir / "custom/core/initial_plan.override.prompt.md"
        actual_path = prompt_override.path
        # Use os.path.samefile if possible, else fallback to realpath comparison
        try:
            self.assertTrue(os.path.samefile(actual_path, expected_path))
        except (AttributeError, FileNotFoundError):
            # Fallback for platforms/filesystems where samefile is not available or file doesn't exist
            self.assertEqual(
                os.path.realpath(str(actual_path)),
                os.path.realpath(str(expected_path))
            )
        self.assertEqual(prompt_override.content, "Custom override initial plan prompt.")

        # Test definition
        prompt_definition = self.manager.get_prompt("project", "my_prompt")
        expected_path = self.temp_dir / "project_prompts/my_project_prompt.prompt.md"
        actual_path = prompt_definition.path
        try:
            self.assertTrue(os.path.samefile(actual_path, expected_path))
        except (AttributeError, FileNotFoundError):
            self.assertEqual(
                os.path.realpath(str(actual_path)),
                os.path.realpath(str(expected_path))
            )
        self.assertEqual(prompt_definition.content, "Project specific prompt.")

        # Test custom directory with default base path (should not be hit due to override)
        # To test this, we'd need a different prompt name or remove the override
        # Let's test a different custom prompt not overridden
        (self.prompts_dir / "custom" / "another_category").mkdir()
        (self.prompts_dir / "custom" / "another_category" / "test_custom.prompt.md").write_text("Another custom prompt.")
        # Temporarily remove the custom base path override to test default custom path
        original_custom_base = self.config_data["prompt_settings"]["base_paths"].pop("custom")
        config_default_custom = PromptConfiguration(self.config_data)
        manager_default_custom = PromptSystem(config_default_custom, self.temp_dir)
        prompt_default_custom = manager_default_custom.get_prompt("another_category", "test_custom")
        expected_path = self.prompts_dir / "custom/another_category/test_custom.prompt.md"
        actual_path = prompt_default_custom.path
        try:
            self.assertTrue(os.path.samefile(actual_path, expected_path))
        except (AttributeError, FileNotFoundError):
            self.assertEqual(
                os.path.realpath(str(actual_path)),
                os.path.realpath(str(expected_path))
            )
        self.assertEqual(prompt_default_custom.content, "Another custom prompt.")
        # Restore the config data
        self.config_data["prompt_settings"]["base_paths"]["custom"] = original_custom_base


        # Test agent directory
        prompt_agent = self.manager.get_prompt("agents", "code_generation")
        expected_path = self.prompts_dir / "agents/code_generation.prompt.md"
        actual_path = prompt_agent.path
        self.assertEqual(
            os.path.normcase(os.path.normpath(str(actual_path))),
            os.path.normcase(os.path.normpath(str(expected_path)))
        )
        self.assertEqual(prompt_agent.content, "Agent code generation prompt.")

        # Test core directory (should not be hit due to override)
        # To test this, we'd need a different prompt name or remove the override
        # Let's test subtask_generator which is not overridden
        (self.prompts_dir / "core" / "subtask_generator.prompt.md").write_text("Core subtask generator prompt.")
        prompt_core = self.manager.get_prompt("core", "subtask_generator")
        expected_path = self.prompts_dir / "core/subtask_generator.prompt.md"
        actual_path = prompt_core.path
        self.assertEqual(
            os.path.normcase(os.path.normpath(str(actual_path))),
            os.path.normcase(os.path.normpath(str(expected_path)))
        )
        self.assertEqual(prompt_core.content, "Core subtask generator prompt.")


    def test_lazy_loading(self):
        test_path = self.prompts_dir / "core" / "initial_plan.prompt.md"
        # Ensure the override is NOT in effect for this specific test to hit the core file
        config_no_override = PromptConfiguration({})
        manager_no_override = PromptSystem(config_no_override, self.temp_dir)

        prompt = manager_no_override.get_prompt("core", "initial_plan")

        # At this point, content should not be loaded yet
        self.assertIsNone(prompt._content)

        # Accessing content should trigger loading
        content = prompt.content
        self.assertEqual(content, "Core initial plan prompt.")
        self.assertIsNotNone(prompt._content) # Content should now be loaded

        # Accessing again should use the cached content
        with patch.object(self.manager._loader, 'load_prompt_content') as mock_load:
            content_again = prompt.content
            mock_load.assert_not_called() # Loading should not happen again
            self.assertEqual(content_again, "Core initial plan prompt.")

    def test_prompt_not_found(self):
        with self.assertRaises(PromptNotFoundError):
            self.manager.get_prompt("non_existent_category", "non_existent_prompt")

    def test_get_prompt_content_with_templating_integration(self):
        # Create a prompt file with placeholders
        template_content = "User: {{{user_name}}}\nTask: {{{task_description}}}"
        template_path = self.prompts_dir / "core" / "templated_prompt.prompt.md"
        template_path.write_text(template_content)

        # Temporarily add a definition for this template prompt
        original_definitions = self.config_data["prompt_settings"].get("definitions", {}).copy()
        self.config_data["prompt_settings"].setdefault("definitions", {})["core.templated_prompt"] = "prompts/core/templated_prompt.prompt.md"
        config_with_template = PromptConfiguration(self.config_data)
        manager_with_template = PromptSystem(config_with_template, self.temp_dir)

        # Use the correct method for templating (get_formatted_prompt)
        rendered_content = manager_with_template.get_formatted_prompt(
            "core",
            "templated_prompt",
            user_name="Roo",
            task_description="Write integration tests"
        )

        expected_content = "User: Roo\nTask: Write integration tests"
        self.assertEqual(rendered_content, expected_content)

        # Restore original definitions
        self.config_data["prompt_settings"]["definitions"] = original_definitions


if __name__ == '__main__':
    unittest.main()