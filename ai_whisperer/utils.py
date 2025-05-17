import logging
import sys
import hashlib  # Import hashlib
import json
from typing import Dict, Any
import os
import fnmatch
from pathlib import Path 


def setup_logging(level=logging.INFO):
    """Sets up basic logging configuration to output to stderr."""
    # Add debug logging to confirm setup_logging is invoked
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr)


def calculate_sha256(file_path: str | Path) -> str:
    """
    Calculates the SHA-256 hash of a file's content.

    Args:
        file_path: The path to the file (as a string or Path object).

    Returns:
        The hexadecimal representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    path = Path(file_path)
    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read and update hash string content in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        # Re-raise FileNotFoundError for clarity
        raise FileNotFoundError(f"File not found: {file_path}")
    except IOError as e:
        # Raise a more general IOError for other read issues
        raise IOError(f"Error reading file {file_path}: {e}") from e

def save_json_to_file(data: Dict[str, Any], output_path: str | Path):
    """
    Saves a dictionary as a JSON file with indentation.

    Args:
        data: The dictionary to save.
        output_path: The path to the output JSON file (as a string or Path object).
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)  # Ensure output directory exists
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    return path
def _parse_gitignore(gitignore_path):
    """
    Parses a .gitignore file.
    Returns a list of tuples: (pattern_string, base_directory_of_this_gitignore_file).
    These patterns are relative to the directory containing the .gitignore file.
    """
    patterns = []
    if not os.path.isfile(gitignore_path):  # Ensure it's a file, not a dir named .gitignore
        return patterns

    # The base directory for patterns in this .gitignore file
    pattern_base_dir = os.path.dirname(gitignore_path)
    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):  # Ignore empty lines and comments
                    patterns.append((line, pattern_base_dir))
    except IOError:
        # Fail silently if .gitignore is unreadable (e.g., permissions)
        # print(f"Warning: Could not read {gitignore_path}") # Optional warning
        pass
    return patterns


def _is_item_ignored(full_item_path, is_item_dir, item_name, active_ignore_rules):
    """
    Checks if an item should be ignored based on the current set of active_ignore_rules.
    The rules are a list of (pattern_str, pattern_base_dir) tuples.
    The LAST matching rule in the list determines the outcome (ignored or not ignored).
    This mimics how .gitignore files override parent rules or later rules override earlier ones.
    """
    # --- Hardcoded essential ignores ---
    # .git directory is almost universally ignored in such tools
    if item_name == ".git":
        return True
    # We process .gitignore files, but don't list them in the tree
    if item_name == ".gitignore":
        return True

    ignored_status = False  # Default: not ignored by any rule yet

    for pattern_str_original, pattern_base_dir in active_ignore_rules:
        pattern_str = pattern_str_original
        is_negation = False
        if pattern_str.startswith("!"):
            is_negation = True
            pattern_str = pattern_str[1:]

        # Patterns ending with '/' are for directories only
        is_dir_only_pattern = pattern_str.endswith("/")
        if is_dir_only_pattern:
            pattern_str = pattern_str[:-1]

        # If a pattern is for directories only, and the current item is not a directory,
        # this rule doesn't apply to this item (it might apply to its parent if it were a dir).
        if is_dir_only_pattern and not is_item_dir:
            continue

        # Determine the path string to test against the pattern
        # Gitignore patterns use forward slashes.
        path_to_test_against_pattern = ""

        # Case 1: Pattern starts with '/' (e.g., "/foo.txt", "/build/")
        # It's anchored to the root of the directory containing the .gitignore file (pattern_base_dir).
        if pattern_str_original.startswith("/") or (is_negation and pattern_str_original.startswith("!/")):
            # The pattern (after '!' and '/') needs to match path relative to pattern_base_dir
            # We need to strip the leading '/' from pattern_str for fnmatch
            current_glob_pattern = pattern_str[1:] if pattern_str.startswith("/") else pattern_str
            path_to_test_against_pattern = os.path.relpath(full_item_path, pattern_base_dir).replace(os.sep, "/")

        # Case 2: Pattern contains '/' but doesn't start with it (e.g., "foo/bar.txt", "docs/")
        # It's a path relative to pattern_base_dir.
        elif "/" in pattern_str:
            current_glob_pattern = pattern_str
            path_to_test_against_pattern = os.path.relpath(full_item_path, pattern_base_dir).replace(os.sep, "/")

        # Case 3: Pattern does not contain '/' (e.g., "*.log", "foo")
        # It matches the basename of the item anywhere.
        else:
            current_glob_pattern = pattern_str
            path_to_test_against_pattern = item_name  # Match against the simple name

        if fnmatch.fnmatch(path_to_test_against_pattern, current_glob_pattern):
            if is_negation:
                ignored_status = False  # Rule explicitly un-ignores the item
            else:
                ignored_status = True  # Rule ignores the item

    return ignored_status


def _build_tree_recursive(current_dir_path, prefix_str, inherited_ignore_rules, output_lines_list):
    """
    Internal recursive function to build the tree.
    - current_dir_path: The directory currently being processed.
    - prefix_str: The prefix string for indentation and tree lines.
    - inherited_ignore_rules: Rules from parent directories' .gitignore files.
    - output_lines_list: The list to which output lines are appended.
    """
    # 1. "Push" .gitignore rules: Combine inherited rules with rules from the current directory
    current_level_active_rules = list(inherited_ignore_rules)  # Start with a copy of parent rules

    gitignore_file_in_current_dir = os.path.join(current_dir_path, ".gitignore")
    # _parse_gitignore returns (pattern, base_dir_of_that_pattern)
    current_level_active_rules.extend(_parse_gitignore(gitignore_file_in_current_dir))

    try:
        # Get all entries, sort them (directories usually first, then by name)
        # os.scandir is more efficient as it provides type information
        raw_entries = list(os.scandir(current_dir_path))
        # Sort: directories first, then files, then alphabetically by name (case-insensitive)
        sorted_entries = sorted(raw_entries, key=lambda e: (not e.is_dir(), e.name.lower()))
    except OSError as e:
        # Could happen due to permissions issues
        output_lines_list.append(
            f"{prefix_str}└── [Error reading: {os.path.basename(current_dir_path)} - {e.strerror}]"
        )
        return

    # Filter out ignored entries *before* determining connector prefixes
    valid_entries_to_display = []
    for entry in sorted_entries:
        if not _is_item_ignored(entry.path, entry.is_dir(), entry.name, current_level_active_rules):
            valid_entries_to_display.append(entry)

    for i, entry in enumerate(valid_entries_to_display):
        is_last_entry = i == len(valid_entries_to_display) - 1
        connector = "└── " if is_last_entry else "├── "

        output_lines_list.append(f"{prefix_str}{connector}{entry.name}")

        if entry.is_dir():
            # For the next level, update the prefix
            new_prefix_segment = "    " if is_last_entry else "│   "
            _build_tree_recursive(
                entry.path, prefix_str + new_prefix_segment, current_level_active_rules, output_lines_list
            )

    # "Pop" happens automatically when this function returns, as current_level_active_rules
    # was local to this call. The caller will use its own set of rules.


def build_ascii_directory_tree(start_path=".", ignore=None):
    """
    Builds an ASCII directory tree starting from the given directory,
    recursing through subdirectories and respecting .gitignore files and an explicit ignore list.

    Args:
        start_path (str): The path to the directory to start from. Defaults to current directory.
        ignore (list[str] | None): List of file or directory names or relative paths to ignore.

    Returns:
        str: A string containing the ASCII representation of the directory tree.
             Returns an error message if start_path is not a valid directory.
    """
    abs_start_path = os.path.abspath(os.path.expanduser(start_path))
    ignore_patterns = set(ignore) if ignore else set()

    if not os.path.isdir(abs_start_path):
        return f"Error: Path '{start_path}' is not a valid directory."

    output_lines = [os.path.basename(abs_start_path)]  # Start with the root directory's name

    # Initial ignore rules are empty; they will be loaded as we traverse
    initial_ignore_rules = []

    def _should_ignore(entry_path, entry_name):
        """
        Checks if the entry should be ignored based on ignore_patterns.
        Supports both basenames and relative paths with slashes.
        """
        rel_path = os.path.relpath(entry_path, abs_start_path).replace(os.sep, "/")
        # Check for direct match with pattern (e.g., 'foo/bar'), or basename match (e.g., 'foo')
        return (
            entry_name in ignore_patterns or
            rel_path in ignore_patterns or
            any(fnmatch.fnmatch(rel_path, pat) for pat in ignore_patterns)
        )

    def _build_tree_recursive_with_explicit_ignore(current_dir_path, prefix_str, inherited_ignore_rules, output_lines_list):
        current_level_active_rules = list(inherited_ignore_rules)
        gitignore_file_in_current_dir = os.path.join(current_dir_path, ".gitignore")
        current_level_active_rules.extend(_parse_gitignore(gitignore_file_in_current_dir))

        try:
            raw_entries = list(os.scandir(current_dir_path))
            sorted_entries = sorted(raw_entries, key=lambda e: (not e.is_dir(), e.name.lower()))
        except OSError as e:
            output_lines_list.append(
                f"{prefix_str}└── [Error reading: {os.path.basename(current_dir_path)} - {e.strerror}]"
            )
            return

        valid_entries_to_display = []
        for entry in sorted_entries:
            if _should_ignore(entry.path, entry.name):
                continue
            if not _is_item_ignored(entry.path, entry.is_dir(), entry.name, current_level_active_rules):
                valid_entries_to_display.append(entry)

        for i, entry in enumerate(valid_entries_to_display):
            is_last_entry = i == len(valid_entries_to_display) - 1
            connector = "└── " if is_last_entry else "├── "

            output_lines_list.append(f"{prefix_str}{connector}{entry.name}")

            if entry.is_dir():
                new_prefix_segment = "    " if is_last_entry else "│   "
                _build_tree_recursive_with_explicit_ignore(
                    entry.path, prefix_str + new_prefix_segment, current_level_active_rules, output_lines_list
                )

    _build_tree_recursive_with_explicit_ignore(abs_start_path, "", initial_ignore_rules, output_lines)

    return "\n".join(output_lines)
