import pytest
import json
from postprocessing.scripted_steps.escape_text_fields import escape_text_fields


@pytest.mark.parametrize(
    "description, input_content, expected_content_after_parse, log_message_part, is_error_case",
    [
        # Case: Valid JSON string - no changes needed by this step
        (
            "Valid JSON string",
            '{"key": "value", "text": "This is a string: with a colon."}',
            {"key": "value", "text": "This is a string: with a colon."},
            "Input is a valid JSON string. No escaping applied by this step.",
            False,
        ),
        (
            "Valid JSON array string",
            '[1, "string with spaces", {"nested": "value: more text"}]',
            [1, "string with spaces", {"nested": "value: more text"}],
            "Input is a valid JSON string. No escaping applied by this step.",
            False,
        ),
        # Case: Input is already a dictionary or list
        (
            "Input is dictionary",
            {"key": "value", "text": "A string: with colon"},
            {"key": "value", "text": "A string: with colon"},
            "Input is a dict, no escaping performed by this step.",
            False,
        ),
        (
            "Input is list",
            [1, "string with colon:", {"nested": "value"}],
            [1, "string with colon:", {"nested": "value"}],
            "Input is a list, no escaping performed by this step.",
            False,
        ),
        # Case: Invalid JSON string - should be returned as is, error logged
        (
            "Invalid JSON string (missing quote)",
            '{"key": "value, "text": "missing end quote}',
            '{"key": "value, "text": "missing end quote}',
            "Failed to parse content as JSON in escape_text_fields",
            True,
        ),
        (
            "Invalid JSON string (trailing comma)",
            '{"key": "value",}',
            '{"key": "value",}',
            "Failed to parse content as JSON in escape_text_fields",
            True,
        ),
        # Case: Empty or whitespace string
        ("Empty string", "", "", "Input content is empty or whitespace-only.", False),  # No error, just a log
        (
            "Whitespace string",
            "   \n\t  ",
            "   \n\t  ",
            "Input content is empty or whitespace-only.",
            False,
        ),  # No error
        # Case: JSON string that is not an object or list at root (but still valid JSON)
        # This step doesn't care about root type, only if it's parsable JSON.
        # The validate_syntax step would catch if root is not object/list.
        (
            "JSON string literal",
            '"a string literal"',
            "a string literal",
            "Input is a valid JSON string. No escaping applied by this step.",
            False,
        ),
        ("JSON number literal", "123", 123, "Input is a valid JSON string. No escaping applied by this step.", False),
    ],
)
def test_escape_text_fields_json(
    description, input_content, expected_content_after_parse, log_message_part, is_error_case
):
    """
    Tests the escape_text_fields function with JSON content.
    For JSON, this step primarily checks if a string input is valid JSON.
    Actual escaping is handled by json.dumps during final serialization.
    """
    data = {"logs": [], "errors": []}
    (output_content, result_data) = escape_text_fields(input_content, data)

    # The output content should be the same as input if it's a string or dict/list
    assert output_content == input_content, f"Test: {description} - Output content mismatch"

    assert "logs" in result_data, f"Test: {description} - Missing logs"
    assert any(
        log_message_part in log for log in result_data["logs"]
    ), f"Test: {description} - Expected log message part '{log_message_part}' not found in logs: {result_data['logs']}"

    if is_error_case:
        assert "errors" in result_data, f"Test: {description} - Missing errors array for an error case"
        assert len(result_data["errors"]) > 0, f"Test: {description} - Errors array is empty for an error case"
        assert any(
            log_message_part in err for err in result_data["errors"]
        ), f"Test: {description} - Expected error message part '{log_message_part}' not found in errors: {result_data['errors']}"
    else:
        # For non-error string cases, try to parse the output_content to verify it's still valid
        if isinstance(output_content, str) and output_content.strip() and not is_error_case:
            try:
                parsed_output = json.loads(output_content)
                assert (
                    parsed_output == expected_content_after_parse
                ), f"Test: {description} - Parsed output does not match expected"
            except json.JSONDecodeError:
                pytest.fail(
                    f"Test: {description} - Output content was not valid JSON after processing: {output_content}"
                )
        elif isinstance(output_content, (dict, list)):
            assert (
                output_content == expected_content_after_parse
            ), f"Test: {description} - Dict/List output does not match expected"


def test_escape_text_fields_unsupported_type():
    """
    Test that an unsupported input type logs an error and returns content as is.
    """
    input_content = 12345  # Integer, not str, dict, or list
    data = {"logs": [], "errors": []}
    (output_content, result_data) = escape_text_fields(input_content, data)

    assert output_content == input_content
    assert any("Unsupported content type" in log for log in result_data["logs"] if "ERROR" in log.upper())
    assert any("Unsupported content type" in err for err in result_data["errors"])
