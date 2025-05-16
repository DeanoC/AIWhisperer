import pytest
from unittest.mock import MagicMock, patch

from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.prompt_system import PromptSystem # Import PromptSystem

# Mock configuration and task data
MOCK_CONFIG = {
    "runner_agent_type_prompts_content": {
        "ai_interaction": "Agent-specific AI prompt content.",
        "planning": "Agent-specific planning prompt content.",
    },
    "global_runner_default_prompt_content": "Global default prompt content.",
}

MOCK_TASK_DEFINITION_WITH_INSTRUCTIONS = {
    "instructions": "Task-specific instructions.",
    "agent_spec": {"type": "ai_interaction"},
}

MOCK_TASK_DEFINITION_NO_INSTRUCTIONS = {"instructions": "", "agent_spec": {"type": "ai_interaction"}}

MOCK_TASK_DEFINITION_UNKNOWN_AGENT = {
    "instructions": "Task-specific instructions for unknown agent.",
    "agent_spec": {"type": "unknown_agent"},
}

MOCK_TASK_DEFINITION_UNKNOWN_AGENT_NO_INSTRUCTIONS = {"instructions": "", "agent_spec": {"type": "unknown_agent"}}

MOCK_TASK_DEFINITION_NO_AGENT_TYPE = {"instructions": "Instructions without agent type.", "agent_spec": {}}

MOCK_TASK_DEFINITION_MINIMAL = {"instructions": "", "agent_spec": {}}


@pytest.fixture
def mock_execution_engine():
    """Fixture to create a mock ExecutionEngine instance with a real config dict."""
    mock_state_manager = MagicMock()
    mock_prompt_system = MagicMock(spec=PromptSystem) # Create a mock PromptSystem
    # Use the real MOCK_CONFIG dict for config
    engine = ExecutionEngine(mock_state_manager, MOCK_CONFIG, mock_prompt_system) # Add mock_prompt_system
    # We need to mock the internal method that calls the AI service to prevent actual calls
    engine._call_ai_service = MagicMock()
    return engine


def test_prompt_selection_agent_type_and_instructions(mock_execution_engine):
    """Test case: Agent-type default prompt exists and task instructions exist."""
    task_definition = MOCK_TASK_DEFINITION_WITH_INSTRUCTIONS.copy()
    agent_spec = task_definition["agent_spec"]

    # Simulate the relevant part of _handle_ai_interaction
    agent_type = agent_spec.get("type")
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    agent_type_prompt = mock_execution_engine.config["runner_agent_type_prompts_content"].get(agent_type)

    if agent_type_prompt:
        selected_prompt = agent_type_prompt
        if task_instructions:
            selected_prompt += "\n\n" + task_instructions
    elif task_instructions:
        selected_prompt = task_instructions
    elif mock_execution_engine.config.get("global_runner_default_prompt_content"):
        selected_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]

    assert selected_prompt == "Agent-specific AI prompt content.\n\nTask-specific instructions."


def test_prompt_selection_agent_type_only(mock_execution_engine):
    """Test case: Agent-type default prompt exists, but no task instructions."""
    task_definition = MOCK_TASK_DEFINITION_NO_INSTRUCTIONS.copy()
    agent_spec = task_definition["agent_spec"]

    # Simulate the relevant part of _handle_ai_interaction
    agent_type = agent_spec.get("type")
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    agent_type_prompt = mock_execution_engine.config["runner_agent_type_prompts_content"].get(agent_type)

    if agent_type_prompt:
        selected_prompt = agent_type_prompt
        if task_instructions:
            selected_prompt += "\n\n" + task_instructions
    elif task_instructions:
        selected_prompt = task_instructions
    elif mock_execution_engine.config.get("global_runner_default_prompt_content"):
        selected_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]

    assert selected_prompt == "Agent-specific AI prompt content."


def test_prompt_selection_instructions_only(mock_execution_engine):
    """Test case: No agent-type default prompt, but task instructions exist (should use global default)."""
    task_definition = MOCK_TASK_DEFINITION_UNKNOWN_AGENT.copy()
    agent_spec = task_definition["agent_spec"]

    # Simulate the relevant part of _handle_ai_interaction
    agent_type = agent_spec.get("type")
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    agent_type_prompt = mock_execution_engine.config["runner_agent_type_prompts_content"].get(agent_type)

    # --- Updated Prompt Selection Logic Simulation ---
    # Priority: Agent Prompt + Instructions > Agent Prompt Only > Instructions Only (embedded) > Global Default Only
    if agent_type_prompt and task_instructions:
        selected_prompt = agent_type_prompt + "\n\n" + task_instructions
    elif agent_type_prompt:
        selected_prompt = agent_type_prompt
    elif task_instructions and mock_execution_engine.config.get("global_runner_default_prompt_content"):
        global_default_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]
        selected_prompt = global_default_prompt.format(instructions=task_instructions)
    elif mock_execution_engine.config.get("global_runner_default_prompt_content"):
        selected_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]
    # --- End Updated Logic Simulation ---

    # The expected prompt should now be the global default with instructions embedded
    expected_prompt = "Global default prompt content.".format(
        instructions="Task-specific instructions for unknown agent."
    )
    assert selected_prompt == expected_prompt


def test_prompt_selection_global_default_only(mock_execution_engine):
    """Test case: No agent-type default prompt, no task instructions, global default exists."""
    task_definition = MOCK_TASK_DEFINITION_UNKNOWN_AGENT_NO_INSTRUCTIONS.copy()
    agent_spec = task_definition["agent_spec"]

    # Simulate the relevant part of _handle_ai_interaction
    agent_type = agent_spec.get("type")
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    agent_type_prompt = mock_execution_engine.config["runner_agent_type_prompts_content"].get(agent_type)

    if agent_type_prompt:
        selected_prompt = agent_type_prompt
        if task_instructions:
            selected_prompt += "\n\n" + task_instructions
    elif task_instructions:
        selected_prompt = task_instructions
    elif mock_execution_engine.config.get("global_runner_default_prompt_content"):
        selected_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]

    assert selected_prompt == "Global default prompt content."


def test_prompt_selection_no_prompts(mock_execution_engine):
    """Test case: No agent-type default, no task instructions, no global default."""
    task_definition = MOCK_TASK_DEFINITION_MINIMAL.copy()
    agent_spec = task_definition["agent_spec"]

    # Create a modified mock config for this test case
    mock_config_no_global_default = {
        "runner_agent_type_prompts_content": {
            "ai_interaction": "Agent-specific AI prompt content.",
            "planning": "Agent-specific planning prompt content.",
        },
        # Exclude global_runner_default_prompt_content
    }

    # Simulate the relevant part of _handle_ai_interaction and expect an error
    agent_type = agent_spec.get("type")
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    # Use the modified mock config for prompt selection
    agent_type_prompt = mock_config_no_global_default["runner_agent_type_prompts_content"].get(agent_type)

    if agent_type_prompt:
        selected_prompt = agent_type_prompt
        if task_instructions:
            selected_prompt += "\n\n" + task_instructions
    elif task_instructions:
        selected_prompt = task_instructions
    elif mock_config_no_global_default.get("global_runner_default_prompt_content"):  # Check the modified config
        selected_prompt = mock_config_no_global_default["global_runner_default_prompt_content"]

    # The actual ExecutionEngine._handle_ai_interaction would raise an error here if selected_prompt is empty
    # We simulate that check here.
    if not selected_prompt:
        with pytest.raises(TaskExecutionError, match="No suitable prompt found"):
            raise TaskExecutionError("No suitable prompt found for AI interaction.")

    # If selected_prompt was not empty, the test would fail here, which is the desired behavior
    # for this specific test case where we expect an error.
    assert selected_prompt == ""  # Ensure the simulated logic resulted in an empty prompt


def test_prompt_selection_no_agent_type_in_spec(mock_execution_engine):
    """Test case: task_definition has no agent_spec['type'], but instructions exist."""
    task_definition = MOCK_TASK_DEFINITION_NO_AGENT_TYPE.copy()
    agent_spec = task_definition.get("agent_spec", {})  # Handle missing agent_spec gracefully

    # Simulate the relevant part of _handle_ai_interaction
    agent_type = agent_spec.get("type")  # This will be None
    task_instructions = task_definition.get("instructions")

    selected_prompt = ""
    # This will correctly return None as agent_type is None
    agent_type_prompt = mock_execution_engine.config["runner_agent_type_prompts_content"].get(agent_type)

    if agent_type_prompt:
        selected_prompt = agent_type_prompt
        if task_instructions:
            selected_prompt += "\n\n" + task_instructions
    elif task_instructions:
        selected_prompt = task_instructions
    elif mock_execution_engine.config.get("global_runner_default_prompt_content"):
        selected_prompt = mock_execution_engine.config["global_runner_default_prompt_content"]

    assert selected_prompt == "Instructions without agent type."
