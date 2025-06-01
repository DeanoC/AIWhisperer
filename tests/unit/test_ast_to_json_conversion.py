"""Unit tests for AST to JSON conversion - TDD RED phase tests."""

import pytest
import ast
import json
from datetime import datetime
from pathlib import Path

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


class TestASTToJSONStatements:
    """Tests for converting Python statement AST nodes to JSON."""
    
    def test_convert_function_def(self):
        """Test converting FunctionDef node to JSON."""
        code = """
def greet(name: str, greeting: str = "Hello") -> str:
    '''Greet someone with a custom greeting.'''
    return f"{greeting}, {name}!"
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
        # When implemented, should verify:
        # - Function node has correct structure
        # - Arguments are properly represented
        # - Docstring is captured
        # - Return annotation is preserved
    
def test_convert_async_function_def(self):
    """Test converting AsyncFunctionDef node to JSON."""
    code = """
async def fetch_data(url: str) -> bytes:
async with session.get(url) as response:
    return await response.read()
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_class_def(self):
    """Test converting ClassDef node to JSON."""
    code = """
@dataclass
class Person(BaseModel):
'''Represents a person.'''
name: str
age: int = 0
    
def __init__(self, name: str, age: int = 0):
    self.name = name
    self.age = age
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Should verify class structure, decorators, methods
    
def test_convert_assign_statements(self):
    """Test converting various assignment statements."""
    code = """
# Simple assignment
x = 42

# Multiple targets
a = b = c = 100

# Tuple unpacking
x, y = 1, 2

# Augmented assignment
total += value

# Annotated assignment
count: int = 0
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_control_flow_statements(self):
    """Test converting control flow statements."""
    code = """
# If statement
if condition:
do_something()
elif other_condition:
do_other()
else:
default_action()

# For loop
for i in range(10):
process(i)
else:
print("Done")

# While loop
while running:
update()
    
# Break and continue
for item in items:
if skip_condition:
    continue
if stop_condition:
    break
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_with_statement(self):
    """Test converting with statements."""
    code = """
with open('file.txt') as f:
content = f.read()

# Multiple context managers
with open('in.txt') as fin, open('out.txt', 'w') as fout:
fout.write(fin.read())
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_try_except(self):
    """Test converting try/except statements."""
    code = """
try:
risky_operation()
except ValueError as e:
handle_value_error(e)
except (TypeError, AttributeError):
handle_type_error()
except Exception:
handle_generic()
else:
success_handler()
finally:
cleanup()
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_import_statements(self):
    """Test converting import statements."""
    code = """
import os
import sys as system
from pathlib import Path
from typing import List, Dict as DictType
from ..parent import module
from . import sibling
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_global_nonlocal(self):
    """Test converting global and nonlocal statements."""
    code = """
def outer():
x = 1
    
def inner():
    nonlocal x
    global y
    x = 2
    y = 3
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_del_statement(self):
    """Test converting del statements."""
    code = """
del variable
del obj.attribute
del list_item[0]
del dict_item['key']
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_raise_statement(self):
    """Test converting raise statements."""
    code = """
raise ValueError("Invalid value")
raise
raise Exception from original_error
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_assert_statement(self):
    """Test converting assert statements."""
    code = """
assert condition
assert value > 0, "Value must be positive"
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_match_statement(self):
    """Test converting match statements (Python 3.10+)."""
    code = """
match command:
case ['move', x, y]:
    move_to(x, y)
case ['rotate', angle]:
    rotate(angle)
case {'action': 'jump', 'height': h}:
    jump(h)
case _:
    unknown_command()
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)

class TestASTToJSONExpressions:
    """Tests for converting Python expression AST nodes to JSON."""
    
    def test_convert_binary_operations(self):
        """Test converting binary operations."""
        code = """
a + b
x - y
m * n
p / q
r // s
t % u
v ** w
i << j
k >> l
x & y
a | b
c ^ d
p @ q
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_unary_operations(self):
    """Test converting unary operations."""
    code = """
+x
-y
~z
not flag
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_comparison_operations(self):
    """Test converting comparison operations."""
    code = """
a < b
x <= y
m > n
p >= q
r == s
t != u
v is w
x is not y
a in b
c not in d
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_boolean_operations(self):
    """Test converting boolean operations."""
    code = """
a and b
x or y
not z
a and b or c
(x or y) and z
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_function_calls(self):
    """Test converting function calls."""
    code = """
func()
func(arg1, arg2)
func(x, y=2)
func(*args)
func(**kwargs)
func(1, 2, *args, key=value, **kwargs)
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_attribute_access(self):
    """Test converting attribute access."""
    code = """
obj.attribute
obj.method()
module.submodule.function
chain.of.attributes.access
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_subscript_access(self):
    """Test converting subscript access."""
    code = """
list_item[0]
dict_item['key']
matrix[i][j]
slice_test[1:10:2]
slice_test[:5]
slice_test[5:]
slice_test[:]
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_literals(self):
    """Test converting various literals."""
    code = """
# Numbers
42
3.14
2 + 3j

# Strings
"hello"
'world'
'''multiline
string'''
f"formatted {value}"
b"bytes"
r"raw\\string"

# Constants
True
False
None
...
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_containers(self):
    """Test converting container literals."""
    code = """
# List
[1, 2, 3]
[]

# Tuple
(1, 2, 3)
()
(1,)

# Set
{1, 2, 3}
set()

# Dict
{'a': 1, 'b': 2}
{}
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_comprehensions(self):
    """Test converting comprehensions."""
    code = """
# List comprehension
[x * 2 for x in range(10)]
[x for x in items if x > 0]

# Dict comprehension
{k: v for k, v in pairs}
{x: x**2 for x in range(5) if x % 2 == 0}

# Set comprehension
{x for x in items}

# Generator expression
(x * 2 for x in range(10))

# Nested comprehension
[[i*j for j in range(3)] for i in range(3)]
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_lambda(self):
    """Test converting lambda expressions."""
    code = """
lambda: 42
lambda x: x * 2
lambda x, y: x + y
lambda x, y=10: x + y
lambda *args: sum(args)
lambda **kwargs: kwargs
lambda x, *args, y=1, **kwargs: x + y
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_conditional_expression(self):
    """Test converting conditional expressions."""
    code = """
x if condition else y
a if b > 0 else c if d > 0 else e
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_starred_expression(self):
    """Test converting starred expressions."""
    code = """
[*items]
{*set1, *set2}
(*tuple1, *tuple2)
func(*args)
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_yield_expressions(self):
    """Test converting yield expressions."""
    code = """
def generator():
yield 1
yield from other_generator()
x = yield 42
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_await_expression(self):
    """Test converting await expressions."""
    code = """
async def async_func():
result = await coroutine()
data = await asyncio.gather(*tasks)
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_walrus_operator(self):
    """Test converting walrus operator (named expressions)."""
    code = """
if (n := len(items)) > 10:
print(n)

while (line := file.readline()):
process(line)
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)

class TestASTToJSONComplexStructures:
    """Tests for converting complex nested structures."""
    
    def test_convert_nested_functions(self):
        """Test converting nested function definitions."""
        code = """
def outer(x):
    def middle(y):
        def inner(z):
            return x + y + z
        return inner
    return middle
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_class_with_nested_classes(self):
    """Test converting classes with nested classes."""
    code = """
class Outer:
class Inner:
    class Innermost:
        value = 42
        
    def method(self):
        return self.Innermost.value
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_complex_decorators(self):
    """Test converting complex decorator patterns."""
    code = """
@decorator1
@decorator2(arg1, arg2)
@decorator3(key=value)
@module.decorator4
class DecoratedClass:
@property
@lru_cache(maxsize=128)
def cached_property(self):
    return expensive_computation()
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_complex_type_annotations(self):
    """Test converting complex type annotations."""
    code = """
from typing import Union, Optional, List, Dict, Callable, TypeVar

T = TypeVar('T')
def complex_func(
    items: List[Union[int, str]],
    callback: Callable[[T], Optional[T]],
    mapping: Dict[str, List[Union[int, float]]]
) -> Optional[Dict[str, T]]:
    pass
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_deeply_nested_expressions(self):
    """Test converting deeply nested expressions."""
    code = """
result = (
func1(
    func2(
        x + y * (z - w) / (a + b),
        [i for i in range(10) if i % 2 == 0]
    ),
    {
        'key1': [1, 2, 3],
        'key2': {'nested': True}
    }
) if condition else default
)
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_convert_complex_comprehension_nesting(self):
    """Test converting complex nested comprehensions."""
    code = """
matrix = [
[
    [
        cell 
        for cell in row 
        if cell > 0
    ] 
    for row in plane 
    if any(cell > 0 for cell in row)
] 
for plane in cube 
if len(plane) > 0
]
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)

class TestASTToJSONMetadataPreservation:
    """Tests for metadata preservation during conversion."""
    
    def test_preserve_line_numbers(self):
        """Test that line numbers are preserved in JSON."""
        code = """x = 1  # Line 1
y = 2  # Line 2

def func():  # Line 4
    pass  # Line 5
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
        # Should verify each node has correct lineno
    
def test_preserve_column_offsets(self):
    """Test that column offsets are preserved in JSON."""
    code = "x = 1; y = 2; z = 3"
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Should verify each node has correct col_offset
    
def test_preserve_end_positions(self):
    """Test that end line and column are preserved."""
    code = """result = (
long_function_call(
    argument1,
    argument2
)
)"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Should verify end_lineno and end_col_offset
    
def test_metadata_with_unicode(self):
    """Test metadata preservation with unicode identifiers."""
    code = """π = 3.14159
面积 = π * 半径 ** 2"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_docstring_preservation(self):
    """Test that docstrings are properly preserved."""
    code = '''
def function_with_docstring():
"""This is a docstring.
    
It has multiple lines.
"""
pass
class ClassWithDocstring:
    """Class docstring."""
    
    def method_with_docstring(self):
        """Method docstring."""
        pass
'''
        tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
    
def test_type_comment_preservation(self):
    """Test preservation of type comments."""
    code = """
x = 1  # type: int
y = []  # type: List[str]
def func(a, b):  # type: (int, str) -> bool
    pass
"""
    tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)

class TestASTToJSONSchemaCompliance:
    """Tests for JSON schema compliance."""
    
    def test_json_structure_has_ast_and_metadata(self):
        """Test that output has required top-level structure."""
        code = "x = 1"
        tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
        # Should have 'ast' and 'metadata' keys
    
def test_metadata_has_required_fields(self):
    """Test that metadata contains all required fields."""
    code = "x = 1"
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # metadata should have python_version, conversion_timestamp
    
def test_node_type_field_present(self):
    """Test that all nodes have node_type field."""
    code = """
x = 1
def func():
return x
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Every node should have 'node_type' field
    
def test_location_info_structure(self):
    """Test that location info follows schema structure."""
    code = "x = 1"
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Location should have lineno, col_offset, etc.
    
def test_json_serializable(self):
    """Test that output is JSON serializable."""
    code = """
import sys
x = 42
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # Should be able to json.dumps(result)
    
def test_no_circular_references(self):
    """Test that JSON has no circular references."""
    code = """
class Node:
def __init__(self):
    self.parent = None
    self.children = []
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
        # JSON should be serializable without circular ref errors

class TestASTToJSONEdgeCases:
    """Tests for edge cases in AST to JSON conversion."""
    
    def test_empty_module(self):
        """Test converting empty module."""
        code = ""
        tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree)
    
def test_comments_only(self):
    """Test module with only comments."""
    code = """
# This is a comment
# Another comment
"""
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_single_expression(self):
    """Test module with single expression."""
    code = "42"
    tree = ast.parse(code, mode='eval')
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_very_long_identifiers(self):
    """Test handling very long identifiers."""
    code = f"{'x' * 1000} = 1"
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_special_string_literals(self):
    """Test various special string literals."""
    code = r'''
s1 = "Line 1\nLine 2"
s2 = r"Raw \n string"
s3 = b"Byte string"
s4 = """Triple
quoted"""
s5 = f"Format {value}"
s6 = fr"Raw format {value}"
'''
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)
    
def test_extreme_nesting_depth(self):
    """Test extremely deep nesting."""
    # Create deeply nested if statements
    code = "if True:\n"
    for i in range(50):
        code += "    " * (i + 1) + "if True:\n"
    code += "    " * 51 + "pass"
        
    tree = ast.parse(code)
        
    result = PythonASTJSONTool.ast_to_json(tree)

class TestASTToJSONWithOptions:
    """Tests for AST to JSON conversion with various options."""
    
    def test_without_metadata(self):
        """Test conversion without metadata."""
        code = "x = 1"
        tree = ast.parse(code)
        
        result = PythonASTJSONTool.ast_to_json(tree, include_metadata=False)
    
    def test_file_to_json_method(self):
        """Test file_to_json static method."""
        result = PythonASTJSONTool.file_to_json("test.py")
    
    def test_module_to_json_method(self):
        """Test module_to_json static method."""
        result = PythonASTJSONTool.module_to_json("os")
    
    def test_formatted_output(self):
        """Test formatted JSON output option."""
        code = "x = 1"
        tool = PythonASTJSONTool()
        
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code",
                format_output=True
            )
    
    def test_unformatted_output(self):
        """Test unformatted JSON output option."""
        code = "x = 1"
        tool = PythonASTJSONTool()
        
        result = tool.execute(
                action="to_json",
                source=code,
                source_type="code",
                format_output=False
            )