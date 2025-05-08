import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import fnmatch
import pathlib # Import pathlib directly for OriginalPath

# Helper function to simulate the file renaming logic
def _determine_next_refine_filename(input_filepath_str):
    """Simulates the logic to determine the next refined filename."""
    input_filepath = pathlib.Path(input_filepath_str) # Use pathlib.Path
    parent_dir = input_filepath.parent
    stem = input_filepath.stem
    suffix = input_filepath.suffix

    # Find existing refined files for this stem
    # Use os.listdir and fnmatch as the original (intended) logic would likely do
    # Ensure parent_dir is a string or an object that os.listdir can handle
    # If parent_dir is a mock, it needs to be configured to return a string representation
    # or os.listdir needs to be patched to handle the mock.
    # For simplicity, we'll assume parent_dir is correctly handled by os.listdir or is a string.
    existing_files = os.listdir(str(parent_dir)) # Use str(parent_dir)
    # The pattern should match files like 'input_iteration1.md', 'input_iteration10.md', etc.
    # It should NOT match the original file 'input.md'
    refined_pattern = f"{stem}_iteration*.{suffix.lstrip('.')}"
    matching_files = [f for f in existing_files if fnmatch.fnmatch(f, refined_pattern)]

    # Determine the highest iteration number
    max_iteration = 0
    for filename in matching_files:
        try:
            # Extract the number between '_iteration' and '.'
            # Example: 'input_iteration12.md' -> '12'
            parts = filename.split('_iteration')
            if len(parts) == 2:
                number_part_with_suffix = parts[1]
                number_part = number_part_with_suffix.rsplit('.', 1)[0] # Split from right to handle dots in stem if any
                iteration = int(number_part)
                max_iteration = max(max_iteration, iteration)
        except ValueError:
            # Ignore files that don't have a valid number after '_iteration'
            continue
        except IndexError:
             # Ignore files that don't have a suffix after the number
             continue


    next_iteration = max_iteration + 1
    next_filename = f"{stem}_iteration{next_iteration}{suffix}"
    # Use os.path.join for platform-independent path construction
    return os.path.join(str(parent_dir), next_filename)


# Remove tests that rely on the non-existent CLI command handling in main.py
# test_parse_input_file and test_handle_nonexistent_file are removed.

OriginalPath = pathlib.Path # Use pathlib.Path

# Patch os, fnmatch, and pathlib.Path as used by the module-level helper
@patch('os.listdir')
@patch('fnmatch.fnmatch')
@patch('pathlib.Path')
def test_rename_first_iteration(mock_path_constructor, mock_fnmatch, mock_os_listdir):
    """Test file renaming logic for the first iteration (N=1)."""
    input_filepath_str = 'path/to/input.md'

    # Configure mocks for file system operations
    mock_input_file_path_obj = MagicMock(spec=OriginalPath) # Use OriginalPath for spec
    # Ensure parent returns an OriginalPath object or a string that os.listdir can handle
    # Let's make parent return an OriginalPath object to mimic real Path behavior
    mock_input_file_path_obj.parent = OriginalPath('path/to')
    mock_input_file_path_obj.stem = 'input'
    mock_input_file_path_obj.suffix = '.md'
    mock_input_file_path_obj.__str__ = MagicMock(return_value=input_filepath_str) # For str(input_filepath)

    # Configure the Path constructor mock
    # It should return our mock_input_file_path_obj when called with input_filepath_str
    # For other calls (like Path(parent_dir) inside the helper), it should return a real Path object
    def path_side_effect(path_arg):
        if str(path_arg) == input_filepath_str:
            return mock_input_file_path_obj
        # If Path is called with the parent directory string, return the parent mock or a real Path
        elif str(path_arg) == str(mock_input_file_path_obj.parent):
             # This case might be tricky if Path() is called with the parent object itself.
             # For now, assume it's called with a string representation.
            return OriginalPath(path_arg) # Return a real Path object for other calls
        return OriginalPath(path_arg) # Default to real Path object

    mock_path_constructor.side_effect = path_side_effect
    # Ensure Path() can also be called with the parent path string by the helper
    # The side_effect should handle this. We also need to mock `Path(parent_dir)` inside the helper if parent_dir is a mock.
    # The `_determine_next_refine_filename` uses `Path(parent_dir)` at the end.

    # Simulate no existing iteration files
    mock_os_listdir.return_value = ['input.md', 'other_file.txt']
    # fnmatch should return False for the original file and True for potential iteration files
    mock_fnmatch.side_effect = lambda name, pattern: name.startswith('input_iteration') and name.endswith('.md') and pattern == 'input_iteration*.md'

    # Call the module-level helper function
    next_filename = _determine_next_refine_filename(input_filepath_str)

    # Assertions for file renaming logic
    # Use os.path.join for expected path for consistency
    expected_filename = os.path.join(str(OriginalPath('path/to')), 'input_iteration1.md')
    assert next_filename == expected_filename

    # Check that Path constructor was called with the input file path string
    mock_path_constructor.assert_any_call(input_filepath_str)
    # Check that listdir was called with the string representation of the parent directory
    mock_os_listdir.assert_called_once_with(str(OriginalPath('path/to')))
    # Check that fnmatch was called for relevant files with the correct pattern
    # These calls happen inside the list comprehension within the helper
    assert mock_fnmatch.call_count >= 2 # Called for 'input.md' and 'other_file.txt'
    mock_fnmatch.assert_any_call('input.md', 'input_iteration*.md')
    mock_fnmatch.assert_any_call('other_file.txt', 'input_iteration*.md')


# Patch os, fnmatch, and pathlib.Path as used by the module-level helper
@patch('os.listdir')
@patch('fnmatch.fnmatch')
@patch('pathlib.Path')
def test_rename_subsequent_iteration(mock_path_constructor, mock_fnmatch, mock_os_listdir):
    """Test file renaming logic for subsequent iterations (N incrementing)."""
    input_filepath_str = 'path/to/input.md'

    mock_input_file_path_obj = MagicMock(spec=OriginalPath) # Use OriginalPath for spec
    mock_input_file_path_obj.parent = OriginalPath('path/to')
    mock_input_file_path_obj.stem = 'input'
    mock_input_file_path_obj.suffix = '.md'
    mock_input_file_path_obj.__str__ = MagicMock(return_value=input_filepath_str)

    def path_side_effect(path_arg):
        if str(path_arg) == input_filepath_str:
            return mock_input_file_path_obj
        return OriginalPath(path_arg)
    mock_path_constructor.side_effect = path_side_effect

    # Simulate existing iteration files up to _iteration2.md
    mock_os_listdir.return_value = ['input.md', 'input_iteration1.md', 'input_iteration2.md', 'other_file.txt']
    # fnmatch should return True only for the iteration files
    mock_fnmatch.side_effect = lambda name, pattern: \
        name in ['input_iteration1.md', 'input_iteration2.md'] and pattern == 'input_iteration*.md'

    next_filename = _determine_next_refine_filename(input_filepath_str)

    expected_filename = os.path.join(str(OriginalPath('path/to')), 'input_iteration3.md')
    assert next_filename == expected_filename

    mock_path_constructor.assert_any_call(input_filepath_str)
    mock_os_listdir.assert_called_once_with(str(OriginalPath('path/to')))
    # Exact call count for fnmatch can be tricky due to list comprehension.
    # Ensure it was called for the relevant files.
    assert mock_fnmatch.call_count >= 4
    mock_fnmatch.assert_any_call('input.md', 'input_iteration*.md')
    mock_fnmatch.assert_any_call('input_iteration1.md', 'input_iteration*.md')
    mock_fnmatch.assert_any_call('input_iteration2.md', 'input_iteration*.md')
    mock_fnmatch.assert_any_call('other_file.txt', 'input_iteration*.md')


# Patch os, fnmatch, and pathlib.Path as used by the module-level helper
@patch('os.listdir')
@patch('fnmatch.fnmatch')
@patch('pathlib.Path')
def test_rename_with_different_suffix(mock_path_constructor, mock_fnmatch, mock_os_listdir):
    """Test file renaming logic with a different file suffix."""
    input_filepath_str = 'path/to/input.txt'

    mock_input_file_path_obj = MagicMock(spec=OriginalPath) # Use OriginalPath for spec
    mock_input_file_path_obj.parent = OriginalPath('path/to')
    mock_input_file_path_obj.stem = 'input'
    mock_input_file_path_obj.suffix = '.txt'
    mock_input_file_path_obj.__str__ = MagicMock(return_value=input_filepath_str)

    def path_side_effect(path_arg):
        if str(path_arg) == input_filepath_str:
            return mock_input_file_path_obj
        return OriginalPath(path_arg)
    mock_path_constructor.side_effect = path_side_effect

    # Simulate existing iteration files with .txt suffix
    mock_os_listdir.return_value = ['input.txt', 'input_iteration1.txt', 'other_file.md']
    # fnmatch should return True only for the iteration files with .txt suffix
    mock_fnmatch.side_effect = lambda name, pattern: \
        name == 'input_iteration1.txt' and pattern == 'input_iteration*.txt'

    next_filename = _determine_next_refine_filename(input_filepath_str)

    expected_filename = os.path.join(str(OriginalPath('path/to')), 'input_iteration2.txt')
    assert next_filename == expected_filename

    mock_path_constructor.assert_any_call(input_filepath_str)
    mock_os_listdir.assert_called_once_with(str(OriginalPath('path/to')))
    assert mock_fnmatch.call_count >= 3
    mock_fnmatch.assert_any_call('input.txt', 'input_iteration*.txt')
    mock_fnmatch.assert_any_call('input_iteration1.txt', 'input_iteration*.txt')
    mock_fnmatch.assert_any_call('other_file.md', 'input_iteration*.txt')


