import unittest
from unittest.mock import patch, MagicMock, mock_open
import os

# Assuming the refine logic is in src/ai_whisperer/main.py and uses OpenRouterAPI
# We will need to mock the relevant parts of main.py and openrouter_api.py
# Since the refine command is not yet fully implemented, we will mock the expected interactions.


# Mock the OpenRouterAPI and its call_chat_completion method
class MockOpenRouterAPI:
    def __init__(self, config):
        pass

    def call_chat_completion(self, prompt_text: str, model: str, params: dict) -> str:
        # This will be replaced by a MagicMock in the tests
        pass


# Mock the main refine function or relevant logic within main.py
# This is a placeholder and will need to be adjusted based on the actual implementation
def mock_refine_command_logic(input_file: str, output_dir: str = ".", iterations: int = 1, custom_prompt: str = None):
    """
    Mock function to simulate the core logic of the refine command for testing.
    In a real scenario, this would call OpenRouterAPI and handle file saving.
    """
    # Simulate reading the input file
    try:
        with open(input_file, "r") as f:
            requirements_content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Simulate prompt construction
    default_prompt = "Refine the following requirements:\n\n"
    prompt_to_send = custom_prompt if custom_prompt is not None else default_prompt + requirements_content

    # Simulate AI interaction
    # In the actual test, this call will be mocked
    ai_response_content = MockOpenRouterAPI({}).call_chat_completion(prompt_to_send, "mock-model", {})

    # Simulate file saving with iteration numbering
    (base_name, ext) = os.path.splitext(os.path.basename(input_file))
    output_file_template = os.path.join(output_dir, f"{base_name}_v{{}}{ext}")

    saved_files = []
    for i in range(1, iterations + 1):
        output_file_path = output_file_template.format(i)
        # In the actual test, this open call will be mocked
        with open(output_file_path, "w") as f:
            f.write(f"Refined content iteration {i}:\n{ai_response_content}")
        saved_files.append(output_file_path)

    return saved_files


class TestRefineAIInteraction(unittest.TestCase):
    @patch("ai_whisperer.ai_service_interaction.OpenRouterAPI", new=MockOpenRouterAPI)
    @patch("builtins.open", new_callable=mock_open)
    @patch("tests.unit.test_refine_ai_interaction.MockOpenRouterAPI.call_chat_completion")
    def test_prompt_construction_default(self, mock_call_chat_completion, mock_file_open):
        """
        Test that the default prompt is constructed correctly.
        """
        mock_call_chat_completion.return_value = "Mocked AI response"
        mock_file_open.return_value = MagicMock()  # Ensure mock_open returns a mock file object

        input_file_content = "Original requirements content."
        mock_file_open.side_effect = [
            mock_open(read_data=input_file_content).return_value,  # For reading input file
            mock_open().return_value,  # For writing output file
        ]

        # Simulate calling the refine logic
        # This needs to be adjusted based on where the actual refine logic resides
        # For now, we call our mock_refine_command_logic
        with patch("builtins.open", new_callable=mock_open) as mock_file_open_inner:
            mock_file_open_inner.side_effect = [
                mock_open(read_data=input_file_content).return_value,  # For reading input file
                mock_open().return_value,  # For writing output file
            ]
            mock_refine_command_logic("test_requirements.md", iterations=1)

            # Assert that call_chat_completion was called with the correct default prompt
            expected_prompt = "Refine the following requirements:\n\n" + input_file_content
            mock_call_chat_completion.assert_called_once_with(expected_prompt, "mock-model", {})
            mock_file_open_inner.assert_any_call(os.path.join(".", "test_requirements_v1.md"), "w")

    @patch("ai_whisperer.ai_service_interaction.OpenRouterAPI", new=MockOpenRouterAPI)
    @patch("builtins.open", new_callable=mock_open)
    @patch("tests.unit.test_refine_ai_interaction.MockOpenRouterAPI.call_chat_completion")
    def test_prompt_construction_custom(self, mock_call_chat_completion, mock_file_open):
        """
        Test that a custom prompt is used when provided.
        """
        mock_call_chat_completion.return_value = "Mocked AI response"
        mock_file_open.return_value = MagicMock()

        input_file_content = "Original requirements content."
        custom_prompt_content = "Please improve these requirements:"
        mock_file_open.side_effect = [
            mock_open(read_data=input_file_content).return_value,  # For reading input file
            mock_open().return_value,  # For writing output file
        ]

        # Simulate calling the refine logic with a custom prompt
        with patch("builtins.open", new_callable=mock_open) as mock_file_open_inner:
            mock_file_open_inner.side_effect = [
                mock_open(read_data=input_file_content).return_value,  # For reading input file
                mock_open().return_value,  # For writing output file
            ]
            mock_refine_command_logic("test_requirements.md", iterations=1, custom_prompt=custom_prompt_content)

            # Assert that call_chat_completion was called with the custom prompt
            mock_call_chat_completion.assert_called_once_with(custom_prompt_content, "mock-model", {})
            mock_file_open_inner.assert_any_call(os.path.join(".", "test_requirements_v1.md"), "w")

    @patch("ai_whisperer.ai_service_interaction.OpenRouterAPI", new=MockOpenRouterAPI)
    @patch("builtins.open", new_callable=mock_open)
    @patch("tests.unit.test_refine_ai_interaction.MockOpenRouterAPI.call_chat_completion")
    def test_handle_mocked_ai_response_and_save(self, mock_call_chat_completion, mock_file_open):
        """
        Test that the mocked AI response is handled and saved correctly.
        """
        mock_ai_response = "This is the refined content from the AI."
        mock_call_chat_completion.return_value = mock_ai_response
        mock_file_open.return_value = MagicMock()

        input_file_content = "Original requirements content."
        read_handle_mock = mock_open(read_data=input_file_content).return_value
        write_handle_mock = mock_open().return_value  # This is the mock for the file handle itself

        mock_file_open.side_effect = [read_handle_mock, write_handle_mock]

        # Simulate calling the refine logic
        # We use the mock_file_open directly which is already patched at the class level
        # No need for an inner patch if the outer one is correctly configured and used.
        # However, the current structure uses mock_file_open_inner for assertions.

        # Let's keep the inner patch for now to minimize changes, but ensure it uses distinct mock handles
        # if we want to inspect them separately from the class-level mock_file_open.

        # Create specific mock handles for the inner context
        inner_read_handle_mock = mock_open(read_data=input_file_content).return_value
        inner_write_handle_mock = mock_open().return_value

        with patch("builtins.open", new_callable=mock_open) as mock_file_open_inner:
            # Assign the specific mock handles to the side_effect of this inner mock
            mock_file_open_inner.side_effect = [inner_read_handle_mock, inner_write_handle_mock]
            mock_refine_command_logic("test_requirements.md", iterations=1)

            # Assert that the file was opened for writing with the correct name
            mock_file_open_inner.assert_any_call(os.path.join(".", "test_requirements_v1.md"), "w")

            # Assert that the mocked AI response was written to the file
            # Now, inner_write_handle_mock is the specific mock object we want to check
            self.assertIsNotNone(inner_write_handle_mock, "Write mock handle not found")
            inner_write_handle_mock.write.assert_called_once_with(f"Refined content iteration 1:\n{mock_ai_response}")

    @patch("ai_whisperer.ai_service_interaction.OpenRouterAPI", new=MockOpenRouterAPI)
    @patch("builtins.open", new_callable=mock_open)
    @patch("tests.unit.test_refine_ai_interaction.MockOpenRouterAPI.call_chat_completion")
    def test_file_saving_with_iterations(self, mock_call_chat_completion, mock_file_open):
        """
        Test that files are saved with correct iteration numbering.
        """
        mock_ai_response = "Mocked AI response"
        mock_call_chat_completion.return_value = mock_ai_response
        mock_file_open.return_value = MagicMock()

        input_file_content = "Original requirements content."
        # Create side effect for multiple file opens (read input + write outputs)
        mock_file_open_side_effects = [mock_open(read_data=input_file_content).return_value]
        for _ in range(3):  # For 3 iterations
            mock_file_open_side_effects.append(mock_open().return_value)

        mock_file_open.side_effect = mock_file_open_side_effects

        # Simulate calling the refine logic with 3 iterations
        with patch("builtins.open", new_callable=mock_open) as mock_file_open_inner:
            mock_file_open_inner.side_effect = mock_file_open_side_effects
            mock_refine_command_logic("test_requirements.md", iterations=3)

            # Assert that files were opened for writing with correct iteration names
            expected_calls = [
                (os.path.join(".", "test_requirements_v1.md"), "w"),
                (os.path.join(".", "test_requirements_v2.md"), "w"),
                (os.path.join(".", "test_requirements_v3.md"), "w"),
            ]
            # Check the calls made to open for writing (skipping the first read call)
            # The first call to mock_file_open_inner is reading the input file.
            # The subsequent calls are for writing the output files.
            write_calls = [
                call_args[0]
                for call_args in mock_file_open_inner.call_args_list
                if call_args[0][1] == "w"  # Filter for write calls
            ]
            self.assertEqual(len(write_calls), 3)
            for i, expected_call in enumerate(expected_calls):
                self.assertEqual(write_calls[i], expected_call)

        # Assert that the correct content was written to each file
        # This requires accessing the write calls for each mocked file handle
        # This part is a bit more complex with mock_open side_effect and might need refinement
        # For simplicity, we'll just check the file names were correct for now.
        # A more robust test would iterate through the mock file handles created by the side_effect
        # and check their write calls.


if __name__ == "__main__":
    unittest.main()
