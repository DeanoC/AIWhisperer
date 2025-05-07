import unittest
from unittest.mock import patch, mock_open, MagicMock, call
import argparse
import csv
import io
import sys
from pathlib import Path

# Mock data for detailed model information
MOCK_DETAILED_MODELS_DATA = [
    {
        "id": "model-1",
        "name": "Model One",
        "pricing": {"prompt": "0.001", "completion": "0.002"},
        "description": "Description of Model One",
        "features": ["chat", "completion"],
        "context_window": 8192,
        "input_cost": 0.001,
        "output_cost": 0.002,
    },
    {
        "id": "model-2",
        "name": "Model Two",
        "pricing": {"prompt": "0.003", "completion": "0.004"},
        "description": "Description of Model Two",
        "features": ["chat"],
        "context_window": 4096,
        "input_cost": 0.003,
        "output_cost": 0.004,
    },
]

# Expected CSV header and data
EXPECTED_CSV_HEADER = ["id", "name", "description", "features", "context_window", "input_cost", "output_cost"]
EXPECTED_CSV_DATA = [
    ["model-1", "Model One", "Description of Model One", ["chat", "completion"], "8192", "0.001", "0.002"],
    ["model-2", "Model Two", "Description of Model Two", ["chat"], "4096", "0.003", "0.004"],
]

class TestMainListModels(unittest.TestCase):

    @patch('src.ai_whisperer.main.OpenRouterAPI')
    @patch('sys.argv', ['ai-whisperer', '--list-models'])
    def test_list_models_no_csv_output(self, mock_openrouter_api):
        # Test case where --output-csv is not provided
        mock_api_instance = mock_openrouter_api.return_value
        mock_api_instance.list_models.return_value = MOCK_DETAILED_MODELS_DATA

        # Mock load_config to return a minimal config with openrouter section
        mock_config = {'openrouter': {'api_key': 'fake_key'}}
        with patch('src.ai_whisperer.main.load_config', return_value=mock_config):
            from src.ai_whisperer.main import main
            with self.assertRaises(SystemExit) as cm:
                main()

        # Assert that the exit code was 0
        self.assertEqual(cm.exception.code, 0)

        # Assert that list_models was called
        mock_api_instance.list_models.assert_called_once()

        # Note: Asserting rich console output is complex with simple mocks.
        # We are skipping detailed console output assertions for now, focusing on core functionality.


    @patch('rich.console.Console')
    @patch('src.ai_whisperer.main.OpenRouterAPI')
    @patch('builtins.open', new_callable=mock_open)
    @patch('sys.argv', ['ai-whisperer', '--list-models', '--output-csv', 'output.csv'])
    def test_list_models_with_csv_output(self, mock_builtin_open, mock_openrouter_api, mock_console):
        # Test case where --output-csv is provided
        csv_filepath = "output.csv"
        mock_api_instance = mock_openrouter_api.return_value
        mock_api_instance.list_models.return_value = MOCK_DETAILED_MODELS_DATA
        mock_console_instance = mock_console.return_value

        # Create a StringIO object to capture the written content
        mock_csv_file = io.StringIO()
        mock_builtin_open.return_value = mock_csv_file
        # Prevent the mocked file from being closed by the 'with open' block in main
        mock_csv_file.close = MagicMock()

        # Mock load_config to return a minimal config with openrouter section
        mock_config = {'openrouter': {'api_key': 'fake_key'}}
        with patch('src.ai_whisperer.main.load_config', return_value=mock_config):
            from src.ai_whisperer.main import main
            with self.assertRaises(SystemExit) as cm:
                main()

        # Assert that the exit code was 0
        self.assertEqual(cm.exception.code, 0)

        # Assert that list_models was called
        mock_api_instance.list_models.assert_called_once()

        # Assert that the file was opened with the correct parameters
        mock_builtin_open.assert_called_once_with(Path(csv_filepath), 'w', newline='', encoding='utf-8')
        
        # Get the written content and read it as CSV
        mock_csv_file.seek(0) # Rewind the StringIO object
        csv_reader = csv.reader(mock_csv_file)
        written_rows = list(csv_reader)

        # Assert that the header and data rows match
        self.assertEqual(written_rows[0], EXPECTED_CSV_HEADER)
        
        # Compare data rows, converting features list to string for comparison if necessary
        # Note: The main code writes features as a list, which csv.writer handles by default
        # We need to ensure our comparison handles this.
        # Let's adjust EXPECTED_CSV_DATA to match the list format
        
        # Re-define EXPECTED_CSV_DATA to match the string representation of list features in CSV
        EXPECTED_CSV_DATA_LIST_FEATURES = [
            ["model-1", "Model One", "Description of Model One", "['chat', 'completion']", "8192", "0.001", "0.002"],
            ["model-2", "Model Two", "Description of Model Two", "['chat']", "4096", "0.003", "0.004"],
        ]

        self.assertEqual(written_rows[1:], EXPECTED_CSV_DATA_LIST_FEATURES)


if __name__ == '__main__':
    unittest.main()