"""
Tests to verify that specific rules related to fixed items have been removed
from the default orchestrator and subtask generator prompts.
"""

import pytest
from pathlib import Path

# Define the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Paths to the prompt files
ORCHESTRATOR_PROMPT_PATH = PROJECT_ROOT / "prompts" / "orchestrator_default.md"
SUBTASK_GENERATOR_PROMPT_PATH = PROJECT_ROOT / "prompts" / "subtask_generator_default.md"

def read_prompt_file(file_path):
    """Read the content of a prompt file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        pytest.skip(f"Prompt file not found: {file_path}")
        return ""

class TestOrchestratorPromptRules:
    """Tests for the orchestrator prompt rules."""
    
    def test_input_hashes_rule_removed(self):
        """Test that the rule requiring input_hashes has been removed."""
        prompt_content = read_prompt_file(ORCHESTRATOR_PROMPT_PATH)
        
        # Check for absence of the specific rule text
        assert "You MUST include the input_hashes dictionary exactly as provided in your YAML output" not in prompt_content
        assert "input_hashes: The dictionary of SHA-256 hashes provided in the prompt (MUST be included exactly as provided)" not in prompt_content
    
    def test_task_id_rule_removed(self):
        """Test that the rule requiring task_id generation has been removed."""
        prompt_content = read_prompt_file(ORCHESTRATOR_PROMPT_PATH)
        
        # Check for absence of the specific rule text
        assert "task_id: A unique identifier for this task (generate a UUID)" not in prompt_content

class TestSubtaskGeneratorPromptRules:
    """Tests for the subtask generator prompt rules."""
    
    def test_step_id_rule_removed(self):
        """Test that the rule requiring step_id preservation has been removed."""
        prompt_content = read_prompt_file(SUBTASK_GENERATOR_PROMPT_PATH)
        
        # Check for absence of the specific rule text
        assert "You MUST preserve the step_id from the input YAML in your output" not in prompt_content
        assert "step_id: The unique identifier for this step (MUST match the input step_id)" not in prompt_content

def test_orchestrator_prompt_exists():
    """Test that the orchestrator prompt file exists."""
    assert ORCHESTRATOR_PROMPT_PATH.exists(), f"Orchestrator prompt file not found at {ORCHESTRATOR_PROMPT_PATH}"

def test_subtask_generator_prompt_exists():
    """Test that the subtask generator prompt file exists."""
    assert SUBTASK_GENERATOR_PROMPT_PATH.exists(), f"Subtask generator prompt file not found at {SUBTASK_GENERATOR_PROMPT_PATH}"
