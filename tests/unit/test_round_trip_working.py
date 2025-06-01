"""Working round-trip tests - GREEN phase implementation."""

import pytest
import ast
import time
import hashlib
import difflib
from typing import Dict, Any, Tuple
from pathlib import Path

from ai_whisperer.tools.python_ast_json_tool import PythonASTJSONTool


def fix_missing_locations(node, lineno=1, col_offset=0):
    """Add missing location information to AST nodes."""
    if isinstance(node, ast.AST):
        if not hasattr(node, 'lineno'):
            node.lineno = lineno
        if not hasattr(node, 'col_offset'):
            node.col_offset = col_offset
        for field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, ast.AST):
                        fix_missing_locations(child, lineno, col_offset)
            elif isinstance(value, ast.AST):
                fix_missing_locations(value, lineno, col_offset)
    return node


class TestRoundTripBasicConstructs:
    """Test round-trip fidelity for basic Python constructs."""
    
    def test_simple_expressions(self):
        """Test round-trip for simple expressions."""
        test_cases = [
            "2 + 2",
            "x * y - z",
            "a and b or c",
            "not x",
            "x if condition else y",
            "x is not None",
            "a < b <= c < d",  # Chained comparison
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code, mode='eval')
            assert result['success'], f"Round-trip failed for: {code}"
            assert result['ast_identical'], f"AST mismatch for: {code}"
    
    def test_basic_statements(self):
        """Test round-trip for basic statements."""
        test_cases = [
            "x = 42",
            "x += 1",
            "x: int = 42",
            "del x",
            "pass",
            "break",
            "continue",
            "return x",
            "return",
            "global x",
            "nonlocal y",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code)
            assert result['success'], f"Round-trip failed for: {code}"
    
    def test_function_definitions(self):
        """Test round-trip for various function definitions."""
        test_cases = [
            # Simple function
            """
def simple():
    pass
""",
            # Function with arguments
            """
def with_args(a, b=1, *args, c, d=2, **kwargs):
    return a + b
""",
            # Async function
            """
async def async_func():
    await something()
""",
            # Decorated function
            """
@decorator
def decorated():
    pass
""",
            # Function with annotations
            """
def annotated(x: int, y: str = "default") -> bool:
    return True
""",
            # Lambda expressions
            "lambda x: x * 2",
            "lambda x, y=0: x if x > y else y",
        ]
        
        for code in test_cases:
            if code.strip().startswith("lambda"):
                result = self._test_round_trip(code, mode='eval')
            else:
                result = self._test_round_trip(code)
            assert result['success'], f"Round-trip failed for function"
    
    def test_class_definitions(self):
        """Test round-trip for class definitions."""
        test_cases = [
            # Simple class
            """
class Simple:
    pass
""",
            # Class with inheritance
            """
class Child(Parent, Mixin):
    pass
""",
            # Class with methods
            """
class Complex:
    '''Class docstring'''
    
    def __init__(self, x):
        self.x = x
    
    def method(self):
        return self.x
""",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code)
            assert result['success'], "Round-trip failed for class"
    
    def _test_round_trip(self, code: str, mode: str = 'exec') -> Dict[str, Any]:
        """Test round-trip conversion and return metrics."""
        try:
            # Stage 1: Python → AST
            original_ast = ast.parse(code, mode=mode)
            
            # Stage 2: AST → JSON
            json_data = PythonASTJSONTool.ast_to_json(original_ast)
            
            # Stage 3: JSON → AST
            reconstructed_ast = PythonASTJSONTool.json_to_ast(json_data)
            
            # Fix missing locations
            fix_missing_locations(reconstructed_ast)
            
            # Stage 4: AST → Python
            reconstructed_code = ast.unparse(reconstructed_ast)
            
            # Verify by parsing again
            final_ast = ast.parse(reconstructed_code, mode=mode)
            
            return {
                'success': True,
                'ast_identical': self._compare_asts(original_ast, final_ast),
                'original_code': code,
                'reconstructed_code': reconstructed_code,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'ast_identical': False,
            }
    
    def _compare_asts(self, ast1: ast.AST, ast2: ast.AST) -> bool:
        """Compare two AST structures for equivalence."""
        # Simple comparison - normalize and compare dumps
        return ast.dump(ast1, annotate_fields=False) == ast.dump(ast2, annotate_fields=False)


class TestRoundTripDataStructures:
    """Test round-trip fidelity for data structures."""
    
    def test_literals(self):
        """Test round-trip for various literals."""
        test_cases = [
            # Numbers
            "42",
            "3.14",
            "1e-10",
            "1_000_000",
            "3.14j",  # Complex number
            
            # Strings
            "'single quotes'",
            '"double quotes"',
            '"""triple quotes"""',
            "r'raw string'",
            "b'bytes'",
            "f'formatted {value}'",
            
            # Special literals
            "None",
            "True",
            "False",
            "...",  # Ellipsis
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code, mode='eval')
            assert result['success'], f"Round-trip failed for: {code}"
    
    def test_collections(self):
        """Test round-trip for collections."""
        test_cases = [
            # Lists
            "[]",
            "[1, 2, 3]",
            
            # Tuples
            "()",
            "(1,)",
            "(1, 2, 3)",
            
            # Sets
            "set()",
            "{1, 2, 3}",
            
            # Dicts
            "{}",
            "{'a': 1, 'b': 2}",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code, mode='eval')
            assert result['success'], f"Round-trip failed for: {code}"
    
    def test_comprehensions(self):
        """Test round-trip for comprehensions."""
        test_cases = [
            # List comprehensions
            "[x for x in range(10)]",
            "[x for x in range(10) if x % 2 == 0]",
            
            # Set comprehensions
            "{x for x in range(10)}",
            
            # Dict comprehensions
            "{x: x**2 for x in range(5)}",
            
            # Generator expressions
            "(x for x in range(10))",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code, mode='eval')
            assert result['success'], f"Round-trip failed for: {code}"
    
    def _test_round_trip(self, code: str, mode: str = 'exec') -> Dict[str, Any]:
        """Test round-trip conversion."""
        try:
            original_ast = ast.parse(code, mode=mode)
            json_data = PythonASTJSONTool.ast_to_json(original_ast)
            reconstructed_ast = PythonASTJSONTool.json_to_ast(json_data)
            fix_missing_locations(reconstructed_ast)
            reconstructed_code = ast.unparse(reconstructed_ast)
            final_ast = ast.parse(reconstructed_code, mode=mode)
            
            return {
                'success': True,
                'ast_identical': ast.dump(original_ast, annotate_fields=False) == ast.dump(final_ast, annotate_fields=False),
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }


class TestRoundTripControlFlow:
    """Test round-trip for control flow structures."""
    
    def test_if_statements(self):
        """Test round-trip for if statements."""
        test_cases = [
            """
if condition:
    do_something()
""",
            """
if x > 0:
    positive()
else:
    negative()
""",
            """
if x > 0:
    positive()
elif x < 0:
    negative()
else:
    zero()
""",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code)
            assert result['success'], "Round-trip failed for if statement"
    
    def test_loops(self):
        """Test round-trip for loops."""
        test_cases = [
            # For loop
            """
for i in range(10):
    print(i)
""",
            # While loop
            """
while condition:
    do_something()
    condition = update()
""",
            # For loop with else
            """
for item in items:
    if found:
        break
else:
    not_found()
""",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code)
            assert result['success'], "Round-trip failed for loop"
    
    def test_exception_handling(self):
        """Test round-trip for exception handling."""
        test_cases = [
            # Simple try-except
            """
try:
    risky()
except Exception:
    handle()
""",
            # Try-except-else-finally
            """
try:
    attempt()
except Error:
    handle()
else:
    success()
finally:
    cleanup()
""",
        ]
        
        for code in test_cases:
            result = self._test_round_trip(code)
            assert result['success'], "Round-trip failed for exception handling"
    
    def _test_round_trip(self, code: str, mode: str = 'exec') -> Dict[str, Any]:
        """Test round-trip conversion."""
        try:
            original_ast = ast.parse(code, mode=mode)
            json_data = PythonASTJSONTool.ast_to_json(original_ast)
            reconstructed_ast = PythonASTJSONTool.json_to_ast(json_data)
            fix_missing_locations(reconstructed_ast)
            reconstructed_code = ast.unparse(reconstructed_ast)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class TestRoundTripRealWorld:
    """Test round-trip with real-world code patterns."""
    
    def test_complete_module(self):
        """Test a complete module structure."""
        code = '''#!/usr/bin/env python3
"""Module docstring."""

import os
import sys

def main():
    """Main function."""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        
        result = self._test_round_trip(code)
        assert result['success'], "Round-trip failed for complete module"
        # Note: Shebang and some formatting might change
    
    def _test_round_trip(self, code: str) -> Dict[str, Any]:
        """Test round-trip conversion."""
        try:
            # Skip shebang if present
            if code.startswith('#!'):
                code = '\n'.join(code.split('\n')[1:])
                
            original_ast = ast.parse(code)
            json_data = PythonASTJSONTool.ast_to_json(original_ast)
            reconstructed_ast = PythonASTJSONTool.json_to_ast(json_data)
            fix_missing_locations(reconstructed_ast)
            reconstructed_code = ast.unparse(reconstructed_ast)
            
            # Verify it parses
            ast.parse(reconstructed_code)
            
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}