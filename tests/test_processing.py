import pytest
import yaml
from pathlib import Path
from src.ai_whisperer.exceptions import ProcessingError
# Import the actual functions
from src.ai_whisperer.processing import read_markdown, save_yaml, format_prompt, process_response


# --- Tests for read_markdown ---

def test_read_markdown_success(tmp_path):
    """Test reading a valid Markdown file."""
    content = "# Header\n\nSome text."
    md_file = tmp_path / "test.md"
    md_file.write_text(content, encoding='utf-8')
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
    content_bytes = b'\xff\xfeH\x00e\x00l\x00l\x00o\x00' # Example UTF-16 bytes
    md_file = tmp_path / "encoding_error.md"
    md_file.write_bytes(content_bytes)
    # Expecting a ProcessingError wrapping the UnicodeDecodeError
    with pytest.raises(ProcessingError, match="Error reading file"):
        read_markdown(str(md_file))


# --- Tests for save_yaml ---

def test_save_yaml_success(tmp_path):
    """Test saving a dictionary to a YAML file."""
    data = {'key1': 'value1', 'list': [1, 2, 3], 'nested': {'nk': 'nv'}}
    yaml_file = tmp_path / "output.yaml"
    save_yaml(data, str(yaml_file))

    assert yaml_file.exists()
    with open(yaml_file, 'r', encoding='utf-8') as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data == data

def test_save_yaml_empty_dict(tmp_path):
    """Test saving an empty dictionary."""
    data = {}
    yaml_file = tmp_path / "empty_output.yaml"
    save_yaml(data, str(yaml_file))

    assert yaml_file.exists()
    with open(yaml_file, 'r', encoding='utf-8') as f:
        loaded_data = yaml.safe_load(f)
    # yaml.safe_load might return None for an empty file representing an empty dict
    assert loaded_data == {} or loaded_data is None

def test_save_yaml_overwrite(tmp_path):
    """Test overwriting an existing YAML file."""
    initial_data = {'old': 'data'}
    yaml_file = tmp_path / "overwrite.yaml"
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(initial_data, f)

    new_data = {'new': 'content'}
    save_yaml(new_data, str(yaml_file))

    assert yaml_file.exists()
    with open(yaml_file, 'r', encoding='utf-8') as f:
        loaded_data = yaml.safe_load(f)
    assert loaded_data == new_data
    assert loaded_data != initial_data


# --- Tests for format_prompt ---

def test_format_prompt_basic():
    """Test basic prompt formatting."""
    template = "Analyze this: {md_content}\nUse model: {model_name}"
    md_content = "# Requirement\nDetails here."
    config_vars = {'model_name': 'gpt-4', 'other_var': 'ignored'}
    expected = "Analyze this: # Requirement\nDetails here.\nUse model: gpt-4"
    assert format_prompt(template, md_content, config_vars) == expected

def test_format_prompt_missing_vars_in_template():
    """Test when template doesn't use all provided vars."""
    template = "Content: {md_content}"
    md_content = "Some markdown."
    config_vars = {'model_name': 'claude-3', 'temperature': 0.5}
    expected = "Content: Some markdown."
    assert format_prompt(template, md_content, config_vars) == expected

def test_format_prompt_no_vars_in_template():
    """Test when template has no placeholders."""
    template = "Just static text."
    md_content = "Input markdown."
    config_vars = {'model_name': 'gemini-pro'}
    expected = "Just static text."
    assert format_prompt(template, md_content, config_vars) == expected


# --- Tests for process_response ---

def test_process_response_valid_yaml():
    """Test processing a valid YAML string response."""
    response_text = "task: Generate code\ndescription: Implement feature X."
    expected = {'task': 'Generate code', 'description': 'Implement feature X.'}
    assert process_response(response_text) == expected

def test_process_response_nested_yaml():
    """Test processing valid YAML with nested structure."""
    response_text = "-\n  step: 1\n  action: Read file\n-\n  step: 2\n  action: Analyze content"
    expected = [
        {'step': 1, 'action': 'Read file'},
        {'step': 2, 'action': 'Analyze content'}
    ]
    assert process_response(response_text) == expected

def test_process_response_invalid_yaml():
    """Test processing an invalid YAML string."""
    response_text = "task: Generate code\n description: Invalid indentation"
    with pytest.raises(ProcessingError, match="Error parsing API response YAML"):
        process_response(response_text)

def test_process_response_empty_string():
    """Test processing an empty string response."""
    response_text = ""
    # Expecting an error because empty string is not valid YAML for a dict/list
    with pytest.raises(ProcessingError, match="Error parsing API response YAML: Empty response"):
        process_response(response_text)

def test_process_response_non_yaml_string():
    """Test processing a string that isn't YAML."""
    response_text = "This is just plain text, not YAML."
    with pytest.raises(ProcessingError, match="Error parsing API response YAML"):
        process_response(response_text)

