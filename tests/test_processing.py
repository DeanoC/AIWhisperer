import pytest
import json
from pathlib import Path
from src.ai_whisperer.exceptions import ProcessingError

# Import the actual functions
from src.ai_whisperer.processing import read_markdown, save_json, format_prompt, process_response


# --- Tests for read_markdown ---


def test_read_markdown_success(tmp_path):
    """Test reading a valid Markdown file."""
    content = "# Header\n\nSome text."
    md_file = tmp_path / "test.md"
    md_file.write_text(content, encoding="utf-8")
    assert read_markdown(str(md_file)) == content


def test_read_markdown_file_not_found():
    """Test reading a non-existent file."""
    with pytest.raises(ProcessingError, match="File not found"):
        read_markdown("non_existent_file.md")


def test_read_markdown_empty_file(tmp_path):
    """Test reading an empty Markdown file."""
    md_file = tmp_path / "empty.md"
    md_file.touch()
    assert read_markdown(str(md_file)) == ""


def test_read_markdown_encoding_error(tmp_path):
    """Test reading a file with non-UTF-8 encoding (if UTF-8 is enforced)."""
    # Simulate non-UTF-8 content that causes a decoding error
    content_bytes = b"\xff\xfeH\x00e\x00l\x00l\x00o\x00"  # Example UTF-16 bytes
    md_file = tmp_path / "encoding_error.md"
    md_file.write_bytes(content_bytes)
    # Expecting a ProcessingError wrapping the UnicodeDecodeError
    with pytest.raises(ProcessingError, match="Error reading file"):
        read_markdown(str(md_file))


# --- Tests for save_json ---


def test_save_json_success(tmp_path):
    """Test saving a dictionary to a JSON file."""
    data = {"key1": "value1", "list": [1, 2, 3], "nested": {"nk": "nv"}}
    json_file = tmp_path / "output.json"
    save_json(data, str(json_file))

    assert json_file.exists()
    with open(json_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == data


def test_save_json_empty_dict(tmp_path):
    """Test saving an empty dictionary."""
    data = {}
    json_file = tmp_path / "empty_output.json"
    save_json(data, str(json_file))

    assert json_file.exists()
    with open(json_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == {}


def test_save_json_overwrite(tmp_path):
    """Test overwriting an existing JSON file."""
    initial_data = {"old": "data"}
    json_file = tmp_path / "overwrite.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f)

    new_data = {"new": "content"}
    save_json(new_data, str(json_file))

    assert json_file.exists()
    with open(json_file, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)
    assert loaded_data == new_data
    assert loaded_data != initial_data


# --- Tests for format_prompt ---


def test_format_prompt_basic():
    """Test basic prompt formatting."""
    template = "Analyze this: {md_content}\nUse model: {model_name}"
    md_content = "# Requirement\nDetails here."
    config_vars = {"model_name": "gpt-4", "other_var": "ignored"}
    expected = "Analyze this: # Requirement\nDetails here.\nUse model: gpt-4"
    assert format_prompt(template, md_content, config_vars) == expected


def test_format_prompt_missing_vars_in_template():
    """Test when template doesn't use all provided vars."""
    template = "Content: {md_content}"
    md_content = "Some markdown."
    config_vars = {"model_name": "claude-3", "temperature": 0.5}
    expected = "Content: Some markdown."
    assert format_prompt(template, md_content, config_vars) == expected


def test_format_prompt_no_vars_in_template():
    """Test when template has no placeholders."""
    template = "Just static text."
    md_content = "Input markdown."
    config_vars = {"model_name": "gemini-pro"}
    expected = "Just static text."
    assert format_prompt(template, md_content, config_vars) == expected


# --- Tests for process_response ---


def test_process_response_valid_json():
    """Test processing a valid JSON string response."""
    response_str = '{"key": "value", "list": ["item1", "item2"]}'
    expected_dict = {"key": "value", "list": ["item1", "item2"]}
    assert process_response(response_str) == expected_dict


def test_process_response_nested_json():
    """Test processing valid JSON with nested structure."""
    response_str = '{"outer": {"inner": {"key": "value", "num": 123}}}'
    expected_dict = {"outer": {"inner": {"key": "value", "num": 123}}}
    assert process_response(response_str) == expected_dict


def test_process_response_empty_string():
    """Test processing an empty string response."""
    with pytest.raises(ProcessingError, match="Error parsing API response JSON: Empty response"):
        process_response("")


def test_process_response_invalid_json():
    """Test processing an invalid JSON string."""
    response_str = '{"key": "value", "extra_indent": "problem"'  # Missing closing brace
    with pytest.raises(ProcessingError, match="Error parsing API response JSON:"):
        process_response(response_str)


def test_process_response_non_json_string():
    """Test processing a string that isn't JSON."""
    response_str = "This is just plain text, not JSON."
    with pytest.raises(ProcessingError, match="Error parsing API response JSON:"):
        process_response(response_str)
