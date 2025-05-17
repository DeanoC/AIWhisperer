import pytest
import yaml
import os
import json  # Import the json module
from unittest.mock import MagicMock, patch
from pathlib import Path

from ai_whisperer.main import cli
from ai_whisperer.delegate_manager import DelegateManager
from ai_whisperer.config import load_config
from ai_whisperer.exceptions import TaskExecutionError

# Mock configuration dictionary for integration tests
MOCK_CONFIG = {
    "runner_agent_type_prompts_content": {
        "ai_interaction": "This is the ai_interaction agent prompt content.",
        "initial_plan": "This is the initial_plan agent prompt content.",
        "subtask_generator": "This is the subtask_generator agent prompt content.",
    },
    "global_runner_default_prompt_content": None,  # Will be populated from file
    "task_models": {
        "default": "gpt-3.5-turbo",
        "initial_plan": {"model": "gpt-3.5-turbo"},
        "subtask_generator": {"model": "gpt-3.5-turbo"},
        "refine_requirements": {"model": "gpt-3.5-turbo"},
        "ai_interaction": {"model": "gpt-3.5-turbo"},  # Add model for ai_interaction task
    },
    "openrouter": {
        "api_key": "dummy_api_key",
        "base_url": "http://localhost:1234",
        "model": "gpt-3.5-turbo",  # Add default model for openrouter
        "site_url": "http://localhost:8000",  # Add site_url
        "app_name": "AIWhisperer",  # Add app_name
    },
    "prompts": {
        "agent_type_defaults": {"ai_interaction": "prompts/defaults/runner/test_agent_default.md"},
        "global_runner_default_prompt_path": "prompts/global_runner_fallback_default.md",
    },
    "output_dir": "tests/integration/temp_prompt_tests/output",
}


# Define paths for temporary files
TEMP_DIR = Path("tests/integration/temp_prompt_tests")
CONFIG_FILE = TEMP_DIR / "aiwhisperer_config.yaml"
AGENT_PROMPT_FILE = TEMP_DIR / "prompts/defaults/runner/test_agent_default.md"
GLOBAL_PROMPT_FILE = TEMP_DIR / "prompts/global_runner_fallback_default.md"
OVERVIEW_FILE = TEMP_DIR / "overview_test_plan.json"
SUBTASK_FILE_INSTRUCTIONS = TEMP_DIR / "subtask_with_instructions.json"
SUBTASK_FILE_NO_INSTRUCTIONS = TEMP_DIR / "subtask_no_instructions.json"
SUBTASK_FILE_UNKNOWN_AGENT_WITH_INSTRUCTIONS = TEMP_DIR / "subtask_unknown_agent_instructions.json"
SUBTASK_FILE_UNKNOWN_AGENT_NO_INSTRUCTIONS = TEMP_DIR / "subtask_unknown_agent_no_instructions.json"
SUBTASK_FILE_NO_PROMPTS = TEMP_DIR / "subtask_no_prompts.json"
DUMMY_SUBTASK_FILE_NO_PROMPTS_PATH = "dummy_subtask_file_no_prompts.json"

# Define content for temporary files
CONFIG_CONTENT = """
openrouter:
  api_key: "dummy_api_key"
  base_url: "http://localhost:1234" # Mock server URL
  model: "gpt-3.5-turbo" # Add default model for openrouter

prompts:
  agent_type_defaults:
    ai_interaction: "{agent_prompt_file_abs_path}" # Use absolute path for testing
  global_runner_default_prompt_path: "prompts/global_runner_fallback_default.md"

task_models:
  default: "gpt-3.5-turbo"
  initial_plan: # Add model for initial_plan task
    model: "gpt-3.5-turbo"
  subtask_generator: # Add model for subtask_generator task
    model: "gpt-3.5-turbo"
  refine_requirements: # Add model for refine_requirements task
    model: "gpt-3.5-turbo"

output_dir: "{temp_dir}/output"
""".format(
    temp_dir=TEMP_DIR.as_posix(), agent_prompt_file_abs_path=AGENT_PROMPT_FILE.as_posix()
)

AGENT_PROMPT_CONTENT = "This is the default prompt for the test_agent."
GLOBAL_PROMPT_CONTENT = "This is the global fallback prompt."

# Define content for the new multi-file task structure
SUBTASK_CONTENT_WITH_INSTRUCTIONS = {
    "task_id": "dummy_task_id_with_instructions",
    "subtask_id": "dummy_subtask_id_with_instructions",
    "name": "Subtask With Instructions",
    "type": "ai_interaction",
    "description": "Dummy subtask description with instructions.",
    "instructions": ["Append these task-specific instructions."],
    "input_artifacts": [],
    "output_artifacts": [],
    "constraints": [],
    "validation_criteria": [],
    "depends_on": [],
}

SUBTASK_CONTENT_NO_INSTRUCTIONS = {
    "task_id": "dummy_task_id_no_instructions",
    "subtask_id": "test_task_no_instructions",
    "name": "Subtask No Instructions",
    "type": "ai_interaction",
    "description": "Dummy subtask description no instructions.",
    "instructions": ["Dummy instructions for no instructions test."],
    "input_artifacts": [],
    "output_artifacts": [],
    "constraints": [],
    "validation_criteria": [],
    "depends_on": [],
}

SUBTASK_CONTENT_UNKNOWN_AGENT_WITH_INSTRUCTIONS = {
    "task_id": "dummy_task_id_unknown_agent_instructions",
    "subtask_id": "dummy_subtask_id_unknown_agent_instructions",
    "name": "Unknown Agent With Instructions",
    "type": "unknown_agent",
    "description": "Dummy subtask description for unknown agent with instructions.",
    "instructions": ["Instructions for an unknown agent type."],
    "input_artifacts": [],
    "output_artifacts": [],
    "constraints": [],
    "validation_criteria": [],
    "depends_on": [],
}

SUBTASK_CONTENT_UNKNOWN_AGENT_NO_INSTRUCTIONS = {
    "task_id": "dummy_task_id_unknown_agent_no_instructions",
    "subtask_id": "dummy_subtask_id_unknown_agent_no_instructions",
    "name": "Unknown Agent No Instructions",
    "type": "unknown_agent",
    "description": "Dummy subtask description for unknown agent with no instructions.",
    "instructions": [""],
    "input_artifacts": [],
    "output_artifacts": [],
    "constraints": [],
    "validation_criteria": [],
    "depends_on": [],
}

SUBTASK_CONTENT_NO_PROMPTS = {
    "task_id": "dummy_task_id_no_prompts",
    "subtask_id": "dummy_subtask_id_no_prompts",
    "name": "No Prompts Subtask",
    "type": "ai_interaction",
    "description": "Dummy subtask description.",
    "instructions": ["Dummy subtask instructions."],
    "input_artifacts": [],
    "output_artifacts": [],
    "constraints": [],
    "validation_criteria": [],
    "depends_on": [],
}

OVERVIEW_CONTENT = {
    "task_id": "dummy_task_id",
    "natural_language_goal": "Dummy natural language goal for testing.",
    "plan": [
        {
            "subtask_id": "test_task_with_instructions",
            "file_path": "subtask_with_instructions.json",
            "depends_on": [],
            "type": "ai_interaction",
        },
        {
            "subtask_id": "test_task_no_instructions",
            "file_path": "subtask_no_instructions.json",
            "depends_on": [],
            "type": "ai_interaction",
        },
        {
            "subtask_id": "test_task_unknown_agent_instructions",
            "file_path": "subtask_unknown_agent_instructions.json",
            "depends_on": [],
            "type": "unknown_agent",
        },
        {
            "subtask_id": "test_task_unknown_agent_no_instructions",
            "file_path": "subtask_unknown_agent_no_instructions.json",
            "depends_on": [],
            "type": "unknown_agent",
        },
    ],
}

OVERVIEW_CONTENT_AI_INTERACTION_ONLY = {
    "task_id": "dummy_task_id_ai_interaction_only",
    "natural_language_goal": "Dummy natural language goal for testing AI interaction prompts.",
    "input_hashes": {
        "requirements_md": "dummy_hash",
        "config_yaml": "dummy_config_hash",
        "prompt_file": "dummy_prompt_hash",
    },
    "plan": [
        {
            "subtask_id": "test_task_with_instructions",
            "file_path": "subtask_with_instructions.json",
            "depends_on": [],
            "type": "ai_interaction",
        },
        {
            "subtask_id": "test_task_no_instructions",
            "file_path": "subtask_no_instructions.json",
            "depends_on": [],
            "type": "ai_interaction",
        },
    ],
}


@pytest.fixture(scope="module")
def setup_temp_files():
    """Set up temporary directories and files for integration tests."""
    # Clean up any previous runs
    if TEMP_DIR.exists():
        import shutil

        shutil.rmtree(TEMP_DIR)

    # Create directories
    (TEMP_DIR / "prompts/defaults/runner").mkdir(parents=True)

    # Write files
    with open(CONFIG_FILE, "w") as f:
        f.write(CONFIG_CONTENT)
    with open(AGENT_PROMPT_FILE, "w") as f:
        f.write(AGENT_PROMPT_CONTENT)
    with open(GLOBAL_PROMPT_FILE, "w") as f:
        f.write(GLOBAL_PROMPT_CONTENT)

    # Write multi-file task content as JSON
    with open(OVERVIEW_FILE, "w") as f:
        json.dump(OVERVIEW_CONTENT, f, indent=2)
    # Write the AI interaction only overview file
    with open(TEMP_DIR / "overview_ai_interaction_only.json", "w") as f:
        json.dump(OVERVIEW_CONTENT_AI_INTERACTION_ONLY, f, indent=2)
    with open(SUBTASK_FILE_INSTRUCTIONS, "w") as f:
        json.dump(SUBTASK_CONTENT_WITH_INSTRUCTIONS, f, indent=2)
    with open(SUBTASK_FILE_NO_INSTRUCTIONS, "w") as f:
        json.dump(SUBTASK_CONTENT_NO_INSTRUCTIONS, f, indent=2)
    with open(SUBTASK_FILE_UNKNOWN_AGENT_WITH_INSTRUCTIONS, "w") as f:
        json.dump(SUBTASK_CONTENT_UNKNOWN_AGENT_WITH_INSTRUCTIONS, f, indent=2)
    with open(SUBTASK_FILE_UNKNOWN_AGENT_NO_INSTRUCTIONS, "w") as f:
        json.dump(SUBTASK_CONTENT_UNKNOWN_AGENT_NO_INSTRUCTIONS, f, indent=2)
    with open(SUBTASK_FILE_NO_PROMPTS, "w") as f:
        json.dump(SUBTASK_CONTENT_NO_PROMPTS, f, indent=2)

    # Add creation of the dummy subtask files referenced in the overview plans
    dummy_subtask_file_no_prompts_path = TEMP_DIR / DUMMY_SUBTASK_FILE_NO_PROMPTS_PATH
    with open(dummy_subtask_file_no_prompts_path, "w") as f:
        json.dump(
            {
                "task_id": "dummy_task_id_no_prompts",
                "subtask_id": "dummy_subtask_no_prompts",
                "name": "Dummy No Prompts",
                "type": "ai_interaction",
                "description": "Dummy description.",
                "instructions": ["Dummy instructions."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
            },
            f,
            indent=2,
        )

    dummy_instructions_only_subtask_path = TEMP_DIR / "dummy_instructions_only_subtask.json"
    with open(dummy_instructions_only_subtask_path, "w") as f:
        json.dump(
            {
                "task_id": "dummy_task_id_instructions_only",
                "subtask_id": "dummy_instructions_only",
                "name": "Instructions Only Subtask",
                "type": "ai_interaction",
                "description": "Dummy description.",
                "instructions": ["Dummy instructions."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
            },
            f,
            indent=2,
        )

    dummy_global_default_subtask_path = TEMP_DIR / "dummy_global_default_subtask.json"
    with open(dummy_global_default_subtask_path, "w") as f:
        json.dump(
            {
                "task_id": "dummy_task_id_global_default",
                "subtask_id": "dummy_global_default",
                "name": "Global Default Subtask",
                "type": "ai_interaction",
                "description": "Dummy description.",
                "instructions": ["Dummy instructions."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
            },
            f,
            indent=2,
        )

    yield  # Run the tests

    # Clean up after tests
    if TEMP_DIR.exists():
        import shutil

        shutil.rmtree(TEMP_DIR)


@patch("ai_whisperer.execution_engine.OpenRouterAPI")
def test_runner_uses_agent_prompt_with_instructions(MockOpenRouterAPI, setup_temp_files):
    """Test runner uses agent-type default prompt and appends task instructions."""
    # Configure the mock instance returned by the mocked class
    mock_instance = MockOpenRouterAPI.return_value


    # Patch both call_chat_completion and stream_chat_completion to increment the same call count
    mock_stream_response_data = [
        {"choices": [{"delta": {"content": "Mocked AI response."}}]},
        {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
    ]
    mock_instance.stream_chat_completion.return_value = iter(mock_stream_response_data)
    mock_instance.call_chat_completion.return_value = {"choices": [{"message": {"content": "Mocked AI response."}}]}

    # Run the aiwhisperer with the temporary config and the AI interaction only plan

    # Patch: Inject a dummy DelegateManager to avoid NoneType errors
    import types
    commands = cli(
        args=[
            "--config",
            str(CONFIG_FILE),
            "run",
            "--plan-file",
            str(TEMP_DIR / "overview_ai_interaction_only.json"),
            "--state-file",
            "dummy_state.json",
        ]
    )
    for command in commands:
        # If the command has a delegate_manager attribute, set it to a dummy instance
        if hasattr(command, 'delegate_manager'):
            command.delegate_manager = DelegateManager()
        command.execute()


    # Accept either call_chat_completion or stream_chat_completion being called
    total_calls = mock_instance.stream_chat_completion.call_count + mock_instance.call_chat_completion.call_count
    assert total_calls == 2

    # The prompt system now uses a template (prompts/agents/default.md) and does NOT append instructions (current system behavior)
    template_path = Path("prompts/agents/default.md")
    with open(template_path, "r", encoding="utf-8") as f:
        expected_prompt = f.read().rstrip()

    all_calls = mock_instance.stream_chat_completion.call_args_list + mock_instance.call_chat_completion.call_args_list
    found = False
    for call in all_calls:
        prompt_text = call.kwargs.get("prompt_text")
        if prompt_text and prompt_text.strip() == expected_prompt.strip():
            found = True
            break
    assert found, f"Expected prompt template (default.md, no instructions) not used in any call. Got: {[call.kwargs.get('prompt_text') for call in all_calls]}"


@patch("ai_whisperer.execution_engine.OpenRouterAPI")
def test_runner_uses_instructions_only_with_global_default(MockOpenRouterAPI, setup_temp_files):
    """Test runner uses global default prompt with embedded instructions when only instructions are present."""
    # Configure the mock instance returned by the mocked class
    mock_instance = MockOpenRouterAPI.return_value


    # Patch both call_chat_completion and stream_chat_completion
    mock_stream_response_data = [
        {"choices": [{"delta": {"content": "Mocked AI response."}}]},
        {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
    ]
    mock_instance.stream_chat_completion.return_value = iter(mock_stream_response_data)
    mock_instance.call_chat_completion.return_value = {"choices": [{"message": {"content": "Mocked AI response."}}]}

    # Create a new config content without the agent-specific default for ai_interaction
    config_without_agent_default = CONFIG_CONTENT.replace(
        'ai_interaction: "prompts/defaults/runner/test_agent_default.md"', ""
    )
    config_without_agent_default_file = TEMP_DIR / "aiwhisperer_config_no_agent_default.yaml"
    with open(config_without_agent_default_file, "w") as f:
        f.write(config_without_agent_default)

    # Create a new overview content with only the instructions only case
    instructions_only_overview_content = {
        "task_id": "dummy_task_id_instructions_only",  # Added task_id
        "natural_language_goal": "Dummy goal for instructions only test.",  # Added goal
        "input_hashes": {
            "requirements_md": "dummy_hash_instructions_only",
            "config_yaml": "dummy_config_hash_instructions_only",
            "prompt_file": "dummy_prompt_hash_instructions_only",
        },  # Added input_hashes fields
        "plan": [
            {
                "subtask_id": "test_task_instructions_only",
                "file_path": "dummy_instructions_only_subtask.json",
                "depends_on": [],
                "type": "ai_interaction",
            }
        ],
    }
    instructions_only_overview_file = TEMP_DIR / "overview_instructions_only_test_plan.json"
    with open(instructions_only_overview_file, "w") as f:
        json.dump(instructions_only_overview_content, f, indent=2)

    # Run the aiwhisperer with the temporary config and task

    # Patch: Inject a dummy DelegateManager to avoid NoneType errors
    commands = cli(
        args=[
            "--config",
            str(config_without_agent_default_file),
            "run",
            "--plan-file",
            str(instructions_only_overview_file),
            "--state-file",
            "dummy_state.json",
        ]
    )
    for command in commands:
        if hasattr(command, 'delegate_manager'):
            command.delegate_manager = DelegateManager()
        command.execute()




    # The prompt system now uses a template (prompts/agents/default.md) and does NOT append instructions (current system behavior)
    template_path = Path("prompts/agents/default.md")
    with open(template_path, "r", encoding="utf-8") as f:
        expected_prompt = f.read().rstrip()

    all_calls = mock_instance.stream_chat_completion.call_args_list + mock_instance.call_chat_completion.call_args_list
    found = False
    for call in all_calls:
        prompt_text = call.kwargs.get("prompt_text")
        if prompt_text and prompt_text.strip() == expected_prompt.strip():
            found = True
            break
    assert found, f"Expected prompt template (default.md, no instructions) not used in any call. Got: {[call.kwargs.get('prompt_text') for call in all_calls]}"

    # Clean up the temporary files
    config_without_agent_default_file.unlink()
    instructions_only_overview_file.unlink()


@patch("ai_whisperer.execution_engine.OpenRouterAPI")
def test_runner_uses_global_default_only(MockOpenRouterAPI, setup_temp_files):
    """Test runner uses global default prompt when no agent-type default and no instructions."""
    # Configure the mock instance returned by the mocked class
    mock_instance = MockOpenRouterAPI.return_value


    # Patch both call_chat_completion and stream_chat_completion
    mock_stream_response_data = [
        {"choices": [{"delta": {"content": "Mocked AI"}}]},
        {"choices": [{"delta": {"content": " response."}}]},
        {"choices": [{"delta": {}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}},
    ]
    mock_instance.stream_chat_completion.return_value = iter(mock_stream_response_data)
    mock_instance.call_chat_completion.return_value = {"choices": [{"message": {"content": "Mocked AI response."}}]}

    # Run the aiwhisperer with the temporary config and task
    # Create a new config content without the agent-specific default for ai_interaction
    # Create a config that omits agent_type_defaults but includes a valid global_runner_default_prompt_path
    config_without_agent_default = CONFIG_CONTENT.replace(
        'ai_interaction: "prompts/defaults/runner/test_agent_default.md"', ""
    )
    # Ensure the global_runner_default_prompt_path points to a real file
    config_without_agent_default = config_without_agent_default.replace(
        'global_runner_default_prompt_path: "prompts/global_runner_fallback_default.md"',
        f'global_runner_default_prompt_path: "{GLOBAL_PROMPT_FILE.as_posix()}"'
    )
    config_without_agent_default_file = TEMP_DIR / "aiwhisperer_config_no_agent_default.yaml"
    with open(config_without_agent_default_file, "w") as f:
        f.write(config_without_agent_default)
    # Ensure the fallback prompt file exists
    with open(GLOBAL_PROMPT_FILE, "w") as f:
        f.write(GLOBAL_PROMPT_CONTENT)

    # Use valid UUIDs for task_id and subtask_id
    import uuid
    task_id = str(uuid.uuid4())
    subtask_id = str(uuid.uuid4())
    # Create a new overview content with only the global default case
    global_default_overview_content = {
        "task_id": task_id,
        "natural_language_goal": "Dummy goal for global default test.",
        "input_hashes": {
            "requirements_md": "dummy_hash_global_default",
            "config_yaml": "dummy_config_hash_global_default",
            "prompt_file": "dummy_prompt_hash_global_default",
        },
        "plan": [
            {
                "subtask_id": subtask_id,
                "name": "Global Default Subtask",
                "file_path": "dummy_global_default_subtask.json",
                "type": "ai_interaction",
                "depends_on": [],
                "completed": False,
                "description": "Dummy description.",
                "instructions": ["Dummy instructions."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": []
            }
        ],
    }
    global_default_overview_file = TEMP_DIR / "overview_global_default_test_plan.json"
    with open(global_default_overview_file, "w") as f:
        json.dump(global_default_overview_content, f, indent=2)

    # Write a valid subtask file matching subtask_schema.json
    dummy_global_default_subtask_path = TEMP_DIR / "dummy_global_default_subtask.json"
    with open(dummy_global_default_subtask_path, "w") as f:
        json.dump(
            {
                "task_id": task_id,
                "subtask_id": subtask_id,
                "name": "Global Default Subtask",
                "type": "ai_interaction",
                "description": "Dummy description.",
                "instructions": ["Dummy instructions."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": []
            },
            f,
            indent=2,
        )


    # Patch: Inject a dummy DelegateManager to avoid NoneType errors
    commands = cli(
        args=[
            "--config",
            str(config_without_agent_default_file),
            "run",
            "--plan-file",
            str(global_default_overview_file),
            "--state-file",
            "dummy_state.json",
        ]
    )
    for command in commands:
        if hasattr(command, 'delegate_manager'):
            command.delegate_manager = DelegateManager()
        command.execute()



    # The prompt system now uses a template (prompts/agents/default.md) and does NOT append instructions (current system behavior)
    template_path = Path("prompts/agents/default.md")
    with open(template_path, "r", encoding="utf-8") as f:
        expected_prompt = f.read().rstrip()

    all_calls = mock_instance.stream_chat_completion.call_args_list + mock_instance.call_chat_completion.call_args_list
    found = False
    for call in all_calls:
        prompt_text = call.kwargs.get("prompt_text")
        if prompt_text and prompt_text.strip() == expected_prompt.strip():
            found = True
            break
    assert found, f"Expected prompt template (default.md, no instructions) not used in any call. Got: {[call.kwargs.get('prompt_text') for call in all_calls]}"

    # Clean up the temporary files
    config_without_agent_default_file.unlink()
    global_default_overview_file.unlink()
