"""Comprehensive tests for preserving metadata, comments, docstrings, and formatting.

These tests verify that contextual information like comments, docstrings, source locations,
and formatting preferences are preserved through the Python ↔ JSON conversion pipeline.
"""

import pytest
import ast
import json
import textwrap
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestDocstringPreservation:
    """Test preservation of docstrings in various contexts."""
    
    def test_module_docstring_preservation(self):
        """Test that module-level docstrings are preserved."""
        test_cases = [
            # Simple module docstring
            '''"""Module docstring."""
x = 1
''',
            # Multi-line module docstring
            '''"""Module docstring.

This is a longer description
with multiple paragraphs.

And even more details.
"""

import os
''',
            # Module with only docstring
            '''"""Just a docstring module."""''',
            
            # Raw string docstring
            '''r"""Raw docstring with \n escapes."""
code = True
''',
        ]
        
        for code in test_cases:
                        result = self._convert_and_verify_docstring(code, 'module')
    assert result['docstring_preserved']
            assert result['docstring_exact_match']
            assert result['location_preserved']
    
def test_function_docstring_preservation(self):
    """Test that function docstrings are preserved."""
    test_cases = [
        # Simple function docstring
        '''
def simple():
"""Simple docstring."""
pass
''',
        # Multi-line function docstring with formatting
        '''
def complex(x: int, y: str) -> bool:
"""
Complex function with detailed documentation.
    
Args:
    x: An integer parameter
    y: A string parameter
        
Returns:
    bool: The result of the operation
        
Raises:
    ValueError: If x is negative
        
Examples:
    >>> complex(1, "test")
    True
"""
return True
''',
        # Nested function with docstring
        '''
def outer():
"""Outer function."""
def inner():
    """Inner function."""
    pass
return inner
''',
        # Async function with docstring
        '''
async def async_func():
"""Async function documentation."""
await something()
''',
        # Lambda with preceding comment (not a docstring)
        '''
# This lambda doubles the input
doubler = lambda x: x * 2
''',
    ]
        
    for code in test_cases:
        result = self._convert_and_verify_docstring(code, 'function')
            assert result['docstring_preserved']
            assert result['indentation_preserved']
    
def test_class_docstring_preservation(self):
    """Test that class and method docstrings are preserved."""
    test_cases = [
        # Class with docstring
        '''
class Simple:
"""Simple class docstring."""
pass
''',
        # Class with method docstrings
        '''
class Complex:
"""Main class docstring."""
    
def __init__(self):
    """Constructor docstring."""
    pass
    
def method(self):
    """Method docstring."""
    pass
    
@property
def prop(self):
    """Property docstring."""
    return self._prop
    
@staticmethod
def static():
    """Static method docstring."""
    pass
    
class Inner:
    """Nested class docstring."""
    pass
''',
        # Dataclass with field documentation
        '''
@dataclass
class Data:
"""Dataclass with field docs."""
    
name: str
"""The name field."""
    
value: int = 0
"""The value field with default."""
''',
    ]
        
    for code in test_cases:
        result = self._convert_and_verify_docstring(code, 'class')
            assert result['all_docstrings_preserved']
            assert result['hierarchy_maintained']
    
def test_docstring_special_cases(self):
    """Test special docstring cases and edge conditions."""
    test_cases = [
        # Unicode in docstring
        '''
def unicode_doc():
"""Unicode: αβγ 中文 🎉 émojis"""
pass
''',
        # Docstring with quotes
        '''
def quotes():
"""This has 'single' and "double" quotes."""
pass
''',
        # Triple single quotes
        """
def triple_single():
'''Triple single quote docstring.'''
pass
""",
        # Raw docstring
        '''
def raw_doc():
r"""Raw string with \n \t \r characters."""
pass
''',
        # Empty docstring
        '''
def empty_doc():
""""""
pass
''',
        # Docstring that looks like code
        '''
def code_like():
"""
def example():
    return 42
"""
pass
''',
    ]
        
    for code in test_cases:
        result = self._convert_and_verify_docstring(code, 'special')
            assert result['special_chars_preserved']
            assert result['format_preserved']
    
def _convert_and_verify_docstring(self, code: str, context: str) -> Dict[str, Any]:
    """Convert code and verify docstring preservation."""
    raise NotImplementedError("Docstring verification not implemented")

class TestSourceLocationMetadata:
    """Test preservation of source location information."""
    
    def test_basic_location_preservation(self):
        """Test that line numbers and column offsets are preserved."""
        code = '''
x = 1
y = 2

def func():
    return x + y

class MyClass:
    pass
'''
        
        result = self._convert_and_verify_locations(code)
        assert result['all_line_numbers_preserved']
        assert result['all_column_offsets_preserved']
        assert result['end_positions_preserved']
    
def test_complex_location_preservation(self):
    """Test location preservation in complex structures."""
    code = '''
# Line 1
def complex_function(
param1: int,  # Line 3
param2: str = "default",
*args,
keyword_only: bool = True,
**kwargs
) -> Optional[Dict[str, Any]]:
"""Docstring on line 9."""
if param1 > 0:  # Line 11
    result = {
        'key': 'value',
        'nested': {
            'deep': True
        }
    }
    return result
else:
    return None
'''
        
    result = self._convert_and_verify_locations(code)
        assert result['multiline_preserved']
        assert result['nested_locations_correct']
        assert result['comment_line_numbers_noted']
    
def test_location_with_decorators(self):
    """Test location preservation with decorators."""
    code = '''
@decorator1
@decorator2(arg=value)
@decorator3(
multi_line_arg=True
)
def decorated_function():
pass

@dataclass
class DecoratedClass:
field: int
'''
        
    result = self._convert_and_verify_locations(code)
        assert result['decorator_locations_preserved']
        assert result['decorated_item_location_correct']
    
def test_location_in_comprehensions(self):
    """Test location preservation in comprehensions."""
    code = '''
# List comprehension
result = [
x * 2
for x in range(10)
if x % 2 == 0
]

# Nested comprehension
matrix = [
[
    i * j
    for j in range(3)
]
for i in range(3)
]

# Dict comprehension with complex formatting
mapping = {
key: value
for key, value in items
if value > threshold
}
'''
        
    result = self._convert_and_verify_locations(code)
        assert result['comprehension_parts_located']
        assert result['nested_comprehension_locations']
    
def test_location_edge_cases(self):
    """Test location preservation in edge cases."""
    test_cases = [
        # Single line with multiple statements
        "x = 1; y = 2; z = 3",
            
        # Line continuation
        """x = 1 + \\
2 + \\
3""",
            
        # Parenthetical continuation
        """result = (
first_part +
second_part +
third_part
)""",
        # Empty lines and whitespace
        """

x = 1

y = 2

""",
        ]
        
        for code in test_cases:
                        result = self._convert_and_verify_locations(code)
            assert result['continuation_handled']
            assert result['whitespace_positions_noted']
    
def _convert_and_verify_locations(self, code: str) -> Dict[str, Any]:
    """Convert code and verify location preservation."""
    raise NotImplementedError("Location verification not implemented")

class TestCommentPreservation:
    """Test preservation of comments where possible."""
    
    def test_comment_detection_and_storage(self):
        """Test that comments are detected and stored separately."""
        code = '''
# Module level comment
"""Module docstring."""

# Import comment
import os  # inline import comment

# Function comment
def func():  # inline function comment
    # Inside function comment
    x = 1  # inline assignment
    # Before return
    return x  # inline return

# Class comment
class MyClass:  # inline class comment
    # Inside class comment
    pass

# End of file comment
'''
        
        result = self._convert_and_extract_comments(code)
        assert len(result['comments']) > 0
        assert result['comment_positions_tracked']
        assert result['inline_comments_separate']
        assert result['comment_associations_mapped']
    
def test_multiline_comment_blocks(self):
    """Test preservation of multi-line comment blocks."""
    code = '''
# This is a multi-line
# comment block that should
# be treated as a unit
def func():
    """Docstring."""
    # Another multi-line
    # comment inside function
    # with multiple lines
    pass

###############################################
# Section separator comment
###############################################

# TODO: This is a todo comment
# FIXME: This needs fixing
# NOTE: Important note here
'''
        
        result = self._convert_and_extract_comments(code)
        assert result['multiline_blocks_detected']
        assert result['special_comments_marked']
        assert result['separator_comments_noted']
    
def test_comment_preservation_strategies(self):
    """Test different strategies for preserving comments."""
    code = '''
def calculate(x, y):
# Step 1: Validate inputs
if x < 0 or y < 0:
    raise ValueError("Negative values not allowed")
    
# Step 2: Perform calculation
result = x * y  # Multiply the values
    
# Step 3: Apply transformation
# This is a complex transformation
# that requires multiple steps
if result > 100:
    result = result / 2  # Halve large results
    
return result  # Return final result
'''
        
    result = self._test_comment_preservation_strategy(code)
        assert result['comment_metadata_stored']
        assert result['comment_reconstruction_possible']
        assert result['relative_positions_maintained']
    
def test_comment_unicode_and_special_chars(self):
    """Test comments with unicode and special characters."""
    code = '''
# Comment with unicode: αβγ 中文 🎉
def func():
# Comment with special chars: @#$%^&*()
x = 1  # λ expression would go here
    
# URL in comment: https://example.com/path?query=1
# Email in comment: user@example.com
# Regex in comment: /^[a-z]+$/
    
return x
'''
        
    result = self._convert_and_extract_comments(code)
        assert result['unicode_preserved']
        assert result['special_chars_intact']
        assert result['urls_not_corrupted']
    
def test_comment_reconstruction_accuracy(self):
    """Test accuracy of comment reconstruction after round-trip."""
    test_cases = [
        # Comments at different positions
        '''
# Before class
class Test:  # After class
# Inside class
def method(self):  # After method
    # Inside method
    pass  # After pass
# After everything
''',
        # Comments with various indentations
        '''
def nested():
# Level 1
if True:
    # Level 2
    for i in range(10):
        # Level 3
        if i % 2:
            # Level 4
            pass
''',
    ]
        
    for code in test_cases:
        result = self._test_comment_reconstruction(code)
            assert result['position_accuracy'] > 0.9
            assert result['indentation_preserved']
            assert result['association_maintained']
    
def _convert_and_extract_comments(self, code: str) -> Dict[str, Any]:
    """Convert code and extract comment information."""
    raise NotImplementedError("Comment extraction not implemented")
    
def _test_comment_preservation_strategy(self, code: str) -> Dict[str, Any]:
    """Test comment preservation strategy."""
    raise NotImplementedError("Comment strategy testing not implemented")
    
def _test_comment_reconstruction(self, code: str) -> Dict[str, Any]:
    """Test comment reconstruction accuracy."""
    raise NotImplementedError("Comment reconstruction not implemented")

class TestFormattingPreservation:
    """Test preservation of formatting preferences and whitespace."""
    
    def test_indentation_style_preservation(self):
        """Test that indentation style is preserved or noted."""
        test_cases = [
            # 4-space indentation (PEP 8 standard)
            '''
def four_spaces():
    if True:
        x = 1
        return x
''',
            # 2-space indentation
            '''
def two_spaces():
  if True:
    x = 1
    return x
''',
            # Tab indentation
            '''
def tabs():
\tif True:
\t\tx = 1
\t\treturn x
''',
            # Mixed (bad practice but should handle)
            '''
def mixed():
    if True:
\t\tx = 1  # This is mixed
        return x
''',
        ]
        
        for code in test_cases:
                        result = self._analyze_formatting(code)
            assert result['indentation_style_detected']
            assert result['indentation_consistency_checked']
            assert result['indentation_metadata_stored']
    
def test_line_length_preferences(self):
    """Test detection of line length preferences."""
    test_cases = [
        # Short lines (< 80 chars)
        '''
def short_lines():
x = 1
y = 2
return x + y
''',
        # Long lines (> 80 chars)
        '''
def long_lines():
result = some_very_long_function_name_that_exceeds_eighty_characters(parameter1, parameter2, parameter3)
return result
''',
        # Mixed with line breaks for length
        '''
def mixed_length():
short = 1
long_result = (
    first_part_of_expression +
    second_part_of_expression +
    third_part_of_expression
)
return long_result
''',
    ]
        
    for code in test_cases:
        result = self._analyze_formatting(code)
            assert result['line_length_stats_calculated']
            assert result['break_preferences_noted']
    
def test_blank_line_patterns(self):
    """Test preservation of blank line patterns."""
    code = '''
import os
import sys

from typing import Dict, List

class FirstClass:
    """First class."""
    
    def method1(self):
        pass
    
    def method2(self):
        pass


class SecondClass:
    """Second class."""
    
    def __init__(self):
        self.value = 1
        
        self.computed = self.value * 2


def standalone_function():
    """Standalone function."""
    pass


# Constants
CONSTANT_1 = 1
CONSTANT_2 = 2


if __name__ == "__main__":
    main()
'''
        
        result = self._analyze_formatting(code)
        assert result['blank_line_patterns_detected']
        assert result['pep8_compliance_checked']
        assert result['section_separation_noted']
    
def test_string_quote_preferences(self):
    """Test detection of string quote preferences."""
    test_cases = [
        # Single quotes preferred
        '''
name = 'single'
message = 'Hello, world!'
items = ['a', 'b', 'c']
''',
        # Double quotes preferred
        '''
name = "double"
message = "Hello, world!"
items = ["a", "b", "c"]
''',
        # Mixed usage
        '''
name = 'single'
message = "double"
sql = """triple double"""
raw = r'raw single'
''',
    ]
        
    for code in test_cases:
        result = self._analyze_formatting(code)
            assert result['quote_preference_detected']
            assert result['quote_consistency_measured']
    
def test_operator_spacing_preferences(self):
    """Test detection of operator spacing preferences."""
    test_cases = [
        # Spaces around operators (PEP 8)
        '''
x = 1 + 2
y = x * 3
z = y / 4
result = x > 0 and y < 10
''',
        # No spaces (compact style)
        '''
x=1+2
y=x*3
z=y/4
result=x>0 and y<10
''',
        # Mixed spacing
        '''
x = 1+2  # Mixed
y = x * 3
z=y / 4
''',
    ]
        
    for code in test_cases:
        result = self._analyze_formatting(code)
            assert result['operator_spacing_analyzed']
            assert result['consistency_score_calculated']
    
def test_import_organization_style(self):
    """Test detection of import organization style."""
    test_cases = [
        # PEP 8 style grouping
        '''
import os
import sys

import numpy as np
import pandas as pd

from mypackage import module1
from mypackage import module2
''',
        # Alphabetical without grouping
        '''
import numpy as np
import os
import pandas as pd
import sys
from mypackage import module1
from mypackage import module2
''',
        # All on individual lines vs multiple
        '''
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, namedtuple
''',
    ]
        
    for code in test_cases:
        result = self._analyze_formatting(code)
            assert result['import_style_detected']
            assert result['import_grouping_analyzed']
    
def _analyze_formatting(self, code: str) -> Dict[str, Any]:
    """Analyze formatting preferences in code."""
    raise NotImplementedError("Formatting analysis not implemented")

class TestMetadataRoundTrip:
    """Test complete round-trip with all metadata preserved."""
    
    def test_complete_metadata_preservation(self):
        """Test that all metadata is preserved in a complete round-trip."""
        code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module with complete metadata.

This module demonstrates preservation of:
- Docstrings
- Comments  
- Formatting
- Location data
"""

import os
import sys
from typing import Optional, List

# Constants section
DEFAULT_VALUE = 42  # The answer
MAX_RETRIES = 3


class DataProcessor:
    """Process data with various methods."""
    
    def __init__(self, config: dict):
        """
        Initialize processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._cache = {}  # Internal cache
    
    def process(self, data: List[str]) -> Optional[str]:
        """
        Process a list of strings.
        
        This method handles:
        - Validation
        - Transformation
        - Caching
        
        Args:
            data: Input strings to process
            
        Returns:
            Processed result or None
        """
        # Step 1: Validate input
        if not data:
            return None
        
        # Step 2: Check cache
        cache_key = str(data)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Step 3: Process data
        result = " ".join(data)  # Simple joining
        
        # Step 4: Cache and return
        self._cache[cache_key] = result
        return result


def main():
    """Main entry point."""
    processor = DataProcessor({"debug": True})
    result = processor.process(["Hello", "World"])
    print(result)


if __name__ == "__main__":
    main()
'''
        
        result = self._test_complete_round_trip(code)
        assert result['all_docstrings_intact']
        assert result['all_comments_trackable']
        assert result['all_locations_accurate']
        assert result['formatting_style_preserved']
        assert result['semantic_equivalence']
        assert result['metadata_fidelity_score'] > 0.95
    
def test_metadata_in_json_structure(self):
    """Test the structure of metadata in JSON representation."""
    code = '''
def example(x: int) -> int:
"""Double the input."""
# Multiply by 2
return x * 2
'''
        
    json_result = self._convert_to_json_with_metadata(code)
            
        # Check JSON structure
        assert 'ast' in json_result
        assert 'metadata' in json_result
        assert 'comments' in json_result
        assert 'formatting' in json_result
            
        # Check metadata content
        metadata = json_result['metadata']
        assert 'source_hash' in metadata
        assert 'line_count' in metadata
        assert 'encoding' in metadata
            
        # Check comment storage
        comments = json_result['comments']
        assert isinstance(comments, list)
        assert all('line' in c and 'text' in c for c in comments)
            
        # Check formatting info
        formatting = json_result['formatting']
        assert 'indentation' in formatting
        assert 'line_endings' in formatting
        assert 'quote_style' in formatting
    
def test_metadata_reconstruction_options(self):
    """Test different options for reconstructing code with metadata."""
    code = '''
# Important function
def calculate(x, y):
"""Calculate result."""
return x + y  # Add them
'''
        
    # Test different reconstruction modes
        modes = [
            'minimal',      # Just the code
            'docstrings',   # Code + docstrings  
            'comments',     # Code + comments
            'formatted',    # Code + original formatting
            'complete'      # Everything preserved
        ]
            
        for mode in modes:
            result = self._reconstruct_with_mode(code, mode)
            assert result['mode_applied'] == mode
            assert result['reconstruction_valid']
    
def test_metadata_compatibility(self):
    """Test metadata compatibility across versions."""
    code = '''
def simple():
"""Simple function."""
pass
'''
        
    # Convert with current version
        json_v1 = self._convert_to_json_with_metadata(code)
            
        # Simulate version change
        json_v2 = self._migrate_metadata_format(json_v1)
            
        # Should still reconstruct correctly
        result = self._reconstruct_from_json(json_v2)
        assert result['backward_compatible']
        assert result['forward_compatible']
    
def test_large_file_metadata_performance(self):
    """Test metadata handling performance with large files."""
    # Generate large code
    lines = []
    for i in range(1000):
        lines.append(f"# Comment for function {i}")
        lines.append(f"def func_{i}():")
        lines.append(f'    """Docstring for function {i}."""')
        lines.append(f"    value = {i}  # Process value")
        lines.append(f"    return value * 2")
        lines.append("")
        
    large_code = "\n".join(lines)
        
    result = self._test_metadata_performance(large_code)
        assert result['processing_time_ms'] < 1000
        assert result['memory_overhead_percent'] < 50
        assert result['metadata_size_ratio'] < 2.0
    
def _test_complete_round_trip(self, code: str) -> Dict[str, Any]:
    """Test complete round-trip with metadata."""
    raise NotImplementedError("Complete round-trip not implemented")
    
def _convert_to_json_with_metadata(self, code: str) -> Dict[str, Any]:
    """Convert code to JSON with all metadata."""
    raise NotImplementedError("Metadata conversion not implemented")
    
def _reconstruct_with_mode(self, code: str, mode: str) -> Dict[str, Any]:
    """Reconstruct code with specific metadata mode."""
    raise NotImplementedError("Mode reconstruction not implemented")
    
def _migrate_metadata_format(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Migrate metadata format for compatibility testing."""
    raise NotImplementedError("Metadata migration not implemented")
    
def _reconstruct_from_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct code from JSON with metadata."""
    raise NotImplementedError("JSON reconstruction not implemented")
    
def _test_metadata_performance(self, code: str) -> Dict[str, Any]:
    """Test metadata handling performance."""
    raise NotImplementedError("Performance testing not implemented")

class TestEdgeCasesAndErrors:
    """Test edge cases and error conditions for metadata preservation."""
    
    def test_malformed_docstrings(self):
        """Test handling of malformed or unusual docstrings."""
        test_cases = [
            # Docstring not on first line
            '''
def bad():
    x = 1
    """This docstring is not first."""
    return x
''',
            # Multiple string literals
            '''
def multiple():
    """First string."""
    """Second string."""
    pass
''',
            # Docstring with triple quotes inside
            '''
def nested_quotes():
    """This has """ inside it."""
    pass
''',
        ]
        
        for code in test_cases:
                        result = self._test_edge_case_handling(code)
            assert result['handled_gracefully']
            assert result['no_data_loss']
    
def test_extreme_formatting(self):
    """Test handling of extreme formatting cases."""
    test_cases = [
        # Single line with semicolons
        "def f(): x = 1; y = 2; return x + y",
            
        # Extremely long lines
        "x = " + " + ".join([f"var{i}" for i in range(50)]),
            
        # Deeply nested structures
        "x = " + "(" * 50 + "1" + ")" * 50,
            
        # Unicode identifiers and comments
        """
# 这是中文注释
def 函数():
变量 = 42
return 变量
""",
    ]
        
    for code in test_cases:
        result = self._test_edge_case_handling(code)
            assert result['parsing_successful']
            assert result['metadata_extracted']
    
def test_comment_edge_cases(self):
    """Test edge cases in comment handling."""
    test_cases = [
        # Comment-like strings
        '''
x = "# This is not a comment"
y = '# Neither is this'
z = """# Nor this
# Multiple lines
"""
''',
        # Comments in string literals
        '''
sql = """
SELECT * FROM table  -- SQL comment
WHERE id = 1  # Not a Python comment
"""
''',
        # Encoding declarations
        '''
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
x = 1
''',
    ]
        
    for code in test_cases:
        result = self._test_edge_case_handling(code)
            assert result['comments_correctly_identified']
            assert result['string_content_preserved']
    
def test_error_recovery(self):
    """Test recovery from errors during metadata extraction."""
    test_cases = [
        # Syntax error but salvage metadata
        ("def func(\n    '''Docstring.'''\n    pass", "syntax_error"),
            
        # Incomplete code
        ("def func():\n    '''Docstring.'''\n    x = ", "incomplete"),
            
        # Invalid encoding in comment
        ("# \udcff Invalid encoding\nx = 1", "encoding_error"),
    ]
        
    for code, error_type in test_cases:
        result = self._test_error_recovery(code, error_type)
            assert result['partial_metadata_extracted']
            assert result['error_reported']
            assert result['graceful_degradation']
    
def _test_edge_case_handling(self, code: str) -> Dict[str, Any]:
    """Test handling of edge cases."""
    raise NotImplementedError("Edge case handling not implemented")
    
def _test_error_recovery(self, code: str, error_type: str) -> Dict[str, Any]:
    """Test error recovery mechanisms."""
    raise NotImplementedError("Error recovery not implemented")

# Utility functions for testing metadata preservation

def extract_comments_from_source(source: str) -> List[Dict[str, Any]]:
    """Extract comments from source code."""
    raise NotImplementedError("Comment extraction not implemented")


def calculate_formatting_metrics(source: str) -> Dict[str, Any]:
    """Calculate formatting metrics for source code."""
    raise NotImplementedError("Formatting metrics not implemented")


def compare_metadata(original: Dict[str, Any], reconstructed: Dict[str, Any]) -> float:
    """Compare metadata between original and reconstructed versions."""
    raise NotImplementedError("Metadata comparison not implemented")


def measure_docstring_fidelity(original: str, reconstructed: str) -> float:
    """Measure fidelity of docstring preservation."""
    raise NotImplementedError("Docstring fidelity measurement not implemented")