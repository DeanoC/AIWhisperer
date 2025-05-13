import pytest
import os
import dotenv
import json
import time
from unittest.mock import patch

from src.ai_whisperer.ai_service_interaction import OpenRouterAPI
from src.ai_whisperer.tools.tool_registry import ToolRegistry
from src.ai_whisperer.tools.read_file_tool import ReadFileTool
from src.ai_whisperer.tools.write_file_tool import WriteFileTool
from src.ai_whisperer.tools.execute_command_tool import ExecuteCommandTool
from src.ai_whisperer.exceptions import OpenRouterAPIError

# Load environment variables from .env file
dotenv.load_dotenv()

# --- Fixtures ---

@pytest.fixture(scope="session")
def openrouter_api():
    """Fixture to provide an OpenRouterAPI instance."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip("OPENROUTER_API_KEY not set")

    # Create a minimal config dictionary for OpenRouterAPI
    # Using a commonly available model for integration tests
    openrouter_config_data = {"api_key": api_key, "model": "openai/gpt-3.5-turbo"}
    return OpenRouterAPI(openrouter_config_data)

@pytest.fixture
def tool_registry():
    """
    Fixture to provide a ToolRegistry instance with manually registered tools
    for integration tests.
    """
    registry = ToolRegistry()
    # Manually register the file tools for testing
    registry.register_tool(ReadFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ExecuteCommandTool())
    return registry

@pytest.fixture
def temp_test_file():
    """Fixture to create a temporary file within the project's output directory for testing and clean it up."""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True) # Ensure output directory exists

    file_content = "This is a test file for AIWhisperer tool usage integration tests."
    file_name = f"test_read_file_{int(time.time())}.txt" # Use timestamp to ensure unique name
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w") as f:
        f.write(file_content)

    yield file_path, file_content

    # Clean up the file
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def temp_write_file_path():
    """Fixture to provide a temporary file path within the project's output directory for testing write operations."""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True) # Ensure output directory exists

    file_name = f"test_write_file_{int(time.time())}.txt" # Use timestamp to ensure unique name
    file_path = os.path.join(output_dir, file_name)

    # Ensure the file does not exist initially
    if os.path.exists(file_path):
        os.remove(file_path)

    yield file_path

    # Clean up the file
    if os.path.exists(file_path):
        os.remove(file_path)

# --- Test Cases ---

@pytest.mark.integration
def test_ai_read_file_tool_call(openrouter_api: OpenRouterAPI, tool_registry: ToolRegistry, temp_test_file: tuple):
    """
    Test that the AI correctly identifies the need to use the read_file tool
    and formulates the correct tool call when prompted to read a file.
    """
    file_path, expected_content = temp_test_file
    prompt = f"Please read the content of the file located at: {file_path}"

    # Simulate the AI interaction that should result in a tool call
    # This part requires the AI to actually generate a tool call response.
    # Due to the nature of integration tests with a real AI, we expect a tool_calls structure.
    # We might need to adjust the prompt or model to encourage tool usage.
    # For this test, we will send the prompt and check the response structure.

    messages = [{"role": "user", "content": prompt}]
    tools = tool_registry.get_all_tool_definitions()

    try:
        # Use call_chat_completion which is designed to handle tool calls
        response_obj = openrouter_api.call_chat_completion(
            prompt_text=prompt,
            model=openrouter_api.model, # Use the configured model
            params={}, # Use default or minimal params
            tools=tools,
            messages_history=messages # Pass messages history for context
        )

        # Assert that the response contains tool calls
        assert isinstance(response_obj, dict)
        assert "tool_calls" in response_obj
        tool_calls = response_obj["tool_calls"]
        assert isinstance(tool_calls, list)
        assert len(tool_calls) > 0

        # Find the read_text_file tool call
        read_file_call = None
        for call in tool_calls:
            if call.get("function", {}).get("name") == "read_text_file":
                read_file_call = call
                break

        assert read_file_call is not None, "AI did not call the read_text_file tool"
        assert "function" in read_file_call
        assert "arguments" in read_file_call["function"]

        # Parse the arguments (they come as a JSON string)
        try:
            args = json.loads(read_file_call["function"]["arguments"])
        except json.JSONDecodeError:
            pytest.fail("Failed to decode tool call arguments JSON")

        # Assert the arguments are correct
        assert isinstance(args, dict)
        assert "file_path" in args
        assert args["file_path"] == file_path

        # Note: Executing the tool and verifying its output would be a separate step
        # or part of a different test case focusing on tool execution.
        # This test specifically verifies the AI's ability to *call* the tool.

    except OpenRouterAPIError as e:
        pytest.fail(f"OpenRouter API error during test_ai_read_file_tool_call: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during test_ai_read_file_tool_call: {e}")


@pytest.mark.integration
def test_ai_write_file_tool_call(openrouter_api: OpenRouterAPI, tool_registry: ToolRegistry, temp_write_file_path: str):
    """
    Test that the AI correctly identifies the need to use the write_to_file tool
    and formulates the correct tool call when prompted to write to a file.
    """
    file_path = temp_write_file_path
    file_content = "This content should be written to the file by the AI."
    prompt = f"Please write the following content to the file at {file_path}:\n\n{file_content}"

    messages = [{"role": "user", "content": prompt}]
    tools = tool_registry.get_all_tool_definitions()

    try:
        response_obj = openrouter_api.call_chat_completion(
            prompt_text=prompt,
            model=openrouter_api.model,
            params={},
            tools=tools,
            messages_history=messages
        )

        assert isinstance(response_obj, dict)
        assert "tool_calls" in response_obj
        tool_calls = response_obj["tool_calls"]
        assert isinstance(tool_calls, list)
        assert len(tool_calls) > 0

        # Find the write_text_file tool call
        write_file_call = None
        for call in tool_calls:
            if call.get("function", {}).get("name") == "write_text_file":
                write_file_call = call
                break

        assert write_file_call is not None, "AI did not call the write_text_file tool"
        assert "function" in write_file_call
        assert "arguments" in write_file_call["function"]

        # Parse the arguments
        try:
            args = json.loads(write_file_call["function"]["arguments"])
        except json.JSONDecodeError:
            pytest.fail("Failed to decode tool call arguments JSON")

        # Assert the arguments are correct
        assert isinstance(args, dict)
        assert "file_path" in args
        # Normalize paths for comparison
        assert os.path.normpath(args["file_path"]) == os.path.normpath(file_path)
        assert "content" in args
        assert args["content"] == file_content
        # The write_text_file tool does not have a line_count parameter in its schema
        # Remove the assertion for line_count
        # assert "line_count" in args
        # Calculate expected line count (including empty lines)
        # expected_line_count = len(file_content.splitlines())
        # assert args["line_count"] == expected_line_count


    except OpenRouterAPIError as e:
        pytest.fail(f"OpenRouter API error during test_ai_write_file_tool_call: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during test_ai_write_file_tool_call: {e}")
    finally:
        # Clean up the file if the test failed after the tool call was identified
        if os.path.exists(file_path):
            os.remove(file_path)


@pytest.mark.integration
def test_ai_execute_command_tool_call(openrouter_api: OpenRouterAPI, tool_registry: ToolRegistry):
    """
    Test that the AI correctly identifies the need to use the execute_command tool
    and formulates the correct tool call when prompted to execute a command.
    """
    command_to_execute = "echo 'hello'"
    prompt = f"Please execute the following command: {command_to_execute}"

    messages = [{"role": "user", "content": prompt}]
    tools = tool_registry.get_all_tool_definitions()

    try:
        response_obj = openrouter_api.call_chat_completion(
            prompt_text=prompt,
            model=openrouter_api.model,
            params={},
            tools=tools,
            messages_history=messages
        )

        assert isinstance(response_obj, dict)
        assert "tool_calls" in response_obj
        tool_calls = response_obj["tool_calls"]
        assert isinstance(tool_calls, list)
        assert len(tool_calls) > 0

        # Find the execute_command tool call
        execute_command_call = None
        for call in tool_calls:
            if call.get("function", {}).get("name") == "execute_command":
                execute_command_call = call
                break

        assert execute_command_call is not None, "AI did not call the execute_command tool"
        assert "function" in execute_command_call
        assert "arguments" in execute_command_call["function"]

        # Parse the arguments
        try:
            args = json.loads(execute_command_call["function"]["arguments"])
        except json.JSONDecodeError:
            pytest.fail("Failed to decode tool call arguments JSON")

        # Assert the arguments are correct
        assert isinstance(args, dict)
        assert "command" in args
        assert args["command"] == command_to_execute
        # The execute_command tool has an optional 'cwd' parameter, no need to assert its presence

    except OpenRouterAPIError as e:
        pytest.fail(f"OpenRouter API error during test_ai_execute_command_tool_call: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during test_ai_execute_command_tool_call: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_tool_valid_params_execution(openrouter_api: OpenRouterAPI, tool_registry: ToolRegistry, temp_test_file: tuple, temp_write_file_path: str):
    """
    Test the end-to-end execution of file tools when the AI provides valid parameters.
    This test simulates the full cycle: AI call -> System invokes tool -> Tool executes.
    """
    read_file_path, expected_content = temp_test_file
    write_file_path = temp_write_file_path
    write_content = "Content written by the AI using the write_to_file tool."

    # Scenario 1: AI reads a file with valid path
    read_prompt = f"Read the content of the file at {read_file_path}."
    messages_read = [{"role": "user", "content": read_prompt}]
    tools = tool_registry.get_all_tool_definitions()

    try:
        # Mock os.path.abspath('.') to return the temporary directory for the read operation
        with patch('os.path.abspath') as mock_abspath:
            mock_abspath.return_value = str(temp_test_file[0]).rsplit(os.sep, 1)[0] # Get the directory of the temp file
            # Simulate AI call for reading
            read_response_obj = openrouter_api.call_chat_completion(
                prompt_text=read_prompt,
                model=openrouter_api.model,
                params={},
                tools=tools,
                messages_history=messages_read
            )

        assert isinstance(read_response_obj, dict) and "tool_calls" in read_response_obj, "AI did not generate tool call for reading"
        read_tool_calls = read_response_obj["tool_calls"]
        assert len(read_tool_calls) > 0

        # Assuming the first tool call is the read_text_file call
        read_call_args = json.loads(read_tool_calls[0]["function"]["arguments"])
        assert read_call_args.get("file_path") == read_file_path

        # Simulate the system executing the tool call
        read_tool_instance = tool_registry.get_tool_by_name("read_text_file")
        assert read_tool_instance is not None, "read_text_file tool not found in registry"

        # Execute the tool with the AI's provided arguments, passing the dictionary directly
        # The mock for os.path.abspath is active here
        # ReadFileTool.execute is NOT async
        read_tool_output = read_tool_instance.execute(read_call_args)

        # Assert the tool output is the expected file content
        # The read_file tool returns the content as a string on success
        assert read_tool_output == expected_content

        # Scenario 2: AI writes to a file with valid path and content
        write_prompt = f"Write the following text to {write_file_path}:\n\n{write_content}"
        messages_write = [{"role": "user", "content": write_prompt}]

        # Simulate AI call for writing
        write_response_obj = openrouter_api.call_chat_completion(
            prompt_text=write_prompt,
            model=openrouter_api.model,
            params={},
            tools=tools,
            messages_history=messages_write
        )

        assert isinstance(write_response_obj, dict) and "tool_calls" in write_response_obj, "AI did not generate tool call for writing"
        write_tool_calls = write_response_obj["tool_calls"]
        assert len(write_tool_calls) > 0

        # Assuming the first tool call is the write_text_file call
        write_call_args = json.loads(write_tool_calls[0]["function"]["arguments"])
        assert write_call_args.get("file_path") == write_file_path
        assert write_call_args.get("content") == write_content
        # The write_text_file tool does not have a line_count parameter in its schema
        # Remove the assertion for line_count
        # assert write_call_args.get("line_count") == len(write_content.splitlines())

        # Simulate the system executing the tool call
        write_tool_instance = tool_registry.get_tool_by_name("write_text_file")
        assert write_tool_instance is not None, "write_text_file tool not found in registry"

        # Execute the tool with the AI's provided arguments, unpacking the dictionary
        write_tool_output = await write_tool_instance.execute(**write_call_args)

        # Assert the tool execution was successful (write_to_file might return None or a success message)
        # Check the actual file content
        assert os.path.exists(write_file_path)
        with open(write_file_path, "r") as f:
            actual_written_content = f.read()
        assert actual_written_content == write_content

    except OpenRouterAPIError as e:
        pytest.fail(f"OpenRouter API error during test_ai_tool_valid_params_execution: {e}")
    except Exception as e:
        pytest.fail(f"An unexpected error occurred during test_ai_tool_valid_params_execution: {e}")
    finally:
        # Clean up the written file
        if os.path.exists(write_file_path):
            os.remove(write_file_path)


@pytest.mark.integration
def test_ai_tool_invalid_params_handling(openrouter_api: OpenRouterAPI, tool_registry: ToolRegistry):
    """
    Test that the AI or the system correctly handles attempts to use file tools
    with invalid parameters (e.g., non-existent file path for read, missing content for write).
    This test focuses on the system's handling of invalid parameters passed to the tool's execute method.
    Simulating the AI generating *invalid* tool calls is harder and might require mocking the AI response.
    For this test, we will simulate the system receiving an invalid tool call from the AI
    and verify that the tool's execute method raises an appropriate error or returns an error structure.
    """
    # Scenario 1: Simulate AI calling read_text_file with a non-existent path
    invalid_read_path = "/path/to/nonexistent/file.txt"
    # The ReadFileTool.execute method expects 'file_path', not 'path'
    read_call_args = {"file_path": invalid_read_path}

    read_tool_instance = tool_registry.get_tool_by_name("read_text_file")
    assert read_tool_instance is not None, "read_text_file tool not found in registry"

    # Expecting the tool's execute method to raise an error or return an error structure
    # based on the tool's implementation for invalid paths.
    # Assuming the tool raises a FileNotFoundError or similar, or returns a specific error dict.
    # Let's assume it raises an error or returns an error dictionary.
    # Based on ReadFileTool implementation, it returns an error string.
    # When an absolute or outside-of-project path is provided, the access denied error is returned first.
    read_tool_output = read_tool_instance.execute(read_call_args)
    assert isinstance(read_tool_output, str)
    assert "Error: Access denied" in read_tool_output

    # Scenario 2: Simulate AI calling write_text_file with missing content
    invalid_write_path = "temp_invalid_write.txt"
    # The WriteFileTool.execute method expects 'file_path' and 'content'
    write_call_args_missing_content = {"file_path": invalid_write_path} # Missing 'content'

    write_tool_instance = tool_registry.get_tool_by_name("write_text_file")
    assert write_tool_instance is not None, "write_text_file tool not found in registry"

    # Expecting the tool's execute method to handle missing required parameters
    # Based on WriteFileTool implementation, it expects 'file_path' and 'content'
    # and will likely raise a TypeError or KeyError if 'content' is missing.
    # Let's adjust the assertion based on the expected behavior for missing 'content'.
    # The execute method signature is `execute(self, file_path: str, content: str)`.
    # If called with `execute({"file_path": "..."})`, it will raise a TypeError.
    with pytest.raises(TypeError):
         write_tool_instance.execute(**write_call_args_missing_content)

    # Scenario 3: Simulate AI calling write_text_file with missing file_path
    write_call_args_missing_filepath = {"content": "some content"} # Missing 'file_path'
    with pytest.raises(TypeError):
         write_tool_instance.execute(**write_call_args_missing_filepath)

    # Clean up any potential partial files created by failed write attempts
    if os.path.exists(invalid_write_path):
        os.remove(invalid_write_path)

    # Note: Testing the AI's ability to *generate* invalid tool calls is complex
    # and might be better suited for mocked tests or require very specific prompting
    # and analysis of the AI's raw response before system processing.
    # This test focuses on the system/tool's robustness when *receiving* invalid parameters.