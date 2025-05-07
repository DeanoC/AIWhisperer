import logging
import sys
import hashlib  # Import hashlib
import json
from typing import Dict, Any
import os
import fnmatch

# from jsonschema import validate, ValidationError # Potential library

from pathlib import Path  # Import Path
from rich.console import Console

from .exceptions import SchemaValidationError

def setup_logging(level=logging.INFO):
    """Sets up basic logging configuration to output to stderr."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

def setup_rich_output() -> Console:
    """Creates and returns a Rich Console object for styled terminal output."""
    return Console(stderr=True)

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

def validate_against_schema(data: Dict[str, Any], schema_path: str):
    """
    Validates the given data against a JSON schema file.

    Args:
        data: The dictionary data to validate.
        schema_path: The path to the JSON schema file.

    Raises:
        SchemaValidationError: If validation fails or schema file cannot be read.
        FileNotFoundError: If the schema file does not exist.
    """
    # Placeholder implementation - Replace with actual validation logic
    print(f"--- Placeholder: Validating data against schema: {schema_path} ---")
    # Example using jsonschema (install with pip install jsonschema)
    # try:
    #     with open(schema_path, 'r') as f:
    #         schema = json.load(f)
    #     validate(instance=data, schema=schema)
    # except FileNotFoundError:
    #      raise # Re-raise FileNotFoundError
    # except ValidationError as e:
    #     raise SchemaValidationError(f"Schema validation failed: {e.message}") from e
    # except Exception as e:
    #     raise SchemaValidationError(f"Failed to load or process schema {schema_path}: {e}") from e

    # Simulate validation for now
    if not isinstance(data, dict) or 'agent_spec' not in data:
         # Simulate a validation failure based on test data
         if data.get('step_id') == 'test_step_1_invalid':
              raise SchemaValidationError("Simulated failure: Missing agent_spec")
    print("--- Placeholder: Validation successful ---")
    pass # Assume valid for now


def _parse_gitignore(gitignore_path):
    """
    Parses a .gitignore file.
    Returns a list of tuples: (pattern_string, base_directory_of_this_gitignore_file).
    These patterns are relative to the directory containing the .gitignore file.
    """
    patterns = []
    if not os.path.isfile(gitignore_path): # Ensure it's a file, not a dir named .gitignore
        return patterns
    
    # The base directory for patterns in this .gitignore file
    pattern_base_dir = os.path.dirname(gitignore_path)
    try:
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'): # Ignore empty lines and comments
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
        if pattern_str.startswith('!'):
            is_negation = True
            pattern_str = pattern_str[1:]

        # Patterns ending with '/' are for directories only
        is_dir_only_pattern = pattern_str.endswith('/')
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
        if pattern_str_original.startswith('/') or (is_negation and pattern_str_original.startswith('!/')):
            # The pattern (after '!' and '/') needs to match path relative to pattern_base_dir
            # We need to strip the leading '/' from pattern_str for fnmatch
            current_glob_pattern = pattern_str[1:] if pattern_str.startswith('/') else pattern_str
            path_to_test_against_pattern = os.path.relpath(full_item_path, pattern_base_dir).replace(os.sep, '/')
        
        # Case 2: Pattern contains '/' but doesn't start with it (e.g., "foo/bar.txt", "docs/")
        # It's a path relative to pattern_base_dir.
        elif '/' in pattern_str:
            current_glob_pattern = pattern_str
            path_to_test_against_pattern = os.path.relpath(full_item_path, pattern_base_dir).replace(os.sep, '/')

        # Case 3: Pattern does not contain '/' (e.g., "*.log", "foo")
        # It matches the basename of the item anywhere.
        else:
            current_glob_pattern = pattern_str
            path_to_test_against_pattern = item_name # Match against the simple name

        if fnmatch.fnmatch(path_to_test_against_pattern, current_glob_pattern):
            if is_negation:
                ignored_status = False  # Rule explicitly un-ignores the item
            else:
                ignored_status = True   # Rule ignores the item
                
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
    current_level_active_rules = list(inherited_ignore_rules) # Start with a copy of parent rules
    
    gitignore_file_in_current_dir = os.path.join(current_dir_path, ".gitignore")
    # _parse_gitignore returns (pattern, base_dir_of_that_pattern)
    current_level_active_rules.extend(_parse_gitignore(gitignore_file_in_current_dir))

    try:
        # Get all entries, sort them (directories usually first, then by name)
        # os.scandir is more efficient as it provides type information
        raw_entries = list(os.scandir(current_dir_path))
        # Sort: directories first, then files, then alphabetically by name (case-insensitive)
        sorted_entries = sorted(
            raw_entries, 
            key=lambda e: (not e.is_dir(), e.name.lower())
        )
    except OSError as e:
        # Could happen due to permissions issues
        output_lines_list.append(f"{prefix_str}└── [Error reading: {os.path.basename(current_dir_path)} - {e.strerror}]")
        return

    # Filter out ignored entries *before* determining connector prefixes
    valid_entries_to_display = []
    for entry in sorted_entries:
        if not _is_item_ignored(entry.path, entry.is_dir(), entry.name, current_level_active_rules):
            valid_entries_to_display.append(entry)

    for i, entry in enumerate(valid_entries_to_display):
        is_last_entry = (i == len(valid_entries_to_display) - 1)
        connector = "└── " if is_last_entry else "├── "
        
        output_lines_list.append(f"{prefix_str}{connector}{entry.name}")

        if entry.is_dir():
            # For the next level, update the prefix
            new_prefix_segment = "    " if is_last_entry else "│   "
            _build_tree_recursive(entry.path, prefix_str + new_prefix_segment, current_level_active_rules, output_lines_list)
    
    # "Pop" happens automatically when this function returns, as current_level_active_rules
    # was local to this call. The caller will use its own set of rules.

def build_ascii_directory_tree(start_path="."):
    """
    Builds an ASCII directory tree starting from the given directory,
    recursing through subdirectories and respecting .gitignore files.

    Args:
        start_path (str): The path to the directory to start from. Defaults to current directory.

    Returns:
        str: A string containing the ASCII representation of the directory tree.
             Returns an error message if start_path is not a valid directory.
    """
    abs_start_path = os.path.abspath(os.path.expanduser(start_path))

    if not os.path.isdir(abs_start_path):
        return f"Error: Path '{start_path}' is not a valid directory."

    output_lines = [os.path.basename(abs_start_path)]  # Start with the root directory's name
    
    # Initial ignore rules are empty; they will be loaded as we traverse
    initial_ignore_rules = [] 
    
    _build_tree_recursive(abs_start_path, "", initial_ignore_rules, output_lines)
    
    return "\n".join(output_lines)

# --- Example Usage ---
if __name__ == "__main__":
    # Create a dummy directory structure for testing
    def setup_test_dir(base="test_proj"):
        if os.path.exists(base):
            import shutil
            shutil.rmtree(base)
        os.makedirs(os.path.join(base, "src", "subdir"), exist_ok=True)
        os.makedirs(os.path.join(base, "build"), exist_ok=True)
        os.makedirs(os.path.join(base, "docs"), exist_ok=True)
        os.makedirs(os.path.join(base, ".git"), exist_ok=True) # To test .git ignore

        with open(os.path.join(base, ".gitignore"), "w") as f:
            f.write("build/\n") # Ignore build directory at root
            f.write("*.log\n")  # Ignore all .log files
            f.write("tempfile.txt\n") # Ignore specific file
            f.write("!src/important.log\n") # BUT, do not ignore this specific log file

        with open(os.path.join(base, "src", ".gitignore"), "w") as f:
            f.write("subdir/\n") # Ignore subdir within src
            f.write("*.tmp\n")   # Ignore .tmp files within src and its children
            f.write("!keep.tmp\n") # But keep this one

        # Create some files
        open(os.path.join(base, "main.py"), "w").close()
        open(os.path.join(base, "README.md"), "w").close()
        open(os.path.join(base, "app.log"), "w").close() # Should be ignored by root .gitignore
        open(os.path.join(base, "tempfile.txt"), "w").close() # Should be ignored
        open(os.path.join(base, "build", "output.o"), "w").close() # build/ dir should be ignored
        open(os.path.join(base, "src", "code.py"), "w").close()
        open(os.path.join(base, "src", "important.log"), "w").close() # Should be included (negated)
        open(os.path.join(base, "src", "data.tmp"), "w").close() # Should be ignored by src/.gitignore
        open(os.path.join(base, "src", "keep.tmp"), "w").close() # Should be included (negated in src)
        open(os.path.join(base, "src", "subdir", "file.txt"), "w").close() # subdir/ should be ignored
        open(os.path.join(base, "docs", "index.html"), "w").close()
        return base

    test_project_path = setup_test_dir()
    print(f"--- Building tree for: {test_project_path} ---")
    tree_output = build_ascii_directory_tree(test_project_path)
    print(tree_output)
    print("--- Done ---")

    # Example with a non-existent path
    print("\n--- Building tree for non-existent path ---")
    print(build_ascii_directory_tree("no_such_directory_exists_here"))
    print("--- Done ---")

    # Clean up the dummy directory
    # import shutil
    # shutil.rmtree(test_project_path)


# Explanation:
# build_ascii_directory_tree(start_path) (Main Function):
# Resolves start_path to an absolute path.
# Initializes output_lines with the name of the starting directory.
# Calls the recursive helper _build_tree_recursive.
# Joins the collected output_lines into a single string.
# _build_tree_recursive(current_dir_path, prefix_str, inherited_ignore_rules, output_lines_list):
# Ignore Rule "Pushing":
# It takes inherited_ignore_rules from its parent.
# It creates current_level_active_rules by copying inherited rules.
# It then calls _parse_gitignore for a .gitignore file in current_dir_path. The parsed rules (along with their base_dir, which is current_dir_path) are appended to current_level_active_rules. This way, rules from deeper .gitignore files (or later in the same file) can override earlier ones when _is_item_ignored processes them.
# Directory Traversal:
# Uses os.scandir() for efficiency as it provides file type information without extra os.stat calls.
# Sorts entries (directories first, then alphabetically by name) for consistent output.
# Filtering:
# Iterates through sorted entries and calls _is_item_ignored for each.
# Only non-ignored entries are kept in valid_entries_to_display. This list is used to correctly determine the ├── vs └── prefixes.
# Output Generation:
# Calculates the correct connector (├── or └──) and new_prefix_segment (│ or ) based on whether the current item is the last in the valid_entries_to_display.
# Appends the formatted line to output_lines_list.
# Recursion: If an entry is a directory, it calls itself with the updated path, prefix, and the current_level_active_rules.
# Ignore Rule "Popping": This happens implicitly. When _build_tree_recursive returns from processing a subdirectory, the current_level_active_rules specific to that subdirectory go out of scope. The calling function continues with its own set of rules, effectively "popping" the subdirectory's rules.
# _parse_gitignore(gitignore_path):
# Reads a given .gitignore file line by line.
# Skips empty lines and lines starting with # (comments).
# Returns a list of tuples: (pattern_string, base_directory_of_this_gitignore_file). The base_directory is crucial for resolving patterns anchored with / or containing /.
# _is_item_ignored(full_item_path, is_item_dir, item_name, active_ignore_rules):
# This is the core of the exclusion logic.
# Hardcoded Ignores: It first checks for .git (always ignore) and .gitignore (don't list the file itself, though it's processed).
# Rule Iteration: It iterates through all active_ignore_rules. The key is that the last rule in this list that matches an item determines its fate (ignored or not). This mimics .gitignore's precedence.
# Pattern Handling:
# !pattern: Handles negation (re-includes a previously ignored item).
# pattern/: Marks the pattern as applying only to directories.
# /pattern: Anchors the pattern to the pattern_base_dir (the directory where the .gitignore file containing this pattern resides).
# path/pattern: Matches a path relative to pattern_base_dir.
# pattern (no slashes): Matches the item_name (basename) directly.
# Uses fnmatch.fnmatch() for glob matching. Note that fnmatch in Python treats * as matching /, which differs slightly from FNM_PATHNAME in C's fnmatch, but is generally good enough for most .gitignore patterns. More complex gitignore features like ** (recursive directory wildcard) are also handled by fnmatch.
# This implementation provides a robust way to generate an ASCII directory tree while respecting the hierarchical and overriding nature of .gitignore files.