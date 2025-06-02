"""Unit tests for Python AST parsing functionality - TDD RED phase tests."""

import pytest
import ast
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestASTParsingFilePaths:
    """Tests for parsing Python files via file paths."""
    
    def test_parse_simple_python_file(self, tmp_path):
        """Test parsing a simple Python file."""
        # Create a test file
        test_file = tmp_path / "simple.py"
        test_file.write_text("x = 42\nprint(x)")
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
    
    def test_parse_file_with_functions(self, tmp_path):
        """Test parsing a file with function definitions."""
        test_file = tmp_path / "functions.py"
        test_file.write_text("""
def hello(name):
    '''Say hello to someone'''
    return f"Hello, {name}!"
def add(a, b):
    return a + b
""")
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
    
    def test_parse_file_with_classes(self, tmp_path):
            """Test parsing a file with class definitions."""
    test_file = tmp_path / "classes.py"
    test_file.write_text("""
class Person:
'''A person class'''
def __init__(self, name: str, age: int):
    self.name = name
    self.age = age
    
def greet(self) -> str:
    return f"Hi, I'm {self.name}"
""")
        
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
    
def test_parse_nonexistent_file(self):
    """Test parsing a file that doesn't exist."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="/nonexistent/file.py",
            source_type="file"
        )
    
def test_parse_file_with_encoding(self, tmp_path):
    """Test parsing a file with specific encoding."""
    test_file = tmp_path / "encoded.py"
    test_file.write_text("# -*- coding: utf-8 -*-\nname = 'café'", encoding="utf-8")
        
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
    
def test_parse_relative_file_path(self):
    """Test parsing with relative file path."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="./tests/unit/test_utils.py",
            source_type="file"
        )
    
    def test_parse_file_preserves_line_numbers(self, tmp_path):
        """Test that parsing preserves line number information."""
        test_file = tmp_path / "multiline.py"
        test_file.write_text("""# Line 1
    x = 1  # Line 2
    y = 2  # Line 3
    def func():  # Line 5
        pass  # Line 6
    """)
            
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
        # When implemented, should verify line numbers are preserved

class TestASTParsingModules:
    """Tests for parsing Python modules by name."""
    
    def test_parse_builtin_module(self):
        """Test parsing a built-in module like 'os'."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="os",
            source_type="module"
        )
    
def test_parse_module_with_submodule(self):
    """Test parsing a module with submodule like 'os.path'."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="os.path",
            source_type="module"
        )
    
def test_parse_third_party_module(self):
    """Test parsing a third-party module."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="pytest",
            source_type="module"
        )
    
def test_parse_nonexistent_module(self):
    """Test parsing a module that doesn't exist."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="nonexistent_module_xyz",
            source_type="module"
        )
    
def test_parse_package_init(self):
    """Test parsing a package's __init__.py."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="ai_whisperer",
            source_type="module"
        )
    
def test_module_to_json_static_method(self):
    """Test the static module_to_json method."""
    result = PythonASTJSONTool.module_to_json("json")

class TestASTParsingCodeStrings:
    """Tests for parsing Python code strings directly."""
    
    def test_parse_simple_code_string(self):
        """Test parsing a simple code string."""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source="x = 42",
            source_type="code"
        )
    
def test_parse_multiline_code_string(self):
    """Test parsing multiline code string."""
    code = """
def factorial(n):
if n <= 1:
    return 1
return n * factorial(n - 1)

result = factorial(5)
"""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
def test_parse_empty_code_string(self):
    """Test parsing an empty code string."""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source="",
            source_type="code"
        )

class TestASTParsingInvalidSyntax:
    """Tests for handling invalid Python syntax."""
    
    def test_parse_syntax_error_missing_colon(self):
        """Test parsing code with missing colon."""
        code = "if True\n    print('missing colon')"
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
    def test_parse_syntax_error_invalid_indentation(self):
        """Test parsing code with invalid indentation."""
        code = "def func():\nprint('bad indent')"
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
        
    def test_parse_syntax_error_unclosed_string(self):
        """Test parsing code with unclosed string."""
        code = 'text = "unclosed string'
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
        
    def test_parse_syntax_error_invalid_assignment(self):
        """Test parsing code with invalid assignment."""
        code = "1 = x"
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
        
    def test_parse_file_with_syntax_error(self, tmp_path):
        """Test parsing a file containing syntax errors."""
        test_file = tmp_path / "syntax_error.py"
        test_file.write_text("def func(\n    pass")
            
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=str(test_file),
                source_type="file"
            )
        
    def test_parse_non_python_file(self, tmp_path):
        """Test parsing a non-Python file."""
        test_file = tmp_path / "data.json"
        test_file.write_text('{"key": "value"}')
            
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=str(test_file),
                source_type="file"
            )

class TestASTNodeStructureVerification:
    """Tests for verifying AST node structure correctness."""
    
    def test_verify_function_node_structure(self):
        """Test that function nodes have correct structure."""
        code = """
def add(a: int, b: int) -> int:
    '''Add two numbers'''
    return a + b
"""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        # When implemented, should verify:
        # - node_type is "FunctionDef"
        # - has name, args, body, returns
        # - docstring is captured
    
def test_verify_class_node_structure(self):
    """Test that class nodes have correct structure."""
    code = """
class MyClass(BaseClass):
'''A test class'''
def __init__(self):
    super().__init__()
"""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        # When implemented, should verify:
        # - node_type is "ClassDef"
        # - has name, bases, body
        # - docstring is captured
    
def test_verify_comprehension_node_structure(self):
    """Test that comprehension nodes have correct structure."""
    code = "[x*2 for x in range(10) if x % 2 == 0]"
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
        # When implemented, should verify:
        # - node_type is "ListComp"
        # - has elt and generators
    
    def test_verify_import_node_structure(self):
        """Test that import nodes have correct structure."""
        code = """
    import os
    from pathlib import Path
    from typing import List, Dict as DictType
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
            # When implemented, should verify import structures
    
    def test_verify_decorator_preservation(self):
        """Test that decorators are preserved in AST."""
        code = """
    @property
    @lru_cache(maxsize=128)
    def cached_property(self):
    return expensive_computation()
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
            # When implemented, should verify decorator_list

class TestPython38PlusFeatures:
    """Tests for Python 3.8+ specific syntax features."""
    
    def test_parse_walrus_operator(self):
        """Test parsing walrus operator (Python 3.8+)."""
        code = """
if (n := len(data)) > 10:
    print(f"List has {n} elements")
"""
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
    def test_parse_positional_only_params(self):
        """Test parsing positional-only parameters (Python 3.8+)."""
        code = """
    def func(a, b, /, c, d):
    return a + b + c + d
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
    
    def test_parse_f_string_equals(self):
        """Test parsing f-string = specifier (Python 3.8+)."""
        code = """
    x = 42
    debug = f"{x=}"
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
    
    def test_parse_type_hint_literals(self):
        """Test parsing Literal type hints (Python 3.8+)."""
        code = """
    from typing import Literal
    def process(mode: Literal['read', 'write']) -> None:
        pass
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
    def test_parse_match_statement(self):
        """Test parsing match statement (Python 3.10+)."""
        code = """
    def process_command(command):
    match command:
        case ['move', x, y]:
            return f"Moving to {x}, {y}"
        case ['rotate', angle]:
            return f"Rotating {angle} degrees"
        case _:
            return "Unknown command"
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
    
    def test_parse_union_types(self):
        """Test parsing union types with | operator (Python 3.10+)."""
        code = """
    def process(value: int | str | None) -> str | None:
    if value is None:
        return None
    return str(value)
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
    
    def test_parse_async_comprehensions(self):
        """Test parsing async comprehensions."""
        code = """
    async def process():
    result = [x async for x in async_generator()]
    return result
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code"
            )
        
    def test_parse_type_params(self):
        """Test parsing generic type parameters (Python 3.12+)."""
        code = """
    def first[T](items: list[T]) -> T:
    return items[0]
    class Stack[T]:
        def __init__(self):
            self.items: list[T] = []
    """
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )

class TestASTParsingEdgeCases:
    """Tests for edge cases in AST parsing."""
    
    def test_parse_very_long_file(self, tmp_path):
        """Test parsing a very long file."""
        test_file = tmp_path / "long_file.py"
        # Create a file with many lines
        lines = [f"var_{i} = {i}" for i in range(1000)]
        test_file.write_text("\n".join(lines))
        
        tool = PythonASTJSONTool()
        result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )
    
def test_parse_deeply_nested_code(self):
    """Test parsing deeply nested code structures."""
    code = """
def outer():
def middle():
    def inner():
        def deepest():
            if True:
                while True:
                    for i in range(10):
                        try:
                            with open('file') as f:
                                pass
                        except:
                            pass
"""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
def test_parse_unicode_identifiers(self):
    """Test parsing code with unicode identifiers."""
    code = """
π = 3.14159
面积 = π * 半径 ** 2
"""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
def test_parse_complex_expressions(self):
    """Test parsing complex nested expressions."""
    code = """
result = (lambda x: [y for y in (z := x * 2 for x in range(10)) if y > 5])(42)
"""
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=code,
            source_type="code"
        )
    
def test_parse_file_with_different_newlines(self, tmp_path):
    """Test parsing files with different newline conventions."""
    test_file = tmp_path / "mixed_newlines.py"
    # Mix different newline styles
    content = "x = 1\r\ny = 2\rz = 3\n"
    test_file.write_bytes(content.encode('utf-8'))
        
    tool = PythonASTJSONTool()
    result = tool.execute(
            action="to_json",
            source=str(test_file),
            source_type="file"
        )

class TestASTParsingMetadata:
    """Tests for metadata preservation during parsing."""
    
    def test_metadata_includes_source_file(self, tmp_path):
        """Test that metadata includes source file path."""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")
        
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=str(test_file),
                source_type="file"
            )
            # When implemented, should verify metadata.source_file
    
    def test_metadata_includes_module_name(self):
        """Test that metadata includes module name."""
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source="json",
                source_type="module"
            )
            # When implemented, should verify metadata.module_name
    
    def test_metadata_includes_python_version(self):
        """Test that metadata includes Python version."""
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source="x = 1",
                source_type="code"
            )
            # When implemented, should verify metadata.python_version
    
    def test_metadata_encoding_detection(self, tmp_path):
        """Test that metadata correctly detects file encoding."""
        test_file = tmp_path / "encoded.py"
        test_file.write_text(
            "# -*- coding: latin-1 -*-\ntext = 'café'",
            encoding="latin-1"
        )
        
        tool = PythonASTJSONTool()
        result = tool.execute(
                action="to_json",
                source=str(test_file),
                source_type="file"
            )
            # When implemented, should verify metadata.encoding == "latin-1"