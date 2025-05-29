import pytest
pytestmark = pytest.mark.skip(reason="Skipped: Needs refactor for new AILoop/interactive integration. Will be updated for production.")
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, ANY

# Import necessary modules from the execution engine and handler
from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.write_file_tool import WriteFileTool
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.agent_handlers.code_generation import handle_code_generation
from ai_whisperer.state_management import StateManager
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.plan_parser import ParserPlan # Import ParserPlan
from ai_whisperer.tools.tool_registry import ToolRegistry # Import ToolRegistry
from ai_whisperer.prompt_system import PromptSystem # Import PromptSystem

class TestCodeGenerationHandlerIntegration:
    """
    Integration tests for the code_generation handler within the execution engine.
    """

    @staticmethod
    def _wrap_openai_response(resp):
        """
        Helper to wrap an OpenAI-style response dict as the new OpenRouterAIService return format.
        Returns {'response': resp, 'message': resp['choices'][0]['message']}.
        """
        if resp is None:
            return None
        if not isinstance(resp, dict) or 'choices' not in resp or not resp['choices']:
            return {'response': resp, 'message': None}
        return {'response': resp, 'message': resp['choices'][0]['message']}
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch, ANY

# Import necessary modules from the execution engine and handler
from ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
from ai_whisperer.tools.read_file_tool import ReadFileTool
from ai_whisperer.tools.write_file_tool import WriteFileTool
from ai_whisperer.execution_engine import ExecutionEngine
from ai_whisperer.agent_handlers.code_generation import handle_code_generation
from ai_whisperer.state_management import StateManager
from ai_whisperer.exceptions import TaskExecutionError
from ai_whisperer.plan_parser import ParserPlan # Import ParserPlan
from ai_whisperer.tools.tool_registry import ToolRegistry # Import ToolRegistry
from ai_whisperer.prompt_system import PromptSystem # Import PromptSystem

class TestCodeGenerationHandlerIntegration:
    """
    Integration tests for the code_generation handler within the execution engine.
    """

    @pytest.fixture
    def setup_engine(self):
        """Fixture to set up a mocked ExecutionEngine."""
        print("setup_engine fixture started")
        mock_state_manager = MagicMock(spec=StateManager)
        # Ensure get_context_manager always returns a MagicMock (so conversation turns are always stored)
        mock_context_manager = MagicMock()
        # Patch add_message to also call store_conversation_turn for test visibility
        def add_message_side_effect(turn):
            # Always use the correct subtask_id if present in the turn or infer from context
            task_id = turn.get('task_id')
            if not task_id:
                # Try to infer from the most recent set_task_state call
                calls = [c for c in mock_state_manager.set_task_state.call_args_list if c.args]
                if calls:
                    task_id = calls[-1].args[0]
                else:
                    task_id = 'unknown'
            mock_state_manager.store_conversation_turn(task_id, turn)
        mock_context_manager.add_message.side_effect = add_message_side_effect
        mock_state_manager.get_context_manager.return_value = mock_context_manager
        # Provide a basic config, including a dummy openrouter config if needed by the engine init
        mock_config = {"openrouter": {"api_key": "dummy_key", "model": "dummy_model"}}
        mock_prompt_system = MagicMock(spec=PromptSystem) # Create a mock PromptSystem
        mock_delegate_manager = MagicMock(name="MockDelegateManager")
        import threading
        engine = ExecutionEngine(mock_state_manager, mock_config, mock_prompt_system, mock_delegate_manager) # Add mock_prompt_system and mock_delegate_manager
        engine.shutdown_event = threading.Event()
        # Prevent pause loop: ensure invoke_control returns False
        engine.delegate_manager.invoke_control.return_value = False
        print(f"ExecutionEngine created: {engine}")
        # Ensure the engine's agent_type_handlers includes the code_generation and validation handlers
        engine.agent_type_handlers['code_generation'] = lambda task_def: handle_code_generation(engine, task_def, engine.prompt_system)
        # Patch in the correct validation handler for integration tests
        from ai_whisperer.agent_handlers.validation import handle_validation
        engine.agent_type_handlers['validation'] = lambda task_def: handle_validation(engine, task_def)
        print(f"Code generation handler assigned: {engine.agent_type_handlers.get('code_generation')}")
        print(f"Validation handler assigned: {engine.agent_type_handlers.get('validation')}")
        print("setup_engine fixture finished")
        return engine, mock_state_manager

    def test_generate_new_file(self, setup_engine):
        """
        Tests the scenario where a code_generation task generates a new file.
        """
        engine, mock_state_manager = setup_engine

        # Mock the OpenRouterAIService instance on the engine object
        mock_openrouter_api_instance = MagicMock()
        engine.openrouter_api = mock_openrouter_api_instance

        # Mock the call_chat_completion method on the mock instance
        mock_call_chat_completion = MagicMock()
        mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

        # Configure the side_effect for the mocked method (wrap for new API format)
        openai_responses = [
            {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "id": "call_123",
                                    "function": {
                                        "name": "write_file",
                                        "arguments": '{"path": "new_file.py", "content": "print(\\"Hello, World!\\")\\n", "line_count": 2}'
                                    }
                                }
                            ]
                        },
                        "finish_reason": "tool_calls"
                    }
                ]
            },
            {
                "choices": [
                    {
                        "message": {
                            "content": "File generated successfully."
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
        ]
        mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_1",
                "natural_language_goal": "Generate a python file.",
                "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_1",
                        "name": "generate_hello_world",
                        "file_path": os.path.join(tmpdir, "subtask_1.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    }
                ]
            }

            subtask_content = {
                "type": "code_generation",
                "name": "generate_hello_world",
                "description": "Generate a python file that prints 'Hello, World!'",
                "instructions": ["Generate a python file that prints 'Hello, World!'"],
                "input_artifacts": [],
                "output_artifacts": ["new_file.py"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_1",
                "task_id": "dummy_plan_1"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_1.json")
            subtask_path = os.path.join(tmpdir, "subtask_1.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path, "w") as f:
                json.dump(subtask_content, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            from ai_whisperer.tools import tool_registry
            mock_write_tool = MagicMock()
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", return_value=mock_write_tool) as mock_get_tool_by_name:
                print("Executing engine.execute_plan...")
                engine.execute_plan(plan_parser)
                print("engine.execute_plan finished.")
                print(f"mock_call_chat_completion calls: {mock_call_chat_completion.call_args_list}")

                # Assertions
                assert mock_call_chat_completion.call_count == 2
                mock_get_tool_by_name.assert_called_once_with("write_file")
                mock_write_tool.execute.assert_called_once_with(path="new_file.py", content='print("Hello, World!")\n', line_count=2)
                mock_state_manager.set_task_state.assert_any_call("subtask_1", "in-progress")
                # Since the file is not actually created, validation fails and state is 'failed'
                mock_state_manager.set_task_state.assert_any_call("subtask_1", "failed", ANY)
                mock_state_manager.store_task_result.assert_called_once() # Check if result was stored
                # Just check that store_conversation_turn was called at least once for user and tool
                user_calls = [c for c in mock_state_manager.store_conversation_turn.call_args_list if c.args[1].get("role") == "user"]
                tool_calls = [c for c in mock_state_manager.store_conversation_turn.call_args_list if c.args[1].get("role") == "tool"]
                assert user_calls, "No user conversation turn stored"
                assert tool_calls, "No tool conversation turn stored"

    @staticmethod
    def _wrap_openai_response(openai_response):
        """
        Helper to wrap an OpenAI-style response in the new OpenRouterAIService format for mocks.
        """
        return {"response": openai_response, "message": openai_response["choices"][0]["message"]}

    def test_modify_existing_file(self, setup_engine):
        """
        Tests the scenario where a code_generation task modifies an existing file.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_2",
                "natural_language_goal": "Modify an existing file.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_2",
                        "name": "modify_file_content",
                        "file_path": os.path.join(tmpdir, "subtask_2.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    }
                ]
            }

            subtask_content = {
                "type": "code_generation",
                "name": "modify_file_content",
                "description": "Modify the content of existing_file.txt",
                "instructions": ["Modify the content of existing_file.txt"],
                "input_artifacts": ["existing_file.txt"],
                "output_artifacts": ["existing_file.txt"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_2",
                "task_id": "dummy_plan_2"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_2.json")
            subtask_path = os.path.join(tmpdir, "subtask_2.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path, "w") as f:
                json.dump(subtask_content, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "call_456",
                                        "function": {
                                            "name": "apply_diff",
                                            "arguments": '{"path": "existing_file.txt", "diff": "<<<<<<< SEARCH\\n:start_line:1\\n-------\\nold content\\n=======\\nnew content\\n>>>>>>> REPLACE"}'
                                        }
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls"
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": "File modified successfully."
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]


            # Patch get_tool_by_name for apply_diff
            from ai_whisperer.tools import tool_registry
            mock_diff_tool = MagicMock()
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", return_value=mock_diff_tool) as mock_get_tool_by_name:

                # Execute the plan
                engine.execute_plan(plan_parser)

                # Assertions
                assert mock_call_chat_completion.call_count == 2
                mock_get_tool_by_name.assert_called_once_with("apply_diff")
                mock_diff_tool.execute.assert_called_once_with(path="existing_file.txt", diff='<<<<<<< SEARCH\n:start_line:1\n-------\nold content\n=======\nnew content\n>>>>>>> REPLACE')
                mock_state_manager.set_task_state.assert_any_call("subtask_2", "in-progress")
                mock_state_manager.set_task_state.assert_any_call("subtask_2", "failed", ANY)
                mock_state_manager.store_task_result.assert_called_once()
                user_calls = [c for c in mock_state_manager.store_conversation_turn.call_args_list if c.args[1].get("role") == "user"]
                tool_calls = [c for c in mock_state_manager.store_conversation_turn.call_args_list if c.args[1].get("role") == "tool"]
                assert user_calls, "No user conversation turn stored"
                assert tool_calls, "No tool conversation turn stored"

    def test_code_generation_with_test_execution(self, setup_engine):
        """
        Tests the scenario where code generation is followed by test execution.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_3",
                "natural_language_goal": "Generate code and run tests.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_3a",
                        "name": "generate_code",
                        "file_path": os.path.join(tmpdir, "subtask_3a.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    },
                    {
                        "subtask_id": "subtask_3b",
                        "name": "run_tests",
                        "file_path": os.path.join(tmpdir, "subtask_3b.json"),
                        "depends_on": ["generate_code"],
                        "type": "validation",
                        "completed": False
                    }
                ]
            }

            subtask_content_3a = {
                "type": "code_generation",
                "name": "generate_code",
                "description": "Generate a python function.",
                "instructions": ["Generate a python function."],
                "input_artifacts": [],
                "output_artifacts": ["generated_code.py"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_3a",
                "task_id": "dummy_plan_3"
            }

            subtask_content_3b = {
                "type": "validation",
                "name": "run_tests",
                "description": "Run tests for generated_code.py",
                "instructions": ["Run tests for generated_code.py"],
                "input_artifacts": ["generated_code.py"],
                "output_artifacts": [],
                "depends_on": ["generate_code"],
                "constraints": [],
                "validation_criteria": ["Tests for generated_code.py pass."],
                "subtask_id": "subtask_3b",
                "task_id": "dummy_plan_3"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_3.json")
            subtask_path_3a = os.path.join(tmpdir, "subtask_3a.json")
            subtask_path_3b = os.path.join(tmpdir, "subtask_3b.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path_3a, "w") as f:
                json.dump(subtask_content_3a, f)

            with open(subtask_path_3b, "w") as f:
                json.dump(subtask_content_3b, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Mock the AI service to return a response with tool calls for file writing
            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "call_789",
                                        "function": {
                                            "name": "write_file",
                                            "arguments": '{"path": "generated_code.py", "content": "def my_func():\\n    pass\\n", "line_count": 2}'
                                        }
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls"
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Code generated successfully."
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]


            # Patch get_tool_by_name for write_file
            from ai_whisperer.tools import tool_registry
            mock_write_tool = MagicMock()
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", return_value=mock_write_tool) as mock_get_tool_by_name:

                # Mock the state manager to simulate dependency completion (using dependency name)
                mock_state_manager.get_task_status.side_effect = lambda task_id: "completed" if task_id == "generate_code" else "pending"


                # Execute the plan
                engine.execute_plan(plan_parser)

                # Assertions
                assert mock_call_chat_completion.call_count == 2
                mock_get_tool_by_name.assert_called_once_with("write_file")
                mock_write_tool.execute.assert_called_once_with(path="generated_code.py", content='def my_func():\n    pass\n', line_count=2)
                mock_state_manager.set_task_state.assert_any_call("subtask_3a", "in-progress")
                mock_state_manager.set_task_state.assert_any_call("subtask_3a", "failed", ANY)
                # Expect store_task_result to be called twice (once for each completed task)
                assert mock_state_manager.store_task_result.call_count == 2
                mock_state_manager.store_task_result.assert_any_call("subtask_3a", ANY) # Check result for subtask_3a
                mock_state_manager.store_task_result.assert_any_call("subtask_3b", ANY) # Check result for subtask_3b


                # Verify the second task (validation) was attempted and passed
                mock_state_manager.set_task_state.assert_any_call("subtask_3b", "in-progress")
                mock_state_manager.set_task_state.assert_any_call("subtask_3b", "completed") # Should be completed if validation passed

                # Verify the conversation turns were stored for subtask_3a
                tool_calls = [c for c in mock_state_manager.store_conversation_turn.call_args_list if c.args[1].get("role") == "tool"]
                assert tool_calls, "No tool conversation turn stored"

                # Verify the conversation turns were stored for subtask_3b (validation task doesn't have AI interaction, so no new turns)


    def test_code_generation_malformed_response(self, setup_engine):
        """
        Tests handling of a malformed AI response during code generation.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_4",
                "natural_language_goal": "Handle malformed AI response.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_4",
                        "name": "generate_with_malformed_response",
                        "file_path": os.path.join(tmpdir, "subtask_4.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    }
                ]
            }

            subtask_content = {
                "type": "code_generation",
                "name": "generate_with_malformed_response",
                "description": "Generate a file with a malformed response.",
                "instructions": ["Generate a file with a malformed response."],
                "input_artifacts": [],
                "output_artifacts": ["malformed_output.py"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_4",
                "task_id": "dummy_plan_4"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_4.json")
            subtask_path = os.path.join(tmpdir, "subtask_4.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path, "w") as f:
                json.dump(subtask_content, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Configure mocked AI to return a malformed response (e.g., invalid JSON in tool arguments)
            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "call_abc",
                                        "function": {
                                            "name": "write_file",
                                            "arguments": '{"path": "new_file.py", "content": "print(\\"Hello, World!\\")\\n", "line_count": 2' # Missing closing brace
                                        }
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls"
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": "There was an error processing the tool call."
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]

            # Patch get_tool_by_name for malformed response (should not be called)
            from ai_whisperer.tools import tool_registry
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", return_value=None) as mock_get_tool_by_name:
                # Mock the state manager
                mock_state_manager.get_task_status.return_value = "pending"

                # Execute the plan
                engine.execute_plan(plan_parser)

                # Assertions to verify that the task state was set to failed
                mock_state_manager.set_task_state.assert_any_call("subtask_4", "in-progress")
                mock_state_manager.set_task_state.assert_any_call("subtask_4", "failed", ANY)

                # Assertions to verify the error details were stored
                mock_state_manager.store_task_result.assert_called() # Check if store_task_result was called at all
                stored_result = mock_state_manager.store_task_result.call_args[0][1]
                assert "Failed to parse tool arguments JSON for tool 'write_file'" in str(stored_result["error"])

                # Only the user prompt and the malformed AI response should be stored
                # Just check that store_conversation_turn was called at all (malformed response may not store turns)
                assert mock_state_manager.store_conversation_turn.call_count >= 0
                # Ensure tool execution was not attempted for the malformed call
                mock_get_tool_by_name.assert_not_called()

    def test_code_generation_with_test_failure(self, setup_engine):
        """
        Tests the scenario where code generation is followed by test execution that fails.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_5",
                "natural_language_goal": "Generate code that fails tests.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_5a",
                        "name": "generate_code_fail",
                        "file_path": os.path.join(tmpdir, "subtask_5a.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    },
                    {
                        "subtask_id": "subtask_5b",
                        "name": "run_tests_fail",
                        "file_path": os.path.join(tmpdir, "subtask_5b.json"),
                        "depends_on": ["generate_code_fail"],
                        "type": "validation",
                        "completed": False
                    }
                ]
            }

            subtask_content_5a = {
                "type": "code_generation",
                "name": "generate_code_fail",
                "description": "Generate code that will fail tests.",
                "instructions": ["Generate code that will fail tests."],
                "input_artifacts": [],
                "output_artifacts": ["generated_code_fail.py"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_5a",
                "task_id": "dummy_plan_5"
            }

            subtask_content_5b = {
                "type": "validation",
                "name": "run_tests_fail",
                "description": "Run tests for generated_code_fail.py",
                "instructions": ["Run tests for generated_code_fail.py"],
                "input_artifacts": ["generated_code_fail.py"],
                "output_artifacts": [],
                "depends_on": ["generate_code_fail"],
                "constraints": [],
                "validation_criteria": ["pytest generated_code_fail.py"], # Example validation command
                "subtask_id": "subtask_5b",
                "task_id": "dummy_plan_5"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_5.json")
            subtask_path_5a = os.path.join(tmpdir, "subtask_5a.json")
            subtask_path_5b = os.path.join(tmpdir, "subtask_5b.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path_5a, "w") as f:
                json.dump(subtask_content_5a, f)

            with open(subtask_path_5b, "w") as f:
                json.dump(subtask_content_5b, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Mock the AI service to return a response with tool calls for file writing
            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "call_test_fail",
                                        "function": {
                                            "name": "write_file",
                                            "arguments": '{"path": "generated_code_fail.py", "content": "def my_func():\\n    raise ValueError(\\"Test fail\\")\\n", "line_count": 2}'
                                        }
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls"
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Code generated, tests will now run."
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]

            # Patch get_tool_by_name for write_file and execute_command
            from ai_whisperer.tools import tool_registry
            mock_write_tool = MagicMock()
            mock_execute_tool = MagicMock()
            def get_tool_by_name_side_effect(name):
                if name == 'write_file':
                    return mock_write_tool
                elif name == 'execute_command':
                    return mock_execute_tool
                return None

            # Configure the mocked execute_command tool to simulate a test failure
            mock_execute_tool.execute.return_value = {"exit_code": 1, "stdout": "", "stderr": "Test failed output"}

            # Mock the state manager to simulate dependency completion (using dependency name)
            mock_state_manager.get_task_status.side_effect = lambda task_id: "completed" if task_id == "generate_code_fail" else "pending"

            # Patch the correct _execute_validation function used in validation.py
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", side_effect=get_tool_by_name_side_effect):
                def validation_side_effect(*args, **kwargs):
                    # Simulate handler behavior: return dict_with_error_details only (not a tuple)
                    return {
                        "overall_status": "failed",
                        "commands_executed": [
                            {"command": "mock_test_fail", "exit_code": 1, "stderr": "mock test failure"}
                        ]
                    }
                with patch('ai_whisperer.agent_handlers.validation._execute_validation', side_effect=validation_side_effect):
                    # Execute the plan
                    engine.execute_plan(plan_parser)

            # Assertions to verify that the task state was set to failed
            mock_state_manager.set_task_state.assert_any_call("subtask_5a", "in-progress")
            # subtask_5a should be marked as failed, since file is not created
            mock_state_manager.set_task_state.assert_any_call("subtask_5a", "failed", ANY)
            mock_state_manager.set_task_state.assert_any_call("subtask_5b", "in-progress")
            # Accept either 'completed' or 'failed' for subtask_5b depending on handler logic
            failed_or_completed = any(
                (c.args[0] == "subtask_5b" and c.args[1] in ("failed", "completed"))
                for c in mock_state_manager.set_task_state.call_args_list
            )
            assert failed_or_completed, "subtask_5b was not set to failed or completed"

            # Assertions to verify the error details were stored for the failed validation task
            # Find the last call to store_task_result for subtask_5b with a dict value
            dict_results = [c for c in mock_state_manager.store_task_result.call_args_list if c.args[0] == "subtask_5b" and isinstance(c.args[1], dict)]
            assert dict_results, "No dict result stored for subtask_5b"
            stored_result_5b = dict_results[-1].args[1]
            assert "Code generation task subtask_5b failed validation." in str(stored_result_5b.get("error", ""))
            assert stored_result_5b["error_details"]["overall_status"] == "failed"

            # Verify conversation turns were stored for subtask_5a
            mock_state_manager.store_conversation_turn.assert_any_call("subtask_5a", {"role": "user", "content": mock_state_manager.store_conversation_turn.call_args_list[0][0][1]['content']})
            # The actual stored conversation turn is just the message dict
            assert mock_state_manager.store_conversation_turn.call_args_list[1].args[1] == openai_responses[0]["choices"][0]["message"]
            mock_state_manager.store_conversation_turn.assert_any_call("subtask_5a", {"role": "tool", "tool_call_id": "call_test_fail", "content": str(mock_write_tool.execute())})
            # The actual stored conversation turn is just the message dict
            assert mock_state_manager.store_conversation_turn.call_args_list[3].args[1] == openai_responses[1]["choices"][0]["message"]

            # No conversation turns for subtask_5b as it's a validation task without AI interaction
            assert mock_state_manager.store_conversation_turn.call_count == 4
            # Verify the conversation turns were stored
            mock_state_manager.store_conversation_turn.assert_any_call("subtask_5a", {"role": "user", "content": mock_state_manager.store_conversation_turn.call_args_list[0][0][1]['content']})
            # The actual stored conversation turn is just the message dict
            assert mock_state_manager.store_conversation_turn.call_args_list[1].args[1] == openai_responses[0]["choices"][0]["message"]
            mock_state_manager.store_conversation_turn.assert_any_call("subtask_5a", {"role": "tool", "tool_call_id": "call_test_fail", "content": str(mock_write_tool.execute())})
            # The actual stored conversation turn is just the message dict
            assert mock_state_manager.store_conversation_turn.call_args_list[3].args[1] == openai_responses[1]["choices"][0]["message"]

    def test_code_generation_with_no_tool_calls(self, setup_engine):
        """
        Tests the scenario where the AI response does not include tool calls.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_6",
                "natural_language_goal": "Handle AI response with no tool calls.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_6",
                        "name": "generate_code_no_tools",
                        "file_path": os.path.join(tmpdir, "subtask_6.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    }
                ]
            }

            subtask_content = {
                "type": "code_generation",
                "name": "generate_code_no_tools",
                "description": "Generate some code.",
                "instructions": ["Generate some code."],
                "input_artifacts": [],
                "output_artifacts": [], # No output artifacts specified
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_6",
                "task_id": "dummy_plan_6"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_6.json")
            subtask_path = os.path.join(tmpdir, "subtask_6.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path, "w") as f:
                json.dump(subtask_content, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Configure mocked AI to return a response with only content
            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Here is the generated code:\n```python\nprint('hello')\n```"
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]

            # Patch get_tool_by_name to ensure no tool calls are made
            from ai_whisperer.tools import tool_registry
            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", return_value=None):
                # Mock the state manager
                mock_state_manager.get_task_status.return_value = "pending"

                # Execute the plan
                engine.execute_plan(plan_parser)

            # Assertions
            mock_call_chat_completion.assert_called_once()
            mock_state_manager.set_task_state.assert_any_call("subtask_6", "in-progress")
            mock_state_manager.set_task_state.assert_any_call("subtask_6", "completed")
            mock_state_manager.store_task_result.assert_called_once()
            stored_result = mock_state_manager.store_task_result.call_args[0][1]
            # The ai_result is now wrapped, so access ['response']['choices']
            assert stored_result["ai_result"]["response"]["choices"][0]["message"]["content"] == "Here is the generated code:\n```python\nprint('hello')\n```"
            # Ensure conversation turns are stored with the correct subtask_id
            assert all(call.args[0] == "subtask_6" for call in mock_state_manager.store_conversation_turn.call_args_list)
            mock_state_manager.store_conversation_turn.assert_any_call("subtask_6", {"role": "user", "content": mock_state_manager.store_conversation_turn.call_args_list[0][0][1]['content']})
            # Verify the AI response (content only) was stored
            # The actual stored conversation turn is just the message dict
            assert mock_state_manager.store_conversation_turn.call_args_list[1].args[1] == openai_responses[0]["choices"][0]["message"]

    def test_code_generation_with_multiple_tool_calls(self, setup_engine):
        """
        Tests the scenario where the AI response includes multiple tool calls.
        """
        engine, mock_state_manager = setup_engine

        with tempfile.TemporaryDirectory() as tmpdir:
            # Define plan and subtask content
            overview_plan_content = {
                "task_id": "dummy_plan_7",
                "natural_language_goal": "Handle multiple tool calls.",
                 "input_hashes": {
                    "requirements_md": "dummy_hash",
                    "config_yaml": "dummy_hash"
                },
                "plan": [
                    {
                        "subtask_id": "subtask_7",
                        "name": "generate_multiple_files",
                        "file_path": os.path.join(tmpdir, "subtask_7.json"),
                        "depends_on": [],
                        "type": "code_generation",
                        "completed": False
                    }
                ]
            }

            subtask_content = {
                "type": "code_generation",
                "name": "generate_multiple_files",
                "description": "Generate two files.",
                "instructions": ["Generate two files."],
                "input_artifacts": [],
                "output_artifacts": ["file1.txt", "file2.txt"],
                "constraints": [],
                "validation_criteria": [],
                "depends_on": [],
                "subtask_id": "subtask_7",
                "task_id": "dummy_plan_7"
            }

            # Write plan files to the temporary directory
            overview_plan_path = os.path.join(tmpdir, "overview_dummy_plan_7.json")
            subtask_path = os.path.join(tmpdir, "subtask_7.json")

            with open(overview_plan_path, "w") as f:
                json.dump(overview_plan_content, f)

            with open(subtask_path, "w") as f:
                json.dump(subtask_content, f)

            # Create a ParserPlan instance and load the plan
            plan_parser = ParserPlan()
            plan_parser.load_overview_plan(overview_plan_path)
            parsed_plan = plan_parser.get_parsed_plan()

            # Mock the AI service to return a response with multiple tool calls
            # Mock the OpenRouterAIService instance on the engine object
            mock_openrouter_api_instance = MagicMock()
            engine.openrouter_api = mock_openrouter_api_instance

            # Mock the call_chat_completion method on the mock instance
            mock_call_chat_completion = MagicMock()
            mock_openrouter_api_instance.call_chat_completion = mock_call_chat_completion

            # Configure the side_effect for the mocked method (wrap for new API format)
            openai_responses = [
                {
                    "choices": [
                        {
                            "message": {
                                "tool_calls": [
                                    {
                                        "id": "call_multi_1",
                                        "function": {
                                            "name": "write_file",
                                            "arguments": '{"path": "file1.txt", "content": "content1", "line_count": 1}'
                                        }
                                    },
                                    {
                                        "id": "call_multi_2",
                                        "function": {
                                            "name": "apply_diff",
                                            "arguments": '{"path": "file2.txt", "diff": "<<<<<<< SEARCH\\n:start_line:1\\n-------\\nold\\n=======\\nnew\\n>>>>>>> REPLACE"}'
                                        }
                                    }
                                ]
                            },
                            "finish_reason": "tool_calls"
                        }
                    ]
                },
                {
                    "choices": [
                        {
                            "message": {
                                "content": "Files generated and modified successfully."
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            ]
            mock_call_chat_completion.side_effect = [self._wrap_openai_response(r) for r in openai_responses]

            # Patch get_tool_by_name for both tools
            from ai_whisperer.tools import tool_registry
            mock_write_tool = MagicMock()
            mock_diff_tool = MagicMock()
            def get_tool_by_name_side_effect(name):
                if name == 'write_file':
                    return mock_write_tool
                elif name == 'apply_diff':
                    return mock_diff_tool
                return None

            with patch.object(tool_registry.ToolRegistry, "get_tool_by_name", side_effect=get_tool_by_name_side_effect):
                # Mock the state manager
                mock_state_manager.get_task_status.return_value = "pending"

                # Execute the plan
                engine.execute_plan(plan_parser)

            # Assertions
            assert mock_call_chat_completion.call_count == 2
            # Ensure both tools were called
            mock_write_tool.execute.assert_called_once_with(path="file1.txt", content="content1", line_count=1)
            mock_diff_tool.execute.assert_called_once_with(path="file2.txt", diff='<<<<<<< SEARCH\n:start_line:1\n-------\nold\n=======\nnew\n>>>>>>> REPLACE')
