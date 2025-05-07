"""
Unit tests for the format_json postprocessing step.
"""

import unittest
import json
from src.postprocessing.scripted_steps.format_json import format_json

class TestFormatJson(unittest.TestCase):
    """
    Test cases for the format_json postprocessing step.
    """

    def test_format_valid_json_string(self):
        """
        Test that a valid JSON string is formatted correctly.
        Expected: consistent indentation and spacing.
        """
        ugly_json_string = '{\n"name":"TestUgly",\n  "items" : [ 1,2,3 ], "active":true\n}'
        expected_formatted_json = """{
    "name": "TestUgly",
    "items": [
        1,
        2,
        3
    ],
    "active": true
}"""
        content, data = format_json(ugly_json_string, {"logs": []})
        self.assertEqual(content, expected_formatted_json)
        self.assertIn("Successfully parsed and formatted JSON string.", data["logs"])

    def test_format_already_formatted_json_string(self):
        """
        Test that an already well-formatted JSON string remains unchanged in structure
        but is re-serialized (ensuring consistent output from json.dumps).
        """
        formatted_json_string = """{
    "name": "Pretty",
    "version": 1.0,
    "features": [
        "f1",
        "f2"
    ]
}"""
        # json.dumps will re-serialize, so we expect the output of that
        expected_output = json.dumps(json.loads(formatted_json_string), indent=4, ensure_ascii=False)
        content, data = format_json(formatted_json_string, {"logs": []})
        self.assertEqual(content, expected_output)
        self.assertIn("Successfully parsed and formatted JSON string.", data["logs"])

    def test_format_json_string_with_unicode(self):
        """
        Test formatting of JSON string containing unicode characters.
        """
        unicode_json_string = '{"city": "São Paulo", "currency": "R$"}'
        expected_formatted_json = """{
    "city": "São Paulo",
    "currency": "R$"
}"""
        content, data = format_json(unicode_json_string, {"logs": []})
        self.assertEqual(content, expected_formatted_json)
        self.assertIn("Successfully parsed and formatted JSON string.", data["logs"])

    def test_input_is_dictionary(self):
        """
        Test that if the input is already a dictionary, it's returned as is,
        and a log message indicates no formatting was applied.
        """
        input_dict = {"key": "value", "number": 123}
        content, data = format_json(input_dict, {"logs": []})
        self.assertEqual(content, input_dict) # Should be the same object or at least equal
        self.assertIn("Input is a dictionary, no formatting applied. Assumed to be valid.", data["logs"])

    def test_invalid_json_string(self):
        """
        Test that an invalid JSON string is returned as is, and an error is logged.
        """
        invalid_json_string = '{"name": "Test", "items": [1, 2, 3], "details": {"type": "example"}' # Missing closing brace
        content, data = format_json(invalid_json_string, {"logs": []})
        self.assertEqual(content, invalid_json_string)
        self.assertIn("errors", data)
        self.assertTrue(any("Invalid JSON syntax" in error for error in data["errors"]))
        self.assertTrue(any("Invalid JSON syntax" in log for log in data["logs"] if "ERROR:" in log))

    def test_empty_json_string(self):
        """
        Test formatting of an empty JSON object string.
        """
        empty_json_string = '{}'
        expected_formatted_json = "{}" # json.dumps({}, indent=4) might produce "{\n}" or "{ }", let's see.
                                      # After checking, json.dumps({}, indent=4) is just "{}"
        content, data = format_json(empty_json_string, {"logs": []})
        self.assertEqual(content, expected_formatted_json)
        self.assertIn("Successfully parsed and formatted JSON string.", data["logs"])

    def test_empty_json_array_string(self):
        """
        Test formatting of an empty JSON array string.
        """
        empty_array_string = '[]'
        expected_formatted_json = "[]" # Similar to above, json.dumps([], indent=4) is "[]"
        content, data = format_json(empty_array_string, {"logs": []})
        self.assertEqual(content, expected_formatted_json)
        self.assertIn("Successfully parsed and formatted JSON string.", data["logs"])

    def test_data_dict_initialization(self):
        """
        Test that 'logs' and 'errors' keys are initialized in the data dict if not present.
        """
        # Test with logs not present
        content, data = format_json("{}", {})
        self.assertIn("logs", data)
        self.assertIsInstance(data["logs"], list)

        # Test with errors not present (after an error occurs)
        content_err, data_err = format_json("{invalid_json", {})
        self.assertIn("logs", data_err)
        self.assertIn("errors", data_err)
        self.assertIsInstance(data_err["errors"], list)

if __name__ == '__main__':
    unittest.main()