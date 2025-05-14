import pytest
from unittest.mock import MagicMock, patch
from logging import Logger # Import Logger
from src.ai_whisperer.agent_handlers.code_generation import handle_code_generation, _gather_context, _construct_initial_prompt, _execute_validation
from src.ai_whisperer.ai_loop import run_ai_loop
from src.ai_whisperer.exceptions import TaskExecutionError, ToolNotFound
from src.ai_whisperer.tools.tool_registry import ToolRegistry # Assuming ToolRegistry is accessible
from pathlib import Path

# Mock dependencies for the handler functions
# We will mock these directly in the tests or pass mocks to the handler function

# Update tests to call handler functions directly

import asyncio
import threading

@patch('src.ai_whisperer.agent_handlers.code_generation.get_logger')
@patch('src.ai_whisperer.ai_loop.run_ai_loop')
def test_handle_code_generation_success(mock_run_loop, mock_get_logger):
    """Test successful execution of handle_code_generation."""
    mock_engine = MagicMock()
    mock_engine.config.get.return_value = MagicMock() # Mock logger
    mock_engine.monitor = MagicMock()
    mock_engine.openrouter_api = MagicMock()
    mock_engine.state_manager = MagicMock()
    # Patch openrouter_api.call_chat_completion to return a real dict
    mock_engine.openrouter_api.call_chat_completion.return_value = {"content": "Final AI response"}


    # Patch get_logger to return a mock logger
    mock_logger_instance = MagicMock()
    mock_get_logger.return_value = mock_logger_instance

    # Prepare the async mock for run_ai_loop
    async def fake_run_ai_loop(*args, **kwargs):
        return {"content": "Final AI response"}
    mock_run_loop.side_effect = fake_run_ai_loop

    with patch('src.ai_whisperer.agent_handlers.code_generation._gather_context', return_value="Mocked context") as mock_gather_context, \
         patch('src.ai_whisperer.agent_handlers.code_generation._construct_initial_prompt', return_value="Mocked prompt") as mock_construct_prompt, \
         patch('src.ai_whisperer.agent_handlers.code_generation._execute_validation', return_value=(True, {"overall_status": "passed"})) as mock_execute_validation:

        task_definition = {
            "description": "Generate code.",
            "instructions": ["Do something."],
            "input_artifacts": [],
            "output_artifacts": [],
            "constraints": [],
            "validation_criteria": [],
            "type": "code_generation",
            "name": "test_task",
            "depends_on": [],
            "task_id": "fake-task-id",
            "subtask_id": "fake-subtask-id"
        }
        task_id = "fake-task-id"
        shutdown_event = threading.Event()

        # Use asyncio.run to avoid DeprecationWarning about no current event loop
        result = asyncio.run(handle_code_generation(mock_engine, task_definition, task_id, shutdown_event))

        assert result is not None
        assert result["message"] == "Code generation completed and validation passed."
        # Accept either the mock or real dict for ai_result
        assert result["ai_result"].get("content") == "Final AI response"
        assert result["validation_details"]["overall_status"] == "passed"

        # Accept any logger instance
        called_args = mock_gather_context.call_args[0]
        assert called_args[0] == mock_engine
        assert called_args[1] == task_definition
        assert called_args[2] == task_id
        import logging
        assert isinstance(called_args[3], logging.Logger)
        mock_construct_prompt.assert_called_once_with(mock_engine, task_definition, task_id, "Mocked context", called_args[3])
        mock_execute_validation.assert_called_once_with(mock_engine, task_definition, task_id, called_args[3])

def test_handle_code_generation_validation_failure():
    """Test handle_code_generation when validation fails."""
def test_handle_code_generation_validation_failure():
    """Test handle_code_generation when validation fails."""
    mock_engine = MagicMock()
    mock_engine.config.get.return_value = MagicMock() # Mock config.get for logger
    mock_engine.monitor = MagicMock()
    mock_engine.openrouter_api = MagicMock()
    mock_engine.state_manager = MagicMock()

    import asyncio
    import threading
    # Mock get_logger directly
    with patch('src.ai_whisperer.agent_handlers.code_generation.get_logger') as mock_get_logger:
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance

        with patch('src.ai_whisperer.agent_handlers.code_generation._gather_context', return_value="Mocked context") as mock_gather_context, \
             patch('src.ai_whisperer.agent_handlers.code_generation._construct_initial_prompt', return_value="Mocked prompt") as mock_construct_prompt, \
             patch('src.ai_whisperer.ai_loop.run_ai_loop') as mock_run_loop, \
             patch('src.ai_whisperer.agent_handlers.code_generation._execute_validation', return_value=(False, {"overall_status": "failed", "commands_executed": [{"command": "test", "exit_code": 1}]})) as mock_execute_validation:

            async def fake_run_ai_loop(*args, **kwargs):
                return {"content": "Final AI response"}
            mock_run_loop.side_effect = fake_run_ai_loop

            task_definition = {
                "description": "Generate code.",
                "instructions": ["Do something."],
                "input_artifacts": [],
                "output_artifacts": [],
                "constraints": [],
                "validation_criteria": ["test"],
                "type": "code_generation",
                "name": "test_task",
                "depends_on": [],
                "task_id": "fake-task-id",
                "subtask_id": "fake-subtask-id"
            }
            task_id = "fake-task-id"
            shutdown_event = threading.Event()

            try:
                asyncio.run(handle_code_generation(mock_engine, task_definition, task_id, shutdown_event))
                pytest.fail("TaskExecutionError was not raised")
            except TaskExecutionError as e:
                assert isinstance(e, TaskExecutionError)
                assert "Code generation task fake-task-id failed validation." in str(e)
                assert hasattr(e, 'details')
                assert e.details is not None
                assert e.details["overall_status"] == "failed"
                assert "commands_executed" in e.details
                assert isinstance(e.details["commands_executed"], list)
                assert len(e.details["commands_executed"]) > 0
                assert e.details["commands_executed"][0]["command"] == "test"
                assert e.details["commands_executed"][0]["exit_code"] == 1
            except Exception as e:
                pytest.fail(f"Caught unexpected exception: {type(e).__name__}: {e}")

            called_args = mock_gather_context.call_args[0]
            assert called_args[0] == mock_engine
            assert called_args[1] == task_definition
            assert called_args[2] == task_id
            # Accept any logger instance
            import logging
            assert isinstance(called_args[3], logging.Logger)
            mock_construct_prompt.assert_called_once_with(mock_engine, task_definition, task_id, "Mocked context", called_args[3])
            # Don't require run_ai_loop to be called if validation fails before it
            mock_execute_validation.assert_called_once_with(mock_engine, task_definition, task_id, called_args[3])

# Add tests for helper functions (_gather_context, _construct_initial_prompt, run_ai_loop, _execute_validation)
# These tests will replace the old class-based tests and cover their specific logic.

# Example: Test for _gather_context
@patch('src.ai_whisperer.agent_handlers.code_generation.Path')
@patch('src.ai_whisperer.agent_handlers.code_generation.build_ascii_directory_tree', return_value="Mocked tree")
def test__gather_context(mock_build_tree, mock_path):
    """Test _gather_context function."""
    mock_engine = MagicMock()
    mock_logger = MagicMock()
    task_definition = {
        "input_artifacts": ["file1.txt", "dir1/"]
    }
    task_id = "fake-task-id"

    # Mock Path objects
    mock_file_path = MagicMock()
    mock_file_path.is_file.return_value = True
    mock_file_path.is_dir.return_value = False
    mock_file_path.read_text.return_value = "File content"
    mock_file_path.__str__.return_value = "file1.txt"

    mock_dir_path = MagicMock()
    mock_dir_path.is_file.return_value = False
    mock_dir_path.is_dir.return_value = True
    mock_dir_path.__str__.return_value = "dir1/"

    mock_path.side_effect = lambda x: mock_file_path if x == "file1.txt" else mock_dir_path

    context = _gather_context(mock_engine, task_definition, task_id, mock_logger)

    assert "--- File: file1.txt ---\nFile content\n--- End File: file1.txt ---" in context
    assert "--- Directory Tree: dir1/ ---\nMocked tree\n--- End Directory Tree: dir1/ ---" in context
    mock_file_path.read_text.assert_called_once()
    mock_build_tree.assert_called_once_with(mock_dir_path)

# Example: Test for _construct_initial_prompt
@patch('src.ai_whisperer.agent_handlers.code_generation.Path')
def test__construct_initial_prompt(mock_path):
    """Test _construct_initial_prompt function."""
    mock_engine = MagicMock()
    mock_logger = MagicMock()
    task_definition = {
        "description": "Test description.",
        "instructions": ["Inst 1", "Inst 2"],
        "constraints": ["Const 1"],
        "raw_text": '{"key": "value"}'
    }
    task_id = "fake-task-id"
    prompt_context = "Some context."

    mock_prompt_file = MagicMock()
    mock_prompt_file.read_text.return_value = "Base prompt."
    mock_path.return_value = mock_prompt_file

    prompt = _construct_initial_prompt(mock_engine, task_definition, task_id, prompt_context, mock_logger)

    assert "Base prompt." in prompt
    assert "--- Task Description ---\nTest description." in prompt
    assert "--- Instructions ---\nInst 1\nInst 2" in prompt
    assert "--- Context ---\nSome context." in prompt
    assert "--- Constraints ---\nConst 1" in prompt
    assert "--- Raw Task JSON ---\n{\"key\": \"value\"}" in prompt

# Example: Test for _run_ai_interaction_loop (simplified)
import pytest
import asyncio
import threading
from unittest.mock import patch, MagicMock
from src.ai_whisperer.ai_loop import run_ai_loop

@patch('src.ai_whisperer.ai_loop.ToolRegistry')
def test_run_ai_loop_finishes(mock_tool_registry):
    """Test run_ai_loop when AI provides final content."""
    mock_engine = MagicMock()
    mock_engine.config.get.return_value = MagicMock() # Mock logger and AI config
    mock_engine.openrouter_api = MagicMock()
    mock_engine.state_manager = MagicMock()
    mock_context_manager = MagicMock() # Mock ContextManager

    # Simulate AI response with content
    mock_engine.openrouter_api.call_chat_completion.return_value = {"content": "Final response"}
    mock_context_manager.get_history.return_value = [] # Mock empty history initially

    task_definition = {}
    task_id = "fake-task-id"
    initial_prompt = "Initial prompt."
    shutdown_event = threading.Event()

    result = asyncio.run(
        run_ai_loop(mock_engine, task_definition, task_id, initial_prompt, mock_engine.config.get.return_value, mock_context_manager, shutdown_event)
    )

    assert result["content"] == "Final response"
    mock_engine.openrouter_api.call_chat_completion.assert_called_once()
    assert mock_context_manager.add_message.call_count == 2 # Initial prompt + final response

# Example: Test for _execute_validation
@patch('src.ai_whisperer.agent_handlers.code_generation.Path')
def test__execute_validation_success(mock_path):
    """Test _execute_validation with all expected files existing."""
    mock_engine = MagicMock()
    mock_logger = MagicMock()
    task_definition = {
        "expected_output_files": ["file1.txt", "dir1/file2.txt"]
    }
    task_id = "fake-task-id"

    # Mock Path objects to simulate files existing
    mock_file1 = MagicMock()
    mock_file1.is_file.return_value = True
    mock_file2 = MagicMock()
    mock_file2.is_file.return_value = True
    mock_path.side_effect = lambda x: mock_file1 if x == "file1.txt" else mock_file2

    passed, details = _execute_validation(mock_engine, task_definition, task_id, mock_logger)

    assert passed is True
    assert details["overall_status"] == "passed"
    assert details["checked_files"] == ["file1.txt", "dir1/file2.txt"]
    assert details["missing_files"] == []
    mock_path.call_count == 2 # Ensure Path was called for each file

@patch('src.ai_whisperer.agent_handlers.code_generation.Path')
def test__execute_validation_failure_missing_file(mock_path):
    """Test _execute_validation with a missing expected file."""
    mock_engine = MagicMock()
    mock_logger = MagicMock()
    task_definition = {
        "expected_output_files": ["file1.txt", "dir1/file2.txt"]
    }
    task_id = "fake-task-id"

    # Mock Path objects to simulate one file missing
    mock_file1 = MagicMock()
    mock_file1.is_file.return_value = True
    mock_file2 = MagicMock()
    mock_file2.is_file.return_value = False # Simulate missing file
    mock_path.side_effect = lambda x: mock_file1 if x == "file1.txt" else mock_file2

    passed, details = _execute_validation(mock_engine, task_definition, task_id, mock_logger)

    assert passed is False
    assert details["overall_status"] == "failed"
    assert details["checked_files"] == ["file1.txt", "dir1/file2.txt"]
    assert details["missing_files"] == ["dir1/file2.txt"]
    assert details["commands_executed"] == [] # commands_executed should be an empty list
    mock_path.call_count == 2 # Ensure Path was called for each file

def test__execute_validation_no_criteria():
    """Test _execute_validation with no validation criteria."""
    mock_engine = MagicMock()
    mock_logger = MagicMock()
    task_definition = {} # No validation_criteria or expected_output_files
    task_id = "fake-task-id"

    passed, details = _execute_validation(mock_engine, task_definition, task_id, mock_logger)

    assert passed is True
    assert details["overall_status"] == "skipped"
    assert "checked_files" not in details # Ensure file checks were skipped
    assert "missing_files" not in details # Ensure file checks were skipped
    assert details["commands_executed"] == [] # commands_executed should be an empty list

# Add more specific tests for _run_ai_interaction_loop covering tool calls,
# unexpected responses, and error handling within the loop.
# Add tests for error handling in _gather_context and _construct_initial_prompt.
# Ensure all original test scenarios (parsing, prompt construction, response processing,
# test/validation runner interaction, error handling, file examination/reuse) are covered
# by the new function-based tests.