"""
Tests to verify that specific rules related to fixed items have been removed
from the default initial plan and subtask generator prompts.
"""

import pytest
from pathlib import Path

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Paths to the prompt files
INITIAL_PLAN_PROMPT_PATH = PROJECT_ROOT / "prompts" / "initial_plan_default.md"
SUBTASK_GENERATOR_PROMPT_PATH = PROJECT_ROOT / "prompts" / "subtask_generator_default.md"


def read_prompt_file(file_path):
    """Read the content of a prompt file, trying both old and new locations."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Try the new location if the old one is missing
        if file_path.name == "initial_plan_default.md":
            alt_path = file_path.parent / "core" / "initial_plan.prompt.md"
        elif file_path.name == "subtask_generator_default.md":
            alt_path = file_path.parent / "core" / "subtask_generator.prompt.md"
        else:
            alt_path = None
        if alt_path and alt_path.exists():
            with open(alt_path, "r", encoding="utf-8") as f:
                return f.read()
        pytest.skip(f"Prompt file not found: {file_path} or {alt_path}")
        return ""


class TestInitialPlanPromptRules:
    """Tests for the initial plan prompt rules."""

    def test_input_hashes_rule_removed(self):
        """Test that the rule requiring input_hashes has been removed."""
        prompt_content = read_prompt_file(INITIAL_PLAN_PROMPT_PATH)

        # Check for absence of the specific rule text
        assert (
            "You MUST include the input_hashes dictionary exactly as provided in your YAML output" not in prompt_content
        )
        assert (
            "input_hashes: The dictionary of SHA-256 hashes provided in the prompt (MUST be included exactly as provided)"
            not in prompt_content
        )

    def test_task_id_rule_removed(self):
        """Test that the rule requiring task_id generation has been removed."""
        prompt_content = read_prompt_file(INITIAL_PLAN_PROMPT_PATH)

        # Check for absence of the specific rule text
        assert "task_id: A unique identifier for this task (generate a UUID)" not in prompt_content


class TestSubtaskGeneratorPromptRules:
    """Tests for the subtask generator prompt rules."""

    def test_subtask_id_rule_removed(self):
        """Test that the rule requiring subtask_id preservation has been removed."""
        prompt_content = read_prompt_file(SUBTASK_GENERATOR_PROMPT_PATH)

        # Check for absence of the specific rule text
        assert "You MUST preserve the subtask_id from the input YAML in your output" not in prompt_content
        assert "subtask_id: The unique identifier for this step (MUST match the input subtask_id)" not in prompt_content


def test_initial_plan_prompt_exists():
    """Test that the initial plan prompt file exists."""
    # Accept either the new or old location for the prompt file
    if not INITIAL_PLAN_PROMPT_PATH.exists():
        # Try the new location
        alt_path = PROJECT_ROOT / "prompts" / "core" / "initial_plan.prompt.md"
        assert alt_path.exists(), f"Initial plan prompt file not found at {INITIAL_PLAN_PROMPT_PATH} or {alt_path}"


def test_subtask_generator_prompt_exists():
    """Test that the subtask generator prompt file exists."""
    # Accept either the new or old location for the prompt file
    if not SUBTASK_GENERATOR_PROMPT_PATH.exists():
        alt_path = PROJECT_ROOT / "prompts" / "core" / "subtask_generator.prompt.md"
        assert alt_path.exists(), f"Subtask generator prompt file not found at {SUBTASK_GENERATOR_PROMPT_PATH} or {alt_path}"
